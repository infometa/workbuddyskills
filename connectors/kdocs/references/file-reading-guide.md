# 文件读取指南

不同文件类型对应不同读取工具。先判断类型再调用工具，可避免空结果和结构丢失。

#### 读取流程

1. **定位文件**：先用 `search_files` / `get_file_info` 获取 `file_id`、`drive_id` 和文件后缀。  
2. **查看文件后缀**：按后缀确认文档类型，禁止 `search_files` 后直接批量调用 `read_file_content`。  
3. **按后缀选择读取工具**：使用下方“类型映射表”的首选路径。  
4. **命中 `read_file_content` 时再选轮询策略**：仅当类型为 `.docx/.pdf` 且使用 `read_file_content` 时，按 `size` 分档设置轮询间隔。  

#### 类型映射表（唯一主表）

| 文件类型 | 首选读取路径 | `read_file_content` 使用策略 |
|---|---|---|
| `.docx`（wps）/ `.pdf` | `read_file_content` | 默认可用 |
| `.otl`（ap） | `otl.block_query`（优先分块） | 仅在导出 Markdown 时使用 |
| `.xlsx`（et）/ `.ksheet`（as） | `sheet.get_sheets_info` + `sheet.get_range_data` | 禁止 |
| `.dbt`（db） | `dbsheet.get_schema` + `dbsheet.list_records` / `dbsheet.get_record` | 禁止 |
| `.csv` | 先转 `.xlsx` 再走 `sheet.*` | 禁止 |

#### `read_file_content` 轮询策略（仅 `.docx/.pdf` 场景）

首次调用（不传 `task_id`）**若返回 `task_status=success`**，此时内容已就绪，无需任何轮询。仅当首次返回 `task_status=running` 时，才需携带 `task_id` 继续轮询。

**客户端轮询分档**（仅 `task_status=running` 时适用）：

- `size` 字段统一使用 `FileInfo.size`（bytes）。
- `size` 来源优先级：`search_files.items[].file.size` > `get_file_info.data.size`。
- 若入口是 `get_share_info` 或当前上下文无 `size`，先调用 `get_file_info(file_id)` 补齐 `size`。

| 分档 | 条件（bytes） | 建议轮询间隔 |
|---|---|---|
| `small` | `< 1MB` | `1s,1s,2s` |
| `medium` | `1MB <= size < 10MB` | `2s,2s,3s` |
| `large` | `>= 10MB` | `3s,3s,5s` |
| `fallback` | `size` 缺失/异常 | `2s,2s,3s,5s` |

#### 特殊类型说明

**智能文档**（.otl / ap）——优先用 `otl.block_query`：

`otl.block_query`（`blockIds: ["doc"]`）可完整获取文档的块结构与内容。`read_file_content` 对 otl 存在内容遗漏风险，仅在需要导出 Markdown 时使用。

**文字文档 / PDF**（.docx / wps、.pdf）——用 `read_file_content`：

返回内容已自动转为 Markdown，可直接用于 AI 分析（摘要、审查、问答等）。

**表格类**（.xlsx / et、.ksheet / as）——**勿用 `read_file_content`**：

1. `sheet.get_sheets_info` 获取工作表列表和结构
2. `sheet.get_range_data` 按范围读取单元格数据

**多维表格**（.dbt / db）——**勿用 `read_file_content`**：

1. `dbsheet.get_schema` 获取数据表、字段、视图结构
2. `dbsheet.list_records` / `dbsheet.get_record` 读取记录

**CSV 文件**（.csv）——**不支持，勿用 `read_file_content`**：
1. 暂不支持 CSV 在线读取。建议用户将 CSV 转为 .xlsx 后用 `sheet.*` 工具读取。

#### 注意事项

- **PDF 精度**：复杂排版（表格、图片、多栏）可能存在精度损失，提取结果为近似纯文本
- **空读取排查**：若 `read_file_content` 返回空内容，检查：(1) 文件是否为空文件 (2) 文件格式是否受支持 (3) 文件后缀与实际格式是否匹配
