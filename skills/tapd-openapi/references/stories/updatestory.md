# UpdateStory

## 接口描述
更新需求，返回需求更新后的数据。每次只允许更新一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/stories

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 每次只允许更新一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| id | 是 | integer | 需求ID |
| workspace_id | 是 | integer | 项目ID |
| name | 否 | string | 标题 |
| priority_label | 否 | string | 优先级（推荐），如 High / Middle / Low 或中文值 |
| priority | 否 | string | 优先级（已废弃，请用 priority_label） |
| business_value | 否 | integer | 业务价值 |
| status | 否 | string | 状态（使用并行工作流时，按状态重置更新节点） |
| v_status | 否 | string | 状态（支持传入中文状态名称） |
| version | 否 | string | 版本 |
| module | 否 | string | 模块 |
| test_focus | 否 | string | 测试重点 |
| size | 否 | integer | 规模 |
| owner | 否 | string | 处理人 |
| current_user | 否 | string | 变更人 |
| cc | 否 | string | 抄送人 |
| developer | 否 | string | 开发人员 |
| begin | 否 | date | 预计开始（格式：YYYY-MM-DD） |
| due | 否 | date | 预计结束（格式：YYYY-MM-DD） |
| iteration_id | 否 | string | 迭代ID |
| effort | 否 | string | 预估工时 |
| effort_completed | 否 | string | 完成工时 |
| remain | 否 | float | 剩余工时 |
| exceed | 否 | float | 超出工时 |
| category_id | 否 | integer | 需求分类 |
| release_id | 否 | integer | 发布计划 |
| source | 否 | string | 来源 |
| type | 否 | string | 类型 |
| description | 否 | string | 详细描述（支持 HTML） |
| is_auto_close_task | 否 | integer | 需求流转到结束状态时是否自动关闭关联任务，传 1 自动关闭，默认 0 |
| label | 否 | string | 标签，多个用英文竖线分隔，不存在时自动创建 |
| custom_field_* | 否 | string/integer | 自定义字段，具体字段名通过「获取需求自定义字段配置」接口获取 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数 |
| cus_{自定义字段别名} | 否 | string | 自定义字段（后台自动转义为 custom_field_*） |

## 请求示例

```bash
# 更新需求优先级和处理人
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/stories" \
  -d '{
    "id": "需求ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "priority_label": "High",
    "owner": "username"
  }'

# 更新需求状态和描述
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/stories" \
  -d '{
    "id": "需求ID",
    "workspace_id": "'"$TAPD_WORKSPACE_ID"'",
    "status": "in_progress",
    "description": "<div>更新后的描述</div>"
  }'
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Story": {
            "id": "1010104801125341253",
            "name": "需求标题",
            "workspace_id": "10104801",
            "status": "planning",
            "owner": "anyechen;",
            "priority": "高",
            "modified": "2025-07-08 14:51:25"
        }
    },
    "info": "success"
}
```

## 注意事项

- `id` 和 `workspace_id` 为必传字段，其余字段按需传入，未传字段不会被修改
- `priority` 字段已废弃，请统一使用 `priority_label`
- `status` 与 `v_status` 二选一，`v_status` 支持中文状态名
- 需求流转到结束状态时，可通过 `is_auto_close_task=1` 自动关闭关联任务
- `label` 中不存在的标签会自动创建，多个标签用英文竖线 `|` 分隔
