# ListComments

## 接口描述
返回符合查询条件的所有评论（分页显示，默认一页30条）。

## 请求信息

**请求方法：** GET

**请求地址：** ${TAPD_API_ENDPOINT}/comments

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 默认返回30条，可通过 limit 参数设置，最大200。也可传 page 参数翻页。

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
| root_id | 否 | integer | 根评论ID | |
| reply_id | 否 | integer | 评论回复的ID | |
| limit | 否 | integer | 返回数量限制，默认30，最大200 | |
| page | 否 | integer | 页码，默认1 | |
| order | 否 | string | 排序规则，如 created%20desc | |
| fields | 否 | string | 返回字段，逗号分隔 | |

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
# 获取项目下所有评论
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments?workspace_id=$TAPD_WORKSPACE_ID"

# 获取某条需求的评论
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments?workspace_id=$TAPD_WORKSPACE_ID&entry_type=stories&entry_id=1131372104001000001&limit=200"

# 获取某条缺陷的评论（含流转评论）
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/comments?workspace_id=$TAPD_WORKSPACE_ID&entry_type=bug|bug_remark&entry_id=1010104801074085199&limit=200"
```

## 返回示例

```json
{
    "status": 1,
    "data": [
        {
            "Comment": {
                "id": "1010104801048492751",
                "title": "流转状态从 [规划中] 到 [实现中] 添加",
                "description": "<b><i><u>adfasd</u></i></b>",
                "author": "v_xuanfang",
                "entry_type": "stories",
                "entry_id": "1010104801858505231",
                "created": "2020-06-09 10:51:06",
                "modified": "2020-06-09 10:51:06",
                "workspace_id": "10104801"
            }
        }
    ],
    "info": "success"
}
```

### 返回字段说明

| 字段 | 说明 |
|------|------|
| id | 评论ID |
| title | 标题 |
| description | 内容（HTML 富文本） |
| author | 评论人 |
| entry_type | 评论类型 |
| entry_id | 评论所依附的业务对象实体ID |
| created | 创建时间 |
| modified | 最后更改时间 |
| workspace_id | 项目ID |
| root_id | 根评论ID（0 表示自身为根评论） |
| reply_id | 评论回复的ID（0 表示非回复） |

### 评论树结构说明

- `root_id = 0` 且 `reply_id = 0`：根评论（一级评论）
- `root_id != 0`：属于某个评论线程，`root_id` 指向线程的根评论
- `reply_id != 0`：回复某条具体评论，`reply_id` 指向被回复的评论
