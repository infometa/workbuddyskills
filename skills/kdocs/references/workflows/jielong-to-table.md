# 接龙转表格

> 识别接龙文本内容，自动提取并转为在线表格

**适用场景**：用户粘贴接龙内容或意图将文字转表格

**触发词**：接龙、接龙转表格、整理接龙、接龙统计、群接龙、文字转表格

- 用户粘贴了接龙文本或要求将文字转为表格

**工具链**：`create_file(.ksheet)` → `sheet.update_range_data`（表头）→ `sheet.update_range_data`（数据）→ `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `create_file` | drive | 创建智能表格（.ksheet） |
| `sheet.update_range_data` | sheet | 写入表头数据 |
| `get_file_link` | drive | 获取表格链接并返回统计信息 |

## 执行流程

**步骤 1**：识别接龙场景 → 根据场景信息和接龙信息，推断表格名称(`sheetName`)和表头(`headerList`)字段

**步骤 2**：通过 `create_file` 创建智能表格(.ksheet)，表名为 `sheetName`，通过 `sheet.update_range_data` 写入表头数据

**步骤 3**：按照接龙顺序和表头字段，依次提取接龙信息(`infoList`)，通过 `sheet.update_range_data` 写入数据

**步骤 4（可选 - 汇总统计）**：若用户要求按品类/分类汇总数量，在数据区域下方通过 `sheet.update_range_data(opType=formula)` 写入汇总公式（如 `=SUMIF(品类列, "苹果", 数量列)`），生成分类汇总行

**步骤 5**：创建成功，回复"已将接龙转为表格"，输出表格统计信息和新表格链接
