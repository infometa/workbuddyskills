# wps.tables.column_content

## 1. wps.tables.column_content

#### 功能说明

查询在线文字文档表格的列内容。

**幂等性**：是 — safe

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "col": 1,
  "table_index": 1
}
```

#### 参数说明

- `col` (number, 可选): 列号
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `table_index` (number, 可选): 表格索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "cells": [
      {
        "begin": 49,
        "col": 1,
        "end": 50,
        "row": 1,
        "text": ""
      },
      {
        "begin": 53,
        "col": 1,
        "end": 54,
        "row": 2,
        "text": ""
      },
      {
        "begin": 57,
        "col": 1,
        "end": 58,
        "row": 3,
        "text": ""
      }
    ],
    "col": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
