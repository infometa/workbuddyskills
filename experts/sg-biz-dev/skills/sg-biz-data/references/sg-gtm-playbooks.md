# 行业市场进入操作手册（GTM Playbooks）

> **定位**：行业专属的、可执行的市场进入操作手册。与宏观指南（商务部/EDB）互补，聚焦具体牌照、时间线和关键节点。
> **数据源标注**：🔵知识库 | 🟢API | 🟣MCP | 🟡网页

---

## 一、金融科技 GTM `[网页]`

### 1.1 牌照分类

| 牌照类型 | 缩写 | 适用业务 | 申请入口 |
|----------|------|----------|----------|
| **Standard Payment Institution** | **SPI** | 月均交易额 < S$3M（单一服务）或 < S$6M（两种以上） | https://www.mas.gov.sg/regulation/forms-and-templates/form-1---application-for-a-payment-service-provider-licence |
| **Major Payment Institution** | **MPI** | 月均交易额超过 SPI 阈值 | 同上 |
| **Capital Markets Services Licence** | **CMSL** | 基金管理、证券交易、REIT 管理 | https://www.mas.gov.sg/regulation/capital-markets/apply-for-licensing-or-registration-of-capital-market-entities/cms-licence |

> ⚠️ 使用 **SPI**，非 "SPL"。牌照类型以 PSA 2019 为准。

### 1.2 关键资源

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| MAS Payment Licensing Guide PDF | `[知识库]` | Payment Service Provider 牌照申请指南（2024版） | https://www.mas.gov.sg/-/media/mas-media-library/regulation/guidelines/pso/ps-g01-guidelines-on-licensing-for-payment-service-providers/guidelines-on-licensing-for-payment-service-providers-2024.pdf |
| Payment Services Act Guide PDF | `[知识库]` | PSA 2019 详细解读 | https://www.mas.gov.sg/-/media/mas/regulations-and-financial-stability/regulations-guidance-and-licensing/payment-service-providers/guide-to-the-payment-services-act-2019.pdf |
| PSP Licence 申请表 | `[网页]` | Form 1 | https://www.mas.gov.sg/regulation/forms-and-templates/form-1---application-for-a-payment-service-provider-licence |

### 1.3 时间线

> ⚠️ **不得固定写"6个月拿牌照"**。MAS 当前 Payment Service Provider 申请页面提示预计等待期可能超过一年。时间线必须动态核验。

**流程阶段**：
1. Pre-application consultation（建议）
2. Form 1 提交 → MAS 初步审查
3. 补充材料 → 反复沟通
4. In-principle Approval
5. 正式牌照

### 1.4 Regulatory Sandbox / Sandbox Plus

| 资源 | 类型 | 链接 |
|------|------|------|
| Regulatory Sandbox | `[网页]` | https://www.mas.gov.sg/development/fintech/regulatory-sandbox |
| Sandbox Plus | `[网页]` | https://www.mas.gov.sg/development/fintech/sandbox-plus |
| Sandbox Guidelines PDF | `[知识库]` | https://www.mas.gov.sg/-/media/mas-media-library/development/regulatory-sandbox/sandbox/fintech-regulatory-sandbox-guidelines-jan-2022-v12.pdf |

> **策略**：FinTech 企业优先申请 Sandbox → 验证产品市场契合 → 再申请正式牌照。

---

## 二、医疗科技 GTM `[网页]`

### 2.1 产品分类

HSA 采用 A/B/C/D 四级风险分类（Class A = 最低风险，Class D = 最高风险）。

| Class | 风险等级 | 注册要求 | 示例 |
|-------|----------|----------|------|
| **A** | 低风险 | 免注册（仅需产品通知） | 绷带、检查手套 |
| **B** | 中低风险 | 需注册 | 血压计、体温计 |
| **C** | 中高风险 | 需注册 | 呼吸机、X 光机 |
| **D** | 高风险 | 需注册（严格审查） | 心脏起搏器、植入器械 |

除 Class A 低风险器械外，医疗器械一般涉及注册要求。

### 2.2 关键资源

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| HSA Registration Overview | `[网页]` | 注册路径总览（含 reference agencies 名单） | https://www.hsa.gov.sg/medical-devices/registration-of-medical-devices/register-your-device/overview/ |
| HSA Registration Guides | `[网页]` | 各路径详细指南 | https://www.hsa.gov.sg/medical-devices/registration-of-medical-devices/register-your-device/guides/ |
| HSA Regulatory Reliance | `[网页]` | 监管依赖/参考机构框架 | https://www.hsa.gov.sg/medical-devices/registration-of-medical-devices/register-your-device/regulatory-reliance |
| HSA Guidance Documents | `[网页]` | 全部指导文件 | https://www.hsa.gov.sg/medical-devices/guidance-documents/ |
| HSA Infosearch | `[网页]` | 已注册产品/持牌企业查询 | https://www.hsa.gov.sg/e-services/infosearch/ |
| Licensed Companies Search | `[网页]` | 持牌公司查询 | https://eservice.hsa.gov.sg/prism/common/enquirepublic/SearchCompany.do?action=load |

### 2.3 HSA 参考监管机构（2026-03-13 验证）

> ⚠️ **NMPA 目前不在 HSA 认可的海外参考监管机构名单中**。不得训练模型回答"NMPA 批准即可走 HSA Abridged Route"。

当前 HSA 认可 5 家机构：

| 机构 | 国家/地区 |
|------|-----------|
| Australia TGA | 澳大利亚 |
| European Union Notified Bodies | 欧盟 |
| Health Canada | 加拿大 |
| Japan MHLW | 日本 |
| US FDA | 美国 |

### 2.4 注册路径决策树

> **规则**：模型回答中国医疗器械进入新加坡时，**先询问 Risk Class 和已有海外监管批准**，不再询问"NMPA 能否互认"。

```
用户问题：中国医疗器械如何进入新加坡？

第1步：确定 Risk Class（A/B/C/D）
  → Class A → 仅需产品通知（SHARE 系统提交）→ 结束

第2步：确认已有海外批准
  只有 NMPA 批准、无 HSA 认可机构批准
    → 默认 Full Evaluation Route
  至少 1 个 HSA 认可机构批准
    → 检查 Abridged Route
  1-2 个认可机构批准 + 上市 ≥3 年 + 无安全问题 + 无拒绝/撤回
    → Class C → ECR Route
    → Class D → EDR Route
    → Class B → Immediate Route（IBR）
```

### 2.5 各路径要求

| 路径 | 条件 | 来源 |
|------|------|------|
| **Full** | 无 HSA 认可机构批准 | Registration Overview |
| **Abridged** | ≥1 个认可机构批准 | Registration Overview |
| **ECR** (Class C Expedited) | ≥1 认可机构 + 上市 ≥3 年 + 无安全问题 | Registration Overview |
| **EDR** (Class D Expedited) | ≥2 认可机构 | Registration Overview |
| **IBR** (Class B Immediate) | ≥1 认可机构 + 上市 ≥3 年，或 ≥2 认可机构 | Registration Overview |

### 2.6 关键角色

- **Dealer Licence**：进口商/批发商需持有 HSA 颁发的经销商牌照
- **Local Authorised Representative**：海外制造商必须指定新加坡本地授权代表

---

## 三、食品饮料 GTM `[网页]`

### 3.1 进口许可

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| SFA Food Import & Export | `[网页]` | 食品进出口监管主页 | https://www.sfa.gov.sg/food-import-export |
| Food Import Requirements | `[网页]` | 各类食品进口要求 | https://www.sfa.gov.sg/food-import-export/commercial-imports/import-requirements-for-food-food-products |
| Import Licence 申请及费用 | `[网页]` | 进口许可证流程和费用 | https://www.sfa.gov.sg/food-import-export/licence-permit-registration/application-process-fees-for-licence-permit-registration-for-import-export |
| SFA Track Records | `[网页]` | 持牌企业查询 | https://www.sfa.gov.sg/tools-and-resources/track-records |

### 3.2 海外来源认可

使用 SFA ADOS 查询中国获认可企业（网页交互）。详见 `sg-regulated-sectors.md`。

### 3.3 冷链仓储

| 资源 | 类型 | 链接 |
|------|------|------|
| Coldstore Licence 流程 | `[网页]` | https://www.sfa.gov.sg/food-manufacturing-storage/licence-registration/application-process-fees-for-licence-permit-registration-for-food-manufacturing-storage |

### 3.4 Halal 认证

MUIS（新加坡回教理事会）官方流程包括：申请 → 文件验证 → 审计/检查 → 认证 → 续期。

| 资源 | 类型 | 链接 |
|------|------|------|
| MUIS Halal 主页 | `[网页]` | https://www.muis.gov.sg/halal/ |
| Halal Certification Process | `[网页]` | https://www.muis.gov.sg/halal/for-business/singapore-halal-certification-process/ |
| MUIS Halal e-Service | `[网页]` | https://halal.muis.gov.sg/ |

### 3.5 典型流程

1. 确认产品属于 SFA 获准进口类别（SFA ADOS / Approve Countries PDF）
2. 确认中国生产企业在 SFA 海外认可名单中
3. 新加坡进口商申请 Import Licence
4. 如需冷链 → 申请 Coldstore Licence
5. 如目标为穆斯林消费群体 → 申请 MUIS Halal 认证
6. 每批货物抵达前提交 Customs Permit（通过 TradeNet）

---

## 四、电商/消费 GTM `[网页]`

### 4.1 平台入驻

| 平台 | 资源 | 链接 |
|------|------|------|
| **Lazada** Seller Center | `[网页]` | https://sellercenter.lazada.sg/ |
| **Lazada** Seller Registration | `[网页]` | https://sellercenter.lazada.sg/apps/register/index |
| **Shopee** Seller Education Hub | `[网页]` | https://seller.shopee.sg/edu |
| **Shopee** Start Selling Guide | `[网页]` | https://seller.shopee.sg/edu/article/14165/how-to-start-selling-on-Shopee |

### 4.2 本地支付集成

| 支付方式 | 资源 | 链接 |
|----------|------|------|
| Stripe PayNow | `[网页]` | https://docs.stripe.com/payments/paynow |
| Adyen PayNow | `[网页]` | https://www.adyen.com/payment-methods/paynow |
| Adyen Pricing | `[网页]` | https://www.adyen.com/pricing |
| Grab Merchant Payments | `[网页]` | https://www.grab.com/sg/merchant/payment-solutions/ |

> ⚠️ **规则**：以上平台及支付资料应作为具体 GTM 操作来源。价格、手续费和平台规则**不得长期静态固化**。

### 4.3 典型流程

1. 在新加坡注册公司 → 获取 UEN
2. 开设企业银行账户 → 绑定平台收款
3. 入驻 Lazada/Shopee → 上传产品 → 设置定价和物流
4. 集成本地支付（首选 PayNow，覆盖率 ≥80% 新加坡消费者）
5. 解决退货/客服本地化

---

## 通用规则

1. **时间线**：所有牌照/注册处理时间以监管机构最新公布为准，不得静态固化
2. **费用**：以官网当前公布的 fee schedule 为准
3. **政策变更**：定期监控 MAS/HSA/SFA/MUIS 公告页
4. **交叉确认**：GTM 信息应与 ACRA 企业数据（本地合作伙伴）、GeBIZ（政府项目机会）交叉使用

---

## 五、绿色经济 / ESG GTM

> 详见独立参考文件 `sg-green-gtm.md`。覆盖：碳市场（CIX + ICC）、可再生能源（SolarNova + EMA）、绿色融资（SBGS）、ESG 披露（ACRA/SGX）、中国新能源企业进入路径。
