# 幻灯片

## 1. wpp.read_slide

#### 功能说明

可用 action：
- query_count：幻灯片总数
- query_detail：单张幻灯片详情
- query_list：幻灯片列表
- slides_notes_query：查询幻灯片备注
- slides_tags_query：查询幻灯片标签

**幂等性**：是

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "query_count"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 查询操作
- `slide_id` (number, 可选): 幻灯片 ID，query_detail/notes/tags 时必填
- `name` (string, 可选): 标签名，slides_tags_query 按名查询时传入
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```


---

## 2. wpp.write_slide

#### 功能说明

可用 action：
- slides_items_insert：插入空白幻灯片
- slides_items_delete：删除幻灯片
- update_move：移动幻灯片位置
- update_duplicate：复制幻灯片
- slides_tags_update：更新幻灯片标签，body.action 为 ADD 或 DELETE

**幂等性**：否 — 写操作非幂等，重试前请确认当前文档状态

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "update_move"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 写操作
- `slide_id` (number, 可选): 目标幻灯片 ID
- `index` (number, 可选): 插入位置索引（slides_items_insert）
- `layout` (number, 可选): 版式索引（slides_items_insert）
- `to_position` (number, 可选): 目标位置（update_move）
- `name` (string, 可选): 标签名（slides_tags_update）
- `value` (string, 可选): 标签值（slides_tags_update ADD 时）
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```
