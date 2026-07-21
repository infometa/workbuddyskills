# GetRelatedBugs

## 接口描述
返回符合查询条件的所有需求关联的缺陷ID。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/stories/get_related_bugs

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回所有关系

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| story_id | 是 | integer | 需求ID | 支持多ID查询 |

## 请求示例

```bash
# 获取某条需求关联的所有缺陷
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/stories/get_related_bugs?workspace_id=$TAPD_WORKSPACE_ID&story_id=需求ID"
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "workspace_id": 10104801,
            "story_id": "1010104801866181263",
            "bug_id": "1010104801083691309"
        },
        {
            "workspace_id": 10104801,
            "story_id": "1010104801866181263",
            "bug_id": "1010104801085894269"
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| workspace_id | 项目ID |
| story_id | 需求ID |
| bug_id | 缺陷ID |
