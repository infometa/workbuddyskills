# UpdateTask

## 接口描述
更新任务，返回任务更新后的数据。每次只允许更新一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/tasks

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只允许更新一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| id | 是 | integer | 任务ID |
| workspace_id | 是 | integer | 项目ID |
| name | 否 | string | 任务标题 |
| description | 否 | string | 详细描述（支持 HTML） |
| creator | 否 | string | 创建人 |
| status | 否 | string | 状态：open / progressing / done |
| owner | 否 | string | 处理人 |
| current_user | 否 | string | 操作人 |
| cc | 否 | string | 抄送人 |
| begin | 否 | date | 预计开始（格式：YYYY-MM-DD） |
| due | 否 | date | 预计结束（格式：YYYY-MM-DD） |
| story_id | 否 | integer | 关联需求ID |
| iteration_id | 否 | integer | 所属迭代ID |
| priority_label | 否 | string | 优先级（推荐），如 High / Middle / Low / Nice To Have |
| priority | 否 | string | 优先级（已废弃，请用 priority_label） |
| effort | 否 | string | 预估工时 |
| auto_complete_effort | 否 | integer | 传 1 时，状态流转到 done 则自动补齐工时 |
| label | 否 | string | 标签，多个用英文竖线分隔，不存在时自动创建 |
| custom_field_* | 否 | string/integer | 自定义字段，具体字段名通过「获取任务自定义字段配置」接口获取 |
| cus_{自定义字段别名} | 否 | string | 自定义字段（后台自动转义为 custom_field_*） |

### 常用字段候选值

**status（状态）**

| 取值 | 说明 |
|------|------|
| open | 未开始 |
| progressing | 进行中 |
| done | 已完成 |

## 请求示例

```bash
# 更新任务状态为已完成
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tasks" \
  -d '{
    "id": "任务ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "status": "done",
    "current_user": "username"
  }'

# 更新任务处理人和预计时间
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tasks" \
  -d '{
    "id": "任务ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "owner": "username",
    "begin": "2026-03-10",
    "due": "2026-03-31",
    "priority_label": "High"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Task": {
            "id": "1010158231500600385",
            "name": "检查数据库",
            "workspace_id": "10158231",
            "status": "done",
            "owner": null,
            "priority": "",
            "progress": "0",
            "completed": "2019-06-27 11:05:26",
            "effort": "0",
            "modified": "2019-06-27 11:05:27"
        }
    },
    "info": "success"
}
```

## 注意事项

- `id` 和 `workspace_id` 为必传字段，其余字段按需传入，未传字段不会被修改
- `priority` 字段已废弃，请统一使用 `priority_label`
- `auto_complete_effort=1` 配合 `status=done` 使用，可自动将剩余工时补齐为完成工时
- `label` 中不存在的标签会自动创建，多个标签用英文竖线 `|` 分隔
