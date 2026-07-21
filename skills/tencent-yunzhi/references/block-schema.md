# Block 类型速查

## 支持的块类型

| 类型 | block_type | 说明 | 支持 children |
|------|-----------|------|--------------|
| 段落 | `p` | 普通文本段落 | ✓ |
| 一级标题 | `h1` | 标题 | ✗ |
| 二级标题 | `h2` | 标题 | ✗ |
| 三级标题 | `h3` | 标题 | ✗ |
| 四级标题 | `h4` | 标题 | ✗ |
| 五级标题 | `h5` | 标题 | ✗ |
| 无序列表 | `bulleted_list` | 项目符号列表 | ✓ |
| 有序列表 | `numbered_list` | 数字编号列表 | ✓ |
| 代码块 | `code` | 代码 | ✗ |
| 分割线 | `divider` | 水平分割线 | ✗ |
| 折叠块 | `toggle` | 可展开/折叠内容 | ✓ |
| 高亮块 | `callout` | 带颜色和图标的提示框 | ✓ (必填) |
| 任务 | `task` | 任务项 | ✓ |
| 分栏容器 | `column_list` | 多列布局容器 | ✓ (必填) |
| 分栏列 | `column` | 单列内容 | ✓ (必填) |
| 表格 | `table` | 表格 | ✓ (必填) |
| 表格单元格 | `table_cell` | 表格单元格 | ✓ (必填) |
| Mermaid | `mermaid` | Mermaid 图表 | ✗ |
| PlantUML | `plantuml` | PlantUML 图表 | ✗ |

---

## 文本结构

```json
{
  "elements": [
    {
      "text_run": {
        "content": "文本内容",
        "text_style": {
          "bold": true,
          "italic": false,
          "underline": false,
          "strikethrough": false,
          "inline_code": false,
          "link": "https://example.com",
          "text_color": "#333333",
          "background_color": "#FFFFFF"
        }
      }
    }
  ],
  "style": {
    "align": "left",
    "background_color": "#FFFFFF",
    "language": "javascript",
    "wrap": false
  }
}
```

---

## 块字段映射

| block_type | 内容字段 |
|-----------|---------|
| p | text |
| h1 | heading1 |
| h2 | heading2 |
| h3 | heading3 |
| h4 | heading4 |
| h5 | heading5 |
| bulleted_list | bulleted |
| numbered_list | numbered |
| code | code |
| toggle | toggle |
| callout | callout |
| task | task |
| table | table |
| table_cell | table_cell |
| column_list | column_list |
| column | column |
| divider | divider |
| mermaid | mermaid |
| plantuml | plantuml |

---

## 特殊块结构

### callout

```json
{
  "callout": {
    "color": "#E3F2FD",
    "icon": "1f680"
  }
}
```

### table

```json
{
  "table": {
    "row_size": 3,
    "column_size": 2,
    "column_width": [300, 400],
    "header_row": true,
    "header_column": false
  }
}
```

### table_cell

```json
{
  "table_cell": {
    "background_color": "#F5F5F5",
    "align": "left",
    "vertical_align": "middle",
    "row_span": 1,
    "col_span": 1
  }
}
```

### column_list / column

```json
{
  "column_list": {"column_size": 2}
}

{
  "column": {"width_ratio": 0.5}
}
```

### mermaid / plantuml

```json
{
  "mermaid": {
    "content": "graph TD\n    A --> B"
  }
}

{
  "plantuml": {
    "content": "@startuml\nA -> B\n@enduml"
  }
}
```

### task

```json
{
  "task": {
    "name": "任务名称",
    "done": false,
    "assignees": [{"staff_id": "user_123"}],
    "due_at": {"date": "2026-01-25", "time": "18:00"}
  }
}
```

---

## 注意事项

1. **容器类块必须指定 children**: callout, table, table_cell, column_list, column
2. **表格 children 顺序**: 从左到右、从上到下
3. **block_id 为临时 ID**: 服务端返回实际 ID 映射
4. **叶子节点不支持 children**: h1-h5, code, divider, mermaid, plantuml
