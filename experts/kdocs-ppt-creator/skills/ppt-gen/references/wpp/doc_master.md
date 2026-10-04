# 母版

## 1. wpp.read_master

#### 功能说明

可用 action：
- masters_properties_query：查询母版：背景/版式/形状/主题/尺寸/配色等，body.master_type 指定 SLIDE_MASTER/NOTES_MASTER/HANDOUT_MASTER

**幂等性**：是

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "masters_properties_query"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 查询操作
- `master_type` (string, 可选): 母版类型：SLIDE_MASTER、NOTES_MASTER、HANDOUT_MASTER
- `fields` (array, 可选): 属性字段列表，如 BACKGROUND/CUSTOM_LAYOUTS/SHAPES/THEME/SIZE/NAME/COLOR_SCHEME
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```


---

## 2. wpp.write_master

#### 功能说明

可用 action：
- masters_properties_update：更新母版名称等
- update_delete：删除母版相关属性

**幂等性**：否 — 写操作非幂等，重试前请确认当前文档状态

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "masters_properties_update"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 写操作
- `master_type` (string, 可选): 母版类型：SLIDE_MASTER、NOTES_MASTER、HANDOUT_MASTER
- `name` (string, 可选): 母版名称
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```
