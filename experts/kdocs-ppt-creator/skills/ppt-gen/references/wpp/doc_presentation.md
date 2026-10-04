# 演示文稿属性

## 1. wpp.read_presentation

#### 功能说明

可用 action：
- presentations_properties_query：查询属性：页面设置/字体/设计/只读状态等
- presentations_tags_query：查询演示文稿级标签

**幂等性**：是

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "presentations_properties_query"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 查询操作
- `fields` (array, 可选): 属性字段列表，如 PAGE_SETUP/FONTS/DESIGNS/READ_ONLY
- `name` (string, 可选): 标签名，按名查询时传入
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```


---

## 2. wpp.write_presentation

#### 功能说明

可用 action：
- presentations_properties_update：更新属性，如 display_comments 或关闭文档 CLOSE
- presentations_tags_update：更新标签，body.action 为 ADD 或 DELETE

**幂等性**：否 — 写操作非幂等，重试前请确认当前文档状态

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "presentations_properties_update"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 写操作
- `display_comments` (boolean, 可选): 是否显示批注（presentations_properties_update）
- `name` (string, 可选): 标签名
- `value` (string, 可选): 标签值（ADD 时）
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```
