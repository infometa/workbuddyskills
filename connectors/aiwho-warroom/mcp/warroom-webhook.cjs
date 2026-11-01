#!/usr/bin/env node
'use strict';
/*
 * WarRoom Webhook MCP —— 向 AIWHO WEBHOOK中台 后端推送 webhook 消息。
 *
 * 两种运行模式：
 *  1) MCP 服务态（默认，由 WorkBuddy mcp.json 驱动）：stdio JSON-RPC 2.0（换行分隔），
 *     零三方依赖，仅用 Node 内置 fetch（Node >= 18）。暴露七个工具：
 *       - setup_receiving_endpoint 接入第一步：识别接收端（用户中心复制的完整入站地址）并设为默认推送目标
 *       - push_warroom_event  通用推送（指定 title/body/level/channelId）
 *       - notify_task_complete 任务完成通知（默认推 ch-workbuddy，自动附「已推送远程 <commit>」）
 *       - notify_task_created 新建任务计划通知（标题「📋 {source} 新建任务计划：<标题>」）
 *       - notify_task_done   已完成任务计划通知（标题「✅ {source} 已完成任务计划：<标题>」）
 *       - notify_turn_start  轮次开始「🙋 收到指令」（**仅无 hook 宿主**每轮必调，补齐轮次事件）
 *       - notify_turn_end    轮次结束「✅ {source} 任务完成」（**仅无 hook 宿主**每轮必调）
 *  2) CLI 一次性推送态（agent 每轮任务完成后调用）：
 *       node warroom-webhook.cjs --notify --summary "本轮做了什么" [--commit <hash>] [--level info] [--channel ch-workbuddy]
 *       node warroom-webhook.cjs --notify --title "⚠️ 需要你操作：..." --summary "..." [--level warning]
 *     （给了 --title 就走通用推送，不套「✅ 任务完成」标题，适合待办/阻塞类事件）
 *     [--external-id <key>] 幂等键（可选）：同一 key 重推折叠为一条，不同 key 各占一条。
 *       ⚠️ 不给时回落 source 常量 `ai:<source>` —— 同一 AI 推的**不同消息会互相覆盖**，
 *       所以「一个来源推多种事件」的场景（如 hook）必须显式给 key。
 *     该模式复用同一套 pushEvent/notifyTaskComplete 逻辑，不启动 stdio 服务，打印结果后退出。
 *
 * 鉴权（v1.2.0 企微风格）：
 *  - 默认（演示）：共享推导密钥 whsec_demo_<channelId>（即用户中心复制的完整入站地址的 ?key=）。
 *    ⚠ 这是**公开演示值，不是密钥**：公式公开（whsec_demo_ + channelId），任何人可推导，
 *      仅供本地演示 / 测试。生产环境必须用 WARROOM_WEBHOOK_KEY 覆盖，否则等于无鉴权。
 *  - 生产：设环境变量 WARROOM_WEBHOOK_KEY 为真实 UUID 密钥（形如企微
 *    https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<uuid>），连接器直接作为 ?key= 发送。
 *    注意：后端 signing.ts 也必须按同一密钥校验才生效（验证期可保持演示密钥）。
 *
 * 可靠性（v1.2.0）：
 *  - --commit 省略时自动 git rev-parse --short HEAD 取最新提交，通知自动附「已推送远程 <hash>」。
 *  - fetch 带 10s 超时（AbortController）；网络错误 / 后端 5xx 自动重试 2 次，失败有明确报错与非 0 退出码。
 *
 * 协议与契约（v1.3.0，对齐 docs/audit-2026-09-19-mcp.md 的 P0/P1）：
 *  - 参数形状：只接受「全包 params.arguments」或「全平铺」两种互斥形状，混用**显式报错**
 *    （旧实现 arguments 一旦存在就整体取代 params，实测静默丢 body、urgent 降 info）；
 *  - 生命周期：initialize 之前调其它方法一律 -32002；通知（无 id / notifications/*）**不回包**；
 *  - 工具白名单：未知工具名显式报错，不再静默当成 push 执行；
 *  - 契约单一来源：level 别名 / title 上限 / 净化规则取自 lib/mcp-contract.mjs（本仓唯一来源），
 *    与服务端 coerceLevel、openapi maxLength 同口径，由 scripts/mcp-contract-check.mjs 十字校验；
 *  - 入参净化：title 去裸换行并按 512 截断、body 按 4000 截断（旧实现从不校验，实测发出 614 字 title）；
 *  - initialize 回包带 instructions，这是**唯一**能一开始告诉 AI「何时该调」的位置。
 *
 * 启动（服务态，由 WorkBuddy 驱动，无需手动跑）：
 *   node warroom-webhook.cjs
 * 可配环境变量 WARROOM_API_BASE（默认 http://localhost:3500）、
 * WARROOM_TENANT（V2 入站路径的租户段；空则按 V1 单段形状发送 —— 通常无需手设，
 * setup_receiving_endpoint 会从完整入站地址自动解析出来）。
 */

const { execSync } = require('child_process');
const path = require('path');
const { pathToFileURL } = require('url');
// 接收端绑定持久化（2026-10-10 修复：setup_receiving_endpoint 的内存绑定进程重启会丢、且 Hook 独立进程读不到）。
// ⚠️ 必须在下方 resolveBaseAndChannel() 调用**之前** require：它是 module-scope const，晚于调用点会命中 TDZ
//    （ReferenceError: Cannot access 'loadReceivingEndpoint' before initialization）—— 而无 env 的「重启场景」
//    正是唯一会走 loadReceivingEndpoint() 的分支，即一启动就崩。护栏 5.9 专门钉这条。
const { loadReceivingEndpoint, persistReceivingEndpoint, stateFilePath } = require(
  path.join(__dirname, '..', 'lib', 'receiving-endpoint.cjs'),
);
// 轮次播报覆盖面探测（2026-10-23）：决定 instructions 里那句「你该不该自己调轮次工具」到底是哪种。
// 旧口径按**宿主品牌**（WorkBuddy/Claude Code = 有 hook）推断，但 hook 的真实生效条件与品牌无关 ——
// 没装 / 装了指到失效路径 / 装了但没接收端，都会让 hook 静默不出声，而 AI 仍以为「有 hook」→ 轮次全丢。
// 详见 lib/turn-coverage.cjs 头注。同样必须早于 resolveBaseAndChannel()（TDZ 同理）。
const { probeTurnCoverage, summarize: summarizeCoverage } = require(
  path.join(__dirname, '..', 'lib', 'turn-coverage.cjs'),
);

// 覆盖面结果按 60s 缓存：每轮都读 192KB 日志没必要，但也不能整个会话只探一次
// （用户可能在会话中途装/修好 hook，或 hook 恰好在这一轮挂了）。
let _covCache = null;
let _covAt = 0;
function currentCoverage(force) {
  const now = Date.now();
  if (!force && _covCache && now - _covAt < 60 * 1000) return _covCache;
  _covCache = probeTurnCoverage();
  _covAt = now;
  return _covCache;
}

// BASE / DEFAULT_CHANNEL 解析优先级（2026-10-10 修复）：
//   显式 env（本地 dev 覆盖）> 持久化接收端（setup_receiving_endpoint 落盘）> 兜底 http://localhost:3500
// 旧实现直接 `process.env.WARROOM_API_BASE || 'http://localhost:3500'` —— 进程重启后无 env 即回落
// 本机 dev 端口（平时不开）→ 静默推失败。现改为：无 env 时先读持久化接收端，没有才回落默认值。
let BASE;
let DEFAULT_CHANNEL;
let BASE_SOURCE = '';
// V2（SaaS）入站路径的**租户段**：POST /api/v2/webhook/<tenantId>/<channelId>?key=<密钥>
// （服务端 routes/index.ts 只注册双段路由，单段形状已下线 —— 见 tenant-scope.ts 头注）。
// 空串 = 不发送租户段，回落 V1 单段形状 /api/v1/webhook/<channelId>（兼容自托管旧部署）。
// 优先级：WARROOM_TENANT 环境变量 > 持久化接收端里记的租户段（setup_receiving_endpoint 写入）。
let TENANT = (process.env.WARROOM_TENANT || '').trim();
function resolveBaseAndChannel() {
  if (process.env.WARROOM_API_BASE) {
    BASE = process.env.WARROOM_API_BASE.replace(/\/+$/, '');
    BASE_SOURCE = 'env 显式指定';
  } else {
    const ep = loadReceivingEndpoint();
    if (ep) {
      BASE = ep.base;
      DEFAULT_CHANNEL = ep.channelId;
      TENANT = (ep.tenantId || '').trim();
      BASE_SOURCE = '持久化接收端';
      // 同步进本进程 env，让 CLI 子进程 / 同进程内 worker 继承（仅本进程内，不写文件）。
      process.env.WARROOM_API_BASE = ep.base;
      if (ep.key) process.env.WARROOM_WEBHOOK_KEY = ep.key;
      process.env.WARROOM_CHANNEL = ep.channelId;
      if (TENANT) process.env.WARROOM_TENANT = TENANT;
      else delete process.env.WARROOM_TENANT;
    } else {
      BASE = 'http://localhost:3500';
      BASE_SOURCE = '⚠ 兜底 localhost:3500（未配置接收端，推送会失败）';
    }
  }
  if (!DEFAULT_CHANNEL) DEFAULT_CHANNEL = resolveDefaultChannel(null);
}
// 默认工位来自唯一来源（lib/demo-secret.mjs，本仓唯一来源）—— 此前 3 处各写了一份，
// 见该文件 DEFAULT_DEMO_CHANNEL 的说明。动态 import 的模块在首次取密钥时一起拿到。
// 🔴 但「唯一来源」本身是**硬编码常量、没有 env 可覆盖** → 工位不叫 ch-workbuddy 的部署
//    除了改代码没有别的办法（外部 review 指出的「坑2」）。这是本 server 应用自己的设计，
//    不是 MCP 协议问题（协议只定义工具调用，默认工位定成啥是 app 的事）。
//    故补一条覆盖链：WARROOM_CHANNEL > 唯一来源模块 > 兜底常量。
//    与 setup_receiving_endpoint 写入的 process.env.WARROOM_CHANNEL **同名**，天然自洽：
//    识别接收端后即便有其它代码路径重算默认工位，也会拿到用户给的工位而不是写死的那个。
const DEFAULT_CHANNEL_FALLBACK = 'ch-workbuddy';
/** 解析默认工位：env 优先（唯一可覆盖硬编码的口子），其次唯一来源模块，最后兜底常量。 */
function resolveDefaultChannel(mod) {
  const env = (process.env.WARROOM_CHANNEL || '').trim();
  return env || (mod && mod.DEFAULT_DEMO_CHANNEL) || DEFAULT_CHANNEL_FALLBACK;
}
resolveBaseAndChannel();
const REQUEST_TIMEOUT_MS = 10000;
const MAX_RETRIES = 2;

// ---------- 密钥（演示回落 + 生产环境变量，企微风格 ?key=<uuid>） ----------
// 公式收在 lib/demo-secret.mjs（**本仓唯一来源**）：此前仓库里 5 处各写了一份，
// 改公式要同时改对 5 处、漏一处的检查也不存在。这里改为动态 import 那份（本文件是 .mjs 之外的
// CJS，静态 require 拿不到 ESM，故用 import()，只在首次取密钥时付一次解析成本）。
const DEMO_SECRET_MODULE = pathToFileURL(
  path.join(__dirname, '..', 'lib', 'demo-secret.mjs'),
).href;

// 入站契约的唯一来源（level 别名 / title 上限 / 净化规则）—— 与 server 侧
// normalizers/levelMap.ts 的 coerceLevel、docs/openapi.yaml 的 maxLength 同口径。
// 此前 MCP 自己写了一份「只认小写三值」的校验，与服务端大小写不敏感 + 别名表相反：
// 用 `critical` / `URGENT` 推的消息会被**静默降成 info**，而 urgent 是语音播报的唯一
// 触发条件 → 大屏不播报且零报错（audit-mcp §1.6）。改为共用同一份实现。
const CONTRACT_MODULE = pathToFileURL(
  path.join(__dirname, '..', 'lib', 'mcp-contract.mjs'),
).href;

// 接收端绑定持久化模块已在文件顶部 require（须早于 resolveBaseAndChannel() 的调用点，见上方注释）。

let demoSecretMod = null;
let contractMod = null;
async function loadDemoSecretMod() {
  if (demoSecretMod === null) {
    demoSecretMod = await import(DEMO_SECRET_MODULE);
    // 🔴 走 resolveDefaultChannel 而不是直接取 DEFAULT_DEMO_CHANNEL —— 否则模块一加载
    //    就把 env 覆盖盖回硬编码的 ch-workbuddy（坑2 的根因就是这个赋值）。
    DEFAULT_CHANNEL = resolveDefaultChannel(demoSecretMod);
  }
  return demoSecretMod;
}
// 契约模块同样按需加载（MCP / CLI 两条路径都在用，且 CLI 路径先于 postWebhook 调用）。
async function contract() {
  if (contractMod === null) {
    contractMod = await import(CONTRACT_MODULE);
  }
  return contractMod;
}

// ---------- 接收端（用户中心复制的完整入站地址）识别：安装后由 AI 调用，替代「一握手就推测试」 ----------
// 旧行为：MCP stdio 在 initialize 握手时自动推一条「🟢 服务上线」，发生在用户还没给
// 服务端地址/工位/密钥之前，等于「连上即推测试」。新流程：安装服务（仅接线）后，AI 等用户
// 从用户中心「接入凭证 → 工位」复制完整入站地址（.../webhook/<channelId>?key=<密钥>）贴过来，
// 再调用 setup_receiving_endpoint 识别 station+key、设为本次会话默认推送目标，并推送「服务上线」确认。
// 解析完整入站地址，兼容两种形状：
//   V2（SaaS）  ：https://<中台>/api/v2/webhook/<tenantId>/<channelId>?key=<密钥>  → tenantId 非空
//   V1（自托管）：https://<中台>/api/v1/webhook/<channelId>?key=<密钥>             → tenantId 空串
// 🔴 旧实现只抓**一段**（/\/webhook\/([^/?]+)/），拿到 V2 的双段 URL 会把**租户 id 当成工位 id**，
//    并把请求打到已下线的 /api/v1 单段路由上 —— 两者都表现为「推送失败但看不出原因」。
function parseReceivingEndpoint(endpoint) {
  let u;
  try {
    u = new URL(endpoint.trim());
  } catch {
    throw new Error(
      '接收端不是合法 URL：' + endpoint +
        '（应为 .../api/v2/webhook/<租户>/<工位>?key=<密钥>，或旧部署的 .../api/v1/webhook/<工位>?key=<密钥>）',
    );
  }
  if (u.protocol !== 'http:' && u.protocol !== 'https:') {
    throw new Error('接收端协议必须是 http/https，收到 ' + u.protocol);
  }
  // 结尾锚定 + 最多两段：`/webhook/a`（V1）或 `/webhook/a/b`（V2）。
  // 多余段（/webhook/a/b/c）不再被静默截断成 a/b，而是直接判为非法地址。
  const m = u.pathname.match(/\/webhook\/([^/]+)(?:\/([^/]+))?\/?$/);
  if (!m) {
    throw new Error('接收端路径里找不到 /webhook/<工位> 或 /webhook/<租户>/<工位>（复制用户中心「接入凭证 → 工位」的完整入站地址，别手拼）');
  }
  const decode = (seg) => {
    try {
      return decodeURIComponent(seg);
    } catch {
      throw new Error('接收端路径段不是合法的百分号编码：' + seg);
    }
  };
  const seg1 = decode(m[1]);
  const seg2 = m[2] === undefined ? '' : decode(m[2]);
  // 判形状：有第二段即 V2；另用 /api/v2/ 前缀兜底识别「V2 地址但缺了租户段」这种手改错误。
  const looksV2 = /\/api\/v2\/webhook\//.test(u.pathname);
  if (seg2 === '' && looksV2) {
    throw new Error(
      'V2 入站地址必须带租户段：/api/v2/webhook/<租户>/<工位>?key=<密钥>（完整入站地址请勿删段）',
    );
  }
  const tenantId = seg2 === '' ? '' : seg1;
  const channelId = seg2 === '' ? seg1 : seg2;
  if (channelId.length === 0 || channelId.includes('%')) {
    throw new Error('接收端解析出的 channelId 非法：' + channelId);
  }
  if (tenantId.includes('%')) {
    throw new Error('接收端解析出的 tenantId 非法：' + tenantId);
  }
  const key = u.searchParams.get('key');
  if (!key || key.trim().length === 0) {
    throw new Error('接收端缺少 ?key=<密钥>（完整入站地址自带，不能手删）');
  }
  return { base: u.origin.replace(/\/+$/, ''), tenantId, channelId, key: key.trim() };
}

/** 幂等键里的身份片段：只保留 ASCII 字母数字与 `_.-`，其余换成下划线；纯中文名净化后回落 unknown。 */
function idSlug(s) {
  const t = String(s == null ? '' : s).replace(/[^0-9A-Za-z_.-]/g, '_');
  return /[0-9A-Za-z]/.test(t) ? t : '';
}

function maskKey(k) {
  if (k.length <= 10) return '••••••';
  return k.slice(0, 6) + '…' + k.slice(-4);
}

// 服务上线确认（在用户给了接收端之后才推，不再握手即推）。永不影响调用方（失败只回报文）。
async function pushOnline(who, channelId) {
  try {
    const extId = 'mcp:online:' + (idSlug(who) || 'unknown') + ':' + Math.floor(Date.now() / 600000).toString(36);
    const resp = await postWebhook(channelId, {
      title: '🟢 服务上线：' + who,
      body: 'AI 已通过接收端接入作战室\n接入时间：' + new Date().toISOString(),
      level: 'info',
      externalId: extId,
    });
    return resp.created ? '已推送（created=true）' : '已存在（去重命中，未新增）';
  } catch (e) {
    return '推送失败：' + (e && e.message ? e.message : String(e));
  }
}

// 接收端识别后回给用户看「本工位会出现的全部消息模板」。
// ⚠️ 之前只列了「AI 主动推送」那一列（4 个工具），漏掉了宿主 Hook 自动发的 5 类生命周期模板，
// 导致用户以为「9 个模板只剩 4 个」。这里把两列都列出并标注来源：
//   A 列 = AI 通过本 MCP 工具显式调用产生的（含本会话新增的 新建/完成待办 2 个）；
//   B 列 = 宿主 Hook 事件自动触发、无需 AI 调用的（收到指令/会话恢复/清空/压缩/会话结束）。
// 用户记忆里的「9 个」= 本表 A 列的 服务上线/任务完成/需要你操作/自由标题 + B 列 5 类
//          （其中 新建任务计划 被用户归入「需要你操作」、未单列；本 MCP 把它独立成工具后才单列）。
const TEMPLATE_GUIDE = [
  '【A. AI 主动推送 —— 由本 MCP 工具调用产生，需 AI 显式调用】',
  '① 🟢 服务上线 —— 调本 setup_receiving_endpoint 时自动确认连接（已从「握手即推」改为「给接收端后才推」）',
  '② ✅ 任务完成 —— notify_task_complete（一轮收尾 / post-commit）→ 标题「✅ {source} 任务完成」',
  '③ 📋 新建任务计划 —— notify_task_created → 标题「📋 {source} 新建任务计划：<标题>」',
  '④ ✅ 已完成任务计划 —— notify_task_done → 标题「✅ {source} 已完成任务计划：<标题>」',
  '⑤ ⚠️ 需要你操作 / 自由标题 —— push_warroom_event（自定义标题；level=warning/urgent 即 ⚠️ 需你操作，会触发语音播报）',
  '⑥ 🙋 收到指令 —— notify_turn_start（**只在「没有 hook 覆盖」时**才由 AI 每轮调；下面这行判定为准）',
  '⑦ ✅ 任务完成（轮次）—— notify_turn_end（同上；hook 侧由 Stop 自动推）',
  '',
  '【B. 宿主 Hook 自动推送 —— 无需 AI 调用；WorkBuddy 连接器包**自带** hooks.json（随包生效），只需一次 --setup 落接收端，见 SKILL.md §7.4】',
  '⑥ 🙋 收到指令 —— UserPromptSubmit（有人发指令）',
  '⑦ 🔄 会话已恢复 —— resume（恢复 / 切换会话）',
  '⑧ 🧹 会话已清空 —— /clear',
  '⑨ 🗜️ 上下文已压缩 —— compact',
  '⑩ （会话结束）—— session-end（一个会话一条）',
].join('\n');

// 工具 3：接收端识别 + 设为默认推送目标 + 推服务上线确认 + 列出匹配模板。
// 这是「安装服务」与「真正推送」之间的分水岭：调用它之前，本服务**不会**向任何地址发消息。
async function setupReceivingEndpoint(params) {
  const args = extractArgs(params, 'setup_receiving_endpoint');
  const endpoint = argString(args, 'endpoint').trim();
  if (!endpoint) throw new Error('endpoint 不能为空（把用户中心「接入凭证 → 工位」的完整入站地址贴过来）');
  const { base, tenantId, channelId, key } = parseReceivingEndpoint(endpoint);
  // 设为本次会话默认推送目标（进程常驻，后续调用直接走它；也写进 env 让子进程继承）。
  BASE = base;
  TENANT = tenantId;
  DEFAULT_CHANNEL = channelId;
  BASE_SOURCE = '本次 setup_receiving_endpoint';
  process.env.WARROOM_API_BASE = base;
  process.env.WARROOM_WEBHOOK_KEY = key;
  process.env.WARROOM_CHANNEL = channelId;
  // 同步租户段：V2 空串时**删掉**该 env —— 否则上一次识别到的租户会残留在进程 env 里，
  // 把这次给的 V1 地址也拼成 V2 双段（表现为 404）。
  if (tenantId) process.env.WARROOM_TENANT = tenantId;
  else delete process.env.WARROOM_TENANT;
  // 🔑 持久化：把绑定落盘，进程重启 / 宿主 Hook 独立进程都能读回 —— 否则重启后会回落
  //    http://localhost:3500（不存在的本地地址）静默推失败（2026-10-10 修复）。
  const persisted = persistReceivingEndpoint({ base, tenantId, channelId, key });
  const source = resolveSource(args) || '未署名客户端';
  // 「服务上线」确认：默认推；WARROOM_ONLINE_NOTIFY=0 可关（如护栏脚本避免污染抓包）。
  const online =
    process.env.WARROOM_ONLINE_NOTIFY === '0'
      ? '已跳过（WARROOM_ONLINE_NOTIFY=0）'
      : await pushOnline(source, channelId);
  return [
    '✅ 已识别接收端并设为默认推送目标：',
    '   服务端基址：' + base,
    '   租户 tenantId：' + (tenantId || '（无 —— 按 V1 单段形状发送）'),
    '   工位 channelId：' + channelId,
    '   入站地址形状：' + (tenantId ? 'V2 双段 /api/v2/webhook/<租户>/<工位>' : 'V1 单段 /api/v1/webhook/<工位>'),
    '   密钥：' + maskKey(key),
    '   来源名 source：' + source,
    '   持久化：' + (persisted ? '已落盘（进程重启 / 宿主 Hook 均会读回，不再回落 localhost:3500）' : '⚠ 落盘失败（仅本进程内存有效，重启会丢）'),
    '',
    '本工位会出现的全部消息模板（A=AI 主动推送 / B=宿主 Hook 自动推送）：',
    TEMPLATE_GUIDE,
    '',
    // 轮次播报该由谁负责，在「用户刚给完接收端」这一刻判一次 —— 这正是 hook 能否工作的分水岭
    // （hook 读的就是这份刚落盘的接收端）。结论随模板一起回给 AI，省得它按宿主品牌猜。
    (() => {
      const cov = currentCoverage(true);
      return [
        '【轮次播报判定 · 现探】' + summarizeCoverage(cov),
        '  依据：' + cov.reason,
        ...cov.evidence.map((e) => '  · ' + e),
      ].join('\n');
    })(),
    '',
    '服务上线通知：' + online,
    '',
    '➡️ 下一步（请 AI 转告用户并询问）：上面这些模板的标题 / 文案是否需要修改？' +
    ' 若需要，请用户指明「哪个模板 + 改成什么」，再按 SKILL.md §7.1 第 6 步落地。',
  ].join('\n');
}

async function webhookKey(channelId) {
  const mod = await loadDemoSecretMod();
  // 生产：真实 UUID 密钥优先；未设则回落公开演示推导值（该回落有启动期护栏兜底，
  // 见 server/src/services/securityGuard.ts）。
  return mod.resolveWebhookSecret(channelId);
}

// ---------- 自动取最新 commit（省略 --commit 时） ----------
function detectCommit() {
  try {
    return execSync('git rev-parse --short HEAD', {
      cwd: process.cwd(),
      stdio: ['ignore', 'pipe', 'ignore'],
      timeout: 3000,
    }).toString().trim();
  } catch {
    return '';
  }
}

// ---------- 带超时 + 重试的 fetch ----------
async function fetchWithRetry(url, options) {
  let lastErr;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS);
    try {
      const resp = await fetch(url, { ...options, signal: ctrl.signal });
      clearTimeout(timer);
      if (resp.status >= 500 && attempt < MAX_RETRIES) {
        lastErr = new Error('后端返回 ' + resp.status + '，准备重试');
        continue;
      }
      return resp;
    } catch (e) {
      clearTimeout(timer);
      lastErr = e;
      if (attempt < MAX_RETRIES) continue;
      if (e && e.name === 'AbortError') {
        throw new Error('请求超时（' + REQUEST_TIMEOUT_MS + 'ms）未收到 ' + BASE + ' 响应');
      }
      throw new Error('请求失败：' + (e instanceof Error ? e.message : String(e)));
    }
  }
  throw lastErr || new Error('未知请求错误');
}

// ---------- 共享：向入站地址发送一条消息 ----------
// 形状由 TENANT 决定（见文件顶部）：
//   V2（SaaS）  ：POST {BASE}/api/v2/webhook/{tenantId}/{channelId}?key=<密钥>  ← 服务端只注册这一种
//   V1（自托管）：POST {BASE}/api/v1/webhook/{channelId}?key=<密钥>
// 两者鉴权都用 ?key=<工位密钥>（服务端 controllers/webhook.ts 的 4b 分支，与请求头签名二选一）。
function webhookUrl(channelId, key) {
  const ch = encodeURIComponent(channelId);
  const qs = '?key=' + encodeURIComponent(key);
  return TENANT
    ? BASE + '/api/v2/webhook/' + encodeURIComponent(TENANT) + '/' + ch + qs
    : BASE + '/api/v1/webhook/' + ch + qs;
}

async function postWebhook(channelId, payload) {
  const ch = channelId.toString().trim();
  const key = await webhookKey(ch);
  const url = webhookUrl(ch, key);
  let resp;
  try {
    resp = await fetchWithRetry(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (e) {
    throw new Error('请求后端失败（' + BASE + ' 是否启动？）：' + (e instanceof Error ? e.message : String(e)));
  }
  const text = await resp.text();
  if (!resp.ok) throw new Error('后端返回 ' + resp.status + '：' + text.slice(0, 240));
  // 返回 {text, created}：created 来自后端响应体的 created 字段（201=true 新消息，200=false 去重命中）。
  // audit-mcp §1.10：此前只判 resp.ok 就打印「已推送」，重投同一轮任务时把
  // 「后端说是重复、其实没新增」也报成成功推送 —— 调用方据此以为大屏会多一条。
  let created = resp.status === 201;
  try {
    const parsed = JSON.parse(text);
    if (parsed !== null && typeof parsed === 'object' && typeof parsed.created === 'boolean') {
      created = parsed.created;
    }
  } catch {
    // 响应体不是 JSON（例如代理错误页）：保守沿用状态码判断，不抛错。
  }
  return { text, created };
}

// ---------- 参数形状：严格解析，不做静默合并 ----------
//
// 修复 audit-mcp §1.1（P0）：旧实现 `const p = (params && params.arguments) || params || {}`
// 的意图是「两种形状都收」，但 `arguments` 一旦存在就**整体取代** params ——
// 平铺传参又带了 arguments 的客户端，业务参数被整体丢弃，实测发出
// {"body":"","level":"info"}：body 丢了、urgent 降成 info，**无任何报错**。
//
// 新口径：只接受两种**互斥**形状，一旦混用（两边都带业务参数）直接报错，
// 绝不静默挑一边。宁可让调用方看到 isError，也不让消息悄悄变样。
//
//   shape A（MCP 标准）： params = { name, arguments: { title, body, level, channelId } }
//   shape B（平铺兼容）： params = { name, title, body, level, channelId }
//
// 协议字段（`name` / `arguments` / `_meta`）**不是业务参数**，一律跳过 —— 与 HTTP 侧
// 服务端 HTTP 传输插件（mcp-http.ts）同口径（契约唯一来源见 lib/mcp-contract.mjs 的
// MCP_TOOL_CALL_PROTOCOL_KEYS）。此前只跳过 name/arguments，宿主自动注入的 `_meta`
// 被当成平铺业务参数 → 与 arguments 并存时误判「混用」→ tools/call 全被拒绝（实测）。
const PROTOCOL_KEYS = ['name', 'arguments', '_meta'];
function extractArgs(params, toolName) {
  if (params === null || typeof params !== 'object') {
    throw new Error('tools/call 的 params 必须是对象（收到 ' + typeof params + '）');
  }
  const hasArgs = params.arguments !== undefined && params.arguments !== null;
  if (hasArgs && typeof params.arguments !== 'object') {
    throw new Error('params.arguments 必须是对象');
  }
  const flat = {};
  for (const k of Object.keys(params)) {
    if (PROTOCOL_KEYS.includes(k)) continue;
    flat[k] = params[k];
  }
  const flatKeys = Object.keys(flat);
  if (hasArgs && flatKeys.length > 0) {
    throw new Error(
      '参数形状混用：params.arguments 与平铺参数（' + flatKeys.join(', ') + '）同时存在。' +
        '请二选一 —— 要么全放进 params.arguments，要么全部平铺，不要混着传。',
    );
  }
  const args = hasArgs ? params.arguments : flat;
  void toolName;
  return args;
}

// 从参数里取字符串（只接受标量，不 toString 掉对象/数组 —— 那会把 [object Object] 推上大屏）
function argString(args, key) {
  const v = args[key];
  if (v === undefined || v === null) return '';
  if (typeof v === 'string') return v;
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  throw new Error(key + ' 必须是字符串（收到 ' + (Array.isArray(v) ? 'array' : typeof v) + '）');
}

// ---------- 多 AI 可分辨：source / aiName ----------
// source 是「谁推的」，会拼进标题、落进 externalId（多 AI 接入后大屏与 /messages 才能分辨）。
// aiName 是兼容别名（宿主习惯把 clientInfo.name 落到这个键上）；两者都给时 aiName 优先。
// 净化走契约唯一来源（去裸换行 + 截断）—— 它会被拼进 title，不净化就是把注入面扩到 source。
function resolveSource(args) {
  const c0 = args.aiName !== undefined && args.aiName !== null ? args.aiName : args.source;
  if (c0 === undefined || c0 === null) return '';
  if (typeof c0 !== 'string' && typeof c0 !== 'number' && typeof c0 !== 'boolean') {
    throw new Error('source/aiName 必须是字符串');
  }
  // 此处同步实现（契约模块是动态 import 的 ESM，本函数在参数解析阶段就要用）：
  // 净化规则与契约 sanitizeSource 一致 —— 去裸换行 + trim + 32 字截断。
  return String(c0).replace(/[\r\n\u2028\u2029]+/g, ' ').trim().slice(0, 32);
}

// externalId 是**去重键**（见 server/src/lib/dedupe.ts）：后端在有它时直接用
// `sha256(channelId + '\x1f' + externalId)`，**不含内容、不含时间窗** ——
// 因此键必须「同事件重推同键（幂等）、不同事件不同键（不互相覆盖）」。
// 净化为单行 + 长度上限（DB 字段是 TEXT，但超长键无意义且会进日志）。
const EXTERNAL_ID_MAX = 160;
function sanitizeExternalId(v) {
  if (v === undefined || v === null) return '';
  if (typeof v !== 'string' && typeof v !== 'number' && typeof v !== 'boolean') {
    throw new Error('externalId 必须是字符串');
  }
  return String(v).replace(/[\r\n\u2028\u2029]+/g, ' ').trim().slice(0, EXTERNAL_ID_MAX);
}

// channelId 只接受**未编码**的裸 id：收到 % 说明调用方把「复制来的整条 URL」塞进来了。
// audit-mcp §1.9：此前会再编码一次（ch%20x → ch%2520x）→ 404，而「复制完整地址」是产品卖点，必踩。
function assertRawChannelId(channelId) {
  if (channelId.includes('%')) {
    throw new Error(
      'channelId 看起来是 URL 编码后的值（含 %）：' + channelId + '。请传未编码的裸 id（如 ch-workbuddy）。',
    );
  }
}

// ---------- 工具 1：通用推送 ----------
async function pushEvent(params) {
  const args = extractArgs(params, 'push_warroom_event');
  const c = await contract();
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const title = c.sanitizeTitle(argString(args, 'title'));
  if (!title) throw new Error('title 不能为空（或净化后为空）');
  // level：与服务端 coerceLevel 同口径 —— 大小写不敏感 + 认别名。
  // 注意：别名收敛是**服务端也认**的语义，不是 MCP 自己放宽；空/未知值回落 info。
  const level = c.coerceLevel(argString(args, 'level') || undefined, 'info');
  const body = c.sanitizeBody(argString(args, 'body'));
  const source = resolveSource(args);
  // 幂等键：**显式 externalId 优先**（CLI `--external-id` 用 —— hook 的各个事件必须据此互不覆盖），
  // 否则按「标题指纹 + 30s 桶」自动生成（见 contract.pushExternalId 的注释）。
  // ⚠️ 曾经这里回落的是 `ai:<source>` —— 对同一来源是**常量**，于是同一 AI 推的不同消息
  // 命中同一条记录、后推覆盖先推（Issue #2）。现在缺省值本身就按内容区分：
  // 不同标题 → 不同键（各占一条）；同标题 30s 内重调 → 同键（抖动折叠）。
  const payload = { title, body, level };
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) || c.pushExternalId(source, title);
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '✅ ' + (resp.created ? '已推送至 ' : '已存在（去重命中，未新增）') + channelId +
    '（level=' + level + (source ? '，source=' + source : '') + '），后端响应。\n' + resp.text.slice(0, 240)
  );
}

// ---------- 工具 2：任务完成通知（完善 mcp 功能：每轮任务完成后推送） ----------
async function notifyTaskComplete(params) {
  const args = extractArgs(params, 'notify_task_complete');
  const c = await contract();
  const summary = argString(args, 'summary').trim();
  if (!summary) throw new Error('summary 不能为空（或净化后为空）');
  const level = c.coerceLevel(argString(args, 'level') || undefined, 'info');
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const source = resolveSource(args);
  let commit = argString(args, 'commit').trim();
  if (!commit) commit = detectCommit();   // v1.2.0：省略时自动取最新提交
  let body = summary;
  if (commit) body += '\n\n已推送远程 ' + commit;
  // 标题走上限截断 + 换行净化（audit-mcp §1.4 / §1.5）：此前 title 从不校验，
  // 实测发出 614 字的 title，超出 @db.VarChar(512) 后被数据库静默截断/报错，
  // 错误信息与真实原因无关，排查成本极高。
  //
  // 标题模板 `✅ {source} 任务完成`（audit-mcp §1.8）：多 AI 接入同一工位时，
  // 写死的「✅ 任务完成」会让大屏出现一串同款标题，分不清是谁推的。
  // 该模板收在契约唯一来源里，与 HTTP 传输、SKILL.md 三处同口径、可校验。
  const title = c.sanitizeTitle(c.taskCompleteTitle(source));
  const payload = { title, body: c.sanitizeBody(body), level };
  // 幂等键：显式 externalId > commit（同一轮任务重推不产生第二条）> source（同一 AI 重复通知折叠）。
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) ||
    (commit ? 'commit-' + commit : c.sourceExternalId(source));
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '✅ ' + (resp.created ? '已推送' : '已存在（去重命中，未新增）') + '「任务完成」通知至 ' + channelId +
    '（level=' + level + (source ? '，source=' + source : '') + (commit ? '，commit=' + commit : '') +
    '），后端响应。\n' + resp.text.slice(0, 240)
  );
}

// ---------- 工具 2.5：新建任务计划通知 ----------
// 与 notify_task_complete（一轮任务收尾摘要）正交：本工具针对「某条**具体待办被新建**」这个事件，
// 标题直接带待办标题，大屏一眼看出建了什么。标题模板取自契约唯一来源 taskCreateTitle（多 AI 可分辨）。
async function notifyTaskCreated(params) {
  const args = extractArgs(params, 'notify_task_created');
  const c = await contract();
  const subject = argString(args, 'subject').trim();
  if (!subject) throw new Error('subject 不能为空（待办标题）');
  const detail = argString(args, 'detail').trim();
  const level = c.coerceLevel(argString(args, 'level') || undefined, 'info');
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const source = resolveSource(args);
  const title = c.sanitizeTitle(c.taskCreateTitle(source, subject));
  const payload = { title, body: c.sanitizeBody(detail), level };
  // 幂等键：显式 externalId > 「来源 + 待办标题」指纹。
  // 第三档 `task-created:<subject>` 曾经永远轮不到（source 为空时 sourceExternalId 也返回空，
  // 但那时 `ai:` 常量档先命中）—— 现在直接按内容派生，不再有死代码分支（Issue #2）。
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) ||
    c.taskCreatedExternalId(source, subject);
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '📋 ' + (resp.created ? '已推送' : '已存在（去重命中，未新增）') + '「新建任务计划」通知至 ' + channelId +
    '（level=' + level + (source ? '，source=' + source : '') + '），后端响应。\n' + resp.text.slice(0, 240)
  );
}

// ---------- 工具 2.6：已完成任务计划通知 ----------
// 与 Hook 侧 TaskCompleted 的「✅ 已完成任务计划：<待办名>」同口径（operations.md），
// 这里补上 source 以利多 AI 分辨。标题模板取自契约唯一来源 taskDoneTitle。
async function notifyTaskDone(params) {
  const args = extractArgs(params, 'notify_task_done');
  const c = await contract();
  const subject = argString(args, 'subject').trim();
  if (!subject) throw new Error('subject 不能为空（待办标题）');
  const detail = argString(args, 'detail').trim();
  const level = c.coerceLevel(argString(args, 'level') || undefined, 'info');
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const source = resolveSource(args);
  const title = c.sanitizeTitle(c.taskDoneTitle(source, subject));
  const payload = { title, body: c.sanitizeBody(detail), level };
  // 幂等键：显式 externalId > 「来源 + 待办标题」指纹（与 notify_task_created 同一范式，Issue #2）。
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) ||
    c.taskDoneExternalId(source, subject);
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '✅ ' + (resp.created ? '已推送' : '已存在（去重命中，未新增）') + '「已完成任务计划」通知至 ' + channelId +
    '（level=' + level + (source ? '，source=' + source : '') + '），后端响应。\n' + resp.text.slice(0, 240)
  );
}

// 轮次工具被调用时的「你可能是多余的」自检 —— 覆盖「AI 判断错了」这一种失败。
// instructions 已经把结论断言给模型了，但模型仍可能忽略（或用户在会话中途装了 hook）。
// 这里不再靠模型自觉，而是在返回值里直接给事实：本条大概率与 hook 重复。
// 不改变推送行为（护栏会调这两个工具断言落点），只多一行提示。
// ⚠️ 不再对「hook 推的工位 ≠ 接收端文件的工位」报警：那份文件是全机共享的，
//    同机多 AI 各自工位不同属正常（2026-10-23 用户纠正：qclaw 是另一套 AI 软件的工位）。
function turnCoverageCaveat(toolName) {
  try {
    const cov = currentCoverage();
    if (cov.mode === 'hook') {
      return (
        '\n⚠️ 本机检测到宿主 Hook 正在推轮次事件（' + cov.lastTurnEvent + ' @ ' + cov.lastTurnEventAt + '），' +
        '本条很可能与它重复上屏。若用户确实看不到「🙋 收到指令 / ✅ 任务完成」，说明 hook 已失效 —— ' +
        '请按 SKILL §7.1.1 排查，而不是长期靠 ' + toolName + ' 顶。'
      );
    }
    return '';
  } catch {
    return '';
  }
}

// ---------- 工具 4：轮次开始（收到指令） ----------
// 为什么存在：MCP 是客户端驱动协议 —— 服务端**无法**感知「用户刚发了一条消息」。有 hook 的宿主
// 由 UserPromptSubmit 自动推「🙋 收到指令」；**无 hook 的纯 MCP 宿主**（OpenClaw 等）没有任何事件，
// 轮次开始在大屏上就是空白。本工具把这个信号补到 MCP 面：名字即指令，参数全可选（调用成本≈0）。
// 与 Hook 侧同标题（不带 source）、同量级幂等键（30s 桶 + 用户原话指纹）。
async function notifyTurnStart(params) {
  const args = extractArgs(params, 'notify_turn_start');
  const c = await contract();
  const prompt = argString(args, 'prompt').trim();
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const source = resolveSource(args);
  const title = c.sanitizeTitle(c.turnStartTitle());
  const payload = { title, level: 'info' };
  if (prompt) payload.body = c.sanitizeBody(prompt);
  // 幂等键：显式 externalId > 轮次指纹（用户原话）+30s 桶。**不回落 ai:<source> 常量** ——
  // 那会让同一 AI 的两轮折叠成一条（每一轮都收不到「收到指令」）。
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) || c.turnStartExternalId(source, prompt);
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '🙋 ' + (resp.created ? '已推送' : '已存在（去重命中，未新增）') + '「收到指令」至 ' + channelId +
    '（level=info' + (source ? '，source=' + source : '') + '），后端响应。\n' + resp.text.slice(0, 240) +
    turnCoverageCaveat('notify_turn_start')
  );
}

// ---------- 工具 5：轮次结束（任务完成） ----------
// 与 Hook 侧 Stop→notify_task_complete 同落点（标题 `✅ {source}任务完成`），但**参数全可选**：
// 普通对话没有「任务摘要」也不该漏报，缺省给占位正文 —— 否则模型会因「没摘要可写」而整轮跳过。
// 🔴 幂等键用「摘要指纹 + 30s 桶」，**刻意不复用 commit-<hash>**（见 lib/mcp-contract.mjs 说明）。
async function notifyTurnEnd(params) {
  const args = extractArgs(params, 'notify_turn_end');
  const c = await contract();
  const summary = argString(args, 'summary').trim();
  const level = c.coerceLevel(argString(args, 'level') || undefined, 'info');
  const channelId = (argString(args, 'channelId') || DEFAULT_CHANNEL).toString().trim();
  assertRawChannelId(channelId);
  const source = resolveSource(args);
  let commit = argString(args, 'commit').trim();
  if (!commit) commit = detectCommit();
  let body = summary || '（本轮无摘要）';
  if (commit) body += '\n\n已推送远程 ' + commit;
  const title = c.sanitizeTitle(c.taskCompleteTitle(source));
  const payload = { title, body: c.sanitizeBody(body), level };
  const externalId =
    sanitizeExternalId(argString(args, 'externalId')) || c.turnEndExternalId(source, summary);
  if (externalId) payload.externalId = externalId;
  const resp = await postWebhook(channelId, payload);
  return (
    '✅ ' + (resp.created ? '已推送' : '已存在（去重命中，未新增）') + '「任务完成（轮次）」至 ' + channelId +
    '（level=' + level + (source ? '，source=' + source : '') + (commit ? '，commit=' + commit : '') +
    '），后端响应。\n' + resp.text.slice(0, 240) +
    turnCoverageCaveat('notify_turn_end')
  );
}

// ---------- 工具定义 ----------
// source 参数的自述（与契约唯一来源的 SOURCE_MAX 同值；由 scripts/mcp-contract-check.mjs 校验）。
const SOURCE_DESC =
  'AI 来源名（多 AI 接入必填，<= 32 字），落进标题与 externalId，' +
  '让大屏与 /messages 能分辨是谁推的。别名 aiName（同义，后者优先）。' +
  '各宿主可在 mcp.json 的 env 里配 WARROOM_AI_NAME 固定它。';

const TOOL_DEF = {
  name: 'push_warroom_event',
  description:
    '向作战室大屏推一条消息（AIWHO WEBHOOK中台入站地址 POST /api/v2/webhook/<租户>/<工位>），urgent 会触发 TTS 语音播报。' +
    '【何时用】① 需要人介入（阻塞 / 等你确认 / 要你补信息）→ title 以「⚠️ 需要你操作：」开头、level=urgent；' +
    '② 关键失败 / 线上异常 → title 写清现象、level=urgent；' +
    '③ 待办 / 阻塞提醒（不急着打断人）→ level=warning；' +
    '④ 普通进展 / 信息同步 → level=info（别用 urgent，会打扰人）。' +
    '一轮任务收尾请改用 notify_task_complete，别用本工具套「任务完成」。' +
    '默认推到 ch-workbuddy；鉴权缺省回落**公开演示推导密钥** whsec_demo_<channelId>（公式公开、非秘密，仅限本地演示），' +
    '生产必须设环境变量 WARROOM_WEBHOOK_KEY 覆盖，否则入站端点等同无鉴权。',
  inputSchema: {
    type: 'object',
    properties: {
      title: { type: 'string', description: '消息标题（必填，<=512 字；超出截断，裸换行会被压成空格）' },
      body: { type: 'string', description: '消息正文（<=4000 字）' },
      level: {
        type: 'string',
        description:
          '告警级别，默认 info；**urgent 是语音播报的唯一触发条件**。' +
          '大小写不敏感，且接受服务端同口径别名：critical/fatal/error/high/p0/sev1/p1 → urgent；' +
          'warn/medium/moderate/p2 → warning；notice/debug/low/ok → info。未知值回落 info。',
      },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: {
        type: 'string',
        description:
          '幂等键（可选，一般不用给）：缺省按「标题指纹 + 30s 桶」自动生成 —— 不同标题各占一条，' +
          '同标题 30s 内重调折叠。要「同一标题在不同时间各推一次」或要让重试严格幂等，才显式传。',
      },
    },
    required: ['title'],
  },
};

const NOTIFY_DEF = {
  name: 'notify_task_complete',
  description:
    '任务收尾时推一条「✅ 任务完成」通知到作战室（默认 ch-workbuddy），配合「每轮自动提交远程」工作流。' +
    'summary 写本轮做了什么（给结论，别贴原始日志）；commit 可选填提交哈希（省略时自动 git rev-parse --short HEAD，并附「已推送远程 <commit>」）；level 默认 info。' +
    '多 AI 共用一块大屏时必须传 source，标题会自动变成「✅ {source} 任务完成」，否则分不清是谁推的同款标题。' +
    '「需要人介入 / 告警 / 待办」请改用 push_warroom_event，别用本工具。' +
    'agent 每轮任务收尾时用 CLI 调用：node warroom-webhook.cjs --notify --summary "..." [--commit <hash>]。',
  inputSchema: {
    type: 'object',
    properties: {
      summary: { type: 'string', description: '本轮完成内容摘要（必填）' },
      commit: { type: 'string', description: '本轮提交哈希（可选，省略则自动取最新提交）' },
      level: {
        type: 'string',
        description:
          '告警级别，默认 info；urgent 会触发语音播报。大小写不敏感，接受服务端同口径别名' +
          '（critical/fatal/error/high/p0/sev1/p1 → urgent 等）。',
      },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: {
        type: 'string',
        description:
          '幂等键（可选，一般不用给）：缺省按 commit-<hash>（同一轮重推折叠），无 commit 时回落来源。' +
          '「同一提交要再推一条」这类场景才显式传。',
      },
    },
    required: ['summary'],
  },
};

const NOTIFY_CREATED_DEF = {
  name: 'notify_task_created',
  description:
    '新建一条待办时推一条「📋 新建任务计划：<标题>」通知到作战室（默认 ch-workbuddy）。' +
    'subject 写待办标题（必填，会进标题，<=120 字）；detail 写待办详情（可选，<=4000 字）；level 默认 info（阻塞性的待办可传 warning）。' +
    '多 AI 共用一块大屏时必须传 source，标题会自动变成「📋 {source} 新建任务计划：<标题>」。' +
    '与 notify_task_complete（一轮任务收尾摘要）不同：本工具针对「某条**具体待办被新建**」这个事件。' +
    '「已完成任务计划」请用 notify_task_done，别用本工具。',
  inputSchema: {
    type: 'object',
    properties: {
      subject: { type: 'string', description: '待办标题（必填，会进标题，<=120 字）' },
      detail: { type: 'string', description: '待办详情（可选，<=4000 字）' },
      level: {
        type: 'string',
        description:
          '告警级别，默认 info；urgent 会触发语音播报。大小写不敏感，接受服务端同口径别名' +
          '（critical/fatal/error/high/p0/sev1/p1 → urgent 等）。',
      },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: {
        type: 'string',
        description:
          '幂等键（可选，一般不用给）：缺省按「来源 + 待办标题指纹」自动生成 —— ' +
          '同一条待办重推会折叠成一条；同名待办要在不同时间各推一次，才显式传。',
      },
    },
    required: ['subject'],
  },
};

const NOTIFY_DONE_DEF = {
  name: 'notify_task_done',
  description:
    '某条具体已完成任务计划时推一条「✅ 已完成任务计划：<标题>」通知到作战室（默认 ch-workbuddy）。' +
    'subject 写已完成的待办标题（必填，会进标题，<=120 字）；detail 写完成情况说明（可选，<=4000 字）；level 默认 info。' +
    '多 AI 共用一块大屏时必须传 source，标题会自动变成「✅ {source} 已完成任务计划：<标题>」。' +
    '与 notify_task_complete（一轮任务收尾摘要）不同：本工具针对「某条**具体已完成任务计划**」这个事件。' +
    '「新建任务计划」请用 notify_task_created，别用本工具。',
  inputSchema: {
    type: 'object',
    properties: {
      subject: { type: 'string', description: '已完成的待办标题（必填，会进标题，<=120 字）' },
      detail: { type: 'string', description: '完成情况说明（可选，<=4000 字）' },
      level: {
        type: 'string',
        description:
          '告警级别，默认 info；urgent 会触发语音播报。大小写不敏感，接受服务端同口径别名' +
          '（critical/fatal/error/high/p0/sev1/p1 → urgent 等）。',
      },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: {
        type: 'string',
        description:
          '幂等键（可选，一般不用给）：缺省按「来源 + 待办标题指纹」自动生成 —— ' +
          '同一条待办的完成通知重推会折叠成一条；要重开同一标题的待办并各推一次，才显式传。',
      },
    },
    required: ['subject'],
  },
};

const NOTIFY_TURN_START_DEF = {
  name: 'notify_turn_start',
  description:
    '【仅当 instructions 判定「没有 hook 覆盖」时才调】轮次开始时推一条「🙋 收到指令」到作战室（默认 ch-workbuddy）。' +
    'MCP 是客户端驱动协议：服务端**无法**感知「用户刚开口」，也**没有轮询**（你只会因用户消息被唤醒）——轮次边界要么由宿主 hook 产生，' +
    '要么由你每轮主动调本工具补。**该不该调，看 initialize 的 instructions 里「【轮次播报 · 结论已现探】」那一行**：' +
    '它给的是本机事实（hook 日志最近活动 / 接收端 / 注册痕迹），不要按宿主品牌自己猜。' +
    'prompt 可选（传用户原话做正文，便于大屏看清这轮在问什么）；不传也能调，调用成本≈0。' +
    '⚠️ 与 notify_turn_end 成对使用；判定为「hook 已覆盖」时**不要**调（会与 hook 重复上屏）。',
  inputSchema: {
    type: 'object',
    properties: {
      prompt: { type: 'string', description: '用户原话（可选，作为「收到指令」的正文；不传则正文为空）' },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: { type: 'string', description: '幂等键（可选，一般不用给；缺省按「用户原话指纹 + 30s 桶」自动生成）' },
    },
    required: [],
  },
};

const NOTIFY_TURN_END_DEF = {
  name: 'notify_turn_end',
  description:
    '【仅当 instructions 判定「没有 hook 覆盖」时才调】轮次结束时推一条「✅ {source} 任务完成」到作战室（默认 ch-workbuddy）。' +
    '与 hook 侧 Stop 的落点一致；**普通对话也要调**（不只有多任务时），否则大屏看不到轮次收尾。' +
    'summary 可选（写本轮结论；不传会以「（本轮无摘要）」占位）；commit 可选（省略自动取最新提交）。' +
    '⚠️ **该不该调看 instructions 里「【轮次播报 · 结论已现探】」那一行**，不要按宿主品牌猜；' +
    '判定为「hook 已覆盖」时不要调，也不要同时调 notify_task_complete（收尾语义重叠，会重复上屏）。',
  inputSchema: {
    type: 'object',
    properties: {
      summary: { type: 'string', description: '本轮结论摘要（可选；不传以「（本轮无摘要）」占位）' },
      commit: { type: 'string', description: '本轮提交哈希（可选，省略则自动取最新提交）' },
      level: {
        type: 'string',
        description:
          '告警级别，默认 info；urgent 会触发语音播报。大小写不敏感，接受服务端同口径别名' +
          '（critical/fatal/error/high/p0/sev1/p1 → urgent 等）。',
      },
      channelId: { type: 'string', description: '目标工位 channelId，默认 ch-workbuddy' },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
      externalId: { type: 'string', description: '幂等键（可选，一般不用给；缺省按「摘要指纹 + 30s 桶」自动生成）' },
    },
    required: [],
  },
};

const SETUP_DEF = {
  name: 'setup_receiving_endpoint',
  description:
    '【接入第一步 · 必须先调】识别并装配「接收端」：用户提供从用户中心「接入凭证 → 工位」复制的完整入站地址' +
    '（形如 https://<中台>/api/v2/webhook/<租户>/<工位channelId>?key=<密钥>），本工具解析出服务端基址、租户、工位与密钥，' +
    '设为默认推送目标（**持久化到本地状态文件，跨进程重启 / 宿主 Hook 均会读回，不再回落 localhost:3500**），' +
    '并推送一条「🟢 服务上线」确认连接，最后回显**匹配的可用消息模板清单**' +
    '（notify_task_complete / notify_task_created / notify_task_done / push_warroom_event 各自的触发场景），' +
    '并在返回末尾提示 AI**转告用户、咨询「这些模板的标题/文案需要改吗」**（见 SKILL.md §7.1 第 6 步）。' +
    '本工具调用之前，本服务**不会**向任何地址发消息 —— 这是「安装服务」与「真正推送」之间的分水岭。' +
    'endpoint 必填；source 可选（多 AI 分辨，否则回落「未署名客户端」）。',
  inputSchema: {
    type: 'object',
    properties: {
      endpoint: {
        type: 'string',
        description:
          '接收端 URL（必填）：用户中心「接入凭证 → 工位」复制的完整入站地址，' +
          '含 /api/v2/webhook/<租户>/<工位>?key=<密钥>（旧部署为单段 /api/v1/webhook/<工位>?key=<密钥>）',
      },
      source: { type: 'string', description: SOURCE_DESC },
      aiName: { type: 'string', description: 'source 的兼容别名（两者都给时 aiName 优先）' },
    },
    required: ['endpoint'],
  },
};

// ================= CLI 一次性推送模式 =================
// agent 每轮任务完成后调用，不启动 stdio 服务。
function runCliNotify() {
  const get = (k) => {
    const i = process.argv.indexOf(k);
    return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : '';
  };
  const summary = get('--summary');
  if (!summary) {
    process.stderr.write('缺少 --summary 参数\n');
    process.exit(2);
  }
  const level = get('--level') || 'info';
  const channelId = get('--channel') || DEFAULT_CHANNEL;
  const title = get('--title');
  // 「已推送远程 <hash>」只对**任务完成通知**有意义：给了 --title 的通用推送
  //（告警 / 待办 / 需要你操作）不该被塞进 commit —— 语义不符，也无从推断属于哪次提交。
  // v1.2.0 的「省略自动取最新提交」保留给任务完成路径；通用推送仅在显式 --commit 时才带。
  const commit = get('--commit') || (title ? '' : detectCommit());
  // 多 AI 可分辨（audit-mcp §1.8）：--source 优先，其次环境变量 WARROOM_AI_NAME
  // （各宿主在自己的 mcp.json / 启动脚本里设一次，之后不用每条都传）。
  const source = get('--source') || process.env.WARROOM_AI_NAME || '';
  // 幂等键（可选）：hook 用它区分各事件、避免都落到 source 常量上互相覆盖。
  // 省略时保持旧行为（给了 --title 回落 ai:<source>；任务完成回落 commit-<hash>）。
  const externalId = get('--external-id');
  // v1.2.1：给 --title 时走通用推送（自定义标题），用于「待你操作 / 阻塞」类事件，
  // 避免和「✅ 任务完成」混用同一标题造成大屏误读；不给 --title 则走任务完成通知。
  const task = title
    ? pushEvent({
        title,
        body: commit ? summary + '\n\n已推送远程 ' + commit : summary,
        level,
        channelId,
        source,
        externalId,
      })
    : notifyTaskComplete({ summary, commit, level, channelId, source, externalId });
  task
    .then((out) => {
      process.stdout.write(out + '\n');
      process.exit(0);
    })
    .catch((e) => {
      process.stderr.write('推送失败：' + (e instanceof Error ? e.message : String(e)) + '\n');
      process.exit(1);
    });
}

// ================= CLI：一次性配置接收端（连接器形态 / 无 MCP 会话时用）=================
// 🔴 为什么需要它：连接器包是「远程 MCP + 宿主 hook」，本机没有常驻的 stdio MCP 进程，
//    所以 setup_receiving_endpoint 那个工具（服务端实现）**够不到本地状态文件**。
//    而 hook 是独立进程，只能读 `~/.warroom/receiving-endpoint.json`。
//    → 给一条纯 CLI 的落盘通道：用户把完整入站地址贴进对话，AI 跑这一条即可。
//    解析器 / 落盘 / 脱敏全部复用上面的同一份实现，不另起一套。
function runCliSetup(url) {
  let parsed;
  try {
    parsed = parseReceivingEndpoint(url);
  } catch (e) {
    process.stderr.write('✗ ' + (e instanceof Error ? e.message : String(e)) + '\n');
    process.exit(1);
    return;
  }
  const { base, tenantId, channelId, key } = parsed;
  const persisted = persistReceivingEndpoint({ base, tenantId, channelId, key });
  const lines = [
    '✅ 已识别接收端：',
    '   服务端基址：' + base,
    '   租户 tenantId：' + (tenantId || '（无 —— 按 V1 单段形状发送）'),
    '   工位 channelId：' + channelId,
    '   密钥：' + maskKey(key),
    '   持久化路径：' + (stateFilePath() || '(不可用)'),
    '   持久化结果：' + (persisted ? '已落盘（宿主 Hook 独立进程会读回）' : '⚠ 落盘失败（检查该路径是否可写）'),
  ];
  process.stdout.write(lines.join('\n') + '\n');
  // 未指定 --push 时**不推送**：这条命令要能在离线 / 自检环境里跑出确定结果。
  if (process.argv.includes('--push')) {
    process.env.WARROOM_API_BASE = base;
    process.env.WARROOM_WEBHOOK_KEY = key;
    process.env.WARROOM_CHANNEL = channelId;
    if (tenantId) process.env.WARROOM_TENANT = tenantId;
    return pushOnline('命令行配置（--setup）', channelId).then(() => process.exit(0));
  }
  process.exit(0);
}

// ---------- CLI：--coverage（轮次播报该由谁负责？） ----------
// 为什么给 CLI 而不是再加一个 MCP 工具：这是「排查/验收」动作，人也会用一条命令问；
// 加工具会改 tools/list 数量（5/7 个的口径写在 SKILL、连接器、护栏里，牵一发动全身）。
// 输出与 initialize 的 instructions 同源，避免「文档说一套、进程判另一套」。
function runCliCoverage() {
  const cov = probeTurnCoverage();
  console.log('轮次播报判定（读本机事实，不按宿主品牌猜）');
  console.log('  结论        : ' + summarizeCoverage(cov));
  console.log('  mode        : ' + cov.mode + '（confidence=' + cov.confidence + '）');
  console.log('  该怎么办    : ' + (cov.mode === 'hook'
    ? '不要调 notify_turn_start / notify_turn_end（hook 已覆盖）'
    : cov.mode === 'self'
      ? 'AI 必须每轮成对调 notify_turn_start / notify_turn_end'
      : '默认不调；先问用户大屏上有没有「🙋 收到指令」'));
  console.log('  依据        : ' + cov.reason);
  console.log('  证据：');
  for (const e of cov.evidence) console.log('    · ' + e);
  console.log('  hook 日志   : ' + (cov.logPath || '(不可用)'));
  console.log('  接收端      : ' + (cov.receiving.ok ? cov.receiving.base + ' / ' + cov.receiving.channelId : '（缺失或仅回环）'));
  process.exit(0);
}

if (process.argv.includes('--coverage')) {
  runCliCoverage();
} else if (process.argv.includes('--setup')) {
  const i = process.argv.indexOf('--setup');
  const url = process.argv[i + 1];
  if (!url || url.startsWith('--')) {
    process.stderr.write(
      '用法：node warroom-webhook.cjs --setup "<完整入站地址>" [--push]\n' +
        '  例：node warroom-webhook.cjs --setup "https://wr.aiwho.cn/api/v2/webhook/test01/ch-workbuddy?key=xxx"\n',
    );
    process.exit(1);
  }
  runCliSetup(url);
} else if (process.argv.includes('--notify')) {
  runCliNotify();
} else {
  // ================= 服务态：stdio JSON-RPC 2.0 =================
  let buf = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (chunk) => {
    buf += chunk;
    let idx;
    while ((idx = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, idx).trim();
      buf = buf.slice(idx + 1);
      if (line) handle(line);
    }
  });
  process.stdin.on('end', () => {
    if (buf.trim()) handle(buf.trim());
  });

  function send(obj) {
    process.stdout.write(JSON.stringify(obj) + '\n');
  }
  function log(...a) {
    process.stderr.write(a.join(' ') + '\n');
  }

  // 已注册的工具白名单（修 audit-mcp §1.7：工具名拼错此前会被静默当成
  // push_warroom_event 执行 —— 调用方以为调了 A，实际执行了 B，且返回成功）。
  const TOOLS = {
    push_warroom_event: pushEvent,
    notify_task_complete: notifyTaskComplete,
    notify_task_created: notifyTaskCreated,
    notify_task_done: notifyTaskDone,
    notify_turn_start: notifyTurnStart,
    notify_turn_end: notifyTurnEnd,
    setup_receiving_endpoint: setupReceivingEndpoint,
  };

  // MCP 生命周期状态机（修 audit-mcp §1.2 P0）：
  // 旧实现不校验握手，不发 initialize 直接 tools/call 照样成功 ——
  // 「协议宽松 = 每个客户端行为不一致 = 出问题时无处归因」。
  // 按 MCP 规范：initialize 之前调用其它方法一律 -32002。
  let initialized = false;

  // 1.5.0：入站地址支持 V2 双段（/api/v2/webhook/<租户>/<工位>），并保留 V1 单段兼容。
  const SERVER_INFO = { name: 'warroom-webhook', version: '1.5.0' };
  // instructions：MCP 里**唯一**能在一开始告诉 AI「什么场景该调这个工具」的位置。
  // 此前为空 —— 宿主只能靠工具 description 自己猜。这段文本与
  // .agents/skills/webroom-webhook/SKILL.md 的「AI 调用时请遵守」同源。
  //
  // 🔴 2026-10-23 改：轮次播报那一段不再写死「按宿主品牌判断」，改为**每次握手现探**（见 lib/turn-coverage.cjs）。
  //    原因：旧文案让 WorkBuddy / Claude Code 上的 AI 一律「不要调」，但 hook 可能压根没装、
  //    装了指到失效路径、或没有接收端（hook 静默跳过）—— 那三种情况下大屏一条轮次消息都没有，
  //    而 AI 读到的指令是「不要调」，双方零报错、无从发现。现改为把**本地事实**（hook 日志最近活动 /
  //    接收端文件 / 注册痕迹）直接断言给 AI，并区分「hook 在跑」「hook 在跑但推错工位」「没有 hook」三种结论。
  function buildInstructions(cov) {
    const turnBlock = ['【轮次播报 · 结论已现探，不要靠宿主品牌猜】' + summarizeCoverage(cov)];
    turnBlock.push('判定：' + cov.reason);
    if (cov.mode === 'hook') {
      turnBlock.push('→ 已覆盖，本轮及后续都**不要**调 notify_turn_start / notify_turn_end。');
    } else if (cov.mode === 'self') {
      turnBlock.push('→ 每收到一条用户消息、开始回答前 → notify_turn_start（prompt 传用户原话，可不传）；');
      turnBlock.push('  本轮回答结束时（**包括普通对话**）→ notify_turn_end（summary 写本轮结论，可不传）。两者成对，别只调一个。');
      turnBlock.push('  🔴 这里**没有轮询**：MCP 是客户端驱动，你不会被定时唤醒，服务端也无法主动问你 —— 只有你每轮主动调，大屏才有轮次边界。');
    } else {
      turnBlock.push('→ 先问用户一句「大屏上能看到『🙋 收到指令』吗？」：看得到 → 不要调；看不到 → 本轮起每轮成对调（同上一行）。');
    }
    return [
      '把告警 / 任务完成 / 待办阻塞推送到 AIWHO WEBHOOK中台（作战室大屏 + TTS 语音播报）。',
      '【接入顺序 · 先装服务，后给接收端】本 MCP 接入后**不会**自动推送任何消息。请等用户登录用户中心 →「接入凭证」→ 工位复制',
      '完整入站地址（形如 https://<中台>/api/v2/webhook/<租户>/<工位>?key=<密钥>）贴给你，然后调用',
      'setup_receiving_endpoint 识别工位+密钥并设为默认推送目标、确认连接。只有这一步之后才推送消息。',
      '【场景 → 怎么调】先判断场景再选工具，别所有情况都套同一个：',
      '· 一轮任务收尾、要告诉大屏「本轮干了什么」 → notify_task_complete（summary 写结论；commit 省略会自动取最新提交）',
      '· 新建了一条待办 → notify_task_created（subject 写待办标题；阻塞性的待办 level=warning）',
      '· 某条具体已完成任务计划 → notify_task_done（subject 写待办标题）',
      '· 需要人介入（阻塞 / 等你确认 / 要你补信息） → push_warroom_event，title 以「⚠️ 需要你操作：」开头，level=urgent',
      '· 关键失败 / 线上异常 → push_warroom_event，title 写清现象，level=urgent',
      '· 普通进展 / 信息同步 → push_warroom_event，level=info（别用 urgent，会打扰人）',
      turnBlock.join('\n'),
      '【级别】urgent 才会触发语音播报，是唯一触发条件；级别宁低勿高。大小写不敏感，认别名（critical/fatal/p0/sev1 → urgent）。',
      '【正文】给结论，不给原始日志；标题 <=512 字、正文 <=4000 字，超出会被截断。',
      '【多 AI】请传 source（如 CodeBuddy / Cursor / 自研 Agent），标题会自动变成「✅ CodeBuddy 任务完成」；',
      '否则大屏会是一串分不清是谁推的同款标题。也可用环境变量 WARROOM_AI_NAME 固定本宿主的来源名。',
    ].join('\n');
  }

  // ---------- 服务上线通知：不再在 initialize 时自动推 ----------
  // 旧实现挂在 initialize 上、任何 AI 一握手就推一条「🟢 服务上线」，发生在用户还没给
  // 服务端地址/工位/密钥之前，等于「连上即推测试」。现已改为：安装服务（仅接线）后，
  // AI 等用户贴来完整入站地址，再调 setup_receiving_endpoint 识别工位+密钥、
  // 设为会话默认推送目标，并在那一步才推「服务上线」确认（见模块级 setupReceivingEndpoint）。
  // 仍需关闭上线通知时（如护栏脚本避免污染抓包），设 WARROOM_ONLINE_NOTIFY=0。



  async function handle(line) {
    let msg;
    try {
      msg = JSON.parse(line);
    } catch {
      // 解析失败：有 id 也回 -32700（宽松客户端可能带 id），没 id 只写 stderr。
      log('[warroom-webhook] JSON 解析失败，已忽略一行输入');
      return;
    }
    if (msg === null || typeof msg !== 'object') return;
    const { id, method, params } = msg;

    // 通知（无 id，或 notifications/* 前缀）**一律不回包**（修 audit-mcp §1.2）：
    // 严格客户端会因「通知收到响应」或「响应缺 id 字段」判报文法错误。
    const isNotification =
      id === undefined || id === null || (typeof method === 'string' && method.startsWith('notifications/'));
    if (isNotification) {
      if (method === 'notifications/initialized') {
        log('[warroom-webhook] 客户端握手完成');
      } else if (method !== undefined) {
        log('[warroom-webhook] 收到通知 ' + method + '（按规范不回包）');
      }
      return;
    }

    // 握手前只允许 initialize / ping（ping 用于探活，规范允许）
    if (!initialized && method !== 'initialize' && method !== 'ping') {
      send({
        jsonrpc: '2.0',
        id,
        error: { code: -32002, message: 'Server not initialized：请先调用 initialize' },
      });
      return;
    }

    if (method === 'initialize') {
      initialized = true;
      // 握手这一下就把「轮次播报到底谁负责」探出来（读本地 hook 日志 / 接收端 / 注册痕迹），
      // 让模型拿到断言而不是让它按宿主品牌猜 —— 这是本文件唯一能在会话初始发声的地方。
      const cov = currentCoverage(true);
      send({
        jsonrpc: '2.0',
        id,
        result: {
          // 回自己支持的版本。规范允许服务端在客户端版本不兼容时回自己的版本
          // （客户端应据此决定是否继续）；此处固定为当前实现的协议版本。
          protocolVersion: '2024-11-05',
          capabilities: { tools: { listChanged: false } },
          serverInfo: SERVER_INFO,
          instructions: buildInstructions(cov),
        },
      });
      // 回包必须先发（客户端不该等我们推消息）。注意：**不在握手时推送任何消息** ——
      // 服务上线确认改由 setup_receiving_endpoint 在用户给出接收端之后才推。
      return;
    }
    if (method === 'ping') {
      send({ jsonrpc: '2.0', id, result: {} });
      return;
    }
    if (method === 'tools/list') {
      send({ jsonrpc: '2.0', id, result: { tools: [SETUP_DEF, TOOL_DEF, NOTIFY_DEF, NOTIFY_CREATED_DEF, NOTIFY_DONE_DEF, NOTIFY_TURN_START_DEF, NOTIFY_TURN_END_DEF] } });
      return;
    }
    if (method === 'tools/call') {
      const name = params && params.name;
      // 白名单：未知工具名显式报错，**不再静默执行推送**（修 §1.7）。
      if (typeof name !== 'string' || !Object.prototype.hasOwnProperty.call(TOOLS, name)) {
        send({
          jsonrpc: '2.0',
          id,
          result: {
            content: [
              {
                type: 'text',
                text:
                  'Error: 未知工具 "' + String(name) + '"（本服务仅注册：' +
                  Object.keys(TOOLS).join(' / ') + '）',
              },
            ],
            isError: true,
          },
        });
        return;
      }
      try {
        const text = await TOOLS[name](params);
        send({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text }] } });
      } catch (e) {
        const err = e instanceof Error ? e.message : String(e);
        send({
          jsonrpc: '2.0',
          id,
          result: { content: [{ type: 'text', text: 'Error: ' + err }], isError: true },
        });
      }
      return;
    }
    send({ jsonrpc: '2.0', id, error: { code: -32601, message: 'method not found: ' + method } });
  }

  // 启动时已按优先级解析 BASE（env > 持久化接收端 > localhost:3500 兜底），把**来源**说清楚，
  // 避免「回落到不存在的 localhost:3500 静默推失败」时无从排查。注意来源要用解析时记下的
  // BASE_SOURCE —— resolveBaseAndChannel 会把持久化值回写进 process.env，据此判断会误报成「env 显式指定」。
  log('[warroom-webhook] MCP 就绪，后端基址=' + BASE + '（来源：' + (BASE_SOURCE || '未知') + '）');
}
