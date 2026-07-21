# 政府资助结构化速查矩阵（Grant Matching Engine）

> 不人工维护固定三行表。基于 GoBusiness Grants Portal 和 Enterprise Singapore 官方页面动态匹配。

---

## 1. 数据来源

### 1.1 统一入口

| 资源 | 类型 | 链接 |
|------|------|------|
| GoBusiness Grants 总入口 | `[网页]` | https://grants.gobusiness.gov.sg/ |
| Grants & Support Directory | `[网页]` | https://grants.gobusiness.gov.sg/support-directory |
| Government Assistance e-Adviser | `[网页]` | https://grants.gobusiness.gov.sg/budget-announcement-for-businesses |
| Business Grants Portal (BGP) | `[网页]` | https://www.businessgrants.gov.sg/ |
| Enterprise Singapore Financial Support | `[网页]` | https://www.enterprisesg.gov.sg/financial-support |

### 1.2 主要资助计划

| 计划 | 类型 | 链接 |
|------|------|------|
| Startup SG Founder | `[网页]` | https://www.startupsg.gov.sg/programmes/4894/startup-sg-founder |
| Enterprise Development Grant (EDG) | `[网页]` | https://www.enterprisesg.gov.sg/financial-support/enterprise-development-grant |
| Market Readiness Assistance (MRA) | `[网页]` | https://www.enterprisesg.gov.sg/financial-support/market-readiness-assistance-grant |
| Productivity Solutions Grant (PSG) | `[网页]` | https://www.enterprisesg.gov.sg/financial-support/productivity-solutions-grant |
| Energy Efficiency Grant | `[网页]` | https://www.enterprisesg.gov.sg/financial-support/energy-efficiency-grant |
| Enterprise Financing Scheme | `[网页]` | https://www.enterprisesg.gov.sg/financial-support/enterprise-financing-scheme |
| Budget 2026 / EDGE 更新 | `[网页]` | https://www.enterprisesg.gov.sg/campaigns/budget-2026 |

---

## 2. 动态匹配逻辑

### 2.1 输入画像

| 参数 | 选项 |
|------|------|
| 注册地 | Singapore / Foreign |
| 成立时间 | < 1年 / 1-3年 / > 3年 |
| 本地股权比例 | ≥30% / <30% |
| 集团收入 | < S$100M / S$100M-500M / > S$500M |
| 员工数 | < 10 / 10-50 / 50-200 / > 200 |
| 行业 | SSIC 代码 |
| 企业阶段 | 初创 / 增长 / 国际化 / 转型 |
| 项目目标 | 创新/R&D / 国际化 / 数字化转型 / 节能 / 融资 / 技能培训 |
| 目标市场 | 新加坡 / ASEAN / 中国 / 全球 |
| 预计项目费用 | S$X |

### 2.2 输出格式

```
【资助匹配结果】
查询日期：{date}
画像：{注册地/阶段/行业/目标市场/预计费用}

匹配方案1：{计划名称}
  - 支持范围：{scope}
  - 支持比例：{rate}%（注明是否为 SME 优惠率）
  - 上限：S${cap}
  - 资格条件：{eligibility}
  - 申请入口：{portal/link}
  - 来源日期：{source date}
  - 置信度：{高/中/低（如计划细节可能随 Budget 更新）}

匹配方案2：...
```

---

## 3. 当前参考数据

> ⚠️ 以下数据来自官方页面截至当前。不得固化——每次查询以官方最新页面为准。

| 计划 | 支持比例 | 资助额/Cap | 关键条件 | 当前状态 |
|------|----------|-----------|----------|----------|
| **Startup SG Founder** | 1:1 | S$20,000-S$50,000 | 首次创业者、新加坡注册 | 有效 |
| **EDG** | 本地 SME 一般最高 50% | 按项目 | 新加坡注册、有实质业务、SME | 有效（EDGE 整合中） |
| **MRA** | 本地 SME 最高 70%（2026-04-01 起） | 按项目 | 中小企业海外拓展 | 有效（EDGE 整合中） |
| **PSG** | 视方案 | 视方案 | SME 技术升级/数字化 | 有效（EDGE 整合中） |
| **Energy Efficiency Grant** | 视方案 | 视方案 | 节能项目 | 有效 |
| **Enterprise Financing Scheme** | N/A（贷款） | 视方案 | 新加坡注册 | 有效 |

### 3.1 EDGE 计划说明

> **EDGE 计划整合 EDG、MRA 和 PSG**。官方仍说明 EDGE 上线前企业可继续申请现有三项计划。不得提前固化 EDGE 的资助比例——等待官方正式发布。

| 资源 | 类型 | 链接 |
|------|------|------|
| Budget 2026 EDGE 更新 | `[网页]` | https://www.enterprisesg.gov.sg/campaigns/budget-2026 |

---

## 4. 匹配规则

1. **只能匹配官方页面当前公布的 eligibility 条件**
2. **比例和上限以官网最新版本为准**
3. **标注 source date 和 confidence**
4. **如某个条件不确定，标记为"需网页验证"并提示用户自行确认**
5. **EDGE 正式参数发布前，引用现有三项计划并注明"将被整合"**
