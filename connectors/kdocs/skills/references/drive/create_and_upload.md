# 一、文档创建与上传

## 1. create_empty_file

#### 功能说明

仅需空白在线文档时用本工具。

支持后缀：`.doc`、`.docx`、`.otl`、`.dbt`、`.xlsx`、`.xls`、`.ksheet`、`.pptx`、`.ppt`。

须同时传 `name` 与 `file_extension` 以明确文档类型。

新建到个人根：盘和目录都不传。新建到某文件夹：只传 `parent_id`。规则见 `file-locating-guide`。

成功响应 `data` 含 `drive_id`、`parent_id`、`name`、`suffix`，可接续 `drive.list_files`。

#### 工具选择

- **适用**：仅需空白在线文档（无正文/表格数据）时
- **勿用**（改用 `create_file_with_content`）：有内容需写入（正文/表格数据/多维表记录）
- **勿用**（改用 `create_file_with_content`）：新建多维表且须自定义列（用户指定字段名/类型） — 须 fields+records 一步建表；本工具产出默认列，无法直接定制 schema
- **勿用**（改用 `create_folder`）：新建文件夹
- **勿用**（改用 `upload_new_file`）：本地已有文件需上传（含本地 PDF）
- **勿用**（改用 `create_file_with_content`）：有 Markdown 正文需写入 PDF

#### 调用约束

- **前置检查**：search_files 查重，避免创建同名文件
- **前置检查**：须传 name 与 file_extension；支持 .doc/.docx/.otl/.dbt/.xlsx/.xls/.ksheet/.pptx/.ppt
- **禁止**：name 只写文件名，不得包含 .doc/.docx/.otl/.dbt/.xlsx/.xls/.ksheet/.pptx/.ppt 等后缀；后缀仅通过 file_extension 指定
- **禁止**：勿传 content/rangeData/fields/records；有内容请用 create_file_with_content
- **后置验证**：get_file_info 确认文件已创建

**幂等性**：否 — 重试前 search_files 检查是否已创建

> dbt「空白」指无自定义列、无业务数据，不是零列；平台默认首张表含：名称、数量、日期、状态。用户只说「包含某几列」时保留默认列，勿 delete_fields 删「多余」列，除非用户明确要求只要这些列
> dbt 新建后可能预置若干条 `fields` 为 `{}` 的全空记录；后续向表内新增数据见 references/dbsheet.md「新增记录与全空记录复用」，勿 delete_records 清理

#### 调用示例

空白智能文档：

```json
{
  "name": "周报",
  "file_extension": "otl"
}
```

指定文件夹：

```json
{
  "parent_id": "CmFqW8kR2nP5xL9vH3jT6aB1dE4gI7sM0",
  "name": "草稿",
  "file_extension": "otl"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID。不传则使用个人云盘
- `parent_id` (string, 可选): 父文件夹 ID，根目录为 "0"。"0" 是某个盘的根，不是个人盘根；不传则使用个人云盘根
- `name` (string, 必填): 文件名，如 `周报` / `合作协议`；不得包含后缀，文档类型由 `file_extension` 指定
- `file_extension` (string, 必填): 文档扩展名。可选 doc/docx/otl/dbt/xlsx/xls/ksheet/pptx/ppt。与 name 一并填写，用于明确文档类型
- `on_name_conflict` (string, 可选): 文件名冲突处理方式。可选值：`fail` / `rename` / `overwrite` / `replace`；默认值：`rename`
- `parent_path` (array[string], 可选): 相对路径（每段为文件目录名，非 ID），不存在则自动创建

#### 返回值说明

```json
{
  "data": {
    "id": "string",
    "drive_id": "8001234567",
    "parent_id": "0",
    "name": "周报.otl",
    "suffix": ".otl",
    "link_url": "https://www.kdocs.cn/l/xxxx",
    "type": "file"
  },
  "code": 0,
  "msg": "string"
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


---

## 2. create_file_with_content

#### 功能说明

对话中已有要写入的正文、表格数据或多维表记录时，一步完成新建+写入。

须同时传 `name` 与 `file_extension` 以明确文档类型。

表格参数示例：

```json
{
  "name": "台账",
  "file_extension": "xlsx",
  "sheet_name": "Sheet1",
  "rangeData": [{
    "row_from": 0,
    "row_to": 0,
    "col_from": 0,
    "col_to": 1,
    "formula": [["姓名", "部门"]]
  }]
}
```

**`rangeData` 根节点必须是数组，每项是对象，`formula` 必须是二维数组；不得混用 `sheet.update_range_data` 的 `{range, values}`。**

新建到个人根：盘和目录都不传。新建到某文件夹：只传 `parent_id`。规则见 `file-locating-guide`。

成功响应 `data` 含 `drive_id`、`parent_id`、`action`（`created_with_content`），可接续 `drive.list_files`。

#### 工具选择

- **适用**：有内容需写入（正文/表格数据/多维表记录）时一步新建并写入
- **适用**：新建多维表（.dbt）且须自定义列（即便暂无业务数据）时
- **适用**：对话中已有 Markdown 正文，需直接创建并保留为 .md 文件时
- **适用**：本地 Markdown 需新建为 otl/docx/pdf 时
- **勿用**（改用 `create_empty_file`）：仅需空白文档

#### 调用约束

- **前置检查**：须传 name 与 file_extension；支持 .otl/.docx/.md/.pdf/.xls/.xlsx/.ksheet/.dbt
- **禁止**：name 只写文件名，不得包含 .otl/.docx/.md/.pdf/.xls/.xlsx/.ksheet/.dbt 等后缀；后缀仅通过 file_extension 指定
- **禁止**：dbt 的 `fields[]` 中选项类禁止 `data.items` 包装；须扁平 `fields[].items`（同 `dbsheet.create_fields`）
- **后置验证**：成功时检查 code=0 与 data.file_id，并用 read 类工具验证写入；data.link_url 非空则直接展示

**幂等性**：否 — 失败且 data 含 file_id 时，按 msg 与 param_detail「失败补写」选用原子工具，勿重试本工具

> 表格仅单表 rangeData；多表或超 500 项请建空文件后用 sheet.update_range_data 续写
> dbt 自定义列：须同时传 fields 与 records（至少 1 条）；缺 records 会 400001，勿改走 create_empty_file 再删列
> dbt：records 列名须在 fields 中声明

#### 调用示例

新建智能文档（Markdown 正文）：

```json
{
  "name": "Q1区域销售周报",
  "file_extension": "otl",
  "content": "# Q1 销售周报\n\n## 概述\n\n本季度销售额同比增长 15%。"
}
```

Markdown 新建 Word：

```json
{
  "name": "会议纪要",
  "file_extension": "docx",
  "content": "# 会议纪要\n\n决议如下。"
}
```

新建 Markdown 文件：

```json
{
  "name": "项目说明",
  "file_extension": "md",
  "content": "# 项目说明\n\n- 支持 Markdown 原始格式\n- 不经过转档"
}
```

新建表格（rangeData + sheet_name）：

```json
{
  "name": "三月台账",
  "file_extension": "xlsx",
  "sheet_name": "三月台账",
  "rangeData": [
    {
      "row_from": 0,
      "row_to": 0,
      "col_from": 0,
      "col_to": 2,
      "formula": [
        [
          "姓名",
          "部门",
          "金额"
        ]
      ]
    },
    {
      "row_from": 1,
      "row_to": 1,
      "col_from": 0,
      "col_to": 2,
      "formula": [
        [
          "张三",
          "研发",
          "1000"
        ]
      ]
    }
  ]
}
```

新建多维表（fields + records + sheet_name）：

```json
{
  "name": "活动报名",
  "file_extension": "dbt",
  "sheet_name": "报名名单",
  "fields": [
    {
      "name": "姓名",
      "type": "SingleLineText"
    },
    {
      "name": "手机",
      "type": "SingleLineText"
    },
    {
      "name": "部门",
      "type": "SingleSelect",
      "items": [
        {
          "value": "市场"
        },
        {
          "value": "研发"
        }
      ]
    }
  ],
  "records": [
    {
      "fields": {
        "姓名": "李四",
        "手机": "13800000000",
        "部门": "市场"
      }
    }
  ]
}
```

新建多维表（仅自定义列，暂无业务数据）：

```json
{
  "name": "项目表",
  "file_extension": "dbt",
  "sheet_name": "项目数据",
  "fields": [
    {
      "name": "名称",
      "type": "SingleLineText"
    },
    {
      "name": "数量",
      "type": "Number"
    }
  ],
  "records": [
    {
      "fields": {}
    }
  ]
}
```

#### 参数说明

- `name` (string, 必填): 文件名，如 `周报` / `合作协议`；文档类型由 `file_extension` 指定
- `file_extension` (string, 必填): 文档扩展名。可选 otl/docx/md/pdf/xls/xlsx/ksheet/dbt。与 name 一并填写，用于明确文档类型
- `content` (string, 可选): 格式为 otl/docx/md/pdf 时必填（Markdown 正文）。UTF-8 文本，不得为文件二进制；单次 content 有字符上限（服务端校验，失败 message 含具体值）
- `rangeData` (array[object], 可选): 格式为 xls / xlsx / ksheet 时需要填入单表单元格数据；项数 ≤ 500；子字段见下
  - `row_from` / `row_to` / `col_from` / `col_to` (number, 必填): 矩形区域，0 起
  - `formula` (array[array], 必填): 二维单元格值，一行对应一个数组，如 `[["姓名", "部门"]]`；仅写值，格式/合并见建好后 `sheet.update_range_data`
- `fields` (array[object], 可选): 格式为 dbt 时需要自定义列；字段类型见 `references/dbsheet/field.md`
  - `name` (string, 必填): 列名，须与 `records[].fields` 的键一致
  - `type` (string, 必填): 字段类型（SingleLineText / Number / SingleSelect / DateTime 等），完整枚举见 `references/dbsheet/field.md`
- `records` (array[object], 可选): 格式为 dbt 时需要填入批量新建记录，条数 ≤ 500
  - `fields` (object, 必填): `{列名: 值}`；值格式见 `references/dbsheet/record.md`
- `sheet_name` (string, 可选): 格式为 xls / xlsx / ksheet / dbt 时设置目标工作表名称（非 sheet_id）；不传则写入首张表（可有 warnings）
- `drive_id` (string, 可选): 目标云盘 ID。不传则使用个人云盘
- `parent_id` (string, 可选): 父文件夹 ID，根目录为 "0"。"0" 是某个盘的根，不是个人盘根；不传则使用个人云盘根

#### 按后缀选参数（须同时传 `name` + `file_extension`）

| 后缀 | 必传 |
|--------|----------|
| `.otl` `.docx` `.md` `.pdf` | `name` + `file_extension` + `content`（UTF-8 Markdown；单次有字符上限） |
| `.xls` `.xlsx` `.ksheet` | `name` + `file_extension` + `rangeData`—非空数组，仅单表，≤ 500 项 |
| `.dbt` | `name` + `file_extension` + `fields` + `records`（至少 1 条；暂无数据时 `records: [{"fields": {}}]`，勿填 `0` 等占位值）；`SingleSelect`/`MultipleSelect` 的 `items` 扁平写在 `fields[]` 根级，**禁止** `data.items` |

#### 失败补写（创建成功但写入失败时的恢复路径）

| 后缀 | 建议工具 | 参数要点 |
|------|----------|----------|
| `.otl` | `otl.insert_content` | `content`、`format=markdown`、`mode=prepend`（创建成功但写入失败时补写） |
| `.docx` `.pdf` | `upload_replace_file` | `file_id` + `content_base64`（本地上传新版本全文覆盖） |
| `.xls` `.xlsx` `.ksheet` | `sheet.update_range_data` | `file_id` + `sheetId` + `rangeData` |
| `.dbt` | 有全空记录时优先 `dbsheet.update_records`（见 dbsheet.md「新增记录与全空记录复用」），否则 `dbsheet.create_records`；缺列先 `dbsheet.create_fields` | `file_id` + `sheet_id` + `records` |

#### 返回值说明

```json
// 成功（智能文档）
{
  "code": 0,
  "msg": "ok",
  "data": {
    "file_id": "EQfLmhXnmxMB7UQE4v3urx2YuK982rEbE",
    "drive_id": "8001234567",
    "parent_id": "0",
    "link_id": "dpjw3VgQkZrm",
    "name": "Q1区域销售周报.otl",
    "suffix": ".otl",
    "link_url": "https://www.kdocs.cn/l/dpjw3VgQkZrm",
    "bytes_written": 2048,
    "records_written": 0,
    "fields_written": 0,
    "sheets_written": 0,
    "sheet_id": 0,
    "warnings": []
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.file_id` | string | 新建文件 ID |
| `data.drive_id` | string | 云盘 ID |
| `data.parent_id` | string | 父文件夹 ID；根目录为 "0"；渠道 parent_path 创建时以上游解析结果为准 |
| `data.link_id` | string | 分享链接 ID |
| `data.name` | string | 文件名 |
| `data.suffix` | string | 文件后缀，如 .docx .md .otl .dbt |
| `data.link_url` | string | 可直接打开和分享的链接 |
| `data.bytes_written` | number | 文本类（.otl/.docx/.md/.pdf 等）本次写入字节数；其余后缀为 0 |
| `data.records_written` | number | dbt 本次插入条数；其余后缀为 0 |
| `data.fields_written` | number | dbt 本次建列数；未传 fields 为 0 |
| `data.sheets_written` | number | 表格类（.xlsx/.ksheet 等）本次写入表数 |
| `data.sheet_id` | number | 表格/多维表本次写入目标表 ID |
| `data.warnings` | array | 非致命提示（如未传 sheet_name 时默认首张表）；不表示写入失败 |
| `data.action` | string | created_with_content 已写入内容 |


---

## 3. create_folder

#### 功能说明

在云盘下新建文件夹。该工具只用于文件夹创建，`name` 传文件夹名即可，不要附带文件后缀。

新建到个人根：盘和目录都不传。新建到某文件夹：只传 `parent_id`。规则见 `file-locating-guide`。

#### 工具选择

- **适用**：仅创建文件夹时
- **勿用**（改用 `create_file_with_content`）：创建文件（非文件夹） — 仅需空白时用 create_empty_file

#### 调用约束

- **前置检查**：list_my_files 或 list_files 在父目录按名匹配，避免重复创建同名目录
- **禁止**：name 仅传目录名，不要附带文件后缀
- **后置验证**：get_file_info 确认目录已创建

**幂等性**：否 — 先 list_my_files/list_files 匹配已有文件夹；仅确认不存在时再 create_folder（on_name_conflict=rename）；勿全库 search_files

#### 调用示例

在指定目录创建文件夹（只传 parent_id）：

```json
{
  "parent_id": "string",
  "name": "2026年合同归档",
  "on_name_conflict": "rename"
}
```

在个人根创建文件夹（盘和目录都不传）：

```json
{
  "name": "临时资料",
  "on_name_conflict": "rename"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID。不传则使用个人云盘
- `parent_id` (string, 可选): 父文件夹 ID，根目录为 "0"。"0" 是某个盘的根，不是个人盘根；不传则使用个人云盘根
- `name` (string, 必填): 文件夹名称（不带文件后缀），如 `2026年项目归档`
- `on_name_conflict` (string, 可选): 文件夹同名冲突处理方式。可选值：`fail` / `rename` / `overwrite` / `replace`；默认值：`rename`
- `parent_path` (array[string], 可选): 相对路径（每段为文件目录名，非 ID），不存在则自动创建

#### 返回值说明

```json
{
  "data": {
    "created_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "ctime": 0,
    "drive_id": "string",
    "ext_attrs": [
      { "name": "string", "value": "string" }
    ],
    "id": "string",
    "link_id": "string",
    "link_url": "string",
    "modified_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "mtime": 0,
    "name": "string",
    "parent_id": "string",
    "shared": true,
    "size": 0,
    "type": "folder",
    "version": 0
  },
  "code": 0,
  "msg": "string"
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


---

## 4. scrape_progress

#### 功能说明

查询网页剪藏任务进度并自动创建智能文档，与 `scrape_url` 配合使用。

#### 调用约束

- **前置检查**：先调用 `scrape_url` 获取 `job_id`，本接口才可用

**幂等性**：是

> status=1 时停止轮询，获取 scrape_file_id
> status=-1 时停止轮询，任务失败
> 其他状态继续轮询（建议间隔 2-3 秒，最多轮询 30 次）

#### 调用示例

查询剪藏进度：

```json
{
  "job_id": "task_1234567890"
}
```

#### 参数说明

- `job_id` (string, 必填): 异步任务 ID（由 `scrape_url` 返回的 `job_id` 字段）

#### 返回值说明

```json
{
    "code": 0,
    "data": {
        "scrape_file_id": 501370651020,
        "link_url": "https://www.kdocs.cn/l/dpjw3VgQkZrm",
        "status": 1,
        "file_name": "［麦理浩径二段精华段+大湾海滩］周四：3月19日 麦径二段12公里徒步，超适合新手小白！.otl",
        "parent_id": 498552876371,
        "group_id": 1231238091,
        "cache": 0,
        "core_err": null
    },
    "msg": "成功"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.scrape_file_id` | number | 剪藏专用文档标识 |
| `data.link_url` | string | 剪藏内容写入智能文档链接 |
| `data.status` | number | 任务状态: 1=完成, -1=失败, 其他=进行中 |
| `data.file_name` | string | 文件名 |
| `data.parent_id` | number | 父目录ID |
| `data.group_id` | number | 组ID |
| `data.cache` | number | 缓存标识 |
| `data.core_err` | string | 内核错误信息 |


---

## 5. scrape_url

#### 功能说明

网页剪藏：抓取网页内容并自动保存为智能文档。这是获取外部网页内容的唯一正确方式，不要使用其他方式访问 URL。

#### 调用流程
1. 调用 `scrape_url` 传入网页 URL，获取返回值中的 `job_id`
2. 立即调用 `scrape_progress` 传入 `job_id` 参数（值为上一步的 `job_id`），每隔 2 秒轮询一次
3. 当 `status=1` 时任务完成，服务端已自动创建智能文档

#### 工具选择

- **适用**：用户发送、分享或提到外部网页 URL，需抓取并保存为智能文档时
- **勿用**（改用 `read_file`）：URL 属于金山文档生态（kdocs.cn / 365.kdocs.cn / wps.cn 文档域、分享页 /l/ /view/l/ /folder/ 等） — 属于「已有云文档」场景，勿当网页剪藏

**幂等性**：否 — 重试前查 scrape_progress 确认上次状态

> 返回 job_id 后需立即调用 scrape_progress 轮询（参数名为 job_id，值为本接口返回的 job_id）
> 每隔2秒轮询一次，status=1 时完成

#### 调用示例

剪藏网页：

```json
{
  "url": "https://example.com/article"
}
```

#### 参数说明

- `url` (string, 必填): 要剪藏的网页URL地址，支持http和https协议

#### 返回值说明

```json
{
  "job_id": "13883829803456643124541",
  "parent_id": 498552876371,
  "group_id": 1231238091
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | string | 异步任务ID |
| `parent_id` | number | 父目录ID |
| `group_id` | number | 组ID |


---

## 6. upload_new_file

#### 功能说明

本地已有文件（或需整文件 Base64 上传）时用本工具新建云文档。

**传入带后缀的 `name`；`content_base64` 是完整源文件内容经过 Base64 编码后得到的字符串，不是文件路径或正文原文。**

支持后缀：`.doc` / `.docx` / `.xls` / `.xlsx` / `.ppt` / `.pptx` / `.pdf` / `.md` / `.txt` / `.html` / `.zip` / `.png` / `.jpg` / `.jpeg` / `.csv` / `.json` / `.dps` / `.et` / `.wps` / `.gif`。

**`drive_id` / `parent_id`**（非必填）：

- **未指定位置**：两参数可省略（默认个人云盘根）。
- **用户已说明目标文件夹**：只传 `parent_id`（文件夹 id）；`drive_id` 由服务端按文件夹自查，不要自己配。

#### 工具选择

- **适用**：本地已有文件需上传新建云文档时
- **勿用**（改用 `create_file_with_content`）：对话内直接撰写内容新建文档
- **勿用**（改用 `create_file_with_content`）：本地 Markdown 需新建为 otl/docx/pdf

#### 调用约束

- **后置验证**：写入后通过返回 size 或小文件 read_file 确认结果；zip/png/jpg/gif/json/dps/et/wps 等 read_file 不支持时用 get_file_info 校验

**幂等性**：是

#### 调用示例

`hello.txt` 的内容为 `Hello`，按 UTF-8 编码后再转为 Base64，结果是 `SGVsbG8=`：

```json
{
  "name": "hello.txt",
  "content_base64": "SGVsbG8="
}
```

新建 PDF 并写入（二进制 PDF Base64）：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "name": "2024年度报告.pdf",
  "content_base64": "JVBERi0xLjQK..."
}
```

新建 WPS 原生文字文件：

```json
{
  "name": "报告.wps",
  "content_base64": "<本地 .wps 二进制 Base64>"
}
```

原样上传 Markdown 文件：

```json
{
  "name": "会议纪要.md",
  "content_base64": "<Markdown UTF-8 文本的 Base64>"
}
```

Markdown 新建文件：

```json
{
  "name": "会议纪要.docx",
  "content_base64": "<Markdown UTF-8 文本的 Base64>",
  "content_format": "markdown"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID。规则见 `references/file-locating-guide.md`。
- `parent_id` (string, 可选): 父文件夹 ID，根目录为 "0"。"0" 是某个盘的根，不是个人盘根；不传则使用个人云盘根
- `name` (string, 必填): 必填。文件名**必须带以下后缀之一**：`.doc` / `.docx` / `.xls` / `.xlsx` / `.ppt` / `.pptx` / `.pdf` / `.md` / `.txt` / `.html` / `.zip` / `.png` / `.jpg` / `.jpeg` / `.csv` / `.json` / `.dps` / `.et` / `.wps` / `.gif`
- `content_base64` (string, 必填): **必填**。源文件内容的 Base64 编码。必须先读取文件二进制内容再做 Base64 编码；原样上传 .md/.txt 时为 UTF-8 文本的 Base64
- `content_format` (string, 可选): 源内容格式。目标后缀须与源一致；传 `markdown` 且目标为 docx/pdf 时服务端会转换后再上传。可选值：`doc` / `docx` / `xls` / `xlsx` / `ppt` / `pptx` / `pdf` / `md` / `txt` / `html` / `zip` / `png` / `jpg` / `jpeg` / `csv` / `json` / `dps` / `et` / `wps` / `gif` / `markdown`
- `file_sum` (string, 可选): 文件哈希值，不传则服务端按内容计算
- `file_type` (string, 可选): 哈希类型。可选值：`sha256` / `md5` / `sha1`
- `parent_path` (array[string], 可选): 父文件夹路径分段（文件夹名，非 ID）。新建时按文件夹名指定父路径

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
    "name": "2024年度报告.pdf",
    "link_url": "https://www.kdocs.cn/l/dpjw3VgQkZrm",
    "size": 57081
  }
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


---

## 7. upload_replace_file

#### 功能说明

通过上传本地文件**全量覆盖**已有云文档；局部编辑（单元格、段落等）请使用 sheet.*/wps.*/otl.* 等编辑工具。

**支持覆盖的类型**：doc、docx、xls、xlsx、ppt、pptx、pdf、md、txt、html、zip、png、jpg、jpeg、csv、json、dps、et、wps、gif。

**不支持**：otl、dbt、ksheet 等（局部编辑走域工具）。

**`drive_id` / `parent_id`**：建议先 `get_file_info(file_id)`，与目标文件所在盘、父目录一致。

#### 工具选择

- **适用**：以本地整文件覆盖已有云文档（非 .otl）时
- **勿用**（改用 `otl.insert_content`）：覆盖 .otl 智能文档 — 智能文档新建用 create_file_with_content，已有文档追加用 otl.insert_content

#### 调用约束

- **禁止**：勿用于 .otl 智能文档覆盖；智能文档新建用 create_file_with_content，已有文档追加用 otl.insert_content
- **后置验证**：写入后确认结果：通过接口返回的 size 字段判断；小文件且 read_file 支持时用 read_file 确认；zip/png/jpg/gif/json/dps/et/wps 等用 get_file_info 校验大小/版本

**幂等性**：是

> 调用前确认目标文档 file_id；类型不明时先 get_file_info。本地整文件直接覆盖不必先 read_file；仅在基于现有正文改写后再覆盖时再 read_file（zip/图片等 read_file 不支持时只用 get_file_info 校验）

#### 调用示例

同类型覆盖（docx → docx）：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
  "content_base64": "<本地 .docx 二进制 Base64>"
}
```

xlsx 整文件覆盖：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
  "content_base64": "<本地 xlsx 二进制 Base64>"
}
```

Markdown 覆盖（转为 docx/pdf）：

```json
{
  "file_id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
  "content_base64": "<Markdown 内容的 Base64>",
  "content_format": "markdown"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标云盘 ID，建议与目标文件所在盘一致
- `parent_id` (string, 可选): 父文件夹 ID，根目录为 "0"。建议与目标文件父目录一致
- `file_id` (string, 必填): 必填。要覆盖的文件 ID。支持 doc / docx / xls / xlsx / ppt / pptx / pdf / md / txt / html / zip / png / jpg / jpeg / csv / json / dps / et / wps / gif
- `content_base64` (string, 必填): **必填**。源文件内容的 Base64 编码。必须先读取文件二进制内容再做 Base64 编码；Markdown 文本需 UTF-8 编码后 Base64，并传 `content_format=markdown`（仅目标 docx/pdf）
- `content_format` (string, 可选): 源内容格式。传 `markdown` 时服务端转为 docx/pdf 后上传（仅目标为 docx/pdf）。可选值：`doc` / `docx` / `xls` / `xlsx` / `ppt` / `pptx` / `pdf` / `md` / `txt` / `html` / `zip` / `png` / `jpg` / `jpeg` / `csv` / `json` / `dps` / `et` / `wps` / `gif` / `markdown`
- `file_sum` (string, 可选): 文件哈希值，不传则服务端按内容计算
- `file_type` (string, 可选): 哈希类型。可选值：`sha256` / `md5` / `sha1`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
    "name": "2024年度报告.docx",
    "link_url": "https://www.kdocs.cn/l/dpjw3VgQkZrm",
    "size": 57081,
    "version": 2
  }
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


---

## 8. upload_attachment

#### 功能说明

向已有文档上传附件，支持传远程 URL 或本地二进制内容（Base64）。
返回 `object_id`，可用于文档内附件或图片引用。

支持两种上传方式：
- 远程 URL：传 `url`
- 本地二进制：传 `content_base64`

**幂等性**：否 — 重复调用会上传多个副本，先确认是否已成功

> url 与 content_base64 必须二选一

#### 调用示例

通过 URL 上传附件：

```json
{
  "file_id": "string",
  "filename": "头像.png",
  "url": "https://img.qwps.cn/example.png",
  "source_type": "url",
  "source": "processon"
}
```

通过 Base64 上传本地附件：

```json
{
  "file_id": "string",
  "filename": "附件.pdf",
  "content_base64": "JVBERi0xLjQK...",
  "content_type": "application/pdf"
}
```

#### 参数说明

- `file_id` (string, 必填): 已有文件 ID
- `filename` (string, 必填): 附件名
- `url` (string, 二选一必填: `url` / `content_base64`): 远程附件 URL，条件必填。与 content_base64 二选一
- `content_base64` (string, 二选一必填: `url` / `content_base64`): 本地附件内容的 Base64 编码，条件必填。与 url 二选一
- `content_type` (string, 可选): 附件 MIME 类型，可选；content_base64 模式下不传则默认 application/octet-stream
- `source_type` (string, 可选): 上传内容类型，可选
- `source` (string, 可选): 来源标记，可选；如 processon

#### 返回值说明

```json
{
  "result": "ok",
  "object_id": "1234567890",
  "extra_info": {
    "width": 600,
    "height": 400
  },
  "old_content_type": "image/jpeg",
  "new_content_type": "image/jpeg"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `object_id` | string | 附件上传后的对象 ID |
| `extra_info.width` | integer | 图片宽度（像素，仅图片类型返回） |
| `extra_info.height` | integer | 图片高度（像素，仅图片类型返回） |
| `old_content_type` | string | 原始内容类型 |
| `new_content_type` | string | 转换后内容类型 |
