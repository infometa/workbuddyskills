// 演示推导式入站密钥的**唯一来源**（single source of truth）。
//
// `whsec_demo_<channelId>` 的公式公开可推导，本质是「公开演示值、不是密钥」：
// 任何人知道工位 id 就能算出它、伪造入站推送。但它在仓库里被 **多 处各自实现**过
// （mcp/warroom-webhook.cjs、mcp/git-hooks/notify-commit.cjs、
//  server/scripts/ws-fanout-probe.mjs、server/scripts/setup-workbuddy.ts，
//  另加服务端护栏里的前缀常量）。
// 公式一旦要改（例如换前缀、加环境维度），需要五处同时改对，且**没有任何检查**
// 会发现漏改的那一处 —— 典型的「注释里写着需同步、实际靠记性」。
//
// 本文件把它收成一处：MJS 侧（MCP / 探针脚本）直接 import；
// TS 侧 runtime 代码不跨目录 import（tsconfig rootDir=src，且 scripts/ 不在构建产物里），
// 由 scripts/demo-secret-check.mjs 做**十字定位** —— 任何人改公式只改一份、其余报错。
//
// 常量与函数都要能被静态抽取，故不写类型注解（本文件是 .mjs，随 node 直跑）。

/** 推导式演示密钥的固定前缀（公式：前缀 + channelId）。 */
export const DEMO_SECRET_PREFIX = 'whsec_demo_';

/** 由工位 id 推导演示密钥。 */
export function deriveDemoSecret(channelId) {
  return `${DEMO_SECRET_PREFIX}${channelId}`;
}

/**
 * 「覆盖优先」解析入站密钥：显式环境变量（真密钥）优先，否则回落推导式演示值。
 *
 * 回落是**静默**的 —— 这正是需要生产护栏（server/src/services/securityGuard.ts）的原因：
 * 注释拦不住一次生产部署，只有启动期硬检查能。
 */
export function resolveWebhookSecret(channelId, envValue = process.env.WARROOM_WEBHOOK_KEY) {
  const explicit = (envValue ?? '').trim();
  return explicit !== '' ? explicit : deriveDemoSecret(channelId);
}

/** 判断一份密钥是否是推导式演示值（不校验 channelId 是否匹配）。 */
export function isDerivedDemoSecret(secret) {
  return typeof secret === 'string' && secret.startsWith(DEMO_SECRET_PREFIX);
}

/**
 * 默认工位 id。
 *
 * `ch-workbuddy` 此前在 3 处各写一份（mcp/warroom-webhook.cjs 的 DEFAULT_CHANNEL、
 * mcp/git-hooks/notify-commit.cjs 的 WARROOM_NOTIFY_CHANNEL 兜底、
 * server/scripts/ws-fanout-probe.mjs 的 WARROOM_CHANNEL 兜底），
 * 改默认工位要同时改对 3 处。这里收成一处，MJS 侧直接引用，由
 * scripts/demo-secret-check.mjs 校验 TS 侧（setup-workbuddy 的建站 id）与之一致。
 */
export const DEFAULT_DEMO_CHANNEL = 'ch-workbuddy';
