# AddComment

## 接口描述
在业务对象（需求、缺陷、任务等）下添加一条评论，一次只能插入一条数据。

## 请求信息

**请求方法：** POST

**请求地址：** ${TAPD_API_ENDPOINT}/comments

**支持格式：** JSON/XML（默认 JSON）

**请求数限制：** 一次插入一条数据

### 请求参数

| 参数名 | 必选 | 类型 | 说明 |
|--------|------|------|------|
| workspace_id | 是 | integer | 项目ID |
| description | 是 | string | 内容（**必须使用 HTML 富文本**，如 `<p>内容</p>`，markdown 不会正确渲染） |
| author | 是 | string | 评论人 |
| entry_type | 是 | string | 评论类型：bug / bug_remark / stories / tasks |
| entry_id | 是 | integer | 评论所依附的业务对象实体ID |
| root_id | 否 | integer | 根评论ID（回复评论线程时必填） |
| reply_id | 否 | integer | 被回复的评论ID（回复某条评论时必填） |

### entry_type 取值说明

| 取值 | 说明 |
|------|------|
| stories | 需求评论 |
| bug | 缺陷评论 |
| bug_remark | 流转缺陷时的评论 |
| tasks | 任务评论 |

## @提及（触发通知）

在 `description` 中使用以下 HTML 标签可触发 @通知：

```html
<b class="at-who" contenteditable="false" data-userid="用户ID" data-type="user">@用户名</b>
```

**必需属性：**

| 属性 | 值 | 说明 |
|------|----|------|
| class | `at-who` | 标识 @提及，缺少则不触发通知 |
| contenteditable | `false` | 编辑器中不可编辑 |
| data-userid | 用户登录名 | 决定通知发给谁 |
| data-type | `user` | 标识对象类型为用户 |

可同时 @多人，写多个 `<b class="at-who" ...>` 标签即可。

## 回复评论

回复某条评论时需同时设置 `root_id` 和 `reply_id`：

- **回复根评论**：`root_id` = `reply_id` = 被回复评论的 ID
- **回复线程中的子评论**：`root_id` = 线程根评论 ID，`reply_id` = 被回复的子评论 ID

## description 支持的富文本格式

| HTML 标签 | 效果 |
|-----------|------|
| `<b>` | 加粗 |
| `<i>` | 斜体 |
| `<u>` | 下划线 |
| `<s>` | 删除线 |
| `<span style="color: red;">` | 颜色文字 |
| `<ul><li>` | 无序列表 |
| `<ol><li>` | 有序列表 |
| `<pre><code>` | 代码块 |
| `<blockquote>` | 引用 |
| `<a href="...">` | 超链接 |
| `<table>` | 表格 |

## 请求示例

```bash
# 添加简单评论
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  --data-urlencode "workspace_id=$TAPD_WORKSPACE_ID" \
  --data-urlencode 'entry_type=stories' \
  --data-urlencode 'entry_id=1131372104001000001' \
  --data-urlencode 'author=username' \
  --data-urlencode 'description=<p>这是一条评论</p>' \
  "${TAPD_API_ENDPOINT}/comments"

# 添加带 @提及 的评论
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  --data-urlencode "workspace_id=$TAPD_WORKSPACE_ID" \
  --data-urlencode 'entry_type=stories' \
  --data-urlencode 'entry_id=1131372104001000001' \
  --data-urlencode 'author=username' \
  --data-urlencode 'description=<p><b class="at-who" contenteditable="false" data-userid="target_user" data-type="user">@target_user</b> 请看一下这个问题</p>' \
  "${TAPD_API_ENDPOINT}/comments"

# 回复某条评论
curl -s -X POST \
  -H "Authorization: Bearer $TAPD_TOKEN" \
  --data-urlencode "workspace_id=$TAPD_WORKSPACE_ID" \
  --data-urlencode 'entry_type=stories' \
  --data-urlencode 'entry_id=1131372104001000001' \
  --data-urlencode 'author=username' \
  --data-urlencode 'root_id=1131372104001000040' \
  --data-urlencode 'reply_id=1131372104001000040' \
  --data-urlencode 'description=<p>这是一条回复评论</p>' \
  "${TAPD_API_ENDPOINT}/comments"
```

## 返回示例

```json
{
    "status": 1,
    "data": {
        "Comment": {
            "id": "1020355782058781915",
            "title": "在状态 [新] 添加",
            "description": "ccc",
            "author": "v_xuanfang",
            "entry_type": "bug",
            "entry_id": "1020355782500647717",
            "reply_id": "0",
            "root_id": "0",
            "created": "2019-12-24 18:33:53",
            "modified": "2019-12-24 18:33:53",
            "workspace_id": "20355782"
        }
    },
    "info": "success"
}
```

## 注意事项

- POST 请求建议使用 `--data-urlencode` 传参，避免 HTML 特殊字符编码问题
- `description` **必须使用 HTML 格式**（如 `<p>...</p>`），传 markdown 不会正确渲染，支持 Emoji
- @提及 的 `data-userid` 需要填用户的登录账号名（非昵称）
- 回复评论时 `root_id` 和 `reply_id` 必须同时提供
