# Risa 知识库索引 — 参考书籍与权威报告库

> 生成日期：2026-06-25
> 用途：为 Risa BD Mode（市场拓客）与 DD Mode（尽职调查）提供宏观定性分析底库
> 铁律：若读取到 PDF 内的图表或非结构化数据，强制进行 OCR 识别，提取文字核心结论

---

## 一、MIDA：马来西亚投资发展局

### 1.1 Costs of Doing Business in Malaysia (CODB)

| 属性 | 值 |
|------|-----|
| 发布机构 | MIDA (Malaysian Investment Development Authority) |
| 最新版本 | CODB 2024 (发布于 2025-03) |
| PDF 直链 | https://www.mida.gov.my/wp-content/uploads/2025/03/CODB_ENG_2024-FINAL.pdf |
| 官网页面 | https://www.mida.gov.my/publications/costs-of-doing-business-in-malaysia/ |
| 语言 | 英语 |
| 关键内容 | 人工成本（按行业/技能）、水电费率、工业用地/厂房租金、物流运输成本、税务激励概览 |

**Risa 使用场景**：
- BD Mode Phase BD-2：当用户询问"马来西亚制造业设厂成本"时，从本文提取最新人工/水电/土地基准价格
- DD Mode Phase DD-5：作为企业运营成本合理性校验的基准线

**OCR 触发条件**：报告中包含大量表格（薪资表、水电费率表）——必须 OCR 提取数值

---

### 1.2 PwC Doing Business in Malaysia 2025

| 属性 | 值 |
|------|-----|
| 发布机构 | PwC Malaysia |
| PDF 直链 | https://www.pwc.com/my/en/assets/publications/2025/doing-business-in-malaysia-2025.pdf |
| 补充价值 | 税务体系详解、外资准入政策、公司设立流程 |

---

## 二、BNM：马来西亚国家银行

### 2.1 BNM Annual Report 2025

| 属性 | 值 |
|------|-----|
| 发布机构 | Bank Negara Malaysia |
| 发布日期 | 2026-03-31 |
| PDF 直链 | https://www.investmalaysia.gov.my/media/1uun2pd4/bank-negara-malaysia-annual-report-2025.pdf |
| 备用链接 | https://www.acccimserc.com/images/researchpdf/2026/20260331%20BNM%20Annual%20Report%202025.pdf |
| 关键内容 | 全年经济回顾、货币政策决策逻辑、金融体系稳定性评估、行业信贷质量分析 |

**Risa 使用场景**：
- BD Mode Phase BD-1：GDP 增速、通胀、货币政策方向——用于宏观环境破冰
- DD Mode Phase DD-5：银行贷款行业分布、不良贷款率——可作为行业信用风险基准

---

### 2.2 BNM Economic and Monetary Review 2025

| 属性 | 值 |
|------|-----|
| PDF 直链 | https://www.investmalaysia.gov.my/media/c42pvntg/bank-negara-malaysia-economic-and-monetary-review-2025.pdf |
| 关键内容 | 各行业增长深度分析、劳动力市场、通胀驱动因素、外部部门详细数据 |

---

### 2.3 BNM Financial Stability Review (Second Half 2025)

| 属性 | 值 |
|------|-----|
| 关键内容 | 银行业压力测试、家庭债务、企业杠杆率、房地产市场风险 |

**OCR 触发条件**：BNM 报告中图表密集（GDP 增长图、行业贡献率饼图、信贷质量矩阵）——强制 OCR

---

## 三、World Bank：世界银行

### 3.1 Malaysia Economic Monitor (最新版)

| 属性 | 值 |
|------|-----|
| 发布机构 | World Bank |
| 最新版本 | October 2025 Edition |
| PDF 直链 | https://openknowledge.worldbank.org/bitstreams/39e33781-ca7f-4f11-90e9-462364f00077/download |
| 官网汇总页 | https://www.worldbank.org/en/country/malaysia/publication/malaysia-economic-monitor-reports |
| 关键内容 | 马来西亚宏观经济展望（4.1% 增长）、财政改革进展、结构性挑战、行业专题分析 |

**Risa 使用场景**：
- BD Mode Phase BD-1：作为宏观定性判断的国际第三方背书
- DD Mode Phase DD-7：世界银行对马来西亚制度/治理的评价可用于 ESG 模块

---

## 四、补充权威数据源（备用链接库）

### 4.1 马来西亚财政部 — 2026 经济展望

| 属性 | 值 |
|------|-----|
| PDF | https://belanjawan.mof.gov.my/pdf/belanjawan2026/economy/economic-2026.pdf |
| 内容 | 2026 年国家预算案、财政政策方向、各行业预期增长率 |

### 4.2 MATRADE — 出口商名录（Web）

| 属性 | 值 |
|------|-----|
| 官网 | https://www.matrade.gov.my/en/malaysian-exporters |
| 搜索入口 | https://www.matrade.gov.my/en/malaysian-exporters/services-for-exporters/exporters-directory |

### 4.3 Halal Malaysia Portal

| 属性 | 值 |
|------|-----|
| 官网 | https://www.halal.gov.my/v4/ |
| 清真认证查询 | https://www.halal.gov.my/v4/halal-certified-directory/ |

### 4.4 MyIPO — 知识产权查询

| 属性 | 值 |
|------|-----|
| 官网 | https://www.myipo.gov.my/ |
| 专利搜索 | https://iponline.myipo.gov.my/iponline/ |
| 商标搜索 | https://iponline.myipo.gov.my/iponline/trademark/ |

---

## 五、Risa 报告引用规范

在 BD/DD 报告中使用上述来源时，必须标注：

```
📚 【权威报告引用】来源：<机构>《<报告名>》(YYYY)
   链接：<URL>
   核心结论：<一句话总结>
   提取方式：<直接文本 / OCR 提取>
```

**OCR 铁律**：任何 PDF 中的图表（GDP 趋势图、行业饼图、成本对比表）只要无法直接提取文本，必须执行 OCR 识别。Risa 不生产幻觉，只传递结构化事实。
