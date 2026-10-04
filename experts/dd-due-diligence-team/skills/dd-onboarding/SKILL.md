---
name: dd-onboarding
display_name: AI尽调·使用引导
display_name_en: AI Due Diligence · Usage Guide
description: 新手引导：向用户介绍系统核心能力与操作流程、演示示例项目、创建在线快速体验项目、讲解注册登录步骤。
description_zh: 使用引导：系统介绍、示例项目演示、快速在线尽调、注册与登录指引。
description_en: Usage guide — system introduction, sample project demo, quick online due-diligence, and registration/login walkthrough.
category: finance
version: 1.0.14
author: 腾讯金融云
permissions: [mcp, network]
skill_type: knowledge
priority: P0
requires_sandbox: false
---

# 使用引导（Onboarding / Usage Guide）

本 Skill 承载首页「使用引导」场景的 4 个引导流程，供主理人（dd-due-diligence-lead）在用户首次进入或主动求助时执行。

## 通用约定（所有流程适用）

- **页面展示统一用产物方式（present_files）**：所有要展示给用户的页面一律通过 `present_files` 打开，让用户在右侧面板直接看到页面内容。**禁止 fetch 页面后仅用文字总结**。
- **静态指引页（/guide/ 下）**：system-intro / auth-guide / guide 均为公开静态页，**无需登录、无需 create_embed_code**，直接传完整 URL 给 `present_files` 打开。
- **业务页面（/embed/ 下）**：走 `create_embed_code` + `present_files` 两步（path 必须以 `/embed/` 开头），禁止自行拼接站点域名。
- **未登录引导**：若 MCP 工具返回未认证/401，先引导用户注册与登录（见流程 D），再继续原流程。
- **项目定位**：`list_projects` 输出**不含 demo 标记字段**，示例项目需按企业名称 search 匹配。

## 流程 A：系统介绍

目标：让用户了解 AI 尽调助手核心能力、操作流程、工作台用法，并看到自己的项目列表。

> **本流程不打开工作台**：工作台页面会覆盖右侧面板的引导页，打开后用户就看不到介绍了。项目列表直接在对话中展示即可。

1. **打开介绍页（产物方式）**：`present_files({ url: "https://aidd-saas.txfc.cloud/guide/system-intro.html" })`，请用户在右侧面板查看；同时用一两句话点出核心（五大功能 + 七步流程），不重复页面内容
2. **查项目列表（对话展示）**：`list_projects()`，按阶段分组展示名称/企业/进度；列表为空则询问用户是否新建项目（新建走流程 C）
3. **介绍工作台用法（文字说明）**：说明项目工作台可统一管理进件、财务核验、风险分析与报告全流程；若用户想进工作台，再按需 `create_embed_code({ path: "/embed/workspace" })` + `present_files` 打开
4. **继续对话**：结束引导后等待用户指令

## 流程 B：示例项目演示

目标：展示默认示例项目【某能源科技股份有限公司】，引导用户走完风险分析旅程。

1. **定位示例项目**：`list_projects({ search: "某能源科技" })`；若无匹配再试 `search: "能源科技"`（示例项目无 demo 标记，须按企业名称匹配）
2. **无匹配兜底**：提示当前没有配置示例项目，引导用户走流程 C「快速体验」新建在线项目
3. **打开项目**：命中后 `create_embed_code({ path: "/embed/workspace/{pid}" })` → `present_files({ url })`
4. **输出详情**：用 `get_project({ projectId })` 获取项目真实信息（名称/企业/进度/三阶段状态）
5. **建议任务与动作**：给出可继续执行的建议，引导用户逐步走完整风险分析旅程：
   - 发起财务核验（S3）→ 企业画像分析 → 财务分析 → 经营分析 → 行业分析（S4）→ 风险总览（S6）→ 报告撰写（S7）
   - 每步完成后询问用户是否继续下一步
6. **未登录**：`present_files({ url: "https://aidd-saas.txfc.cloud/guide/auth-guide.html" })` 展示注册登录指引，引导完成后再执行本流程

## 流程 C：快速体验（在线尽调）

目标：创建基于在线数据的尽调项目，不上传任何本地进件材料，让用户快速体验完整流程。

1. **选择公司**：从下方备选公司中让用户确认一家（或由用户指定任意企业），给用户展示时可用简称、创建时用企业登记全称：
   - 无锡烨隆精密机械股份有限公司
   - 君乐宝乳业集团股份有限公司
   - 博瑞生物医药（苏州）股份有限公司
   - 中润光能（江苏中润光能科技股份有限公司）
   - 比格披萨（北京比格餐饮管理有限责任公司）
   - 金桥德克新材料股份有限公司
   - 南京海纳医药科技股份有限公司
   - 苏州锦艺新材料科技股份有限公司
   - 巴奴火锅（巴奴国际）
   - 惠科股份有限公司
2. **创建项目**：`create_project({ name, enterpriseName })`——enterpriseName 优先传企业登记全称（条目为「简称（全称）」形式时取括号内全称，无括号用整行）；在线信源默认全开，无需上传进件
3. **逐步执行**：基于公开数据执行 企业画像 → 财务分析 → 经营分析 → 行业分析 → 风险总览，每步展示结果并与用户确认
   - **数据不足自适应**：若所选企业为非上市/披露有限、公开财报或经营数据不足，该环节据实给"公开信息有限"的说明性结论并解释原因，禁止编造数字；可提示当前为演示体验，完整财务核验需在真实项目补进件材料
4. **收尾**：询问是否需要生成尽调报告；完成后总结体验内容

## 流程 D：注册与登录指引

目标：讲解注册、登录步骤，帮助用户开通并进入系统。

1. **打开指引页（产物方式）**：`present_files({ url: "https://aidd-saas.txfc.cloud/guide/auth-guide.html" })`，请用户在右侧面板查看注册与登录步骤；同时简要口播要点：
   - 注册：进入申请页（/login?mode=register）→ 填用户名（建议手机号）/密码/机构邀请码（可选）→ 提交后等待管理员审核（一般 1 个工作日内）
   - 登录：/login 输入用户名密码；登录后可在工作台管理项目
2. **提示价值**：说明注册登录后即可进入尽调工作台使用完整功能

## 流程 E：MCP 连接与授权指引

目标：讲解如何在 WorkBuddy 中连接 AI 尽调助手（MCP）并完成授权。**用户问"怎么连接 MCP / 怎么授权 / 连不上 / 授权失败"时优先走本流程。**

1. **打开指引页（产物方式）**：`present_files({ url: "https://aidd-saas.txfc.cloud/guide/mcp-guide.html" })`，请用户在右侧面板查看 MCP 连接步骤与截图；同时简要口播要点：
   - 顶栏切「连接器」Tab → 找到「AI 尽调助手」
   - 「配置 MCP」→ 确认 aidd-saas 开关启用
   - 再次「配置 MCP」→ 确认 url 为 `https://aidd-saas.txfc.cloud/mcp` 且 `disabled: false` → 保存
   - 回对话重新发起连接 → 完成登录与 OAuth 授权
2. **未登录/未开通账号**：若用户尚未注册，先 `present_files({ url: "https://aidd-saas.txfc.cloud/guide/auth-guide.html" })` 引导注册（流程 D）；账号开通详情走 `https://aidd-saas.txfc.cloud/guide/guide.html`
3. **授权失败/已绑定提示**：若提示「该账号已绑定其他 WorkBuddy 账号」，告知用户联系管理员解除绑定后再试

## 流程 F：授权失败 / 无账号处理（取消授权后重进）

目标：用户授权 Buddy 失败、或当前无账号时，引导用户取消授权后关闭页面，等账号状态正常后从 WorkBuddy 客户端重新进入，重新触发授权登录页。**用户问"授权失败 / 没账号 / 取消授权 / 重新授权登录"时优先走本流程。**

1. **打开处理指引页（产物方式）**：`present_files({ url: "https://aidd-saas.txfc.cloud/guide/buddy-auth-guide.html" })`，请用户在右侧面板查看处理步骤与截图；同时简要口播要点：
   - **授权失败**：在 WorkBuddy 应用授权页遇到「无法绑定 · 授权已失效或已使用」提示时 → 按页面步骤在 WorkBuddy 中取消/断开「AI 尽调助手」授权 → 关闭当前页面 → 从 WorkBuddy 客户端重新进入 → 重新弹出授权登录页 → 完成授权
   - **无账号**：关闭当前页面 → 申请账号（`/login?mode=register`，用户名建议手机号）→ 等管理员审核（一般 1 个工作日内）→ 审核通过后按取消授权步骤重进并授权
2. **账号开通兜底**：需要完整开通流程时，`present_files({ url: "https://aidd-saas.txfc.cloud/guide/guide.html" })`
3. **取消授权后再重进**：明确告知用户「取消授权后，重新进入 WorkBuddy 就会重新弹出授权登录页面」，鼓励其重试

## 红线

1. **禁止编造** — 项目/企业/风险/数据一律以 MCP 工具实际返回为准
2. **页面必须用产物方式打开** — 业务页面 path 用站内相对路径（/embed/ 开头）走 create_embed_code + present_files；静态指引页直接传完整 URL 给 present_files。禁止只输出 URL 文本，禁止用 fetch 替代页面展示
3. **不代为确认** — 创建项目、执行分析等有副作用动作前必须与用户确认
4. **不重复复用 embed url** — 每次打开业务页面重新调用 create_embed_code（登录码一次性约 60 秒过期）
