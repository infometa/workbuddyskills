# 自动化监控与预警

> 为专家模型建立主动监控能力，从"被动词料库"升级为"监控系统"。

---

## 一、新建企业预警 `[API]`

### 1.1 机制

ACRA/data.gov.sg 企业数据**按月更新**。采用月度快照差异比较，不依赖单独"新企业推送 API"。

```
流程：
1. 每月拉取 data.gov.sg Collection 2 全量数据
2. 以 UEN 为 key，与上月快照 diff
3. 识别：
   - 新注册企业（上月无、本月有）
   - 状态变化（Live → Struck Off / Dissolved）
   - 目标 SSIC 新增企业
4. 对目标 SSIC 新增企业套用 Lead Scoring 模型
5. A 级（≥75分）自动触发预警
```

### 1.2 数据源

| 资源 | 类型 | 链接 |
|------|------|------|
| ACRA Collection 2 | `[API]` | https://data.gov.sg/collections/2/view |
| Collection Metadata API | `[API]` | https://api-production.data.gov.sg/v2/public/api/collections/2/metadata |
| Dataset API（搜索/过滤） | `[API]` | https://guide.data.gov.sg/developer-guide/dataset-apis/search-and-filter-within-dataset |

---

## 二、招标机会预警 `[网页]`

### 2.1 机制

使用 GeBIZ 官方 Business Alerts 的 RSS 和 Email Alert 路径。

> ⚠️ **不要预设为 UNSPSC 分类**，除非实际 GeBIZ 返回字段明确采用 UNSPSC。GeBIZ 官方使用 Procurement Category / Main Category / Sub-category。

### 2.2 数据源

| 资源 | 类型 | 用途 | 链接 |
|------|------|------|------|
| GeBIZ Business Alerts | `[网页]` | RSS + Email Alert 设置 | https://www.gebiz.gov.sg/business-alerts.html |
| GeBIZ Opportunities | `[网页]` | 招标机会浏览 | https://www.gebiz.gov.sg/ptn/opportunity |
| GeBIZ Supplier Guide PDF | `[知识库]` | 供应商使用指南 | https://www.gebiz.gov.sg/docs/supplier_guide_detailed.pdf |
| GoBusiness GeBIZ Alerts | `[网页]` | 预警订阅入口 | https://govassist.gobusiness.gov.sg/gebiz-alerts |

---

## 三、中资企业动态预警 `[知识库]`

### 3.1 机制

接入 CEA 会员动态 RSS Feed，自动提取：

- Company name（企业名称）
- Event date（事件日期）
- Event type（事件类型：新会员入会/商务活动/获奖/合作签约等）
- Counterparty（合作方）
- Industry（行业）

### 3.2 数据源

| 资源 | 类型 | 链接 |
|------|------|------|
| CEA 会员动态 RSS | `[知识库]` | https://cea.org.sg/category/会员专区/会员动态/feed/ |
| CEA 会员专区 | `[网页]` | https://cea.org.sg/category/会员专区/ |

### 3.3 处理规则

- 仅明确标注"会员/新会员"的企业可更新 CEA 会员身份
- 活动报道中的企业标记为"CEA 公开资料出现企业"
- 企业 UEN、注册状态和 SSIC 通过 data.gov.sg API 补全

---

## 四、监管变化预警 `[网页]`

### 4.1 机制

建立监管机构公告页面/API 的增量监控：
- 发现新发布日期、标题或文件 URL 时触发预警
- 仅在发现新内容时触发，不重复推送已有内容
- 提取：监管机构 / 发布日期 / 目标行业 / 规则主题 / 生效日期 / 潜在企业影响

### 4.2 数据源

| 监管机构 | 资源 | 类型 | 链接 |
|----------|------|------|------|
| **MAS** | Regulations and Guidance | `[网页]` | https://www.mas.gov.sg/regulation/regulations-and-guidance |
| **HSA** | Announcements | `[网页]` | https://www.hsa.gov.sg/announcements |
| **SFA** | Circulars & Notices | `[网页]` | https://www.sfa.gov.sg/news-publications/circulars-and-notices |

> SFA Circulars & Notices 支持按关键词、类型、商品、国家/地区和时间筛选，适合食品监管变化监控。

---

## 五、预警汇总矩阵

| 预警类型 | 频率 | 数据源 | 接入方式 |
|----------|------|--------|----------|
| 新建企业 | 月度 | data.gov.sg API | 🟢 API |
| 招标机会 | 实时（RSS） | GeBIZ Alerts | 🟡 网页 RSS |
| 中资企业动态 | 实时（RSS） | CEA RSS | 🔵 知识库 RSS 抓取 |
| 监管变化 | 按更新频率 | MAS/HSA/SFA 公告页 | 🟡 网页增量监控 |

---

## 六、实施优先级

| 优先级 | 预警类型 | 理由 |
|--------|----------|------|
| P0 | 招标机会 | GeBIZ 已提供 RSS/Email，实施成本最低 |
| P1 | 中资企业动态 | CEA RSS 已验证可用 |
| P2 | 监管变化 | 需建立多源增量监控逻辑 |
| P3 | 新建企业 | 需月度快照存储 + diff 逻辑 |
