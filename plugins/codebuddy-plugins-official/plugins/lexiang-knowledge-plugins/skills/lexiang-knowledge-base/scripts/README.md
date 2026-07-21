# yunzhi-doc-writer Scripts

云知文档写入辅助脚本集合。

## 安装依赖

### TypeScript 脚本

```bash
npm install -g ts-node typescript
npm install @types/node
```

### Python 脚本

```bash
pip install aiohttp requests
```

## 脚本列表

### sync-folder.ts

本地文件夹增量同步到云知知识库。

```bash
# Dry run 模式（仅生成计划）
npx ts-node sync-folder.ts --local ./docs --entry-id abc123 --dry-run

# 完整参数
npx ts-node sync-folder.ts \
  --local ./docs \
  --entry-id <parent_entry_id> \
  --space-id <space_id> \
  --state-file .sync-state.json \
  --dry-run
```

### upload-files.py

并行上传文件到云知。

```bash
# 单文件上传
python upload-files.py --files doc1.md doc2.pdf --entry-id abc123

# 文件夹批量上传
python upload-files.py --folder ./docs --entry-id abc123 --parallel 5

# 输出上传计划到 JSON
python upload-files.py --folder ./docs --entry-id abc123 --output plan.json --dry-run
```

### block-helper.ts

Block 构建辅助工具，作为模块导入使用。

```typescript
import { BlockBuilder, UpdateBlocksBuilder, ContentReorganizer, MarkdownToBlocks } from './block-helper';

// 构建块结构
const builder = new BlockBuilder();
builder.heading(1, '标题');
builder.paragraph('内容');
const mcpCall = builder.toMCPCall(entryId);

// 批量更新
const updater = new UpdateBlocksBuilder()
  .updateText('block_1', '新内容')
  .updateStyle('block_2', { background_color: '#E8F5E9' });
const updateCall = updater.toMCPCall(entryId);

// 内容重组
const reorganizer = new ContentReorganizer()
  .move(['block_1', 'block_2'], 'parent_block');
const moveCalls = reorganizer.toMCPCalls(entryId);

// Markdown 转 Block
const converter = new MarkdownToBlocks(theme);
const convertCall = converter.toMCPCall(entryId, markdownContent);
```

### mcp-validator.ts

MCP 参数校验和自动修复工具。

```typescript
import {
  validateApplyUpload,
  validateCreateBlockDescendant,
  fixApplyUploadArgs,
  fixCreateBlockDescendantArgs,
  formatValidationResult,
  LEAF_BLOCK_TYPES,
  CONTAINER_BLOCK_TYPES
} from './mcp-validator';

// 校验文件上传参数
const uploadResult = validateApplyUpload(
  { parent_entry_id: 'abc', name: 'doc.md', size: 1234 },
  { isUpdate: false }
);
if (!uploadResult.valid) {
  console.log(formatValidationResult(uploadResult));
}

// 校验块创建参数
const blockResult = validateCreateBlockDescendant({
  entry_id: 'xxx',
  descendant: [
    { block_id: 'h1', block_type: 'h1', heading1: {...} }
  ]
});

// 自动修复参数
const fixedArgs = fixCreateBlockDescendantArgs(originalArgs);
```

#### 校验器功能

| 函数 | 说明 |
|------|------|
| `validateApplyUpload` | 校验文件上传参数，检查 size/file_id/parent_entry_id |
| `validateCreateBlockDescendant` | 校验块创建参数，检查叶子节点 children |
| `validateUpdateBlocks` | 校验批量更新参数 |
| `validateMoveBlocks` | 校验块移动参数 |
| `fixApplyUploadArgs` | 自动修复上传参数 |
| `fixCreateBlockDescendantArgs` | 自动修复块创建参数（移除叶子节点 children） |

#### 常量

```typescript
// 叶子节点（不支持 children）
LEAF_BLOCK_TYPES: h1, h2, h3, h4, h5, code, image, attachment, video, divider, mermaid, plantuml

// 容器节点（必须有 children）
CONTAINER_BLOCK_TYPES: callout, table, table_cell, column_list, column, toggle
```

## 工作流示例

### 1. 项目文档同步

```bash
# 1. 首次同步（dry run 检查）
npx ts-node sync-folder.ts --local ./project-docs --entry-id root123 --dry-run

# 2. 执行同步
# 将生成的 MCP 调用序列提供给 AI 助手执行

# 3. 后续增量同步
# 脚本会自动检测变更，只同步修改的文件
```

### 2. Markdown 文档导入

```bash
# 1. 生成上传计划
python upload-files.py --folder ./markdown-docs --entry-id target123 --output plan.json

# 2. 查看计划
cat plan.json

# 3. 执行上传（通过 AI 助手）
# 将 plan.json 中的 MCP 调用提供给 AI 助手
```

## 注意事项

1. **MCP 调用需要通过 AI 助手执行**：脚本生成 MCP 调用参数，实际执行需要 AI 助手的 MCP 能力
2. **文件上传是 3 步流程**：apply_upload → HTTP PUT → commit_upload
3. **同步状态文件**：`.yunzhi-sync-state.json` 记录同步状态，请勿删除
4. **大文件建议分批**：单次 MCP 调用的数据量有限制
5. **调用前先校验**：使用 `mcp-validator.ts` 校验参数，避免常见错误
