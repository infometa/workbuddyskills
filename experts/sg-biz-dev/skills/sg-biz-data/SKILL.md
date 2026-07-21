---
name: sg-biz-data
description: "Singapore business development data sources and API reference — government open data, company registry, industrial parks, exhibitions, investment policies, and market entry resources."
---

# 新加坡商务拓展数据源（sg-biz-data）

本 Skill 为"新加坡商务拓展专家"提供数据支撑，整合新加坡各级政府及公共机构的公开 API、数据库和商务资源索引。

---

## 数据源能力层级（必读）

所有资源按可接入方式分为四类。**不得将"已录入网址"表述为"可以调用数据源"**：

| 层级 | 标注 | 含义 | 示例 |
|------|------|------|------|
| 🔵 **知识库/RAG** | `[知识库]` | URL 已录入，内容可供检索，但无法实时调用 | data.gov.sg 企业集合页面、CEA 会员名录 |
| 🟢 **API** | `[API]` | 可通过 REST/HTTP API 实时查询结构化数据 | data.gov.sg v1 Datastore API、SingStat Developer API |
| 🟣 **MCP** | `[MCP]` | 已配置 MCP connector，可在 WorkBuddy 中直接调用 | SingStat MCP（需实际连接测试） |
| 🟡 **网页交互** | `[网页]` | 需手动访问网页进行交互式查询，无法通过 API 自动获取 | SFA ADOS、BITE、CEA 会员专区 |

> **汇报规则**：模型每次汇报数据能力时，必须分别说明"已录入知识库""可实时 API 查询""已连接 MCP""需要网页交互"。

---

## 数据源分类

### 一、企业发现与商业网络

#### 1.1 企业基础数据库 — ACRA Open Data & data.gov.sg

> **[API]** data.gov.sg v1 Datastore API 可直接查询结构化企业记录（已验证可用）。
> **[知识库]** ACRA Open Data、SSIC 2025 等页面已录入。

在寻找本地客户、供应商、合作伙伴、渠道商和代理商时，优先使用 data.gov.sg 企业实体 API。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| **data.gov.sg 企业集合 Collection 2** | `[API]` | 27 个 CSV 数据集，按月更新，57000+ 记录/字母 | https://data.gov.sg/collections/2/view |
| **Collection 2 Metadata API** | `[API]` | 集合元数据（数据集列表、更新日期） | `GET https://api-production.data.gov.sg/v2/public/api/collections/2/metadata` |
| **Datastore Search API** | `[API]` | 实时查询企业数据，支持过滤（已验证） | `GET https://data.gov.sg/api/action/datastore_search?resource_id=<dataset_id>&limit=5` |
| **Dataset API 说明** | `[知识库]` | 搜索与过滤文档 | https://guide.data.gov.sg/developer-guide/dataset-apis/search-and-filter-within-dataset |
| **ACRA Open Data Initiative** | `[知识库]` | ACRA 开放数据计划 | https://www.acra.gov.sg/resources/open-data-initiative/ |
| **ACRA API Marketplace** | `[API]` | 收费 API，企业详细信息 | https://www.acra.gov.sg/resources/eservice-tools-portals/api-marketplace/ |
| **SSIC 2025** | `[知识库]` | 行业分类代码，自然语言→代码映射 | https://www.singstat.gov.sg/standard-classifications/national-classifications/singapore-standard-industrial-classification-ssic |

> **已验证查询示例**：`data.gov.sg/api/action/datastore_search?resource_id=d_af2042c77ffaf0db5d75561ce9ef5688&limit=5&filters={"entity_status_description":["Live Company"]}` → 返回 UEN、entity_name、entity_status_description、primary_ssic_code 等字段。
>
> **策略提示**：结合 SSIC 2025 将用户的自然语言行业需求映射到新加坡官方行业分类后，用 Datastore Search API 筛选目标企业。

#### 1.2 新加坡工商总会 — SBF

> `[网页]` SBF 会员目录为公开网页目录，需手动访问。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| SBF 官网 | `[知识库]` | 工商联合总会 | https://www.sbf.org.sg/ |
| SBF Members' Directory | `[网页]` | 企业会员目录（可搜索） | https://members.sbf.org.sg/membershipdirectory |
| SBF Trade Associations & Chambers | `[知识库]` | 下属行业协会与商会网络 | https://www.sbf.org.sg/membership-tacs/tacs |
| New SBF Members 2025 PDF | `[知识库]` | 新入会企业名单（商业网络信号） | https://www.sbf.org.sg/docs/default-source/membership/members-orientation/%28for-networking%29---members%27-directory---02-april-2025.pdf |

#### 1.3 中华总商会 — SCCCI

> `[网页]` SCCCI 企业会员目录需网页交互查询。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| SCCCI 官网 | `[知识库]` | 中华总商会 | https://www.sccci.org.sg/ |
| Corporate Members Directory | `[网页]` | 企业会员目录 | https://www.sccci.org.sg/corporate-members-directory |
| Trade Association Members | `[网页]` | 下属行业协会目录 | https://www.sccci.org.sg/ta-members-directory |
| SCCCI Membership | `[知识库]` | 会员申请入口 | https://www.sccci.org.sg/membership-application |

#### 1.4 中资企业协会 — CEA

> `[网页]` CEA 会员专区为动态网页 + RSS Feed。**不存在**公开的 2021 年后完整会员名录。

**CEA 会员识别规则（三级分类）**：

| 标记级别 | 条件 | 示例 |
|----------|------|------|
| **CEA 会员** | CEA 明确表述为"新会员、会员单位或会员名录"的企业 | 2023年10月 15 家新会员、2025年1-4月新会员（中企通讯第2期） |
| **CEA 公开资料出现企业** | 仅出现在活动、调研或年度报告中的企业，不得自动认定为会员 | 南华新加坡、天合光能、中国电信 |
| **疑似中资企业** | 中文名称疑似中资但未经 CEA/官方资料验证 |

**增量会员数据库**：
- 基准：2021 会员名录（`[知识库]`，仅作历史基准）
- 增量1：2023年10月 15 家新会员名单 → https://cea.org.sg/协会动态-新入会会员名单/
  - ⚠️ 页面含二维码名单，未直接列出企业名
- 增量2：中企通讯 2025年第2期 "2025年1—4月新会员名单" → https://cea.org.sg/wp-content/uploads/2025/06/中企通讯_2025-第二期-电子版.pdf
  - ⚠️ PDF 为二进制压缩，WebFetch 无法直接提取文本
- 持续追踪：CEA 会员动态 RSS → https://cea.org.sg/category/会员专区/会员动态/feed/

| 数据源 | 类型 | 说明 |
|--------|------|------|
| CEA 官网 | `[知识库]` | 中资企业（新加坡）协会 | https://cea.org.sg/ |
| CEA 会员专区 | `[网页]` | 会员企业最新动态 | https://cea.org.sg/category/会员专区/ |
| CEA 会员动态 RSS | `[知识库]` | **已验证可用**，RSS Feed 定期更新 | https://cea.org.sg/category/会员专区/会员动态/feed/ |
| 新入会会员名单 | `[知识库]` | 2023年10月 15 家新会员（含二维码名单） | https://cea.org.sg/协会动态-新入会会员名单/ |
| 会员名录 2021 | `[知识库]` | **仅作历史基准**，不代表当前状态 | https://cea.org.sg/《中资企业（新加坡）协会会员名录2021年版》正式/ |

#### 1.5 CEA 年度发展报告（案例语料）

> `[知识库]` PDF 报告，用于训练"中国企业→新加坡市场进入"模式。

| 报告 | 类型 | 链接 |
|------|------|------|
| 2024-2025 年度报告 PDF（中英） | `[知识库]` | https://cea.org.sg/wp-content/uploads/2025/12/2025新加坡中资企业年度发展报告_中英文版_R2_电子版.pdf |
| 2023-2024 年度报告 PDF（中英） | `[知识库]` | https://cea.org.sg/wp-content/uploads/2025/03/《2024新加坡中资企业年度发展报告》-中英文-电子版.pdf |

> **注意**：这些报告来自 CEA 及其合作研究团队，应作为案例语料而不是实时企业经营数据库使用。

#### 1.6 CEA 中企通讯

> `[知识库]` PDF 下载。第三期已确认上线（2025-11-04），完整 PDF 待恢复。

**⚠️ 重要**：第三期发布页"阅读全文"链接当前指向第2期 PDF，**不得**将其作为第3期文件使用。

| 期数 | 类型 | 状态 | 链接 |
|------|------|------|------|
| 2025年 第1期 | `[知识库]` | ✅ PDF 可用 | https://cea.org.sg/wp-content/uploads/2025/03/中企通讯_2025-第一期-电子版.pdf |
| 2025年 第2期 | `[知识库]` | ✅ PDF 可用 | https://cea.org.sg/wp-content/uploads/2025/06/中企通讯_2025-第二期-电子版.pdf |
| 2025年 第3期 发布页 | `[知识库]` | ⚠️ 官方发布已确认、完整 PDF 待恢复 | https://cea.org.sg/会员动态-《中企通讯》2025年第三期正式上线发布/ |
| CEA 会员动态 RSS | `[知识库]` | ✅ 可读取，用于持续追踪企业动态 | https://cea.org.sg/category/会员专区/会员动态/feed/ |

> **处理规则**：第3期当前标记为"官方发布已确认、完整PDF待恢复"；不得把第2期PDF误标为第3期。优先使用会员动态 RSS 更新流补充企业动态。

#### 1.7 初创企业与科技生态 — Startup SG

> `[网页]` Startup Directory 为网页浏览目录。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| Startup SG | `[知识库]` | 新加坡初创生态门户 | https://www.startupsg.gov.sg/ |
| Startup Directory | `[网页]` | 初创企业目录（公开 Profile） | https://frontend.startupsg.gov.sg/directory/startups/ |

---

### 二、行业监管目录与持牌企业

#### 2.1 金融机构 — MAS Directory

> `[网页]` MAS FID 为网页搜索目录，非 API。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| MAS Financial Institutions Directory | `[网页]` | 持牌金融机构总目录 | https://eservices.mas.gov.sg/fid |
| Major Payment Institution | `[网页]` | 按类别直达 | https://eservices.mas.gov.sg/fid/institution?category=Major+Payment+Institution |
| Banking | `[网页]` | 按 Banking sector 筛选 | https://eservices.mas.gov.sg/fid/institution?sector=Banking |

#### 2.2-2.5 建筑、医疗器械、食品、中国食品出口

> 均为 `[网页]` 交互式查询目录。详见 `references/sg-regulated-sectors.md`。

---

### 三、MICE 与商务活动生态

> 均为 `[网页]` 或 `[知识库]`，详见 `references/sg-events-innovation.md`。

---

### 四、政府采购与创新合作

#### 4.1 GeBIZ 政府招标

> `[网页]` GeBIZ 为 Web 门户，需手动搜索和筛选。

#### 4.2 Open Innovation Network

> `[网页]` Enterprise Singapore OIN 为网页浏览。

#### 4.3 Global Innovation Alliance

> `[网页]` GIA 为信息页面，无公开 API。

---

### 五、产业园区与选址分析

#### 5.1 JTC 园区空间

> `[网页]` JTC Find Space 为交互式网页工具。

#### 5.7 地理位置分析 — OneMap API

> `[API]` OneMap 提供 Search/Routing API（需注册 API key）。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| OneMap API Documentation | `[API]` | 需注册获取 token | https://www.onemap.gov.sg/apidocs/ |

#### 5.8 URA SPACE

> `[网页]` 交互式地图平台。

---

### 六、统计数据与市场分析

#### 6.1 SingStat 新加坡统计局

> ✅ **[API]** SingStat Developer API 已验证可用。
> ⚠️ **[MCP]** SingStat MCP 需实际连接测试，若不可用则使用 Developer API。

| 数据源 | 类型 | 说明 |
|--------|------|------|
| **SingStat Developer API** | `[API]` | REST API，按 resourceId 查询统计数据（已验证） | https://tablebuilder.singstat.gov.sg/view-api/for-developers |
| **SingStat MCP** | `[MCP]` | AI 原生查询接口（需连接测试） | https://www.singstat.gov.sg/data-tools-services/singstat-mcp |
| **Get Latest Data** | `[网页]` | 最新关键指标速览 | https://www.singstat.gov.sg/find-data/get-latest-data |

**已验证的 SingStat API 查询流程**：
1. 搜索 resourceId：`GET https://tablebuilder.singstat.gov.sg/api/table/resourceid?keyword=GDP&searchOption=all`
2. 获取表格数据（需进一步测试完整数据读取端点）

**已验证真实数据**（2026-07-06 查询）：
- 指标：Formation Of All Business Entities, Monthly
- 数值：2026年5月 **7,039** 家新注册企业
- 前一期：7,275 家
- Cessation：2026年5月 **4,674** 家
- 参考期：May 2026
- 来源：Singapore Department of Statistics (SingStat)，表 M085441/M085451
- 获取方式：WebFetch → https://www.singstat.gov.sg/find-data/get-latest-data

#### 6.2 BITE（企业商业洞察工具）

> `[网页]` BITE 为交互式商业分析工具，不作为核心 API。机器结构化查询优先使用 SingStat API。

| 模块 | 类型 | 说明 |
|------|------|------|
| BITE 主页 | `[网页]` | 交互式仪表盘 | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite |
| Wholesale Trade | `[网页]` | 批发贸易 | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/know-my-industry/wholesale-trade |
| Retail Trade | `[网页]` | 零售贸易 | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/know-my-customers/retail-trade |

#### 6.3 I-O Tables 2023

> `[知识库]` PDF/网页，非实时数据。

---

### 七、签证、税务、薪资与租金（运营数据）

> ⚠️ **规则**：所有具体数值必须实时回查官方来源。不得输出无来源的"行业平均"值。
> 工作准证最低工资与市场招聘薪资必须分开表述。
> 租金必须说明物业类型、地区和参考期。

| 数据域 | 数据源 | 类型 | 说明 |
|--------|--------|------|------|
| **EP 就业准证薪资门槛** | MOM Eligibility | `[网页]` | 实时最新门槛，需网页查询 | https://www.mom.gov.sg/passes-and-permits/employment-pass/eligibility |
| **S Pass 资格条件** | MOM S Pass | `[网页]` | 评分标准、配额、levy | https://www.mom.gov.sg/passes-and-permits/s-pass/eligibility |
| **LQS 本地合格薪资** | MOM LQS | `[网页]` | Progressive Wage Model | https://www.mom.gov.sg/employment-practices/progressive-wage-model/local-qualifying-salary |
| **企业所得税税率** | IRAS | `[网页]` | 当前税率、减免计划 | https://www.iras.gov.sg/quick-links/tax-rates/corporate-income-tax-rates |
| **GST 税率** | IRAS GST | `[网页]` | 当前 GST 税率 | https://www.iras.gov.sg/taxes/goods-services-tax-%28gst%29/basics-of-gst/current-gst-rates |
| **商业物业数据** | URA | `[网页]` | 商用物业租金/售价指数 | https://www.ura.gov.sg/property-data/commercial-properties/ |
| **工业物业数据** | JTC | `[网页]` | 工业用地/厂房租金 & 售价 | https://stats.jtc.gov.sg/content/static/landing.html |
| **市场薪资对比** | MOM | `[网页]` | 按职业/行业/年龄薪资基准 | https://stats.mom.gov.sg/bt/Pages/salary-comparison-general-for-employer.aspx |

---

### 八、SFA ADOS（海外食品认可数据库）

> `[网页]` ADOS 为交互式网页查询工具，支持导出 Excel/PDF。**无公开 API**。不得把 ADOS 描述为 API。

**两种使用模式**：
- 若 Agent 支持浏览器/RPA → 自动选择 Country/Region、Product Type 或 Establishment 并执行查询
- 若不支持网页交互 → 人工导出 Excel/PDF 后上传知识库，定期更新

| 数据源 | 类型 | 说明 |
|--------|------|------|
| SFA ADOS | `[网页]` | 按国家/产品/企业搜索获认可海外来源，支持导出 Excel/PDF | https://www.sfa.gov.sg/tools-and-resources/accreditation-database-for-overseas-sources |
| SFA 获准出口国家/地区清单 PDF | `[知识库]` | 静态备用数据源，用于判断国家和产品类别准入（标示更新 2026-05-07） | https://www.sfa.gov.sg/docs/default-source/food-import-and-export/list_of_approved_countries_regions.pdf |
| Overseas Accreditation 说明 | `[知识库]` | 海外认可制度说明 | https://www.sfa.gov.sg/food-import-export/accreditation-of-overseas-farms-establishments/overseas-accreditation-of-food-food-products |

> **查询流程**：访问 ADOS → 选 Country/Region=China → 选 Commodity → 查看 Establishment Number/Name/Province/Commodity/Form。SFA 官方 PDF 用于判断国家和产品类别准入。

---

### 九、中国官方实时信息源 — 驻新加坡大使馆经商处 `[网页]`

> **⭐ 优先级最高**：中国商务部派驻新加坡的官方机构网站。中文、日更级频率、覆盖经贸/政策/投资/合作/市场五大板块。

| 栏目 | 类型 | 说明 |
|------|------|------|
| 经贸动态 | `[网页]` | 新加坡最新经济/商业新闻（日更，已验证 2026-07-06 当天有文章） | https://sg.mofcom.gov.cn/jmdt/ |
| 政策解析 | `[网页]` | 新加坡政策变化的中文解读（家办新规、竞争法、AI政策等） | https://sg.mofcom.gov.cn/zcjx/ |
| 双向投资 | `[网页]` | 中国对新加坡投资流程、中资企业报到登记指引 | https://sg.mofcom.gov.cn/sxtz/ |
| 工程劳务 | `[网页]` | 中国企业在新承包工程/劳务项目确认流程 | https://sg.mofcom.gov.cn/gclw/ |
| 国际合作 | `[网页]` | RCEP / 一带一路 / 东盟合作动态 | https://sg.mofcom.gov.cn/gjhz/ |
| 中新合作 | `[网页]` | 苏州工业园/广州知识城等国家级双边项目 | https://sg.mofcom.gov.cn/zxhz/ |
| 市场信息 | `[网页]` | 新加坡行业市场分析、并购动态（中文） | https://sg.mofcom.gov.cn/scxx/ |

> **网站主页**：https://sg.mofcom.gov.cn/
>
> **使用策略**：经贸动态 + 政策解析 = 实时市场情报源；双向投资 = 中资企业合规入口；中新合作 = 双边商机信号；市场信息 = 行业分析。与 EDB/Enterprise Singapore 数据交叉验证。

---

### 十、投资与移民（保留原有）

| 数据源 | 类型 | 说明 |
|--------|------|------|
| EDB | `[知识库]` | 经济发展局 | https://www.edb.gov.sg |
| Enterprise Singapore | `[知识库]` | 企业发展局 | https://www.enterprisesg.gov.sg |
| MAS | `[网页]` | 金融管理局 | https://www.mas.gov.sg |
| IRAS | `[网页]` | 国内税务局 | https://www.iras.gov.sg |
| MOM | `[网页]` | 人力部 | https://www.mom.gov.sg |
| Singapore Customs | `[知识库]` | 海关 | https://www.customs.gov.sg |

---

## 信息检索策略（速查）

| 需求场景 | 优先路径 | 接入方式 |
|----------|----------|----------|
| 找本地客户/供应商 | data.gov.sg Datastore API → SSIC 代码筛选 | 🟢 API 实时 |
| 找华商网络 | SCCCI Corporate Members Directory | 🟡 网页 |
| 找中资企业（最新） | CEA 会员专区动态 → 年度报告（2021名录仅供历史参考） | 🟡 网页 |
| 中资企业近期动态 | CEA 中企通讯 2025 第1-3期 | 🔵 知识库 |
| 找持牌金融机构 | MAS FID | 🟡 网页 |
| 找建筑/工程伙伴 | BCA Directory | 🟡 网页 |
| 找医疗器械渠道 | HSA Infosearch | 🟡 网页 |
| 找食品进口/生产 | SFA Track Records | 🟡 网页 |
| 中国食品出口新加坡 | SFA ADOS（网页交互查询） | 🟡 网页 |
| 找政府招标 | GeBIZ | 🟡 网页 |
| 找展会/商务活动 | STB MICE Event Listing → Enterprise SG Events | 🟡 网页 |
| 统计数据（结构化） | SingStat Developer API | 🟢 API |
| 统计数据（AI查询） | SingStat MCP（需连接测试） | 🟣 MCP |
| 选产业园区 | JTC Find Space | 🟡 网页 |
| 选商业位置 | URA SPACE | 🟡 网页 |
| 签证/薪资门槛 | MOM Eligibility 实时查询 | 🟡 网页 |
| 税率查询 | IRAS 官网实时查询 | 🟡 网页 |
| 租金查询 | URA/JTC 官网实时查询 | 🟡 网页 |
| 中国→新加坡市场进入 | 驻新经商处实时情报 → 商务部指南 → EDB Workshop → 企业案例库 | 🟡 网页 + 🔵 知识库 |
| 新加坡实时商业情报（中文） | 驻新经商处 经贸动态 + 政策解析（日更） | 🟡 网页 |
| 商机排序与 Lead Scoring | Lead Scoring 模型（SSIC匹配度+合规+规模） → A/B/C 分级 | 🟢 API + 🔵 知识库 |
| 行业 GTM 操作手册 | FinTech / MedTech / F&B / 电商四大行业操作手册 | 🔵 知识库 |
| 银行开户与跨境支付 | DBS/OCBC/BOC/ICBC 开户清单 + Stripe/Adyen PayNow | 🔵 知识库 |
| IP 保护与 R&D 税务 | IPOS 专利/商标 + IRAS EIS / R&D Tax Measures | 🔵 知识库 |
| 人才招聘与高端签证 | 招聘平台 + MOM EA Directory + NUS/NTU/SMU 雇主通道 + ONE Pass | 🟡 网页 |
| 合作伙伴合规筛查 | MAS/UN/OFAC 制裁名单 + ACRA 合规信号 + SGX 气候披露 | 🟡 网页 + 🔵 知识库 |
| 自动化监控预警 | GeBIZ RSS / CEA RSS / data.gov.sg 月度 diff / MAS-HSA-SFA 监管变更 | 🟢 API + 🟡 网页 |
| 竞争格局分析 | Porter's Five Forces + I-O Tables + CCS 集中度框架 + ACRA 代理指标 | 🔵 知识库 |
| 新加坡 vs ASEAN 对比 | ASEANstats 跨国数据 + 各国税务/移民/房地产机构 | 🟡 网页 + 🔵 知识库 |
| 公司注册实操 | ACRA BizFile 分步 + CSP 代办 vs 自行办理 + 合规时间线 | 🟡 网页 + 🔵 知识库 |
| 销售赋能 | EDB GTM 框架 + SBF 企业痛点调查 + MRA 合作伙伴定义 | 🔵 知识库 |
| 定价策略 | GeBIZ 中标代理 + BITE 行业数据 + SaaS/消费品定价框架 | 🟡 网页 + 🔵 知识库 |
| M&A / JV | SIRA 外资审查 + CCS 竞争审查 + JV 关键条款框架 | 🟡 网页 + 🔵 知识库 |
| 政府关系 | SGDI 机构图谱 + EDB/ESG/STB 正式联系渠道 | 🟡 网页 |
| 媒体与 PR | BT/CNA/ST/Tech in Asia + EDB/STB 官方新闻稿语料 | 🟡 网页 |
| 供应链与物流 | SLA 会员 + Customs/TradeNet + MPA + PSA + SCDF（分层费用） | 🟡 网页 |
| 争议解决与退出 | SIAC/SICC/SIMC 三路径 + 纽约公约 + ACRA 退出 + SGX 上市 | 🟡 网页 + 🔵 知识库 |
| 绿色经济 / ESG GTM | 碳市场(CIX+ICC) + 可再生能源(SolarNova+EMA) + 绿色融资(SBGS) + ESG 报告 | 🟡 网页 + 🔵 知识库 |
| 政府资助匹配 | 10 参数画像 → 动态匹配 Startup SG/EDG/MRA/PSG/EEG/EFS → 输出比例/上限/入口 | 🟡 网页 + 🔵 知识库 |
| 区域总部设立 | Subsidiary vs Branch vs IHQ vs DEI vs FTC + DTA/TP/Withholding Tax | 🟡 网页 + 🔵 知识库 |
| 第一年成本估算 | 18 项成本公式 + ACRA 固定费用 + URA/JTC/MOM 动态变量 + 市场报价规则 | 🟡 网页 + 🔵 知识库 |

---

## References

- `references/sg-gov-apis.md` — 政府 API 详细文档（data.gov.sg、SingStat、ACRA、GeBIZ、EDB/ESG）
- `references/sg-biz-resources.md` — 商务拓展资源目录（园区、展馆、协会、展会排期、银行、服务机构）
- `references/sg-enterprise-discovery.md` — 企业发现数据源详解（ACRA、SBF、SCCCI、CEA、Startup SG）
- `references/sg-regulated-sectors.md` — 行业监管目录（MAS、BCA、HSA、SFA）
- `references/sg-events-innovation.md` — MICE 与创新合作（SACEOS、STB、Enterprise SG、OIN、GIA）
- `references/sg-market-entry.md` — 中国→新加坡市场进入全路径（驻新经商处、商务部指南、EDB 案例、Workshop、MRA、专业服务）
- `references/sg-operational-data.md` — 运营数据参考（签证、税务、薪资、租金实时查询链接）
- `references/sg-lead-scoring.md` — 商机优先级排序（基于 ACRA 字段的评分模型、A/B/C 分级、合规趋势判断）
- `references/sg-gtm-playbooks.md` — 行业 GTM 操作手册（FinTech/MedTech/F&B/E-commerce 四大行业进入路径）
- `references/sg-business-operations.md` — 商业运营参考（银行开户、IP 与技术转移、人才获取、合规风险、商业文化、销售赋能、定价策略、M&A/JV、政府关系、媒体/PR、供应链物流、争议解决/退出）
- `references/sg-automation-monitoring.md` — 自动化监控与预警（新企预警、招标预警、中资动态、监管变化）
- `references/sg-competitive-analysis.md` — 竞争格局分析（Porter's Five Forces、代理指标、CCS 集中度框架、中国企业优劣势矩阵）
- `references/sg-asean-comparison.md` — 新加坡 vs ASEAN 枢纽对比（SG/MY/TH/ID 跨维度统一口径比较）
- `references/sg-company-registration.md` — 公司注册分步实操（准备→名称→BizFile→UEN→CorpPass→合规时间线）
- `references/sg-green-gtm.md` — 绿色经济/ESG GTM（碳市场/可再生能源/绿色融资/ESG 披露/中国新能源企业路径）
- `references/sg-grant-matching.md` — 政府资助动态匹配引擎（10 参数画像→匹配计划→支持比例/上限/资格/入口/来源日期）
- `references/sg-regional-hq.md` — 区域总部设立指南（Subsidiary/Branch/IHQ/DEI/FTC 结构对比 + DTA/TP/Withholding Tax）
- `references/sg-cost-calculator.md` — 第一年成本估算模板（18 项成本公式 + 政府固定锚点 + 动态变量 + 市场报价规则）
