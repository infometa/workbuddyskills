# 场景：Markdown 转 Block 写入

将 Markdown 内容解析并转换为云知 Block 结构写入文档。

## 使用辅助工具

```typescript
import { MarkdownToBlocks } from './scripts/block-helper';
import theme from './themes/default.json';

const converter = new MarkdownToBlocks(theme);
const mcpCall = converter.toMCPCall(entryId, markdownContent);
```

---

## 支持的 Markdown 语法

| Markdown | Block 类型 | 说明 |
|----------|-----------|------|
| `# 标题` | h1 | 一级标题 |
| `## 标题` | h2 | 二级标题 |
| `### 标题` | h3-h5 | 三到五级标题 |
| 普通段落 | p | 段落文本 |
| `> 引用` | callout | 根据关键词自动选择类型 |
| `- 列表` | bulleted_list | 无序列表 |
| `1. 列表` | numbered_list | 有序列表 |
| ``` code ``` | code | 代码块 |
| `---` | divider | 分割线 |

---

## Callout 语义映射

引用块会根据内容关键词自动映射到对应的 Callout 类型：

| 关键词 | Callout 类型 | 颜色 |
|--------|-------------|------|
| 核心、重要、价值 | primary | #E3F2FD |
| 提示、建议、tips | tip | #FFF3E0 |
| 成功、完成、搞定 | success | #E8F5E9 |
| 警告、注意、风险 | warning | #FFF8E1 |
| 错误、禁止、危险 | error | #FFEBEE |

---

## 示例

### 输入 Markdown

```markdown
# 产品介绍

> 核心价值：提升 10 倍效率

## 功能特性

- 自动化处理
- 智能分析
- 实时同步

## 快速开始

```bash
npm install yunzhi-sdk
```

---

> 提示：更多信息请查阅文档
```

### 生成的 MCP 调用

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "<entry_id>",
  "descendant": [
    {"block_id": "blk_1", "block_type": "h1", "heading1": {"elements": [{"text_run": {"content": "产品介绍"}}]}},
    {"block_id": "blk_2", "block_type": "callout", "callout": {"color": "#E3F2FD", "icon": "1f680"}, "children": ["blk_3"]},
    {"block_id": "blk_3", "block_type": "p", "text": {"elements": [{"text_run": {"content": "核心价值：提升 10 倍效率"}}]}},
    {"block_id": "blk_4", "block_type": "h2", "heading2": {"elements": [{"text_run": {"content": "功能特性"}}]}},
    {"block_id": "blk_5", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "自动化处理"}}]}},
    {"block_id": "blk_6", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "智能分析"}}]}},
    {"block_id": "blk_7", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "实时同步"}}]}},
    {"block_id": "blk_8", "block_type": "h2", "heading2": {"elements": [{"text_run": {"content": "快速开始"}}]}},
    {"block_id": "blk_9", "block_type": "code", "code": {"elements": [{"text_run": {"content": "npm install yunzhi-sdk"}}], "style": {"language": "bash"}}},
    {"block_id": "blk_10", "block_type": "divider", "divider": {}},
    {"block_id": "blk_11", "block_type": "callout", "callout": {"color": "#FFF3E0", "icon": "1f4a1"}, "children": ["blk_12"]},
    {"block_id": "blk_12", "block_type": "p", "text": {"elements": [{"text_run": {"content": "提示：更多信息请查阅文档"}}]}}
  ],
  "children": ["blk_1", "blk_2", "blk_4", "blk_5", "blk_6", "blk_7", "blk_8", "blk_9", "blk_10", "blk_11"]
}
```

---

## 使用 BlockBuilder 手动构建

```typescript
import { BlockBuilder } from './scripts/block-helper';

const builder = new BlockBuilder();
builder.heading(1, '文档标题');
builder.callout('#E3F2FD', '1f680', '核心价值描述');
builder.paragraph('正文内容...');
builder.divider();
builder.bulletedList(['功能1', '功能2', '功能3']);
builder.codeBlock('console.log("hello")', 'javascript');
builder.table([
  ['特性', '说明'],
  ['功能A', '描述A']
], { headerRow: true, headerBgColor: '#F5F5F5' });

const mcpCall = builder.toMCPCall(entryId);
```
