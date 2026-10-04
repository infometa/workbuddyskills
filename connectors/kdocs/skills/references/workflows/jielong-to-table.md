# 接龙转表格

> 识别接龙文本内容，自动提取并转为在线表格

**适用场景**：用户粘贴接龙内容或意图将文字转表格

**触发词**：接龙、接龙转表格、整理接龙、接龙统计、群接龙、文字转表格

- 用户粘贴了接龙文本或要求将文字转为表格

**工具链**：抽取 infoList → `create_file_with_content` →（必要时）`sheet.update_range_data` 续写 → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `create_file_with_content` | drive | 新建智能表格（.ksheet）并一次性写入表头和最终 infoList |
| `sheet.update_range_data` | sheet | （仅当数据超 500 项时）续写剩余数据 |
| `get_file_link` | drive | 获取表格链接并返回统计信息 |

## 执行流程

**步骤 1**：识别接龙场景 → 根据场景信息和接龙内容，推断表格名称(`sheetName`)和表头(`headerList`)字段；处理重复、取消、修改（同一人以最后一次记录为准），得到最终数据(`infoList`)

**步骤 2**：通过 `create_file_with_content` 一次性创建智能表格（`name` 为 `{sheetName}`，传 `file_extension=ksheet`、`sheet_name=sheetName` 与表头+`infoList` 的 `rangeData`；单批 `rangeData` 项数 ≤ 500）

**步骤 3（仅当数据超 500 项时）**：通过 `sheet.update_range_data` 续写剩余数据

**步骤 4（可选 - 汇总统计）**：若用户要求按品类/分类汇总数量，通过 `sheet.update_range_data(op_type=cell_operation_type_formula)` 在数据区域下方写入汇总公式（如 `=SUMIF(品类列, "苹果", 数量列)`）

**步骤 5**：调用 `get_file_link` 获取新表格链接，回复"已将接龙转为表格"并输出表格统计信息和链接
