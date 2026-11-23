# 问法路由

常见问法与工具组合。日期按[共享规则](shared-rules.md)换算后再传参。

## 查询

| 问法 | 工具组合 | 要点 |
| --- | --- | --- |
| 我上个月报了多少钱？ | `ycbx_order_list`（上月起止日期，翻完分页） | 按[统计口径](order-status.md#统计口径)汇总，写明口径 |
| 我有几张单子在审批？ | `ycbx_order_list`（`statusName=待审批`，再查 `待处理`） | 两个状态分别查询后合并 |
| 我最近的差旅报销单有哪些？ | `ycbx_order_list`（`templateName=差旅报销单`） | 模板名不对时按返回的可选模板重试一次 |
| 帮我看看 BX2608261602387327 这张单 | `ycbx_order_detail` | — |
| 我 9 月那张 3000 多的单子报了什么？ | `ycbx_order_list` 定位 → `ycbx_order_detail` | 多张匹配时让用户选 |
| 我的报销单到谁那了？ | `ycbx_order_list`（`statusName=待审批`）→ 对每张调 `ycbx_order_progress` | 单据多时先列出来，问用户要看哪张 |
| 这张单超预算了吗？ | `ycbx_order_budget` | `overBudget` 和 `overInfo` 一起说明 |
| 我还有哪些费用没报？ | `ycbx_fee_unused_list` | 有 `missingFields` 的要提醒先补填 |
| 发票夹里还有多少张没用的发票，一共多少钱？ | `ycbx_invoice_unused_list`（翻完分页） | 汇总金额，号码只说后 4 位 |
| 去上海出差住宿标准是多少？ | `ycbx_cost_standard`（`cityName=上海`） | 说明标准可能按角色区分，以 App 校验为准 |
| 我出差的餐补标准是多少？ | `ycbx_user_profile`（取常驻城市，不在常驻地才算出差）→ `ycbx_cost_standard` | 用户没说城市时问一句目的地 |
| 我还欠公司多少借款？ | `ycbx_loan_list`（翻完分页） | 汇总 `remainingAmount`，`paidOff` 为 true 的不计 |
| 我是哪个部门的？ | `ycbx_user_profile` | — |
| 今年我一共报销了多少钱，按月列一下 | `ycbx_order_list`（今年 1 月 1 日到今天，翻完分页） | 按 `submitDate` 分月汇总并写明口径 |

## 不调用工具

| 问法 | 回应 |
| --- | --- |
| 帮我把这张打车发票报了 | 本服务只能查询，不能填单。请在有成报销 App 里打开 AI 助手，上传发票即可一键生成报销单 |
| 帮我提交 / 撤回这张单子 | 本服务只读，提交和撤回需要在有成报销 App 里操作 |
| 帮我审批一下张三的报销单 | 本服务不支持审批，请在有成报销 App 里处理 |
| 帮我把这张发票上传到发票夹 | 暂不支持上传，请在有成报销 App 里上传 |
| 帮我看看李四的报销单 | 只能查询你本人的数据 |
| 查一下我在 CRM 里的客户 | 这是有成 CRM 的数据，不在本服务范围 |
