# 竞争格局分析框架

> 使用 SingStat I-O Tables/BITE/Industry Data 分析行业结构，CCS 并购框架判断集中度。不直接计算 HHI/CR4（无企业收入数据时不可行）。

---

## 1. 数据来源

| 数据源 | 类型 | 用途 | 链接 |
|--------|------|------|------|
| SingStat I-O Tables 2023 | `[知识库]` | 行业上下游依赖、投入产出结构 | https://www.singstat.gov.sg/publication-resources/supply-use-and-input-output-tables-2023-infographic |
| I-O 方法说明 | `[知识库]` | 投入产出表解读 | https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/supply-use-and-input-output-tables/our-data-explained |
| SingStat Industry Data | `[网页]` | 行业规模、企业经营指标、趋势 | https://www.singstat.gov.sg/find-data/explore-data-themes/industry |
| BITE | `[网页]` | 企业表现、行业洞察（交互式） | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite |
| CCS Mergers & Acquisitions | `[网页]` | 并购竞争审查框架 | https://www.cccs.gov.sg/anti-competitive-practices/mergers-and-acquisitions |
| CCS Competition Guidelines | `[知识库]` | Competition Act 详细指南 | https://www.cccs.gov.sg/anti-competitive-practices/legislation-and-guidelines/competition-act-and-guidelines |
| SBF Research Reports | `[知识库]` | 企业调查、行业报告 | https://www.sbf.org.sg/what-we-do/advocacy-policy/sbf-research-reports |
| CEA 中资企业年度报告 | `[知识库]` | 中资企业在新加坡的行业分布和经营情况 | https://cea.org.sg/wp-content/uploads/2025/12/2025新加坡中资企业年度发展报告_中英文版_R2_电子版.pdf |

---

## 2. Porter's Five Forces 分析模板

| Force | 数据来源 | 分析指标 |
|-------|----------|----------|
| **新进入者威胁** | ACRA 企业数据（新注册量趋势）、EDB 招商政策 | 目标 SSIC 企业增长率、capital 门槛、牌照要求 |
| **供应商议价力** | I-O Tables（上游行业集中度）、SBF 调查 | 上游行业企业数量、投入品可替代性 |
| **买方议价力** | I-O Tables（下游行业结构）、BITE 客户行业数据 | 下游行业企业数量、集中度、采购规模 |
| **替代品威胁** | BITE 行业数据、技术趋势 | 替代技术/产品的新企业注册信号 |
| **现有竞争** | ACRA 企业数量、CCS 集中度框架、GeBIZ 中标份额 | 企业数量、存活率、政府项目竞争格局 |

---

## 3. 代理指标（无企业收入数据时使用）

> ⚠️ **I-O Tables 和 BITE 不能直接计算真实 HHI 或 CR4 企业集中度。**

| 代理指标 | 数据来源 | 含义 |
|----------|----------|------|
| 目标 SSIC 企业数量 | data.gov.sg | 竞争密度 |
| 企业净增率（新注册-注销/退市） | SingStat Monthly | 行业活力/饱和度 |
| GeBIZ 中标企业数量 vs 投标企业数量 | GeBIZ Awarded Results | 政府采购竞争程度 |
| CEA 报告中的中资企业行业分布 | CEA 年度报告 | 中国竞争者的密度 |
| SBF 调查中的行业信心指数 | SBF Research Reports | 企业主观预期 |

### CCS 竞争关注参考框架

CCS 官方并购框架中的参考情形（用于定性判断，非硬性划线）：
- 单一实体市场份额 ≥ 40%
- 前三大企业合计 ≥ 70%，且单一实体在 20%-40% 区间

> **注意**：没有实际市场份额数据时，这些阈值只能作为理论参考框架，不能作为确定性的竞争判断结论。

---

## 4. 中国企业优势/劣势矩阵（模板）

> **规则**：人工建立模板，数据从 SingStat、CCS、SBF 和 CEA 动态填充。

| 维度 | 中国企业典型优势 | 中国企业典型劣势 | 应对策略 |
|------|-----------------|-----------------|----------|
| 成本结构 | 制造成本优势 | 新加坡本地运营成本高 | 保留中国制造，新加坡做销售/服务 |
| 技术能力 | 特定领域技术领先（如5G、AI、光伏） | 本地客户对"中国技术"的信任需时间建立 | 获取行业认证、参加新加坡展会、POC |
| 品牌认知 | 产品性价比优势 | 在新加坡 B2B 市场品牌知名度低 | 从价格敏感型客户切入，逐步建立案例 |
| 政府关系 | 中国驻新经商处/CEA 网络 | 对新加坡政府流程不熟悉 | 通过 EDB/Enterprise SG 正式渠道进入 |
| 人才储备 | 中国工程师成本相对低 | 新加坡本地招聘难度和成本 | 先用 EP 派遣核心团队，逐步本地化 |
| 生态资源 | 中国供应链深度整合 | 新加坡本地合作伙伴关系薄弱 | 通过 SLA/SBF 协会网络建立合作 |

数据填充来源：ACRA 行业数据 + SingStat Industry + SBF 调查报告 + CEA 年度报告。

---

## 5. 输出模板

```
【竞争格局分析】

行业：{SSIC 代码 + 描述}
分析日期：{date}

1. 行业结构
   - 企业数量：{ACRA count}（活跃 / 总注册）
   - 增长率：{YoY %}（SingStat Monthly）
   - 上下游依赖：{I-O Tables 关键投入/产出行业}

2. 竞争态势（五力）
   - 新进入者威胁：{高/中/低}
   - 供应商议价力：{高/中/低}
   - 买方议价力：{高/中/低}
   - 替代品威胁：{高/中/低}
   - 现有竞争强度：{高/中/低}

3. 中国企业定位
   - 核心优势：{3-5 条}
   - 核心劣势：{3-5 条}
   - 推荐进入策略：{差异化/成本领先/聚焦}

【数据来源】
{列出各指标的具体数据源和查询日期}

【⚠️ 局限性声明】
未获取企业收入/市场份额数据时，竞争集中度结论为代理指标推断，非精确 HHI。
```
