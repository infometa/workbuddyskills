---
name: gaia-wfm-openapi-attendance-personal-query
description: "查询当前登录人员的非 LA 个人考勤数据，包括打卡记录、打卡结果、出勤结果、工时、排班、津贴、假期余额、个人表单和待本人审批表单。用户明确查询本人已有记录、申请单或出勤结果时使用；不处理申请、修改、撤回或审批写操作，不用于团队或他人查询。涉及请假、加班、异常、出差的泛化查询时，只在用户确实需要同时了解申请记录和出勤结果时执行双查询，否则按用户明确的查询对象选择单一数据源。"
metadata:
  releaseChannel: NON_LA
  requires:
    bins: ["gaia"]
  gaia:
    modes: [external]
---
# Gaia WFM 个人考勤查询（非 LA）

仅适用于 External 模式的非 LA 业务。先读取本入口的 frontmatter 和 description；遵循 WorkBuddy 连接器的 `gaia-cli` 基础 Skill。

1. 执行 `gaia config show --json` 确认 `install_mode=external`，执行 `gaia status --json` 确认登录、当前租户及有效的 `release_channel`。
2. 仅当当前 `release_channel=NON_LA` 与 `metadata.releaseChannel` 一致时，读取 [完整查询流程](references/workflow.md) 并处理业务。
3. 模式或版本不匹配时停止采用本 Skill，不读取 workflow，不执行其中的命令或字段映射；不要为适配本 Skill 切换租户或覆盖版本。登录无效或版本缺失、非法时，按[`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md) 恢复后重新核对。
4. 登录、切换租户或重新连接后重新执行上述核对；必要时提示新建或重载会话。

认证、权限及错误恢复由[`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md) 统一处理。本入口不保存业务凭据或服务地址。

本 Skill 只固定业务范围和方法名称，不固定任何接口参数、Header、路径、请求/响应字段、枚举、分页或示例值。读取完整流程后，执行方法表中的当前契约查询命令，再按当前结果组装命令和解释响应。契约读取失败、方法不存在或方法语义变化时停止，不猜测替代方法。
## 执行规则

- 运行时契约标记为必填的输入缺失时先询问用户；无法从用户意图确定的值不得猜测或提交占位值。
- 按真实响应组织和解释结果，展示与本次请求有关的业务内容；空结果说明实际条件，不扩大查询范围。
- 错误处理和异常恢复遵循 WorkBuddy `gaia-cli` 基础 Skill。认证失败恢复后仅重试原命令一次；权限、参数、业务、服务或网络错误保留可用诊断并停止依赖步骤。
- 方法按当前契约标记为只读、写操作或高影响操作执行。写操作执行前需要明确确认，高影响操作还要二次确认；只读查询无需执行前确认。
- 跨命令字段映射只使用当前契约和本次真实响应确认的值；没有可靠映射时停止并询问，不用历史字段替代。
- 契约来源和核验以每个方法的 --help 为准，必要时补充模块级 Discovery；历史版本和制作时租户不代表当前契约。
