# 新加坡企业发现数据源详解

> 本文档详述如何在 ACRA Open Data、data.gov.sg、SBF、SCCCI、CEA 和 Startup SG 中系统性发现目标企业。
>
> **数据源能力标注**：🔵知识库/RAG | 🟢API | 🟣MCP | 🟡网页交互

---

## 1. ACRA 企业基础数据库 `[API]`

### 1.1 数据定位逻辑

在寻找新加坡本地客户、供应商、合作伙伴、渠道商和代理商时，优先使用 data.gov.sg Datastore API（已验证可用）：

- **识别维度**：企业名称、UEN（统一实体编号）、注册状态、成立日期、实体类型、注册地址、主要 SSIC、次要 SSIC
- **行业映射**：结合 SSIC 2025 将用户的自然语言行业需求映射到新加坡官方行业分类，再筛选目标企业
- **更新频率**：data.gov.sg 企业集合按月更新

### 1.2 核心资源

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| **data.gov.sg 企业集合 Collection 2** | `[API]` | 27个CSV数据集，按月更新，57,000+记录/字母 | https://data.gov.sg/collections/2/view |
| **Collection 2 Metadata API** | `[API]` | 集合元数据（数据集列表、更新日期） | `GET https://api-production.data.gov.sg/v2/public/api/collections/2/metadata` |
| **Datastore Search API** | `[API]` | 实时查询企业数据，支持过滤（已验证） | `GET https://data.gov.sg/api/action/datastore_search?resource_id=<id>&limit=5&filters={"entity_status_description":["Live Company"]}` |
| **ACRA Open Data Initiative** | `[知识库]` | 企业开放数据计划 | https://www.acra.gov.sg/resources/open-data-initiative/ |
| **ACRA API Marketplace** | `[API]` | 收费API，企业详细信息 | https://www.acra.gov.sg/resources/eservice-tools-portals/api-marketplace/ |
| **Dataset API 文档** | `[知识库]` | 搜索与过滤指南 | https://guide.data.gov.sg/developer-guide/dataset-apis/search-and-filter-within-dataset |

### 1.3 已验证 API 查询示例

**查询 5 家真实新加坡企业（Live Company）**：
```
GET https://data.gov.sg/api/action/datastore_search?resource_id=d_af2042c77ffaf0db5d75561ce9ef5688&limit=5&filters={"entity_status_description":["Live Company"]}
```

**返回示例**（2026-07-06 验证）：
| UEN | 企业名称 | 状态 | Primary SSIC |
|-----|----------|------|-------------|
| 191200028Z | WBL CORPORATION LIMITED | Live Company | 64202 - HOLDING COMPANY |
| 193700005K | WEARNES AUTOMOTIVE SERVICES PTE. LTD. | Live Company | 66221 |
| 194000021M | WOH HUP (PRIVATE) LIMITED | Live Company | 41001 |
| 194000033G | WAH HIN AND COMPANY PRIVATE LIMITED | Live Company | 64300 - PERSONAL INVESTMENT HOLDING COMPANIES |
| 194700016Z | WBL PROPERTIES (CHINA) (PRIVATE) LIMITED | Live Company | 64202 - HOLDING COMPANY |

数据来源：data.gov.sg Datastore API，ACRA Information on Corporate Entities ('W') 数据集，总记录 57,373，Live Company 11,680 条。

SSIC 2025（Singapore Standard Industrial Classification）是新加坡标准行业分类代码体系，用于：
- 将用户自然语言需求（如"新能源企业""物流公司"）映射到官方行业代码
- 精准筛选目标行业的企业
- 分析行业规模和结构

| 资源 | 链接 |
|------|------|
| SSIC 2025 主页 | https://www.singstat.gov.sg/standard-classifications/national-classifications/singapore-standard-industrial-classification-ssic |
| ACRA SSIC 选择说明 | https://www.acra.gov.sg/register/business/choosing-reserving-a-business-name/finding-the-right-ssic-code/ |

### 1.4 data.gov.sg API 说明

| 资源 | 链接 |
|------|------|
| API Overview | https://guide.data.gov.sg/developer-guide/api-overview |
| Dataset APIs | https://guide.data.gov.sg/developer-guide/dataset-apis |
| API Key 说明 | https://guide.data.gov.sg/developer-guide/api-overview/how-to-use-your-api-key |

---

## 2. SBF 企业商业网络

### 2.1 使用场景

寻找具有一定经营规模、商协会参与度和本地商业网络的企业时使用。重点识别：
- 企业名称、行业组
- 商协会关系
- 新会员信号（企业新增商业网络活动）

### 2.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| SBF 官网 | 工商联合总会 | https://www.sbf.org.sg/ |
| SBF Membership | 会员体系说明 | https://www.sbf.org.sg/membership-tacs/membership |
| SBF Members' Directory | 企业会员目录（可搜索） | https://members.sbf.org.sg/membershipdirectory |
| SBF Trade Associations & Chambers | 下属行业协会与商会网络 | https://www.sbf.org.sg/membership-tacs/tacs |
| New SBF Members 2025 PDF | 新入会企业名单（商业网络信号） | https://www.sbf.org.sg/docs/default-source/membership/members-orientation/%28for-networking%29---members%27-directory---02-april-2025.pdf |

### 2.3 分析策略

- SBF 会员目录公开提供企业目录信息
- 新会员 PDF 可进一步作为企业新增商业网络活动信号
- SBF 下属 TACs 网络覆盖各主要行业协会，可沿 TAC→会员企业路径扩展发现

---

## 3. SCCCI 华商网络

### 3.1 使用场景

寻找新加坡华商企业、华人商业网络、行业协会及潜在渠道合作伙伴。SCCCI 是新加坡历史最悠久的华商组织（1906 年成立），会员网络覆盖大量企业和行业协会，适合建立"企业→行业协会→商业网络"关系。

### 3.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| SCCCI 官网 | 中华总商会 | https://www.sccci.org.sg/ |
| SCCCI Connect | 商业连接平台 | https://www.sccci.org.sg/connect |
| Corporate Members Directory | 企业会员目录 | https://www.sccci.org.sg/corporate-members-directory |
| Trade Association Members | 下属行业协会目录 | https://www.sccci.org.sg/ta-members-directory |
| SCCCI Membership | 会员申请入口 | https://www.sccci.org.sg/membership-application |
| Corporate Membership 详情 | 企业会员类型 | https://www.sccci.org.sg/user/membership/overview/type/corporate |

---

## 4. CEA 中资企业网络

> **核心变化**：CEA 不存在公开的 2021 年后完整会员名录。改为"增量会员数据库"模式。

### 4.1 会员识别规则（三级分类） `[关键规则]`

| 标记级别 | 条件 | 示例 |
|----------|------|------|
| **CEA 会员** | CEA 明确表述为"新会员、会员单位或会员名录"的企业 | 2023年10月15家新会员、中企通讯第2期"2025年1-4月新会员" |
| **CEA 公开资料出现企业** | 仅出现在活动报道、调研或年度报告中的企业 | 南华新加坡、天合光能、中国电信 |
| **疑似中资企业** | 中文名称疑似中资但未经 CEA/官方资料验证 | — |

> **不得**自动将"CEA 公开资料出现企业"升级为"CEA 会员"。企业 UEN、注册状态和 SSIC 使用 data.gov.sg API 补全。

### 4.2 增量会员数据库

| 层级 | 内容 | 来源 | 状态 |
|------|------|------|------|
| 基准 | 2021 会员名录 | `[知识库]` | ✅ 有完整名单 |
| 增量1 | 2023年10月 15 家新会员 | https://cea.org.sg/协会动态-新入会会员名单/ | ⚠️ 页面含二维码名单，未直接列出企业名 |
| 增量2 | 2025年1-4月新会员 | 中企通讯 2025年第2期 PDF | ⚠️ PDF 二进制压缩，WebFetch 无法提取文本 |
| 增量N | 持续追踪 | CEA 会员动态 RSS | ✅ RSS 可用（已验证） |

### 4.3 持续追踪渠道

| 数据源 | 类型 | 说明 |
|--------|------|------|
| CEA 官网 | `[知识库]` | https://cea.org.sg/ |
| CEA 会员专区 | `[网页]` | https://cea.org.sg/category/会员专区/ |
| **CEA 会员动态 RSS** | `[知识库]` | **已验证可用** | https://cea.org.sg/category/会员专区/会员动态/feed/ |
| 新入会会员名单 | `[知识库]` | 2023-10，15 家（含二维码名单） | https://cea.org.sg/协会动态-新入会会员名单/ |
| 会员名录 2021 | `[知识库]` | **仅作历史基准** | https://cea.org.sg/《中资企业（新加坡）协会会员名录2021年版》正式/ |

### 4.4 已验证的 CEA 公开资料出现企业（2025年）

以下通过 CEA 会员动态 RSS 在 2026-07-06 验证，**仅标记为"CEA 公开资料出现企业"，非 CEA 会员**：

| 企业 | 最新证据日期 | 活动类型 |
|------|-------------|----------|
| 南华新加坡 | 2025-11-05 | 联合 SGX/中行举办闭门会议 |
| 中国石化 | 2025-10-28 | 工厂"公众开放日" |
| 天合光能 | 2025-10-03 | 落子新加坡十六年 |
| 中建南洋 | 2025-09-30 | WSH Award 7 项大奖 |
| 中国移动 | 2025-08-18 | 东南亚区域合作会议 |
| 新企程集团 | 2025-06-20 | 携手重庆共建中新出海平台 |

### 4.5 中资企业年度发展报告（案例语料） `[知识库]`

以下 PDF 报告用于训练"中国企业→新加坡市场进入"模式：

| 报告 | 链接 |
|------|------|
| 2024-2025 年度报告 PDF（中英） | https://cea.org.sg/wp-content/uploads/2025/12/2025新加坡中资企业年度发展报告_中英文版_R2_电子版.pdf |
| 2023-2024 年度报告 PDF（中英） | https://cea.org.sg/wp-content/uploads/2025/03/《2024新加坡中资企业年度发展报告》-中英文-电子版.pdf |

> **注意**：这些报告应作为案例语料，不是实时企业经营数据库。

### 4.6 中企通讯（中资企业动态信号） `[知识库]`

> **⚠️ 第3期状态**：2025-11-04 官方发布已确认，但当前"阅读全文"链接指向第2期 PDF。标记为"官方发布已确认、完整 PDF 待恢复"。**不得**把第2期 PDF 误标为第3期。

| 期数 | 类型 | 状态 | 链接 |
|------|------|------|------|
| 2025年 第1期 | `[知识库]` | ✅ | https://cea.org.sg/wp-content/uploads/2025/03/中企通讯_2025-第一期-电子版.pdf |
| 2025年 第2期 | `[知识库]` | ✅（含2025年1-4月新会员名单） | https://cea.org.sg/wp-content/uploads/2025/06/中企通讯_2025-第二期-电子版.pdf |
| 2025年 第3期 发布页 | `[知识库]` | ⚠️ 发布确认，PDF 待恢复 | https://cea.org.sg/会员动态-《中企通讯》2025年第三期正式上线发布/ |
| CEA 会员动态 RSS | `[知识库]` | ✅ 持续更新 | https://cea.org.sg/category/会员专区/会员动态/feed/ |

---

## 5. Startup SG 初创生态

### 5.1 使用场景

寻找 Startup、科技合作伙伴、投资标的、孵化器、加速器和 Corporate Innovation Partner。重点识别：企业行业、技术、融资和公开合作需求。

### 5.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| Startup SG | 新加坡初创生态门户 | https://www.startupsg.gov.sg/ |
| Startup Directory | 初创企业目录（公开 Profile） | https://frontend.startupsg.gov.sg/directory/startups/ |

---

## 快速检索矩阵

| 目标 | 路径 | 接入方式 |
|------|------|----------|
| 找所有新加坡注册企业 | data.gov.sg Datastore API → SSIC 代码筛选 | 🟢 API 实时 |
| 找特定行业企业 | SSIC 2025 代码映射 → Datastore API 筛选 | 🟢 API 实时 |
| 找大型/活跃企业 | SBF Members' Directory → 新会员 PDF 信号 | 🟡 网页 |
| 找华商/华商网络 | SCCCI Corporate Members → TA Members Directory | 🟡 网页 |
| 找中资企业（最新） | CEA 会员专区动态 → 年度报告（**不依赖 2021 名录**） | 🟡 网页 |
| 找中资企业近期动态 | CEA 中企通讯 2025 第1-3期 | 🔵 知识库 |
| 找初创/科技企业 | Startup SG Directory | 🟡 网页 |
