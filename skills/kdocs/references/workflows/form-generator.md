# 信息收集表单生成

> 根据用户需求自动设计并创建信息收集表格

**适用场景**：用户需要新建表格用来收集信息、统计信息

**触发词**：报名表、信息收集、登记表、表单、收集信息、报名

- 用户需要新建表格用来收集或统计信息

**工具链**：AI 设计表头 → 用户确认 → `create_file(.ksheet)` → `sheet.update_range_data` → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `create_file` | drive | 创建智能表格（.ksheet） |
| `sheet.update_range_data` | sheet | 写入表头数据 |
| `get_file_link` | drive | 返回表格分享链接 |

## 执行流程

**步骤 1**：识别用户场景 → 根据用户场景推测表格名称(`sheetName`)和表头(`headerList`)字段

**步骤 2**：将推测的表头返回给用户确认，格式：
"已为你设计好 {{sheetName}} 表，表头为 {{headerList}}，确认生成？回复'确认'或告诉我需要调整的字段"
→ 用户回复需要调整则继续调整，回复确认则进入下一步

**步骤 3**：`create_file` 创建智能表格(.ksheet)，`sheet.update_range_data` 写入表头

**步骤 4**：返回表格分享链接
