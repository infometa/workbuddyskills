---
name: gaia-wfm-openapi-attendance-team-query
description: "[NON_LA] 查询当前主管可见团队的考勤记录、累计数据、考勤卡、设备卡和排班。用户询问下属、团队或部门成员在指定日期范围内的考勤、假期累计、打卡卡片、设备卡或排班时使用；不用于个人查询或修改考勤数据。"
metadata:
  releaseChannel: NON_LA
  requires:
    bins: ["gaia"]
  gaia:
    modes: [external]
---
# gaia-wfm-openapi-attendance-team-query

本 Skill 在 WorkBuddy Connector 中使用 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md) 作为基础 Skill，认证、租户、权限、安全确认和错误恢复遵循该说明。

执行 `gaia config show --json` 确认 `install_mode=external`，再执行 `gaia status --json` 确认登录有效且 `release_channel=NON_LA`。模式或版本不匹配、登录无效或状态不可用时停止使用本 Skill；按 WorkBuddy `gaia-cli` 基础 Skill 恢复后重新核对，不切换租户或猜测版本。

本 Skill 只固定团队查询业务范围和方法名称，不固定任何接口参数、Header、路径、请求/响应字段、枚举、分页或示例值。读取完整流程后，执行方法表中的当前契约查询命令，再按当前结果组装命令和解释响应。契约读取失败、方法不存在或方法语义变化时停止，不猜测替代方法。

仅在入口检查通过后读取完整业务流程 [references/workflow.md](references/workflow.md)。登录、账号、租户或连接变化后重新检查；只读查询无需写操作确认。

## 执行规则

- 运行时契约标记为必填的输入缺失时先询问用户；无法从用户意图确定的值不得猜测或提交占位值。
- 按真实响应组织和解释结果，展示与本次请求有关的业务内容；空结果说明实际条件，不扩大查询范围。
- 错误处理和异常恢复遵循 WorkBuddy `gaia-cli` 基础 Skill。认证失败恢复后仅重试原命令一次；权限、参数、业务、服务或网络错误保留可用诊断并停止依赖步骤。
- 方法按当前契约标记为只读操作执行；只读查询无需执行前确认。
- 跨命令字段映射只使用当前契约和本次真实响应确认的值；没有可靠映射时停止并询问，不用历史字段替代。
- 契约来源和核验以每个方法的 --help 为准，必要时补充模块级 Discovery；历史版本和制作时租户不代表当前契约。
