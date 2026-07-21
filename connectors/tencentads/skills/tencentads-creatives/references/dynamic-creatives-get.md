# 获取动态创意 (dynamic_creatives/get)


## 请求参数

### 必需参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| account_id | integer | 广告主账号ID |

### 可选参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| filtering | struct[] | 过滤条件，最多10项 |
| fields | string[] | 指定返回字段列表 |
| page | integer | 页码，默认1，范围1-100 |
| page_size | integer | 每页条数，默认10，范围1-100 |
| is_deleted | boolean | 是否查询已删除创意，默认false |
| pagination_mode | enum | 分页方式：`PAGINATION_MODE_NORMAL`（默认）或 `PAGINATION_MODE_CURSOR` |
| cursor | string | 游标值，`pagination_mode=CURSOR` 时使用 |

---

## filtering 支持的字段

| field | 支持的 operator | 说明 |
|-------|----------------|------|
| `dynamic_creative_id` | `EQUALS`, `IN` | 创意ID |
| `dynamic_creative_name` | `EQUALS`, `CONTAINS` | 创意名称 |
| `adgroup_id` | `EQUALS`, `IN` | 广告组ID |
| `configured_status` | `IN` | 配置状态 |
| `created_time` | `LESS_EQUALS`, `GREATER_EQUALS` | 创建时间（时间戳） |
| `last_modified_time` | `LESS_EQUALS`, `GREATER_EQUALS` | 最后修改时间（时间戳） |
| `component_id` | `IN` | 包含该组件ID的创意 |
| `source` | `IN` | 来源 |

---

## fields 可用字段

| 字段名 | 说明 |
|--------|------|
| `dynamic_creative_id` | 创意ID |
| `adgroup_id` | 广告组ID |
| `dynamic_creative_name` | 创意名称 |
| `creative_template_id` | 创意形式ID（0表示不指定） |
| `delivery_mode` | 投放模式 |
| `dynamic_creative_type` | 创意形式匹配方式 |
| `creative_components` | 创意组件内容（结构与 add 接口相同） |
| `configured_status` | 配置状态：`AD_STATUS_NORMAL` / `AD_STATUS_SUSPEND` |
| `created_time` | 创建时间（时间戳） |
| `last_modified_time` | 最后修改时间（时间戳） |
| `impression_tracking_url` | 曝光监测URL |
| `click_tracking_url` | 点击监测URL |

---

## 响应结构

```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "dynamic_creative_id": 8362490722,
        "adgroup_id": 987654321,
        "dynamic_creative_name": "创意名称_20240324",
        "creative_template_id": 0,
        "delivery_mode": "DELIVERY_MODE_COMPONENT",
        "dynamic_creative_type": "DYNAMIC_CREATIVE_TYPE_PROGRAM",
        "configured_status": "AD_STATUS_NORMAL",
        "creative_components": {
          "video": [{ "component_id": 1905866436402 }],
          "brand": [{ "component_id": 1895897993168 }],
          "description": [{ "value": { "content": "广告文案" } }],
          "action_button": [{ "component_id": 1895897993170 }],
          "main_jump_info": [{ "component_id": 1906127499786 }]
        }
      }
    ],
    "page_info": {
      "page": 1,
      "page_size": 10,
      "total_number": 1,
      "total_page": 1
    }
  }
}
```

---

## 常见错误

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数缺失或格式错误 |
| 40006 | account_id 不存在 |
