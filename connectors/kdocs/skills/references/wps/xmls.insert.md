# wps.xmls.insert

## 1. wps.xmls.insert

#### 功能说明

按字符区间插入 WordML/OOXML 片段。仅支持 wordxml（WordProcessingML）与 ooxml（Office Open XML）格式，不支持其他 XML 类型。

**幂等性**：否 — unsafe

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入 XML：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 10,
  "xml": "<w:p><w:r><w:t>smoke</w:t></w:r></w:p>"
}
```

#### 参数说明

- `begin` (number, 可选): 区间起点
- `end` (number, 可选): 区间终点
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `xml` (string, 必填): WordML/OOXML 片段，仅支持 wordxml 与 ooxml 格式，其他 XML 类型不支持

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "begin": 1,
    "end": 10
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
