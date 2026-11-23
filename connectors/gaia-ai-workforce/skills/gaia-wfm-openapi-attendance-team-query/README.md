# gaia-wfm-openapi-attendance-team-query

查询当前主管可见团队的非 LA 考勤记录、累计数据、考勤卡、设备卡和排班。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：当前账号有权限访问的团队、下属或组织成员；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getTeamAtdRecordAccess、getTeamAtdRecordList、getTeamBalanceAccess、getTeamBalanceList、getTeamCardAccess、getTeamCardList、getTeamDeviceCardAccess、getTeamDeviceCardList、getTeamScheduleAccess、queryTeamScheduleList。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查团队考勤记录权限 | `gaia YA ATD_TEAM_QUERY getTeamAtdRecordAccess` | read | `gaia YA ATD_TEAM_QUERY getTeamAtdRecordAccess --help` |
| 查询团队考勤记录 | `gaia YA ATD_TEAM_QUERY getTeamAtdRecordList` | read | `gaia YA ATD_TEAM_QUERY getTeamAtdRecordList --help` |
| 检查团队累计数据权限 | `gaia YA ATD_TEAM_QUERY getTeamBalanceAccess` | read | `gaia YA ATD_TEAM_QUERY getTeamBalanceAccess --help` |
| 查询团队累计数据 | `gaia YA ATD_TEAM_QUERY getTeamBalanceList` | read | `gaia YA ATD_TEAM_QUERY getTeamBalanceList --help` |
| 检查团队考勤卡权限 | `gaia YA ATD_TEAM_QUERY getTeamCardAccess` | read | `gaia YA ATD_TEAM_QUERY getTeamCardAccess --help` |
| 查询团队考勤卡 | `gaia YA ATD_TEAM_QUERY getTeamCardList` | read | `gaia YA ATD_TEAM_QUERY getTeamCardList --help` |
| 检查团队设备卡权限 | `gaia YA ATD_TEAM_QUERY getTeamDeviceCardAccess` | read | `gaia YA ATD_TEAM_QUERY getTeamDeviceCardAccess --help` |
| 查询团队设备卡 | `gaia YA ATD_TEAM_QUERY getTeamDeviceCardList` | read | `gaia YA ATD_TEAM_QUERY getTeamDeviceCardList --help` |
| 检查团队排班权限 | `gaia YA ATD_TEAM_QUERY getTeamScheduleAccess` | read | `gaia YA ATD_TEAM_QUERY getTeamScheduleAccess --help` |
| 查询团队排班 | `gaia YA ATD_TEAM_QUERY queryTeamScheduleList` | read | `gaia YA ATD_TEAM_QUERY queryTeamScheduleList --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_TEAM_QUERY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
