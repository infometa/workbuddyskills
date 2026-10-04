---
name: enable-mcp
description: "为 page-deliver 应用开启 MCP 能力：把业务 REST API 暴露为 Agent 可调用的工具，并生成维护 public/restful.json 能力描述。当用户提出「开启 MCP」「MCP 化」「暴露 REST API tools」「生成或修复 restful.json」「维护 App Capability Gateway」「接入 Agent」「变成智能应用」等需求时使用。本 skill 只负责应用侧的 MCP 能力供给，不承担运行时调用，也不负责部署上线。"
---

# 开启 MCP 能力

将 page-deliver 应用的业务服务 MCP 化：把可稳定调用的 REST API 暴露为 Agent 工具，并维护
`public/restful.json` 能力描述。路由实现与能力描述必须同步交付，避免出现只存在于 JSON
中的虚假工具。

本 skill 只负责生成和维护应用侧能力契约。已上线应用通过
`list_apps` / `list_app_tools` / `call_app_tool` 发现和调用是 `control-hr-claw-app` 的
职责；本 skill 不承担运行时调用。

## Workflow

1. **确认项目身份**
   - 读取 `{project_dir}/.deploy-state.json`，取得 `projectId` 与 `projectName`
   - 若没有 state，先要求用户提供项目目录；不要猜测 `appId`
   - 若用户给出的目录仍无 state、`projectId` 为空或入口文件不可识别，停止执行；说明缺失项并要求用户提供项目目录或真实 `projectId`
2. **盘点能力范围**（产出：确认后的能力清单与权限基线）
   - 先阅读应用已有权限设计：页面对用户身份的判断、服务端中间件、接口级/数据级鉴权、
     角色或组织范围、敏感数据脱敏逻辑。以它作为 MCP 接口的权限基线
   - 阅读服务端入口（通常为 `server.js`）与页面需求，盘点现有或计划中的业务能力
   - 将候选能力分成三类向用户展示：`推荐暴露`、`待确认`、`不暴露`
   - `推荐暴露` 仅包含与用户目标直接相关、稳定、适合 Agent 调用的业务查询或业务动作
   - 健康检查、内部接口、调试接口、框架接口、临时接口，以及涉及敏感数据或写操作但用户未明确要求的接口，放入 `不暴露` 或 `待确认`
   - 清单中每个候选能力都写明拟用工具名、方法、路径、入参概要和数据风险
   - 不得把“开启 MCP 能力”本身理解为确认暴露全部接口；用户已明确指定的能力范围可直接作为确认范围
   - 每个确认能力拆成一个工具；工具名使用蛇形命名，如 `query_funnel`
   - 🔴 CHECKPOINT · STOP：提交能力范围清单；得到用户明确确认前，不得进入第 3 步或生成路由
   - 用户调整范围后重新提交确认；用户拒绝则记录原因并回到能力盘点，不得缩小范围后继续
3. **确认应用元信息**（产出：确认后的 `projectName` 与 `projectDescription`）
   - `projectName` 对应 `restful.json` 的 `appName`，`projectDescription` 对应顶层 `description`
   - 向用户展示两者的拟写入值、字符数、来源和适用场景；用户预览并明确确认或修改后，才能写入文件
   - 预览值必须满足当前能力契约：`projectName` 最长 16 字符，`projectDescription` 最长 256 字符；超限时先压缩改写并重新预览确认
   - 描述内容基于第 2 步确认后的能力写实改写，不能照抄 `.deploy-state.json` 的历史文案
   - `.deploy-state.json` 的 `projectName` 或历史配置只能作为草稿来源，不能视为用户已确认
   - 🔴 CHECKPOINT · STOP：提交元信息预览；得到用户明确确认前，禁止修改路由或写入 `restful.json`
   - 用户若修改，按新值重新校验长度并再次预览确认
4. **生成 API 路由**
   - 每个 MCP 路由必须按第 2 步确认的权限基线与能力范围生成：`GET` 同样做身份和数据范围校验，
     `POST` / `PUT` / `DELETE` 必须在服务端显式鉴权
   - 禁止用 `trusted`、`admin`、`super` 等静态特权参数替换应用已有权限判断，也禁止为
     MCP 降级为无条件放行；无权用户应返回 401/403，而不是返回空数组伪装成功
   - 在服务端实现 `GET` / `POST` / `PUT` / `DELETE` 路由，路径统一挂载在 `/app-mcp/` 前缀下
   - 响应统一为 JSON；非 2xx 响应要给出可理解错误
   - 需要身份判断时读取网关注入的 `X-Staff-Id` / `X-Staff-Name`
   - 大结果集提供分页或过滤参数，避免一次性返回不可用的大对象
5. **生成能力描述**
   - 写入 `{project_dir}/public/restful.json`
   - 以 `${SKILL_DIR}/assets/templates/restful.json` 为起点，按实际能力裁剪
   - `appId` 必须等于真实 `projectId`
   - `appName` 必须写入用户确认的 `projectName` 且不超过 16 字符，顶层 `description` 必须写入用户确认的 `projectDescription` 且不超过 256 字符
   - 顶层 `description` 与每个 `summary` 写实际业务能力，不能残留 TODO
   - 每个 `method` + `path` 必须与服务端真实路由一一对应
   - 每个 `path` 必须且只能以 `/app-mcp/` 开头；不得复用页面、静态资源或其他普通 API 路径
   - 每个参数必须完整声明 `name`、`in`、`type`、`required`、`description`；名称、类型、必填性必须与服务端解析规则一致
   - `object` / `array` 参数必须用 `fields` 逐字段展开；嵌套字段同样声明 `type` 与 `required`
   - 每个工具必须写入 `callExample.good`，值为 JSON 字符串（与 `call_app_tool.args` 入参形态一致）：`good` 解析后的键名只能来自 `parameters[].name` 且是能通过必填校验的真实参数值
   - 详细结构见 `${SKILL_DIR}/references/restful-spec.md`
6. **自查**
   - 每个工具的真实服务端路径都能回答：谁能调用、能看到哪些数据、越权时返回什么；无法
     回答时停止，不得发布该工具
   - `public/restful.json` 可被 `JSON.parse`
   - 每个工具的 `path` 都以 `/app-mcp/` 开头
   - path 占位符均有 `in: "path"` 参数声明
   - 每个工具都有 `callExample.good`，均为 JSON 字符串，且未引入未声明参数或包装字段
   - 每个工具都能在服务端找到对应路由
   - 对照参考文档的参数还原矩阵，逐个参数核对位置、JSON 键路径、类型和必填性；服务端存在隐藏必填参数即视为失败
   - Agent 只看 JSON 就能准确还原请求，不需要阅读服务端代码
7. **部署验证**
   - 必须进入 page-deliver 工作流，由该 skill 按自身流程路由并完成部署验证
   - `RESTFUL_SPEC_INVALID` 表示结构违规；`restful-probe` WARN 表示声明与实现不一致
   - 🔴 CHECKPOINT · STOP：部署前向用户展示最终工具清单、文件 diff 和验证计划；确认后交由 page-deliver 路由

## Execution Contract

- 输入：项目目录、`.deploy-state.json`、服务端入口、用户确认的能力范围与元信息
- 输出：真实 API 路由、`public/restful.json`、修改摘要、page-deliver 验证结果
- 每次执行必须停在三个显性检查点：能力范围确认、应用元信息确认、部署前最终确认
- 修改仅限确认的能力所需路由、`restful.json` 和必要的服务端参数解析代码

## Failure Handling

| 触发条件 | 一线修复 | 修复失败后的停止动作 |
|----------|----------|------------------------|
| `.deploy-state.json` 缺失或 `projectId` 为空 | 向用户索要项目目录或真实 `projectId` | 停止；不得猜测 `appId` |
| 找不到服务端入口或路由 | 根据 `package.json`、启动脚本和 `server.js` 定位入口 | 停止并列出已检查文件，要求用户指认入口 |
| 项目不是 page-deliver 应用或不存在 `public` 目录 | 检查项目根目录和静态资源配置 | 停止并说明需要先走 page-deliver 建项 |
| 现有 `restful.json` 已存在 | 先读取并对比能力差异，生成交互式修改预览 | 用户不确认合并方案时保留原文件 |
| 路由解析依赖 query/body/path 之外的来源 | 仅当该输入来自网关注入身份头时允许隐藏；否则必须声明 | 停止并说明无法被第三方 Agent 还原 |
| 参数树嵌套超过 3 层 | 合并中间层级或改用扁平业务参数 | 无法在 3 层内准确表达时拒绝暴露该接口 |
| 生成路径不以 `/app-mcp/` 开头 | 将 MCP 暴露路由统一迁到 `/app-mcp/` 前缀 | 不得降低前缀要求或写入其他路径 |
| 应用已有权限设计无法识别或不完整 | 检查页面身份判断、服务端中间件、角色/组织范围和脱敏逻辑 | 停止；不得用无鉴权或静态特权参数补齐 |
| MCP 路由与服务端既有权限不一致 | 复用既有鉴权函数或中间件，保持数据范围一致 | 不得发布比原接口更宽松的 MCP 路由 |
| `projectName` 超过 16 字符或 `projectDescription` 超过 256 字符 | 保留业务主体词，删除修饰词和重复能力名 | 重新预览并等待用户确认 |
| 参数存在隐藏必填校验 | 从校验代码读取规则并补入 `parameters` / `fields` | 停止；不得发布让 Agent 误调用的描述 |
| `RESTFUL_SPEC_INVALID` | 按错误中的字段路径修正结构 | 重跑 page-deliver 校验；仍失败则停止并保留原文件 |
| `restful-probe` WARN | 对照工具的 method/path 修复路由或删除未实现工具 | 重新进入 page-deliver 部署验证；仍失败则回滚本次路由与描述变更 |
| page-deliver 部署失败 | 读取失败步骤日志，仅修复本 skill 生成的路由与描述 | 连续两次失败后停止，保留原始项目文件并汇报失败证据 |

## Do Not

- 不要把健康检查、内部接口、调试接口、框架接口、临时接口放入 `tools[]`
- 不要未经用户确认暴露全部接口、敏感数据接口或写操作
- 不要忽略应用已有权限设计，也不要用无条件放行、静态特权参数或前端传身份模拟鉴权
- 不要声明服务端不存在的路由，或保留模板中未裁剪的工具
- 不要生成非 `/app-mcp/` 前缀的应用 MCP 路由，也不要把普通页面/API 路由放到 `/app-mcp/` 下
- 不要把必填结构只写在 `description` 文本里，或隐藏服务端必填参数
- 不要修改 `appId` 以绕过归属校验，不要为了通过探测而添加空路由
- 不要绕开 page-deliver 自行部署或自行调用平台网关上线
- 不要在参数树不完整、嵌套超过 3 层或依赖隐藏输入时生成 `tools[]`
- 不要在用户拒绝后继续生成，也不要覆盖已存在的 `restful.json` 而不展示差异
- 不要在部署连续失败两次后继续重试

## Completion Criteria

- API 路由、`public/restful.json`、实际业务行为三者一致
- 每个 MCP 路由的鉴权范围不宽于原应用接口；身份、角色/组织、数据范围和敏感字段脱敏均已复用
  或补齐
- `appId` 为真实 projectId，`appName` / 顶层 `description` 与用户确认的 `projectName` / `projectDescription` 完全一致且分别不超过 16 / 256 字符，描述写实且无 TODO
- 每个工具的 `path` 都以 `/app-mcp/` 开头，并只覆盖实际存在的应用 MCP 路由
- 参数、字段、必填性、调用正确示例和响应示例足以让 Agent 一次构造正确请求
- page-deliver full-deploy 无 `RESTFUL_SPEC_INVALID`，且 GET 工具探测无未实现 WARN
