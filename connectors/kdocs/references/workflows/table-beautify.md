# 表格美化与数据规范

> 读取表格数据，进行格式美化、数据规范化和样式调整，并通过条件格式、数据校验、区域权限固化规则

**适用场景**：用户要求优化、美化或规范表格的格式和数据，或需要为表格添加输入约束、高亮规则

**触发词**：表格美化、美化表格、优化表格、整理表格、规范表格、格式化表格、加下拉、添加校验、高亮异常、锁定表头、条件格式、数据校验

- 用户要求对表格进行格式调整、样式美化或数据规范化
- 用户要求为枚举列添加下拉选项或输入约束
- 用户要求高亮显示异常值、重复值或满足条件的数据
- 用户要求锁定表头或保护公式区域不被修改

**工具链**：`search_files` → `sheet.get_sheets_info` → `sheet.get_range_data` → AI 分析 → `sheet.update_range_data`（格式化/规范化）→ `sheet.create_conditional_format_rules`（高亮异常值）→ `sheet.create_data_validations`（下拉约束）→ `sheet.create_protection_ranges`（锁定区域，可选）

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目标表格文件 |
| `sheet.get_sheets_info` | sheet | 获取工作表列表和数据区域范围 |
| `sheet.get_range_data` | sheet | 读取现有数据和格式，分析列类型（枚举列、数值列、日期列等） |
| `sheet.update_range_data` | sheet | 批量应用格式和数据修正（字体、颜色、对齐、边框、值覆盖） |
| `sheet.create_conditional_format_rules` | sheet | 为数值/日期/枚举列创建条件格式，自动高亮异常值、重复值或达标/超标数据 |
| `sheet.create_data_validations` | sheet | 为枚举列创建下拉校验规则，固化输入选项，防止自由输入导致数据不一致 |
| `sheet.create_protection_ranges` | sheet | 锁定表头行或公式列，防止误操作修改关键区域（需用户确认） |

## 执行流程

> 🎯 **核心原则**：美化 = 格式修正（`update_range_data`）+ 规则固化（条件格式 / 数据校验 / 区域权限）。仅写入数据而不固化规则，后续录入仍会再次混乱。

**步骤 1**：定位表格
- 用户给文件名 → `search_files(keyword="表格名")`
- 用户给链接 → 解析 `link_id` → `get_share_info`

**步骤 2**：读取表格结构和数据
```
sheet.get_sheets_info(file_id) → 获取 sheetId、数据区域 rowTo/colTo
sheet.get_range_data(file_id, worksheet_id=sheetId, row_from=0, row_to=rowTo, col_from=0, col_to=colTo) → 读取全部数据
```

**步骤 3**：AI 分析数据问题，识别列类型，生成美化与规范方案

列类型识别结果决定后续操作：
- 枚举列（状态、分类、优先级等）→ 需要创建数据校验（下拉列表）
- 数值/日期列 → 需要创建条件格式（高亮异常或超阈值数据）
- 表头行 / 公式列 → 可选创建区域权限（防误改）

**步骤 4**：格式美化（`update_range_data`）

**格式美化**（字体、颜色、对齐、边框）：
```
sheet.update_range_data(file_id, worksheet_id=sheetId, range_data=[
  {op_type: "cell_operation_type_format", row_from, row_to, col_from, col_to, xf: {font: {...}, alc_h: 2, fill: {...}, dg_bottom: 1, ...}}
])
```

**表头规范**（重写列名）：
```
sheet.update_range_data(file_id, worksheet_id=sheetId, range_data=[
  {op_type: "cell_operation_type_formula", row_from: 0, row_to: 0, col_from: 0, col_to: 0, formula: "新列名"}
])
```

**数据格式统一**（如统一手机号、日期格式）：
```
sheet.update_range_data(file_id, worksheet_id=sheetId, range_data=[
  {op_type: "cell_operation_type_formula", row_from: r, row_to: r, col_from: c, col_to: c, formula: "规范化后的值"}
])
```

**合并单元格**：
```
sheet.update_range_data(file_id, worksheet_id=sheetId, range_data=[
  {op_type: "cell_operation_type_merge", row_from, row_to, col_from, col_to, merge_type: "merge_type_center"}
])
```

**数据去重（模拟删行）**：
由于没有直接的删行 API，通过「读取 → 本地去重 → 全量覆盖 → 清空多余行」实现：
1. `get_range_data` 读取包含可能重复数据的所有行（如 100 行）
2. AI 在本地识别并剔除重复行，得到去重后的数据（如 80 行）
3. `update_range_data` 将去重后的 80 行覆盖写入表格顶部（`row_from: 0` 到 `row_to: 79`）
4. `update_range_data`（`op_type: "cell_operation_type_formula"`, `formula: ""`）将底部多余的 20 行（`row_from: 80` 到 `row_to: 99`）清空

**步骤 5**：条件格式（高亮异常值）

适用场景：数值列超阈值高亮、日期列逾期标红、重复值标黄、空值警示。

**高亮数值超阈值**（如金额 > 10000 标红）：
```
sheet.create_conditional_format_rules(file_id, worksheet_id=sheetId, rule={
  cf_rule_type: "cf_rule_type_value_range",
  operator: "cf_rule_operator_greater",
  formula1: "10000",
  ranges: [{row_from: 1, row_to: rowTo, col_from: colIdx, col_to: colIdx}],
  xf: {fill: {back: {type: 1, value: 0xFF4444, tint: 0}, fore: {type: 0, value: 0, tint: 0}, type: 1}},
  lastone: false
})
```

**高亮重复值**：
```
sheet.create_conditional_format_rules(file_id, worksheet_id=sheetId, rule={
  cf_rule_type: "cf_rule_type_value_range",
  operator: "cf_rule_operator_duplicate_values",
  formula1: "",
  ranges: [{row_from: 1, row_to: rowTo, col_from: colIdx, col_to: colIdx}],
  xf: {fill: {back: {type: 1, value: 0xFFFF00, tint: 0}, fore: {type: 0, value: 0, tint: 0}, type: 1}},
  lastone: false
})
```

> 调用前先用 `sheet.get_conditional_format_rules` 检查是否已存在同列规则，避免冲突叠加。

**步骤 6**：数据校验（枚举列固化下拉选项）

适用场景：状态列、分类列、优先级列等取值固定的枚举列，加下拉约束后录入时只能选择预设选项。

```
sheet.create_data_validations(file_id, worksheet_id=sheetId,
  field_type: "List",
  args: {
    list_items: [{value: "待处理"}, {value: "进行中"}, {value: "已完成"}],
    validation_error_title: "输入不合法",
    validation_error_text: "请从下拉列表中选择"
  },
  range: {col_from: colIdx, col_to: colIdx, row_from: 1, row_to: 1048575}  // row_to=1048575 表示整列
)
```

> 行列索引均为 0-based。设置整列校验时 `row_to` 传 `1048575`。

**步骤 7（可选）**：区域权限（锁定表头 / 公式区域）

适用场景：用户明确要求保护表头行或特定公式区域不被他人误改时执行，**执行前必须向用户确认**。

```
sheet.create_protection_ranges(file_id, sheets_protection_infos=[{
  master_id: currentUserId,          // 当前操作用户 ID
  worksheet_id: sheetId,
  other_user_permission: "user_access_permission_visible",
  protection_infos: [{
    others_access_permission: "others_access_permission_visible",  // 他人只读
    protection_ranges: [{column_from: 0, column_to: colTo, row_from: 0, row_to: 0}],  // 第 0 行（表头）
    protection_user_data: [],
    range_creator_id: currentUserId
  }]
}])
```

> 该能力同时支持智能表格（.ksheet）和普通表格（.xlsx）；智能表格的 `other_user_permission` 仅支持 `user_access_permission_editable`。执行前询问用户是否需要锁定、锁定哪些区域。
