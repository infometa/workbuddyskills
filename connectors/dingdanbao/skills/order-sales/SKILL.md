---
name: dingdanbao-order-sales
description: "订单豹代客下单、复购、草稿、报价、销售订单跟进与审核。"
description_zh: "代客下单、复购、草稿、报价、销售订单查询与审核。"
description_en: "Ordering on behalf of customers, repurchase, drafts, quotations, sales-order tracking and audit."
version: "1.0.0"
author: "订单豹"
---

# 订单豹 · 下单与销售

搜客户、确认清单、提交订单、复购、草稿、报价和审核。

## 认证说明

登录失败时请用户打开连接器设置重填账号密码。不要在对话里要密码。

## 对用户说话

只说姓名、手机号、商品名、单号、金额。不要说内部编号、会话键、工具名或参数名。

## 模型路由（不要向用户复述）

为开单而搜客户用本技能。催款和收款码用财务技能。只查档案、不准备下单用客户技能。库存、采购补货、业绩简报不用本技能。禁止教用户跑命令行，禁止提配置文件路径。

## 代客下单铁律

1. **先定客户，再识别商品。** 先 `ddb_search_customers`。多个结果时列出姓名+手机号让用户选，禁止自动挑。选定后用返回 JSON 里的 `memberId` 作为后续 `member_id`，不要把 `memberId` 展示给用户。
2. **`ddb_build_confirmation` 必须同时传 `text` 和 `member_id`。** `text` 用用户的下单原话（商品和数量）；`member_id` 用上一步的 `memberId`。禁止只传 `text`。必须把返回的 `confirmation` 展示给用户。
3. **内部键只回传、不展示。** 从工具 JSON 取 `sessionKey`、`memberId`、`result.goods[].skuId`、`draft_id`、`orderId`，原样传给下一跳工具。改数量/单价：按商品名在 `result.goods` 里匹配 `skuId`，再调用 `ddb_apply_sku_change`（`session_key` + `sku_id` + `num`/`price`）。禁止重新 `ddb_build_confirmation`，禁止本地改价，禁止向用户索要内部 ID。
4. **用户明确说「确认 / 提交」后再 `ddb_submit_proxy_order`。** 禁止静默提交。同一 `sessionKey` 只能成功提交一次。`confirmation` 若出现「待补全」，先问用户补齐再提交。
5. **审核三环须用户逐环确认**，禁止自动串联。只支持通过，不支持驳回。先查详情确认当前环节，再只调对应的 `ddb_audit_*`。

## 可用工具

### ddb_search_customers

搜索客户。参数：`keyword`(必填)、`page`、`page_size`。返回客户列表；对用户只展示姓名和手机号。

### ddb_build_confirmation

生成确认清单。参数：`text`(必填)、`member_id`(必填)、`stash_id`、`salesman_id`。返回 `sessionKey` + `confirmation`。

### ddb_apply_sku_change

改 SKU 数量或单价并重新计价。参数：`session_key`(必填)、`sku_id`(必填)、`num`、`price`。

### ddb_submit_proxy_order

提交代客订单。参数：`session_key`(必填)，可选覆盖 `member_id`、`delivery_type`、`salesman_id`、`buyer_message`、`stash_id`、`receiver_name`、`receiver_mobile`、`pay_way`。

### ddb_list_orders

销售订单列表。参数：`keyword`、`order_status`(默认 effective；待审 order_check / price_check / second_check)、`page`、`page_size`、`member_id`。

### ddb_get_order_detail

订单详情。优先 `order_no`，其次 `order_id`。

### ddb_audit_order_check / ddb_audit_price_check / ddb_audit_second_check

三环审核通过。参数：`order_no` 或 `order_id`。用户明确「通过这一环」后再调。

### ddb_list_repeatable_orders

可复购历史订单。参数：`member_id`、`page`、`page_size`、`order_status`。

### ddb_list_frequently_bought

常购商品。参数：`member_id`(必填)、`page`、`page_size`、`keyword`。

### ddb_build_repeat_order

复购确认清单。参数：`member_id`(必填)，`order_id`/`order_no` 二选一，`quantity_multiplier`、`stash_id`、`salesman_id`。返回 `sessionKey` + `confirmation`。

### ddb_submit_repeat_order

提交复购。参数：`session_key`(必填)、`source_order_id`。

### ddb_list_drafts / ddb_save_draft / ddb_load_draft / ddb_delete_draft / ddb_submit_draft

草稿。保存用确认清单的 `session_key`；取回后展示 confirmation，用户确认再提交。删除须用户确认。

### ddb_share_quotation

草稿报价短链/海报。参数：`draft_id`(必填)、`generate_link`、`generate_qrcode`。

### ddb_share_order_poster / ddb_share_payment_link

订单海报、收款短链。参数：`order_id`；支付链可附 `receipt_id`。

### ddb_get_order_todo_counts

各状态待办数量。无参数。

### ddb_track_orders

跟进列表。参数：`keyword`、`order_status`、`page`、`page_size`、`member_id`。

### ddb_lookup_order

查单笔进度。参数：`keyword` / `order_no` / `order_id` 至少一个。

## 使用示例

- 「帮王老板下单，酱油 5 桶料酒 10 瓶」→ 搜客户 → 用户选定 → `ddb_build_confirmation(text, member_id)` → 展示 confirmation → 确认后提交。
- 「把酱油改成 10」→ 在上一轮 `result.goods` 里取该商品 `skuId` → `ddb_apply_sku_change`。
- 「审核通过订单 DDxxxx」→ 先看当前环节 → 只调对应审核工具。
- 「按上一单再来一份」→ 可复购列表 → `ddb_build_repeat_order` → 确认后提交。

## 错误场景

| 现象 | 处理 |
|------|------|
| 未获取到登录凭证 / 登录失败 | 请用户在连接器设置重填账号密码后重新连接 |
| 客户不唯一 | 列出姓名+手机号让用户选 |
| 会话不存在 / 已提交 | 不要重试同一 sessionKey，重新 search + build |
| 请先审核订单 | 当前不是这一环，先查详情 |
| 改数量失败 / 缺少 sku_id | 从 `result.goods` 取 `skuId`，不要问用户 |
