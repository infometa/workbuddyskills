'use strict';
/*
 * 接收端绑定（服务端基址 + 工位 + 密钥）持久化。
 *
 * 为什么需要它（修 2026-10-10 实测 bug）：
 *   setup_receiving_endpoint 原本只把绑定写进「当前 MCP 进程内存」（BASE / DEFAULT_CHANNEL /
 *   process.env），进程一重启（宿主重启 / 重新信任连接器 / 升级）就回落 http://localhost:3500
 *   （本机 dev 端口，平时不开）→ 推送静默失败；而且宿主 Hook 是**独立进程**，读不到这份内存，
 *   所以连「不重启」时 Hook 自动推送也拿不到用户刚设的接收端。
 *
 * 做法：把绑定落盘到一个稳定状态文件，MCP 启动 / Hook 取连接参数时都优先读它。
 *   - 位置：WARROOM_RECEIVING_STATE 环境变量 > ~/.warroom/receiving-endpoint[.<scope>].json
 *   - scope：取 WARROOM_AI_NAME（多 AI 同机时各占一份，见 bindingScope 注释）
 *   - 优先级（两处共用）：显式 env（本地 dev 覆盖）> 持久化接收端（setup 写入）> mcp.json 声明基线 > localhost:3500 兜底
 *   - 文件权限 0600（Windows 忽略），密钥与 mcp.json 的 WARROOM_WEBHOOK_KEY 同级处理。
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

/**
 * 「这份绑定属于哪个 AI」—— 用于把状态文件按来源隔离。
 *
 * 为什么（2026-10-23 实测）：`~/.warroom/receiving-endpoint.json` 是**全机唯一**的一份，
 * 同一台机器上装两套 AI（本机就有 WorkBuddy + QClaw）时，谁跑 setup 谁就覆盖它 ——
 * QClaw 把自己的工位 `qclaw` 写了进去，而 WorkBuddy 的 hook 推的是 `ch-workbuddy`。
 * 两者各自没错，但**任何读这份文件的一方都会拿到别人的工位**，一旦本仓 MCP 装进
 * WorkBuddy 就会把消息推去 QClaw 的工位（零报错、只是「大屏上没有」）。
 *
 * 做法：优先用 `WARROOM_AI_NAME`（各宿主在 mcp.json 的 env 里配一次）当 scope，
 *   → 文件名变成 `receiving-endpoint.<scope>.json`，各 AI 互不干扰。
 *   没配 scope 时仍用旧文件名 `receiving-endpoint.json`（**老用户行为完全不变**）。
 * 显式 `WARROOM_RECEIVING_STATE` 依旧最高优先级（测试隔离 / 特殊部署）。
 */
function bindingScope() {
  const raw = String(process.env.WARROOM_AI_NAME || '').trim();
  if (!raw) return '';
  // 只留安全字符，避免把路径拼坏（source 允许中文，但文件名不必要地复杂）
  return raw.replace(/[^\w.-]+/g, '_').slice(0, 32);
}

function stateFilePath() {
  if (process.env.WARROOM_RECEIVING_STATE) return process.env.WARROOM_RECEIVING_STATE;
  const home = process.env.USERPROFILE || process.env.HOME || '';
  if (!home) return '';
  const scope = bindingScope();
  const file = scope ? 'receiving-endpoint.' + scope + '.json' : 'receiving-endpoint.json';
  return path.join(home, '.warroom', file);
}

/** 读持久化接收端；任何异常 / 缺字段一律返回 null（调用方回落其它来源）。 */
function loadReceivingEndpoint() {
  const p = stateFilePath();
  if (!p) return null;
  try {
    if (!fs.existsSync(p)) return null;
    const j = JSON.parse(fs.readFileSync(p, 'utf8'));
    if (!j || typeof j !== 'object') return null;
    if (!j.base || !j.channelId) return null;
    return {
      base: String(j.base).replace(/\/+$/, ''),
      // V2 入站路径的租户段（/api/v2/webhook/<tenantId>/<channelId>）。
      // 旧状态文件没有这个字段 → 空串，调用方据此回落 V1 单段形状（向后兼容）。
      tenantId: j.tenantId ? String(j.tenantId) : '',
      channelId: String(j.channelId),
      key: j.key ? String(j.key) : '',
      updatedAt: j.updatedAt ? String(j.updatedAt) : '',
    };
  } catch {
    return null;
  }
}

/** 原子写持久化接收端（先写 .tmp 再 rename，避免读到半截 JSON）。 */
function persistReceivingEndpoint(ep) {
  const p = stateFilePath();
  if (!p) return false;
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    const data = {
      base: String(ep.base).replace(/\/+$/, ''),
      tenantId: ep.tenantId ? String(ep.tenantId) : '',
      channelId: String(ep.channelId),
      key: ep.key ? String(ep.key) : '',
      updatedAt: new Date().toISOString(),
    };
    const tmp = p + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(data, null, 2), 'utf8');
    try {
      fs.chmodSync(tmp, 0o600);
    } catch {
      /* Windows 忽略 chmod */
    }
    fs.renameSync(tmp, p);
    return true;
  } catch {
    return false;
  }
}

/** 用于日志：把密钥脱敏展示。 */
function maskEndpoint(ep) {
  if (!ep) return '(未配置)';
  const key = ep.key
    ? ep.key.length <= 10
      ? '••••'
      : ep.key.slice(0, 6) + '…' + ep.key.slice(-4)
    : '';
  const tenant = ep.tenantId ? ` / 租户 ${ep.tenantId}` : '';
  return `${ep.base}${tenant} / ${ep.channelId}${key ? ' / 密钥 ' + key : ''}`;
}

module.exports = { stateFilePath, loadReceivingEndpoint, persistReceivingEndpoint, maskEndpoint, bindingScope };
