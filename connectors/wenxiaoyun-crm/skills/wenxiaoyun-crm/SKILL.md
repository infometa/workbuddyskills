---
name: wenxiaoyun-crm
description: 本租户管理员只读查询稳销云线索、跟进、通话、报表、业绩、SOP 和库存复盘。禁止写操作。
description_zh: 稳销云管理员只读查询技能
description_en: Read-only Wenxiaoyun CRM lookup
version: 1.2.0
author: 稳销云
---

# 稳销云只读技能

仅超级管理员或管理员授权后使用。查询范围是当前租户。字段含义以本文为准。

## 硬性规则

- 禁止创建、修改、删除、导出文件，也不要索要完整手机号。
- 微信可以读指定员工的单聊原文，不能读群聊。
- 录音地址 `file_url` 和转写 `audio_text` 可以读取。转写单条最多约 2000 字。
- 租户以授权 token 为准。员工或部门不属于本租户时，结果为空。
- 姓名至少 2 个字。用手机号定位线索时必须是 11 位。
- 线索列表每页最多 10 条。跟进、通话、报表、SOP、库存复盘每页最多 20 条。
- 返回里的 `total` 是命中总数。`total` 大于本页条数时，用 `page` 继续取，直到答完或用户只要概况。
- SOP 分数明细可能上万条，不要逐页拉全量。先看 `list_sop_stats`，再按具体员工查明细。
- 图表、线索报表、员工报表、业绩合计、SOP 分数统计和分数明细必须带起止时间，跨度不超过 31 天。

## 字段

线索和通话使用稳定英文字段：

- `clue_id`：线索内部 ID。`clue_num`：PC 上的线索单号。
- `c_name`：客户姓名。`mobile_short`：隐号，如 `138****1234`。`mobile`：同样是隐号，不是完整号码。
- `staff_name`：跟进人或通话员工。`status`：线索状态。`level`：线索等级。
- `response_time`：分配到首次通话的间隔，用来回答谁响应慢。它不是单通电话的响铃时长。
- `file_url`：录音地址。`audio_text`：录音转写，格式为 `声道:文本`。
- `start_time` / `connect_time`：通话开始、接通时间。`duration_sec`：通话秒数。`result`：已接通或未接通。
- 跟进时间线 `type` 为 `跟进` 或 `通话`。跟进看 `content`，通话看上面的录音字段。

报表、SOP、库存复盘的每一行直接使用 PC 中文列名。等级列使用等级名称，如 `A`、`B`，不是数字编号。

业绩合计使用中文键：`新增线索`、`新增商机`、`到访量`、`认购笔数`、`认购金额万元`、`网签笔数`、`网签金额万元`。

## 工具

- `search_clues`：线索列表，也用来打开报表和库存格子里的名单。回答数量用 `total`。
- `get_clue`：用 `clue_id`、`clue_num`、`mobile` 或 `mobile_short` 定位。命中一条时 `matched` 为 `one`，多条为 `multiple`。
- `list_follow_todos`：待跟进线索。
- `list_follow_records`：指定线索的跟进和通话时间线。
- `list_call_records`：通话记录。传 `clue_id` 时按该线索手机号查询。有时间范围时看 `quality` 的通话次数、接通次数、接通率。
- `list_clue_report` / `list_staff_report`：已启用报表。`view` 传 `营业顾问`、`主管` 或 `经理`，按报表名称匹配；不传用第一张。`report_name` 是实际选中的表。
- `get_clue_report_chart`：线索汇总。`dimension` 用 `staff`、`channel`、`create_type`。`metric` 用 `clue_total`、`valid_clue_total`、`visited_total`、`order_total`、`unconnected_total`、`unprocessed_total`。结果按值从高到低，最多 30 个。
- `get_performance`：认购金额、网签金额、新增商机等合计。不传员工和部门时统计全租户。
- `list_sop_stats`：SOP 分数统计。`list_sop_score_details`：分数明细。`list_sop_tasks`：任务列表。
- `list_inventory_review`：库存复盘。
- `list_visits`：到访。`list_orders`：订单。`list_clue_pool`：公海，不能认领。
- `list_clue_action_logs`：线索操作日志。
- `list_wechat_calls`：微信语音和视频通话。`list_wechat_chats`：指定员工的单聊。
- `list_org`：部门和在职成员。`list_staff_alloc_status`：成员接单状态。
- `get_clue_rules`：查重范围和公海规则。`list_products`：产品。`list_channels`：渠道。

## 报表格子怎么打开名单

先用报表拿到数字和员工，再用 `search_clues` 的 `total` 对数量，用 `list` 看姓名。筛选和创建时间、员工一起传。

- 总线索量：只传时间和员工或渠道。
- 有效线索量：再传 `level=有效`。
- 未接通：`status_text=未接通`。未处理：`status_text=未处理`。
- 到访量：`visit=已到访`。
- 几天未跟进：`no_follow_days`。即将掉公：`expire_pool_days` 只传 1 或 3。
- 今日新分：`first_alloc_staff_id` 加当天 `alloc_start`、`alloc_end`。
- 成交量不要用线索列表，改查 `list_orders`。

渠道转化用 `get_clue_report_chart`，`dimension=channel`。要比两天，同一工具各查一次。谁垫底用 `list_clue_report`，`sort_field` 传列名如成交量，`sort_order=asc`，再按 `page` 翻完。

## 问法怎么串

1. 「今天线索转化」→ `list_clue_report`，`view` 按角色传，起止时间传今天。要名单时按上一节打开。
2. 「今天认购和网签金额、新增商机」→ `get_performance`，起止时间传今天。
3. 「今天通话质量」→ `list_call_records`，看 `quality`，再抽 `audio_text`。谁响应慢看线索的 `response_time`，或 SOP 统计里的首电延迟。
4. 「今天上户量 / 腾讯上户量」→ `search_clues`，回答用 `total`。腾讯再传 `channel_name`。
5. 「查单号」→ `get_clue`。跟进和录音用 `list_follow_records`。操作过程用 `list_clue_action_logs`。
6. 「这个员工今天微信」→ `list_org` 拿员工 ID，再查单聊和微信通话。

## 错误处理

- 未授权：请用户在 WorkBuddy 中重新连接稳销云。
- 未找到：明确说当前租户没有匹配数据，不要编造。
- 命中多条：列出候选的单号、姓名和隐号，请用户指定一条。
