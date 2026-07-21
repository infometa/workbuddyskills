# 普通表格 (sheet) 命令参考

> 普通表格（在线电子表格/Sheet）与 AI 表格（多维表/Base）是不同产品。普通表格是传统行列电子表格，AI 表格支持字段/记录/视图等结构化能力。意图路由见下方"意图判断"。

## 命令总览

| 子命令 | 用途 |
|-------|------|
| `create` | 创建新的普通表格 |
| `info` | 获取表格元信息（含工作表列表） |
| `list` | 列出表格中的工作表 |
| `range read` | 读取单元格区域数据（别名: `get`） |
| `range update` | 更新单元格区域数据（值/公式/超链接） |
| `append` | 在表格末尾追加行数据 |
| `find` | 按关键词/正则搜索单元格内容 |
| `replace` | 批量替换单元格内容 |
| `add-dimension` | 添加行或列 |
| `insert-dimension` | 在指定位置插入行或列 |
| `delete-dimension` | 删除行或列 |
| `move-dimension` | 移动行或列 |
| `update-dimension` | 更新行/列属性（隐藏/尺寸） |
| `merge-cells` | 合并单元格 |
| `unmerge-cells` | 取消合并单元格 |
| `filter-view` | 筛选视图管理 |
| `write-image` | 向单元格写入图片 |
| `new` | 创建新的普通表格（别名） |

---

## create — 创建普通表格

```
Usage:
  dws sheet create [flags]
Example:
  dws sheet create --name "项目进度表"
  dws sheet create --name "Q1 预算" --folder <FOLDER_ID>
  dws sheet create --name "团队排期表" --workspace <WS_ID>
Flags:
      --name string        表格名称 (必填)
      --folder string      目标文件夹 ID 或 URL
      --workspace string   目标知识库 ID
```

---

## info — 获取表格元信息

返回表格的基础元数据和所有工作表列表。

```
Usage:
  dws sheet info [flags]
Example:
  dws sheet info --node <NODE_ID>
  dws sheet info --node <NODE_ID> --sheet-id <SHEET_ID>
  dws sheet info --node <NODE_ID> --sheet-id "Sheet1"
Flags:
      --node string       表格节点 ID 或 URL (必填)
      --sheet-id string   工作表 ID 或名称 (可选，不传则返回全部工作表信息)
```

---

## list — 列出工作表

```
Usage:
  dws sheet list [flags]
Example:
  dws sheet list --node <NODE_ID>
  dws sheet list --node "https://alidocs.dingtalk.com/i/nodes/<DOC_UUID>"
Flags:
      --node string   表格节点 ID 或 URL (必填)
```

---

## range read — 读取单元格区域

别名: `range get` / `read` / `get`

```
Usage:
  dws sheet range read [flags]
Example:
  dws sheet range read --node <NODE_ID>
  dws sheet range read --node <NODE_ID> --sheet-id <SHEET_ID>
  dws sheet range read --node <NODE_ID> --sheet-id "Sheet1" --range "A1:D10"
  dws sheet range read --node <NODE_ID> --range "Sheet1!A1:D10"
Flags:
      --node string       表格节点 ID 或 URL (必填)
      --sheet-id string   工作表 ID 或名称 (可选)
      --range string      单元格范围，A1 记法 (如 A1:D10，不传则读取整个工作表)
```

---

## range update — 更新单元格区域

支持写入值、公式和超链接。

```
Usage:
  dws sheet range update [flags]
Example:
  # 写入值
  dws sheet range update --node <NODE_ID> --sheet-id <SHEET_ID> --range "A1:B2" \
    --values '[["姓名","成绩"],["张三",90]]'

  # 写入公式
  dws sheet range update --node <NODE_ID> --sheet-id <SHEET_ID> --range "C2" \
    --values '[["=A2&B2"]]'

  # 写入超链接
  dws sheet range update --node <NODE_ID> --sheet-id <SHEET_ID> --range "A1" \
    --hyperlinks '[[{"type":"path","link":"https://dingtalk.com","text":"链接"}]]'

  # 清空区域（传 null）
  dws sheet range update --node <NODE_ID> --sheet-id <SHEET_ID> --range "A1:B3" \
    --values '[[null,null],[null,null],["保留",null]]'
Flags:
      --node string            表格节点 ID (必填)
      --sheet-id string        工作表 ID 或名称 (必填)
      --range string           单元格范围，A1 记法 (必填)
      --values string          二维数组 JSON (与 --hyperlinks 二选一)
      --hyperlinks string      超链接二维数组 JSON (与 --values 二选一)
      --number-format string   数字格式: General/@/#,##0/0%/yyyy/m/d 等
```

---

## append — 追加行数据

在指定工作表末尾追加一行或多行数据。

```
Usage:
  dws sheet append [flags]
Example:
  dws sheet append --node <NODE_ID> --sheet-id <SHEET_ID> --values '[["项目A","进行中",50000]]'
  dws sheet append --node <NODE_ID> --sheet-id "Sheet1" --values '[["项目B","已完成",38000],["项目C","待启动",62000]]'
Flags:
      --node string       表格节点 ID 或 URL (必填)
      --sheet-id string   工作表 ID 或名称 (必填)
      --values string     二维数组 JSON (必填)
```

---

## find — 搜索单元格内容

支持关键词搜索、正则匹配、公式搜索。

```
Usage:
  dws sheet find [flags]
Example:
  dws sheet find --node <NODE_ID> --sheet-id <SHEET_ID> --find "关键词"
  dws sheet find --node <NODE_ID> --sheet-id <SHEET_ID> --find "标题" --match-entire-cell
  dws sheet find --node <NODE_ID> --sheet-id <SHEET_ID> --find "^total" --use-regexp --match-case=false
  dws sheet find --node <NODE_ID> --sheet-id <SHEET_ID> --find "SUM" --match-formula
Flags:
      --node string           表格节点 ID 或 URL (必填)
      --sheet-id string       工作表 ID 或名称 (必填)
      --find string           搜索内容 (必填)
      --range string          限定搜索范围，A1 记法 (可选)
      --match-case            区分大小写 (默认 true)
      --match-entire-cell     完全匹配整个单元格
      --match-formula         在公式中搜索
      --use-regexp            使用正则表达式
      --include-hidden        包含隐藏行/列
```

---

## 意图判断

- 用户说"普通表格 / 在线表格 / Sheet / 单元格 / 工作表" 且没有多维表语义 → `sheet`
- 用户说"创建一个表格"且未提多维表/Base/字段/记录 → `sheet create`
- 用户说"读表格 / 看表格数据" → `sheet range read`
- 用户说"写表格 / 改表格 / 更新单元格" → `sheet range update`
- 用户说"给表格加几行" → `sheet append`
- 用户说"搜表格内容 / 找单元格" → `sheet find`
- 用户说"AI 表格 / 多维表 / Base / 记录 / 字段" → `aitable`（参见 [aitable.md](./aitable.md)）

关键区分: sheet(传统电子表格，行列单元格) vs aitable(结构化多维表，字段/记录/视图)

## 核心工作流

```bash
# 1. 创建表格
dws sheet create --name "项目进度" --format json

# 2. 获取表格信息 — 提取 nodeId 和 sheetId
dws sheet info --node <NODE_ID> --format json

# 3. 读取数据
dws sheet range read --node <NODE_ID> --sheet-id <SHEET_ID> --range "A1:D10" --format json

# 4. 写入数据
dws sheet range update --node <NODE_ID> --sheet-id <SHEET_ID> --range "A1:B2" \
  --values '[["姓名","进度"],["张三","90%"]]' --format json

# 5. 追加行
dws sheet append --node <NODE_ID> --sheet-id <SHEET_ID> \
  --values '[["李四","80%"]]' --format json
```

## 上下文传递表

| 操作 | 从返回中提取 | 用于 |
|------|-------------|------|
| `doc list` / `doc search` | 表格类型文件的 `nodeId` | sheet 命令的 `--node` |
| `sheet create` | `nodeId` | 后续 info/range/append 等的 `--node` |
| `sheet info` | `sheetId`、工作表名称 | range/append/find 的 `--sheet-id` |

## 注意事项

- `--node` 同时支持节点 ID 和完整 URL（`https://alidocs.dingtalk.com/i/nodes/<DOC_UUID>`）
- `--sheet-id` 支持传入工作表 ID 或工作表名称（如 `"Sheet1"`）
- `--values` 必须是合法 JSON 二维数组，外层 `[]` 包含行，内层 `[]` 包含列值
- 写操作前建议先用 `--dry-run` 预览；确认后加 `--yes`
- 大范围读写建议分段操作，避免超时

## 相关产品

- [aitable](./aitable.md) — AI 表格/多维表，支持字段/记录/视图/图表/仪表盘
- [doc](./doc.md) — 钉钉文档读写和块级编辑
- [drive](./drive.md) — 钉盘文件存储/上传/下载
