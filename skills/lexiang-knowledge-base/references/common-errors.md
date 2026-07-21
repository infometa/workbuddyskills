# 乐享 MCP 常见错误和修复

本文档列出 Agent 调用乐享 MCP 时的常见错误和修复方法。

---

## ⚠️ 高频错误速查

| 错误 | 原因 | 修复 |
|------|------|------|
| 文件上传失败 | 缺少 size 参数 | **必须指定文件大小（字节数）** |
| 更新文件失败 | file_id 未传或 parent_entry_id 错误 | 更新时 parent_entry_id = 当前文件 entry_id |
| 块创建报错 | h1/h2/code 等叶子节点包含 children | **标题、代码块等不支持 children** |
| 块创建不完整 | 缺少顶层 children | 确保 children 包含所有顶层块 ID |

---

## 错误一：文件上传缺少 size

### 错误表现

```
调用 apply_upload 后返回错误或上传失败
```

### 错误参数

```json
{
  "parent_entry_id": "abc123",
  "name": "document.md",
  "mime_type": "text/markdown",
  "upload_type": "PRE_SIGNED_URL"
  // ❌ 缺少 size
}
```

### 正确参数

```json
{
  "parent_entry_id": "abc123",
  "name": "document.md",
  "mime_type": "text/markdown",
  "size": 1234,  // ✅ 必须指定文件大小（字节数）
  "upload_type": "PRE_SIGNED_URL"
}
```

### 如何获取文件大小

```typescript
// TypeScript/JavaScript
const fs = require('fs');
const size = fs.statSync(filePath).size;
```

```python
# Python
import os
size = os.path.getsize(file_path)
```

---

## 错误二：更新文件时参数混淆

### 错误表现

```
更新文件时创建了新文件，或报参数错误
```

### 关键区别

| 场景 | parent_entry_id | file_id |
|------|-----------------|---------|
| **新建文件** | 父目录的 entry_id | 不传 |
| **更新文件** | **当前文件自己的 entry_id** | **必传**（从 describe_entry 获取） |

### 新建文件

```json
{
  "parent_entry_id": "<父目录 entry_id>",
  "name": "new-doc.md",
  "mime_type": "text/markdown",
  "size": 1234,
  "upload_type": "PRE_SIGNED_URL"
  // 不传 file_id
}
```

### 更新文件

```json
{
  "parent_entry_id": "<当前文件自己的 entry_id>",  // ⚠️ 注意：不是父目录！
  "name": "existing-doc.md",
  "mime_type": "text/markdown",
  "size": 5678,
  "file_id": "<从 describe_entry 获取的 target_id>",  // ⚠️ 必传
  "upload_type": "PRE_SIGNED_URL"
}
```

### 获取 file_id 的方法

```
Step 1: 调用 describe_entry 获取条目详情
MCP Tool: lexiang.entry_describe_entry
Arguments: { "entry_id": "<文件条目 entry_id>" }

Step 2: 从返回值中提取
返回: { "entry": { "target_id": "<这就是 file_id>", ... } }
```

---

## 错误三：叶子节点包含 children

### 错误表现

```
块创建失败，或文档结构异常
```

### 叶子节点类型（不支持 children）

- `h1`, `h2`, `h3`, `h4`, `h5` - 标题块
- `code` - 代码块
- `divider` - 分割线
- `image` - 图片块
- `attachment` - 附件块
- `video` - 视频块
- `mermaid` - Mermaid 图表
- `plantuml` - PlantUML 图表

### 错误示例

```json
{
  "block_id": "h2_1",
  "block_type": "h2",
  "heading2": {"elements": [{"text_run": {"content": "标题"}}]},
  "children": ["para_1", "para_2"]  // ❌ 标题块不支持 children！
}
```

### 正确示例

```json
// 标题块（叶子节点，无 children）
{
  "block_id": "h2_1",
  "block_type": "h2",
  "heading2": {"elements": [{"text_run": {"content": "标题"}}]}
  // ✅ 不要 children
}

// 段落块作为顶层块排列
{
  "block_id": "para_1",
  "block_type": "p",
  "text": {"elements": [{"text_run": {"content": "段落内容"}}]}
}
```

### 正确的文档结构

标题和其下的内容应该是**平级**的，通过顶层 children 的顺序来体现层级：

```json
{
  "entry_id": "xxx",
  "descendant": [
    {"block_id": "h2_1", "block_type": "h2", "heading2": {...}},
    {"block_id": "para_1", "block_type": "p", "text": {...}},
    {"block_id": "para_2", "block_type": "p", "text": {...}},
    {"block_id": "h2_2", "block_type": "h2", "heading2": {...}},
    {"block_id": "para_3", "block_type": "p", "text": {...}}
  ],
  "children": ["h2_1", "para_1", "para_2", "h2_2", "para_3"]  // ✅ 顺序体现结构
}
```

---

## 错误四：容器块缺少 children

### 容器块类型（必须有 children）

- `callout` - 高亮块
- `table` - 表格（children 是 table_cell）
- `table_cell` - 表格单元格（children 是内容块）
- `column_list` - 分栏容器（children 是 column）
- `column` - 分栏列（children 是内容块）
- `toggle` - 折叠块

### 错误示例

```json
{
  "block_id": "callout_1",
  "block_type": "callout",
  "callout": {"color": "#E3F2FD", "icon": "1f680"}
  // ❌ 缺少 children
}
```

### 正确示例

```json
// Callout 必须有内容子块
{
  "block_id": "callout_1",
  "block_type": "callout",
  "callout": {"color": "#E3F2FD", "icon": "1f680"},
  "children": ["callout_1_p"]  // ✅ 指向内容块
},
{
  "block_id": "callout_1_p",
  "block_type": "p",
  "text": {"elements": [{"text_run": {"content": "提示内容"}}]}
}
```

---

## 使用校验工具

### 导入校验器

```typescript
import {
  validateApplyUpload,
  validateCreateBlockDescendant,
  fixApplyUploadArgs,
  fixCreateBlockDescendantArgs,
  formatValidationResult
} from './scripts/mcp-validator';
```

### 校验上传参数

```typescript
const result = validateApplyUpload(
  { parent_entry_id: 'abc', name: 'doc.md' },
  { isUpdate: false }
);

console.log(formatValidationResult(result));
// 输出错误列表和修复建议
```

### 校验块创建参数

```typescript
const result = validateCreateBlockDescendant({
  entry_id: 'xxx',
  descendant: [
    { block_id: 'h1', block_type: 'h1', heading1: {...}, children: ['p1'] }  // 错误
  ]
});

console.log(formatValidationResult(result));
// 🔴 [descendant[0].children] 【关键】h1 是叶子节点，不能包含 children
```

### 自动修复

```typescript
// 自动修复块创建参数
const fixed = fixCreateBlockDescendantArgs(originalArgs);

// 自动修复上传参数
const fixedUpload = fixApplyUploadArgs(args, {
  path: '/docs/readme.md',
  size: 1234,
  entryId: 'xxx',
  fileId: 'yyy'  // 如果是更新
});
```

---

## 块类型速查

### 支持 children 的块

| 类型 | children 内容 |
|------|--------------|
| `p` | 可选，嵌套内容 |
| `bulleted_list` | 可选，嵌套列表 |
| `numbered_list` | 可选，嵌套列表 |
| `callout` | **必须**，内容块 |
| `toggle` | **必须**，折叠内容 |
| `table` | **必须**，table_cell |
| `table_cell` | **必须**，内容块 |
| `column_list` | **必须**，column |
| `column` | **必须**，内容块 |
| `task` | 可选，子任务 |

### 不支持 children 的块（叶子节点）

| 类型 | 说明 |
|------|------|
| `h1` - `h5` | 标题 |
| `code` | 代码块 |
| `divider` | 分割线 |
| `image` | 图片 |
| `attachment` | 附件 |
| `video` | 视频 |
| `mermaid` | Mermaid 图表 |
| `plantuml` | PlantUML 图表 |

---

## 常见问题 (FAQ)

### Q: 如何选择 Markdown 导入方式？

**A**: 根据需求选择：

- **作为文件上传**（`apply_upload` → PUT → `commit_upload`）：保留原始格式，支持版本管理，适合文档归档
- **转为在线文档**（`import_content`）：转换为 Block 结构，可在线编辑，适合协作场景

### Q: Block ID 如何管理？

**A**: 客户端传入的 `block_id` 是临时标识，用于在单次调用中建立关系。服务端返回实际 ID 映射，后续更新操作使用服务端返回的 ID。

### Q: 表格单元格如何排序？

**A**: `children` 数组按**从左到右、从上到下**顺序排列。例如 2x2 表格：

```
[row1_col1, row1_col2, row2_col1, row2_col2]
```

### Q: 如何实现文档版本控制？

**A**: 文件上传方式（`apply_upload`）支持版本管理。更新已有文件时，`parent_entry_id` 传文件自身的 `entry_id`。

### Q: 为什么 `entry_describe_entry` 不返回文档正文内容？

**A**: `entry_describe_entry` 设计用于获取条目的元信息（如ID、名称、类型、创建时间等），不包含实际内容。要读取文档的正文内容，请使用 `entry_describe_ai_parse_content` 工具。

### Q: 什么时候使用 `entry_describe_entry`，什么时候使用 `entry_describe_ai_parse_content`？

**A**:
- 使用 `entry_describe_entry`：当您需要获取文档的基本信息用于后续操作时（如获取ID、确认文档类型）
- 使用 `entry_describe_ai_parse_content`：当您需要读取文档的实际内容进行摘要、分析或处理时