# wps.shapes.wrap_type

#### 功能说明

设置形状的环绕方式

**幂等性**：是 — safe

> 非法 wrap_type 值（非 0-7）会显式报错（500002），不会静默成功

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "shape_item": "2",
  "wrap_type": 0
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询环绕方式）/ update（设置环绕方式）。可选值：`query` / `update`
- `shape_item` (string, 可选): shape item
- `wrap_type` (number, 可选): 环绕方式（WdWrapType：0=四周型 1=紧密型 2=穿越型 3=无环绕 4=上下型 5=衬于文字下方 6=浮于文字上方 7=嵌入型）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 2,
      "name": "TextBox 5",
      "type": 17
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

