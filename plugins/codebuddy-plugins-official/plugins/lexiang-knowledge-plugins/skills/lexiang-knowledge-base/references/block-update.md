# 场景：Block 增量更新

批量更新已有文档中的多个块内容或样式。

## 批量更新 API

```
MCP Tool: 云知.block_update_blocks
Arguments: {
  "entry_id": "<entry_id>",
  "updates": {
    "<block_id_1>": { <更新操作> },
    "<block_id_2>": { <更新操作> },
    ...
  }
}
```

**限制**: 单次最多更新 20 个块

---

## 更新操作类型

### 更新文本内容

```json
{
  "update_text": {
    "text": {
      "elements": [
        {"text_run": {"content": "新内容", "text_style": {"bold": true}}}
      ]
    }
  }
}
```

### 更新块样式

```json
{
  "update_style": {
    "style": {
      "background_color": "#FFF8E1",
      "align": "center"
    }
  }
}
```

### 更新任务状态

```json
{
  "update_task": {
    "done": true,
    "name": "任务名称"
  }
}
```

### 插入文本

```json
{
  "insert_text": {
    "position": {"index": 5},
    "text": "插入的文本",
    "text_style": {"italic": true}
  }
}
```

### 删除文本

```json
{
  "delete_text": {
    "range": {"start_index": 0, "end_index": 10}
  }
}
```

---

## 完整示例

```
MCP Tool: 云知.block_update_blocks
Arguments: {
  "entry_id": "abc123",
  "updates": {
    "block_001": {
      "update_text": {
        "text": {
          "elements": [{"text_run": {"content": "更新后的标题", "text_style": {"bold": true}}}]
        }
      }
    },
    "block_002": {
      "update_style": {
        "style": {"background_color": "#E8F5E9"}
      }
    },
    "block_003": {
      "update_task": {"done": true}
    }
  }
}
```

---

## 使用辅助工具

```typescript
import { UpdateBlocksBuilder } from './scripts/block-helper';

const updater = new UpdateBlocksBuilder()
  .updateText('block_1', '新标题', { bold: true })
  .updateStyle('block_2', { background_color: '#E8F5E9' })
  .updateTask('block_3', true)
  .insertText('block_4', 0, '前缀: ')
  .deleteText('block_5', 0, 5);

const mcpCall = updater.toMCPCall(entryId);
// { tool: '云知.block_update_blocks', args: {...} }
```

---

## 注意事项

1. 每个块在单次请求中只能执行一种更新操作
2. 如需同时更新文本和样式，使用 `update_text` 并在 text.style 中指定样式
3. 更新前需先获取 block_id，可通过 `list_block_children` 获取
