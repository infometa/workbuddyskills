# gaia-wfm-openapi-attendance-replacepunch-apply

处理当前登录人员的非 LA 补卡申请、补卡修改和补卡撤回，并查询补卡单、补卡记录和补卡原因。

- 适用模式：Gaia CLI External，NON_LA。
- 业务范围：本人补卡；不处理未列出的对象、审批或其他版本业务。
- 方法目录：getPunchApplyAccess、getPunchFormAndRecord、getPunchApplyReason、applyPunchForm、modifyPunchApply、cancelPunchApply。

## 可用命令

| 用途 | Gaia CLI 命令 | 类型 | 当前契约查询命令 |
|---|---|---|---|
| 检查补卡权限 | `gaia YA ATD_FORM_APPLY getPunchApplyAccess` | read | `gaia YA ATD_FORM_APPLY getPunchApplyAccess --help` |
| 查询补卡单和记录 | `gaia YA ATD_FORM_APPLY getPunchFormAndRecord` | read | `gaia YA ATD_FORM_APPLY getPunchFormAndRecord --help` |
| 查询补卡原因 | `gaia YA ATD_FORM_APPLY getPunchApplyReason` | read | `gaia YA ATD_FORM_APPLY getPunchApplyReason --help` |
| 申请补卡 | `gaia YA ATD_FORM_APPLY applyPunchForm` | write | `gaia YA ATD_FORM_APPLY applyPunchForm --help` |
| 修改补卡 | `gaia YA ATD_FORM_APPLY modifyPunchApply` | write | `gaia YA ATD_FORM_APPLY modifyPunchApply --help` |
| 撤回补卡 | `gaia YA ATD_FORM_APPLY cancelPunchApply` | destructive | `gaia YA ATD_FORM_APPLY cancelPunchApply --help` |

执行任一方法前，必须运行同一行的当前契约查询命令；帮助不足时再运行 gaia api show YA ATD_FORM_APPLY --json。命令、请求位置、当前必填项、响应解释和分页均以本次读取结果为准。完整业务流程见 SKILL.md 和 references/workflow.md。

## WorkBuddy Connector

本 Skill 在 WorkBuddy Connector 中通过 `gaia-cli` 执行。入口检查、认证、租户、权限、安全确认和错误恢复遵循 [`../../gaia-cli/SKILL.md`](../../gaia-cli/SKILL.md)。
