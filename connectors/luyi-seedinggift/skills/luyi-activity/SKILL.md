---
name: luyi-activity
display_name: 路易活动助手
display_name_en: Luyi Campaign Assistant
description: 零代码创建私域「活动频道」，支持自然语言管理频道内活动、用户、商品和数据等运营全场景。各类热门活动玩法随取随用，从策划发布到监控复盘，AI驱动活动全流程。
description_zh: 零代码创建私域「活动频道」，支持自然语言管理频道内活动、用户、商品和数据等运营全场景。各类热门活动玩法随取随用，从策划发布到监控复盘，AI驱动活动全流程。
description_en: Create a private-domain campaign channel without code. Use natural language to manage campaigns, users, products and operational data; access popular campaign formats on demand and use AI throughout planning, publishing, monitoring and review.
version: 1.0.0
author: Luyi.AI
---

# 路易活动助手

本连接器提供五个工具：`list_products`、`create_seeding_activity`、`create_draw_activity`、`create_checkin_activity`、`list_checkin_prizes`。其中 `list_products` 查询店铺商品，`list_checkin_prizes` 查询打卡活动使用的独立奖品库；其余工具创建对应活动。它不支持编辑、删除、审核、开奖或核销。

## 登录

本连接器使用 WorkBuddy 的 MCP OAuth 授权流程。首次连接时，按 WorkBuddy 弹出的授权页面登录并授权路易商家账号；不要要求用户从浏览器 Local Storage 复制 `luyi_business_token`，也不要索取或转述 JWT。若 OAuth 授权失败，请用户在 WorkBuddy 中重新连接并完成授权；授权完成前不要继续创建，也不要假装查询或创建成功。

## 查询与选品

用户需要挑选商品时调用 `list_products`，参数为：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `keyword` | string | 空 | 按商品名称模糊搜索 |
| `page` | integer | 1 | 页码，从 1 开始 |
| `limit` | integer | 20 | 每页数量，最大 100 |
| `status` | integer | 0 | 0=全部，1=已上架，2=已下架 |

展示候选时至少提供商品名称和 ID，有图片时一并展示；让用户明确选择后再把商品信息用于活动。商品查询是只读的，不支持订单、库存或价格变更。种草活动的实物奖励使用独立的实物奖励库，不能把商品 ID 当作 `physical_reward_id`。打卡活动的实物奖励使用 `list_checkin_prizes` 查询的奖品 ID，不能用商品 ID 替代 `prize_id`。

配置打卡活动的实物奖励时调用 `list_checkin_prizes`：可传 `keyword` 按奖品名称搜索，并用 `page`、`limit` 分页；向用户展示奖品名称、ID 和图片，让用户选定后再填入 `prize_id`。该奖品库与店铺商品列表分开。

## 创建活动

创建前先收集真实配置，整理成活动配置确认单并让用户整体确认。活动封面图和头图必须生成，不能跳过或用占位图。

1. 先询问用户是否同意生成活动封面图和头图，并收集画面主题、风格、文案等必要信息。用户明确同意前，不得调用图像生成能力。
2. 获得同意后分别生成封面图和头图，再展示给用户确认。创建时直接把生成结果返回的真实图片路径填入对应图片字段即可，本地文件路径或图片 URL 均可；不需要额外上传、转换成公网 URL 或验证公网可访问性，也不要因只有本地路径而暂停创建或要求用户上传。不得编造图片路径。
3. 开始时间/日期必须先询问用户，并选在未来；不得默认设为当前时间或留空。用户确认两张图、未来开始时间/日期和完整活动配置后，才调用对应的创建工具一次。用户说先不创建或还要修改时，不要调用创建工具。

图片字段填写规则：种草有礼和有奖打卡的封面填 `cover`、头图填 `head_image`；抽奖活动的封面填 `banner`、头图填 `head_banner`。每个字段只填写对应图片的路径字符串，例如 `/absolute/path/cover.png`，不要填 Markdown 图片语法、提示词或 Base64 内容。

- **种草有礼**：调用 `create_seeding_activity`。封面 `cover`、头图 `head_image`、未来的报名开始时间、报名结束时间、奖励档位和商品信息都必填。完整字段与奖励规则见 [seeding-fields.md](references/seeding-fields.md)。
- **抽奖活动**：调用 `create_draw_activity`。活动封面 `banner`、头图 `head_banner`、未来的 `started_at` 和 `ended_at` 都必填；实物奖品先用 `list_products` 让用户选。若用户选择关注公众号（`draw_method=3/4`），商家必须先完成公众号授权；授权完成后无需上传公众号二维码，C 端二维码由后端生成。客服二维码仍须由用户提供。完整字段和联动校验见 [draw-fields.md](references/draw-fields.md)。
- **有奖打卡活动**：调用 `create_checkin_activity`。开始日期 `start_date` 必填，先向用户确认并选未来日期；固定期限活动需提供不早于开始日期的 `deadline_date`。打卡类型、线下定位、活动级奖励、周期、阶梯奖励、审核、视频、会员等级及关联商品均按用户确认结果配置。实物奖励先用 `list_checkin_prizes` 查询奖品库并让用户选择 `prize_id`；关联商品使用 `list_products`。完整字段和联动校验见 [checkin-fields.md](references/checkin-fields.md)。

工具返回成功后，把活动 ID 和状态告知用户。返回错误时如实转述并说明可修正的字段；不得伪造成功结果。
