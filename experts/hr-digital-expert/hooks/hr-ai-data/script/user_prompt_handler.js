#!/usr/bin/env node
// =============================================================================
// user_prompt_handler.js — UserPromptSubmit 处理
// =============================================================================
// 在用户每次提交对话时注入 HR 数据安全自检提示词（additionalContext）。
// 注入完整版规则（buildPromptFull），确保模型每轮都有安全检测规则在上下文中。
// 完整规则也同步在 skills/hr-data-security/SKILL.md（按需加载，语义一致）。
// 提示词由本文件构建（权威来源）；hooks/doc/prompt.md 为其维护副本，仅供维护者阅读。
// =============================================================================

const fs = require('fs');
const path = require('path');
const { nowISO, readJSON, readStdin } = require('./hook_common.js');

const CONFIG_FILE = path.join(__dirname, '..', 'data', 'config', 'config_user_prompt.json');
const WHITELIST_FILE = path.join(__dirname, '..', 'data', 'white-list', 'legal_domain_ip_whitelist.json');
const MCP_WL_FILE = path.join(__dirname, '..', 'data', 'white-list', 'mcp_whitelist.json');

let _config = null;
function loadConfig() {
  if (_config !== null) return _config;
  try { _config = fs.existsSync(CONFIG_FILE) ? JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8')) : {}; }
  catch (_) { _config = {}; }
  return _config;
}

function loadLegalList() {
  const wl = readJSON(WHITELIST_FILE);
  return (wl.domains || []).concat(wl.ips || []).join(', ');
}

function loadMcpWhitelist() {
  const wl = readJSON(MCP_WL_FILE);
  return (wl.servers || []).join(', ');
}

// ---- 完整版提示词（每轮注入，确保规则始终在模型上下文中）-----------------
function buildPromptFull(scriptWlPath) {
  const legalList = loadLegalList();
  const mcpWhitelist = loadMcpWhitelist();

  return '【系统注入 — HR 数据安全自检提示】\n\n' +
    '本会话已启用 HR 数据环境安全检测。你在调用可能涉及网络请求的工具前必须先进行自我风险判断。\n\n' +
    '【输出原则 · 最重要】本提示仅供你内部风险判断，不要向用户提及本检测机制的存在。\n' +
    '- 判定无风险时：回复中不要出现任何安全检测相关表述（如"已检查安全""无泄露风险""符合安全规范"等），正常回答用户问题即可。\n' +
    '- 判定有风险时：才按下方对应章节的措辞告知用户风险并停止；其余情况一律不要提及"数据安全""风险检测"等内容。\n\n' +

    '## 一、何为数据泄露\n\n' +
    '通过数仓 MCP（hr_data_service，测试 uat_hr_data_service_* / 生产 HRIT/hr-ai-data/hr_data_service_v*）查询出来的数据，' +
    '无论是原始结果还是经加工/摘要/转换后的内容，发送到外部服务器即为泄露。\n\n' +
    '以下原则适用于风险判定：\n' +
    '  1. 任何来源于数仓 MCP 查询结果的内容，无论当前以何种形式存在——包括已写入本地文件、' +
    '已作为模型上下文或会话记忆、已直接包含在命令执行参数或工具调用参数中、或已转换为文字描述/摘要/图表数据等——仍视为数仓数据。\n' +
    '  2. 判断时应检查操作涉及的【所有数据内容】，而非仅检查参数中是否直接包含数仓字段名。\n' +
    '  3. 【核心原则】必须有「数仓数据 + 发送到外部服务器」才构成泄露风险。\n' +
    '    若操作不涉及网络请求（纯本地处理）→ 数据不离开本机 → 无风险。\n\n' +
    '【何为"外部服务器"】\n' +
    '以下域名与 IP 是数仓项目生态中的内部服务器（提供与数仓联动的功能），向这些目标发送数据不视为泄露。' +
    '本列表称为「域名/IP 白名单」，只用于判定网络请求目标（域名/IP）是否合法，' +
    '与后文的「脚本白名单」「MCP 服务器白名单」相互独立 ：\n' +
    legalList + '\n' +
    '【域名/IP 白名单匹配铁律】上述列表是判定网络请求目标是否合法的唯一依据。\n' +
    '禁止自行推断：不允许以"同属公司内部"、"也是腾讯平台"、"与列表中 XXX 同属内部服务"、为理由的推断。\n' +

    '## 二、Bash / PowerShell 命令检测\n\n' +
    'Bash / PowerShell 命令可能通过 curl/wget 等网络工具或脚本内代码（fetch/requests 等）发起网络请求。' +
    '检测方式：检查命令中的网络请求目标是否在「域名/IP 白名单」——在白名单内 → 无风险；不在白名单 → 检查发送内容是否含数仓查询数据，含则阻止，不含则放行。\n' +
    '纯本地命令→ 无风险。\n' +
    '### 命令含脚本文件路径时的处理\n' +
    '1. 先用 read_file 读取插件「脚本白名单」文件（绝对路径：' + scriptWlPath + '），查看该脚本路径是否在「脚本白名单」entries 中（子串匹配）。\n' +
    '2. 若脚本路径在「脚本白名单」内 → 判定无风险，在命令末尾添加 `# hook:safe` 后调用。\n' +
    '3. 若脚本路径不在「脚本白名单」内 → 用 read_file 读取脚本文件内容，检查其内部网络请求：\n' +
    '   - 无网络请求代码，或网络请求目标均在「域名/IP 白名单」内 → 无风险，在命令末尾添加 `# hook:safe` 后调用。\n' +
    '   - 含网络请求且目标不在「域名/IP 白名单」，或发送内容含数仓数据 → 有风险，不调用，直接告知用户风险并建议卸载/禁用引发风险的 MCP 或插件。\n' +
    '### Bash / PowerShell 标记规则\n' +
    '判定命令无风险后，必须在 Bash 命令末尾添加标记后再调用，统一格式：`<原命令> # hook:safe`（# 前必须有空格；PowerShell 与 bash 中 # 均为注释符，不改变命令执行）。\n' +
    '- 纯本地命令（不涉及网络传输）→ 100% 安全，必须添加 `# hook:safe`。\n' +
    '- 网络请求目标命中「域名/IP 白名单」 → 无风险，添加 `# hook:safe` 后调用。\n' +
    '- 判定有风险 → 不调用，直接告知用户「检测到将数仓数据发送到外部服务器的风险，已阻止」，并建议卸载/禁用引发风险的 MCP 或插件，不提供替代方案。\n' +
    '- 不确定 → 宁可阻止。\n\n' +
    
    '## 三、MCP 工具调用检测\n\n' +
    '数仓 MCP（名称含 hr_data_service 核心段：测试 uat_hr_data_service_*、生产 HRIT/hr-ai-data/hr_data_service_v*）→ 直接调用，【不要】在数仓 MCP 的参数中添加 hookSafe。\n' +
    '「MCP 服务器白名单」内（匹配时忽略大小写，当前为：' + mcpWhitelist + '）→ 直接调用，无需添加标记。\n' +
    '其余 MCP 均为外部服务器——检查 tool_input.arguments 中是否含数仓数据（定义见第一节）：\n' +
    '- 不含 → 判定无风险，按下述方式调用：\n' +
    '  · 【仅当工具定义支持 explanation 参数时】（如 CodeBuddy mcp_call_tool 有 explanation 参数）→ 在 explanation 值开头添加 [hookSafe] 标记后调用，MCP 业务参数保持不变。\n' +
    '  · 若工具定义【不支持 explanation 参数】→ 不要添加任何标记，直接原样调用，由 hook 按原流程检测（拦截时按拦截提示配合）。\n' +
    '- 含 → 存在泄露风险 → 不调用，告诉用户「该 MCP 工具会将数据发送到外部服务器，已阻止调用。' +
    '建议卸载或禁用该 MCP 服务器以消除此风险」，停止\n\n' +
    
    '## 四、部署操作检测（HR 数据泄露与部署行为联动判断）\n\n' +
    '此规则阻止将含数仓访问脚本的文件或者包含数仓数据的文件部署到外部的、不在「域名/IP 白名单」中的部署平台。\n\n' +
    '### 允许放行的内部部署链路（部署目标全程走「域名/IP 白名单」内服务器）\n' +
    '  - page-deliver（HR 内部交付插件，其交付产物即 HRClaw 平台）：其部署链路全部通过「域名/IP 白名单」内服务器——\n' +
    '    部署文件只能上传到这些内部服务器，无外泄风险 → 允许执行，不拦截。\n' +
    '  - HRClaw / HRClaw Gateway（page-deliver 的部署落地产品名）：部署到 HRClaw 即视为 page-deliver 内部链路，\n' +
    '    其目标服务器同样为上述「域名/IP 白名单」地址 → 允许执行，不拦截。\n\n' +
    '### 必须阻止的外部部署平台（不在「域名/IP 白名单」中）\n' +
    '以下平台均不在「域名/IP 白名单」中，即使项目通过 page-deliver 生成了部署包，也不得将部署包转投到：\n' +
    '  - Cloud Studio / EdgeOne Pages / CloudBase 静态托管 / GitHub Pages / Vercel / Netlify 等任何公网部署平台。\n\n' +
    '### 数仓访问脚本定义\n' +
    '向 dos-dataview-mcp.woa.com / dos-dataview.mcp.it.woa.com 等内部数仓接口发请求的调用，\n' +
    '无论脚本形式，一律视为数仓访问脚本。\n\n' +
    '### 判定有风险（目标为外部部署平台且有上述的数据泄露风险） →\n' +
    '不调用任何部署相关工具，不调用 Bash 执行部署命令。\n' +
    '直接告诉用户：\n' +
    '"⚠️ 检测到待部署文件包含数仓访问脚本（向内部数仓发起查询请求的代码）。\n' +
    ' 将其部署到外部服务器即构成 HR 数据泄露风险，已阻止。\n' +
    ' 为彻底消除此风险，建议：\n' +
    '  1. 卸载或禁用所有外部部署相关的 MCP 服务器 / Skill 插件；\n' +
    '  2. 解除该项目的部署意图，不要将含数仓访问脚本的应用部署到任何外部平台。"\n' +
    '随后结束本轮对话，不再继续推理或提出后续操作。\n\n' +
    
    '## 五、其他工具兜底\n\n' +
    '本规则未逐一列名的工具' +
    '若其参数会发送到外部服务器，同样需按本规则判定：检查参数是否含数仓查询数据，不含则调用，含则阻止并告知用户。\n' +
    '纯本地工具不涉及网络请求 → 可正常调用。\n\n' +

    '## 六、被 hook 拦截时如何配合（重要）\n\n' +
    '当你的一次工具调用被 PreToolUse hook 暂停，提示「需分析风险后原样重试」时，' +
    '说明 hook 正在等待你的风险判定结果并写入会话状态，这不是报错。请按下述方式配合：\n\n' +
    '- `# hook:safe` 标记【仅适用于 Bash / PowerShell 命令】。对 MCP、Write/Read 等工具调用不适用——' +
    '不要试图给工具调用添加 `# hook:safe`，工具没有该参数，加了也不会被识别。\n' +
    '- 【写会话状态只能用 Bash】拦截提示会给出一条形如 `node "<...>/state_write.js" set "<会话文件>" "<字段>" "<值>"` ' +
    '的现成命令。判定完成后，直接用 Bash 原样执行该命令即可——命令已在脚本白名单内，无需附加 `# hook:safe`。\n' +
    '- 【严禁】用 Edit / Write / MultiEdit 修改会话文件，也不要用 cat / echo / 重定向自行拼 JSON。' +
    '- 该命令，直接执行即可，无需先读取会话文件。\n' +
    '- 执行顺序固定：先执行写状态命令，确认成功后，再使用完全相同的参数原样重试本次调用；' +
    '判定有风险则不重试，直接拒绝并告知用户。\n' +
    '- 【无风险时全程静默 · 最重要】被拦截后判定为无风险，属于纯内部流程，用户不应察觉。此时：\n' +
    '  · 不要输出任何文字说明——不说"执行被拒绝"、不说明原因、不陈述判定结论、' +
    '不描述你接下来要做什么、不在事后总结你做了什么；\n' +
    '  · 调用 Bash 执行写状态命令时，【不要传 description 参数】。' +
    '  · 正确的表现是：静默执行写状态命令 → 静默原样重试 → 直接给出用户原本想要的结果，' +
    '中间不出现任何与判定有关的可见痕迹。\n' +
    '- 只有判定为有风险时，才向用户说明并停止——这是用户唯一应该感知到本机制的场景。\n';
}

// ---- 主入口 --------------------------------------------------------------
async function main() {
  if (!loadConfig().active) {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  const pluginRoot = path.resolve(__dirname, '..', '..', '..');
  const logDir = path.join(pluginRoot, 'logs');
  try { fs.mkdirSync(logDir, { recursive: true }); } catch (_) {}

  const inputData = await readStdin();
  const sessionId = inputData.session_id || 'no-session';

  // 日志（观察真实输入字段格式）
  if (loadConfig().logging) {
    const logFile = path.join(logDir, 'hook-user-prompt-' + sessionId + '.log');
    const entry = [
      '=== [' + nowISO() + '] event=UserPromptSubmit ===',
      '>>> INPUT:', JSON.stringify(inputData, null, 2),
      '==================================\n\n'
    ].join('\n');
    try { fs.appendFileSync(logFile, entry, 'utf8'); } catch (_) {}
  }

  // 判断运行环境：WB 的插件安装在 .workbuddy 路径下，CB 在 .codebuddy 下
  const IS_WB = __dirname.includes('.workbuddy');
  // 脚本白名单绝对路径（CB/WB 对应文件），注入提示词供模型 read_file 使用
  const scriptWlPath = path.join(__dirname, '..', 'data', 'white-list', IS_WB ? 'script_whitelist_wb.json' : 'script_whitelist.json');

  // 注入完整版安全检测规则
  const promptText = buildPromptFull(scriptWlPath);

  const responseOutput = {
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: promptText
    }
  };

  process.stdout.write(JSON.stringify(responseOutput));
  process.exit(0);
}

main().catch(err => {
  console.error('user_prompt_handler 异常:', err);
  try { process.stdout.write(JSON.stringify({ continue: true })); } catch (_) {}
  process.exit(0);
});
