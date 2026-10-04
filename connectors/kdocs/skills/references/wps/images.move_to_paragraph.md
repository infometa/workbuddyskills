# wps.images.move_to_paragraph

## 1. wps.images.move_to_paragraph

#### 功能说明

将在线文字文档图片移动到指定段落。

**幂等性**：是 — safe

> index 为 1-based，可由 wps.images.list 获取；目标段落 paragraph_index 为 1-based，可由 wps.texts.range 或 wps.texts.search 定位后换算。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 必填): 索引，从 1 开始
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `move_wrap_type` (number, 可选): 移动后的环绕方式
- `paragraph_index` (number, 可选): 段落索引，从 1 开始
- `position` (string, 可选): 插入位置：before/after
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
