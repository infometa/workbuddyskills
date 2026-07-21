# 第一年度成本估算模板（First-Year Cost Calculator）

> 每个成本项目必须保存：cost item / official source / official amount or range / reference date / market quote / contingency。

---

## 1. 数据来源

### 1.1 注册与合规费用

| 费用项 | 来源 | 类型 | 链接 |
|--------|------|------|------|
| 公司名称申请 | ACRA | `[网页]` | https://www.acra.gov.sg/manage/companies/service-transaction-fees/ |
| 公司注册 | ACRA | `[网页]` | $300 |
| 注册结构成本 | ACRA | `[网页]` | https://www.acra.gov.sg/register/business/choosing-business-structure/ |
| 公司秘书要求 | ACRA | `[网页]` | https://www.acra.gov.sg/register/business/registering-different-business-structures/local-company/appointing-company-directors-other-key-officers/ |
| 审计豁免条件 | ACRA | `[网页]` | https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/preparing-financial-statements/audit-exemptions/ |
| CSP 验证 | ACRA | `[网页]` | https://www.acra.gov.sg/resources/guides-forms/using-bizfiles-search-functions/ |

### 1.2 办公成本

| 费用项 | 来源 | 类型 | 链接 |
|--------|------|------|------|
| 办公室/商业租金 | URA | `[网页]` | https://www.ura.gov.sg/property-data/commercial-properties/ |
| 街道级商业租金统计 | URA | `[网页]` | https://eservice.ura.gov.sg/property-market-information/pmiCommercialRentalStatsByStreet |
| 工业物业租金/售价 | JTC | `[网页]` | https://stats.jtc.gov.sg/content/static/landing.html |

### 1.3 人员成本

| 费用项 | 来源 | 类型 | 链接 |
|--------|------|------|------|
| 薪资统计 | MOM | `[网页]` | https://stats.mom.gov.sg/ |
| 薪资对比工具 | MOM | `[网页]` | https://stats.mom.gov.sg/bt/Pages/salary-comparison-general-for-employer.aspx |
| EP 申请及费用 | MOM | `[网页]` | https://www.mom.gov.sg/passes-and-permits/employment-pass/apply-for-a-pass |
| CPF 缴费率 | CPF Board | `[网页]` | https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay |
| CPF Calculator | CPF Board | `[网页]` | https://www.cpf.gov.sg/employer/tools-and-services/calculators/cpf-contribution-calculator |

### 1.4 税务

| 费用项 | 来源 | 类型 | 链接 |
|--------|------|------|------|
| 企业所得税率 | IRAS | `[网页]` | https://www.iras.gov.sg/quick-links/tax-rates/corporate-income-tax-rates |
| GST 当前税率 | IRAS | `[网页]` | https://www.iras.gov.sg/taxes/goods-services-tax-%28gst%29/basics-of-gst/current-gst-rates |

---

## 2. 成本公式

```
第一年总成本 = 注册与设立
           + CSP / 公司秘书
           + 银行及支付
           + 办公室租金
           + 押金
           + 装修及设备
           + 人员工资
           + CPF
           + Work Pass
           + 招聘
           + 会计/税务
           + 审计（如适用）
           + 法律
           + 许可证
           + IT 基础设施
           + 市场拓展
           + 营运资金
           + 风险预留
```

---

## 3. 固定成本锚点（政府收费）

| 费用项 | 官方金额 | 来源 |
|--------|----------|------|
| 公司名称申请（Name Reservation） | **S$15** | ACRA |
| 公司注册（Incorporation） | **S$300** | ACRA |
| 公司秘书 | 注册后 6 个月内任命（非注册前） | ACRA |

> **秘书必须在注册后 6 个月内任命**，不是注册前必完成步骤。

---

## 4. 动态成本（需读取官方页面）

| 费用项 | 数据源 | 读取方式 | 备注 |
|--------|--------|----------|------|
| 办公室租金 | URA / JTC | 按地区、物业类型、面积查询最新 psf 月租区间 | 带 reference date |
| 人员薪资 | MOM Salary Comparison | 按职业、行业、年龄查询中位数/P25/P75 | 与 EP 门槛分开 |
| CPF | CPF Calculator | 按年龄、PR 年份、薪资计算 | 仅本地公民/PR |
| Work Pass 费用 | MOM EP Apply | 按准证类型查询申请费和 issuance fee | 区分一次性/续期 |
| 企业所得税 | IRAS | 当前税率 + 部分免税计划（PTE） | 新公司前三年 SUTE |
| GST | IRAS | 当前税率 | 年营业额 >S$1M 需注册 |

---

## 5. 市场报价保留项（不编造）

以下成本项**没有统一官方市场价**，保留"实际报价"字段：

| 费用项 | 处理规则 |
|--------|----------|
| CSP / 公司秘书 | 至少获取 3 家供应商报价后才能生成市场区间 |
| 银行开户及交易费 | 见 `sg-business-operations.md` §1.4 费率双层机制 |
| 装修及设备 | 按办公室面积 × 行业经验区间（注明来源） |
| 会计/税务外包 | 至少 3 家报价 |
| 审计 | 先检查 ACRA Audit Exemption 条件 |
| 法律服务 | 至少 3 家报价（含本地律所和中资律所） |
| IT 基础设施 | 按员工数估算（云服务、宽带、硬件） |
| 招聘费 | 内部招聘 vs 猎头（EA 服务费通常为首月薪资的 15-25%） |
| 市场拓展 | MRA Grant 可覆盖最高 70%（本地 SME，2026-04-01 起） |

---

## 6. 输出模板

```
【第一年成本估算】

企业类型：{Private Limited / Branch}
计划团队规模：{N}人（{本地/N}，{EP/N}）
办公室类型：{Serviced Office / Traditional Lease}
地区：{CBD / City Fringe / Outside Central}

| 编号 | 成本项 | 官方金额/区间 | 实际报价 | 参考期 | 来源 |
|------|--------|-------------|---------|--------|------|
| 1 | Name Reservation | S$15 | — | 2026 | ACRA |
| 2 | Incorporation | S$300 | — | 2026 | ACRA |
| ... | ... | ... | ... | ... | ... |

合计：
  - 政府固定收费：S$X
  - 动态官方数据：S$X (区间: S$X-Y)
  - 市场报价：S$X（待供应商报价）
  - 总估算：S$X

contingency: +{15-20%}

【数据来源与局限性】
政府收费为固定金额；租金/薪资/MOM 数据已注明参考期和来源；
装修/秘书/会计/法律等地保留"实际报价"字段，未编造区间。
```
