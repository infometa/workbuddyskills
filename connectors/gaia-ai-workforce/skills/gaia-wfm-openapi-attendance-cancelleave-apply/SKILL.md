---
name: gaia-wfm-openapi-attendance-cancelleave-apply
description: "[NON_LA] 处理当前登录用户的销假申请、修改、撤回，并按日期范围查询可销假的请假记录。用户提出申请本人销假、修改或撤回销假单、查询可销假记录等请求时使用；不处理他人销假或审批。"
metadata:
  releaseChannel: NON_LA
  requires:
    bins: ["gaia"]
  gaia:
    modes: [external]
---
# gaia-wfm-openapi-attendance-cancelleave-apply

本 Skill 供 WorkBuddy Connector 通过 Gaia CLI 处理 External NON_LA 业务。先读取 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)，遵循其中的认证、租户、权限、安全确认和错误恢复规则。

执行 `gaia config show --json` 确认 `install_mode=external`，再执行 `gaia status --json` 确认登录有效且 `release_channel=NON_LA`。可复用当前未变化会话中刚完成的检查。模式或版本不匹配时停止使用本 Skill；未登录或状态不可用时先按 WorkBuddy `gaia-cli` 基础 Skill 恢复并重新核对，不为适配本 Skill 切换租户或猜测版本。

本 Skill 只固定业务范围和方法名称，不固定任何接口参数、Header、路径、请求/响应字段、枚举、分页或示例值。读取完整流程后，执行方法表中的当前契约查询命令，再按当前结果组装命令和解释响应。契约读取失败、方法不存在或方法语义变化时停止，不猜测替代方法。

仅在检查通过后读取并遵循 [完整业务流程](references/workflow.md)。登录、账号、租户或连接变化后重新检查；写操作前再次核对当前模式、版本和目标。不要采用 LA 版本的命令、字段映射或业务结论。
## 执行规则

- 运行时契约标记为必填的输入缺失时先询问用户；无法从用户意图确定的值不得猜测或提交占位值。
- 按真实响应组织和解释结果，展示与本次请求有关的业务内容；空结果说明实际条件，不扩大查询范围。
- 错误处理和异常恢复遵循 WorkBuddy `gaia-cli` 基础 Skill。认证失败恢复后仅重试原命令一次；权限、参数、业务、服务或网络错误保留可用诊断并停止依赖步骤。
- 方法按当前契约标记为只读、写操作或高影响操作执行。写操作执行前需要明确确认，高影响操作还要二次确认；只读查询无需执行前确认。
- 跨命令字段映射只使用当前契约和本次真实响应确认的值；没有可靠映射时停止并询问，不用历史字段替代。
- 契约来源和核验以每个方法的 --help 为准，必要时补充模块级 Discovery；历史版本和制作时租户不代表当前契约。
