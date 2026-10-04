# 财务分析进件材料路由

完整材料要求、时间窗和缺口处理见 `intake-requirements.md`。

| docType                  | 材料                                 | 用途                                       |
| ------------------------ | ------------------------------------ | ------------------------------------------ |
| `audit_report`           | 完整审计报告、审计意见和附注         | 三表、会计政策、合并范围、科目明细         |
| `annual_report`          | 最近三年年报/年度财务资料            | 行业、业务、分部、历史趋势                 |
| `financial_statements`   | 最近三年、最近一期、上年同期盖章三表 | 财务简表和指标计算                         |
| `trial_balance`          | 科目余额表、总账和明细账             | 异动、勾稽和科目真实性                     |
| `tax_filing`             | 增值税/所得税申报、完税凭证          | 收入和利润交叉验证                         |
| `invoice_data`           | 销项/进项发票明细                    | 收入、采购和交易真实性                     |
| `bank_statement`         | 同期全部主要经营账户流水             | 回款率、收入和现金验证                     |
| `receivable_detail`      | 应收账龄、前五客户、关联方应收       | 回款质量和集中度                           |
| `inventory_detail`       | 分类、库龄、盘点、减值               | 存货质量和变现能力                         |
| `debt_schedule`          | 借款、租赁、利息、到期和担保清单     | 偿债压力、期限和融资成本                   |
| `credit_application`     | 授信用途、金额、期限、还款安排       | 融资需求与经营周期匹配                     |
| `industry_benchmark`     | Wind/iFinD、协会、研报、可比公司     | 有来源的行业对标                           |
| `public_filing`          | 交易所、监管机构或企业官网公开公告   | 重大异动、担保、关联交易和公开附注补充     |
| `public_industry_source` | 政府统计、行业协会、授权数据库       | 行业趋势和基准                             |
| `public_context`         | 可信研究资料或媒体线索               | 仅作背景或定位原始来源，不进入公司数值字段 |

每份材料同时标记 `source_origin`：`provided`、`existing-public-file` 或 `public-research`。联网新增文件必须关联 `public_research.sources[].source_id`、本地文件和 SHA-256；`public_context` 不得作为财务数值来源，`public-research` 也不得登记为银行流水、税表、发票底账、内部台账或授信方案。
