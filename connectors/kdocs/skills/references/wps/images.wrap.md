# wps.images.wrap

## 1. wps.images.wrap

#### 功能说明

设置在线文字文档图片的环绕方式（WdWrapType：0=四周型 1=紧密型 2=穿越型 3=无环绕 4=上下型 5=衬于文字下方 6=浮于文字上方 7=嵌入型）。

**幂等性**：是 — safe

> index 是图片在文档中的当前序号（从 1 起），插入/删除图片后序号会变化；操作前先调 wps.images.list 获取最新 index，勿沿用旧序号。
> 时序约束：改环绕方式会把内联图转为浮动形状，此前通过 wps.images.border 设置的边框可能丢失，建议 wrap 后再用 wps.images.border 或 wps.shapes.line_* 设置边框。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 必填): 索引，从 1 开始
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `wrap_type` (number, 可选): 环绕方式（WdWrapType：0=四周型 1=紧密型 2=穿越型 3=无环绕 4=上下型 5=衬于文字下方 6=浮于文字上方 7=嵌入型）

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
