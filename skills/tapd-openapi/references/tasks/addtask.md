# AddTask

## 接口描述
在项目下创建一条任务（Task），一次只能插入一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/tasks

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 一次插入一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| name | 是 | string | 任务标题 |
| description | 否 | string | 详细描述（支持 HTML） |
| creator | 否 | string | 创建人 |
| owner | 否 | string | 处理人 |
| cc | 否 | string | 抄送人 |
| begin | 否 | date | 预计开始（格式：YYYY-MM-DD） |
| due | 否 | date | 预计结束（格式：YYYY-MM-DD） |
| story_id | 否 | integer | 关联需求ID |
| iteration_id | 否 | integer | 所属迭代ID |
| priority_label | 否 | string | 优先级（推荐），如 High / Middle / Low / Nice To Have |
| priority | 否 | string | 优先级（已废弃，请用 priority_label） |
| effort | 否 | string | 预估工时 |
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
# 创建最简任务
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tasks" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "任务标题"
  }'

# 创建带完整信息的任务
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/tasks" \
  -d '{
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "name": "任务标题",
    "owner": "username",
    "priority_label": "High",
    "story_id": "关联需求ID",
    "iteration_id": "迭代ID",
    "begin": "2026-03-10",
    "due": "2026-03-31",
    "effort": "8",
    "description": "<div>任务详细描述</div>"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Task": {
            "id": "1010158231500600411",
            "name": "任务标题",
            "workspace_id": "10158231",
            "creator": "api_doc_oauth",
            "created": "2019-06-27 11:02:14",
            "modified": "2019-06-27 11:02:14",
            "status": null,
            "owner": null,
            "story_id": "0",
            "iteration_id": "0",
            "priority": "",
            "progress": "0",
            "effort": "0",
            "label": "",
            "created_from": "api"
        }
    },
    "info": "success"
}
```

## 注意事项

- `priority` 字段已废弃，请统一使用 `priority_label`
- `label` 中不存在的标签会自动创建，多个标签用英文竖线 `|` 分隔
- `description` 支持 HTML 富文本格式
- `status` 动态可选值需通过「获取任务所有字段及候选值」接口获取
