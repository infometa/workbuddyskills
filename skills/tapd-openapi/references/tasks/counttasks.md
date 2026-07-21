# CountTasks

## 接口描述
计算符合查询条件的任务数量并返回。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/tasks/count

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 只返回任务数量

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | ID | 支持多ID查询、模糊匹配 |
| name | 否 | string | 任务标题 | 支持模糊匹配 |
| description | 否 | string | 任务详细描述 | |
| creator | 否 | string | 创建人 | 支持模糊匹配 |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后修改时间 | |
| status | 否 | string | 状态 | 支持枚举查询 |
| label | 否 | string | 标签查询 | 支持枚举查询 |
| owner | 否 | string | 任务当前处理人 | 支持模糊匹配 |
| cc | 否 | string | 抄送人 | |
| begin | 否 | date | 预计开始 | 支持时间查询 |
| due | 否 | date | 预计结束 | 支持时间查询 |
| story_id | 否 | integer | 关联需求的ID | 支持多ID查询 |
| iteration_id | 否 | integer | 所属迭代的ID | |
| priority | 否 | string | 优先级。推荐使用 priority_label | |
| priority_label | 否 | string | 优先级（推荐） | |
| progress | 否 | integer | 进度 | |
| completed | 否 | datetime | 完成时间 | 支持时间查询 |
| effort_completed | 否 | string | 完成工时 | |
| exceed | 否 | float | 超出工时 | |
| remain | 否 | float | 剩余工时 | |
| effort | 否 | string | 预估工时 | |
| custom_field_* | 否 | string/integer | 自定义字段参数，具体字段名通过「获取任务自定义字段配置」接口获取 | 支持枚举查询 |

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
# 获取项目下的任务数量
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/tasks/count?workspace_id=$TAPD_WORKSPACE_ID"

# 获取指定处理人、进行中的任务数量
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/tasks/count?workspace_id=$TAPD_WORKSPACE_ID&owner=username&status=progressing"
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 1
    },
    "info": "success"
}
```
