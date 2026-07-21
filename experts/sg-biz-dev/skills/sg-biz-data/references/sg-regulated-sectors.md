# 新加坡行业监管目录与持牌企业查询

> 本文档详述如何通过监管机构目录查找持牌金融机构、建筑承包商、医疗器械企业和食品企业。

---

## 1. MAS 金融机构目录

### 1.1 使用准则

在寻找银行、支付机构、跨境汇款企业、基金管理机构、资本市场机构和金融渠道伙伴时，**必须优先使用 MAS Financial Institutions Directory**，按照 licence type 和 regulated activity 筛选。不得仅依据企业自我宣传判断其金融业务资格。

### 1.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| MAS Directories | 金管局目录入口 | https://www.mas.gov.sg/directories |
| MAS Financial Institutions Directory | 持牌金融机构总目录 | https://eservices.mas.gov.sg/fid |
| MAS Institution Directory | 按类型查询 | https://eservices.mas.gov.sg/fid/institution |

### 1.3 常用查询

| 牌照类型 | 直接链接 |
|----------|----------|
| Major Payment Institution | https://eservices.mas.gov.sg/fid/institution?category=Major+Payment+Institution |
| Capital Markets Services Licensee | https://eservices.mas.gov.sg/fid/institution?category=Capital+Markets+Services+Licensee |
| Banking | https://eservices.mas.gov.sg/fid/institution?sector=Banking |

### 1.4 商务拓展场景

- 跨境支付合作伙伴 → Major Payment Institution 目录
- 基金管理/投资伙伴 → Capital Markets Services Licensee
- 企业银行开户 → Banking 目录确认持牌资质
- 保险/再保险 → Insurance sector 筛选

---

## 2. BCA 建筑与工程目录

### 2.1 使用场景

寻找建筑承包商、Licensed Builder、Facilities Management 企业、建筑材料供应商、机电工程企业、智能楼宇和工程渠道伙伴。

### 2.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| BCA Directory | 建筑企业目录 | https://www.bca.gov.sg/ebacs/bca_directory |
| BCA eBACS | 电子建筑认证系统入口 | https://www.bca.gov.sg/ebacs/ |
| Contractors Registration System (CRS) | 承包商注册系统，按等级和工程类型查询 | https://www1.bca.gov.sg/growth-and-transformation/procurement/registration-of-built-environment-firms/contractors-registration-system-crs/ |
| BCA Suppliers Registry | 符合公共建筑供应注册要求的材料和设备供应企业 | https://www1.bca.gov.sg/growth-and-transformation/procurement/registration-of-built-environment-firms/suppliers-sy-registry/ |

### 2.3 分析策略

- BCA Directory 直接覆盖 registered contractors、licensed builders、FM companies 和 construction-related suppliers
- Suppliers Registry 用于识别符合公共建筑供应注册要求的材料和设备供应商
- 结合 ACRA SSIC 代码（建筑类）交叉验证

---

## 3. HSA 医疗器械企业查询

### 3.1 使用场景

寻找医疗器械代理商、健康产品进口商、批发商、制造商和持牌合作伙伴。

### 3.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| HSA Infosearch | 健康产品与医疗器械企业查询 | https://www.hsa.gov.sg/e-services/infosearch/ |
| HSA Licensed Companies Search | 持牌公司直接查询 | https://eservice.hsa.gov.sg/prism/common/enquirepublic/SearchCompany.do?action=load |
| HSA Medical Devices | 医疗器械监管主页 | https://www.hsa.gov.sg/medical-devices/ |

### 3.3 分析准则

- 应将 HSA 监管资格与 ACRA 企业主体、企业官网和已代理产品结合分析
- 不得仅凭企业官网宣传判断其医疗器械资质
- HSA Infosearch 同时提供健康产品进口商、批发商和制造商查询入口

---

## 4. SFA 食品企业查询

### 4.1 使用场景

寻找食品进口商、食品生产商、餐饮终端、餐饮客户和食品供应链企业。重点识别：
- 企业经营类型（Food Stall / Caterer / Manufacturer / Importer）
- 食品许可或登记状态
- 实际经营地点

### 4.2 核心资源

| 资源 | 用途 | 链接 |
|------|------|------|
| SFA Track Records | 持牌食品场所记录查询 | https://www.sfa.gov.sg/tools-and-resources/track-records |
| SFA Tools & Resources | 食品局工具资源总入口 | https://www.sfa.gov.sg/tools-and-resources |
| SFA Food Import & Export | 食品进出口监管 | https://www.sfa.gov.sg/food-import-export |
| SFA 进口许可企业类别 | 需要许可证/注册的进口业务类型 | https://www.sfa.gov.sg/food-import-export/licence-permit-registration/businesses-that-need-licence-permit-registration-for-import-export |
| SFA Import Requirements | 食品产品进口要求 | https://www.sfa.gov.sg/food-import-export/commercial-imports/import-requirements-for-food-food-products |
| data.gov.sg Licensed Eating Establishments | 持牌餐饮场所开放数据 | https://data.gov.sg/datasets/d_227473e811b09731e64725f140b77697/view |
| SFA data.gov.sg 数据入口 | SFA 在 data.gov.sg 上的所有数据集 | https://data.gov.sg/datasets?agencies=Singapore+Food+Agency+%28SFA%29 |

### 4.3 分析策略

- SFA Track Records 可查询 food stalls、caterers、food manufacturers 等持牌经营主体
- data.gov.sg 持牌餐饮场所数据集可用于地理分布分析

---

## 5. 中国食品出口新加坡 — SFA 海外认可

> **重要**：SFA ADOS 为交互式网页查询工具，**无公开 API**。不得将 ADOS 描述为 API。

### 5.1 两种使用模式

| 模式 | 条件 | 操作 |
|------|------|------|
| **浏览器/RPA 自动查询** | Agent 支持浏览器自动化 | 自动选择 Country/Region、Product Type 或 Establishment 并执行查询 |
| **人工导出 + 知识库上传** | 不支持网页交互 | 人工在 ADOS 页面导出 Excel/PDF，上传知识库，定期更新 |

### 5.2 核心资源

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| SFA ADOS | `[网页]` | 交互式查询获认可海外农场/企业，支持导出 Excel/PDF | https://www.sfa.gov.sg/tools-and-resources/accreditation-database-for-overseas-sources |
| SFA 获准出口国家/地区清单 PDF | `[知识库]` | 静态备用数据源，判断国家和产品类别准入（标示更新 2026-05-07） | https://www.sfa.gov.sg/docs/default-source/food-import-and-export/list_of_approved_countries_regions.pdf |
| Overseas Accreditation of Food | `[知识库]` | 食品海外认可制度说明 | https://www.sfa.gov.sg/food-import-export/accreditation-of-overseas-farms-establishments/overseas-accreditation-of-food-food-products |
| General Requirements | `[知识库]` | 海外认可通用要求 | https://www.sfa.gov.sg/food-import-export/accreditation-of-overseas-farms-establishments/general-requirements-for-overseas-farms-establishments-accreditation |

> **查询流程**：ADOS → 选 Country/Region=China → 选 Commodity → 查看 Establishment Number/Name/Province/Commodity/Form。SFA 官方 PDF 用于判断国家和产品类别准入。PDF 为二进制压缩，WebFetch 无法直接提取文本。

---

## 快速检索矩阵

| 寻找目标 | 优先路径 |
|----------|----------|
| 持牌银行/支付机构 | MAS FID → Banking / Major Payment Institution |
| 基金管理/证券 | MAS FID → Capital Markets Services Licensee |
| 建筑承包商 | BCA Directory → CRS 等级查询 |
| 建材供应商 | BCA Suppliers Registry |
| 医疗器械代理商 | HSA Infosearch → Licensed Companies Search |
| 食品进口商 | SFA Track Records → 进口许可类别 |
| 餐饮终端客户 | data.gov.sg Licensed Eating Establishments |
| 中国食品出口新加坡 | SFA ADOS → 按国家和产品类型查询 |
