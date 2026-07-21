# theme.json 配置说明

主题配置文件定义文档的视觉和结构规范。

## 文件位置

```
.codebuddy/themes/yunzhi-{template-name}.json
```

默认主题: `skills/yunzhi-doc-writer/themes/default.json`

---

## 配置结构

```json
{
  "$schema": "yunzhi-doc-theme/v1",
  "name": "主题名称",
  "source": "https://lexiangla.com/pages/{entry_id}",
  "extracted_at": "2026-01-22T10:00:00Z",
  
  "callout": { ... },
  "table": { ... },
  "text": { ... },
  "code_block": { ... },
  "structure": { ... },
  "semantic_mapping": { ... }
}
```

---

## callout 配置

```json
{
  "callout": {
    "primary": {
      "color": "#E3F2FD",
      "icon": "1f680",
      "usage": "开篇引导、核心价值、重要说明"
    },
    "tip": {
      "color": "#FFF3E0",
      "icon": "1f4a1",
      "usage": "提示信息、注意事项、小技巧"
    },
    "success": {
      "color": "#E8F5E9",
      "icon": "2705",
      "usage": "成功、完成、总结确认"
    },
    "warning": {
      "color": "#FFF8E1",
      "icon": "26a0",
      "usage": "警告、风险提示"
    },
    "error": {
      "color": "#FFEBEE",
      "icon": "274c",
      "usage": "错误、禁止、危险操作"
    },
    "info": {
      "color": "#E8EAF6",
      "icon": "2139",
      "usage": "补充说明、背景信息"
    }
  }
}
```

---

## table 配置

```json
{
  "table": {
    "header": {
      "background_color": "#F5F5F5",
      "text_style": {"bold": true}
    },
    "cell": {
      "success": {"background_color": "#E8F5E9"},
      "warning": {"background_color": "#FFF8E1"},
      "error": {"background_color": "#FFEBEE"},
      "highlight": {"background_color": "#E3F2FD"},
      "neutral": {"background_color": "#FAFAFA"}
    },
    "default_column_width": [300, 400],
    "compare_table": {
      "column_width": [400, 550],
      "left_header": "传统方式",
      "right_header": "新方案"
    }
  }
}
```

---

## text 配置

```json
{
  "text": {
    "emphasis": {
      "keyword": {"bold": true},
      "important": {"bold": true, "underline": true},
      "highlight": {"bold": true, "background_color": "#FFF59D"}
    },
    "code": {"inline_code": true}
  }
}
```

---

## code_block 配置

```json
{
  "code_block": {
    "default_language": "go",
    "wrap": false
  }
}
```

---

## structure 配置

```json
{
  "structure": {
    "use_divider_between_sections": true,
    "callout_at_start": true,
    "callout_at_end": true
  }
}
```

---

## semantic_mapping 配置

语义映射，用于自动识别内容类型：

```json
{
  "semantic_mapping": {
    "markdown_to_callout": {
      "> 核心": "primary",
      "> 重要": "primary",
      "> 提示": "tip",
      "> 建议": "tip",
      "> 注意": "warning",
      "> 警告": "warning",
      "> 成功": "success",
      "> 完成": "success",
      "> 错误": "error",
      "> 危险": "error",
      "> 信息": "info",
      "> ": "primary"
    },
    "table_cell_keywords": {
      "success": ["完成", "成功", "推荐", "支持", "是", "✓", "✅"],
      "error": ["失败", "不支持", "否", "✗", "❌", "危险"],
      "warning": ["注意", "警告", "待定", "可选"]
    }
  }
}
```

---

## 提取主题

从现有文档提取主题：

```
MCP Tool: 云知.block_list_block_children
Arguments: {"entry_id": "{entry_id}", "with_descendants": true}
```

提取内容：

| 块类型 | 提取字段 |
|--------|---------|
| callout | color, icon |
| table | header_row, column_width |
| table_cell | background_color |
| text/heading | style.align, style.background_color |
| code | style.language, style.wrap |

### 稳定性规则

- 同一文档多次提取产生相同 theme.json
- 只提取显式设置的样式，未设置使用 null
- 不依赖块顺序或内容
