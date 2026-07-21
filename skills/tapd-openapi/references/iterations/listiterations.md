# ListIterations

## 接口描述
返回符合查询条件的所有迭代（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/iterations

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| name | 否 | string | 标题 | 支持模糊匹配 |
| description | 否 | string | 详细描述 | |
| startdate | 否 | date | 开始时间 | 支持时间查询 |
| enddate | 否 | date | 结束时间 | 支持时间查询 |
| workitem_type_id | 否 | integer | 迭代类别 | |
| plan_app_id | 否 | integer | 计划应用ID | |
| status | 否 | string | 状态（系统状态open/done，自定义状态可传中文） | |
| creator | 否 | string | 创建人 | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |
| completed | 否 | datetime | 完成时间 | |
| locker | 否 | string | 锁定人 | |
| custom_field_* | 否 | string/integer | 自定义字段参数 | |
| limit | 否 | integer | 返回数量限制，默认30 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

### 迭代状态(status)字段说明

自定义状态可以直接传中文字符。

| 字段值 | 状态名 |
|--------|--------|
| open | 开启 |
| done | 已关闭 |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/iterations?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Iteration": {
                "id": "1010158231000388075",
                "name": "迭代2",
                "workspace_id": "10158231",
                "startdate": "2017-06-26",
                "enddate": "2017-07-07",
                "status": "open",
                "release_id": null,
                "description": "熟悉敏捷迭代开发",
                "creator": "anyechen",
                "created": "2017-06-20 16:49:05",
                "modified": "2017-06-20 16:49:05",
                "completed": null,
                "custom_field_1": null,
                "custom_field_2": null,
                "custom_field_3": null,
                "custom_field_4": null,
                "custom_field_5": null
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | ID |
| name | 标题 |
| workspace_id | 项目ID |
| description | 详细描述 |
| startdate | 开始时间 |
| enddate | 结束时间 |
| status | 状态 |
| creator | 创建人 |
| created | 创建时间 |
| modified | 最后修改时间 |
| completed | 完成时间 |
| lock_info | 锁定内容 |
| locker | 锁定人 |
| workitem_type_id | 迭代类别 |
| plan_app_id | 计划应用ID |
