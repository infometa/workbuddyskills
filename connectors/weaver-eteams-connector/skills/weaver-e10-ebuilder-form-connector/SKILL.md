---
name: weaver-e10-ebuilder-form-connector
display_name: 泛微E10 eBuilder表单
display_name_en: Weaver E10 eBuilder Forms
description: "泛微E10 eBuilder 表单助手：定位菜单，查询 List/NList 列表，读取字段和浏览数据，并通过 CLI 安全执行表单 OpenAPI/自定义接口读写。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_zh: "面向泛微 E10 eBuilder 表单：通过 weaver-work-cli ebuilder-form 定位菜单与页面上下文，查询列表和表单数据，解析字段、选项和浏览字段，并用 prepare/apply 确认链新增、修改或删除数据。本技能为泛微eteams数智办公云平台连接器配套使用，CLI 安装与登录地址由连接器提供。"
description_en: "Query eBuilder menus, List/NList pages, fields, browser values, and form data through the weaver-work-cli ebuilder-form command with prepare/apply confirmation for writes. For use with the Weaver E10 connector, which provides the CLI installation and the login endpoint."
version: 1.0.0
author: 泛微网络科技股份有限公司
requires:
  bins: ["weaver-work-cli"]
dependencies:
  - weaver-e10-login
cliHelp: "weaver-work-cli ebuilder-form --help"
---

# 泛微E10 eBuilder表单

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../weaver-e10-shared-connector/SKILL.md`](../weaver-e10-shared-connector/SKILL.md)，其中包含安装、E10 认证、JSON 输出和高风险写入规则。该文件由连接器随包提供，读取失败时必须停止执行；不要自行安装 CLI 或 Skill。**

本技能覆盖 eBuilder 表单菜单定位、List/NList 页面查询、字段/选项/浏览字段解析，以及 OpenAPI 和已发布自定义接口的表单数据读写。所有业务调用必须通过 `weaver-work-cli ebuilder-form`，禁止绕过 CLI 直接拼 E10 接口、Cookie、ETEAMSID 或 `/api/bs/` 路径。

**认证与会话由连接器托管**（登录由连接器执行 `weaver-work-cli auth login`，业务命令统一显式带 `--profile eteams`；`weaver-e10-login` 仅作为兼容依赖保留，Agent 不得自行调用）。底层请求头由 CLI 自动设置，Agent 不得在对话或命令输入中索取、粘贴或输出这些凭证：

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## 命令入口

```text
weaver-work-cli ebuilder-form --help
weaver-work-cli ebuilder-form schema
weaver-work-cli --profile eteams --json ebuilder-form run <operation> --input-json '<json>'
```

`schema` 是可用 operation 与字段的事实来源。未出现在 schema 中的能力，不要写成可执行步骤。

## 高优先级语义

- “这个表单在哪 / 找某个 eBuilder 菜单” → `ebuilder-form.menu.search` 取候选菜单，再 `ebuilder-form.context.resolve`
- “页面 URL 解析 / 这个列表页对应哪个 objId” → `ebuilder-form.context.resolve`（`url` 传整串 URL）
- “这个表单有哪些视图 / 切换列表视图” → `ebuilder-form.views.list`
- “查列表 / 表格数据 / 分页 / 总数” → 先 resolve，再按 `listKind` 走 `ebuilder-form.list.query` 或 `ebuilder-form.nlist.query`
- “看列表字段、搜索项、排序、统计、固定条件” → `ebuilder-form.list.config` 或 `ebuilder-form.nlist.config`
- “表单字段、选项、主明细映射、人员/部门/关联字段按名称解析” → `fields.get`、`options.get`、`mapping.get`、`browser.resolve`
- “按 objId 查详情/分页/总数” → `openapi.detail`、`openapi.query`、`openapi.count`
- “新增/修改/删除表单数据” → 对应 `*.prepare` → 用户确认 → 对应 `*.apply`
- “已发布自定义接口 interfacePk 查询/写入” → `custom.*`

菜单多命中时必须列出候选让用户选择，不得自动取第一条。

## Reference 路由表

| 触发条件 | Reference |
| --- | --- |
| 菜单搜索、URL 解析、apiPrefix、appId/listId/objId 上下文、页面地址、视图枚举 | [`references/context-routing.md`](references/context-routing.md) |
| List/NList 配置、分页、总数、搜索条件、NList customConfig 编码 | [`references/list-nlist.md`](references/list-nlist.md) |
| 字段定义、选项、主明细映射、人员/部门/审批/文档等浏览字段 | [`references/fields-browser.md`](references/fields-browser.md) |
| OpenAPI 详情、分页、总数的只读查询 | [`references/openapi-read.md`](references/openapi-read.md) |
| OpenAPI 新增、修改、删除的 prepare/apply 确认链 | [`references/openapi-write.md`](references/openapi-write.md) |
| 已发布自定义接口的查询、新增、修改、删除 | [`references/custom-api.md`](references/custom-api.md) |
| 源资料中存在但当前 CLI 未自动化或需要人工补充的能力边界 | [`references/disabled-capabilities.md`](references/disabled-capabilities.md) |

## 处理链

1. 先运行 `weaver-work-cli ebuilder-form schema` 确认 operation 和字段。
2. 有菜单名或页面 URL 时先执行 `ebuilder-form.context.resolve`，保留返回的 `context`。同一任务后续 operation 优先传 `context`，避免重复搜索菜单或猜 ID。
3. 页面列表查询必须按 `context.listKind` 分流：`List` 用 `list.*`，`NList` 用 `nlist.*`。不要把两套接口互相试跑。
4. 表单级数据查询或写入必须先确认接口族：有 `objId` 走 OpenAPI；有 `interfacePk` 且用户明确是已发布自定义接口时走 `custom.*`；两者同时出现且用户没有指定时先消歧。
5. 字段显示名（`text`）不能直接当写入键：通常用字段的 `name`；自定义字段若 `name == id`，或目标接口明确要求组件数据键时，改用 `config.dataKey`。写入前用 `fields.get` 核对真实字段。选择类字段写入选项 `id`，不写选项名称。
6. 新增、修改、删除必须先 prepare。prepare 返回 `requestPreview` 和 10 分钟有效的 `continuation`；向用户摘要目标、字段、数量和风险，得到明确确认后 apply。

## 写操作失败决策树

| 错误 subtype | 含义 | 处置 |
| --- | --- | --- |
| `required` / `confirm_required` | 未显式确认 | 先向用户确认，再传 `confirm: true` |
| `continuation_invalid` / `continuation_expired` / `continuation_mismatch` | continuation 无效、过期或不属于当前 operation | 重新执行 prepare |
| `continuation_actor_changed` | 当前 E10 登录环境或用户与 prepare 时不一致 | 重新 prepare，不复用旧 continuation |
| `business_error` / `http_error` | 服务端业务失败或 HTTP 失败 | 保留业务消息，停止后续写入 |
| `session_expired` | 登录态失效或权限不足 | 引导用户断开并重新连接本连接器以重新登录，然后从只读步骤重新开始 |
| `too_many_pages` | 查询全部页超过 100 页预算 | 请用户增加筛选条件，不得拆成多次单页查询规避预算 |
| `write_uncertain` | 写请求结果未知 | 立即停止，不自动重放；先做只读核验 |

## 安全边界

- 认证、profile、Cookie 与 ETEAMSID 由连接器 `weaver-work-cli` 托管；不要索取或输出凭证。
- 禁止调用 `/api/bs/`，禁止默认域名，禁止从 `menuId`、`appId`、`listId` 或 `objId` 互相猜测。
- 文件、附件、OCR、导入、远程 URL 解析不属于当前模块；如后续新增，执行前必须提醒用户「文件内容可能被上传到业务系统、OCR/解析服务，并可能进入当前大模型上下文」，**必须等待用户明确确认后才继续**（见 `weaver-e10-shared-connector` 通用准则）。
- 查询列表时单页最大 200；查询全部页预计 100 页或更多时停止。
- 删除不可逆。用户当前请求已明确删除目标时仍必须走 CLI 的 continuation 校验；目标不明确时先询问。

## 失败处理与自检

- 业务失败看 stderr JSON 的 `error.type` / `error.subtype` / `error.message`，不要用退出码 `0` 判断成功。
- 不确定某个能力是否可用时，先跑 `weaver-work-cli ebuilder-form schema` 核对；`schema` 是唯一事实来源，未出现在其中的能力不要写成可执行步骤。
- 命令不可用（`command not found` 或退出码 127）时，按 `weaver-e10-shared-connector` 的安装章节处理（先区分「未安装」与「已安装但不在 PATH」，**不要执行 `npm install`**）：让用户断开连接器后重新点「连接」，由连接器重跑安装；不要自行拼装接口。
- **诊断出口**：任何步骤拿不到预期结果时，优先回到 `ebuilder-form schema` 与对应 reference 核对参数，不要换接口硬试、不要绕过 CLI 直连 E10。
- 认证类错误（`authentication` / `session_expired`）：引导用户断开并重新连接本连接器以重新登录，然后从**只读步骤**重新开始；写操作的旧 continuation 作废，必须重新 prepare。

## 平台兼容示例

Windows PowerShell：

```powershell
weaver-work-cli ebuilder-form schema
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.menu.search --input-json '{"menuKeywords":["客户档案"]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.context.resolve --input-json '{"menuKeywords":["客户档案"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli ebuilder-form schema
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.menu.search --input-json '{"menuKeywords":["客户档案"]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.context.resolve --input-json '{"menuKeywords":["客户档案"]}'
```

复杂 JSON 使用 UTF-8 文件和 `--input <path>`；只在确认当前 shell 管道稳定时使用 `--input -`。
