# 补卡申请流程（非 LA）

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

## 入口和动态契约

仅在入口 SKILL.md 的 External 模式、登录和 NON_LA 版本检查通过后读取本文件。只通过 Gaia CLI 调用业务方法，不直接调用 HTTP、SDK 或自建客户端。

本 Skill 保留业务范围和以下方法名称：getPunchApplyAccess、getPunchFormAndRecord、getPunchApplyReason、applyPunchForm、modifyPunchApply、cancelPunchApply。它不固化任何方法的请求参数、Header、路径、响应字段、枚举、分页默认值、编码或示例值。执行任一方法前，先运行对应表格中的当前契约查询命令（即该方法的 --help）；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。按本次读取结果决定参数位置、必填项、响应解释和后续步骤。方法不存在、契约无法读取或方法语义发生变化时停止，并说明原因，不猜测替代方法。

## Gaia CLI 命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查补卡权限 | `gaia YA ATD_FORM_APPLY getPunchApplyAccess` | read | `gaia YA ATD_FORM_APPLY getPunchApplyAccess --help` |
| 查询补卡单和记录 | `gaia YA ATD_FORM_APPLY getPunchFormAndRecord` | read | `gaia YA ATD_FORM_APPLY getPunchFormAndRecord --help` |
| 查询补卡原因 | `gaia YA ATD_FORM_APPLY getPunchApplyReason` | read | `gaia YA ATD_FORM_APPLY getPunchApplyReason --help` |
| 申请补卡 | `gaia YA ATD_FORM_APPLY applyPunchForm` | write | `gaia YA ATD_FORM_APPLY applyPunchForm --help` |
| 修改补卡 | `gaia YA ATD_FORM_APPLY modifyPunchApply` | write | `gaia YA ATD_FORM_APPLY modifyPunchApply --help` |
| 撤回补卡 | `gaia YA ATD_FORM_APPLY cancelPunchApply` | destructive | `gaia YA ATD_FORM_APPLY cancelPunchApply --help` |

## 业务流程

### 查询和准备
先检查补卡权限，再按日期范围查询补卡单和记录；需要原因时查询当前原因选项。展示真实候选并隐藏内部标识，无法唯一确定目标时先询问。

### 申请、修改和撤回
申请或修改前确认日期、时间、原因、目标表单及当前契约要求的其他信息，展示摘要并取得确认；附件处理必须按当前契约和用户明确选择执行，不把文件名或路径猜成标识。撤回前二次确认，只有明确成功响应才报告完成。

## 统一执行规则

- 只处理当前登录账号在本 Skill 范围内的业务，不扩大到他人、其他租户或其他版本。
- 用户提供的日期、范围、类型、记录或表单目标有歧义时先询问；只使用用户确认或当前响应中真实存在的信息。
- 按当前契约组装命令和解释真实响应；不把历史文档、CLI 示例或 HTTP 成功状态当作当前业务结论。
- 查询为空时说明实际条件，不自动扩大范围；参数错误只追问 CLI 指出的缺失或非法信息。
- 认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复后仅重试原命令一次；权限拒绝、业务错误、接口 4xx/5xx、网络错误或解析失败时停止依赖步骤，保留可用诊断和任务 ID。
- 不输出 Token、Secret、密码、服务地址或原始调试日志；需要排障时按 WorkBuddy `gaia-cli` 基础 Skill 整理脱敏任务信息。
- 本 Skill 含写操作。申请或修改前展示摘要并取得明确确认；撤回前单独进行二次确认。写操作超时、连接中断或结果无法判断时报告结果未知，不得自动重试或重复提交。

## 契约来源和验证

运行时契约来源为各方法的 --help，必要时补充 gaia api show YA ATD_FORM_APPLY --json。文档中的历史核验日期、CLI 版本或租户信息不代表当前契约；首次使用和接口变更后都必须重新读取。
