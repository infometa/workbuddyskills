# CountComments

## 接口描述
计算符合查询条件的评论数量并返回。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/comments/count

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 只返回评论数量

### 请求参数

| 参数名 | 必选 | 类型 | 说明 | 特殊规则 |
|--------|------|------|------|----------|
| workspace_id | 是 | integer | 项目ID | |
| id | 否 | integer | 评论ID | 支持多ID查询 |
| title | 否 | string | 标题 | |
| description | 否 | string | 内容 | |
| author | 否 | string | 评论人 | |
| entry_type | 否 | string | 评论类型（取值见下方说明，多个类型间以竖线隔开） | 支持枚举查询 |
| entry_id | 否 | integer | 评论所依附的业务对象实体ID | |
| created | 否 | datetime | 创建时间 | 支持时间查询 |
| modified | 否 | datetime | 最后更改时间 | 支持时间查询 |

### entry_type 取值说明

| 取值 | 说明 |
|------|------|
| stories | 需求评论 |
| bug | 缺陷评论 |
| bug_remark | 流转缺陷时的评论 |
| tasks | 任务评论 |
| wiki | Wiki 评论 |

多个类型间以竖线 `|` 隔开，如 `entry_type=bug|bug_remark`。

## 请求示例

```bash
# 获取项目下评论总数
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments/count?workspace_id=$TAPD_WORKSPACE_ID"

# 获取某条缺陷的评论数量
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments/count?workspace_id=$TAPD_WORKSPACE_ID&entry_type=bug&entry_id=1010104801074085199"

# 获取某用户的评论数量
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments/count?workspace_id=$TAPD_WORKSPACE_ID&author=username"
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "count": 61
    },
    "info": "success"
}
```
