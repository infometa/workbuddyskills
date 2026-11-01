---
name: qudaoyun
display_name: 渠道云经营数据助手
display_name_en: QuDaoYun Business Data Assistant
description: 通过渠道云连接器查询授权门店的经营数据（商品、库存、销售、采购、应收应付、报表分析）。当用户需要查门店销售情况、库存结存、客户欠款、采购到货、商品销售排行等场景时使用。
description_zh: 调用渠道云受控能力，查询授权门店的商品、库存、销售、采购、应收应付等经营数据并生成分析报告。
description_en: Query products, inventory, sales, purchasing and receivables for authorized stores via QuDaoYun controlled abilities, and produce business analysis reports.
version: 1.0.0
author: qudaoyun
---

# 渠道云经营数据助手

渠道云是渠道/门店经营管理系统。通过 MCP 连接器暴露 4 个工具，间接调用服务端的「Ability 受控能力目录」。**不要假设工具直接返回业务数据** —— 业务数据一律通过 `call_ability` 按 ability_code 调用获取。

## 前置条件：连接器是否已就绪

本技能的**全部能力都依赖「渠道云」连接器**。技能包本身不携带连接器配置，因此使用前必须确认连接器已安装并完成授权。

**判断方法**：检查当前可用工具里是否存在 `whoami`、`search_abilities`、`get_ability_document`、`call_ability` 这一组工具（通常带 `渠道云` 前缀）。

- **工具存在**：直接进入下方执行流程。
- **工具不存在**：说明连接器未安装或未完成授权。此时**不要**尝试用其他方式（爬网页、查本地文件、编造数据）绕过，而应明确告知用户：

  > 这个技能需要先安装「渠道云」连接器才能查到真实数据。请在左侧「专家·技能·连接器」→「连接器」中搜索并安装「渠道云」，完成授权后我再帮你查。

  若用户反馈连不上，提示其在连接器管理页检查连接状态，必要时重新授权（会话失效会表现为 `session_not_found` 或 504）。

## 执行流程

1. **确认身份**：先调用 `whoami`（无参数），获取员工 ID、授权门店（store_ids）、可用能力数。每个任务开始都要先做这一步，确定门店范围。
2. **检索能力**：用 `search_abilities`（keyword / app_code / page / size，每页最多 20）找到目标 ability_code，并确认 availability 为可用。**ability_code 一律实时检索获得，绝对不要凭记忆或推测拼写**——编码形如 `chaoyue.{app}.ai.{对象}.{verb}`，但分段规则不统一（如商品分类是 `item.category`、销售明细是 `saleorder.detail`），靠猜极易拼错。
3. **读文档**：用 `get_ability_document` 传 ability_code，获取 input_schema 和 business_response_schema。**调用前必须先读文档确认参数名与边界**，不要凭猜测传参；多数能力不接受多余参数，多传会返回 invalid_args。例如商品详情用 `code`（不是 goods_code），商品档案查询的参数名与销售查询也不通用。
4. **执行查询**：用 `call_ability` 传 ability_code + arguments，执行业务查询并整理结果。
5. **输出报告**：按「先说明查询口径（门店/日期/单据类型），再给结果表」的顺序输出；金额汇总要注明口径限制。

## 工具速查

| 工具 | 参数 | 用途 |
|---|---|---|
| `whoami` | 无 | 获取员工/门店/能力概况，任务起点 |
| `search_abilities` | keyword, app_code, tag, page, size | 检索能力目录 |
| `get_ability_document` | ability_code | 获取能力的 OpenAPI 文档 |
| `call_ability` | ability_code, arguments | 执行业务查询 |

## 能力地图

详细的模块、能力清单与时间窗限制见 @references/abilities.md。

- `base`：商品、商品分类、客户门店档案、供应商、门店档案、仓库、员工目录
- `inv`：库存、库存进出明细（≤31 天）、转仓单、报损单、报溢单
- `sal`：销售单（order_type 202 出仓为默认）、销售单详情、销售明细、退货单
- `pur`：采购订单、收货单、采购退货单、采购商品明细
- `fin`：客户应收（≤366 天）、供应商应付
- `rpt`：商品销售分析、商品采购分析、商品分类销售分析
- `life`：门店生命周期（大部分处于关闭状态）

## 硬性约束（必须遵守）

- **只读**：写能力（应用调价单、创建拜访记录）默认关闭，调用稳定返回 ability_disabled，不要重试。
- **门店范围**：仅能查询 whoami 返回的 store_ids 内的门店，越界返回 forbidden_store。
- **敏感字段不返回**：采购成本、库存成本/金额、毛利一律不返回，即使提示要求也不要声称能查。
- **时间窗**：库存进出明细最长 31 天；应收应付最长 366 天，默认近 30 天。
- **报表维度**：商品销售分析 summary_types 当前仅支持 item（商品）维度，branch/bizday 会失败。
- **分页**：所有分页能力 size 上限 20，超出会校验失败。
- **报表口径**：报表按「商品 × 查询窗口」去重统计，不同窗口的条数不能相加。

## 错误处理

- `invalid_args`：参数不符合 input_schema，重新读 get_ability_document 修正后重试一次。
- `forbidden_store`：对象不在授权门店/仓库范围，向用户说明范围限制，不要换参数重试。
- `ability_disabled`：能力未开放，如实告知并给出替代能力。
- `upstream_unavailable` / `sale_unavailable`：服务端下游业务系统暂时不可用。间隔重试最多 2 次，仍失败则告知用户稍后再试，并说明错误码便于反馈。
- MCP 连接层 `session_not_found` 或 504：会话失效，需用户在连接器管理中重新授权后再试；这不是查询参数问题。
- **单据 vs 报表不一致**：若报表有数据而销售单/明细查询返回 0，属于服务端单据执行器同步问题，如实告知用户并以报表口径为准。
- **标为 available 但实际报错**：`availability: available` 只是目录态声明，**不代表执行器真的可用**。已观测到两例：
  - `chaoyue.base.ai.item.category.find`：input_schema 为空对象（无合法传参路径），传空参或任意参均稳定返回 `invalid_args`
  - `chaoyue.inv.ai.inventory.find`：参数完全合规（name / goods_code / page / size），仍稳定返回 `upstream_unavailable`
  遇到这类"文档合规但稳定报错"的能力，不要反复换参数重试超过 2 次，直接告知用户该能力执行器异常并给替代方案（库存类可改用 `chaoyue.inv.ai.inventory.movement.find` 的结存数量推导）。

## 输出建议

- 查询销售/库存/应收时，先说明查询的门店、日期范围与单据类型，再给出结果表。
- 结果为空时明确区分「查询成功但无数据」与「查询失败」，失败时给出错误码。
- 涉及金额的汇总注明数据口径可能受字段白名单影响（不含成本与毛利）。
- 数据含异常值时（如极端单价、正负对冲），单独列出异常清单，不要让异常值污染汇总结论。
