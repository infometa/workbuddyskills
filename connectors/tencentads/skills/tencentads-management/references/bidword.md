# 关键词管理（bidword）

---

## add.mjs — 创建关键词

```bash
node scripts/bidword/add.mjs '{"account_id":"123456789","list":[{"adgroup_id":987654321,"bidword":"游戏下载","match_type":"PHRASE_MATCH"},{"adgroup_id":987654321,"bidword":"手机游戏","match_type":"EXACT_MATCH","bid_price":500}]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `list` | struct[] | 关键词列表（最少 1 条，最多 1000 条） |

**list 每项字段**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `adgroup_id` | int64 | 是 | 广告 ID |
| `bidword` | string | 是 | 关键词词面（最大 20 等宽字符 / 60 字节） |
| `match_type` | enum | 是 | 匹配方式：`EXACT_MATCH`（精确匹配）、`WIDE_MATCH`（广泛匹配）、`WORD_MATCH`（词匹配）、`PHRASE_MATCH`（短语匹配） |
| `bid_price` | integer | 否 | 关键词出价（分），1-99999 |
| `use_group_price` | enum | 否 | 是否使用组出价：`USE_GROUP_PRICE`、`NOT_USE_GROUP_PRICE` |
| `configured_status` | enum | 否 | 暂停状态：`KEYWORD_STATUS_NORMAL`、`KEYWORD_STATUS_SUSPEND` |
| `dynamic_creative_id` | integer | 否 | 广告创意 ID |
| `pc_landing_page_info` | struct | 否 | 关键词落地页信息 |

**返回**：`{ "success": true, "success_list": [{ "index": 0, "bidword_id": 123, "bidword": "...", ... }], "error_list": [...] }`

---

## update.mjs — 更新关键词

```bash
node scripts/bidword/update.mjs '{"account_id":"123456789","list":[{"bidword_id":123,"bid_price":600},{"bidword_id":456,"match_type":"EXACT_MATCH","configured_status":"KEYWORD_STATUS_SUSPEND"}]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `list` | struct[] | 要更新的关键词列表（最少 1 条，最多 1000 条） |

**list 每项字段**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `bidword_id` | integer | 是 | 关键词 ID |
| `bid_price` | integer | 否 | 关键词出价（分），1-99999 |
| `bid_mode` | enum | 否 | 出价方式：`BID_MODE_CPC`、`BID_MODE_CPM`、`BID_MODE_OCPC`、`BID_MODE_OCPM` 等 |
| `use_group_price` | enum | 否 | 是否使用组出价：`USE_GROUP_PRICE`、`NOT_USE_GROUP_PRICE` |
| `price_update_type` | enum | 否 | 出价修改类型：`RAISE_PRICE_VALUE`、`RAISE_PRICE_PERCENT` |
| `raise_price` | integer | 否 | 出价修改幅度（-99999 到 99999） |
| `match_type` | enum | 否 | 匹配方式：`EXACT_MATCH`、`WIDE_MATCH`、`WORD_MATCH`、`PHRASE_MATCH` |
| `configured_status` | enum | 否 | 暂停状态：`KEYWORD_STATUS_NORMAL`、`KEYWORD_STATUS_SUSPEND` |
| `dynamic_creative_id` | integer | 否 | 广告创意 ID |
| `pc_landing_page_info` | struct | 否 | 关键词落地页信息 |

**返回**：`{ "success": true, "success_list": [{ "index": 0, "bidword_id": 123, ... }], "error_list": [...] }`

---

## delete.mjs — 删除关键词

```bash
node scripts/bidword/delete.mjs '{"account_id":"123456789","list":[123,456]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |
| `list` | integer[] | 要删除的关键词 ID 列表（最少 1 条，最多 1000 条） |

**返回**：`{ "success": true, "success_list": [{ "index": 0, "bidword_id": 123, ... }], "error_list": [...] }`

---

## get.mjs — 查询关键词

```bash
node scripts/bidword/get.mjs '{"account_id":"123456789","filtering":[{"field":"adgroup_id","operator":"EQUALS","values":["987654321"]}]}'
```

**必填参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `account_id` | integer | 广告主账号 ID |

**可选参数**：
| 参数 | 类型 | 说明 |
|------|------|------|
| `filtering` | struct[] | 过滤条件，支持字段：`bidword_id`、`adgroup_id`、`campaign_id`、`bidword`、`match_type`、`created_time`、`last_modified_time`、`delete_time`、`configured_status`、`bidword_status` |
| `fields` | string[] | 指定返回字段 |
| `page` | integer | 页码（默认 1） |
| `page_size` | integer | 每页条数（默认 20，最大 100） |

**返回**：
```json
{
  "list": [
    {
      "bidword_id": 123,
      "adgroup_id": 987654321,
      "bidword": "游戏下载",
      "match_type": "PHRASE_MATCH",
      "bid_price": 500,
      "configured_status": "KEYWORD_STATUS_NORMAL"
    }
  ],
  "page_info": { "page": 1, "page_size": 20, "total_number": 1, "total_page": 1 }
}
```

---

## 匹配方式说明

| 匹配方式 | 枚举值 | 说明 |
|---------|--------|------|
| 精确匹配 | `EXACT_MATCH` | 搜索词与关键词完全一致时触发 |
| 广泛匹配 | `WIDE_MATCH` | 搜索词包含关键词的同义词、相关词均可触发 |
| 词匹配 | `WORD_MATCH` | 搜索词包含关键词时触发 |
| 短语匹配 | `PHRASE_MATCH` | 搜索词包含关键词或其近义变体时触发 |
