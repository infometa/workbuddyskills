# 标讯搜索类工具 API 详情

## 目录
- [search_bids - 常规搜索](#search_bids)
- [query_bids_advanced - 高级搜索](#query_bids_advanced)
- [get_bid_detail - 标讯详情](#get_bid_detail)
- [get_bid_timeline - 项目全阶段时间线](#get_bid_timeline)
- [search_expiring_projects - 临期项目](#search_expiring_projects)
- [search_proposed_projects - 拟建项目](#search_proposed_projects)

---

## search_bids - 常规搜索 {#search_bids}

按关键词、地区、金额、时间等条件检索招/中标公告。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keywords` | list[str] | 是 | 搜索关键词，如 `["大模型", "人工智能"]` |
| `match_modes` | list[str] | 否 | 匹配模式，默认 `["all"]` |
| `bid_type` | str | 否 | 公告类型：`招标`/`中标`/`全部`，默认 `全部` |
| `bid_process` | list[int] | 否 | 公告阶段，默认 `[1,2,4,7,8]` |
| `begin_date` | str | 否 | 开始日期 `YYYY-MM-DD` |
| `end_date` | str | 否 | 结束日期 `YYYY-MM-DD` |
| `provinces` | list[str] | 否 | 省份列表，如 `["北京", "广东"]` |
| `cities` | list[str] | 否 | 城市列表 |
| `counties` | list[str] | 否 | 区县列表 |
| `min_amount` | float | 否 | 最低金额，**单位万元**（服务端会 ×10000 转成元再过滤） |
| `max_amount` | float | 否 | 最高金额，**单位万元** |
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20，最大 50 |

### 响应结构

```json
{
  "success": true,
  "data": {
    "total": 150,
    "items": [
      {
        "bid_id": 12345678,
        "title": "XX市智慧城市建设项目",
        "bid_type": "招标",
        "bid_process": 4,
        "pub_time": "2025-01-15",
        "money": 5000000,
        "money_wan": 500,
        "caller_name": "XX市人民政府",
        "winner_names": [],
        "sm_names": ["智慧城市平台", "数据中心建设"],
        "province": "广东",
        "city": "深圳",
        "url": "https://www.zhiliaobiaoxun.com/content/12345678/b1"
      }
    ]
  }
}
```

### 示例

**北京地区AI相关招标**：
```json
{
  "keywords": ["人工智能", "AI"],
  "bid_type": "招标",
  "provinces": ["北京"],
  "begin_date": "2025-01-01"
}
```

---

## query_bids_advanced - 高级搜索 {#query_bids_advanced}

支持所有 `search_bids` 参数，扩展支持关键词分组、排除词、复杂逻辑。

### 扩展参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `keyword_groups` | list[dict] | 关键词组，每个组与主keywords为AND关系 |
| `exclude_keywords` | list[str] | 排除关键词，匹配任一则排除 |
| `sort_field` | str | 排序字段，默认 `pub_time` |
| `sort_order` | str | 排序方向 `asc`/`desc`，默认 `desc` |

**注意**：`query_bids_advanced` 金额参数名为 `min_money`/`max_money`（不是 min_amount/max_amount），
且**单位是元**，与 `search_bids` 的万元不同。传错参数名不会报错，会被静默忽略（表现为筛选没生效）。

### keyword_groups 结构

```json
{
  "keywords": ["关键词A", "关键词B"],
  "match_modes": ["sm", "title"]
}
```

### 使用示例

**复合查询 - 广东深圳，财产/资产类险种投保项目**：
```json
{
  "keywords": ["财产", "资产"],
  "keyword_groups": [
    {
      "keywords": ["险"],
      "match_modes": ["title"]
    }
  ],
  "provinces": ["广东"],
  "cities": ["深圳"],
  "bid_type": "招标"
}
```

**搜索服务器/大模型，排除运维耗材**：
```json
{
  "keywords": ["服务器", "大模型"],
  "exclude_keywords": ["运维", "耗材", "维保"],
  "bid_process": [7, 8]
}
```

**查询A公司和B公司共同参与的项目**：
```json
{
  "keywords": ["华为技术有限公司"],
  "match_modes": ["winner", "tender"],
  "keyword_groups": [
    {
      "keywords": ["中兴通讯"],
      "match_modes": ["winner", "tender"]
    }
  ]
}
```

**查询某公司中标的特定产品**：
```json
{
  "keywords": ["阿里云"],
  "match_modes": ["winner"],
  "keyword_groups": [
    {
      "keywords": ["云存储", "云服务器", "云数据库"],
      "match_modes": ["sm", "title"]
    }
  ]
}
```

---

## get_bid_detail - 标讯详情 {#get_bid_detail}

根据 `bid_id`、`bid_url` 或 `uniq_key` 获取单条标讯完整详情及正文（三者至少填一个）。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `bid_id` | int | 标讯ID（优先使用） |
| `bid_url` | str | 知了标讯公告链接 |
| `uniq_key` | str | 公告唯一标识 |
| `bid_type` | int | 1=招标 2=中标（可选，加速查询） |

### 扩展响应字段

| 字段 | 说明 |
|------|------|
| `county` | 区县 |
| `agency_name` | 代理机构 |
| `source` | 信息来源 |
| `service_end_date` | 服务截止日期 |
| `fulltext` | 公告原文 |

### 示例

```json
// 根据ID获取
{"bid_id": 12345678}

// 根据URL获取
{"bid_url": "https://www.zhiliaobiaoxun.com/content/1234567890/b1"}
```

---

## get_bid_timeline - 项目全阶段时间线 {#get_bid_timeline}

给一条标讯，返回**同一项目所有阶段的公告**，按时间正序排列。
用于回答「这个项目后来怎么样了」「改过几次」「从发标到定标花了多久」
「中标候选人和最终中标是不是同一家」。

**请求**：`POST /api_v2/get_bid_timeline`

```json
{"bid_id": 484460619, "bid_type": 2}
```

也可以直接传知了标讯链接，工具会自行解析出 `bid_id` 与 `bid_type`：

```json
{"bid_url": "https://www.zhiliaobiaoxun.com/content/xxx/b1"}
```

| 参数 | 说明 |
|---|---|
| `bid_id` | 标讯 ID，与 `bid_url` 二选一 |
| `bid_type` | 1=招标类公告，2=中标类公告；传 `bid_id` 时必填 |
| `bid_url` | 知了标讯详情页链接，可替代上面两个参数 |

**返回**：字段结构同 `search_bids`，按 `pub_time` 升序。
典型阶段顺序：采购意向 → 招标公告 → 变更公告 → 中标候选人 → 中标结果 → 合同。

> 项目没有其他阶段公告时返回 `total=0`（不计费）。
> 这不代表项目不存在，只说明该项目目前只有这一条公告。

---

## search_expiring_projects - 临期项目 {#search_expiring_projects}

查询即将到期的周期性项目，用于商机预测和续期机会挖掘。

### 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `keywords` | list[str] | 必填，产品/服务关键词 |
| `begin_date` | str | 到期开始日期，默认今天 |
| `end_date` | str | 到期结束日期，**默认今天起 180 天后** |
| `provinces` | list[str] | 省份列表 |
| `cities` | list[str] | 城市列表 |
| `counties` | list[str] | 区县列表 |
| `min_amount` | float | 最低金额，**单位万元** |
| `company_type` | list[str] | 招标公司类型，如 `["学校", "医院"]` |
| `page` | int | 页码，默认 1 |
| `page_size` | int | 每页数量，默认 20 |

### 扩展响应字段

| 字段 | 说明 |
|------|------|
| `days_until_expiry` | 距离到期天数（越小越紧急） |
| `service_end_date` | 服务截止日期 |
| `caller_name` | 潜在续约客户 |
| `money` | 历史项目金额，可参考报价 |

### 示例

**北京地区职工体检服务临期项目**：
```json
{
  "keywords": ["职工体检"],
  "provinces": ["北京"]
}
```

**90天内到期的医院物业管理项目**：
```json
{
  "keywords": ["物业管理"],
  "company_type": ["医院"],
  "end_date": "2026-07-28"
}
```

---

## search_proposed_projects - 拟建项目 {#search_proposed_projects}

查询还在**立项审批阶段**的项目，比招标公告早 6-18 个月。
用于回答「有哪些项目正在立项」「哪些还没发标但快了」这类需要提前布局的问题。

**请求**：`POST /api_v2/search_proposed_projects`

```json
{
  "keywords": ["智慧校园"],
  "provinces": ["广东"],
  "cities": ["深圳"],
  "min_amount": 100,
  "begin_date": "2026-04-01",
  "approval_status_code": 3,
  "match_type": 0,
  "page_size": 20
}
```

| 参数 | 说明 |
|---|---|
| `keywords` | 搜索关键词，字符串或列表 |
| `approval_status_code` | 1=未审批 2=审批中 3=办结（通过） 4=审批未通过 5=撤销 6=其他；0/不传=全部。**办结的最接近落地** |
| `match_type` | 0=标题智能匹配（默认，匹配项目名+立项单位），3=全文匹配（连带返回正文） |
| `min_amount` / `max_amount` | **单位万元**（拟建索引金额字段本身即万元，不做转换） |
| `provinces` / `cities` | 地区筛选 |
| `begin_date` / `end_date` | 发布日期范围，YYYY-MM-DD |

**返回关键字段**：`project_name`（项目名）、`project_code`（发改委项目代码）、
`caller_name`（立项单位）、`money` / `money_format`、`approval_status`、`pub_time`、
`url`（带 sk 免登录参数，可直接点击）。

> **金额单位**：本工具、`search_expiring_projects`、`search_bids`、`get_company_partners` 都用**万元**；
> `query_bids_advanced`、`aggregate_bids_advanced`、Top 类工具用**元**。完整对照见 SKILL.md 的金额单位速查表。
>
> **`money_format` 暂不可靠**：拟建索引的 `money` 本身是万元，但服务端格式化时按元又除了一次 10000，
> 会把「500 万」显示成「500元」。**请用 `money` 原值自行按万元展示，不要直接引用 `money_format`。**
