# 新加坡运营数据参考（签证、税务、薪资、租金）

> **核心规则**：所有具体数值必须实时回查官方来源。不得输出无来源的"行业平均"值。不得将"知道网址"表述为"可以调用数据源"。

---

## 1. 工作准证与签证

### 1.1 EP 就业准证（Employment Pass）

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| EP 薪资门槛（最新） | `[网页]` MOM | https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility |
| COMPASS 评分框架 | `[网页]` MOM | https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility |

> ⚠️ **规则**：
> - EP 最低薪资门槛按年龄和行业分层，实时数值以 MOM 官网为准
> - 工作准证最低工资与市场招聘薪资必须分开表述
> - 不得在语料库中静态存储 EP 门槛数值（如 S$5,000/S$5,500/S$10,500 等已过时）

### 1.2 S Pass

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| S Pass 资格条件 | `[网页]` MOM | https://www.mom.gov.sg/passes-and-permits/s-pass/eligibility |

### 1.3 LQS 本地合格薪资

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| Local Qualifying Salary | `[网页]` MOM | https://www.mom.gov.sg/employment-practices/progressive-wage-model/local-qualifying-salary |

---

## 2. 税收

### 2.1 企业所得税

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| 企业所得税税率 | `[网页]` IRAS | https://www.iras.gov.sg/quick-links/tax-rates/corporate-income-tax-rates |

> ⚠️ **规则**：部分免税计划（PTE）、新公司免税计划（SUTE）等减免规则以 IRAS 官网当前版本为准。

### 2.2 GST（消费税/增值税）

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| GST 当前税率 | `[网页]` IRAS | https://www.iras.gov.sg/taxes/goods-services-tax-%28gst%29/basics-of-gst/current-gst-rates |

### 2.3 预扣税与中新协定

| 数据项 | 接入方式 | 说明 |
|--------|----------|------|
| Withholding Tax | `[网页]` IRAS | 特许权使用费、利息、技术服务费等税率以 IRAS 为准 |
| 中新 DTA | `[知识库]` | 消除双重征税协定，IRAS 官网可查 |

---

## 3. 商业与工业物业租金

### 3.1 商业物业（办公室/商铺）

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| 商用物业租金/售价 | `[网页]` URA | https://www.ura.gov.sg/property-data/commercial-properties/ |

> ⚠️ **规则**：
> - 租金必须说明物业类型（如 Grade A Office / Retail）、地区（如 Raffles Place / CBD Fringe / Outside Central Region）和参考期（如 Q1 2026）
> - 不得输出无来源的统一"新加坡平均租金"

### 3.2 工业物业（厂房/仓库/工业用地）

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| 工业物业统计 | `[网页]` JTC | https://stats.jtc.gov.sg/content/static/landing.html |

> JTC 提供按物业类型（Standard Factory / Flatted Factory / Warehouse / Land）和区域细分的租金及售价数据。

---

## 4. 市场薪资

### 4.1 薪资对比工具

| 数据项 | 接入方式 | 官方链接 |
|--------|----------|----------|
| 薪资对比（按职业/行业/年龄） | `[网页]` MOM | https://stats.mom.gov.sg/bt/Pages/salary-comparison-general-for-employer.aspx |

> ⚠️ **规则**：
> - 市场薪资数据与 EP/S Pass 最低门槛是两个独立的参考标准
> - 市场薪资用于判断"该岗位的市场竞争力"
> - EP/S Pass 门槛用于判断"是否可以申请工作准证"
> - 两者必须分开表述，不得混为一谈

---

## 5. 使用决策

| 用户问题 | 应回查 | 不应 |
|----------|--------|------|
| "EP 薪资门槛是多少？" | 实时访问 MOM Eligibility | 不要输出语料库中存储的历史数值 |
| "新加坡办公室租金大概多少钱？" | 先问地区/类型/参考期，再查 URA | 不要输出"新加坡平均月租约 S$X/sqft" |
| "GST 现在多少？" | 实时访问 IRAS | 不要输出记忆中的税率 |
| "这个岗位市场薪资多少？" | MOM 薪资对比工具 | 不要输出 EP 门槛数字 |
