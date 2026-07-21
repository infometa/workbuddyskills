# ListTasks

## 接口描述
返回符合查询条件的所有任务（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/tasks

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询 |
| name | 否 | string | 任务标题 | 支持模糊匹配 |
| description | 否 | string | 任务详细描述 | |
| creator | 否 | string | 创建人 | 支持多人员查询 |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | 支持时间查询 |
| status | 否 | string | 状态 | 支持枚举查询 |
| label | 否 | string | 标签查询 | 支持枚举查询 |
| owner | 否 | string | 任务当前处理人 | 支持模糊匹配 |
| cc | 否 | string | 抄送人 | |
| begin | 否 | date | 预计开始 | 支持时间查询 |
| due | 否 | date | 预计结束 | 支持时间查询 |
| story_id | 否 | integer | 关联需求的ID | 支持多ID查询 |
| iteration_id | 否 | integer | 所属迭代的ID | 支持枚举查询 |
| priority | 否 | string | 优先级。推荐使用 priority_label | |
| priority_label | 否 | string | 优先级（推荐） | |
| progress | 否 | integer | 进度 | |
| completed | 否 | datetime | 完成时间 | 支持时间查询 |
| effort_completed | 否 | string | 完成工时 | |
| exceed | 否 | float | 超出工时 | |
| remain | 否 | float | 剩余工时 | |
| effort | 否 | string | 预估工时 | |
| custom_field_* | 否 | string/integer | 自定义字段参数 | 支持枚举查询 |
| limit | 否 | integer | 返回数量限制，默认30，最大200 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

### 任务状态(status)字段说明

| 取值 | 字面值 |
|------|--------|
| open | 未开始 |
| progressing | 进行中 |
| done | 已完成 |

### 任务优先级(priority)字段说明

推荐使用 priority_label 字段。以下取值将不再使用。

| 取值 | 字面值 |
|------|--------|
| 4 | High |
| 3 | Middle |
| 2 | Low |
| 1 | Nice To Have |

## 请求示例

```bash
curl -H 'Authorization: Bearer $TAPD_TOKEN' \
  '${TAPD_API_ENDPOINT}/tasks?workspace_id=$TAPD_WORKSPACE_ID'
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Task": {
                "id": "1020358627854792559",
                "name": "测试2",
                "description": " ",
                "workspace_id": "20358627",
                "creator": "v_xinyucao",
                "created": "2021-06-02 10:36:19",
                "modified": "2022-07-05 15:54:10",
                "status": "open",
                "owner": "",
                "cc": "",
                "begin": null,
                "due": null,
                "story_id": "0",
                "iteration_id": "0",
                "priority": "",
                "progress": "0",
                "completed": null,
                "effort_completed": "0",
                "exceed": "0",
                "remain": "0",
                "effort": "0",
                "has_attachment": "0",
                "release_id": "1020358627100003283",
                "label": null,
                "custom_field_one": null
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
| name | 任务标题 |
| description | 任务详细描述 |
| workspace_id | 项目ID |
| creator | 创建人 |
| created | 创建时间 |
| modified | 最后修改时间 |
| status | 状态 |
| owner | 任务当前处理人 |
| cc | 抄送人 |
| begin | 预计开始 |
| due | 预计结束 |
| release_id | 发布计划ID |
| story_id | 关联需求的ID |
| iteration_id | 所属迭代的ID |
| priority | 优先级 |
| priority_label | 优先级 |
| progress | 进度 |
| completed | 完成时间 |
| effort_completed | 完成工时 |
| exceed | 超出工时 |
| remain | 剩余工时 |
| effort | 预估工时 |
