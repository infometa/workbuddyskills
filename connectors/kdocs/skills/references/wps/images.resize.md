# wps.images.resize

## 1. wps.images.resize

#### 功能说明

设置在线文字文档图片的尺寸。

**幂等性**：是 — safe

> index 是图片在文档中的当前序号（从 1 起），插入/删除图片后序号会变化；操作前先调 wps.images.list 获取最新 index，勿沿用旧序号。
> 图片尺寸/位置按 0.75 磅栅格吸附：写入的宽高会被内核取整到 0.75 磅的整数倍（如 100 磅落到 99.75），读回值与写入值允许 ±0.75 磅偏差，断言时按此口径比较。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `height` (number, 可选): 高度
- `index` (number, 必填): 索引，从 1 开始
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `width` (number, 可选): 宽度

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
