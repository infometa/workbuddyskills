# 权限状态机

权限不是一次性布尔值，而是按来源或故事记录的状态：`pending`、`family_only`、`manuscript_allowed`、`public_allowed`、`withdrawn`、`anonymized`、`disputed`。

状态只能在有明确授权者和记录依据时升级；任何撤回或冲突立即采用更严格范围。公开许可不自动等于入稿许可，家庭内部可见也不等于可发送给其他家庭成员。导出前检查所有来源和故事的权限状态。
