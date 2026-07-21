# 新加坡政府 API 详细参考

## 1. data.gov.sg API

### 概述
新加坡政府开放数据平台（data.gov.sg）是新加坡政府数据共享的核心门户，由 GovTech 管理。提供超过 1700 个数据集，覆盖经济、人口、交通、环境、教育等领域。

### API 基本规范

- **Base URL**: `https://api.data.gov.sg/v1`
- **认证**: 部分 API 需要 API Key，通过 `api-key` header 传递
- **速率限制**: 一般为每分钟 100 次请求
- **响应格式**: JSON
- **分页**: 部分端点支持 `page` 参数

### 商务拓展相关 API

#### 人口与劳动力
| API | 路径 | 说明 |
|-----|------|------|
| 人口趋势 | 通过 SingStat Table Builder 获取 | 人口结构、年龄分布、收入中位数 |
| 劳动力数据 | 通过 SingStat 获取 | 就业率、行业就业分布、薪资水平 |
| CPI 消费者价格指数 | 通过 SingStat 获取 | 通胀数据，用于定价策略 |

#### 经济数据
| API | 路径 | 说明 |
|-----|------|------|
| GDP 数据 | 通过 SingStat 获取 | 季度 GDP 增长、行业贡献度 |
| 对外贸易数据 | 通过 SingStat 获取 | 中新贸易额、主要商品类别 |
| FDI 外资数据 | 通过 SingStat 获取 | 各国外商直接投资流向 |

#### 房地产与土地
| API | 路径 | 说明 |
|-----|------|------|
| 房地产价格指数 | `/realestate/resale-prices` | HDB 转售价格指数 |
| 私人住宅价格 | URA Property Market Information | 私人住宅价格指数 |

#### 交通
| API | 路径 | 说明 |
|-----|------|------|
| 实时交通图像 | `/transport/traffic-images` | 高速公路实时画面 |
| 出租车可用性 | `/transport/taxi-availability` | 实时可用出租车位置 |
| 公交到达时间 | `/transport/bus-arrival` | 实时公交到站信息 |

#### 环境
| API | 路径 | 说明 |
|-----|------|------|
| PSI 空气质量 | `/environment/psi` | 全国及各区域 PSI 指数 |
| PM2.5 | `/environment/pm25` | 细颗粒物浓度 |
| 紫外线指数 | `/environment/uv-index` | 紫外线指数 |
| 天气预报 | `/environment/2-hour-weather-forecast` | 2 小时天气预报 |
| 24 小时预报 | `/environment/24-hour-weather-forecast` | 24 小时天气预报 |
| 4 天预报 | `/environment/4-day-weather-forecast` | 4 天天气预报 |

### SingStat Table Builder

新加坡统计局（SingStat）提供 Table Builder 工具（https://tablebuilder.singstat.gov.sg），可自定义查询和下载统计数据。支持 API 访问。

### 开发者资源

- 开发者门户: https://developers.data.gov.sg
- API 文档: https://data.gov.sg/api-documentation
- GitHub: https://github.com/datagovsg

---

## 2. ACRA（企业注册局）

### BizFile+ 系统

ACRA 主要通过 BizFile+ 提供服务，不是标准 REST API，而是 Web 门户。

**可查询信息：**
- 公司基本信息（免费）：公司名称、UEN、注册日期、注册地址、主要业务活动（SSIC 代码）
- 公司详细档案（付费）：董事/秘书/股东信息、年度申报、财务报表摘要
- 合规状态：是否处于活跃状态、是否有违规记录

**费用参考（新币）：**
- 公司基本档案：S$5.50
- 公司详细档案：S$16.00
- 财务报表摘要：S$28.00

**访问**: https://www.bizfile.gov.sg

---

## 3. GeBIZ（政府电子采购平台）

### 概述
GeBIZ 是新加坡政府统一的电子采购和招标平台，所有政府部门和法定机构的采购项目必须通过 GeBIZ 发布。

### 功能模块
- **招标公告**（Tender Notices）：公开招标信息
- **报价请求**（Request for Quotation, RFQ）：小额采购询价
- **采购订单**（Purchase Orders）：已中标的采购
- **供应商注册**（Supplier Registration）：成为政府供应商

### 分类体系
GeBIZ 使用 UNSPSC 分类码对采购项目进行分类，覆盖：
- 信息技术
- 建筑工程
- 咨询服务
- 医疗器械
- 教育培训
- 物流运输
- 等等

### 供应商注册等级
- **S1**（最低）：合同金额 ≤ S$70,000
- **S2**：合同金额 ≤ S$200,000
- **S3**：合同金额 ≤ S$500,000
- **S4**：合同金额 ≤ S$1,000,000
- **S5-S10**：更高金额等级

**访问**: https://www.gebiz.gov.sg

---

## 4. EDB & Enterprise Singapore 资助计划 API 参考

### EDB 激励计划（非 API，需直接联系）

| 计划名称 | 说明 | 适用对象 |
|----------|------|----------|
| Pioneer Certificate Incentive (PC) | 先锋企业优惠，5-15 年免税 | 引入新技术/新产业的企业 |
| Development and Expansion Incentive (DEI) | 发展与扩展优惠，5-10% 优惠税率 | 扩展高附加值业务的企业 |
| Finance & Treasury Centre (FTC) Incentive | 金融与财资中心优惠，8% 优惠税率 | 设立区域财资中心的企业 |
| Intellectual Property Development Incentive (IDI) | 知识产权发展优惠 | 研发和 IP 管理企业 |
| Tech@SG | 科技企业工作签证快速通道 | 高增长科技企业 |

### Enterprise Singapore 资助计划

| 计划名称 | 说明 | 适用对象 |
|----------|------|----------|
| Market Readiness Assistance (MRA) | 市场进入资助，最高 70% 费用补贴 | 中小企业海外拓展 |
| Double Tax Deduction for Internationalisation (DTDi) | 国际化双重减税 | 参与海外展会/考察的企业 |
| Enterprise Development Grant (EDG) | 企业发展资助，最高 70% | 创新/转型/国际化项目 |
| Productivity Solutions Grant (PSG) | 生产力解决方案资助 | 中小企业技术升级 |
| Startup SG | 创业支持系列计划 | 初创企业 |

---

## 5. SingStat 统计 API 与 MCP

### 能力层级

| 接入方式 | 状态 | 说明 |
|----------|------|------|
| 🟢 **Developer API** | **已验证可用** | REST API，免费，按 resourceId 查询统计数据 |
| 🟣 **SingStat MCP** | **需实际连接测试** | AI 原生查询接口，能否在 WorkBuddy 直接运行需连接测试 |
| 🔵 **Get Latest Data (Web)** | **已验证可用** | 网页，WebFetch 可获取最新关键指标 |

### SingStat Developer API `[API]`

**已验证可用**。REST API，无需认证（公开数据）。

**API Base URL**：`https://tablebuilder.singstat.gov.sg/api/table/`

**已验证端点**：
```
# 搜索 resourceId（已验证可用）
GET https://tablebuilder.singstat.gov.sg/api/table/resourceid?keyword={keyword}&searchOption=all

# 示例：搜索 GDP 相关表
GET https://tablebuilder.singstat.gov.sg/api/table/resourceid?keyword=GDP&searchOption=all
→ 返回 50 个表，包含 resourceId、title、tableType
```

**已验证可用表**：
- M085441：Formation Of All Business Entities By Industry, Monthly
- M085451：Cessation Of All Business Entities By Industry, Monthly
- M085831：Formation Of All Business Entities By Detailed Industry, Monthly

| 资源 | 链接 |
|------|------|
| Developer API 主页 | https://tablebuilder.singstat.gov.sg/view-api/for-developers |
| Find APIs | https://tablebuilder.singstat.gov.sg/view-api/find-apis |
| Get Latest Data (Web) | https://www.singstat.gov.sg/find-data/get-latest-data |

### SingStat MCP `[MCP]`

> ⚠️ **需连接测试**：SingStat MCP 真实性已确认，但能否在 WorkBuddy 直接运行需实际连接测试。若 MCP 无法接入，使用 Developer API 作为备用。

- **SingStat MCP**：https://www.singstat.gov.sg/data-tools-services/singstat-mcp
- SingStat 官方明确将 MCP 定位为 AI 聊天工具和 AI-powered applications 检索官方数据的接口

### ✅ 已验证真实数据（2026-07-06）

通过 WebFetch → https://www.singstat.gov.sg/find-data/get-latest-data 获取：

| 指标 | 数值 | 参考期 | 表名 |
|------|------|--------|------|
| Formation Of Business Entities | **7,039** | May 2026 | M085441 |
| Cessation Of Business Entities | **4,674** | May 2026 | M085451 |
| 前一月 Formation | 7,275 | Apr 2026 | M085441 |
| 前一月 Cessation | 4,631 | Apr 2026 | M085451 |

数据来源：Singapore Department of Statistics (SingStat)

### BITE（企业商业洞察工具） `[网页]`

> BITE 作为交互式商业分析工具使用，不作为核心 API。机器结构化查询优先使用 SingStat MCP 或 Developer API。

| 模块 | 链接 |
|------|------|
| BITE 主页 | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite |
| Wholesale Trade | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/know-my-industry/wholesale-trade |
| Retail Trade | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/know-my-customers/retail-trade |
| F&B Services | https://www.singstat.gov.sg/data-tools-services/business-insights-tool-for-enterprises-bite/know-my-customers/food-and-beverage-services |

## 6. Input-Output Tables（产业关联分析）

Singapore Supply, Use and Input-Output Tables 2023，用于判断产业的主要投入行业、下游需求和行业间关联。

| 资源 | 链接 |
|------|------|
| SU-IOT 2023 Infographic | https://www.singstat.gov.sg/publication-resources/supply-use-and-input-output-tables-2023-infographic |
| Data Explained | https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/supply-use-and-input-output-tables/our-data-explained |
| Interact With Our Data | https://www.singstat.gov.sg/find-data/explore-data-themes/economy-prices/supply-use-and-input-output-tables/interact-with-our-data |
| Official PDF | https://www.singstat.gov.sg/files/38baa109-ceb9-48e4-9dac-e25b7d7b253c.pdf |

> **注意**：I-O Tables 用于产业关联结构分析，不应直接作为实时企业名单使用。

## 7. OneMap API（地理位置）

将 ACRA 注册地址映射至位置后，进行园区、距离和产业集聚分析。

| 资源 | 链接 |
|------|------|
| OneMap API Documentation | https://www.onemap.gov.sg/apidocs/ |
| Search API | https://www.onemap.gov.sg/apidocs/search |
| Routing API | https://www.onemap.gov.sg/apidocs/routing |
| Registration | https://www.onemap.gov.sg/apidocs/register |
| Authentication | https://www.onemap.gov.sg/apidocs/authentication |

## 8. URA SPACE（土地用途与规划）

判断某业务是否适合某区域、分析工业用途、Business Park 和土地规划。

| 资源 | 链接 |
|------|------|
| URA SPACE | https://eservice.ura.gov.sg/maps/index.html |
| URA Master Plan | https://eservice.ura.gov.sg/maps/index.html?service=mp |
| Data Services API Registration | https://eservice.ura.gov.sg/maps/api/reg.html |

> **注意**：URA SPACE 数据用于 Business Location Intelligence，不作为企业客户目录。

## 9. 数据查询工具建议

### 推荐工具栈
- **实时 API 调用**：使用 `curl` 或 Python `requests` 调用 data.gov.sg Datastore API（已验证可用）
- **统计数据**：SingStat Developer API（已验证可用），替代方案：SingStat MCP（需连接测试）
- **AI 原生查询**：SingStat MCP（优先推荐，需先确认可在 WorkBuddy 中运行）
- **企业查询**：data.gov.sg v1 Datastore API（优先），ACRA BizFile+（备选）
- **招标监控**：GeBIZ 支持邮件订阅和 RSS 通知
- **展会追踪**：STB MICE Event Listing + Enterprise SG Events
- **选址分析**：OneMap API（需注册 API key）+ URA SPACE

### 数据整合建议
- 可结合中国商务部、海关总署的贸易数据做交叉验证
- 建议建立定期更新机制（月度/季度），确保数据时效性
- SingStat MCP 提供 AI 原生查询能力，应作为统计数据检索的首选路径（需先确认可用性）
- data.gov.sg v1 API 为免费公开 API，已验证可直接返回结构化企业数据
