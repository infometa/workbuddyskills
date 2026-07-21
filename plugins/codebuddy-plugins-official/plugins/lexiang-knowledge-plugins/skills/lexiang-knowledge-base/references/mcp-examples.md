# MCP 调用完整示例

## 创建完整文档结构

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "intro",
      "block_type": "callout",
      "callout": {"color": "#E3F2FD", "icon": "1f680"},
      "children": ["intro_p"]
    },
    {
      "block_id": "intro_p",
      "block_type": "p",
      "text": {"elements": [{"text_run": {"content": "核心价值描述", "text_style": {"bold": true}}}]}
    },
    {
      "block_id": "h2_1",
      "block_type": "h2",
      "heading2": {"elements": [{"text_run": {"content": "功能特性", "text_style": {}}}]}
    },
    {
      "block_id": "divider_1",
      "block_type": "divider",
      "divider": {}
    }
  ],
  "children": ["intro", "h2_1", "divider_1"]
}
```

---

## 创建对比表格

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "table_1",
      "block_type": "table",
      "table": {"row_size": 3, "column_size": 2, "column_width": [400, 500], "header_row": true},
      "children": ["c1", "c2", "c3", "c4", "c5", "c6"]
    },
    {"block_id": "c1", "block_type": "table_cell", "table_cell": {"background_color": "#F5F5F5"}, "children": ["c1_p"]},
    {"block_id": "c1_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "传统方式", "text_style": {"bold": true}}}]}},
    {"block_id": "c2", "block_type": "table_cell", "table_cell": {"background_color": "#F5F5F5"}, "children": ["c2_p"]},
    {"block_id": "c2_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "新方案", "text_style": {"bold": true}}}]}},
    {"block_id": "c3", "block_type": "table_cell", "table_cell": {"background_color": "#FFEBEE"}, "children": ["c3_p"]},
    {"block_id": "c3_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "手动操作", "text_style": {}}}]}},
    {"block_id": "c4", "block_type": "table_cell", "table_cell": {"background_color": "#E8F5E9"}, "children": ["c4_p"]},
    {"block_id": "c4_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "自动化", "text_style": {}}}]}},
    {"block_id": "c5", "block_type": "table_cell", "table_cell": {}, "children": ["c5_p"]},
    {"block_id": "c5_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "耗时长", "text_style": {}}}]}},
    {"block_id": "c6", "block_type": "table_cell", "table_cell": {}, "children": ["c6_p"]},
    {"block_id": "c6_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "秒级完成", "text_style": {}}}]}}
  ],
  "children": ["table_1"]
}
```

---

## 创建代码块

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "code_1",
      "block_type": "code",
      "code": {
        "elements": [{"text_run": {"content": "const config = {\n  apiKey: 'xxx',\n  endpoint: 'https://api.example.com'\n};"}}],
        "style": {"language": "javascript", "wrap": false}
      }
    }
  ],
  "children": ["code_1"]
}
```

---

## 创建列表

### 无序列表

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {"block_id": "li_1", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "功能一"}}]}},
    {"block_id": "li_2", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "功能二"}}]}},
    {"block_id": "li_3", "block_type": "bulleted_list", "bulleted": {"elements": [{"text_run": {"content": "功能三"}}]}}
  ],
  "children": ["li_1", "li_2", "li_3"]
}
```

### 有序列表

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {"block_id": "ni_1", "block_type": "numbered_list", "numbered": {"elements": [{"text_run": {"content": "步骤一"}}]}},
    {"block_id": "ni_2", "block_type": "numbered_list", "numbered": {"elements": [{"text_run": {"content": "步骤二"}}]}},
    {"block_id": "ni_3", "block_type": "numbered_list", "numbered": {"elements": [{"text_run": {"content": "步骤三"}}]}}
  ],
  "children": ["ni_1", "ni_2", "ni_3"]
}
```

---

## 创建分栏布局

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "col_list",
      "block_type": "column_list",
      "column_list": {"column_size": 2},
      "children": ["col_1", "col_2"]
    },
    {
      "block_id": "col_1",
      "block_type": "column",
      "column": {"width_ratio": 0.5},
      "children": ["col_1_p"]
    },
    {"block_id": "col_1_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "左侧内容"}}]}},
    {
      "block_id": "col_2",
      "block_type": "column",
      "column": {"width_ratio": 0.5},
      "children": ["col_2_p"]
    },
    {"block_id": "col_2_p", "block_type": "p", "text": {"elements": [{"text_run": {"content": "右侧内容"}}]}}
  ],
  "children": ["col_list"]
}
```

---

## 创建 Mermaid 图表

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "mermaid_1",
      "block_type": "mermaid",
      "mermaid": {
        "content": "graph TD\n    A[开始] --> B{判断}\n    B -->|是| C[执行]\n    B -->|否| D[结束]"
      }
    }
  ],
  "children": ["mermaid_1"]
}
```

---

## 创建任务块

```
MCP Tool: 云知.block_create_block_descendant
Arguments: {
  "entry_id": "{entry_id}",
  "descendant": [
    {
      "block_id": "task_1",
      "block_type": "task",
      "task": {
        "name": "完成文档编写",
        "done": false,
        "assignees": [{"staff_id": "user_123"}],
        "due_at": {"date": "2026-01-25"}
      }
    }
  ],
  "children": ["task_1"]
}
```
