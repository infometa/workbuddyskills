# gaia-wfm-openapi-attendance-personal-query

查询当前登录人员的非 LA 个人考勤数据，包括打卡记录、打卡结果、出勤结果、工时、排班、津贴、假期余额、个人表单和待本人审批表单。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：当前登录人员本人及待本人审批列表；不处理未列出的对象、审批或其他版本业务。
- 方法目录：queryMyAllowance、queryMyBalance、queryMyForms、queryMyPaycodeResult、queryMyPunchRecord、queryMyPunchResult、queryMySchedule、queryMyUnApproveForms、queryMyWorkHours。

## 可用命令

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

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_PERSONNAL_QUERY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
