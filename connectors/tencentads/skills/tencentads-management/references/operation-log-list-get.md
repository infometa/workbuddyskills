# 操作日志查询（query-operation-logs.mjs）

查询广告/创意对象的操作日志，返回每次操作（新建/修改）前后的字段变化详情。

## 调用方式

```bash
node scripts/query-operation-logs.mjs '<JSON 参数>'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `account_id` | string/integer | **是** | 广告主帐号 id，不支持代理商 id |
| `operation_object_type` | enum | **是** | 操作对象类型，**枚举值只允许以下三者之一**：`"OPERATION_OBJECT_TYPE_ADGROUP"`（广告）、`"OPERATION_OBJECT_TYPE_DYNAMIC_CREATIVE"`（创意）、`"OPERATION_OBJECT_TYPE_JOINT_BUDGET"`（联合预算） |
| `start_date` | string | **是** | 开始日期，格式 `YYYY-MM-DD`，不支持查询 3 个月前的数据 |
| `end_date` | string | **是** | 结束日期，格式 `YYYY-MM-DD`，与 `start_date` 时间差不超过 1 个月 |
| `object_id` | integer | 否 | 指定查询的对象 id（广告 id 或创意 id），不传则返回账户下所有对象的日志 |
| `operation_action_list` | string[] | 否 | 操作动作过滤，如 `["新建"]`、`["修改"]`，数组长度 1-2 |
| `operator_platform_list` | string[] | 否 | 操作平台过滤，如 `["投放管理平台"]`，数组长度 1-10 |
| `page` | integer | 否 | 页码，最大 100，默认 1 |
| `page_size` | integer | 否 | 每页条数，最大 100，默认 20 |

## 使用示例

#### 查询指定广告的操作日志

```bash
node scripts/query-operation-logs.mjs '{"account_id":"25610","operation_object_type":"OPERATION_OBJECT_TYPE_ADGROUP","object_id":103519996520,"start_date":"2026-05-19","end_date":"2026-05-25"}'
```

#### 只查新建操作

```bash
node scripts/query-operation-logs.mjs '{"account_id":"25610","operation_object_type":"OPERATION_OBJECT_TYPE_ADGROUP","start_date":"2026-05-19","end_date":"2026-05-25","operation_action_list":["新建"]}'
```

## 输出说明

```json
{
  "list": [
    {
      "operation_object_id": 103519996520,
      "operation_object_name": "广告名称",
      "operation_action": "新建",
      "fronted_operator": "QQ(2849246071)",
      "fronted_operator_type": "客户",
      "fronted_operator_platform": "投放管理平台",
      "created_time": "2026-05-25 16:26:03",
      "operation_log": [
        { "name": "广告名称", "before": null, "after": "商品销售广告_05_25" },
        { "name": "出价", "before": "100元", "after": "187.9元" }
      ],
      "adtarget": [...],
      "adcreative": []
    }
  ],
  "page_info": { "page": 1, "page_size": 20, "total_num": 1, "total_page": 1 }
}
```

- `operation_log`：操作前后字段变化列表，`before` 为修改前值（新建操作时为 `null`），`after` 为修改后值
- `adtarget`：同次操作关联的定向变更子列表
- `adcreative`：同次操作关联的创意变更子列表
