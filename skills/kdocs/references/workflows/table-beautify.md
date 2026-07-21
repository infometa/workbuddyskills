# 表格美化与数据规范

> 读取表格数据，进行格式美化、数据规范化和样式调整

**适用场景**：用户要求优化、美化或规范表格的格式和数据

**触发词**：表格美化、美化表格、优化表格、整理表格、规范表格、格式化表格

- 用户要求对表格进行格式调整、样式美化或数据规范化

**工具链**：`search_files` → `sheet.get_sheets_info` → `sheet.get_range_data` → AI 分析 → `sheet.update_range_data`（格式化/规范化）

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` | drive | 定位目标表格文件 |
| `sheet.get_sheets_info` | sheet | 获取工作表列表和数据区域范围 |
| `sheet.get_range_data` | sheet | 读取现有数据和格式 |
| `sheet.update_range_data` | sheet | 批量应用格式和数据修正 |

## 执行流程

> 🎯 **核心工具**：`sheet.update_range_data` 支持 `opType=format`（格式化）、`opType=formula`（写值/公式）、`opType=merge`（合并单元格）。

**步骤 1**：定位表格
- 用户给文件名 → `search_files(keyword="表格名")`
- 用户给链接 → 解析 `link_id` → `get_share_info`

**步骤 2**：读取表格结构和数据
```
sheet.get_sheets_info(file_id) → 获取 sheetId、数据区域 rowTo/colTo
sheet.get_range_data(file_id, sheetId, range={rowFrom:0, rowTo, colFrom:0, colTo}) → 读取全部数据
```

**步骤 3**：AI 分析数据问题，生成美化方案

**步骤 4**：执行美化操作

**格式美化**（字体、颜色、对齐、边框）：
```
sheet.update_range_data(file_id, sheetId, rangeData=[
  {opType: "format", rowFrom, rowTo, colFrom, colTo, xf: {font: {...}, alcH: 2, fill: {...}, dgBottom: 1, ...}}
])
```

**表头规范**（重写列名）：
```
sheet.update_range_data(file_id, sheetId, rangeData=[
  {opType: "formula", rowFrom: 0, rowTo: 0, colFrom: 0, colTo: 0, formula: "新列名"}
])
```

**数据格式统一**（如统一手机号格式）：
```
sheet.update_range_data(file_id, sheetId, rangeData=[
  {opType: "formula", rowFrom: r, rowTo: r, colFrom: c, colTo: c, formula: "规范化后的值"}
])
```

**合并单元格**：
```
sheet.update_range_data(file_id, sheetId, rangeData=[
  {opType: "merge", rowFrom, rowTo, colFrom, colTo, type: "MergeCenter"}
])
```

**数据去重（模拟删行）**：
由于没有直接的删行 API，需通过「读取 → 本地去重 → 全量覆盖 → 清空多余行」来实现：
1. `get_range_data` 读取包含可能重复数据的所有行（如 100 行）
2. AI 在本地识别并剔除重复行，得到去重后的数据（如 80 行）
3. 使用 `update_range_data` 将去重后的 80 行覆盖写入表格的顶部（`rowFrom:0` 到 `rowTo:79`）
4. 使用 `update_range_data(opType="formula", formula="")` 将底部多余的 20 行（`rowFrom:80` 到 `rowTo:99`）清空，模拟删行效果
