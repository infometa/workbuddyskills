# 游戏创作、质量与复用
## 新游戏

依次调用：模板列表 → 设计 Schema → 设计校验 → 启动生成 → 轮询任务 → 读取游戏 → 质量审计。

常规商务游戏默认 `decisionMakerCounts=[5,3,3,3,3]`，预期五个商机和 22 个 NPC。只有用户明确要求其他结构时才调整。

生成失败或取消后使用 `salesnail_retry_job`，不要用新的随机参数重复启动同一意图。

## 游戏修改

先调用 `salesnail_get_game`。`salesnail_preview_game_patch` 支持严格字段的：

- update_game
- add_round / update_round
- add_card / update_card
- add_npc / update_npc
- add_chance / update_chance
- add_rule / update_rule

不支持删除。优先一次确认一个聚焦变更；跨实体操作不是数据库事务。

## 质量和上架

上架前调用 `salesnail_audit_game_readiness`。阻断项包括结构缺失、NPC/卡牌/商机字段不完整、语言泄漏、不安全材料、名称/简介/封面缺失。警告也应向用户说明。

首次上架可能收费人民币 9.90 元，必须展示 preview 返回的实际金额。下架通过 game reuse 的 unpublish 操作完成，不删除已有课程。

## 复用和授权

使用 `salesnail_list_game_library` 查看 owned、authorized_by_me、shared_with_me、template 和 copied 游戏。

复制后 MCP 会识别新游戏并尽量修复缺失 NPC 头像。分享、授权、修改期限、撤销授权和下架均先调用 `salesnail_preview_game_reuse`。
