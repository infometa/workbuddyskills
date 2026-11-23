# 企业分析类工具 API 详情

## 目录
- [search_company - 搜索公司](#search_company)
- [get_company_registry - 工商登记信息](#get_company_registry)
- [get_company_profile - 公司画像](#get_company_profile)
- [get_company_business_keywords - 主营业务关键词](#get_company_business_keywords)
- [get_company_partners - 合作客户与供应商](#get_company_partners)
- [get_company_contacts - 公司项目联系人](#get_company_contacts)
- [find_competitors - 竞争对手分析](#find_competitors)
- [find_potential_bidders - 推荐潜在供应商](#find_potential_bidders)

---

## search_company - 搜索公司 {#search_company}

按名称搜索公司列表。**当用户输入公司简称或需要覆盖总部+各地分子公司时，先调用此接口获取所有相关公司，后续分析使用全量公司列表。**

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company_name` | str | ✓ | 公司名称，支持全称、简称或别名 |
| `province` | str | | 省份筛选，如「北京」「广东」 |
| `city` | str | | 城市筛选，如「深圳」「上海」 |
| `page` | int | | 页码，默认 1 |
| `page_size` | int | | 每页数量，最大 20，默认 10 |

### 请求示例

```json
POST /api_v2/search_company
{
  "company_name": "华润万家",
  "page": 1,
  "page_size": 20
}
```

### 响应结构

```json
{
  "data": {
    "total": 3,
    "page": 1,
    "page_size": 10,
    "items": [
      {
        "id": 12345,
        "fullname": "华润万家有限公司",
        "name": "华润万家",
        "province": "广东",
        "city": "深圳市",
        "win_count": 8920,
        "bid_count": 15600,
        "url": "https://www.zhiliaobiaoxun.com/company/12345?from=mcp"
      }
    ]
  }
}
```

### 使用规则

**自动匹配，无需用户确认**：调用后由 LLM 根据公司名称语义自动筛选相关结果，将所有匹配公司（总部+各地分子公司）一并用于后续查询，不打断用户流程。

```
用户说"分析华润万家的采购情况"
→ 调用 search_company(company_name="华润万家", page_size=20)
→ 获得：华润万家有限公司、华润万家（北京）有限公司、华润万家（上海）有限公司...
→ 自动将所有相关公司 fullname 列表用于后续 query_bids_advanced 查询
→ 直接输出分析结果，无需用户介入确认
```

**何时使用**：
- 用户输入简称（如"华为""腾讯""华润万家"）
- 需要统计某集团旗下所有主体的采购/中标数据
- 需要覆盖总部与各地分公司的完整市场表现

---

## get_company_registry - 工商登记信息 {#get_company_registry}

查企业的工商登记全量字段。与 `get_company_profile` 互补：本工具给工商登记事实，后者给招投标战绩。

**请求**：`POST /api_v2/get_company_registry`

```json
{"company_name": "企业名称，全称或简称均可"}
```

**内部已包含消歧**：先按全称精确查，未命中则用**招投标主体库**消歧拿到规范全称再取详情。
**不要自己先调 `search_company` 再调本工具**，那是多花一次调用做重复的事。

常见简称（「海康威视」「格力电器」「用友软件」）能定位到正主。**定位不到唯一主体时返回 `QUERY_EMPTY` 错误**，
并在 `error.details.candidates` 里给出候选 —— 此时把候选列给用户选，**绝不要自己挑一个当答案**。

**返回**：

| 字段 | 说明 |
|---|---|
| `matched_by` | `exact`（全称直接命中）/ `bidding_index`（经招投标主体库消歧命中，**必须告知用户实际查的是哪家**） |
| `matched_name` | 消歧后的规范企业全称 |
| `other_candidates` | 其余候选（仅 `bidding_index` 时非空），每项 `name`/`company_id`/`province`/`city`/`win_count` |
| `company` | 工商详情，字段见下 |

`company` 内的字段：

- **身份**：`name`、`unifiedSocialCreditCode`（统一社会信用代码）、`businessRegistrationNumber`（工商注册码）、`organizationCode`（组织机构代码）、`organizationType`（企业类型）、`legalRepresentative`（法定代表人）
- **状态**：`businessStatus` / `standardBusinessStatus`（经营状态，后者已标准化为存续/注销/吊销）、`establishmentDate`（成立日期）、`approvalDate`（核准日期）、`operatingPeriod`（营业期限，`{startDate, endDate}`，endDate 为空表示无固定期限）
- **实力**：`registeredCapital`（注册资本，万人民币）、`paidInCapital`（实缴资本，万人民币）、`scale`（人员规模区间 `{min, max}`）
- **业务**：`industry`（行业分类，实测形如「运营商/增值服务」，非国标层级码）、`professionalIndustry`（专业行业标签）、`businessScope`（经营范围）、`intro`（简介）
- **地址**：`province`/`city`/`area`、`address`（注册地）、`officialAddress`（办公地）、`registrationAuthority`（登记机关）
- **其它**：`usedName`（曾用名）、`nickNames`（简称）、`phone`、`email`、`site`（官网）、`trademark`（商标）、`tagValues`（企业标签）、`financeTypes`（融资情况）

**⚠️ 低填充率字段**：`trademark`（1.6%）、`site`（0.4%）、`phone`（42.6%）、`nickNames`（18.6%），`city`/`area` 对部分企业也为空（实测华为只有省份）。
**为空只能说「暂未收录」，绝不能说该企业没有商标/官网/电话。**

**`tagValues` 值得用起来**：里面常有「近期中标」「近期招标」「注册资本变更」「高管变动」「股权转让」「战略合作」
这类经营动态标签，比静态工商字段更能回答「这家公司最近在干嘛」。

---

## get_company_profile - 公司画像 {#get_company_profile}

获取公司基础工商信息、行业、招中标次数等画像数据。

### 请求参数

`company`（公司名/简称/ID）和 `company_url` 至少填一个。

| 参数 | 类型 | 说明 |
|------|------|------|
| `company` | str\|int | 公司全称/简称/ID（优先级：ID > 全称 > 简称） |
| `company_url` | str | 知了标讯公司详情页链接 |

### 响应结构

```json
{
  "data": {
    "id": 1234567890,
    "fullname": "华为技术有限公司",
    "name": "华为",
    "org_base_type": "企业",
    "industry": "通信设备制造",
    "industry_l1": "制造业",
    "province": "广东",
    "city": "深圳",
    "capital": "10000万人民币",
    "size": "大型企业",
    "business_status": "在营",
    "caller_count": 1500,
    "winner_count": 3200,
    "establishment_date": "1987-09-15",
    "url": "https://www.zhiliaobiaoxun.com/company/1234567890"
  }
}
```

---

## get_company_business_keywords - 主营业务关键词 {#get_company_business_keywords}

从中标记录提炼公司主营业务关键词，了解公司实际业务方向。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `company` | str\|int | 公司名或ID |
| `company_url` | str | 知了标讯公司详情页链接 |
| `begin_date` | str | 统计开始日期 |
| `end_date` | str | 统计结束日期 |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `limit` | int | 返回数量，默认10，最大50 |

### 响应结构

```json
{
  "data": {
    "company_name": "华为技术有限公司",
    "keywords": [
      {"keyword": "服务器", "count": 150, "amount": 50000000},
      {"keyword": "交换机", "count": 120, "amount": 30000000}
    ]
  }
}
```

---

## get_company_partners - 合作客户与供应商 {#get_company_partners}

查询公司的合作客户（采购方）和供应商（分包方），分析上下游关系。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company` | str\|int | 否* | 公司名或ID |
| `company_url` | str | 否* | 知了标讯公司详情页链接 |
| `partner_type` | str | **是** | `客户`/`供应商`/`全部` |
| `begin_date` | str | 否 | 统计开始日期 |
| `end_date` | str | 否 | 统计结束日期 |
| `provinces` | list[str] | 否 | 省份列表 |
| `keywords` | list[str] | 否 | 产品关键词过滤 |
| `min_amount` | float | 否 | 最低合作金额，**单位万元**（服务端 ×10000 后与元口径的合作额比较） |
| `limit` | int | 否 | 返回数量，默认20，最大100 |

### 响应结构

```json
{
  "data": {
    "company": "华为技术有限公司",
    "partner_type": "全部",
    "total": 500,
    "partners": [
      {
        "company_name": "中国移动通信集团",
        "cooperation_count": 50,
        "cooperation_amount": 500000000,
        "cooperation_amount_wan": 50000,
        "last_cooperation_time": "2025-01-10",
        "products": ["5G基站", "核心网设备"]
      }
    ]
  }
}
```

### 示例

**查看科大讯飞在教育行业的客户**：
```json
{
  "company": "科大讯飞股份有限公司",
  "partner_type": "客户",
  "keywords": ["教育", "学校"]
}
```

---

## get_company_contacts - 公司项目联系人 {#get_company_contacts}

查询公司的项目联系人信息（招标联系人或中标联系人）。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `company` | str\|int | 公司名或ID |
| `company_url` | str | 知了标讯公司详情页链接 |
| `keywords` | list[str] | 筛选关键词，如 `["呼吸机", "监护仪"]` |
| `match_modes` | list[str] | 搜索范围，默认 `["sm","title"]` |
| `begin_date` | str | 筛选开始日期 |
| `end_date` | str | 筛选截止日期 |
| `role` | int | 1=招标联系人，2=中标联系人，0=全部（默认） |
| `limit` | int | 返回数量，默认5，最大20 |

> 联系电话按账户分层返回：付费账户完整电话；免费/试用账户脱敏（`contact_privacy: "masked"`），提示一次「充值可查看完整联系方式」即可。按返回原样展示，不补全、不成批导出。

### 响应结构

```json
{
  "data": {
    "total": 50,
    "contacts": [
      {
        "phone": "138****1234",
        "name": "张先生",
        "bid_count": 10,
        "last_pub_time": "2025-01-10",
        "last_bid_url": "https://www.zhiliaobiaoxun.com/content/1234567890/b1"
      }
    ]
  }
}
```

---

## find_competitors - 竞争对手分析 {#find_competitors}

基于投标重叠度分析竞争对手列表。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `company` | str\|int | 公司名或ID |
| `company_url` | str | 知了标讯公司详情页链接 |
| `limit` | int | 返回数量，默认10，最大50 |

### 响应结构

```json
{
  "data": {
    "company_name": "目标公司",
    "total_projects": 1000,
    "competitors": [
      {
        "company_name": "竞争对手A",
        "co_bid_count": 80,
        "latest_co_bid_time": "2025-01-05",
        "top_co_bid_products": [{"product": "服务器", "count": 30}],
        "top_co_bid_callers": [{"caller": "中国移动", "count": 20}],
        "top_co_bid_provinces": [{"province": "北京", "count": 25}]
      }
    ]
  }
}
```

**响应分析要点**：
- `co_bid_count`：共同投标次数，越大竞争越激烈
- `top_co_bid_products`：竞争产品领域
- `top_co_bid_callers`：共同争夺的客户
- `top_co_bid_provinces`：竞争活跃地区

---

## find_potential_bidders - 推荐潜在供应商 {#find_potential_bidders}

针对一个招标项目，推荐历史上参与同类项目较多的潜在供应商。

`bid_id`、`bid_url`、`uniq_key`、`project_title` 至少填一个。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `bid_id` | int | 标讯ID（优先使用） |
| `bid_url` | str | 知了标讯公告链接 |
| `uniq_key` | str | 公告唯一标识 |
| `project_title` | str | 项目标题（无ID时可用标题推荐） |
| `bid_type` | str | `招标`/`中标` |
| `limit` | int | 返回数量，默认10，最大50 |

### 响应结构

```json
{
  "data": {
    "project_title": "XX市智慧城市建设项目",
    "bidders": [
      {
        "company_name": "潜在供应商A",
        "source": "历史中标",
        "caller_history_count": 10,
        "caller_history_amount": 5000000,
        "region_win_count": 5,
        "matched_products": ["智慧城市平台"],
        "main_customers": ["深圳市政府"]
      }
    ]
  }
}
```

**响应分析要点**：
- `caller_history_count`：与该采购方的历史合作次数
- `region_win_count`：在该地区的中标次数
- `matched_products`：匹配的产品领域
