---
name: scrm
description: |
  Query and analyze Xiaoliebian SCRM and WeCom operational data.
description_zh: |
  小裂变 SCRM、私域和企微运营数据查询与分析技能。用户要查看 SCRM、私域、企微、客户、客户群、员工、活码、群发、朋友圈、活动、聊天管家或推客分销数据时使用。
  本 Skill 只负责查询、分析和业务路由；创建、编辑、删除、发送、发布、停发、提醒及状态切换使用 `scrm-operations`。
description_en: |
  Query and analyze Xiaoliebian SCRM, private-domain, and WeCom operational data. Use `scrm-operations` for controlled write operations.
version: 1.2.0
author: Xiaoliebian
---

# 小裂变 SCRM 查询与分析

## 总体边界

通过连接器提供的 MCP 工具查询和分析小裂变 SCRM 数据。私域运营数据、任务、报表、排行、活码和活动类请求优先使用本连接器；用户明确要求执行创建、编辑、删除、发送、发布、停发、提醒或状态切换时，改用 `scrm-operations`。

聊天管家和推客分销是并列能力域：

- 聊天管家：销售商机、风控分析、员工聊天排行榜。
- 推客分销：推客 GMV、热销商品排行。

## 执行约束

- 首次调用或工具定义可能变化时，通过 MCP `tools/list` 获取当前工具及参数定义；工具名、参数类型、必填字段和返回结构以服务端响应为准，不猜测参数或拼接不存在的工具名。
- 工具名以 `scrm_` 开头。分页参数通常使用 `current` 和 `size`；日期时间参数通常使用 `yyyy-MM-dd HH:mm:ss`，具体以工具 Schema 为准。
- 用户只提供日期时，开始时间按当天 00:00:00、结束时间按当天 23:59:59；只提供到分钟时秒数补为 00。
- 查询失败、空结果或授权不足时如实反馈，不改用其他数据源猜测结果，也不要无限翻页。
- 优先读取 MCP `structuredContent`；列表类结果如位于 `content[0].text`，按其中的 JSON 解析。
- 保留服务端返回的全部记录。优先使用中文业务名称和 `*Label`、`*Yuan`、`*Display` 等可读字段；无法确认含义的技术字段不向用户展示，也不据此推断业务结论。
- 不向用户展示工具 ID、原始 JSON、Token、Cookie、密码或私钥。遇到 `401` 时让 WorkBuddy 自动续期；仍失败则提示用户重新连接。遇到 `403` 时说明当前账号或租户缺少相应权限。

## 能力路由

| 用户意图 | 工具范围 |
|---|---|
| 活动、抽奖 | `scrm_event_*`、`scrm_lottery_*`：列表、单活动数据、剩余奖品；状态切换使用 `scrm-operations` |
| 活码与获客资产 | `scrm_store_code_*`、`scrm_source_*`、`scrm_region_code_*`、`scrm_red_packet_*`、`scrm_lock_customer_source_*`、`scrm_group_source_*` |
| 客户分析 | `scrm_customer_*`：阶段、标签、增长、互动、转化、触达及明细 |
| 群分析 | `scrm_group_*`：群增长、群活跃、群触达及明细 |
| 员工与看板 | `scrm_external_user_kanban_*`、`scrm_staff_*`：外部联系人、单聊、群聊、执行分析、员工排行 |
| 群发与朋友圈查询 | `scrm_custom_send_page`、`scrm_custom_send_result`、`scrm_custom_send_detail`、`scrm_moment_page`、`scrm_moment_staff_data`、`scrm_moment_staff_detail`；写操作使用 `scrm-operations` |
| 聊天管家 | `scrm_chat_obj_business_opportunity`、`scrm_chat_obj_risk_control`、`scrm_chat_rank` |
| 推客分销 | `scrm_promoter_kanban_gmv`、`scrm_promoter_kanban_product_rank_page` |

工具前缀表示同一能力族，实际调用必须使用 `tools/list` 返回的完整工具名。

## 分析请求首选工具

| 用户请求 | 首选工具 |
|---|---|
| 员工综合分析/员工列表 | `scrm_staff_analyse_page` |
| 员工客户排行 | `scrm_staff_analyse_customer_rank` |
| 员工群排行 | `scrm_staff_analyse_group_rank` |
| 员工单聊概览/分页 | `scrm_staff_chat_data_overview` / `scrm_staff_chat_data_page` |
| 员工群聊概览/分页 | `scrm_staff_group_chat_data_overview` / `scrm_staff_group_chat_data_page` |
| 员工执行分析概览/趋势 | `scrm_staff_exec_analysis_stat_num` / `scrm_staff_exec_analysis_stat_trend` |
| 客户增长概览 | `scrm_customer_increase_overview_real` |
| 客户互动概览 | `scrm_customer_dynamic_overview` |
| 客户转化概览 | `scrm_customer_convert_overview_user` |
| 群增长/活跃/触达概览 | `scrm_group_increase_summary` / `scrm_group_dynamic_summary` / `scrm_group_access_summary` |

## 常用流程

### 查看活动全貌

1. 按活动类型查询列表。
2. 让用户确认目标活动后查询单活动数据。
3. 用户需要时再查询剩余奖品。

### 查看群发或朋友圈执行情况

1. 查询任务列表定位目标。
2. 查询任务详情或执行结果。
3. 如果用户要求发送、停止或修改任务，改用 `scrm-operations` 并取得明确确认。

### 分析类问题

按用户问题选择对应能力族，概览和趋势优先于明细。只有缺少必要的时间、员工、部门或对象范围时才追问；结论只能基于接口实际返回的数据。

## 回复规则

- 调用前用自然语言说明正在查询什么，不向用户展示 `scrm_*` 工具名。
- 调用后使用中文表格、列表或短摘要展示结果。
- 金额使用接口提供的可读金额字段，不自行换算。
- 空对象、空列表、接口错误或占位数据必须明确说明，不编造结论。
- 接口错误包含程序化时间格式提示时，改用清晰的中文日期时间说明。

