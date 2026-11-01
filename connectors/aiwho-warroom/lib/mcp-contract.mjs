// MCP / CLI / Skill 共用的入站契约**唯一来源**（single source of truth）。
//
// 为什么需要它：同一份契约此前散在三处，且**各写一份口径**：
//   1. `mcp/warroom-webhook.cjs` 的 `inputSchema` 与参数校验（工具自述）；
//   2. `.agents/skills/webroom-webhook/SKILL.md`（写给 AI 看的文档）；
//   3. `server/src/`（运行时权威：normalizers/levelMap.ts 的 coerceLevel、openapi 的 maxLength）。
//
// 漂移的后果是**语义静默失效**：MCP 侧 `level` 只认小写 `urgent`，而服务端
// `coerceLevel` 大小写不敏感且认 `critical`/`fatal`/`p0` 等别名 —— 两边不一致时，
// 用 `critical` 推的消息会被 MCP 静默降成 `info`，而 **urgent 是语音播报的唯一触发条件**
// → 大屏不播报、零报错。见 `docs/audit-2026-09-19-mcp.md` §1.6。
//
// 本文件是 .mjs（随 node 直跑，可被 MCP/脚本 import），与 demo-secret.mjs 同一约定：
// 常量与函数可静态抽取，不写类型注解。TS 侧由其自身实现 + `mcp-contract-check.mjs` 十字校验。

/** 级别白名单（与 server/src/lib/constants.ts 的 MESSAGE_LEVELS 同值）。 */
export const MESSAGE_LEVELS = ['info', 'warning', 'urgent'];

/** title 上限（与 docs/openapi.yaml 的 Message.title.maxLength / @db.VarChar(512) 同值）。 */
export const WEBHOOK_TITLE_MAX = 512;

/** body 上限（与 openapi Message.body.maxLength 同值）。 */
export const WEBHOOK_BODY_MAX = 4000;

/** 默认摘要上限（普通消息外置字段，非 openapi 字段，由 MCP 自己约束）。 */
export const WEBHOOK_SUMMARY_MAX = 4000;

/**
 * 跨平台通用别名表 —— **必须与服务端 `coerceLevel` 的别名分支逐条同值**。
 *
 * 服务端 coerceLevel（server/src/normalizers/levelMap.ts:81）的真实口径：
 *   1. 原值命中白名单 → 直接返回（大小写敏感，因为白名单本身全小写）；
 *   2. 非字符串 / 空串 → fallback；
 *   3. 转小写后先查用户 levelMap，再查下面的通用别名；
 *   4. 未命中 → fallback。
 *
 * MCP 侧不接收用户 levelMap（那是工位配置，不是工具参数），故只覆盖 1/2/3 的通用别名部分。
 */
export const LEVEL_ALIASES = {
  fatal: 'urgent',
  critical: 'urgent',
  urgent: 'urgent',
  p0: 'urgent',
  sev1: 'urgent',
  error: 'urgent',
  err: 'urgent',
  high: 'urgent',
  p1: 'urgent',
  warning: 'warning',
  warn: 'warning',
  medium: 'warning',
  moderate: 'warning',
  p2: 'warning',
  info: 'info',
  notice: 'info',
  debug: 'info',
  low: 'info',
  ok: 'info',
};

/**
 * 把入参级别收敛成白名单三值，**与服务端 coerceLevel 逐条同口径**。
 *
 * @param {unknown} raw 原始值
 * @param {'info'|'warning'|'urgent'} fallback 未命中时的兜底（服务端入站路径传 'info'）
 * @returns {'info'|'warning'|'urgent'}
 */
export function coerceLevel(raw, fallback = 'info') {
  if (typeof raw === 'string') {
    const s = raw.trim().toLowerCase();
    if (s === 'info' || s === 'warning' || s === 'urgent') return s;
    if (Object.prototype.hasOwnProperty.call(LEVEL_ALIASES, s)) return LEVEL_ALIASES[s];
  }
  return fallback;
}

/**
 * 收敛 title：去除裸换行（title 会进前端承载层与**播报文本**，裸换行会把一行标题
 * 拆成两行、后续行被当成正文渲染 —— 见 audit-mcp §1.5），并按契约上限截断。
 */
export function sanitizeTitle(raw, fallback = '') {
  const s = raw === undefined || raw === null ? fallback : String(raw);
  // 换行 / 回车 / 其他行分隔符统一压成空格（不删字，避免相邻词粘连）
  const oneLine = s.replace(/[\r\n\u2028\u2029]+/g, ' ');
  return oneLine.trim().slice(0, WEBHOOK_TITLE_MAX);
}

/** 收敛 body：仅按契约上限截断（正文允许换行）。 */
export function sanitizeBody(raw, fallback = '') {
  const s = raw === undefined || raw === null ? fallback : String(raw);
  return s.slice(0, WEBHOOK_BODY_MAX);
}

// ─────────────────────────────────────────────────────────────────────────────
// 多 AI 可分辨（audit-mcp §1.8 / §3.4）
// 「全 AI 接入」的实际诉求之一是：多个 AI 推消息到同一工位时，**大屏上要分得清是谁推的**。
// 旧实现把标题写死成「✅ 任务完成」，多 AI 同时接入后就是一串同款标题。
// 修法是引入 `source`（AI 来源名）：
//   1) MCP 工具与 HTTP 传输都接受 `source` / `aiName`（同义，`aiName` 为兼容别名）；
//   2) 任务完成通知标题模板统一为 `✅ {source} 任务完成`（无 source 时退回旧标题）；
//   3) HTTP 传输写进 `externalId`（`ai:<source>`），让 /messages 与 /stats 能按 AI 分开。
// ─────────────────────────────────────────────────────────────────────────────

/** source（AI 来源名）长度上限。与 WEBHOOK_TITLE_MAX 同源考量：它会被拼进 title。 */
export const SOURCE_MAX = 32;

/** 任务完成通知的标题模板。`{source}` 会被替换成净化后的 source。 */
export const TASK_COMPLETE_TITLE = '✅ {source}任务完成';

/**
 * 收敛 source：去裸换行 + trim + 按上限截断。
 *
 * 为什么必须净化：source 会**被拼进 title**，而 title 会进播报文本 ——
 * 不净化等于把标题注入面从 title 扩到 source（audit-mcp §1.5 同类问题）。
 */
export function sanitizeSource(raw, fallback = '') {
  const s = raw === undefined || raw === null ? fallback : String(raw);
  return s.replace(/[\r\n\u2028\u2029]+/g, ' ').trim().slice(0, SOURCE_MAX);
}

/**
 * 任务完成通知的标题：`✅ {source} 任务完成`。
 * source 为空时退回 `✅ 任务完成`（保持与历史消息一致的观感，不出现 `✅ 任务完成` 前多一个空格）。
 */
export function taskCompleteTitle(rawSource) {
  const source = sanitizeSource(rawSource);
  return source.length > 0
    ? TASK_COMPLETE_TITLE.replace('{source}', source + ' ')
    : TASK_COMPLETE_TITLE.replace('{source}', '');
}

/** HTTP 传输的 externalId 前缀（让 /messages 能按 AI 筛选）。 */
export const AI_EXTERNAL_ID_PREFIX = 'ai:';

/**
 * 由 source 推出 externalId —— **让重推天然幂等**。
 *
 * 没有这一项时，HTTP 传输推的两条内容相同的消息会各自落一条（去重走 title+body+时间窗分支）；
 * 有了它，同一个 AI（或同一条通知）重投会被去重层折叠（`created:false`），
 * 这正是「AI 重试无害」的实现方式（Skill §2.5 对 AI 的承诺）。
 */
export function sourceExternalId(rawSource) {
  const source = sanitizeSource(rawSource);
  return source.length > 0 ? AI_EXTERNAL_ID_PREFIX + source : '';
}

// ---------- 待办类通知标题模板（notify_task_created / notify_task_done） ----------
// 与 TASK_COMPLETE_TITLE 同源风格：来源拼进标题（多 AI 可分辨），待办标题进标题（一眼看出建/完了什么）。

/** 新建任务计划通知标题模板（带来源与待办标题）。 */
export const TASK_CREATE_TITLE = '📋 {source}新建任务计划：{subject}';

/** 已完成任务计划通知标题模板（带来源与待办标题）。 */
export const TASK_DONE_TITLE = '✅ {source}已完成任务计划：{subject}';

/** 待办标题（subject）长度上限：它会被拼进 title，故单独收敛。 */
export const TASK_SUBJECT_MAX = 120;

/**
 * 新建任务计划通知标题：`📋 {source} 新建任务计划：{subject}`。
 * source 为空时退回 `📋 新建任务计划：{subject}`；subject 为空时退回「未命名待办」。
 */
export function taskCreateTitle(rawSource, subject) {
  const source = sanitizeSource(rawSource);
  const subj = (subject == null ? '' : String(subject))
    .replace(/[\r\n\u2028\u2029]+/g, ' ').trim().slice(0, TASK_SUBJECT_MAX) || '未命名待办';
  return `📋 ${source.length > 0 ? source + ' ' : ''}新建任务计划：${subj}`;
}

/**
 * 已完成任务计划通知标题：`✅ {source} 已完成任务计划：{subject}`。
 * 与 Hook 侧 TaskCompleted 的「✅ 已完成任务计划：<待办名>」同口径（operations.md），
 * 这里补上 source 以利多 AI 分辨。
 */
export function taskDoneTitle(rawSource, subject) {
  const source = sanitizeSource(rawSource);
  const subj = (subject == null ? '' : String(subject))
    .replace(/[\r\n\u2028\u2029]+/g, ' ').trim().slice(0, TASK_SUBJECT_MAX) || '未命名待办';
  return `✅ ${source.length > 0 ? source + ' ' : ''}已完成任务计划：${subj}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// 轮次类通知（notify_turn_start / notify_turn_end）—— 补齐「无 hook 宿主」的轮次播报
//
// 为什么需要：MCP 是**客户端驱动**协议，服务端只在客户端发 `tools/call` 时才知道发生了什么，
//   **没有原语**能感知「用户刚发了一条消息」「助手刚回答完」。这两个轮次信号今天只有宿主的
//   hook 能产生（`UserPromptSubmit` → 收到指令；`Stop` → 任务完成）。
//   于是纯 MCP 宿主（无 hook，如 OpenClaw）里：轮次开始没有事件、轮次结束也不会常态触发。
//   → 补一对「轮次工具」，让 AI 每轮自己调（名字即指令，参数全可选以降低调用成本）。
//
// 与 Hook 侧同口径：收到指令标题 `🙋 收到指令`（**不带** source，与 hook 的 `--title` 一致）；
//   轮次结束复用 `taskCompleteTitle`（`✅ {source}任务完成`，与 hook Stop 的落点一致）。
// ─────────────────────────────────────────────────────────────────────────────

/** 轮次开始（收到指令）标题。与 Hook `UserPromptSubmit` 的 `🙋 收到指令` 同口径（不带 source）。 */
export const TURN_START_TITLE = '🙋 收到指令';

/** 轮次开始标题 getter（与 taskXxxTitle 同风格，便于护栏统一断言）。 */
export function turnStartTitle() {
  return TURN_START_TITLE;
}

/**
 * 轮次幂等键的时间桶（ms）：同桶内重复调用折叠为一条，跨桶新增。
 * 取 30s —— 与 Hook 侧 `hook:prompt:…:<30s桶>` 同量级；目的是吸收「模型抖动重调」，
 * 又不至于把两次真实问话折叠（真实问话间隔通常 > 30s）。
 */
export const TURN_KEY_BUCKET_MS = 30 * 1000;

/** 轮次指纹：djb2 → base36。短且稳定，**仅用于幂等键**，不做安全用途。 */
export function turnFingerprint(s) {
  const t = String(s == null ? '' : s).replace(/\s+/g, ' ').trim().slice(0, 200);
  let h = 5381;
  for (let i = 0; i < t.length; i++) h = ((h << 5) + h + t.charCodeAt(i)) >>> 0;
  return h.toString(36);
}

/** 把 source 净化为幂等键片段：仅保留 ASCII 字母数字与 `_.-`，空则回落 `unknown`。 */
export function sourceSlug(rawSource) {
  const t = sanitizeSource(rawSource).replace(/[^0-9A-Za-z_.-]/g, '_');
  return /[0-9A-Za-z]/.test(t) ? t : 'unknown';
}

/**
 * 轮次开始（收到指令）的幂等键：`mcp:turn-start:<source|unknown>:<指纹>:<30s桶>`。
 * 指纹取**用户原话** → 不同提问永不互相折叠；同一提问 30s 内重调折叠（防抖动重复调）。
 */
export function turnStartExternalId(rawSource, prompt, now = Date.now()) {
  const bucket = Math.floor(now / TURN_KEY_BUCKET_MS).toString(36);
  return `mcp:turn-start:${sourceSlug(rawSource)}:${turnFingerprint(prompt)}:${bucket}`;
}

/**
 * 轮次结束（任务完成）的幂等键：`mcp:turn-end:<source|unknown>:<指纹>:<30s桶>`。
 *
 * 🔴 **不复用 `commit-<hash>`**：它在两次提交之间是**常量** → 多轮落同一条、而「去重命中不更新正文」
 * → 现场就是「调了也白调，大屏永远只有第一条」。这正是「轮次结束不能常态化」的隐藏主因。
 */
export function turnEndExternalId(rawSource, summary, now = Date.now()) {
  const bucket = Math.floor(now / TURN_KEY_BUCKET_MS).toString(36);
  return `mcp:turn-end:${sourceSlug(rawSource)}:${turnFingerprint(summary)}:${bucket}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// 事件类通知的幂等键（push_warroom_event / notify_task_created / notify_task_done）
//
// 【为什么必须有（Issue #2）】这三个工具此前的缺省键是 `sourceExternalId()` → `ai:<source>`
//   —— 对同一个来源是**常量**。而后端在有 externalId 时 hash 只算
//   `sha256(channelId + externalId)`（server/src/lib/dedupe.ts），**不含内容、不含时间窗**：
//   于是同一来源推的**不同**事件落到同一条记录上，后推原地覆盖先推，
//   返回体还照样是 `created:true` —— 现场症状是「三个工具连着调，大屏只剩最后一条」，
//   而且是**静默**的（HTTP 201、无任何告警）。
//
//   三代键的区别就在这里：
//     · `notify_turn_*` 早就用「内容指纹 + 30s 桶」，所以多个轮次天然各占一条；
//     · 本组三个工具漏了同一件事，缺省值退回常量；
//     · `notify_task_complete` 的 `commit-<hash>` 是**有意为之**（两次提交之间是常量，
//       用来把多轮折叠成一条），不在本组，也不该跟着改。
// ─────────────────────────────────────────────────────────────────────────────

/**
 * 待办类（新建 / 完成）的幂等键：`mcp:task-created:<source>:<subject 指纹>`。
 *
 * **刻意不带时间桶** —— 待办是**实体**，不是事件流：同一条待办被重推
 * （模型抖动重调、跨轮次又提一次）应当折叠成一条，而不是每 30 秒多一条重复。
 * 真要「同名待办在不同时间各推一次」，那是调用方语义，请显式传 `externalId`。
 */
export function taskCreatedExternalId(rawSource, subject) {
  return `mcp:task-created:${sourceSlug(rawSource)}:${turnFingerprint(subject)}`;
}

/** 已完成待办的幂等键：`mcp:task-done:<source>:<subject 指纹>`。规则同 taskCreatedExternalId。 */
export function taskDoneExternalId(rawSource, subject) {
  return `mcp:task-done:${sourceSlug(rawSource)}:${turnFingerprint(subject)}`;
}

/**
 * 通用推送的幂等键：`mcp:push:<source>:<title 指纹>:<30s 桶>`。
 *
 * **带时间桶** —— 推送是**事件流**：同标题的告警/进展在不同时刻是两件事，应当各占一条；
 * 而 30s 内重调（模型抖动）折叠，与 `notify_turn_*` 同量级、同一个 `TURN_KEY_BUCKET_MS`。
 */
export function pushExternalId(rawSource, title, now = Date.now()) {
  const bucket = Math.floor(now / TURN_KEY_BUCKET_MS).toString(36);
  return `mcp:push:${sourceSlug(rawSource)}:${turnFingerprint(title)}:${bucket}`;
}

// ─────────────────────────────────────────────────────────────────────────────
// HTTP 型 MCP 传输（audit-mcp §2 / §3.1 P1-3）
//
// 为什么必须有它：stdio 传输要求宿主**能在本机 spawn 子进程**，于是
//   浏览器里的 AI、只支持 HTTP 型 MCP 的宿主、云端 Agent —— 全都接不进来。
// 这是「全 AI 接入」今天的最后一块墙。
//
// 设计（与审计建议一致）：
//  - 传输内置进服务端静态路由 `POST /api/v2/mcp`：零外部端口、零三方依赖、天然可跨机访问；
//  - 鉴权挂**外层**：`Authorization: Bearer <令牌>`（复用现有 token 体系；令牌可以是手工签发的
//    ApiToken，也可以是 OAuth 2.1 签发的 access token —— 两者在服务端走同一条校验路径），
//    绝不接受「公开推导密钥」——那是演示值，不能用于远端可访问的端点；
//  - 入站推送仍走现有 `/api/v2/webhook/:tenantId/:channelId` 管线（归一化 / 去重 / 播报一行不改）。
// ─────────────────────────────────────────────────────────────────────────────

/** HTTP 传输端点路径（服务端注册、MCP http 客户端、Skill/README 三处必须同值）。 */
export const MCP_HTTP_PATH = '/api/v2/mcp';

/** HTTP 传输鉴权头名（外层鉴权，绝不用演示密钥）。 */
export const MCP_HTTP_AUTH_HEADER = 'Authorization';

/** HTTP 传输协议版本（与 stdio 侧 initialize 回包同值）。 */
export const MCP_PROTOCOL_VERSION = '2024-11-05';

/**
 * HTTP 传输的请求体上限（字节）。
 *
 * 与 Fastify 默认 bodyLimit（1 MiB，见 plugins 配置）取同一量级，但更小：
 * 一次 MCP 调用不需要 1 MiB —— 上限越小，远端把服务端当内存放大器打的门槛越高。
 */
export const MCP_HTTP_BODY_LIMIT = 512 * 1024;

/** HTTP 传输的工位限流（请求/分钟）。沿用入站契约的 120/min/工位量级。 */
export const MCP_HTTP_RATE_PER_MIN = 120;

/** `tools/call` 里**不接受**的参数名：工具名由 `params.name` 给，参数里再写一次只会造成歧义。 */
export const MCP_TOOL_CALL_RESERVED_KEYS = ['name', 'arguments', 'source', 'aiName'];

/**
 * `tools/call` 的 `params` 里**协议层**字段 —— 属于 MCP 报文结构，不是业务参数。
 *
 * `extractArgs` 的两个实现（stdio 侧 mcp/warroom-webhook.cjs、HTTP 侧
 * server/src/plugins/mcp-http.ts）做「平铺 vs arguments 互斥」判定时**必须**跳过它们，
 * 否则合规客户端带的 `_meta`（协议规定的进度追踪等保留字段）会被当成平铺业务参数，
 * 与 `arguments` 并存时误判为「参数形状混用」→ 工具调用直接失败。
 * 实测：宿主自动注入 `_meta` 时两次 tools/call 全被拒（audit 记录）。
 *
 * 与 `MCP_TOOL_CALL_RESERVED_KEYS` 的区别：**这个列表是"要忽略"，那个是"禁止出现"**
 * —— `name`/`arguments` 是结构字段（也在此忽略），`source`/`aiName` 是合法业务参数
 * （由工具 schema 定义），只是不允许重复出现在 params 顶层。
 */
export const MCP_TOOL_CALL_PROTOCOL_KEYS = ['name', 'arguments', '_meta'];
