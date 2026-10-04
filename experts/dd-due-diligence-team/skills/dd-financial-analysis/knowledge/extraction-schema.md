# 财务分析抽取 JSON Schema

## 顶层结构

```json
{
  "company_name": "某某有限公司",
  "entity_identity": {
    "legal_name": "某某有限公司",
    "security_code": null,
    "uscc": "统一社会信用代码"
  },
  "fiscal_year": "2026Q1",
  "period_label": "2026/03",
  "period_type": "interim",
  "period_role": "current",
  "period_start": "2026-01-01",
  "period_end": "2026-03-31",
  "period_days": 90,
  "source_unit": "万元",
  "currency": "CNY",
  "statement_scope": "合并",
  "table_units": { "cross_validation": "元" },
  "balance_sheet": {},
  "opening_balance_sheet": {},
  "income_statement": {},
  "cash_flow": {},
  "financial_supplement": {},
  "opening_financial_supplement": {},
  "cross_validation": {},
  "industry_benchmarks": { "sources": [], "metrics": {} },
  "public_research": {
    "mode": "provided-only",
    "status": "not-run",
    "network_attempted": false,
    "queries": [],
    "sources": [],
    "enrichments": [],
    "conflicts": []
  },
  "source_refs": {},
  "material_manifest": [],
  "comparative_periods": []
}
```

`comparative_periods` 使用相同字段结构，按时间升序依次放置：可选的 `calculation_base`、`prior_year_3`、`prior_year_2`、`prior_year`、`prior_year_same_period`。角色不得重复；除 `prior_year_same_period` 为 `interim` 外均为 `annual`，顶层必须为 `current`。`calculation_base` 只用于最早展示年度的平均余额和增长率，不进入最终五期表。最近一期为中期时，同比使用 `prior_year_same_period`；年度报告使用 `prior_year`。

脚本将角色绑定到当前期年份：`prior_year/prior_year_2/prior_year_3` 分别为前一/前二/前三年，`calculation_base` 必须是最早分析年度的上一年；中期的 `prior_year_same_period` 必须与当前期月份或季度端点一致、年份相差一年、覆盖天数相差不超过一天。所有期间 `company_name` 必须一致。

## 期间和来源元数据

- `period_label`：报告表头显示值，如 `2025/12`、`2026/03`。
- `period_type`：`annual` 或 `interim`，不自动年化。
- `period_role`：当前或比较期角色。
- `period_start`、`period_end`、`period_days`：利润表/现金流量表实际覆盖起止日和天数；脚本按首尾均含当天反算天数，并与报告期标签核对。周转天数以脚本核实后的天数为分子。
- `source_unit`、`currency`、`statement_scope`：每个期间都必须显式提供；本模型的币种固定为 `CNY`，报表口径规范为 `合并`、`母公司` 或 `单体`。脚本不设默认值，拒绝“未披露/未知”等占位词，且所有比较期口径必须一致；其他币种需先扩展汇率来源与换算规则，不能直接混入。
- `table_units`：某一数据表来源单位与财务报表不同时逐表声明；只要 `cross_validation` 非空，就必须提供 `table_units.cross_validation`。
- `opening_balance_sheet`：本期间期初余额；平均资产、权益、应收、存货等必须从这里取期初值。
- `source_refs`：键为 `balance_sheet.total_assets` 等字段路径；值记录文件、页码/表名、报告期、口径和备注；公开增强来源同时记录 `source_id` 和 `source_origin`。
- `material_manifest`：逐份登记 `file_name`、`doc_type`、期间、口径、币种、单位、盖章/签章、可用性和来源类型。
- `entity_identity`：公开公司事实的主体锚点；至少记录法定全称，并在使用公开公司事实时提供证券代码或统一社会信用代码之一。
- `public_research`：最终输入必须显式提供，记录本次是否联网、查询结果、公开来源和字段级增强映射；不在其中重复保存待计算数值。

最终报告的 `material_manifest` 至少包含一个可用材料对象：

```json
{
  "file_name": "2025年度审计报告.pdf",
  "doc_type": "审计报告",
  "period": "2025/12",
  "statement_scope": "合并",
  "currency": "CNY",
  "source_unit": "万元",
  "source_origin": "provided",
  "usable": true
}
```

`source_origin` 允许：

- `provided`：客户或信贷经理提供的进件材料。
- `existing-public-file`：进件中已经包含的公开披露文件。
- `public-research`：本次运行通过联网检索新增的公开来源。

联网新增材料还要登记 `source_id`、`source_origin=public-research`、`local_file` 和 `sha256`，并与 `public_research.sources[].source_id`、文件名、期间及摘要一致。进件和公开来源出现同一字段冲突时，不得覆盖进件值；在来源记录和 narrative 中披露差异。公开来源材料不得登记为银行流水、纳税申报表、完税证明、发票底账、内部台账或授信方案。

行业基准或宏观背景材料使用 `doc_type=public_industry_source` 或 `public_context`；其 `statement_scope`、`currency` 必须为 `not-applicable`，`source_unit` 只能为 `ratio` 或 `not-applicable`。这类材料不得伪装成企业自身报表，也不得用于补充企业财务报表字段。

当前期及每个比较期都必须有非空 `source_refs`；每个登记项必须是含 `file` 以及 `page/sheet/range/section/ref` 之一的对象，且文件名必须对应 `material_manifest` 中同报告期、`usable: true` 的材料。每期至少一个引用必须真正指向同单位的财务报表/审计报告，不能用营业执照等非财务文件占位；附注明细引用也必须与其声明单位一致。全局清单允许登记 `usable: false` 的损坏或不适用文件。

## 公开研究 `public_research`

完整字段、来源等级和检索边界见 `public-source-policy.md`。模式与状态必须匹配：

- `provided-only` 对应 `not-run`，`network_attempted=false`，查询和新增来源为空。
- `auto-enrich` 或 `full-research` 在没有实质缺口时使用 `not-needed`。
- 联网成功且至少一个来源通过核验时使用 `completed`。
- 执行过检索但没有合格来源时使用 `no-usable-result`。
- 工具或网络不可用时使用 `network-unavailable`。

每个查询记录唯一 `query_id`、`query`、`purpose` 和 `outcome`。每个采用来源通过 `query_id` 链接一条 `outcome=accepted` 的查询，并记录 `source_id`、来源类型、证据范围、使用方式、标题、发布机构、原始 URL、发布日期、检索时间、适用期间、定位和主体匹配结果。

用于数值的公开来源必须满足：

- `evidence_use=numeric`，且来源等级允许数值使用。
- `evidence_scope=company_fact` 时 `entity_match=confirmed`，法定全称一致，且证券代码或统一社会信用代码至少一项一致。
- 保存 `local_file`、`sha256`、`period` 和 `locator`。
- 抽取值进入标准财务字段；`public_research` 只保留来源元数据。

每个公开补入字段必须写入 `public_research.enrichments`：

```json
{
  "period_role": "prior_year",
  "field": "balance_sheet.total_assets",
  "source_id": "public-001",
  "merge_action": "fill-null"
}
```

`field` 仅允许三表、期初表、补充数据、科目附注明细或行业基准中的真实字段；目标必须已有数值，首次输入中必须为 `null`/不存在。公司字段还必须在对应期间的 `source_refs[field]`（附注明细使用自身 `source_ref`）链接同一 `source_id` 和 `source_origin=public-research`。行业基准逐指标映射到 `industry_benchmarks.sources` 的同一 `source_id`。禁止用公开来源补写 `cross_validation` 中的流水、税表、发票或其他内部验证数值。

公开来源与进件值冲突时写入 `conflicts`，字段为 `period_role`、`field`、`source_id` 和固定的 `resolution=kept-provided`；冲突字段不得同时列入 `enrichments`。

新闻或聚合资料只能使用 `evidence_use=lead-only`，不得写入数值字段。研究报告只有在行业样本、年份、定义和方法明确时才能用于 `industry_benchmarks`。

## 科目附注明细 `note_details`

LLM 只抽取附注原始构成，不计算占比或贡献。键使用脚本事实键（如 `bs_inventory`、`bs_accounts_receivable`、`inc_revenue`、`cf_operating_cash_flow`）：

```json
{
  "bs_inventory": {
    "source_unit": "万元",
    "currency": "CNY",
    "statement_scope": "合并",
    "source_ref": { "file": "2025年度审计报告.pdf", "page": "附注页" },
    "raw_text": "附注中的定性说明原文或忠实摘要",
    "components": [
      { "name": "原材料", "amount": 1200 },
      { "name": "产成品", "amount": 800 }
    ]
  }
}
```

每个期间分别抽取，同一科目内的明细名称必须唯一；来源出现同名行时先按原始分类补充可区分名称，不得让脚本静默覆盖。脚本只对已筛出的显著异动科目匹配明细，统一换算为元，并计算各明细占科目余额比例、明细变动金额及其对科目变动的贡献。缺少相邻年度明细时不跨期拼接贡献率。

## 新旧准则同义科目（禁止拆成两个字段）

以下名称是**同一科目**在新旧会计准则下的两种叫法，值相同。抽取时只归入左侧字段，
**严禁**当作两个科目各抽一次，否则配平校验会重复计数：

| 归入字段                                     | 新准则名称           | 旧准则名称                                   |
| -------------------------------------------- | -------------------- | -------------------------------------------- |
| `trading_financial_assets`                   | 交易性金融资产       | 以公允价值计量且其变动计入当期损益的金融资产 |
| `trading_financial_liabilities`              | 交易性金融负债       | 以公允价值计量且其变动计入当期损益的金融负债 |
| `advances_from_customers`                    | 预收账款             | 预收款项                                     |
| `prepaid_accounts`                           | 预付款项             | 预付账款                                     |
| `noncurrent_liabilities_due_within_one_year` | 一年内到期的长期负债 | 一年内到期的非流动负债                       |

> 行业特有科目（结算备付金、拆出资金、存出保证金、应收保费、应收分保账款、
> 买入返售金融资产等）不在上表内：求和类配平校验对未列示行按 0 处理；
> 若原表有值但字段清单未覆盖，差异会体现在配平结果里（差额恰等于该行金额时
> 可由差额反查 diagnosis 定位）。

报表中两者通常**只出现其一**（新准则企业只有新名称，旧准则企业只有旧名称）。
若同一份报表两者都出现，取新准则名称对应的行，并在 `source_refs` 备注口径；
不要相加。

## 资产负债表 `balance_sheet`

| 字段                                         | 中文名                                       | 完整报告 |
| -------------------------------------------- | -------------------------------------------- | :------: |
| `cash_and_equivalents`                       | 货币资金                                     |    是    |
| `trading_financial_assets`                   | 交易性金融资产                               |    是    |
| `derivative_financial_assets`                | 衍生金融资产                                 |   条件   |
| `notes_receivable`                           | 应收票据                                     |    是    |
| `accounts_receivable`                        | 应收账款                                     |    是    |
| `receivables_financing`                      | 应收款项融资                                 |   条件   |
| `prepaid_accounts`                           | 预付款项                                     |    是    |
| `other_receivables`                          | 其他应收款                                   |    是    |
| `inventory`                                  | 存货                                         |    是    |
| `contract_assets`                            | 合同资产                                     |    是    |
| `assets_held_for_sale`                       | 持有待售资产                                 |   条件   |
| `noncurrent_assets_due_within_one_year`      | 一年内到期的非流动资产                       |   条件   |
| `other_current_assets`                       | 其他流动资产                                 |    是    |
| `current_assets`                             | 流动资产合计                                 |    是    |
| `debt_investments`                           | 债权投资                                     |   条件   |
| `other_debt_investments`                     | 其他债权投资                                 |   条件   |
| `available_for_sale_financial_assets`        | 可供出售金融资产                             |   条件   |
| `long_term_receivables`                      | 长期应收款                                   |   条件   |
| `long_term_equity_investments`               | 长期股权投资                                 |    是    |
| `other_equity_instrument_investments`        | 其他权益工具投资                             |   条件   |
| `investment_property`                        | 投资性房地产                                 |   条件   |
| `fixed_assets`                               | 固定资产                                     |    是    |
| `construction_in_progress`                   | 在建工程                                     |    是    |
| `productive_biological_assets`               | 生产性生物资产                               |   条件   |
| `oil_and_gas_assets`                         | 油气资产                                     |   条件   |
| `right_of_use_assets`                        | 使用权资产                                   |   条件   |
| `intangible_assets`                          | 无形资产                                     |    是    |
| `development_expenditure`                    | 开发支出                                     |   条件   |
| `goodwill`                                   | 商誉                                         |   条件   |
| `long_term_deferred_expenses`                | 长期待摊费用                                 |   条件   |
| `entrusted_loans`                            | 委托贷款                                     |   条件   |
| `foreclosed_assets`                          | 抵债资产                                     |   条件   |
| `deferred_tax_assets`                        | 递延所得税资产                               |   条件   |
| `other_non_current_assets`                   | 其他非流动资产                               |   条件   |
| `non_current_assets`                         | 非流动资产合计                               |    是    |
| `total_assets`                               | 资产总计                                     |    是    |
| `short_term_borrowings`                      | 短期借款                                     |    是    |
| `fvtpl_financial_liabilities`                | 以公允价值计量且其变动计入当期损益的金融负债 |   条件   |
| `trading_financial_liabilities`              | 交易性金融负债                               |   条件   |
| `derivative_financial_liabilities`           | 衍生金融负债                                 |   条件   |
| `notes_payable`                              | 应付票据                                     |    是    |
| `accounts_payable`                           | 应付账款                                     |    是    |
| `advances_from_customers`                    | 预收账款                                     |    是    |
| `contract_liabilities`                       | 合同负债                                     |    是    |
| `guarantee_deposits_received`                | 存入担保保证金                               |   条件   |
| `financial_assets_sold_for_repurchase`       | 卖出回购金融资产款                           |   条件   |
| `fees_and_commissions_payable`               | 应付手续费及佣金                             |   条件   |
| `employee_benefits_payable`                  | 应付职工薪酬                                 |    是    |
| `taxes_payable`                              | 应交税费                                     |    是    |
| `guarantee_compensation_reserve`             | 担保赔偿准备                                 |   条件   |
| `short_term_liability_reserve`               | 短期责任准备金                               |   条件   |
| `other_payables`                             | 其他应付款                                   |    是    |
| `liabilities_held_for_sale`                  | 持有待售负债                                 |   条件   |
| `noncurrent_liabilities_due_within_one_year` | 一年内到期的长期负债                         |    是    |
| `other_current_liabilities`                  | 其他流动负债                                 |   条件   |
| `current_liabilities`                        | 流动负债合计                                 |    是    |
| `long_term_borrowings`                       | 长期借款                                     |    是    |
| `bonds_payable`                              | 应付债券                                     |   条件   |
| `lease_liabilities`                          | 租赁负债                                     |   条件   |
| `long_term_payables`                         | 长期应付款                                   |   条件   |
| `long_term_employee_benefits_payable`        | 长期应付职工薪酬                             |   条件   |
| `provisions`                                 | 预计负债                                     |   条件   |
| `insurance_contract_reserve`                 | 保险合同准备金                               |   条件   |
| `deferred_income`                            | 递延收益                                     |   条件   |
| `deferred_tax_liabilities`                   | 递延所得税负债                               |   条件   |
| `other_non_current_liabilities`              | 其他非流动负债                               |   条件   |
| `non_current_liabilities`                    | 非流动负债合计                               |    是    |
| `total_liabilities`                          | 负债总计                                     |    是    |
| `paid_in_capital`                            | 实收资本（或股本）                           |    是    |
| `other_equity_instruments`                   | 其他权益工具                                 |   条件   |
| `capital_reserve`                            | 资本公积                                     |    是    |
| `treasury_stock`                             | 减：库存股                                   |   条件   |
| `other_comprehensive_income`                 | 其他综合收益                                 |   条件   |
| `special_reserve`                            | 专项储备                                     |   条件   |
| `surplus_reserve`                            | 盈余公积                                     |    是    |
| `general_risk_reserve`                       | 一般风险准备                                 |   条件   |
| `retained_earnings`                          | 未分配利润                                   |    是    |
| `total_equity`                               | 所有者权益合计                               |    是    |
| `total_liabilities_and_equity`               | 负债和所有者权益总计                         |    是    |

`opening_balance_sheet` 使用同一字段集。若来源只披露本期期末而没有期初，期初字段写 `null`，不得用期末余额替代。

## 利润表 `income_statement`

| 字段                       | 中文名           | 完整报告 |
| -------------------------- | ---------------- | :------: |
| `revenue`                  | 营业总收入       |    是    |
| `cost_of_revenue`          | 营业成本         |    是    |
| `tax_surcharge`            | 税金及附加       |   条件   |
| `selling_expense`          | 销售费用         |   条件   |
| `admin_expense`            | 管理费用         |   条件   |
| `rd_expense`               | 研发费用         |   条件   |
| `finance_expense`          | 财务费用         |   条件   |
| `interest_expense`         | 利息支出         |   条件   |
| `interest_income`          | 利息收入         |   条件   |
| `asset_impairment_loss`    | 资产减值损失     |   条件   |
| `credit_impairment_loss`   | 信用减值损失     |   条件   |
| `investment_income`        | 投资收益         |   条件   |
| `fair_value_change_income` | 公允价值变动收益 |   条件   |
| `asset_disposal_income`    | 资产处置收益     |   条件   |
| `other_income`             | 其他收益         |   条件   |
| `operating_profit`         | 营业利润         |    是    |
| `non_operating_income`     | 营业外收入       |    是    |
| `non_operating_expense`    | 营业外支出       |    是    |
| `total_profit`             | 利润总额         |    是    |
| `income_tax`               | 所得税费用       |    是    |
| `net_profit`               | 净利润           |    是    |

`interest_expense` 必须优先取附注的利息支出，不得无提示地把财务费用当作利息支出。确实只能使用财务费用代理时，在 `source_refs` 备注代理口径。

## 现金流量表 `cash_flow`

| 字段                                   | 中文名                                             | 完整报告 |
| -------------------------------------- | -------------------------------------------------- | :------: |
| `sales_cash_received`                  | 销售商品、提供劳务收到的现金                       |    是    |
| `fvtpl_disposal_cash_received`         | 处置公允价值计量且其变动计入当期损益               |   条件   |
| `interest_fee_commission_received`     | 收取利息、手续费及佣金的现金                       |   条件   |
| `net_increase_in_borrowing_funds`      | 拆入资金净增加额                                   |   条件   |
| `net_increase_in_repurchase_funds`     | 回购业务资金净增加额                               |   条件   |
| `tax_refunds_received`                 | 收到的税费返还                                     |   条件   |
| `other_operating_cash_received`        | 收到的其他与经营活动有关的现金                     |   条件   |
| `operating_cash_inflow`                | 经营活动现金流入小计                               |    是    |
| `purchases_cash_paid`                  | 购买商品、接受劳务支付的现金                       |   条件   |
| `employee_cash_paid`                   | 支付给职工以及为职工支付的现金                     |   条件   |
| `taxes_cash_paid`                      | 支付的各项税费                                     |   条件   |
| `other_operating_cash_paid`            | 支付的其他与经营活动有关的现金                     |   条件   |
| `operating_cash_outflow`               | 经营活动现金流出小计                               |    是    |
| `operating_cash_flow`                  | 经营活动产生的现金流量净额                         |    是    |
| `investment_recovered`                 | 收回投资收到的现金                                 |   条件   |
| `investment_income_cash_received`      | 取得投资收益收到的现金                             |   条件   |
| `subsidiary_acquisition_cash_received` | 取得子公司及其他营业单位所收到的现金净额           |   条件   |
| `asset_disposal_cash_received`         | 处置固定资产、无形资产和其他长期资产收回的现金净额 |   条件   |
| `subsidiary_disposal_cash_received`    | 处置子公司及其他营业单位收到的现金净额             |   条件   |
| `other_investing_cash_received`        | 收到的其他与投资活动有关的现金                     |   条件   |
| `investing_cash_inflow`                | 投资活动现金流入小计                               |    是    |
| `capital_expenditure`                  | 购建固定资产、无形资产和其他长期资产支付的现金     |   条件   |
| `investments_paid`                     | 投资支付的现金                                     |   条件   |
| `other_investing_cash_paid`            | 支付的其他与投资活动有关的现金                     |   条件   |
| `investing_cash_outflow`               | 投资活动现金流出小计                               |    是    |
| `investing_cash_flow`                  | 投资活动产生的现金流量净额                         |    是    |
| `capital_contributions_received`       | 吸收投资收到的现金                                 |   条件   |
| `borrowings_received`                  | 取得借款收到的现金                                 |   条件   |
| `bond_issuance_cash_received`          | 发行债券收到的现金                                 |   条件   |
| `other_financing_cash_received`        | 收到其他与筹资活动有关的现金                       |   条件   |
| `financing_cash_inflow`                | 筹资活动现金流入小计                               |    是    |
| `debt_repaid`                          | 偿还债务支付的现金                                 |   条件   |
| `interest_dividends_paid`              | 分配股利、利润或偿付利息支付的现金                 |   条件   |
| `other_financing_cash_paid`            | 支付的其他与筹资活动有关的现金                     |   条件   |
| `financing_cash_outflow`               | 筹资活动现金流出小计                               |    是    |
| `financing_cash_flow`                  | 筹资活动产生的现金流量净额                         |    是    |
| `exchange_effect`                      | 汇率变动对现金及现金等价物的影响                   |   条件   |
| `cash_change`                          | 现金及现金等价物净增加额                           |    是    |
| `cash_begin`                           | 期初现金及现金等价物余额                           |    是    |
| `cash_end`                             | 期末现金及现金等价物余额                           |    是    |

## 信贷补充数据 `financial_supplement`

金额字段沿用 `source_unit`：

- `restricted_cash`、`interest_bearing_debt`、`debt_due_within_one_year`。
- `overdue_receivables`、`receivables_over_one_year`、`aged_inventory`。
- `external_guarantees`、`related_party_occupancy`、`collateral_value`。
- `non_recurring_profit`、`adjusted_net_profit`、`purchases`。
- `depreciation_and_amortization`：折旧与摊销合计，仅从现金流量表补充资料、附注或明确披露中提取；不得由固定资产余额反推。
- `dividends_declared`、`retained_earnings_other_adjustments`。
- `requested_credit_amount`：本次申请金额；如需在报告正文引用，使用 `{{sup_requested_credit_amount}}`，不得写入自由文本元数据。

比例字段采用小数（例如 60% 写 `0.6`），脚本不会做金额单位换算：

- `top_five_receivables_ratio`、`receivables_over_one_year_ratio`。
- `related_party_receivables_ratio`、`finished_goods_inventory_ratio`。

`opening_financial_supplement` 用于平均有息债务等期初补充余额。

## 外部验证 `cross_validation`

金额使用 `table_units.cross_validation` 指定的来源单位，禁止默认沿用 `source_unit`：

- `vat_declared_revenue`：同期增值税申报收入。
- `bank_operating_inflows`：同期经营性银行进账/可核验销售回款。
- `taxable_income`、`income_tax_paid`。
- `utility_cost`、`payroll`、`social_security_base`。
- `business_registry_assets`：同口径工商年报资产。

每个值都要在 `source_refs` 记录期间、主体、口径和出处。

## 行业基准 `industry_benchmarks`

```json
{
  "classification": "国民经济行业分类/证监会/申万及层级",
  "as_of_period": "2025",
  "sources": [{ "name": "来源名称", "ref": "链接或页码", "sample": "样本口径" }],
  "metrics": {
    "gross_profit_margin": {
      "mean": 0.25,
      "median": 0.23,
      "excellent": 0.32,
      "weak": 0.16,
      "peer": 0.27
    },
    "gross_profit_margin_change": {
      "mean": 0.01,
      "std_dev": 0.02
    }
  }
}
```

可对标键见 `business-rules.md`。没有可靠数值来源时 `metrics` 写空对象，不允许模型推断。

## 抽取红线

1. 允许单位：元、千元、万元、百万元、亿元及带“人民币”前缀的同义值；不得省略单位或币种。
2. 缺失写 `null`；横杠只有确认代表零时才写 `0`。
3. 保留原始正负号，不执行换算、合计、相减或同比。
4. 不混用合并与母公司口径，不把不同会计期间强行比较。
5. 负值、零分母、亏损基期和最近一期是否可比均交给脚本处理。
6. 每个关键字段都要有 `source_refs`；公开增强字段还必须链接 `public_research.sources`，模型推断不能写入数值字段。
7. 比例字段采用 `0` 至 `1` 的小数；例如 60% 写 `0.6`，写 `60` 会被脚本拒绝。
8. 用户进件值优先；公开来源与其冲突时不得静默替换或平均。
9. 搜索摘要、媒体转述和无法定位的网页数字不得进入财务字段。
