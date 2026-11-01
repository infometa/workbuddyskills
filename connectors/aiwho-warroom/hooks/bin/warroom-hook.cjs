#!/usr/bin/env node
'use strict';
/*
 * WarRoom Hook —— 把 WorkBuddy 的「任务完成 / 用户提问」事件自动推送到 AIWHO WEBHOOK中台。
 *
 * 为什么需要它（而不是 MCP）：
 *   MCP 工具要 agent「记得调」才发；Hooks 由宿主引擎在固定时机**自动**拉起，
 *   与模型是否自觉无关。这正是「固定完成任务和询问执行的时候都发送」的正确机制。
 *
 * 注册方式（~/.workbuddy/settings.json）—— 现注册 9 个事件：
 *   UserPromptSubmit / Stop / Notification / PermissionRequest /
 *   SessionStart / SessionEnd / StopFailure / TaskCreated / TaskCompleted
 *   🔑 一键注册：`node scripts/install-hook.mjs`（自动探宿主 + 系统 node 绝对路径 + 引号包裹 + 幂等 + 备份）。
 *      ⚠️ **连接器包（connector/）里没有 hook 槽位** —— WorkBuddy 连接器规范只有
 *      mcp.json / connector-meta.json / token-schema.json / icon / skills，所以「事件自动推送」
 *      必须在**用户机上装这一次**，装不了的部分退到 MCP 工具（AI 主动调）或 git hook。
 *   ⚠️ 改 settings.json 的**事件列表**必须完全退出并重开 WorkBuddy（引擎只在启动时快照配置）；
 *      而改**本文件内容**不用重启 —— 每次事件都是新起一个进程来跑它。
 *   "hooks": {
 *     "Stop":             [{ "hooks": [{ "type": "command", "command": "node <本文件>", "timeout": 15 }] }],
 *     "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "node <本文件>", "timeout": 15 }] }]
 *   }
 *
 * 宿主可移植性（2026-10-07 核对）：
 *   本文件吃的事件名与 stdin 字段**就是 Claude Code 的 hook 协议**（同名同形）——
 *   `session_id` / `transcript_path` / `cwd` / `hook_event_name` / `stop_hook_active` / `prompt`，
 *   配置形状 `{"hooks":{"<事件>":[{"hooks":[{"type":"command",…}]}]}}` 也一致。
 *   所以搬到 Claude Code 只需：注册进 ~/.claude/settings.json + handler 加 `"async": true`
 *   + **必须**带 `--host=claude-code`（见下「宿主判别」）。见 SKILL.md §7.4。
 *
 * stdin：宿主写入一个 JSON 对象后立即 end()
 *   { session_id, transcript_path, cwd, hook_event_name, prompt?(UserPromptSubmit), stop_hook_active?(Stop) }
 *
 * stdout 协议（见引擎 parseHookOutput / tryAsyncProbe）：
 *   - 以 '{' 开头且解析出的对象含 "async": true → 宿主**立刻放行并分离**本进程，不等我们跑完。
 *     Stop 钩子必须这样做，否则每轮收尾都会被 3500 的推送时延堵住。
 *   - exit code 0 = allowed；非 0 会被视作 blocked（Stop 事件会变成「反馈注入」）。
 *     所以：**任何失败都不许非 0 退出**，一律 exit 0 + 贴一行 stderr 备注。
 *   🔴 这是 **WorkBuddy 私有**的 stdout 握手，不是 Claude Code 的。
 *      Claude Code 的异步靠配置里的 `"async": true`，而它会把 hook 的 stdout 当**上下文**注入下一轮
 *      → 在 Claude Code 下吐这段 JSON 等于每次提问都往模型上下文里塞垃圾。
 *      故：`--host=claude-code` 时**闭嘴**（不发握手），异步交给 handler 的 `"async": true`。
 *      默认不传 `--host` → 行为与本机既有配置**逐字不变**（WorkBuddy 照旧吐握手）。
 *
 * 输出策略（事件 → 标题 / 级别；`sid` = session_id）：
 *   UserPromptSubmit  → 「🙋 收到指令」                        info    （正文 = 用户原话）
 *   Stop              → 「✅ 任务完成」                        info    （走 notify_task_complete）
 *   Notification      → 「⚠️ 需要你操作：…」/「⏳ 等待你的输入」  按 notification_type 分流
 *   PermissionRequest → 「🔐 请求权限：<工具名>」                urgent
 *     ⚠️ 这两类（Notification / PermissionRequest）的幂等键都带 **5s 短时间桶**（`NOTIFY_BUCKET_MS`）：
 *        引擎给的 message 是固定文案，纯指纹会让后续每次都被去重折叠（命中还不更新正文）
 *        → 大屏上只剩最早那一条，看着就像「根本没推」（10-02 实测踩过）。
 *   SessionStart      → `startup` **静音**（与「收到指令」重复）；
 *                        `resume`/`clear`/`compact` 各推一条状态变更
 *   SessionEnd        → 「⚪ 会话结束」                        info
 *   StopFailure       → 「❌ 本轮失败」                        warning
 *   TaskCreated      → 「📋 新建任务计划：<标题>」                   info    （**创建时刻即时推**，见⑧；防刷屏回落见 WARROOM_HOOK_CREATED_EACH=0）
 *   TaskCompleted    → 「✅ 已完成任务计划：<标题>」                   info    （**入队合并**，见⑦；逐条见 WARROOM_HOOK_DONE_EACH=1）
 *   每个事件都**显式给--external-id** —— 不是因为缺省值不能用（10-23 Issue #2 起缺省键已按
 *   「内容指纹 + 时间桶」生成，不同内容天然不撞），而是因为 hook 的语义更严：
 *   它要保证「同一次提示词跨进程 / 跨重投折叠成一条」，这个「同一次」只有 hook 自己知道
 *   （会话 id + 事件类型 + 指纹），交给缺省值反而会丢粒度。
 *
 * 本轮聚合（10-02 用户反馈「做任务时同时推送好几条，TTS 排队重复播报」）：
 *   成因：TaskCreate 是**成批**发生的（一次规划就建 5~7 条），TaskCompleted 也常连成串
 *   （实测 07:00:03 起 140ms 内 4 条）→ 每个事件一个独立进程、各推一条 → 大屏刷 5 行、语音排队念 5 遍。
 *   做法：**按事件类型分治**，不是一刀切 —— 粒度要匹配语义：
 *     · TaskCreated → 🔴 10-04 改为**创建时刻即时推送**（每条「📋 新建任务计划：<名>」立即上屏），
 *       不再等收尾合并。原因：并入收尾会让「新建」与「完成」时间戳相同，看着像「完成后才推新建」。
 *       代价是规划 5~7 条会即时刷多行；嫌刷屏设 `WARROOM_HOOK_CREATED_EACH=0` 回落回「入队合并成一条」。
 *     · TaskCompleted →10-02 改判为**入队合并**（初版逐条；用户实测一轮连完成 3 条 → TTS 念 3 遍）。
 *       改判理由：用户实测「一轮连着完成 3 条 → 大屏 3 行 + TTS 念 3 遍」，听感上仍是「被拆成三条」。
 *       🔑 逃生舱 `WARROOM_HOOK_DONE_EACH=1` → 立刻恢复「完成逐条上屏」，不必改代码。
 *     · TTS 只念**标题**（`renderBroadcastText({title})`），所以长描述进正文、不进标题。
 *
 *   🔴🔴 10-02 用户实测反馈的**真正根因 = 标题，不是条数**：
 *     待办标题写成「新建任务计划：1.xxx / 2.xxx / 3.xxx」这种**自带类别前缀 + 序号**的形式时，
 *     哪怕合并成一条，收尾那条的正文/标题仍会把「新建任务计划一点 xxx」念出来 → 听感依旧是三条。
 *     所以 `cleanSubject()` 在**入队前**剥掉「新建任务计划：」/「待办：」等类别前缀与「1.」「(2)」「③」等序号，
 *     只留动作本体（「更新文档与备忘」）。**合并管条数，清洗管念读，两者缺一不可。**
 *
 *   ⚠️ 为什么**不**用「抢锁 + 静默窗口」那套（初版设计，已废弃）：它要求多个 hook 进程
 *   **真的同时活着**，谁抢到锁谁等 1.5s 收口。一旦宿主改成串行拉起、或某次队列目录写不进去，
 *   就**静默退化成逐条单发** —— 又回到刷屏，而且现场看不出来（10-02 实测 07:00 那批就是如此）。
 *   现在这套不依赖任何时序假设：入队只增不改（无锁），出队锚在**每轮天然唯一**的收尾时刻。
 *
 *   ⚠️ Stop **并非每轮都触发**（10-02 实测 7 次提问只等到 3 次 Stop，被中断的轮次更不会有）——
 *   所以有第二道：`UserPromptSubmit`（= 新一轮开始的那一刻）会把「躺够 `STALE_FLUSH_MS`(10min)」
 *   的陈货冲成一条发掉，只兜底、不会打断正常合并。收尾事件缺席也不会把待办永久困在队列里。
 *   🔴 10-02 修掉的 BUG：原先是「**任何非收尾**事件开头都冲」+ 20s 阈值，而一轮真实要跑
 *      2~20 分钟 → 下一轮第一个事件就把上一轮的待办抢跑冲掉，消息与轮次对不上号。
 *      现在只在 `UserPromptSubmit` 冲，且阈值拉到 10 分钟（见 `STALE_FLUSH_MS` 处详述）。
 *
 *   ⚠️ **Notification / PermissionRequest 保持即时单发**：它们是「要人当场动手」的
 *   （授权确认、等你补信息），延迟或并条都可能被漏看 —— 少推几条不值得冒这个险。
 *   正常一轮 = 1（收到指令）+ N（新建即时·每条各 1 条）+ 1（收尾·完成合并成 1 条）+ 可能的通知。
 *   若规划新建过多刷屏，设 `WARROOM_HOOK_CREATED_EACH=0` 让新建也并入收尾那条。
 *
 *   队列落在 `~/.workbuddy/logs/warroom-hook-batch/<会话 id>/`，发完即删、目录自动回收。
 *   自检：`node <本文件> --turn-doctor [N] [M]`（起 N+M+1 个真进程演一轮，dry-run 不联网，
 *   硬判据：建待办期间推送 0 次、M 条完成各占 1 条、整轮 = M+1 条）。
 *
 * 连接参数从哪来（重要）：
 *   引擎**不注入任何 env**（settings.json 无 env 段）→ 旧实现回落 `http://localhost:3500`
 *   （本机 dev 端口，平时并不开）→ 9 个事件的推送**全部静默失败**，大屏上只剩 agent
 *   手动推的通知，看起来像「只有任务完成在推」。
 *   现改为读 `~/.workbuddy/mcp.json` 里 warroom-webhook 的 env（MCP 自己用的那份，
 *   唯一来源）；若进程 env 设了 WARROOM_* 则以 env 为准（用于临时指向本机 dev）。
 *   自检：`node <本文件> --doctor`（加 `--no-push` 只探活、不真推）。
 *   日志：`~/.workbuddy/logs/warroom-hook.log`（stderr 只有引擎看得到，故另落盘一份）。
 *
 * 硬性要求：stdout 里**只**能有那个 {async} 对象。
 *   子进程（warroom-webhook.cjs）的输出必须继承到 stderr，绝不能与 stdout 混流。
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// 接收端绑定持久化：与 MCP 共用同仓 lib 下的 CJS 版（setup_receiving_endpoint 落盘，本文件启动时读回）。
// 否则本 Hook 独立进程读不到 MCP 进程内存里的绑定，且 MCP 进程重启后也丢 —— 详见 lib/receiving-endpoint.cjs。
const { loadReceivingEndpoint } = require(
  path.resolve(__dirname, '..', '..', 'lib', 'receiving-endpoint.cjs'),
);

const NODE = process.execPath;
const DEFAULT_CHANNEL = 'ch-workbuddy';
const MAX_TEXT = 300;
// 进程自杀兜底：宿主已收到 {async:true} 就放行了，但本进程不能永远挂着。
// 现在所有分支都只做「最多一次推送」或「只写一个文件」，12s 绰绰有余 ——
// 再没有「等静默窗口」那种要单独放宽的长活。
const GUARD_MS = 12000;

// 定位 warroom-webhook.cjs（MCP 同款脚本，支持 --notify 一次性推送）。
// 逐个候选探测，别写死相对层级 —— 本文件放在 .workbuddy/hooks/，
// 而脚本在仓库的 mcp/ 下，想当然的 __dirname 拼接会落到不存在的文件。
function locateCli() {
  const candidates = [
    process.env.WARROOM_WEBHOOK_CLI || '',
    path.resolve(__dirname, '..', '..', 'mcp', 'warroom-webhook.cjs'), // 仓库内：<repo>/.workbuddy/hooks → <repo>/mcp
    path.resolve(__dirname, 'warroom-webhook.cjs'),                    // 同目录副本
    path.resolve(__dirname, '..', 'mcp', 'warroom-webhook.cjs'),
  ].filter(Boolean);
  for (const c of candidates) {
    try {
      if (fs.existsSync(c)) return c;
    } catch {
      /* 忽略 */
    }
  }
  return candidates[0];
}

const CLI = locateCli();

// ---------- 宿主判别（决定要不要往 stdout 写异步握手）----------
// 🔴 默认 'workbuddy' —— 不传参数时行为与既有配置**逐字不变**。
//   只有显式 `--host=claude-code` 才改行为：Claude Code 把 hook 的 stdout 注入下一轮上下文，
//   而它的异步靠配置 `"async": true`，不需要（也不该要）我们的 stdout 握手。
const HOST = (() => {
  const a = process.argv.find((v) => v.startsWith('--host='));
  const v = a ? a.slice('--host='.length).trim().toLowerCase() : '';
  return v || 'workbuddy';
})();
// 只有 WorkBuddy 认 stdout 上的 {async:true}；其他宿主（Claude Code / Copilot CLI / Cursor…）一律闭嘴。
const STDOUT_ASYNC_HANDSHAKE = HOST === 'workbuddy';

// ---------- 最早放行：只要宿主一给 stdin，就先吐出 {async:true} 把自己摘出去 ----------
// （Stop 钩子阻塞的是「本轮回答收尾」，必须零等待；推送在后台跑。）
let detached = false;
function detach() {
  if (detached) return;
  detached = true;
  if (!STDOUT_ASYNC_HANDSHAKE) return; // 非 WorkBuddy：stdout 会被当上下文注入，绝不写
  try {
    process.stdout.write(JSON.stringify({ async: true, asyncTimeout: 20000 }) + '\n');
  } catch {
    /* 忽略 */
  }
}

// 自杀兜底计时器（非 unref 会拖住进程；unref 后只要还有 pending 的子进程/sleep 就仍活着）。
let guardTimer = null;
function armGuard(ms) {
  if (guardTimer) clearTimeout(guardTimer);
  guardTimer = setTimeout(() => process.exit(0), ms);
  guardTimer.unref?.();
}

function log(msg) {
  const line = '[warroom-hook] ' + msg + '\n';
  process.stderr.write(line);
  fileLog(line); // stderr 没人看得到 —— 同时落一份日志，事后可查
}

// ---------- 日志落盘 ----------
// 🔴 为什么必须落盘：hook 的 stderr 只有宿主引擎收，人看不到。
// 推送失败（地址错 / 密钥错 / 端口没开）此前**完全静默** —— 大屏上什么都不出现，
// 而人只会以为「它就是没推」，无法与「推了但被去重」区分。见 docs/operations.md。
const LOG_FILE = (() => {
  // 测试隔离用：允许把日志也指到别处（如模拟器/自检的临时目录）。
  // 不设该 env 时行为完全不变（仍旧 ~/.workbuddy/logs/warroom-hook.log）。
  if (process.env.WARROOM_HOOK_LOG) return process.env.WARROOM_HOOK_LOG;
  const home = process.env.USERPROFILE || process.env.HOME || '';
  return home ? path.join(home, '.workbuddy', 'logs', 'warroom-hook.log') : '';
})();
const LOG_MAX_BYTES = 256 * 1024;

function fileLog(line) {
  if (!LOG_FILE) return;
  try {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    let st = null;
    try {
      st = fs.statSync(LOG_FILE);
    } catch {
      /* 首次写 */
    }
    if (st && st.size > LOG_MAX_BYTES) {
      // 简单轮转：留最后 500 行，别引第三方依赖
      const kept = fs.readFileSync(LOG_FILE, 'utf8').split('\n').slice(-500).join('\n');
      fs.writeFileSync(LOG_FILE, kept);
    }
    // 调用方可能传入被截断的片段（末尾无换行）→ 统一补一个，避免几行粘成一行
    fs.appendFileSync(LOG_FILE, new Date().toISOString() + ' ' + String(line).replace(/\n+$/, '') + '\n');
  } catch {
    /* 日志失败绝不能影响推送 */
  }
}

// ---------- 连接参数 ----------
// 🔴 引擎**不给 hook 注入任何 env**（settings.json 没有 env 段，本机 User/Machine 级也没有
// WARROOM_*）→ 旧实现回落 `http://localhost:3500`，而那是本机 dev 端口、平时并不常开
// → 9 个事件的推送**全部静默失败**，大屏上只剩 agent 手动推的通知。
// 现改为：process.env 优先（临时覆盖用），否则读 `~/.workbuddy/mcp.json` 里
// warroom-webhook 的 env —— 那是**已经配好、唯一一份**的连接参数（MCP 自己也用它），
// 不再要求为了 hook 单独再维护一处配置。
function mcpConfigPath() {
  const home = process.env.USERPROFILE || process.env.HOME || '';
  const cands = [process.env.WARROOM_MCP_CONFIG || '', home ? path.join(home, '.workbuddy', 'mcp.json') : ''];
  for (const c of cands) {
    if (!c) continue;
    try {
      if (fs.existsSync(c)) return c;
    } catch {
      /* 忽略 */
    }
  }
  return '';
}

let CONN = null;

/** 从 mcp.json 的 `server.url` 推导基址 —— OAuth 形态的连接器**只有 url、没有 env**。
 *  只取 origin：`https://wr.aiwho.cn/api/v2/mcp` → `https://wr.aiwho.cn`。
 *  带模板变量（`${VAR}`）的直接放弃：没展开的串拼出来的地址必然不通，不如老实落兜底并在日志里说清。
 */
function baseFromMcpUrl(raw) {
  const s = String(raw || '').trim();
  if (!s || s.includes('${')) return '';
  try {
    const u = new URL(s);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return '';
    return u.origin;
  } catch {
    return '';
  }
}

function connection() {
  if (CONN) return CONN;
  CONN = { base: '', key: '', name: '', channel: '', tenant: '', from: '（未找到配置）', explicit: false };
  // 1) mcp.json 声明的基线（MCP 自己也用这份 env）
  const p = mcpConfigPath();
  if (p) {
    try {
      const j = JSON.parse(fs.readFileSync(p, 'utf8'));
      const srv = (j && j.mcpServers && j.mcpServers['warroom-webhook']) || {};
      const e = srv.env || {};
      // 基线有两种形态，都要认：
      //   ① 旧 stdio 配置：连接参数写在 env 里（WARROOM_API_BASE）；
      //   ② OAuth 形态的连接器（本包市场版 mcp.json）：**只有 url、没有 env**。
      //      只读 env 的话，装连接器的机器上 hook 拿不到 base → 落 localhost:3500
      //      → 9 个事件全部静默失败。连接器装在哪，hook 就该推到哪，所以 url 的 origin 即基线。
      CONN.base = String(e.WARROOM_API_BASE || '') || baseFromMcpUrl(srv.url);
      CONN.key = String(e.WARROOM_WEBHOOK_KEY || '');
      CONN.name = String(e.WARROOM_AI_NAME || '');
      CONN.channel = String(e.WARROOM_CHANNEL || '');
      CONN.from = p + (e.WARROOM_API_BASE ? '' : CONN.base ? '（base 由 url 推导）' : '');
      if (CONN.base) CONN.explicit = true;
    } catch (e) {
      log('读 mcp.json 失败（回落 env / 默认地址）：' + e.message);
    }
  }
  // 2) 持久化接收端（setup_receiving_endpoint 落盘，比 mcp.json 基线更贴近用户最近一次设置）→ 覆盖基线
  //    🔑 关键修复：Hook 是独立进程，读不到 MCP 内存里的绑定；且 MCP 重启后那份内存也丢。
  //    🔴 2026-10-23：状态文件按 AI 名字隔离（receiving-endpoint.<scope>.json）。Hook 是宿主 spawn 的
  //       独立进程，mcp.json 里 server 的 env **不会**注入到它 —— 所以必须把刚从 mcp.json 读到的
  //       WARROOM_AI_NAME 补进 env，否则它会去读别人的（本机实测：读到 QClaw 写的工位 qclaw）。
  if (CONN.name && !process.env.WARROOM_AI_NAME) process.env.WARROOM_AI_NAME = CONN.name;
  const ep = loadReceivingEndpoint();
  if (ep) {
    CONN.base = ep.base;
    CONN.key = ep.key || CONN.key;
    CONN.channel = ep.channelId || CONN.channel;
    // 🔴 租户段必须一起带：V2 服务端只注册 /api/v2/webhook/<租户>/<工位>，
    //    少租户段会回落 V1 单段 /api/v1/webhook/<工位> → 生产直接 404。
    CONN.tenant = ep.tenantId || CONN.tenant || '';
    CONN.from = (CONN.from ? CONN.from + ' + ' : '') + '持久化接收端(' + ep.base + ')';
    CONN.explicit = true;
  }
  // 3) 进程 env 优先（临时覆盖，如本机 dev）
  if (process.env.WARROOM_API_BASE) {
    CONN.base = process.env.WARROOM_API_BASE;
    CONN.from = 'env（临时覆盖）';
    CONN.explicit = true;
  }
  if (process.env.WARROOM_WEBHOOK_KEY) CONN.key = process.env.WARROOM_WEBHOOK_KEY;
  if (process.env.WARROOM_CHANNEL) CONN.channel = process.env.WARROOM_CHANNEL;
  if (process.env.WARROOM_AI_NAME) CONN.name = process.env.WARROOM_AI_NAME;
  if (!CONN.base) CONN.base = 'http://localhost:3500';
  if (!CONN.channel) CONN.channel = DEFAULT_CHANNEL;
  return CONN;
}

// ---------- 自检：node warroom-hook.cjs --doctor ----------
// hook 的失败是**静默**的（stderr 只有引擎收），所以必须留一条能主动问的通道。
function runDoctor() {
  const conn = connection();
  console.log('CLI 脚本        : ' + CLI + (fs.existsSync(CLI) ? '  ✓' : '  ✗ 不存在'));
  console.log('宿主(--host)    : ' + HOST + (STDOUT_ASYNC_HANDSHAKE ? '（stdout 会发 {async:true} 握手）' : '（stdout 保持沉默，异步交给宿主配置）'));
  console.log('配置来源        : ' + conn.from);
  console.log('推送目标        : ' + conn.base);
  console.log(
    '密钥            : ' +
      (conn.key ? conn.key.slice(0, 10) + '…' + conn.key.slice(-4) : '⚠ 未设（回落公开演示值 → 生产必 401）'),
  );
  console.log('AI 名(--source) : ' + (conn.name || '(未设 → WorkBuddy)'));
  console.log('日志文件        : ' + (LOG_FILE || '(不可用)'));
  return fetch(conn.base + '/healthz')
    .then(async (r) => {
      console.log('探活 /healthz   : ' + r.status + ' ' + (await r.text()).slice(0, 120));
    })
    .catch((e) => {
      console.log('探活 /healthz   : ✗ ' + e.message + '  → 后端不可达，推送必失败');
    })
    .then(() => {
      if (process.argv.includes('--no-push')) return undefined;
      return push([
        '--title', '🔧 Hook 自检',
        '--summary', '来自 warroom-hook.cjs --doctor：验证 hook 自己的连接参数与密钥可用（可忽略本条）',
        '--level', 'info',
        '--channel', conn.channel || DEFAULT_CHANNEL,
        '--source', conn.name || 'WorkBuddy',
        '--external-id', 'hook:doctor:' + Date.now().toString(36),
      ]).then((code) => console.log('试推一条        : ' + (code === 0 ? '✓ 成功' : '✗ 失败 exit=' + code)));
    })
    .then(() => process.exit(0));
}

// ---------- 自检：node warroom-hook.cjs --turn-doctor [N] [M] ----------
// 演一遍真实的一轮：N 条 TaskCreated → M 条 TaskCompleted → 1 条 Stop（各自独立进程、各自喂 stdin）。
// 全程 dry-run（只把「本该推什么」记到文件），**不联网、不碰真后端**，所以可以随时跑。
// 判据是三条硬数字（默认模式：新建即时、完成合并）：
//   ① 建完待办后已推送 N 次（每条新建即时各占 1 条）；② M 条完成入队、0 次即时推（完成合并）；
//   ③ 整轮总次数 == N + 1，且收尾那条正文里有「完成 M 项」（新建已各自即时上屏）。
//   （逃生舱 WARROOM_HOOK_CREATED_EACH=0 → ① 退化为 0 次、③ 退化为 M+1 且收尾含「新建任务计划 N 项」；
//      WARROOM_HOOK_DONE_EACH=1 → 完成逐条，② 退化为 M 次、③ 相应 +M。）
// ⚠️ 若整个命令跑在**沙箱**里，孙进程（这里的子进程的子进程）可能被拦掉文件写入 →
//    表现为「整轮推送 0 次」的**假红**。判定：看命令回显里有没有 sandbox bypassed 提示；
//    把同一条命令放行重跑即可，别去改合并逻辑（10-02 踩过）。
async function runTurnDoctor() {
  const idx = process.argv.indexOf('--turn-doctor');
  const n = Math.max(1, Number(process.argv[idx + 1] || 5) || 5);
  const m = Math.max(1, Number(process.argv[idx + 2] || 3) || 3);
  const root = stateRoot();
  console.log('队列目录        : ' + (root || '⚠ 候选目录全部不可写 → 待办会回落逐条单发'));
  console.log(
    '目录候选        : ' + STATE_ROOT_CANDS.map((c) => c + (c === root ? ' ← 选中' : '')).join('  |  '),
  );
  console.log('推送目标        : ' + connection().base + '（本自检不会真的推）');
  if (!root) {
    console.log('✗ 队列目录不可写，无法自检');
    process.exit(0);
    return;
  }
  const sid = 'doctor' + Date.now().toString(36);
  const logFile = path.join(root, '.dryrun-' + sid + '.ndjson');
  const childEnv = {
    ...process.env,
    WARROOM_HOOK_DRY_RUN: '1',
    WARROOM_HOOK_DRYRUN_LOG: logFile,
    WARROOM_HOOK_STATE_DIR: root,
  };
  const runOne = (payload) =>
    new Promise((resolve) => {
      const c = spawn(NODE, [__filename], { env: childEnv, stdio: ['pipe', 'ignore', 'ignore'], windowsHide: true });
      const t = setTimeout(() => {
        try {
          c.kill();
        } catch {
          /* 忽略 */
        }
        resolve(-1);
      }, 10000);
      c.on('error', () => {
        clearTimeout(t);
        resolve(-1);
      });
      c.on('exit', (code) => {
        clearTimeout(t);
        // 🔴 10-02 修：Windows 上子进程的 `exit` 事件可能早于 dry-run 日志的
        //    `appendFileSync` 真正刷盘（那个写在 push() 的 Promise 微任务里）。
        //    实测症状：`--turn-doctor` 报「整轮推送总次数 0（期望 1）」而**真机推送完全正常**
        //    —— 差点被误判成合并功能坏了、差点回退成逐条。给 120ms 让它落盘。
        setTimeout(() => resolve(code), 120);
      });
      c.stdin.end(JSON.stringify(payload));
    });
  const readCalls = () => {
    try {
      return fs
        .readFileSync(logFile, 'utf8')
        .split('\n')
        .filter(Boolean)
        .map((l) => {
          try {
            return JSON.parse(l);
          } catch {
            return null;
          }
        })
        .filter(Boolean);
    } catch {
      return [];
    }
  };
  // 🔴 10-02 修：Windows 上子进程 `exit` 与 dry-run 日志刷盘不同步（实测 Stop 从收尾到
  //    push 落盘可差 2.5s，而 `exit` 先到）。先前用「读不够就等」的轮询，结果**随机失败**：
  //    同一份代码连跑三次给出 0 / 1 / 0 —— 极易误判成「合并把消息弄丢了」而回退成逐条。
  //    现在改成**等到内容稳定**（连续两次读到同样多的行才算数），最多等 ~6s。
  //    这样返回的一定是最终态，判据不会再抖。
  const readCallsSettled = async (timeoutMs = 6000) => {
    const t0 = Date.now();
    let prev = -1;
    let stable = 0;
    for (;;) {
      const got = readCalls();
      if (got.length > 0 && got.length === prev) {
        if (++stable >= 2) return got;
      } else {
        stable = 0;
      }
      prev = got.length;
      if (Date.now() - t0 > timeoutMs) return got;
      await new Promise((r) => setTimeout(r, 150));
    }
  };
  const argOf = (a, k) => {
    const i = a.indexOf(k);
    return i >= 0 ? a[i + 1] : '';
  };

  console.log('--- 第 1 步：' + n + ' 条 TaskCreated（各起一个进程，模拟规划一次建一批）---');
  for (let i = 1; i <= n; i++) {
    await runOne({ hook_event_name: 'TaskCreated', session_id: sid, task_subject: '演示待办 ' + i, task_id: 't' + i });
  }
  const eachCreated = process.env.WARROOM_HOOK_CREATED_EACH !== '0';
  const afterTasks = readCalls().length;
  const queued = listItems(sid).length;
  console.log('  新建已入队      : ' + queued + ' 条（期望 ' + (eachCreated ? '0 —— 新建即时不自入队' : n) + '）');
  console.log('  此刻已推送      : ' + afterTasks + ' 条（期望 ' + (eachCreated ? n + ' —— 新建即时各占 1 条' : '0 —— 新建入队不自推') + '）');

  console.log('--- 第 2 步：' + m + ' 条 TaskCompleted（10-02 改判：也入队合并）---');
  // 🔴 用**用户实测的真实标题**做样本（含「新建任务计划：1.」这类前缀+序号），
  //    顺带验证 cleanSubject 是否把前缀与序号剥干净 —— 这正是 TTS 念三遍的根因。
  const REAL_TITLES = [
    '新建任务计划：1.在 hook 里实现待办事件批量合并',
    '新建任务计划：2.用桩 CLI 做隔离验证 + 真机 E2E',
    '新建任务计划：3.更新文档与备忘',
    '新建任务计划：4.整理项目 MEMORY.md 并归档超期日志',
    '新建任务计划：5.提交并推送 main',
  ];
  for (let i = 1; i <= m; i++) {
    await runOne({
      hook_event_name: 'TaskCompleted',
      session_id: sid,
      task_subject: REAL_TITLES[i - 1] || '演示完成 ' + i,
      task_id: 'd' + i,
    });
  }
  const afterDone = readCalls().length; // 第 2 步后累计已推送（含新建即时 + 完成即时）
  // 期望值跟随模式：逃生舱（WARROOM_HOOK_DONE_EACH=1）下完成回到逐条。
  // 🔴 直读env 而不是引用文件后半部的 `const EACH_DONE` —— 本函数声明在文件上半部，
  //    那个 const 还没初始化（TDZ），引用会让整段抛错被吞 → 判据恒假、真机却是好的。
  //    全文只在此处 + 下方判据处各定义一次同名局部常量，作用域内自洽。
  const eachDone = process.env.WARROOM_HOOK_DONE_EACH === '1';
  const expCreatedPush = eachCreated ? n : 0;            // 新建即时推几条
  const expDonePush = eachDone ? m : 0;                  // 完成即时推几条
  const turnEndCreated = !eachCreated && n > 0 ? 1 : 0;  // 回落模式下新建收尾贡献 1 条
  const turnEndDone = !eachDone && m > 0 ? 1 : 0;        // 回落模式下完成收尾贡献 1 条
  // 双即时（两者都不回落）→ 队列空 → 收尾生成 1 条 plain（本轮结束）；否则不生成。
  const expCalls = expCreatedPush + expDonePush + turnEndCreated + turnEndDone + (turnEndCreated === 0 && turnEndDone === 0 ? 1 : 0);
  console.log(
    '  完成已推送      : ' + (afterDone - afterTasks) + ' 条（期望 ' + (eachDone ? m + ' —— 逃生舱：完成逐条' : '0 —— 完成已改为入队') + '）',
  );
  const expQueue = (eachCreated ? 0 : n) + (eachDone ? 0 : m);
  console.log(
    '  队列累计        : ' + listItems(sid).length + ' 条（期望 ' + expQueue +
      (eachCreated ? '，新建即时不入队' : ' = ' + n + ' 新建入队') +
      (eachDone ? (eachCreated ? '' : '，') + '完成不入队' : ' + ' + m + ' 完成入队') + '）',
  );

  console.log('--- 第 3 步：1 条 Stop（本轮收尾）---');
  await runOne({ hook_event_name: 'Stop', session_id: sid });

  // 🔴 10-02 修：必须**在等够之后再取内容**。Windows 上子进程 `exit` 事件与 dry-run 日志的
  //    文件刷盘不同步（实测 Stop 子进程从收尾到 push 落盘可差 2.5s），先前版本在这里
  //    `await readCallsSettled()` 之后又重新 `readFileSync`，两次读之间仍可能读到半截内容
  //    → 症状：判据随机失败（同一份代码连跑三次给出 0 / 1 / 0），而**真机推送完全正常**。
  //    现在：一次等到满足条件，**用同一份结果**做全部判据，不再二次读盘。
  const calls = await readCallsSettled();
  console.log('--- 结果 ---');
  console.log('整轮推送总次数  : ' + calls.length + '（期望 ' + expCalls + ' —— ' + (eachCreated ? '新建即时 ' + n + ' 条' : '新建并入收尾 1 条') + ' + ' + (eachDone ? '完成逐条 ' + m + ' 条' : '完成收尾 1 条') + '）');
  calls.forEach((a, i) =>
    console.log(
      '  #' + (i + 1) + ' 标题=' + JSON.stringify(argOf(a, '--title') || '(任务完成通知·无自定义标题)') +
      ' 摘要=' + JSON.stringify(clip(argOf(a, '--summary'), 300)),
    ),
  );
  console.log('残留队列文件    : ' + listItems(sid).length + '（期望 0）');
  // 🔴 清洗逻辑用一份**等价本地实现**（stripTitle），不引用文件后半部的 `cleanSubject` ——
  //    函数声明会提升、const 不会；`cleanSubject` 虽是 function 声明，但它内部无外部依赖，
  //    引用是安全的，这里仍用本地实现是为了让自检判据与被测逻辑**完全解耦**：
  //    万一 cleanSubject 本身坏了，自检要能独立发现（自检不能自己验自己）。
  const stripTitle = (s) => {
    let t = String(s || '').trim();
    for (let i = 0; i < 3; i++) {
      const before = t;
      t = t.replace(
        /^(?:[^\p{L}\p{N}]{0,3}\s*)?(?:新建任务计划|已完成任务计划|新建待办|待办完成|完成任务|新建|创建|新增|完成|待办|任务|todo)\s*[:：]\s*/iu,
        '',
      );
      if (t === before) break;
    }
    return t.replace(/^\s*(?:[（(]?\d{1,2}[）).、::]|[③⑴❶]|[-•*]\s)\s*/, '')
      .replace(/^[\s:：.、-]+/, '')
      .trim();
  };
  const allSummary = calls.map((c) => argOf(c, '--summary') || '').join('\n');
  const mergedCreated = new RegExp('(新建任务计划|新建待办|新建) ' + n + ' 项').test(allSummary);
  // 🔴 判据必须**跟随模式**：`WARROOM_HOOK_DONE_EACH=1` 时完成回到逐条，
  //    收尾正文不该出现「任务计划 N 项」—— 否则逃生舱一用自检必假红。
  const mergedDone = eachDone
    ? !new RegExp('任务计划 ' + m + ' 项').test(allSummary)
    : new RegExp('任务计划 ' + m + ' 项').test(allSummary);
  // 新建即时：默认应有 n 条标题以「📋 新建任务计划」开头；回落模式则收尾含「新建任务计划 N 项」。
  const createdTitles = calls.filter((c) => String(argOf(c, '--title') || '').startsWith('📋 新建任务计划')).length;
  const createdOk = eachCreated ? createdTitles === n : mergedCreated;
  // 🔴 判据：正文里**不得**残留「新建任务计划：」前缀或「1.」序号 —— 残留即 TTS 会念出来。
  const noPrefix = !/新建任务计划\s*[:：]\s*\d|已完成任务计划\s*[:：]/.test(allSummary);
  const cleaned = stripTitle(REAL_TITLES[0]) === '在 hook 里实现待办事件批量合并';
  const ok =
    afterTasks === expCreatedPush &&
    afterDone === expCreatedPush + expDonePush &&
    calls.length === expCalls &&
    createdOk && mergedDone && noPrefix && cleaned;
  console.log('  模式            : ' + (eachCreated ? '默认 · 新建即时' : '回落 · 新建并入收尾') + (eachDone ? ' + 完成逐条' : ' + 完成合并'));
  console.log('  标题清洗生效    : ' + (cleaned ? '是' : '否 ❌'));
  console.log('  正文无前缀残留  : ' + (noPrefix ? '是' : '否 ❌'));
  console.log(
    ok
      ? eachDone
        ? (eachCreated
            ? '✓ 完成逐条(' + m + ' 条) + 新建即时(' + n + ' 条) 各占一条'
            : '✓ 完成逐条(' + m + ' 条) + 新建并入收尾(' + n + ' 项) 各占一条')
        : (eachCreated
            ? '✓ 新建即时(' + n + ' 条) + 完成合并成 1 条（共 ' + (n + 1) + ' 条推送）+ 标题已清洗 ⇒ TTS 不念前缀'
            : '✓ 新建并收尾(' + n + ' 项) + 完成合并(' + m + ' 项) 共 1 条 + 标题已清洗')
      : '✗ 未达标：看上面几个数字',
  );

  // 清理：只用本文件已在用的 unlink/rmdir（不用 rm -rf，Windows 沙箱下它会挂死）
  for (const f of listItems(sid)) {
    try {
      fs.unlinkSync(f.file);
    } catch {
      /* 忽略 */
    }
  }
  cleanupSessDir(sid);
  try {
    fs.unlinkSync(logFile);
  } catch {
    /* 忽略 */
  }
  process.exit(ok ? 0 : 1);
}

// ⚠ 入口分发挪到**文件末尾**了 —— 它依赖的 STATE_ROOT / BATCH_* 都是 `const`，
//    在这儿执行会踩 TDZ（Cannot access 'STATE_ROOT' before initialization）。

function clip(s, n) {
  const t = String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
  return t.length > n ? t.slice(0, n - 1) + '…' : t;
}

// 从会话记录里回捞「本轮助手的最终答复」—— Stop 事件本身不携带任何正文。
function lastAssistantText(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return '';
  let lines;
  try {
    lines = fs.readFileSync(transcriptPath, 'utf8').split(/\r?\n/);
  } catch {
    return '';
  }
  // 从尾部往前找第一条 assistant 消息
  for (let i = lines.length - 1; i >= 0 && i >= lines.length - 400; i--) {
    const raw = lines[i].trim();
    if (!raw) continue;
    let rec;
    try {
      rec = JSON.parse(raw);
    } catch {
      continue;
    }
    const role = rec.role || rec.type || (rec.message && rec.message.role);
    if (role !== 'assistant') continue;
    const msg = rec.message || rec;
    const c = msg.content;
    if (typeof c === 'string') return c;
    if (Array.isArray(c)) {
      const texts = c
        .map((p) => (typeof p === 'string' ? p : p && p.type === 'text' ? p.text : ''))
        .filter(Boolean);
      if (texts.length) return texts.join('\n');
    }
  }
  return '';
}

function push(args) {
  // dry-run：自检（--turn-doctor）用。只把「本该推什么」记一行，绝不联网、绝不碰真后端。
  if (DRY_RUN) {
    try {
      if (DRYRUN_LOG) fs.appendFileSync(DRYRUN_LOG, JSON.stringify(args) + '\n');
    } catch {
      /* 忽略 */
    }
    return Promise.resolve(0);
  }
  return new Promise((resolve) => {
    if (!fs.existsSync(CLI)) {
      log('找不到 warroom-webhook.cjs，跳过推送。已探测：' + CLI);
      return resolve(-1);
    }
    let done = false;
    const conn = connection();
    let out = '';
    const finish = (code) => {
      if (done) return;
      done = true;
      clearTimeout(killTimer);
      const tail = out.replace(/\s+/g, ' ').trim().slice(0, 200);
      fileLog((code === 0 ? '✓ ' : '✗ exit=' + code + ' ') + conn.base + ' :: ' + (tail || '(无输出)'));
      resolve(code);
    };
    const child = spawn(NODE, [CLI, '--notify', ...args], {
      cwd: path.dirname(CLI),
      env: {
        ...process.env,
        WARROOM_API_BASE: conn.base,
        // 显式给值（空串也写）：CLI 只有在没有 WARROOM_API_BASE 时才去读持久化接收端拿租户段，
        // 而这里必然给了 base —— 不显式传就会丢掉租户段，退化成 V1 单段（V2 上 404）。
        WARROOM_TENANT: conn.tenant || '',
        ...(conn.key ? { WARROOM_WEBHOOK_KEY: conn.key } : {}),
        ...(conn.name ? { WARROOM_AI_NAME: conn.name } : {}),
      },
      // stdout 必须留给宿主的 async 探针：子进程的 stdout 由本进程**接管并转发到 stderr**，
      // 绝不混进 hook 的 stdout —— 旧写法 'inherit' 会把 CLI 的「✅ 已推送…」直接写进宿主读的管道。
      stdio: ['ignore', 'pipe', 'inherit'],
      windowsHide: true,
    });
    if (child.stdout)
      child.stdout.on('data', (d) => {
        out += d;
        process.stderr.write(d);
      });
    child.on('error', (e) => {
      log('spawn 失败：' + e.message);
      finish(-1);
    });
    child.on('exit', (code) => finish(code));
    const killTimer = setTimeout(() => {
      try {
        child.kill();
      } catch {
        /* 忽略 */
      }
      finish(-1);
    }, 10000);
  });
}

// ---------- 待办类事件：新建即时、完成合并 ----------
// 完整设计见文件头「本轮聚合」一节。
// 🔴 10-04 用户反馈：10-02 把 TaskCreated 也并入收尾那条，导致「新建」与「完成」挤在同一时间戳，
//    看着像「完成全部任务后才推新建」。现改为 **TaskCreated 即时推送**（创建时刻立即上屏）；
//    TaskCompleted 维持 10-02 的合并口径（避免一轮连完成 3 条 → 大屏刷屏 + TTS 念 3 遍）。
// 🔴 下面两个常量**必须声明在自检函数之前**（自检在文件上半部，靠 --turn-doctor 进入）：
//    放后面会踩 TDZ —— `Cannot access 'EACH_DONE' before initialization` 被 catch 吞掉，
//    症状 = 自检「整轮推送总次数」恒为 0、判据恒假，但**真机推送其实完全正常**（10-02 踩过）。
// 🔴 10-04：新建默认即时；逃生舱 `WARROOM_HOOK_CREATED_EACH=0` 回落回「入队、由收尾合并」（规划 5~7 条防刷屏）。
const EACH_CREATED = process.env.WARROOM_HOOK_CREATED_EACH !== '0';
// 🔴 10-02 用户改判：TaskCompleted **也入队合并**（初版逐条，实测一轮连完成 3 条 → TTS 念 3 遍）。
//    逃生舱：设 WARROOM_HOOK_DONE_EACH=1 即恢复「完成逐条上屏」，无需改代码。
const EACH_DONE = process.env.WARROOM_HOOK_DONE_EACH === '1';
// 「收尾事件」= 一轮/一个会话真正结束的时刻。只有它们会把整轮攒下的待办并进自己那一条。
const TURN_END_EVENTS = new Set(['Stop', 'StopFailure', 'SessionEnd']);
const BATCH_LIST_MAX = 6; // 正文里逐条列几项，其余概括
// 兜底冲货阈值：Stop **并非每轮都触发**（10-02 实测 7 次提问只等到 3 次 Stop，被中断的轮次更没有），
// 所以队列里躺够这么久的陈货要有人带走发成一条。
// 🔴 10-02 调整：① 触发点收窄到「仅 `UserPromptSubmit`」（见主流程 ⓪）；② 阈值 20s → 10min。
//    ①是治本的：原先「任何非收尾事件开头都冲」+ 20s，而一轮真实要跑 2~20 分钟
//    （实测 16:00:45 建 5 条 → 16:22:27 才 Stop）→ 下一轮**第一个**事件就把上一轮的待办
//    当陈货抢跑冲掉，抢在收尾之前，消息与轮次彻底对不上号（16:03:04 抓到现场）。
//    ②是补漏：触发点收窄后，阈值的意义变成「同一轮内用户**连问**时，别把刚建的待办误当陈货」。
//    20s 太短（用户一句没跑完又追一句，间隔就超过 20s）→ 同样会误冲自己这一轮。
//    10min 足够宽松：真被中断的上一轮，下一次开口一定是「上一轮已经结束之后」，远超 10min。
//    ⚠️ 阈值只影响「等多久才算陈货」，**不影响**何时去冲 —— 何时冲由上面的事件过滤决定。
const STALE_FLUSH_MS = Number(process.env.WARROOM_HOOK_STALE_MS || 600000);
// 「需要你操作」类（Notification / PermissionRequest）的幂等键**必须带短时间桶**。
// 🔴 为什么：Notification 的 message 是**引擎固定文案**，纯指纹会让同一会话里的每一次
//    permission_prompt 都命中第一条 —— 而后端去重命中**不更新正文**（server/src/lib/dedupe.ts）
//    → 大屏上永远只有最早那条，表现和「被跳过」一模一样。10-02 实测：permission_prompt 推 13 次、
//    其中 6 次 `created:false` 且 id 恒为同一条；agent_needs_input / elicitation_dialog 同理。
//    桶取 5s：足以覆盖引擎重推（实测重推间隔 <1s，不因此多出重复条目），
//    又不会把用户几分钟内被连问的两次权限并掉 —— 「要人当场动手」的消息宁可重复也不可漏。
const NOTIFY_BUCKET_MS = Number(process.env.WARROOM_NOTIFY_BUCKET_MS || 5000);
// 自检用：dry-run 只记录「本该推什么」到文件，不联网（见 --turn-doctor）。
const DRY_RUN = !!process.env.WARROOM_HOOK_DRY_RUN;
const DRYRUN_LOG = process.env.WARROOM_HOOK_DRYRUN_LOG || '';
// 队列目录：与日志同处（同一个「已经能写」的位置，不必再申请一处写权限）。
// ⚠️ 但要**探测**而不是假定可写：宿主/沙箱/只读挂载都可能让首选目录写不进去，
//    而写不进去的后果不是「不推」，是**静默退化成逐条单发** —— 又回到刷屏老路。
//    所以按序探测候选目录（探到了就记住，同一环境里所有 hook 进程得出同一答案）。
//    自检见 `--turn-doctor`：它会直接打印最终选中的目录。
const STATE_ROOT_CANDS = [
  process.env.WARROOM_HOOK_STATE_DIR || '', // 自检隔离用：把队列指到临时目录
  path.join(LOG_FILE ? path.dirname(LOG_FILE) : os.tmpdir(), 'warroom-hook-batch'),
  path.join(os.tmpdir(), 'warroom-hook-batch'),
].filter(Boolean);
let ROOT = undefined; // undefined = 还没探测；null = 哪儿都写不了
function stateRoot() {
  if (ROOT !== undefined) return ROOT;
  ROOT = null;
  for (const c of STATE_ROOT_CANDS) {
    try {
      fs.mkdirSync(c, { recursive: true });
      const probe = path.join(c, '.writable-' + process.pid);
      fs.writeFileSync(probe, '');
      fs.unlinkSync(probe);
      ROOT = c;
      break;
    } catch {
      /* 换下一个候选 */
    }
  }
  return ROOT;
}

function safeSid(sid) {
  const s = String(sid || '').replace(/[^A-Za-z0-9_-]/g, '').slice(0, 64);
  return s || 'nosession';
}
function sessDir(sid) {
  const root = stateRoot();
  return root ? path.join(root, safeSid(sid)) : '';
}
// 一条事件 = 一个独立文件（文件名带 13 位毫秒前缀 → 天然按时间排序）。
// 不用「一个文件里存数组」：并发写会读-改-写互相覆盖，而独立文件是**只增不改**，天然无锁安全。
// 🔑 这也是为什么整套机制**不需要锁**：入队是只增不改，出队由「收尾事件」这个天然唯一的时间点负责，
//    没有「谁是合并器」要争 —— 不依赖任何时序假设，就不会出现「抢不到锁就退化成逐条刷屏」。
function enqueueTask(sid, item) {
  const d = sessDir(sid);
  if (!d) return false; // 没有可写目录 → 上游回落单发
  try {
    fs.mkdirSync(d, { recursive: true });
    const name =
      String(Date.now()).padStart(13, '0') + '-' + process.pid + '-' + Math.random().toString(36).slice(2, 8) + '.json';
    const p = path.join(d, name);
    fs.writeFileSync(p + '.tmp', JSON.stringify(item), 'utf8');
    fs.renameSync(p + '.tmp', p); // 原子落位：读的人不会看到半截 JSON
    return true;
  } catch (e) {
    log('待办入队失败（' + e.message + '），回落立即单发');
    return false;
  }
}

function listItems(sid) {
  const d = sessDir(sid);
  if (!d) return [];
  let names;
  try {
    names = fs.readdirSync(d);
  } catch {
    return []; // 目录不存在 = 空队列
  }
  const out = [];
  for (const n of names) {
    if (!n.endsWith('.json')) continue; // 跳过 .tmp / .lock
    const file = path.join(d, n);
    try {
      out.push({ file, name: n, mtime: fs.statSync(file).mtimeMs });
    } catch {
      /* 已被别人取走 */
    }
  }
  out.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)); // 13 位毫秒前缀 → 按时间
  return out;
}

// 取走队列条目（读完即删）。
// `olderThanMs` 给定时只取比它更老的，其余留在队列里等收尾事件 —— 兜底路径专用。
// 🔴 删文件而不是打「已读」标记：文件名就是唯一状态，不留游标就不会有游标错位。
function drainTasks(sid, olderThanMs) {
  const out = [];
  for (const f of listItems(sid)) {
    if (olderThanMs !== undefined && Date.now() - f.mtime < olderThanMs) continue;
    try {
      const rec = JSON.parse(fs.readFileSync(f.file, 'utf8'));
      if (rec && typeof rec === 'object' && rec.event) out.push(rec);
    } catch {
      /* 坏文件丢弃：别让一条脏数据卡住整批 */
    }
    try {
      fs.unlinkSync(f.file);
    } catch {
      /* 忽略 */
    }
  }
  return out;
}

// 发完即回收：目录空则删（非空说明又来了新条目，留给下一轮）。避免每个会话都留一个空壳目录。
function cleanupSessDir(sid) {
  const d = sessDir(sid);
  if (!d) return;
  try {
    fs.rmdirSync(d);
  } catch {
    return; // 非空 / 不存在
  }
  try {
    fs.rmdirSync(path.dirname(d));
  } catch {
    /* 别的会话还在用 */
  }
}

// ---------- 待办标题清洗 ----------
// 🔴 10-02 用户实测反馈的根因：待办标题写成「新建任务计划：1.xxx / 2.xxx / 3.xxx」这种
//    **自带序号 + 自带类别前缀**的形式时，3 条待办会被念成 3 遍「新建任务计划一点 xxx」——
//    用户听感上就是「同一件事被拆成三条推送」。
//    合并只能减少**消息条数**，但只要标题里还留着前缀，TTS 仍会把前缀念出来。
//    所以治本在标题：剥掉「新建任务计划：」/「已完成任务计划：」这类类别前缀 + 「1.」「(2)」「③」这类序号。
//    只剥前缀与序号，**保留正文本体**（「更新文档与备忘」这种动作短语要原样留下）。
function cleanSubject(s) {
  let t = String(s || '').trim();
  if (!t) return '';
  // 剥类别前缀，可叠加多次（「新建任务计划：」= 先剥「新建任务计划」，再剥序号）。
  // 🔴 组合词必须排在单词**前面**：「新建任务计划」要先整体吃掉，否则「新建」先匹配、
  //    剩下「待办：」进入下一轮 —— 顺序写错会导致前缀残留（单测已抓到）。
  for (let i = 0; i < 3; i++) {
    const before = t;
    t = t.replace(
      /^(?:[^\p{L}\p{N}]{0,3}\s*)?(?:新建任务计划|已完成任务计划|新建待办|待办完成|完成任务|新建|创建|新增|完成|待办|任务|todo)\s*[:：]\s*/iu,
      '',
    );
    if (t === before) break;
  }
  // 剥开头的序号：「1.」「1、」「(1)」「（1）」「1)」「-」「•」「③」
  t = t.replace(/^\s*(?:[（(]?\d{1,2}[）).、::]|[③⑴❶]|[-•*]\s)\s*/, '');
  // 剥完若只剩空/标点，归零让调用方填「（无标题）」。
  return t.replace(/^[\s:：.、-]+/, '').trim();
}

// 正文里的待办清单：**短句、一行一类**。
// TTS 只念标题（`renderBroadcastText({title})`），所以正文怎么写都只会被念一次 ——
// 这正是「整轮一条」的关键：数量进正文，不把 5 个标题塞进标题里念成一长串。
function brief(arr) {
  const names = arr.map((s) => cleanSubject(s) || '（无标题）');
  if (names.length <= BATCH_LIST_MAX) return names.join('、');
  return names.slice(0, BATCH_LIST_MAX).join('、') + ' …等共 ' + names.length + ' 项';
}
function taskBlock(items) {
  if (!items.length) return '';
  // 10-02 起 `done` 分支**不再是防御性代码**：TaskCompleted 已改为入队（见 EACH_DONE），
  // 所以一轮里新建与完成都会出现在这里，分别成行、各自成段。
  const created = items.filter((i) => i.event === 'TaskCreated');
  const done = items.filter((i) => i.event === 'TaskCompleted');
  const lines = [];
  if (created.length) lines.push('📋 新建任务计划 ' + created.length + ' 项：' + brief(created.map((i) => i.subject)));
  if (done.length) lines.push('✅ 完成 ' + done.length + ' 项：' + brief(done.map((i) => i.subject)));
  return lines.join('\n');
}

// 收尾事件统一走这里：把整轮攒下的待办合并成**标题带待办名**的消息，然后清空队列。
// 🔴 10-04：默认 **TaskCreated 已即时推送**（见⑧），队列里通常只剩「完成」；
//    created 分支只在 `WARROOM_HOOK_CREATED_EACH=0` 回落模式下才有数据，仍保留以防退化。
// 🔴 10-02 修正方向：用户要「3 条待办名拼成 1 条，标题里就能看到三个名」，不是「任务完成通知」这
//    类抽象汇总（旧版待办塞进 summary 正文、标题用 source 默认，大屏上看不到待办名）。现在：
//      · 新建 N 条 → 1 条，标题 =「新建任务计划：清洗名1 + 清洗名2 + …」
//      · 完成 M 条 → 1 条，标题 =「已完成任务计划：清洗名1 + 清洗名2 + …」
//      · 本轮答复 / 原因（summary 参数）融进新建那条 summary 末尾；无待办则单独播报。
function composeTurnEnd(sid, summary) {
  const items = drainTasks(sid);
  const created = items.filter((i) => i.event === 'TaskCreated');
  const done = items.filter((i) => i.event === 'TaskCompleted');
  cleanupSessDir(sid);
  const msgs = [];
  if (created.length) {
    const names = created.map((i) => cleanSubject(i.subject) || i.subject || '（无标题）');
    msgs.push({
      kind: 'created',
      title: clip('📋 新建任务计划：' + names.join(' + '), 120),
      summary: '📋 新建任务计划 ' + created.length + ' 项：' + names.join('、') + (summary ? '\n\n' + summary : ''),
    });
  }
  if (done.length) {
    const names = done.map((i) => cleanSubject(i.subject) || i.subject || '（无标题）');
    msgs.push({
      kind: 'done',
      title: clip('✅ 已完成任务计划：' + names.join(' + '), 120),
      summary: '✅ 已完成任务计划 ' + done.length + ' 项：' + names.join('、'),
    });
  }
  if (!msgs.length) {
    msgs.push({ kind: 'plain', title: '', summary: summary || '本轮结束' });
  }
  log('收尾并入 ' + items.length + ' 条待办（新建 ' + created.length + ' + 完成 ' + done.length + '）→ 合并成 ' + msgs.length + ' 条带名消息');
  return { msgs, n: items.length };
}

// 收尾消息逐条推送：标题带待办名（plain 那条不传标题 → 走 source 默认）。
async function pushComposed(base, sid, msgs) {
  let last = 0;
  for (const m of msgs) {
    const code = await push([
      ...(m.title ? ['--title', m.title] : []),
      '--summary', m.summary,
      '--level', 'info',
      ...base,
      '--external-id', 'hook:turn-end:' + sid + ':' + m.kind + ':' + fingerprint(m.title + ' ' + m.summary),
    ]);
    log('收尾推送 exit=' + code + '（' + m.kind + (m.title ? ' 标题=' + m.title : '') + '）');
    last = code;
  }
  return last;
}

// 兜底：Stop 不一定来（被中断 / 引擎未触发），陈货不能永远躺在队列里等。
// 任何非收尾事件开头都顺手把「躺够 STALE_FLUSH_MS」的那批冲成一条 —— 仍然是一条，不是 N 条。
async function flushStale(sid, base) {
  const items = drainTasks(sid, STALE_FLUSH_MS);
  if (!items.length) return 0;
  await pushMerged({ sid, base }, items, '超时兜底');
  cleanupSessDir(sid);
  return items.length;
}

// 兜底路径的**独立**一条（收尾事件缺席时用）。标题同样带待办名拼接，与收尾口径一致。
async function pushMerged(ctx, items, tag) {
  const n = items.length;
  const created = items.filter((i) => i.event === 'TaskCreated');
  const done = items.filter((i) => i.event === 'TaskCompleted');
  const cNames = created.map((i) => cleanSubject(i.subject) || i.subject || '（无标题）');
  const dNames = done.map((i) => cleanSubject(i.subject) || i.subject || '（无标题）');
  let title;
  if (created.length && !done.length) title = clip('📋 新建任务计划：' + cNames.join(' + '), 120);
  else if (done.length && !created.length) title = clip('✅ 已完成任务计划：' + dNames.join(' + '), 120);
  else {
    const seg = [];
    if (created.length) seg.push('新建任务计划：' + cNames.join(' + '));
    if (done.length) seg.push('已完成任务计划：' + dNames.join(' + '));
    title = clip(seg.join('；'), 120);
  }
  const code = await push([
    '--title', title,
    '--summary', taskBlock(items),
    '--level', 'info',
    ...ctx.base,
    // 键 = 这一批的 task_id 集合：同批重推折叠，不同批各占一条。
    '--external-id',
    'hook:task-batch:' + ctx.sid + ':' + fingerprint(items.map((it) => it.tid || it.subject).join('|')),
  ]);
  log(`待办兜底推送（${tag}，${n} 条 → 1 条）exit=${code} 标题=${title}`);
  return code;
}

// ---------- 幂等键 ----------
// 后端去重：有 externalId 时 hash = sha256(channelId + externalId)，**不含内容、不含时间窗**
// （server/src/lib/dedupe.ts）。所以键必须「同事件重推同键（幂等）、不同事件不同键（不互相覆盖）」——
// 若都不给，同一 source 的所有事件会落到 `ai:<source>` 这一条上互相覆盖，历史只剩最后一条。
function fingerprint(s) {
  let h = 5381;
  const t = String(s == null ? '' : s);
  for (let i = 0; i < t.length; i++) h = ((h << 5) + h + t.charCodeAt(i)) >>> 0;
  return h.toString(36);
}
function bucket(ms) {
  return Math.floor(Date.now() / ms).toString(36);
}
function safeJson(v) {
  if (v === undefined || v === null) return '';
  if (typeof v === 'string') return v;
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
}

// Notification 的子类型 → 场景适配（标题 / 级别）。
// 引擎的 notification_type 枚举见 codebuddy 包：permission_prompt / idle_prompt /
// auth_success / elicitation_dialog / agent_needs_input / agent_completed。
// 返回 null = 噪声类型，跳过（避免大屏被 auth_success / agent_completed 刷屏）。
function adaptNotification(type) {
  switch (type) {
    case 'permission_prompt':
      return { title: '⚠️ 需要你操作：等待授权确认', level: 'urgent' };
    case 'agent_needs_input':
      return { title: '⚠️ 需要你操作：待你补充信息', level: 'urgent' };
    case 'elicitation_dialog':
      return { title: '⚠️ 需要你操作：MCP 服务弹窗', level: 'urgent' };
    case 'idle_prompt':
      return { title: '⏳ 等待你的输入', level: 'warning' };
    default:
      return null;
  }
}

async function handle(input) {
  const event = input.hook_event_name || '';
  const conn = connection();
  // 每次事件都把「推给谁、配置从哪来」写进日志 —— 排查「大屏上什么都没有」的第一手证据。
  log(`事件=${event} 目标=${conn.base} 来源=${conn.from}${conn.key ? '' : ' ⚠ 无密钥'}`);
  // 🔴 连接器形态（包内置 hook）未配置接收端时**直接跳过**：
  //    市场用户装完连接器还没贴接收端 URL，若照旧回落 http://localhost:3500，
  //    9 个事件会一次次失败——日志噪音 + 每次白起子进程。判定只看「有没有真实来源」，
  //    对已有配置的老用户零影响（他们 explicit 恒为 true）。
  if (!conn.explicit && process.env.CODEBUDDY_PLUGIN_ROOT) {
    log('插件形态尚未配置接收端（缺 ~/.warroom/receiving-endpoint.json），跳过推送');
    return;
  }
  const source = conn.name || 'WorkBuddy';
  const sid = String(input.session_id || '');
  // 用工位取自接收端绑定（持久化接收端 / mcp.json / env，回落 DEFAULT_CHANNEL），不再硬编码
  // ch-workbuddy —— 否则用户把接收端设成 ch-xyz 后，Hook 仍推到 ch-workbuddy（静默错工位）。
  const base = ['--channel', conn.channel || DEFAULT_CHANNEL, '--source', source];

  // ⓪ 兜底冲货（先于本事件自己的推送）：上一轮若没等到收尾事件（被中断 / 引擎没触发 Stop），
  //    队列里会躺着陈货。**只在 `UserPromptSubmit` 冲** —— 它才是「用户又开口了 = 新一轮开始」
  //    的天然边界，此刻结算上一轮遗留，语义最贴。
  //
  //    🔴 10-02 修掉的真 BUG：原先是「**任何非收尾**事件开头都冲」，配 20s 阈值。
  //       但一轮真实要跑 2~20 分钟（实测 16:00:45 建 5 条 → 16:22:27 才 Stop），
  //       于是下一轮**第一个**事件就把上一轮的待办当陈货抢跑冲掉，抢在收尾之前 ——
  //       而那一轮往往随后还会补 TaskCreated/TaskCompleted，消息与轮次彻底对不上号。
  //       现场：16:03:04 一个 TaskCompleted 进来，先冲了 5 条陈货、再把自己入队。
  //       保留 `!TURN_END_EVENTS.has(event)` 是必要的：收尾事件自己会全量清空，不必重复冲。
  if (!TURN_END_EVENTS.has(event) && event === 'UserPromptSubmit') {
    try {
      const n = await flushStale(sid, base);
      if (n) log('兜底：上一轮遗留 ' + n + ' 条待办已并成 1 条发出');
    } catch (e) {
      log('兜底冲货失败：' + (e && e.message ? e.message : String(e)));
    }
  }

  // ① 用户下达指令
  if (event === 'UserPromptSubmit') {
    const prompt = clip(input.prompt || '', MAX_TEXT);
    if (!prompt) {
      log('UserPromptSubmit 无 prompt 字段，跳过');
      return;
    }
    const code = await push([
      '--title', '🙋 收到指令',
      '--summary', prompt,
      '--level', 'info',
      ...base,
      // 同一提示词 30s 内折叠（引擎重推无害），否则新增一条。
      '--external-id', 'hook:prompt:' + sid + ':' + fingerprint(prompt) + ':' + bucket(30000),
    ]);
    log(`UserPromptSubmit 推送完成 exit=${code}`);
    return;
  }

  // ② 本轮任务完成
  if (event === 'Stop') {
    // stop_hook_active=true 表示本轮已由 Stop 钩子续跑过 —— 避免和续跑循环重复播报
    if (input.stop_hook_active) {
      log('stop_hook_active=true，跳过（避免续跑重复推送）');
      return;
    }
    // 引擎已把本轮答复直接放进 payload（last_assistant_message）；仅老引擎 / 字段缺失时回捞会话记录。
    const direct = clip(input.last_assistant_message || '', MAX_TEXT);
    const tail = direct || clip(lastAssistantText(input.transcript_path), MAX_TEXT);
    // 🔑 收尾只处理**完成**（默认新建已在创建时刻各自即时上屏，见⑧）；
    //    若处于 `WARROOM_HOOK_CREATED_EACH=0` 回落模式，队列里会有新建，这里一并并入。
    //    （完成事件默认入队合并、由本收尾发出，见上面 TaskCompleted 分支。）
    const composed = composeTurnEnd(sid, tail || '本轮回答结束（未从会话记录取到正文）');
    await pushComposed(base, sid, composed.msgs);
    log(`Stop 收尾完成（并入 ${composed.n} 条待办 → ${composed.msgs.length} 条带名消息）`);
    return;
  }

  // ③ 需要你操作（权限确认 / 等待输入 / MCP 弹窗）
  if (event === 'Notification') {
    const type = String(input.notification_type || 'permission_prompt');
    const spec = adaptNotification(type);
    if (!spec) {
      log('Notification(' + type + ') 属噪声类型，跳过');
      return;
    }
    const msg = clip(input.message || '', MAX_TEXT) || '（无附加说明）';
    const code = await push([
      '--title', spec.title,
      '--summary', msg,
      '--level', spec.level,
      ...base,
      '--external-id', 'hook:notify:' + sid + ':' + type + ':' + fingerprint(msg) + ':' + bucket(NOTIFY_BUCKET_MS),
    ]);
    log(`Notification(${type}) 推送完成 exit=${code}`);
    return;
  }

  // ④ 申请权限（比 Notification 更精确：带工具名与参数）
  if (event === 'PermissionRequest') {
    const tool = clip(input.tool_name || '', 60) || '未知工具';
    const detail = clip(safeJson(input.tool_input), MAX_TEXT);
    const code = await push([
      '--title', '🔐 请求权限：' + tool,
      '--summary', detail || '（无参数摘要）',
      '--level', 'urgent',
      ...base,
      '--external-id', 'hook:permreq:' + sid + ':' + tool + ':' + fingerprint(detail) + ':' + bucket(NOTIFY_BUCKET_MS),
    ]);
    log(`PermissionRequest 推送完成 exit=${code}`);
    return;
  }

  // ⑤ 会话开 / 关
  // 🔴 SessionStart 的 source 有四种（从引擎 `emitSessionStart(session, source)` 调用点反查确认）：
  //    startup / resume / clear / compact。
  //    **startup 必须静音** —— 新会话的第一条指令会在 1s 内接着触发 UserPromptSubmit
  //    （实测两条落库间隔 943ms，且顺序不定：收到指令反而先到），大屏上就是重复的两条。
  //    「有人来了」这个信号统一由 UserPromptSubmit 承担；SessionStart 只在**状态真的变了**时说话。
  if (event === 'SessionStart') {
    const src = String(input.source || 'startup');
    if (src === 'startup') {
      log('SessionStart(startup) 与紧随其后的 UserPromptSubmit 重复，静音');
      return;
    }
    // 非 startup 的三种才是「需要提醒人」的真状态变更（上下文可能已不完整）。
    const META = {
      resume: ['🔄 会话已恢复', '会话被恢复/切换，上下文可能来自更早的记录。'],
      clear: ['🧹 会话已清空', '上下文已重置，此前讨论的内容不再可见。'],
      compact: ['🗜️ 上下文已压缩', '对话被压缩，较早的细节可能已丢失 —— 继续前请确认关键前提。'],
    }[src] || ['🟢 会话状态变更：' + src, 'source=' + src];
    const code = await push([
      '--title', META[0],
      '--summary', META[1],
      '--level', 'info',
      ...base,
      // 键里带 source：同一对话先 clear 再 compact 是两条不同的事件，不该互相折叠。
      '--external-id', 'hook:session:' + src + ':' + sid,
    ]);
    log(`SessionStart(${src}) 推送完成 exit=${code}`);
    return;
  }

  if (event === 'SessionEnd') {
    // 也是收尾事件：会话结束前把还没发出去的待办一并带走（否则它们再没有收尾事件可依附）。
    const composed = composeTurnEnd(sid, '原因：' + clip(input.reason || '', 60));
    await pushComposed(base, sid, composed.msgs);
    log(`SessionEnd 收尾完成（并入 ${composed.n} 条待办 → ${composed.msgs.length} 条）`);
    return;
  }

  // ⑥ 本轮异常收尾
  if (event === 'StopFailure') {
    const err = clip(input.error || '', MAX_TEXT) || '未知错误';
    // 本轮虽然失败，但这轮建过/完成的待办属实 —— 一并带走，别让它们滞留到下一轮。
    const composed = composeTurnEnd(sid, err);
    await pushComposed(base, sid, composed.msgs);
    log(`StopFailure 收尾完成（并入 ${composed.n} 条待办 → ${composed.msgs.length} 条）`);
    return;
  }

  // ⑦ 待办**完成** —— 🔴 10-02 用户改判：**也合并**。
  //    初版是逐条立即上屏（当时判「完成是进度里程碑，被并掉就看不见了」），但用户实测反馈：
  //    一轮连着完成 3 条 → 大屏 3 行 + TTS 排队念 3 遍，听感上仍是「被拆成三条」。
  //    现按用户要求与 TaskCreated 同策：只入队，由收尾事件并进它自己那一条发出。
  //    标题清洗（cleanSubject）保证合并后那一条的标题是「✅ 已完成任务计划：更新文档与备忘」这种
  //    干净短句，TTS 只念一次、也不念出「新建任务计划：1.」这类前缀。
  //    🔑 想临时恢复旧行为（逐条）时：WARROOM_HOOK_DONE_EACH=1，无需改代码。
  if (event === 'TaskCompleted') {
    const subjectRaw = clip(input.task_subject || '', 120);
    const subject = cleanSubject(subjectRaw);
    const desc = clip(input.task_description || '', MAX_TEXT);
    if (!EACH_DONE) {
      const item = {
        event,
        subject: subject || subjectRaw,
        desc: desc || subject || subjectRaw,
        tid: String(input.task_id || '') || fingerprint(subjectRaw || subject),
        at: Date.now(),
      };
      if (enqueueTask(sid, item)) {
        log('TaskCompleted 已入队（' + (subject || subjectRaw) + '），等本轮收尾一并发出');
        return;
      }
      log('TaskCompleted 入队失败，落回逐条单发');
    }
    const code = await push([
      '--title', '✅ 已完成任务计划：' + clip(subject || subjectRaw || '（无标题）', 60),
      '--summary', desc || subject || subjectRaw,
      '--level', 'info',
      ...base,
      // 🔴 键里必须带**时间桶**：task_id 缺失时 tid 只能取自标题，而「提交并推送 main」这类任务名
      //    **每轮都会出现** → 常量键会把后续轮次全吞掉（09-27 的 `commit-<hash>` 就是这个坑）。
      //    加 30s 桶后：同一事件被引擎重发 → 同桶折叠；跨轮同名 → 各占一条。
      '--external-id',
      'hook:task-done:' + sid + ':' + (String(input.task_id || '') || fingerprint(subjectRaw || subject)) + ':' + bucket(30000),
    ]);
    log('TaskCompleted 逐条推送完成 exit=' + code + '（' + (subject || subjectRaw) + '）');
    return;
  }

  // ⑧ 待办**新建** —— 🔴 10-04 用户要求**即时推送**（创建时刻立即上屏，不再等收尾合并）。
  //    旧行为（10-02）：TaskCreated 也并入收尾那条 → 时间戳与「完成」挤在一起，
  //    看着像「完成全部后才推新建」。现在：每个新建立即推一条「📋 新建任务计划：<名>」。
  //    ⚠️ 代价：一次规划连建 5~7 条会即时刷 5~7 行。若嫌刷屏，设 `WARROOM_HOOK_CREATED_EACH=0`
  //    回落回「入队、由收尾合并」（单条「新建任务计划 N 项」），无需改代码。
  if (event === 'TaskCreated') {
    const subjectRaw = clip(input.task_subject || '', 120);
    const subject = cleanSubject(subjectRaw) || subjectRaw || '（无标题）';
    const desc = clip(input.task_description || '', MAX_TEXT);
    if (!EACH_CREATED) {
      // 回落：入队，由收尾事件并进它自己那一条（旧 10-02 行为，防刷屏）。
      const item = {
        event,
        subject: subject || subjectRaw,
        desc: desc || '',
        tid: String(input.task_id || '') || fingerprint(subjectRaw || subject),
        at: Date.now(),
      };
      if (enqueueTask(sid, item)) {
        log('TaskCreated 已入队（回落模式，' + (subject || subjectRaw) + '），等本轮收尾一并发出');
        return;
      }
      await pushMerged({ sid, base }, [item], '入队失败回落');
      return;
    }
    // 默认：创建时刻即时单发。键带 task_id + 30s 桶，引擎重推同桶折叠、跨轮同名各占一条。
    const code = await push([
      '--title', '📋 新建任务计划：' + clip(subject, 60),
      '--summary', desc || subject,
      '--level', 'info',
      ...base,
      '--external-id',
      'hook:task-created:' + sid + ':' + (String(input.task_id || '') || fingerprint(subjectRaw || subject)) + ':' + bucket(30000),
    ]);
    log('TaskCreated 即时推送完成 exit=' + code + '（' + subject + '）');
    return;
  }

  log('未处理的事件：' + event);
}

// ================= 入口分发（必须在文件末尾）=================
// 两个分支都要先让**所有 `const` 初始化语句**跑完：--turn-doctor 会用 STATE_ROOT / BATCH_LIST_MAX，
// 主流程要用 BATCH_EVENTS / TURN_END_EVENTS。函数声明会提升、`const` 不会 —— 放前面就是 TDZ 崩溃。
if (process.argv.includes('--doctor')) {
  runDoctor();
} else if (process.argv.includes('--turn-doctor')) {
  runTurnDoctor();
} else {
  // ---------- 主流程（宿主驱动）----------
  let buf = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => {
    if (!detached) detach(); // 有输入就说明宿主在跑了 —— 立刻放行
    buf += c;
  });
  process.stdin.on('error', () => {});
  process.stdin.on('end', () => {
    detach();
    let input = {};
    try {
      input = JSON.parse(buf.trim() || '{}');
    } catch (e) {
      log('stdin 不是合法 JSON，按空对象处理：' + e.message);
    }
    try {
      handle(input);
    } catch (e) {
      log('处理失败：' + (e && e.message ? e.message : String(e)));
    }
    // 兜底：给后台推送一点时间，然后无条件 0 退出（绝不能让宿主判成 blocked）
    armGuard(GUARD_MS);
  });
}
