#!/usr/bin/env node
'use strict';

/**
 * hook-handler.js — page-deliver 指标上报 hook
 *
 * 单文件 CJS、零依赖。行为：
 *   把 hook 事件上报到 page-deliver-cli metrics-report
 *   —— Pre/Post 事件受 HOOK_REPORT_FILTER 允许列表控制；
 *      SessionStart / Stop / SessionEnd 默认全量上报。
 *
 * 调用方式：node hook-handler.js <event-type>
 *   - <event-type> 仅作前缀标记，便于按类型 grep
 *   - sessionId 从 stdin JSON 顶层 `session_id` 字段提取（失败回退 'unknown'）
 *
 * 安全：任何异常都 exit 0，不阻塞主流程
 *
 * 节流：每次 hook 调用都会 spawn 一个独立的 node 进程，进程间无法共享内存信号。
 *   metrics_report 调用可能触发 OAuth 授权弹窗，在用户尚未授权时高频 hook 调用
 *   会导致疯狂弹窗。通过文件时间戳实现每会话 10s 节流：
 *   每次上报前检查 <projectDir>/.page-deliver/report-throttle-<sessionId>.json，
 *   若距上次上报不足 PD_REPORT_THROTTLE_MS（默认 10000ms）则跳过本次上报。
 */

const fs = require('node:fs');
const path = require('node:path');
const child_process = require('node:child_process');
const crypto = require('node:crypto');

// ---------------------------------------------------------------------------
// 常量
// ---------------------------------------------------------------------------

const PRE_POST_EVENTS = new Set(['PreToolUse', 'PostToolUse']);

/**
 * 每会话 metrics_report 上报节流间隔（毫秒）。
 * 用户尚未授权 OAuth 时，频繁的 hook 调用会触发大量授权弹窗；
 * 在此间隔内的后续调用被跳过，避免弹窗风暴。
 * 可通过环境变量 PD_REPORT_THROTTLE_MS 覆盖（设为 0 可禁用节流）。
 */
const REPORT_THROTTLE_MS = (() => {
  const raw = process.env.PD_REPORT_THROTTLE_MS;
  if (raw == null || raw === '') return 10000;
  const n = parseInt(raw, 10);
  return Number.isFinite(n) && n >= 0 ? n : 10000;
})();

/**
 * 文件锁超时（毫秒）：锁文件 mtime 超过此时间视为残留锁（进程崩溃等），
 * 直接抢占。hook 进程本身执行很快（通常 <50ms），30s 足够判定残留。
 */
const THROTTLE_LOCK_STALE_MS = 30000;

/**
 * Pre/Post 事件上报允许列表（原 hook-report-filter.json）。
 * 规则格式：
 *   - 无冒号              → glob 匹配 tool_name
 *   - Skill:<name>        → 严格 tool_name === 'Skill' + glob 匹配 tool_input.command
 *   - mcp_call_tool:<s>:<t> → 严格 tool_name === 'mcp_call_tool' + glob 匹配 serverName + glob 匹配 toolName
 * 需要扩展时直接在此数组中追加即可。
 */
const HOOK_REPORT_FILTER = {
  allow: [
    // CodeBuddy: mcp_call_tool 使用完整 HRIT 路径
    'mcp_call_tool:HRIT/page-deliver/*:*',
    'mcp_call_tool:HRIT/hr-ai-data/*:*',
    // local-wiki 的 manifest name 为 hr-ai-knowledge（与目录名 local-wiki 不同），
    // CodeBuddy 按 manifest name 拼接 HRIT 路径段，故此处用 hr-ai-knowledge。
    // 同时覆盖 hr-ai-knowledge 插件自身的 hr-ai-knowledge MCP server。
    'mcp_call_tool:HRIT/hr-ai-knowledge/*:*',
    // hr-auth-copilot（权限中台助手）：CodeBuddy 全路径
    'mcp_call_tool:HRIT/hr-auth-copilot/*:*',
    // WorkBuddy: DeferExecuteTool 规范化后 serverName 为短名
    'mcp_call_tool:hr_deploy_prod_service:*',
    'mcp_call_tool:hr_data_service_v1:*',
    'mcp_call_tool:hihr:*',
    // hr-ai-knowledge skill 在 WorkBuddy 侧可能以短名 hr-ai-knowledge 调用 MCP
    //（见 SKILL.md「三级探测链」：完整名探测不到回退短名）
    'mcp_call_tool:hr-ai-knowledge:*',
    // hr-auth-copilot 的 MCP server key 为 mcp-auth-copilot（WorkBuddy 短名形态）
    'mcp_call_tool:mcp-auth-copilot:*',
    // page-deliver
    'Skill:page-deliver',
    // page-design
    "Skill:hr-common-llm", "Skill:hr-design-refs", "Skill:hr-vue-next", "Skill:hrclaw-message",
    // hr-ai-data
    "Skill:data-table-permission-checker", "Skill:data-warehouse-api-codegen", "Skill:hr-data-sql-builder",
    "Skill:indicator_query", "Skill:indicator-api-codegen",
    // hr-ai-knowledge
    "Skill:hr-ai-knowledge",
    // agent-boost
    "Skill:agent-boost",
    // local-wiki
    "Skill:local-wiki",
    // hr-auth-copilot
    "Skill:auth-code-checker", "Skill:auth-code-developer", "Skill:auth-code-tester", "Skill:hr-right"
  ],
};

/**
 * hooks.json 中 argv[2] 的 event-type 字符串 → 规范事件名。
 * 用于 stdin JSON 解析失败时也能正确判定 Pre/Post。
 */
const EVENT_TYPE_TO_CANONICAL = {
  'session-start': 'SessionStart',
  'pre-tool': 'PreToolUse',
  'post-tool': 'PostToolUse',
  'stop': 'Stop',
  'session-end': 'SessionEnd',
};

function canonicalEventName(eventType) {
  return EVENT_TYPE_TO_CANONICAL[eventType] || eventType;
}

/**
 * 识别 Bash 中的 anydev publish 命令（register_project 的 CLI 调用形态）。
 * 兼容 Unix（/）、Windows（\）路径分隔符及无路径前缀（空格分隔）三种情况；
 * `page-deliver.js` 前面必须是 /、\、空白或行首，排除 `my-page-deliver.js` 等误匹配。
 */
const PUBLISH_CMD_RE = /(?:^|[\\/\s])page-deliver\.js\s+anydev\s+publish\b/;

/**
 * Windows PowerShell 形态：`page-deliver.js` 路径常被存入变量后再调用，例如：
 *   $env:PD = "C:\path\to\page-deliver.js"; ...; node $env:PD anydev publish --input-file ...
 * 此时 `page-deliver.js` 与 `anydev publish` 之间隔了变量赋值与引用，PUBLISH_CMD_RE 无法命中。
 *
 * 通过两段独立检测兜底：
 *   1) 命令包含 page-deliver.js 路径（前导为行首 / 路径分隔符 / 空白，
 *      后接引号 / 空白 / 分号 / 行尾，排除 `page-deliver.js.bak` 等粘连）
 *   2) 命令包含独立的 anydev publish 调用
 * 同时满足即视为 publish 命令；任一不满足则不命中。
 */
const PAGE_DELIVER_JS_RE = /(?:^|[\\/\s])page-deliver\.js(?=["'\s;]|$)/;
const ANYDEV_PUBLISH_RE = /\banydev\s+publish\b/;

function looksLikePublishCommand(command) {
  if (typeof command !== 'string' || !command) return false;
  if (PUBLISH_CMD_RE.test(command)) return true;
  return PAGE_DELIVER_JS_RE.test(command) && ANYDEV_PUBLISH_RE.test(command);
}

// ---------------------------------------------------------------------------
// 纯函数（可被单测直接 require）
// ---------------------------------------------------------------------------

/**
 * Glob match：`*` 至少匹配一个非空字符；不支持 `?` / `[...]`；区分大小写。
 * 用于 hook-report-filter.json 规则匹配 tool_name / skill / serverName / toolName。
 */
function globMatch(pattern, value) {
  if (typeof pattern !== 'string' || typeof value !== 'string') return false;
  if (!pattern.includes('*')) return pattern === value;
  const escaped = pattern
    .split('*')
    .map((part) => part.replace(/[.+^${}()|[\]\\]/g, '\\$&'))
    .join('.+');
  return new RegExp('^' + escaped + '$').test(value);
}

/**
 * 判定一条 hook 事件是否应该上报。
 *
 *  - 非 Pre/Post 事件（SessionStart / Stop / SessionEnd）→ true（默认全量）
 *  - Pre/Post 事件：allowList 非数组或为空 → false
 *  - 遍历 allowList，按字符串前缀分发：
 *      * 无冒号              → glob 匹配 tool_name
 *      * Skill:<name>        → 严格 tool_name === 'Skill' + glob 匹配 tool_input.command
 *      * mcp_call_tool:<s>:<t> → 严格 tool_name === 'mcp_call_tool' + glob 匹配 serverName + glob 匹配 toolName
 *      * 其他前缀（无冒号规则在第一分支已处理）→ 跳过该条
 */
function shouldReport(allowList, eventName, toolName, toolInput) {
  if (!PRE_POST_EVENTS.has(eventName)) return true;
  if (!Array.isArray(allowList) || allowList.length === 0) return false;

  for (const rule of allowList) {
    if (typeof rule !== 'string') continue;
    if (!rule.includes(':')) {
      // 单段：glob 匹配 tool_name
      if (globMatch(rule, toolName)) return true;
    } else if (rule.startsWith('Skill:')) {
      const sub = rule.slice('Skill:'.length);
      if (toolName === 'Skill' && toolInput && globMatch(sub, toolInput.command)) return true;
    } else if (rule.startsWith('mcp_call_tool:')) {
      const rest = rule.slice('mcp_call_tool:'.length);
      const colon = rest.indexOf(':');
      if (colon < 0) continue;
      const server = rest.slice(0, colon);
      const tname = rest.slice(colon + 1);
      if (
        toolName === 'mcp_call_tool' &&
        toolInput &&
        globMatch(server, toolInput.serverName) &&
        globMatch(tname, toolInput.toolName)
      ) {
        return true;
      }
    }
    // 其他前缀（含两段但不是 Skill/mcp_call_tool 的）→ 静默跳过
  }
  return false;
}

/**
 * 判断 anydev publish 的 PostToolUse 响应是否表示成功。
 * 从 tool_response.stdout 末尾一行 JSON 中提取 status === 'success'。
 * 解析失败 / 无输出 → 返回 false。
 */
function isPublishSuccess(toolResponse) {
  if (!toolResponse || typeof toolResponse.stdout !== 'string') return false;
  const lines = toolResponse.stdout.trimEnd().split('\n');
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      const obj = JSON.parse(line);
      return obj && obj.status === 'success';
    } catch {
      /* 末尾非 JSON 行，继续向上找 */
    }
  }
  return false;
}

/**
 * 读取 <projectDir>/.deploy-state.json。
 * 文件不存在时向下枚举一层子目录继续查找（DFS，最多一层）。
 * 文件不存在 / 解析失败 / IO 异常 → 返回 null。
 */
function readDeployState(projectDir) {
  if (!projectDir || typeof projectDir !== 'string') return null;

  // 尝试解析单个 state 文件，成功返回对象，失败返回 null
  function tryRead(filePath) {
    try {
      if (!fs.existsSync(filePath)) return null;
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    } catch {
      return null;
    }
  }

  // 优先查当前目录
  const direct = tryRead(path.join(projectDir, '.deploy-state.json'));
  if (direct !== null) return direct;

  // 向下一层子目录查找
  try {
    const entries = fs.readdirSync(projectDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const result = tryRead(path.join(projectDir, entry.name, '.deploy-state.json'));
      if (result !== null) return result;
    }
  } catch {
    // readdirSync 失败（权限等）→ 静默降级
  }

  return null;
}

/**
 * 定位 .deploy-state.json：在 projectDir 本身、其后一层子目录里查找。
 * 与 readDeployState 的查找顺序一致，但返回 { dir, parsed }：
 *   - dir    ：文件所在目录（供 state update / .client-info.json 用作 projectDir）
 *   - parsed ：解析后的对象；文件存在但解析失败 / 内容非对象 → null
 * 完全找不到 .deploy-state.json 文件 → 返回 null。
 *
 * 注意区分「找不到文件」(返回 null) 与「文件存在但异形/损坏」({ dir, parsed:null })：
 * 后者仍然定位到了目录，客户端信息应落到该目录，交给 state init 归一化时消费。
 */
function locateDeployState(projectDir) {
  if (!projectDir || typeof projectDir !== 'string') return null;

  // 文件不存在 → undefined；文件存在 → { dir, parsed }（parsed 解析失败为 null）
  const tryDir = (dir) => {
    const file = path.join(dir, '.deploy-state.json');
    try {
      if (!fs.existsSync(file)) return undefined;
    } catch {
      return undefined;
    }
    let parsed = null;
    try {
      const obj = JSON.parse(fs.readFileSync(file, 'utf8'));
      if (obj && typeof obj === 'object' && !Array.isArray(obj)) parsed = obj;
    } catch {
      parsed = null;
    }
    return { dir, parsed };
  };

  const direct = tryDir(projectDir);
  if (direct) return direct;

  try {
    const entries = fs.readdirSync(projectDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const res = tryDir(path.join(projectDir, entry.name));
      if (res) return res;
    }
  } catch {
    // readdirSync 失败（权限等）→ 静默降级
  }

  return null;
}

/**
 * 定位包含 .deploy-state.json 的目录（projectDir 本身，或其一层子目录）。
 * 找不到返回 null。（保留为薄封装：只关心「目录」而不关心内容是否合规。）
 */
function findDeployStateDir(projectDir) {
  const located = locateDeployState(projectDir);
  return located ? located.dir : null;
}

/**
 * 判断已定位到的 state 是否已是「标准 v2」——与 state.ts isCompliantV2 的核心信号对齐：
 * 解析成功 + schemaVersion===2 + projectDir 指向该目录。
 * 仅此情形才走 state update（保证文件可解析、update 不会抛错，且无需归一化）；
 * 异形 / 损坏 / 旧结构一律视为「待归一化」，改走 .client-info.json 路径。
 */
function isNormalizedV2(parsed, dir) {
  return !!parsed && parsed.schemaVersion === 2 && parsed.projectDir === dir;
}

/**
 * 返回 state 子命令所在的 page-deliver CLI bundle 路径。
 * 注意：这与 resolvePlatformBin（metrics-report 专用的 pd-mcp-cli）是两个不同产物，
 * state init/update 仅存在于 skills 下的 page-deliver.js bundle。
 */
function resolveStateCliBin() {
  return path.join(__dirname, '..', 'skills', 'page-deliver', 'bin', 'page-deliver.js');
}

/**
 * 落地客户端信息（clientType / clientVersion）。
 *
 * 三条路径归一（本质是「能否安全 update」二分）：
 *  - 已有「标准 v2」.deploy-state.json（projectDir 或一层子目录，schemaVersion===2
 *    且 projectDir 匹配）→ detached 调用 `page-deliver state update` 覆盖式写入；
 *  - 已有 .deploy-state.json 但异形 / 损坏（旧 schemaVersion、残留 steps、解析失败等）
 *    → 把 { clientType, clientVersion } 写入**该文件所在目录**的 .client-info.json，
 *      交给后续 state init 归一化时一并消费（避免 update 在异形/损坏文件上抛错丢数据）；
 *  - 完全没有 .deploy-state.json → 写 <projectDir>/.client-info.json。
 *
 * 任何异常都吞掉，不阻塞主流程。
 */
function persistClientInfo(projectDir, clientType, clientVersion) {
  if (!projectDir || typeof projectDir !== 'string') return;
  if (!clientType && !clientVersion) return;

  const fields = {};
  if (clientType) fields.clientType = clientType;
  if (clientVersion) fields.clientVersion = clientVersion;

  const located = locateDeployState(projectDir);

  // 标准 v2：走 CLI 覆盖式 update
  if (located && isNormalizedV2(located.parsed, located.dir)) {
    try {
      child_process
        .spawn(
          process.execPath,
          [
            resolveStateCliBin(),
            'state',
            'update',
            '--input',
            JSON.stringify({ projectDir: located.dir, fields }),
          ],
          { detached: true, stdio: 'ignore' }
        )
        .unref();
    } catch {
      // spawn 失败静默降级
    }
    return;
  }

  // 无 state / 异形 / 损坏：写 .client-info.json，交给后续 state init 消费并归一化。
  // 异形文件已定位到目录 → 写该目录；完全没文件 → 写 projectDir。
  const targetDir = located ? located.dir : projectDir;
  try {
    fs.writeFileSync(
      path.join(targetDir, '.client-info.json'),
      JSON.stringify(fields, null, 2) + '\n'
    );
  } catch {
    // 落盘失败静默降级
  }
}


// ---------------------------------------------------------------------------
// WorkBuddy 兼容：检测 + 规范化
// ---------------------------------------------------------------------------

/**
 * 将 WorkBuddy 的 hook payload 规范化为 CodeBuddy 格式。
 *
 * 处理逻辑（浅拷贝，不修改原对象）：
 *   1) 剥除 WorkBuddy 特有字段：call_id / tool_use_id / agent_type / permission_mode
 *   2) Skill tool_input 规范化：
 *      - WorkBuddy 使用 { skill: "xxx", args: "..." }，CodeBuddy 使用 { command: "xxx" }
 *      - 将 tool_input.skill 映射为 tool_input.command（若 command 不存在）
 *      - 删除 tool_response（Skill 上报不需要响应体）
 *   2b) Bash + anydev publish → mcp_call_tool:register_project 转换（CLI 调用形态还原为 mcp 协议）
 *      - 命中 looksLikePublishCommand 时，重写 tool_input 为 { serverName, toolName: 'register_project', arguments: '{}' }
 *      - serverName 按 client 区分：WorkBuddy → 短名，否则 → 完整 HRIT 路径
 *      - 设标记 _attachDeployState = true，供 main 触发 readDeployState
 *   3) DeferExecuteTool → mcp_call_tool 转换（仅当 tool_input.toolName 以 'mcp__' 开头）
 *      - 解析 mcp__<serverPart>__<toolPart> 格式（取第一个 __ 作为分隔点）
 *      - 构造 tool_input: { serverName, toolName, arguments: JSON.stringify(params ?? {}) }
 *   3b) mcp_call_tool + tool_input.mcpToolName 规范化（"server:tool" 格式）
 *      - 将 mcpToolName 拆解为 serverName / toolName（以第一个 : 分隔）
 *   4) mcp_call_tool 删除 tool_response（tool_response 不应与 tool_input 同级出现）
 *   5) 其他字段原样保留
 */
function normalizePayload(parsed) {
  const WB_ONLY_FIELDS = ['call_id', 'tool_use_id', 'agent_type', 'permission_mode'];
  const result = Object.assign({}, parsed);

  // 1) 剥除 WorkBuddy 特有字段
  for (const key of WB_ONLY_FIELDS) {
    delete result[key];
  }

  // 2) Skill tool_input 规范化：WorkBuddy 用 skill 字段，CodeBuddy 用 command 字段
  //    同时删除 tool_response（Skill 上报不需要响应体）
  if (result.tool_name === 'Skill') {
    if (result.tool_input && typeof result.tool_input.skill === 'string' && !result.tool_input.command) {
      result.tool_input = Object.assign({}, result.tool_input, { command: result.tool_input.skill });
      delete result.tool_input.skill;
    }
    delete result.tool_response;
  }

  // 2b) Bash + anydev publish → mcp_call_tool:register_project 转换
  //     register_project 不再通过 MCP tool 直接调用，改为 CLI anydev publish；
  //     这里把特征 Bash 命令还原为 mcp_call_tool 形态，复用既有白名单 + deploy_state 附带逻辑。
  //     直接形态与 PowerShell 变量形态都通过 looksLikePublishCommand 兜底命中。
  if (
    result.tool_name === 'Bash' &&
    result.tool_input &&
    typeof result.tool_input.command === 'string' &&
    looksLikePublishCommand(result.tool_input.command)
  ) {
    const isWorkBuddy = result.client === 'WorkBuddy';
    result.tool_name = 'mcp_call_tool';
    result.tool_input = {
      serverName: isWorkBuddy
        ? 'hr_deploy_prod_service'
        : 'HRIT/page-deliver/hr_deploy_prod_service',
      toolName: 'register_project',
      arguments: '{}',
    };
    result._attachDeployState = true;
  }

  // 3) DeferExecuteTool → mcp_call_tool 转换
  if (
    result.tool_name === 'DeferExecuteTool' &&
    result.tool_input &&
    typeof result.tool_input.toolName === 'string' &&
    result.tool_input.toolName.startsWith('mcp__')
  ) {
    const rawToolName = result.tool_input.toolName; // e.g. 'mcp__hr_data_service_v1__slang_query'
    const withoutPrefix = rawToolName.slice('mcp__'.length); // 'hr_data_service_v1__slang_query'
    const sepIdx = withoutPrefix.indexOf('__');
    if (sepIdx >= 0) {
      const serverPart = withoutPrefix.slice(0, sepIdx);
      const toolPart = withoutPrefix.slice(sepIdx + 2);
      const params = result.tool_input.params;
      result.tool_name = 'mcp_call_tool';
      result.tool_input = {
        serverName: serverPart,
        toolName: toolPart,
        arguments: JSON.stringify(params != null ? params : {}),
      };
    }
  }

  // 3b) mcp_call_tool + tool_input.mcpToolName（"server:tool" 格式）→ 规范化为 serverName/toolName
  if (
    result.tool_name === 'mcp_call_tool' &&
    result.tool_input &&
    typeof result.tool_input.mcpToolName === 'string' &&
    !result.tool_input.serverName
  ) {
    const colon = result.tool_input.mcpToolName.indexOf(':');
    if (colon >= 0) {
      result.tool_input = Object.assign({}, result.tool_input, {
        serverName: result.tool_input.mcpToolName.slice(0, colon),
        toolName: result.tool_input.mcpToolName.slice(colon + 1),
      });
      delete result.tool_input.mcpToolName;
    }
  }

  // 4) mcp_call_tool 删除 tool_response（tool_input 与 tool_response 不应同时出现）
  if (result.tool_name === 'mcp_call_tool') {
    delete result.tool_response;
  }

  return result;
}

// ---------------------------------------------------------------------------
// spawn（默认实现 + 可注入）
// ---------------------------------------------------------------------------

/**
 * 返回 page-deliver-cli JS bundle 路径。
 * 产物为单一 JS 文件，通过 node 执行，无须按平台区分二进制。
 */
function resolvePlatformBin() {
  return path.join(__dirname, '..', 'bin', 'pd-mcp-cli', 'page-deliver-cli.js');
}

let _spawnReporter = function defaultSpawnReporter(payload, deployState) {
  const cliJs = resolvePlatformBin();
  return child_process
    .spawn(
      process.execPath,
      [
        cliJs,
        'metrics-report',
        '--payload', JSON.stringify(payload),
        '--deploy-state', deployState != null ? JSON.stringify(deployState) : '',
      ],
      { detached: true, stdio: 'ignore' }
    )
    .unref();
};

/**
 * 触发上报。deployState 独立传入，不从 payload 读取。
 * 返回 child_process.ChildProcess 或 null（由注入函数决定）。
 */
function spawnReporter(payload, deployState) {
  return _spawnReporter(payload, deployState);
}

/** 仅供单测使用：注入自定义 spawn 实现。 */
function _setSpawnReporter(fn) {
  _spawnReporter = fn;
}

// ---------------------------------------------------------------------------
// 节流：文件时间戳保证跨进程幂等
// ---------------------------------------------------------------------------

/**
 * 与 mcporter OAuth vault（~/.mcporter/credentials.json）的 vault key 计算保持一致。
 * hraimgt-prod 是 HTTP server，无 oauthProvider / 无 global scope，故使用默认 key：
 *   <name>|<sha256(descriptor)[:16]>
 * descriptor = { name, url, command: null }（HTTP server 的 command 为 null）。
 */
const PD_VAULT_GLOBAL_KEY = 'global:*|oauth-wildcard-scope';

/**
 * 返回 mcporter OAuth vault 文件路径。
 * 每次 isAuthorized 调用时重新计算，使测试可以通过修改 process.env.HOME 隔离。
 */
function vaultFilePath() {
  return path.join(require('node:os').homedir(), '.mcporter', 'credentials.json');
}

function vaultKeyForHraimgtProd() {
  const descriptor = {
    name: 'hraimgt-prod',
    url: 'https://hraimgt-prod.mcp.it.woa.com/',
    command: null,
  };
  const hash = crypto
    .createHash('sha256')
    .update(JSON.stringify(descriptor))
    .digest('hex')
    .slice(0, 16);
  return 'hraimgt-prod|' + hash;
}

/**
 * 检查用户是否已授权（OAuth token 存在）。
 *
 * 读取 ~/.mcporter/credentials.json，检查以下 vault key 下是否存在 tokens.access_token：
 *   1. hraimgt-prod 的默认 key（hraimgt-prod|<hash>）
 *   2. global:*|oauth-wildcard-scope（全局 scope 回退）
 *
 * 这是一个轻量的"有/无"判断，不做 token 过期检测：
 *   - token 存在 → 大概率已授权（refresh 通常能成功）→ 跳过节流，恢复全量上报
 *   - token 不存在 → 大概率未授权 → 走节流逻辑
 *   - 文件不存在 / 解析失败 / IO 异常 → 视为未授权（保守节流）
 *
 * @returns {boolean}
 */
function isAuthorized() {
  let vault;
  try {
    const raw = fs.readFileSync(vaultFilePath(), 'utf8');
    vault = JSON.parse(raw);
  } catch {
    // 文件不存在 / 解析失败 → 视为未授权
    return false;
  }
  if (!vault || typeof vault !== 'object' || !vault.entries) return false;

  // 检查默认 key
  const primaryKey = vaultKeyForHraimgtProd();
  const primaryEntry = vault.entries[primaryKey];
  if (primaryEntry && primaryEntry.tokens && primaryEntry.tokens.access_token) {
    return true;
  }

  // 检查 global scope 回退
  const globalEntry = vault.entries[PD_VAULT_GLOBAL_KEY];
  if (globalEntry && globalEntry.tokens && globalEntry.tokens.access_token) {
    return true;
  }

  return false;
}

/**
 * 返回节流文件路径：<projectDir>/.page-deliver/report-throttle-<sessionId>.json
 * sessionId 经过净化（仅保留 a-zA-Z0-9_-），防止路径穿越。
 */
function throttleFilePath(projectDir, sessionId) {
  const safeSession = String(sessionId || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');
  return path.join(projectDir, '.page-deliver', 'report-throttle-' + safeSession + '.json');
}

/**
 * 节流文件锁的路径：<throttleFile>.lock
 */
function lockFilePath(throttleFile) {
  return throttleFile + '.lock';
}

/**
 * 尝试获取文件锁（O_EXCL 原子创建）。
 *
 * 并发场景：多个 hook 进程同时执行 shouldThrottleReport 时，
 * 只有一个进程能成功创建锁文件，其余进程获取失败后等待重试。
 *
 * 残留锁处理：锁文件 mtime 超过 THROTTLE_LOCK_STALE_MS 视为残留
 * （进程崩溃未释放），直接 unlink 后重新抢占。
 *
 * @param {string} lockPath  - 锁文件路径
 * @param {number} now       - 当前时间戳（用于 stale 判定）
 * @returns {fs.PathLike | null} 成功返回 fd，失败返回 null
 */
function tryAcquireLock(lockPath, now) {
  if (typeof now !== 'number' || !Number.isFinite(now)) now = Date.now();
  try {
    const fd = fs.openSync(lockPath, 'wx');
    return fd;
  } catch (e) {
    if (e.code !== 'EEXIST') throw e;
    // 锁文件已存在 → 检查是否残留
    try {
      const stat = fs.statSync(lockPath);
      if (now - stat.mtimeMs > THROTTLE_LOCK_STALE_MS) {
        // 残留锁 → 强制删除后重试
        fs.unlinkSync(lockPath);
        try {
          const fd = fs.openSync(lockPath, 'wx');
          return fd;
        } catch (e2) {
          if (e2.code !== 'EEXIST') throw e2;
          return null;
        }
      }
    } catch {
      // stat 失败 → 锁已被其他进程释放，重试
      try {
        const fd = fs.openSync(lockPath, 'wx');
        return fd;
      } catch {
        return null;
      }
    }
    return null;
  }
}

/**
 * 释放文件锁（关闭 fd + 删除锁文件）。
 * 任何异常都静默吞掉，不影响主流程。
 */
function releaseLock(lockPath, fd) {
  try {
    if (fd != null) fs.closeSync(fd);
  } catch {
    // fd 已关闭
  }
  try {
    fs.unlinkSync(lockPath);
  } catch {
    // 锁文件已被删除 / 不存在
  }
}

/**
 * 判定当前是否应该跳过上报（节流）。
 *
 * 每个 hook 调用都是独立的 node 进程，无法在内存中共享信号。
 * 通过文件时间戳实现跨进程节流：写入上次上报时间，下次读取比对。
 *
 * 并发安全：read-check-write 临界区用 O_EXCL 文件锁保护，
 * 确保同一 session 同时只有一个进程执行节流判定。
 *
 * @param {string} projectDir - 项目目录（用于定位 .page-deliver/）
 * @param {string} sessionId  - 会话 ID（从 stdin JSON session_id 提取）
 * @param {number} now        - 当前时间戳（可注入，便于单测）
 * @returns {{throttled: boolean, reason?: string}}
 *   - throttled=true  → 距上次上报不足节流间隔，跳过
 *   - throttled=false → 允许上报（同时已更新文件时间戳）
 *
 * 节流间隔为 0 时禁用节流（直接返回 throttled=false，不写文件）。
 * 锁获取失败（高并发竞争）时放行上报（宁可多报不可漏报）。
 * 任何 IO 异常都吞掉并返回 throttled=false。
 */
function shouldThrottleReport(projectDir, sessionId, now) {
  if (typeof now !== 'number' || !Number.isFinite(now)) now = Date.now();

  // 节流间隔为 0 → 禁用节流
  if (REPORT_THROTTLE_MS <= 0) return { throttled: false };

  // 已授权（OAuth token 存在）→ 跳过节流，恢复全量上报
  // 已授权时不会触发授权弹窗，无需节流；节流只针对未授权窗口防弹窗风暴
  if (isAuthorized()) return { throttled: false };

  if (!projectDir || typeof projectDir !== 'string') return { throttled: false };

  const filePath = throttleFilePath(projectDir, sessionId);
  const lockPath = lockFilePath(filePath);

  // 确保 .page-deliver/ 目录存在
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
  } catch {
    // mkdirSync 失败 → 不节流，放行上报
    return { throttled: false };
  }

  // 获取文件锁（最多重试 3 次，每次间隔 5ms）
  let fd = null;
  for (let i = 0; i < 3; i++) {
    fd = tryAcquireLock(lockPath, now);
    if (fd !== null) break;
    // 短暂等待后重试（同进程内的同步 sleep，不影响其他 hook 进程）
    try {
      const start = Date.now();
      while (Date.now() - start < 5) { /* busy-wait 5ms */ }
    } catch {
      break;
    }
  }

  // 锁获取失败（高并发竞争）→ 放行上报（宁可多报不可漏报）
  if (fd === null) {
    return { throttled: false };
  }

  try {
    // 读取上次上报时间戳
    let lastReport = 0;
    try {
      const raw = fs.readFileSync(filePath, 'utf8');
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed.lastReport === 'number') {
        lastReport = parsed.lastReport;
      }
    } catch {
      // 文件不存在 / 解析失败 → 视为从未上报，不节流
    }

    // 距上次上报不足节流间隔 → 跳过
    if (lastReport > 0 && now - lastReport < REPORT_THROTTLE_MS) {
      return {
        throttled: true,
        reason: 'throttled: last report ' + (now - lastReport) + 'ms ago (< ' + REPORT_THROTTLE_MS + 'ms)',
      };
    }

    // 更新文件时间戳（原子写入：先写临时文件再 rename，避免文件内容损坏）
    const tmpPath = filePath + '.tmp.' + process.pid;
    fs.writeFileSync(tmpPath, JSON.stringify({ lastReport: now }, null, 0));
    fs.renameSync(tmpPath, filePath);
  } catch {
    // IO 异常 → 不节流，放行上报
  } finally {
    releaseLock(lockPath, fd);
  }

  return { throttled: false };
}

// ---------------------------------------------------------------------------
// stdin / project dir / sessionId
// ---------------------------------------------------------------------------

function readStdinRaw() {
  return fs.readFileSync(0, 'utf8');
}

function getProjectDir() {
  return process.env.CODEBUDDY_PROJECT_DIR || process.cwd();
}

function extractSessionId(raw) {
  if (!raw) return 'unknown';
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.session_id === 'string' && parsed.session_id) {
      return parsed.session_id;
    }
  } catch {
    /* fall through */
  }
  return 'unknown';
}

/**
 * 若环境变量 PD_HOOK_RAW_DEBUG 置位（值为 "1" / "true" / "on"，大小写不敏感），
 * 将 raw stdin 追加落盘到 <projectDir>/.page-deliver/hook-raw-<sessionId>.log。
 * 同一 session 的多次 hook 事件追加到同一文件，每条仅写 raw 内容（+ 末尾换行）。
 * sessionId 从 raw JSON 顶层 session_id 提取，缺失或解析失败 → 'unknown'。
 * 用于排查 hook 上报 / WorkBuddy 规范化问题；任何 IO 异常都静默吞掉，不阻塞主流程。
 */
function dumpRawIfNeeded(raw, eventType, projectDir) {
  const flag = process.env.PD_HOOK_RAW_DEBUG;
  if (typeof flag !== 'string') return;
  const v = flag.trim().toLowerCase();
  if (v !== '1' && v !== 'true' && v !== 'on') return;
  if (!raw || !projectDir || typeof projectDir !== 'string') return;
  try {
    const dir = path.join(projectDir, '.page-deliver');
    fs.mkdirSync(dir, { recursive: true });
    const sessionId = extractSessionId(raw);
    const safeSession = String(sessionId || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');
    const filename = `hook-raw-${safeSession}.log`;
    fs.appendFileSync(path.join(dir, filename), raw + '\n');
  } catch {
    // 静默吞掉：落盘失败不影响上报
  }
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

/**
 * 主流程。
 *
 * options（仅供单测传入；正常执行时全部 undefined，从环境/argv/stdin 读）：
 *   - eventType: 覆盖 argv[2]
 *   - rawInput:  覆盖 stdin（避免 fs.readFileSync(0)）
 *   - projectDir: 覆盖 process.env.CODEBUDDY_PROJECT_DIR / cwd
 */
function main(options = {}) {
  const eventType =
    (options && typeof options.eventType === 'string' && options.eventType) ||
    process.argv[2] ||
    'unknown-event';

  let raw;
  if (options && typeof options.rawInput === 'string') {
    raw = options.rawInput;
  } else {
    try {
      raw = readStdinRaw();
    } catch (e) {
      process.stderr.write('[hook-handler] Failed to read stdin: ' + e.message + '\n');
      process.exit(0);
      return;
    }
  }

  if (!raw || !raw.trim()) {
    process.exit(0);
    return;
  }

  // 可选：将 raw 落盘到 <projectDir>/.page-deliver/，便于调试
  // 环境变量 PD_HOOK_RAW_DEBUG=1/true/on 启用
  const dumpProjectDir =
    (options && typeof options.projectDir === 'string' && options.projectDir) ||
    process.env.CODEBUDDY_PROJECT_DIR ||
    process.cwd();
  dumpRawIfNeeded(raw, eventType, dumpProjectDir);

  // 指标上报（detached）
  try {
    let parsed = {};
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = {};
    }
    const filter = HOOK_REPORT_FILTER;
    const eventName =
      (parsed && typeof parsed.hook_event_name === 'string' && parsed.hook_event_name) ||
      canonicalEventName(eventType);
    // 规范化：统一调用 normalizePayload（WorkBuddy 转换格式，CodeBuddy 清理 tool_response 等）
    const payloadToReport = normalizePayload(parsed);
    const reportToolName = payloadToReport && payloadToReport.tool_name;
    const reportToolInput = payloadToReport && payloadToReport.tool_input;
    // projectDir 优先级：单测注入 > CODEBUDDY_PROJECT_DIR > payload.cwd > process.cwd()
    // 注意：payload.cwd 是 IDE 工作目录（可能为 /），不是项目目录，优先级低于环境变量
    const projectDir =
      (options && typeof options.projectDir === 'string' && options.projectDir) ||
      process.env.CODEBUDDY_PROJECT_DIR ||
      (parsed && typeof parsed.cwd === 'string' && parsed.cwd) ||
      process.cwd();

    // 当 PreToolUse + Skill:page-deliver 时，落地客户端信息（clientType / clientVersion）。
    // PreToolUse 在 skill 执行前触发，此时 .deploy-state.json 可能尚未由 state init 创建：
    //  - 已有 state → detached 调用 state update 覆盖式写入；
    //  - 无 state   → 写 <projectDir>/.client-info.json，交给后续 state init 消费并归一化。
    // client: 调用方客户端标识，如 'CodeBuddyIDE' / 'WorkBuddy'
    // version: 客户端版本号，如 '5.1.2' / '4.9.14'
    if (
      eventName === 'PreToolUse' &&
      reportToolName === 'Skill' &&
      reportToolInput &&
      reportToolInput.command === 'page-deliver'
    ) {
      const clientType = payloadToReport.client;      // e.g. 'CodeBuddyIDE' | 'WorkBuddy'
      const clientVersion = payloadToReport.version;  // e.g. '5.1.2'
      persistClientInfo(projectDir, clientType, clientVersion);
    }

    if (shouldReport(filter.allow, eventName, reportToolName, reportToolInput)) {
      // 节流检查：每个会话内按照 REPORT_THROTTLE_MS 间隔限流 metrics_report 调用。
      // 防止 hook 高频触发时，在用户尚未授权 OAuth 的情况下疯狂弹窗。
      // 进程间无共享内存，通过文件时间戳实现跨进程节流。
      const sessionId = extractSessionId(raw);
      const throttleResult = shouldThrottleReport(projectDir, sessionId, Date.now());
      if (throttleResult.throttled) {
        process.exit(0);
        return;
      }

      const attachDeployState = payloadToReport._attachDeployState === true;
      let deployState = attachDeployState ? readDeployState(projectDir) : null;
      // PostToolUse + anydev publish 成功时，内存中将 state 置为 completed 后上报，不写文件
      if (
        attachDeployState &&
        deployState &&
        eventName === 'PostToolUse' &&
        isPublishSuccess(parsed.tool_response)
      ) {
        deployState = Object.assign({}, deployState, { state: 'completed' });
      }
      delete payloadToReport._attachDeployState;
      payloadToReport.received_time = Date.now();
      spawnReporter(payloadToReport, deployState);
    }
  } catch (e) {
    process.stderr.write('[hook-handler] Failed to report: ' + e.message + '\n');
  }

  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = {
  globMatch,
  shouldReport,
  isPublishSuccess,
  PUBLISH_CMD_RE,
  looksLikePublishCommand,
  readDeployState,
  locateDeployState,
  findDeployStateDir,
  isNormalizedV2,
  persistClientInfo,
  normalizePayload,
  dumpRawIfNeeded,
  spawnReporter,
  _setSpawnReporter,
  main,
  throttleFilePath,
  shouldThrottleReport,
  REPORT_THROTTLE_MS,
  isAuthorized,
  vaultKeyForHraimgtProd,
  lockFilePath,
  tryAcquireLock,
  releaseLock,
  THROTTLE_LOCK_STALE_MS,
};
