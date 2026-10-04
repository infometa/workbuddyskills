# 形状

## 1. wpp.read_shape

#### 功能说明

可用 action：
- query_list：形状列表
- query_detail：单个形状详情
- shapes_texts_query：查询形状内文本与字体
- shapes_tags_query：查询形状标签

**幂等性**：是

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装

#### 调用示例

示例调用：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "query_list"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 查询操作
- `slide_id` (number, 必填): 幻灯片 ID
- `shape_id` (number, 可选): 形状 ID，query_detail/texts/tags 时必填
- `name` (string, 可选): 标签名，shapes_tags_query 按名查询时传入
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```


---

## 2. wpp.write_shape

#### 功能说明

可用 action：
- insert_textbox：插入文本框
- insert_table：插入表格
- insert_line：插入线条
- insert_picture：插入图片形状（需公网可访问的图片 URL）
- update_attr：更新位置/尺寸
- update_fill：更新填充
- update_line：更新线条样式
- update_group：组合形状
- shapes_texts_update：更新形状文本
- shapes_tags_update：更新形状标签，body.action 为 ADD 或 DELETE
- shapes_items_delete：删除形状

**幂等性**：否 — 写操作非幂等，重试前请确认当前文档状态

> 推荐传 `body` 对象承载完整请求体；未传时从顶层参数组装
> insert_picture 需 image_url 为公网可访问的图片 URL；action 选定后由服务自动补全图片形状所需字段

#### 调用示例

更新形状位置：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "update_attr"
}
```

插入图片：

```json
{
  "file_id": "38b17a1f6216a9fe412583a400fb35dd",
  "action": "insert_picture",
  "slide_id": 1,
  "image_url": "https://example.com/picture.png",
  "left": 100,
  "top": 100,
  "width": 200,
  "height": 150
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `action` (string, 必填): 写操作
- `slide_id` (number, 必填): 幻灯片 ID
- `shape_id` (number, 可选): 形状 ID，更新/删除时必填
- `left` (number, 可选): 左边距
- `top` (number, 可选): 上边距
- `width` (number, 可选): 宽度
- `height` (number, 可选): 高度
- `text` (string, 可选): 形状文本（shapes_texts_update）
- `image_url` (string, 可选): 图片 URL（insert_picture 时必填，须公网可访问）
- `body` (object, 可选): 完整请求体，优先使用

#### 返回值说明

```json
{"code": 0, "message": "成功", "data": {}}

```
