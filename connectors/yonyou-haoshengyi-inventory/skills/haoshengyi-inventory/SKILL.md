---
name: haoshengyi-inventory
display_name: 用友好生意进销存查询
display_name_en: Yonyou HaoShengYi Inventory Query
description: 通过用友好生意官方 MCP 查询已授权账套的采购、销售、库存、往来与经营报表，完成进销存问数与只读分析。
description_zh: 连接用友好生意，查询授权账套的采购、销售、库存、往来及经营报表，完成进销存问数与只读分析。
description_en: Query purchasing, sales, inventory, receivables and business reports from authorized Yonyou HaoShengYi account books via its official MCP service.
version: 1.3.0
author: 畅捷通信息技术股份有限公司
---

# 用友好生意连接器使用说明

本技能用于指导 AI 通过「好生意 MCP 官方」服务（由畅捷通提供）完成进销存数据查询与分析。默认场景为只读问数。

## 何时使用本技能

- 用户询问进销存业务数据：采购、销售、库存、往来、资金、经营报表等。
- 用户要求查询商品库存、销售订单、采购订单、客户应收、供应商应付等业务事实。
- 用户要求基于账套数据做进销存分析、汇总、期间对比或生成经营摘要。

## 服务与认证前置

- MCP 服务地址：`https://mcphub.chanapp.chanjet.com/27/mcp`（Streamable HTTP，HTTPS）。
- 认证方式：MCP 标准 OAuth 2.1，由 WorkBuddy 内置 OAuth 管理器自动完成（未携带凭证时服务返回 401 并提供 OAuth 发现元数据）。
- 配置中不写入任何密钥；也不要向用户索要或记录 Token。
- 授权失效（401/403）时：提示用户在连接器管理中重新连接授权，不要反复重试，更不要伪造调用结果。

## 调用流程（必须遵守）

1. **initialize 握手**：首次连接先完成 MCP `initialize` 建立会话。它是协议握手步骤，不是业务查询工具，不要向用户承诺"initialize 能查数据"。
2. **工具发现**：通过 `tools/list` 读取服务实际暴露的工具名称、参数 Schema 与描述。所有调用必须以返回的真实工具为准，不得编造工具名或参数。
3. **账套选择**：
   - 用户未指定账套：调用 `accountingOpenapiCcAiBookQueryV1` 获取账套列表，识别并使用默认账套。
   - 用户指定账套：按名称对账套列表做模糊自然语言匹配，确认 `book-id`。
   - 匹配到多个账套时：列出候选让用户确认后再查询。
   - 不得跨账套混用数据，不得猜测或推断未授权账套。
4. **查询执行**：按工具 Schema 传参（注意日期格式、期间范围、分页参数），一次查询失败可修正参数重试一次，仍失败则如实报告。

## 参数模式（以 tools/list 实际返回为准）

- 除 `accountingOpenapiCcAiBookQueryV1` 外，其余工具均需在顶层传 `book-id`（账套ID，别名 tenant-id，来自账套列表的 `tenant.id` 数字字符串，不是域名或企业ID）。
- 业务参数统一包装在 `$x-request-body$` 对象内：`OperateGuide` 传 `keyword`；`QueryboV60` 传 `label`（业务对象中文名）与 `pageSize`（最大 100，默认 5）；`Excutefn` 传 `code`（来自 OperateGuide 返回的接口 code）及可选 `body` / `params` / `pathParams`；`ReportDesc` 传 `query`（GraphQL 字符串）。
- `BookQueryV1` 固定传 `Content-Type: application/json` 与 `queryType: BINDING_TO_THIRD_PLATFORM`。
- `QueryboV60` 返回的枚举字段带 `enumTypeName`、外键字段带 `referBoName`；GraphQL 查询中枚举拼 `**Enum{label value}`、外键拼 `**Id{id name}`。
- 以上参数模式已在编号 27（好生意）与编号 28（好业财）两个服务的真实授权环境下逐工具实测确认。

## 官方六项工具与调用顺序

以下六个工具名已通过 2026-10-27 对编号 27 服务的 `tools/list` 实测确认：

1. `accountingOpenapiCcAiBookQueryV1`：启动时首先查询可用账套，获取并确认 `book-id` 上下文；多个账套时让用户选择。
2. `accountingOpenapiCcAiOperateGuide`：不确定接口或操作方法时，以业务关键词搜索接口及使用说明。
3. `accountingOpenapiCcAiQueryboV60`：不知道业务对象（BO）名称、字段时先查定义；尽量只取 `id`、`name`、`code` 等必要字段。枚举字段按 `**Enum{label value}` 形式选择，外键按 `**Id{id name}` 形式选择（以返回 schema 为准）。
4. `accountingOpenapiCcReportDesc`：查询报表维度字段定义（GraphQL 格式，`reportName` 必填且不可为空）。**注意**：官方介绍页写的是 `accountingOpenapiCcAiQueryDesc`，但服务实际暴露的工具名为 `accountingOpenapiCcReportDesc`，一律以 `tools/list` 实际返回为准。
5. `accountingOpenapiCcAiQueryreport`：根据已获取的报表定义查询报表数据，支持分页。
6. `accountingOpenapiCcAiExcutefn`：按照操作指南和工具参数 schema 查询业务对象、档案或执行被允许的业务操作。

## 典型意图与处理

| 用户意图 | 处理方式 |
| --- | --- |
| 查询本月销售收入、订单状态 | 确定统计期间与账套 → 选定口径 → 调用销售单据或报表查询工具 |
| 查看某商品当前库存 | 按商品编码/名称定位档案 → 查询可用库存，注明仓库与库存口径 |
| 查询采购订单及到货进度 | 按订单条件过滤 → 说明查询截止日期 |
| 查看客户应收 / 供应商应付 | 调用往来查询类工具，说明余额截止日期 |
| 查询经营报表 | 先用 `accountingOpenapiCcReportDesc` 发现报表字段定义，再用 `accountingOpenapiCcAiQueryreport` 获取数据 |
| 生成进销存分析或经营摘要 | 基于真实返回数据归纳，区分"数据事实"与"分析推断" |

如所需能力未出现在 `tools/list` 中，明确告知用户当前不支持，不得模拟调用成功。

## 输出要求

- 说明统计期间、账套名称、金额单位（元/万元）与数据口径。
- 只呈现工具真实返回的数据；分析结论须与原始数据明确区分。
- 返回数据为空时说明无结果，不推断为零；注明查询时间与筛选条件。
- 数据缺失、口径不一致或工具返回异常时，如实说明而不是编造数字。

## 错误处理

| 场景 | 处理 |
| --- | --- |
| 401 / 授权失效 | 引导用户重新连接授权，终止本次查询 |
| 账套不存在或无权限 | 停止查询，向用户解释原因 |
| 参数错误 | 按 Schema 修正参数重试一次，仍失败则报告原始错误信息 |
| 多账套匹配不唯一 | 列出候选账套请用户选择 |
| 工具不存在（能力未暴露） | 明确告知不支持，不模拟成功 |
| 接口超时 | 展示可理解的错误；对非幂等写操作不得盲目重试 |
| 返回 `status: 401` 且 `code: 50112`（"该appKey和orgId本月访问已达上限"） | 本月调用额度已用完，停止重试；如实告知用户，可提示返回体中的 `buyUrl`（流量包购买链接，约 5 分钟有效）或等待下月额度恢复 |
| 返回 `code: thirdsrv.e0004`（"用户未在当前账套授权，请设置用户权限"） | OAuth/账号已在企业层认证，但该用户未被分配此账套的操作权限；停止重试，提示用户由账套管理员在好生意内为该用户设置账套权限，或换用已授权的账套 |

## 安全与高风险操作

- 仅访问用户已授权的账套；不泄露 Token、客户敏感信息与账套数据到无关上下文。
- 默认只读查询。对新增、修改、删除、提交、审核、反审核、结算、付款、出库等可能产生业务影响的动作，必须在调用前说明目标账套、操作对象、关键字段、影响范围与参数，取得用户明确确认后才可执行；未确认不得执行。
- 不得自行推断接口参数或构造未经 Schema 验证的操作。
- 不得将分析推断伪装成账套真实返回的数据。
