---
name: gaia-wfm-openapi-attendance-overtime-apply
description: "[NON_LA] 处理当前登录用户的加班申请、修改和撤回，并提供申请流程所需的权限、类型、原因、班单和结果查询。用户提出申请、修改或撤回本人加班时优先使用；纯粹查询已有加班记录或出勤结果时优先使用个人考勤查询 Skill，除非需要本流程的专属候选查询。"
metadata:
  releaseChannel: NON_LA
  requires:
    bins: ["gaia"]
  gaia:
    modes: [external]
---
# gaia-wfm-openapi-attendance-overtime-apply

本 Skill 供 WorkBuddy Connector 通过 Gaia CLI 处理 External NON_LA 业务。先读取 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)，遵循其中的认证、租户、权限、安全确认和错误恢复规则。

执行 `gaia config show --json` 确认 `install_mode=external`，再执行 `gaia status --json` 确认登录有效且 `release_channel=NON_LA`。模式或版本不匹配时停止使用本 Skill；未登录或状态不可用时按 `gaia-cli` 恢复后重新核对。登录、租户或连接变化后重新检查。

仅在入口检查通过后读取 [完整业务流程](references/workflow.md)。不要采用其他版本正文中的命令、字段映射或业务结论。

## 适用范围

本 Skill 仅适用于 Gaia CLI External 的 NON_LA 租户，处理当前登录用户本人加班业务。不处理他人加班、审批代办、权限授予或未列出的 API。

## 能力概览

- 查询加班申请权限、时间范围内可用加班类型、可用加班原因，以及指定日期的班单和加班结果。
- 提交本人加班申请，修改已确认表单号的加班单，或撤回已确认表单号的加班单。
- 申请和修改在提交前展示摘要并取得明确确认；撤回属于高影响操作，必须二次确认。

命令参数、字段状态、日期映射、跨命令关系和错误处理见 [`references/workflow.md`](references/workflow.md)。

本 Skill 只固定业务范围和方法名称，不固定任何接口参数、Header、路径、请求/响应字段、枚举、分页或示例值。读取完整流程后，执行方法表中的当前契约查询命令，再按当前结果组装命令和解释响应。契约读取失败、方法不存在或方法语义变化时停止，不猜测替代方法。
## 执行规则

- 运行时契约标记为必填的输入缺失时先询问用户；无法从用户意图确定的值不得猜测或提交占位值。
- 按真实响应组织和解释结果，展示与本次请求有关的业务内容；空结果说明实际条件，不扩大查询范围。
- 错误处理和异常恢复遵循 WorkBuddy `gaia-cli` 基础 Skill。认证失败恢复后仅重试原命令一次；权限、参数、业务、服务或网络错误保留可用诊断并停止依赖步骤。
- 方法按当前契约标记为只读、写操作或高影响操作执行。写操作执行前需要明确确认，高影响操作还要二次确认；只读查询无需执行前确认。
- 跨命令字段映射只使用当前契约和本次真实响应确认的值；没有可靠映射时停止并询问，不用历史字段替代。
- 契约来源和核验以每个方法的 --help 为准，必要时补充模块级 Discovery；历史版本和制作时租户不代表当前契约。
