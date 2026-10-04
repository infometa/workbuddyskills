# wps.lists.blocks

## 1. wps.lists.blocks

#### 功能说明

枚举在线文字文档内的列表块（连续列表段落为一个块，按出现顺序编号），用于多列表文档定位各列表的段落范围与块序。

**幂等性**：是 — safe

> 只读枚举，不改文档。块定义：连续 listed 段落（ListType!=0），被无列表段打断则分块。
> 与 wps.lists.level_style 的 list_block 参数配合：先枚举块，再按块定向改编号样式。
> 技术债：只读操作暂走 documents/lists/update 通道（后端 query 通道的请求 pb 冻结、不支持 LIST_BLOCKS 属性透传，枚举分支只读不落盘）。MCP 对外不暴露 verb/scope，用户侧语义为只读；待后端 query 通道支持后迁移。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "block_count": 2,
    "blocks": [
      {"block": 1, "first_paragraph": 2, "last_paragraph": 4},
      {"block": 2, "first_paragraph": 7, "last_paragraph": 9}
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
