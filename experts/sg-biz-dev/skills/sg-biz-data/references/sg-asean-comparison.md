# 新加坡 vs ASEAN 枢纽对比

> **核心规则**：不得将不同年份或不同统计口径的数据直接排名。每次输出必须注明 reference period 和 source。产业优势结论根据 FDI、行业产出、贸易和投资政策判断，不得固定写"新加坡=科技、马来西亚=制造"等永久标签。

---

## 1. 数据来源总览

### 1.1 跨国对比平台

| 数据源 | 类型 | 指标 | 链接 |
|--------|------|------|------|
| **ASEANstats Data Portal** | `[网页]` | 宏观、劳动、FDI、贸易（跨成员国统一口径） | https://data.aseanstats.org/ |
| **Enterprise SG Market Guides** | `[知识库]` | 东南亚各市场商业环境入口 | https://www.enterprisesg.gov.sg/grow-your-business/go-global/market-guides |

### 1.2 新加坡

| 指标 | 来源 | 链接 |
|------|------|------|
| 企业所得税 | IRAS | https://www.iras.gov.sg/quick-links/tax-rates/corporate-income-tax-rates |
| EP 门槛 | MOM | https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility |
| 工资 | MOM Stats | https://stats.mom.gov.sg/ |
| 商业租金 | URA | https://www.ura.gov.sg/property-data/commercial-properties/ |

### 1.3 马来西亚

| 指标 | 来源 | 链接 |
|------|------|------|
| 企业所得税 | Hasil (LHDN) | https://www.hasil.gov.my/en/company/tax-rate-of-company/ |
| EP 薪资政策 2026 | ESD | https://esd.imi.gov.my/portal/latest-news/announcement/announcement-266-ep-salary-policy-2026/ |
| 工资/经济数据 | DOSM | https://www.dosm.gov.my/portal-main/home |
| 房地产数据 | NAPIC | https://napic.jpph.gov.my/portal |

### 1.4 泰国

| 指标 | 来源 | 链接 |
|------|------|------|
| 企业所得税 | Revenue Department | https://www.rd.go.th/english/6044.html |
| 投资政策 | BOI | https://www.boi.go.th/en/index/ |
| LTR 长期签证 | BOI LTR | https://ltr.boi.go.th/ |
| 经济数据 | NSO | https://www.nso.go.th/nsoweb/index?set_lang=en |
| 房地产数据 | REIC | https://www.reic.or.th/ |

### 1.5 印度尼西亚

| 指标 | 来源 | 链接 |
|------|------|------|
| 投资政策 | BKPM | https://bkpm.go.id/ |
| 投资指南 PDF | BKPM | https://bkpm.go.id/storage/file/pdf/1683512273.pdf |
| 工资数据 | BPS | https://www.bps.go.id/en/statistics-table/2/NTgzIzI%3D/average-wages-net-salaries-of-labor-employee-per-month-by-province-and-main-job-type.html |

---

## 2. 对比维度

### 2.1 必须统一参考期的指标

| 维度 | 数据来源 | 注意 |
|------|----------|------|
| 企业所得税率 | 各国税务局官网 | 含 SME 优惠、免税期的需分开说明 |
| 外籍人才准入 | 各国移民局/BOI | 门槛金额、审批周期、家属权益分开对比 |
| 市场工资 | 各国统计局/MOM | 按行业和级别分层，不直接对比"平均工资" |
| 商业物业成本 | 各国房地产机构 | 区分 CBD/非 CBD、写字楼/工业/零售 |
| FDI 流入 | ASEANstats | 统一口径，可用 |
| 贸易规模 | ASEANstats | 统一口径，可用 |
| 产业结构 | SingStat/DOSM/NSO/BPS | 各国产业分类体系不同，不可直接映射 |

### 2.2 输出模板

```
【新加坡 vs {目标枢纽} 对比】

对比日期：{date}
参考期：{统一年份/季度}

| 维度 | 新加坡 | {对比枢纽} | 数据期 |
|------|--------|-----------|--------|
| 企业所得税 | X% (含SME Y%) | X% | 2026 |
| EP/外籍人门槛 | S$X/月 | RM/US$/THB X/月 | 2026 |
| CBD 写字楼月租 | S$X/sqft | X/sqft | QX 2026 |
| FDI 流入 | US$X Bn | US$X Bn | 2025 |
| 劳动力人口 | X M | X M | 2025 |

【产业优势对比（基于FDI+行业产出+投资政策）】
新加坡：{当前的优势行业，基于最新数据}
{对比枢纽}：{当前的优势行业}

【选择建议】
{基于用户行业、预算和团队规模的具体建议}

【数据来源】
各指标注明来源链接和查询日期
```

---

## 3. 关键规则

1. **不得固定标签**：产业优势随数据动态更新，不永久固化
2. **口径一致性**：ASEANstats 优先用于跨国比较（统一口径）
3. **时效性标注**：每个指标必须标注 reference period
4. **Hub Score**：可建立定性评分（税率优势/人才便利/成本竞争力/市场潜力/政策友好度），但每次标注评分依据和数据期
