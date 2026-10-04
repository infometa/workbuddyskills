# 跨表字段回填（按主键匹配）

> 两张表格按主键列（如订单号、企业ID、SKU）匹配，将源表指定列写入目标表对应列；须先读表头按列名定位，写后按列名回读验证

**适用场景**：用户要求根据两张表的某列做匹配，按字段名对应关系更新目标表数据（如明细表回填到汇总表）

**触发词**：跨表、回填、匹配更新、主键、匹配键、关联列、按企业ID、企业ID匹配、字段对应、明细同步、更新数据、VLOOKUP、两张表

- 用户给出源表与目标表，要求按某主键列（如订单号、企业ID）匹配并写入多个字段
- 用户描述「A表字段 → B表字段」的列名对应关系，而非列号

**工具链**：`sheet.get_sheets_info`（源+目标）→ `sheet.get_range_data`（0..rowTo，含表头）→ `sheet.range_data_batch_update` → `sheet.get_range_data`（按列名验证）

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `sheet.get_sheets_info` | sheet | 分别获取源表与目标表的 worksheet_id、rowTo、colTo |
| `sheet.get_range_data` | sheet | 每表一次读取 rowFrom:0..rowTo（含表头与全量数据行）；从 cellText 解析字段名行与各列 colFrom |
| `sheet.range_data_batch_update` | sheet | 按主键匹配结果批量写入目标列（formula 为源单元格字符串值） |

## 执行流程

> 🎯 **何时读本文件**：用户要求两张 `.xlsx`/`.ksheet` 按主键列匹配、把源表字段写入目标表（如「近30日销售额 → 月销售额」）。**禁止**跳过本流程直接 `range_data_batch_update`。

**适用范围**：双表、同一匹配键列值相等、一行对一行回填、用户给出列名映射；工具为 `sheet.*`（`.xlsx`/`.ksheet`）。
**不适用**：`.dbt` 多维表（走 `dbsheet.*`）；仅改格式/美化（见 `table-beautify`）；条件筛选子集更新（用 `find_range_data`）；多工作表须先明确 `sheetId`，勿默认第一个工作表。

## 硬性约束

1. **列索引只能来自表头 `cellText`**：从步骤 3 同一次 `get_range_data` 响应中解析字段名行，建立「列名→`colFrom`」映射；禁止凭首轮思考、历史经验或列字母猜测列号。
2. **行范围必须覆盖 `get_sheets_info` 定义的全部数据行**：默认单次 `get_range_data` 且 `rowTo` = `get_sheets_info.rowTo`；仅极大表时分块读取/写入，各块行区间并集无遗漏、无重叠，且每块 `rowTo` 不得小于该块末行索引。
3. **写后必须按列名验证**：用表头索引回读目标列（如「月销售额」），抽样 + 统计已更新行数；禁止仅用 `code:0` 或错误列号回读宣称成功。
4. **相似列名须逐列核对**：存在「日/周/月」等同系列相邻列时，写入前在表头行确认目标列名与源字段语义一致（例：「近30日销售额」→ **月销售额**，不是周销售额）。

## 步骤

**1. 定位两表**  
用户给链接 → 解析 `file_id`；给文件名 → `search_files`。记下源表、目标表各一份 `file_id`。

**2. 工作表与数据边界（各表一次）**

```
sheet.get_sheets_info(file_id) → worksheet_id = sheetsInfo[0].sheetId
rowTo / colTo 用于后续 get_range_data 上限
```

多工作表时须按用户指定的 `sheetName` 选择对应 `sheetId`，禁止默认 `[0]`。

**3. 读表（表头 + 全量数据，每表一次）**  
`get_range_data`：`rowFrom:0`、`rowTo` = 步骤 2 的 `rowTo`（不得截断）。从 `rangeData[].cellText` 识别**字段名行**（常见为第 0 或第 1 行）与各列 `colFrom`，同一响应即用于后续匹配与写入。参数见 `references/sheet/data.md` 中 `sheet.get_range_data` 工具卡。

**数据行估算**：`数据行数 ≈ rowTo - 字段名行索引`（0-based）。**默认 ≤1000 行**维持上述一次读完；超过 1000 或读/写超时、响应过大时，按 **500 行一块**分批 `get_range_data` + `range_data_batch_update`（每块仍须用表头映射，块内 `rowTo` 不得小于本块末行）。

**源表索引（分批时）**：默认源表**一次读完**并在内存建「匹配键→行」Map（仅保留匹配键 + 映射列），目标表按块写入。源表也 >1000 且一次读失败时，源表按块读入同一 Map 或每块只读「匹配键 + 映射列」后写目标对应块；禁止目标已分块而源表未建索引就写入。

**4. 建立映射表**  
用户给出的「源列名 → 目标列名」须在两边表头中**精确匹配** `cellText`（trim 后相等）。无同名列时向用户确认，禁止静默映射到相邻列。

**5. 按主键匹配并写入**  
匹配键列（如「订单号」「企业ID」）同样通过表头定位。对每个目标数据行，在源表找同键值，构造 `range_data`（`op_type: cell_operation_type_formula`，`formula` 为字符串值）。调用前读 `references/sheet/data.md` 中 `sheet.range_data_batch_update` 工具卡（`formula` 为字符串，非二维数组）。

**6. 写后验证**  
再次 `get_range_data` 回读目标表；对至少 3 个分散行 + 全量行数检查：目标列 `cellText` 与源表一致，且未写入错误相邻列。

## 验证清单

- [ ] 目标表已更新行数 = 应匹配行数（无漏行）
- [ ] 每个映射字段写入的目标列名与表头一致
- [ ] 易混淆的同系列相邻列（如日/周/月）未错位
