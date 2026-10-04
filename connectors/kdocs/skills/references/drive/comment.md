# 九、评论

## 1. list_document_comments

#### 功能说明

获取云文档底部留言（全文评论）的分页列表。支持两级结构：根评论 + 子评论（回复）。

> 解析评论字段时先读 items[].comment，部分响应可能直接将字段平铺在 items[] 上
> 根评论按 id 倒序；子评论按 id 正序
> next_page_token 不存在或为空时表示已到末页

#### 调用示例

获取根评论第一页：

```json
{
  "file_id": "f_abc123",
  "origin_id": "0",
  "page_size": 10
}
```

获取指定根评论的子评论：

```json
{
  "file_id": "f_abc123",
  "origin_id": "1001",
  "page_size": 100
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `origin_id` (string, 必填): `"0"` 返回根评论列表（每条附带最多 2 条子评论预览 `sub_comments.items`）；
传根评论 ID 返回该根下全部子评论。
`sub_comments.total` 大于预览条数时需再次调用并传根评论 ID。

- `page_size` (integer, 可选): 每页条数；根评论最大 10（默认 10），子评论最大 100（默认 100）
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "comment": {
          "id": 1001,
          "content": "请确认第三条款。",
          "created_by": { "id": "user_xxx", "name": "王五" },
          "ctime": 1717234200,
          "status": "normal"
        },
        "sub_comments": {
          "items": [
            {
              "id": 1002,
              "content": "已确认。",
              "origin_id": 1001,
              "reply_id": 1001,
              "created_by": { "name": "赵六" }
            }
          ],
          "total": 3
        }
      }
    ],
    "total": 8
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 当前页评论项 |
| `data.items[].comment` | object | 根评论对象（查根评论时） |
| `data.items[].comment.id` | integer | 评论唯一 ID |
| `data.items[].comment.content` | string | 评论正文 |
| `data.items[].comment.created_by` | object | 创建者，含 `id`、`name` |
| `data.items[].comment.ctime` | integer | 创建时间（Unix 时间戳） |
| `data.items[].comment.status` | string | 评论状态，正常为 `normal` |
| `data.items[].sub_comments` | object | 子评论预览（仅查根评论时返回） |
| `data.items[].sub_comments.items` | array | 预览子评论列表 |
| `data.items[].sub_comments.items[].id` | integer | 子评论 ID |
| `data.items[].sub_comments.items[].content` | string | 子评论正文 |
| `data.items[].sub_comments.items[].created_by` | object | 创建者，含 `id`、`name` |
| `data.items[].sub_comments.items[].ctime` | integer | 创建时间（Unix 时间戳） |
| `data.items[].sub_comments.items[].status` | string | 评论状态，正常为 `normal` |
| `data.items[].sub_comments.items[].origin_id` | integer | 所属根评论 ID |
| `data.items[].sub_comments.items[].reply_id` | integer | 被回复的评论 ID |
| `data.total` | integer | 当前查询条件下的评论总条数 |
| `data.next_page_token` | string | 下一页游标；不存在或为空表示已到末页 |


---

## 2. create_document_comment

#### 功能说明

在云文档底部发表留言（根评论）或回复已有评论。

| 业务场景 | 请求体字段 |
|----------|------------|
| 发表根留言 | `file_id`、`content` |
| 回复根评论 | `file_id`、`content`、`origin_id`（根评论 ID）、`reply_id`（与 `origin_id` 相同） |
| 回复子评论 | `file_id`、`content`、`origin_id`（所属根评论 ID）、`reply_id`（被回复的子评论 ID） |

`origin_id` 始终为根评论 ID，回复子评论时不要改成子评论 ID。
`origin_id` 与 `reply_id` 必须同时传或同时不传；不传表示根留言。

#### 调用约束

- **后置验证**：创建成功后调用 list_document_comments（origin_id=根评论ID）查子评论列表，新条目出现才算回复成功

**幂等性**：否 — 收到非 2xx 或 code != 0 时不重试，需用户确认后再操作，避免重复发表评论

#### 调用示例

发表根留言：

```json
{
  "file_id": "f_abc123",
  "content": "请法务审阅本合同。"
}
```

回复根评论：

```json
{
  "file_id": "f_abc123",
  "content": "收到，今日下班前反馈。",
  "origin_id": "1001",
  "reply_id": "1001"
}
```

回复子评论：

```json
{
  "file_id": "f_abc123",
  "content": "已收到你的反馈。",
  "origin_id": "1001",
  "reply_id": "1002"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `content` (string, 必填): 评论正文，1–5000 字符
- `origin_id` (string, 可选): 根评论 ID；回复时必填，始终填根评论 ID（不是子评论 ID），与 reply_id 成对使用
- `reply_id` (string, 可选): 被回复的评论 ID；回复根评论时与 origin_id 相同，回复子评论时为该子评论 ID；不可单独省略

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "id": 1003,
    "content": "收到，今日下班前反馈。",
    "created_by": { "id": "1814614481", "name": "张鹏达" },
    "ctime": 1748000000,
    "status": "normal",
    "origin_id": 1001,
    "reply_id": 1001
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | integer | 新建评论 ID |
| `data.content` | string | 评论正文 |
| `data.created_by` | object | 创建者信息，含 `id`、`name` |
| `data.ctime` | integer | 创建时间（Unix 时间戳） |
| `data.status` | string | 评论状态，正常为 `normal` |
| `data.origin_id` | integer | 所属根评论 ID（仅回复时返回） |
| `data.reply_id` | integer | 被回复的评论 ID（仅回复时返回） |


---

## 3. get_file_inline_comments

#### 功能说明

读取云文档正文中锚定/划选的批注（侧栏「评论」），返回 `inline_comments` 数组。
与 `list_document_comments`（底部留言面板）是两套独立数据，勿混用：
本工具读正文中**划选/锚定**的批注，`list_document_comments` 读底部**留言面板**的评论。

> 主要支持文字文档（.docx、.doc、.wps 等），表格、演示等类型可能返回空数组 `[]`
> doc.comments 路径不存在时视为无批注，返回 `[]` 不报错
> 需同时获取两类评论时，分别调用本工具和 `list_document_comments`，展示时注明来源

#### 调用示例

只传 file_id（drive_id 自动补全）：

```json
{
  "file_id": "f_abc123"
}
```

同时传 file_id 和 drive_id：

```json
{
  "file_id": "f_abc123",
  "drive_id": "d_xyz456"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `drive_id` (string, 可选): 云盘 ID

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "inline_comments": [
      {
        "id": "c_001",
        "content": "请法务确认此条款",
        "author": { "name": "张三" },
        "ctime": "2026-06-01T10:00:00+08:00"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.inline_comments` | array | 正文划选批注列表；无批注或不支持的文件类型返回空数组 `[]` |
| `data.inline_comments[].id` | string | 批注 ID |
| `data.inline_comments[].content` | string | 批注内容 |
| `data.inline_comments[].author` | object | 批注作者信息 |
| `data.inline_comments[].ctime` | string | 批注创建时间（ISO 8601） |
