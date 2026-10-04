# otl.convert

## 1. otl.convert

#### 功能说明

将 HTML、Markdown 等内容转换为智能文档块结构，适合在正式插入前先生成可复用的块内容。

#### 工具选择

- **适用**：配合 `otl.block_insert` 将外部 Markdown/HTML 转为块后再插入指定位置
- **适用**：表格转块（`params.format=markdown` + 管道表）
- **勿用**（改用 `otl.insert_content`）：仅需在文档末尾追加表格且无需指定块位置 — 一步 `format=markdown` + `mode=append` 即可；勿绕 convert+insert
- **勿用**（改用 `otl.convert`）：params.content 含表格却拟用 format=html — 改 `params.format=markdown` 写管道表，或改 `otl.insert_content`

#### 调用约束

- **禁止**：表格内容禁止 `params.format=html`；须改为 `markdown` 管道表

**幂等性**：是

> `otl.convert` 仅做格式转换，不会修改文档内容；需配合 `otl.block_insert` 才能将转换结果写入文档
> 返回结果中 `blocks` 字段为转换得到的块数组，可直接用于 `otl.block_insert` 插入至文档。块类型和属性说明见 `references/otl/node.md`
> `params.format` 只支持 `"html"` 和 `"markdown"` 两种值
> `params.content` 中如包含换行符，使用 `\n` 表示

#### 调用示例

将 Markdown 内容转为块数据：

```json
{
  "file_id": "string",
  "params": {
    "format": "markdown",
    "content": "# 标题\n\n段落内容"
  }
}
```

将 Markdown 表格转为块数据：

```json
{
  "file_id": "string",
  "params": {
    "format": "markdown",
    "content": "## 数据\n\n| 列A | 列B |\n| --- | --- |\n| 1 | 2 |"
  }
}
```

将 HTML 段落转为块数据（非表格）：

```json
{
  "file_id": "string",
  "params": {
    "format": "html",
    "content": "<h1>标题</h1><p>段落内容</p>"
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `params` (object, 必填): 转换参数对象
  - `format` (string, 必填): 源数据格式，支持 `"html"` 或 `"markdown"`
  - `content` (string, 必填): 待转换的源数据内容

#### 表格内容

**识别**：`params.content` 含 Markdown 管道表（`| col |` + `| --- |`），或 HTML `<table`。

| 场景 | `params.format` |
| :--- | :--- |
| 表格 | **`markdown`**（管道表语法） |
| 非表格富文本段落 | `html` 或 `markdown` |

**禁止**：表格使用 `params.format=html`。全文末尾追加表格时优先 `otl.insert_content`（`format=markdown`），见 `otl/insert_content.md`。

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```
