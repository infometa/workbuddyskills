# 个人考勤查询流程（非 LA）

本流程在 WorkBuddy Connector 中由 `gaia-cli` 执行。认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。

## 入口和动态契约

仅在入口 SKILL.md 的 External 模式、登录和 NON_LA 版本检查通过后读取本文件。只通过 Gaia CLI 调用业务方法，不直接调用 HTTP、SDK 或自建客户端。

本 Skill 保留业务范围和以下方法名称：queryMyAllowance、queryMyBalance、queryMyForms、queryMyPaycodeResult、queryMyPunchRecord、queryMyPunchResult、queryMySchedule、queryMyUnApproveForms、queryMyWorkHours。它不固化任何方法的请求参数、Header、路径、响应字段、枚举、分页默认值、编码或示例值。执行任一方法前，先运行对应表格中的当前契约查询命令（即该方法的 --help）；帮助不足时再运行 gaia api show YA ATD_PERSONNAL_QUERY --json。按本次读取结果决定参数位置、必填项、响应解释和后续步骤。方法不存在、契约无法读取或方法语义发生变化时停止，并说明原因，不猜测替代方法。

## Gaia CLI 命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 查询个人津贴 | `gaia YA ATD_PERSONNAL_QUERY queryMyAllowance` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyAllowance --help` |
| 查询假期余额 | `gaia YA ATD_PERSONNAL_QUERY queryMyBalance` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyBalance --help` |
| 查询个人表单 | `gaia YA ATD_PERSONNAL_QUERY queryMyForms` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyForms --help` |
| 查询出勤结果 | `gaia YA ATD_PERSONNAL_QUERY queryMyPaycodeResult` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyPaycodeResult --help` |
| 查询打卡原始记录 | `gaia YA ATD_PERSONNAL_QUERY queryMyPunchRecord` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyPunchRecord --help` |
| 查询打卡结果 | `gaia YA ATD_PERSONNAL_QUERY queryMyPunchResult` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyPunchResult --help` |
| 查询排班 | `gaia YA ATD_PERSONNAL_QUERY queryMySchedule` | read | `gaia YA ATD_PERSONNAL_QUERY queryMySchedule --help` |
| 查询待本人审批表单 | `gaia YA ATD_PERSONNAL_QUERY queryMyUnApproveForms` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyUnApproveForms --help` |
| 查询工时 | `gaia YA ATD_PERSONNAL_QUERY queryMyWorkHours` | read | `gaia YA ATD_PERSONNAL_QUERY queryMyWorkHours --help` |

## 业务流程

### 查询规则
识别数据类别、日期范围以及是否需要同时对照申请记录和出勤结果。只查询本人数据；每个要调用的方法先读取该方法的当前契约。日期缺失或边界不清时先询问，相对日期按 Asia/Shanghai 解析。

只有用户明确需要双查询时才分别查询个人表单和出勤结果；不把一个响应当作另一个方法的输入。按真实响应展示结果和覆盖范围，空结果不扩大条件，部分成功分别说明。所有方法只读，无需额外确认。

## 统一执行规则

- 只处理当前登录账号在本 Skill 范围内的业务，不扩大到他人、其他租户或其他版本。
- 用户提供的日期、范围、类型、记录或表单目标有歧义时先询问；只使用用户确认或当前响应中真实存在的信息。
- 按当前契约组装命令和解释真实响应；不把历史文档、CLI 示例或 HTTP 成功状态当作当前业务结论。
- 查询为空时说明实际条件，不自动扩大范围；参数错误只追问 CLI 指出的缺失或非法信息。
- 认证失败按 WorkBuddy `gaia-cli` 基础 Skill 恢复后仅重试原命令一次；权限拒绝、业务错误、接口 4xx/5xx、网络错误或解析失败时停止依赖步骤，保留可用诊断和任务 ID。
- 不输出 Token、Secret、密码、服务地址或原始调试日志；需要排障时按 WorkBuddy `gaia-cli` 基础 Skill 整理脱敏任务信息。
- 本 Skill 只包含只读查询，不需要额外执行确认。

## 契约来源和验证

运行时契约来源为各方法的 --help，必要时补充 gaia api show YA ATD_PERSONNAL_QUERY --json。文档中的历史核验日期、CLI 版本或租户信息不代表当前契约；首次使用和接口变更后都必须重新读取。
