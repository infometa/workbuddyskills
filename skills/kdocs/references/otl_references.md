# 智能文档（otl）工具完整参考文档

金山文档智能文档（otl）提供了专属的内容写入接口，支持以 Markdown 格式向文档插入内容（标题、文本、列表等），系统自动转换为富文本格式。

---

## 前置说明（重要）
当终端为powershell时，为避免转义问题，你可以**必须**以下方式传入JSON参数!!
### JSON 参数传递方式
#### 方式一：`--%` 内联（适合简短参数）
PowerShell 中用 `--%` 停止解析，双引号用 `\"` 转义：

示例
```powershell
mcporter call kdocs otl.block_query --args '{\"file_id\":\"cqTNWO4EMAn9\",\"params\":{\"blockIds\":[\"doc\"]}}'
```
#### 方式二：临时文件（推荐，适合大参数）
先写入 `temp.json`，再读取并转义后传给 `--args`：

示例
```powershell
$json = Get-Content -Raw -Encoding UTF8 .\temp.json
$jsonEscaped = $json -replace '"', '\"'
mcporter call kdocs otl.block_insert --args "$jsonEscaped"
```

## 通用说明

### 智能文档特点

- **推荐度**：⭐⭐⭐ **首选文档格式**
- 排版美观，支持标题、列表、待办、表格、分割线等丰富块组件
- 适合图文混排、报告撰写、知识文档、会议纪要等场景
- 是网页剪藏（`scrape_url`）的默认输出格式

### 创建智能文档

通过 `create_file` 创建，`name` 须带 `.otl` 后缀，`file_type` 设为 `file`：

```json
{
  "name": "项目周报.otl",
  "file_type": "file",
  "parent_id": "folder_abc123"
}
```

创建完成后用下文 **`otl.insert_content`** 写入 Markdown/文本。**勿**对 `.otl` 使用 `upload_file`：该工具面向本地文字/表格/演示/PDF 文件上传，不支持 `.otl` 智能文档。

### 读取智能文档

#### 首选方式：`otl.block_query`（结构化读取）

使用 `otl.block_query` 查询文档块结构与内容，能完整获取文档的层级信息和全部块类型。传入 `blockIds: ["doc"]` 可获取全文：

```json
{
  "file_id": "file_otl_001",
  "params": { "blockIds": ["doc"] }
}
```

#### 备选方式：`read_file_content`（Markdown 导出）

> ⚠️ `read_file_content` 对智能文档存在**内容遗漏风险**——部分组件类型（如嵌入表格、附件、特殊块）可能在转换过程中丢失。**仅在需要将文档导出为 Markdown 格式时使用**，日常读取和编辑前的内容确认应优先使用 `otl.block_query`。

##### 步骤 1：提交读取任务

调用参数：

```json
{
  "drive_id": "drive_abc123",
  "file_id": "file_otl_001",
  "format": "markdown",
  "include_elements": ["all"]
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `drive_id` | string | 是 | 文件所在云盘 ID |
| `file_id` | string | 是 | 文件 ID |
| `format` | string | 是 | 固定传 `"markdown"` |
| `include_elements` | array | 是 | 固定传 `["all"]` |

> **⚠️ mcporter CLI 调用注意**：`include_elements` 是**数组**，`key=value` 语法无法可靠传递数组。请用 `--args` 传递数组参数，其余参数可用 `key=value`。**`--args` 的 JSON 必须用单引号 `'...'` 包裹，内部双引号用 `\"` 转义**：
>
> ```shell
> mcporter call kdocs read_file_content drive_id=<DRIVE_ID> file_id=<FILE_ID> format=markdown --args '{\"include_elements\":[\"all\"]}'
> ```
>
> **禁止**省略外层单引号——不加单引号会导致 shell 解析错误。

##### 步骤 2：轮询获取内容

将步骤 1 返回的 `task_id` 加入参数再次调用：

```json
{
  "drive_id": "drive_abc123",
  "file_id": "file_otl_001",
  "format": "markdown",
  "include_elements": ["all"],
  "task_id": "步骤1返回的task_id"
}
```

> **mcporter CLI 轮询命令**（替换 `<TASK_ID>` 为步骤 1 返回值；**单引号必须保留**）：
>
> ```shell
> mcporter call kdocs read_file_content drive_id=<DRIVE_ID> file_id=<FILE_ID> format=markdown --args '{\"include_elements\":[\"all\"]}' task_id=<TASK_ID>
> ```

> ⚠️ **`include_elements` 必须是数组** `["all"]`，不是字符串 `"all"`。传错类型会导致服务端仅返回段落文本。


# 将 Markdown/纯文本数据直接写入智能文档

调用 `otl.insert_content` 工具，向智能文档写入 Markdown 或纯文本内容。支持从文档开头或末尾插入。支持修改文档标题。

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `content` (string, 必填): 写入内容，支持 Markdown 或纯文本
- `title` (string, 可选): 文档标题
- `pos` (string, 可选): 插入位置 — `begin` = 从文档开头插入，`end` = 在文档末尾追加；默认 `begin`

---

## 返回值说明

`data.result` 为 `"ok"` 表示写入成功。

---

## 调用示例

从文档开头写入：

```json
{
  "pos": "begin",
  "content": "# 项目周报\n\n## 本周进展\n\n- 完成需求评审\n- 启动开发任务"
}
```

在文档末尾追加：

```json
{
  "pos": "end",
  "content": "## 补充说明\n\n以上数据截至本周五。"
}
```

带标题写入：

```json
{
  "pos": "begin",
  "title": "项目周报",
  "content": "# 项目周报\n\n正文内容"
}
```

---

## 典型用法

1. **新建文档并写入**：先 `create_file` 创建 `.otl` 文件，再调用 `otl.insert_content` 写入内容
2. **追加内容**：对已有文档，`pos=end` 在末尾追加新内容
3. **覆盖开头**：`pos=begin` 从文档开头插入（不会删除已有内容，而是插入到前面）

---

## 注意事项

1. 如需精确修改文档中某个块，应使用 `otl.block_query` → `otl.block_delete` / `otl.block_insert` 组合

2. 对于数据中Unicode制表图，有以下注意事项：

若 `content` 里用 `┌` `─` `│` `┐` `└` `┘` `┼` 等 Unicode 制表字符画的架构图、数据流、框图等**落在普通段落或列表里**，智能文档会按富文本渲染（比例字体、空白与换行处理），容易出现**线条错位、框线对不齐
| 源内容状态 | 写入时怎么做 |
| :--- | :--- |
| 制表字符**未**在围栏代码块中 | 用围栏代码块（语言标签 `text` 或 `plain`）包裹**制表段**后再写入；只包裹图，不包裹全部内容 |
| 制表字符**已**在围栏代码块中 | 原样写入，不要再套一层围栏 |

**示例**：下列片段表示写入 `content` 时，**制表段已被围栏代码块包裹**的推荐形态。

````markdown
## 4.1 整体架构

```text
┌──────────────┐     ┌──────────────┐
│  用户交互层   │────▶│   智能体层    │
└──────────────┘     └──────────────┘
```
````

Mermaid、PlantUML 等需单独渲染引擎的制表图不在此列；此处仅针对**纯文本 Unicode/ASCII 制表图**

# 将 HTML/Markdown 数据转为智能文档的块数据

调用 `otl.convert` 工具，传入智能文档的 `file_id` 和转换参数，即可将 HTML 或 Markdown 内容转换为智能文档块结构。适合在正式插入前先生成可复用的块内容。

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 转换参数对象
  - `format` (string, 必填): 源数据格式，支持 `"html"` 或 `"markdown"`
  - `content` (string, 必填): 待转换的源数据内容

---

## 返回值说明

返回结果中 `blocks` 字段为转换得到的块数组，可直接用于 `otl.block_insert` 插入至文档。块类型和属性说明见 `references/otl_execute/node.md`。

---

## 调用示例

将 Markdown 内容转为块数据：

```json
{
  "params": {
    "format": "markdown",
    "content": "# 标题\n\n段落内容"
  }
}
```

将 HTML 内容转为块数据：

```json
{
  "params": {
    "format": "html",
    "content": "<h1>标题</h1><p>段落内容</p>"
  }
}
```

---

## 典型用法

1. **外部内容转块后插入**：先调用 `otl.convert` 将 HTML/Markdown 转为块结构，再调用 `otl.block_insert` 将转换结果插入文档
2. **预览转换结果**：在正式写入前，通过 convert 预先查看块结构是否符合预期

---

## 注意事项

1. `otl.convert` 仅做格式转换，不会修改文档内容；需配合 `otl.block_insert` 才能将转换结果写入文档
2. `content` 中如包含换行符，使用 `\n` 表示
3. `format` 只支持 `"html"` 和 `"markdown"` 两种值


# 读取智能文档中的块

调用 `otl.block_query` 工具，传入智能文档的 `file_id` 和查询参数，即可读取指定块的结构与内容。适合在更新或删除前先获取目标块信息。

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 查询参数对象
  - `blockIds` (array, 必填): 要查询的块 ID 列表， 块ID为"doc"可查询完整文档块

---

## 调用示例

查询文档根块：

```json
{
  "params": {
    "blockIds": ["doc"]
  }
}
```

查询多个指定块：

```json
{
  "params": {
    "blockIds": ["blockId_1", "blockId_2"]
  }
}
```

---

## 典型用法

1. **获取文档完整数据**：`blockIds` 传 `["doc"]`，返回文档块（含各子块的 `blockId`、类型等）
2. **查询子块**：从步骤 1 的返回结果中取出子块 ID，在需要时再次调用 `otl.block_query` 查询该子块

---

## 注意事项

1. 查询得到的块类型和属性具体含义可参考 `references/otl_execute/node.md`


# 在智能文档指定位置插入内容

调用`otl.block_insert`工具，传入智能文档的 `file_id` 和相关参数，可在指定位置插入内容，适合局部新增。

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 插入操作
  - `blockId` (string, 必填): 目标父块 ID，为"doc"表示在文档中插入，其他块ID可通过查询块获得
  - `index` (integer, 必填): 插入位置索引
  - `content` (array, 必填): 待插入的节点数组，节点类型和属性可参考`references/otl_execute/node.md`

---

## 调用示例

在文档开头插入段落节点

```json
{
  "params": {
    "blockId": "doc",
    "index": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "content": "一些文字"
          }
        ]
      }
    ]
  }
}
```

将段落的首个子节点后插入文本节点

```json
{
  "params": {
    "blockId": "PARA_ID",
    "index": 1,
    "content": [
      {
        "type": "text",
        "content": "希望插入的文字"
      }
    ]
  }
}
```

## 典型用法

1. **文档内插入新内容**： blockId设置为"doc"，确定好插入index和插入的子节点。 插入子节点的类型和属性可参考 `references/otl_execute/node.md`
2. **段落内插入新文本**: blockId设置为通过查询得到的段落id，确定好插入index和插入的子节点。插入子节点的类型和属性可参考 `references/otl_execute/node.md`

--- 

## 注意事项

1. 当blockId为"doc"时，index必须大于等于1，因为doc的首个子节点必须是title（全局唯一），如果需要在正文开头插入内容，index应为1。 
2. 若查询到的块的content里包含rangeMarkBegin或rangeMarkEnd，计算index时应忽略它们，它们是虚拟节点。


# 在智能文档指定位置删除内容

调用`otl.block_delete`工具，传入智能文档的 `file_id` 和相关参数，可在指定位置插入内容，适合局部删除

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 删除操作
  - `blockId` (string, 必填): 目标父块 ID，为"doc"表示删除文档块的子节点，其他块ID可通过查询块获得
  - `startIndex` (integer, 必填): 删除的起始索引（操作区间左闭右开），startIndex 需要小于 endIndex
  - `endIndex` (integer, 必填): 删除的末尾索引（操作区间左闭右开），startIndex 需要小于 endIndex

---

## 调用示例

清空文档标题

```json
{
  "params": {
    "blockId": "doc",
    "startIndex": 0,
    "endIndex": 1
  }
}
```

删除文档正文首个块

```json
{
  "params": {
    "blockId": "doc",
    "startIndex": 1,
    "endIndex": 2
  }
}
```

删除段落的首个子节点

```json
{
  "params": {
    "blockId": "PARA_ID",
    "startIndex": 0,
    "endIndex": 1
  }
}
```

## 典型用法

1. **清空文档标题**： blockId设置为"doc",startIndex设置为0，endIndex设置为1，可清空文档标题。
2. **删除某个块的子节点**: blockId设置为通过查询得到的块id，确定好startIndex和endIndex，调用工具即可。

## 注意事项

1. 删除操作不可逆，请确保删除的内容确实不需要再进行该操作！！！
2. 若查询到的块的content里包含rangeMarkBegin或rangeMarkEnd，计算startIndex和endIndex时应忽略它们，它们是虚拟节点。


# 更新智能文档
调用`otl.block_update`工具，传入智能文档的 `file_id` 和相关参数，可更新指定块，适合局部更新或者更新Markdown数据不支持的内容。

当前支持以下操作：
1. 更新块的内容
2. 更新块的属性
3. 插入表格行
4. 插入表格列
5. 删除表格行
6. 删除表格列
7. 合并单元格
8. 拆分单元格

---

## 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (array, 必填): 操作数组，各类型操作参数参考下方

---

## 各类型操作参数

### 更新块的内容

- `blockId` (string, 必填): 块ID，为"doc"表示更新全文内容，其余子块ID可通过查询文档块获取。
- `operation` (string, 必填): 固定为"update_content"
- `content` (array, 必填)： 块的内容，其中可填入的节点类型和属性参考`references/otl_execute/node.md`

#### 调用示例

覆盖文档的标题和正文

```json
{
  "params": [
    {
      "operation": "update_content",
      "blockId": "doc",
      "content": [
        {
          "type": "title",
          "content": [
            {
              "type": "text",
              "content": "文档的标题"
            }
          ]
        },
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "content": "文档的正文"
            }
          ]
        }
      ]
    }
  ]
}
```

更新段落的文本内容

```json
{
  "params": [
    {
      "operation": "update_content",
      "blockId": "PARA_ID",
      "content": [
        {
          "type": "text",
          "content": "更新的文本内容"
        }
      ]
    }
  ]
}
```

#### 注意事项
1. 块支持的子节点，参考`references/otl_execute/node.md`
2. 当blockId为"doc"时，第一个子节点必须是title

### 更新块属性

- `blockId` (string, 必填): 块ID，可通过查询文档块获取。
- `operation` (string, 必填): 固定为"update_attrs"
- `attrs` (object, 必填)： 块的属性，属性参考`references/otl_execute/node.md`，当前不支持设置doc、appComponent、lockBlock这三种块的属性，tableCell的colSpan/rowSpan属性请通过下方表格相关操作设置。

#### 调用示例

更新段落的背景颜色

```json
{
  "params": [
    {
      "operation": "update_attrs",
      "blockId": "PARA_ID",
      "attrs": {
        "color": {
          "backgroundColor": "#FBF5B3"
        }
      }
    }
  ]
}
```

#### 注意事项
1. 更新属性是覆盖操作，不需要更新的属性保持原样传入
2. 当前不支持设置doc、appComponent、lockBlock这三种块的属性
3. 本操作不支持设置tableCell的rowSpan/colSpan属性

### 插入表格行

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。
- `operation` (string, 必填): 固定为"insert_table_rows"
- `content` (array, 必填)： tableRow数组，需与表格列数对齐。tableRow节点参考`references/otl_execute/node.md`
- `start` (integer, 非必填)：插入的行索引，默认0

#### 调用示例

```json
{
  "params": [
    {
      "operation": "insert_table_rows",
      "blockId": "TABLE_ID",
      "content": [
        {
          "type": "tableRow",
          "content": [
            {
              "type": "tableCell",
              "content": [
                {
                  "type": "paragraph",
                  "content": [
                    {
                      "type": "text",
                      "content": "1111"
                    }
                  ]
                }
              ]
            },
            {
              "type": "tableCell"
            }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            {
              "type": "tableCell"
            },
            {
              "type": "tableCell"
            }
          ]
        }
      ]
    }
  ]
}
```

#### 注意事项
1. 表格行里的单元格数量，需与表格列数对齐。

### 插入表格列

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。
- `operation` (string, 必填): 固定为"insert_table_columns"
- `content` (array, 必填)： tableRow数组，需与表格行数对齐。tableRow节点参考`references/otl_execute/node.md`
- `start` (integer, 非必填)：插入的列索引，默认0

#### 调用示例

```json
{
  "params": [
    {
      "operation": "insert_table_columns",
      "blockId": "TABLE_ID",
      "content": [
        {
          "type": "tableRow",
          "content": [
            {
              "type": "tableCell",
              "content": [
                {
                  "type": "paragraph",
                  "content": [
                    {
                      "type": "text",
                      "content": "1111"
                    }
                  ]
                }
              ]
            },
            {
              "type": "tableCell"
            }
          ]
        },
        {
          "type": "tableRow",
          "content": [
            {
              "type": "tableCell"
            },
            {
              "type": "tableCell"
            }
          ]
        }
      ]
    }
  ]
}
```

#### 注意事项
1. content字段里的表格行数量，要与表格行数对齐。每个表格行的单元格数量也需要一致。

### 删除表格行

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。
- `operation` (string, 必填): 固定为"delete_table_rows"
- `count` (integer, 必填)： 删除行数，至少为1
- `start` (integer, 非必填)：删除起始索引，默认0

#### 调用示例

```json
{
  "params": [
    {
      "operation": "delete_table_rows",
      "blockId": "TABLE_ID",
      "count": 2,
      "start": 2
    }
  ]
}
```

### 删除表格列

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。
- `operation` (string, 必填): 固定为"delete_table_columns"
- `count` (integer, 必填)： 删除行数，至少为1
- `start` (integer, 非必填)：删除起始索引，默认0

#### 调用示例

```json
{
  "params": [
    {
      "operation": "delete_table_columns",
      "blockId": "TABLE_ID",
      "count": 2,
      "start": 2
    }
  ]
}
```

### 合并单元格

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。
- `operation` (string, 必填): 固定为"merge_table_cells"
- `rowSpan` (integer, 必填)： 合并行数，至少为1，与colSpan不可同时为1
- `colSpan` (integer, 必填)： 合并列数，至少为1，与rowSpan不可同时为1
- `startRow` (integer, 非必填)：合并的起始行号，默认0
- `startCol` (integer, 非必填)：合并的起始列号，默认0

#### 调用示例

```json
{
  "params": [
    {
      "operation": "merge_table_cells",
      "blockId": "TABLE_ID",
      "rowSpan": 2,
      "colSpan": 3,
      "startRow": 1,
      "startCol": 1
    }
  ]
}
```

### 拆分单元格

- `blockId` (string, 必填): 块ID，可通过查询文档块获取，对应块必须是table。拆分对应的单元格必须是合并单元格
- `operation` (string, 必填): 固定为"split_table_cell"
- `startRow` (integer, 非必填)：拆分单元格的行号，默认0
- `startCol` (integer, 非必填)：拆分单元格的列号，默认0

```json
{
  "params": [
    {
      "operation": "split_table_cell",
      "blockId": "TABLE_ID",
      "startRow": 1,
      "startCol": 1
    }
  ]
}
```

---

## 智能文档（otl）专属接口

### 1. otl.insert_content

#### 功能说明

向智能文档写入 Markdown/纯文本内容。支持从文档开头或末尾插入，写入时系统自动转换为智能文档富文本格式。


#### 调用示例

从开头写入：

```json
{
  "file_id": "string",
  "title": "项目周报",
  "content": "# 项目周报\n\n## 本周进展\n\n- 完成需求评审\n- 启动开发任务",
  "pos": "begin"
}
```

在末尾追加：

```json
{
  "file_id": "string",
  "title": "补充内容",
  "content": "## 补充说明\n\n以上数据截至本周五。",
  "pos": "end"
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `title` (string, 可选): 文档标题
- `content` (string, 必填): 写入内容，支持 Markdown 或纯文本
- `pos` (string, 可选): 插入位置，begin=从文档开头插入，end=在文档末尾追加。可选值：`begin` / `end`；默认值：`begin`

#### Unicode 制表图（架构图、数据流等）

**现象**：若 `content` 里用 `┌` `─` `│` `┐` `└` `┘` `┼` 等 Unicode 制表字符画的架构图、数据流、框图等**落在普通段落或列表里**，智能文档会按富文本渲染（比例字体、空白与换行处理），容易出现**线条错位、框线对不齐**。

**原则**：只对**改写前**的源 Markdown 判断一次——这段制表内容**是否已经**在 Markdown **围栏代码块**里。

| 源内容状态 | 写入 `content` 时怎么做 |
| :--- | :--- |
| **尚未**在围栏代码块里（制表字符裸露在段落、列表等中） | 把**整段**制表内容用围栏代码块包裹再写入；**只包裹图，不包裹全部Markdown内容**；语言标签推荐 `text` 或 `plain`。写入后，该段在文档中一般为 **Plain Text** 代码块，等宽显示，对齐可保留。 |
| **已经**在围栏代码块里（含 `text` / `plain` 或未标注语言的代码块） | **原样写入**，勿再套一层围栏。 |

**示例**：下列片段表示写入 `content` 时，**制表段已被围栏代码块包裹**的推荐形态。

````markdown
## 4.1 整体架构

```text
┌──────────────┐     ┌──────────────┐
│  用户交互层   │────▶│   智能体层    │
└──────────────┘     └──────────────┘
```
````

> **说明**：Mermaid、PlantUML 等需单独渲染引擎的制表图不在此列；此处仅针对**纯文本 Unicode/ASCII 制表图**。


#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": "ok"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.result` | string | ok 表示成功 |


#### 操作约束

- **前置检查**：先 otl.block_query 读取现有内容，了解文档当前状态
- **提示**：仅支持插入操作（begin/end），不支持替换已有内容
---

### 2. otl.block_insert

#### 功能说明

向智能文档插入一个或多个块，适合在指定父块下按位置追加段落、列表、表格等结构化内容。


#### 调用示例

在文档开头插入段落：

```json
{
  "file_id": "string",
  "params": {
    "blockId": "doc",
    "index": 1,
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "content": "hello"
          }
        ]
      }
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 插入操作
  - `blockId` (string, 常用): 目标父块 ID，例如 `doc`
  - `index` (integer, 常用): 插入位置索引
  - `content` (array, 常用): 待插入的块内容数组

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```


#### 操作约束

- **前置检查**：先 otl.block_query 了解文档块结构，确认插入位置
- **提示**：返回结果因内容和文档状态不同而异，以 code == 0 判断成功
---

### 3. otl.block_delete

#### 功能说明

删除一个或多个块区间，适合按父块和索引范围删除内容。


#### 调用示例

删除指定块区间：

```json
{
  "file_id": "string",
  "params": {
    "blockId": "父blockId",
    "startIndex": 0,
    "endIndex": 1
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 删除操作
  - `blockId` (string, 常用): 目标父块 ID
  - `startIndex` (integer, 常用): 删除起始索引
  - `endIndex` (integer, 常用): 删除结束索引

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```


#### 操作约束

- **用户确认**：删除操作不可逆，执行前必须向用户确认删除范围
- **前置检查**：先 otl.block_query 确认待删除块的内容，避免误删
---

### 4. otl.block_query

#### 功能说明

查询指定块的结构与内容，适合在更新前先读取目标块信息。


#### 调用示例

查询全文：

```json
{
  "file_id": "string",
  "params": {
    "blockIds": [
      "doc"
    ]
  }
}
```

查询指定块：

```json
{
  "file_id": "string",
  "params": {
    "blockIds": [
      "目标blockId"
    ]
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 查询参数对象
  - `blockIds` (array, 常用): 要查询的块 ID 列表

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```

---

### 5. otl.convert

#### 功能说明

将 HTML、Markdown 等内容转换为智能文档块结构，适合在正式插入前先生成可复用的块内容。


#### 调用示例

转换内容：

```json
{
  "file_id": "string",
  "params": {
    "...": "..."
  }
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (object, 必填): 转换参数对象。根据待转换内容类型填写对应字段

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```

---

### 6. otl.block_update

#### 功能说明

更新指定块的内容或属性，支持多种操作：更新块内容、更新块属性、插入/删除表格行列、合并/拆分单元格。适合局部更新或处理 Markdown 数据不支持的内容。


#### 调用示例

更新块内容（覆盖文档标题和正文）：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "update_content",
      "blockId": "doc",
      "content": [
        {
          "type": "title",
          "content": [
            {
              "type": "text",
              "content": "文档的标题"
            }
          ]
        },
        {
          "type": "paragraph",
          "content": [
            {
              "type": "text",
              "content": "文档的正文"
            }
          ]
        }
      ]
    }
  ]
}
```

更新块属性（设置段落背景色）：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "update_attrs",
      "blockId": "PARA_ID",
      "attrs": {
        "color": {
          "backgroundColor": "#FBF5B3"
        }
      }
    }
  ]
}
```

插入表格行：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "insert_table_rows",
      "blockId": "TABLE_ID",
      "start": 0,
      "content": [
        {
          "type": "tableRow",
          "content": [
            {
              "type": "tableCell",
              "content": [
                {
                  "type": "paragraph",
                  "content": [
                    {
                      "type": "text",
                      "content": "单元格内容"
                    }
                  ]
                }
              ]
            },
            {
              "type": "tableCell"
            }
          ]
        }
      ]
    }
  ]
}
```

删除表格行：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "delete_table_rows",
      "blockId": "TABLE_ID",
      "count": 2,
      "start": 0
    }
  ]
}
```

合并单元格：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "merge_table_cells",
      "blockId": "TABLE_ID",
      "rowSpan": 2,
      "colSpan": 3,
      "startRow": 0,
      "startCol": 0
    }
  ]
}
```

拆分单元格：

```json
{
  "file_id": "string",
  "params": [
    {
      "operation": "split_table_cell",
      "blockId": "TABLE_ID",
      "startRow": 0,
      "startCol": 0
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): 智能文档文件 ID
- `params` (array, 必填): 操作数组，每项为一个操作对象。所有操作必须包含 `operation` 和 `blockId`，其余字段由 `operation` 决定，详见下方各操作说明
  - `operation` (string, 必填): 操作类型
  - `blockId` (string, 必填): 目标块 ID

**各 operation 类型及其附加参数：**

**`update_content`** — 更新块的内容
- `content` (array, 必填): 新的子节点数组，节点类型参考 `references/otl_execute/node.md`
- 当 blockId 为 "doc" 时，第一个子节点必须是 title

**`update_attrs`** — 更新块的属性
- `attrs` (object, 必填): 块属性对象，属性定义参考 `references/otl_execute/node.md`
- 更新属性是覆盖操作，不需更新的属性需保持原样传入
- 不支持设置 doc、appComponent、lockBlock 的属性；tableCell 的 colSpan/rowSpan 请用表格合并/拆分操作

**`insert_table_rows`** — 插入表格行（blockId 对应的块必须是 table）
- `content` (array, 必填): tableRow 数组，单元格数量需与表格列数对齐
- `start` (integer, 可选): 插入位置行索引，默认 0

**`insert_table_columns`** — 插入表格列（blockId 对应的块必须是 table）
- `content` (array, 必填): tableRow 数组，行数需与表格行数对齐，每行的单元格数量需一致
- `start` (integer, 可选): 插入位置列索引，默认 0

**`delete_table_rows`** — 删除表格行（blockId 对应的块必须是 table）
- `count` (integer, 必填): 删除行数，至少为 1
- `start` (integer, 可选): 删除起始行索引，默认 0

**`delete_table_columns`** — 删除表格列（blockId 对应的块必须是 table）
- `count` (integer, 必填): 删除列数，至少为 1
- `start` (integer, 可选): 删除起始列索引，默认 0

**`merge_table_cells`** — 合并单元格（blockId 对应的块必须是 table）
- `rowSpan` (integer, 必填): 合并行数，至少为 1，与 colSpan 不可同时为 1
- `colSpan` (integer, 必填): 合并列数，至少为 1，与 rowSpan 不可同时为 1
- `startRow` (integer, 可选): 起始行号，默认 0
- `startCol` (integer, 可选): 起始列号，默认 0

**`split_table_cell`** — 拆分单元格（blockId 对应的块必须是 table，目标单元格必须是已合并的）
- `startRow` (integer, 可选): 目标单元格行号，默认 0
- `startCol` (integer, 可选): 目标单元格列号，默认 0


#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "...": "..."
  }
}

```


#### 操作约束

- **前置检查**：先 otl.block_query 了解目标块结构，确认更新内容
- **提示**：update_attrs 是覆盖操作，不需更新的属性需保持原样传入
> 当 blockId 为 "doc" 且 operation 为 "update_content" 时，第一个子节点必须是 title
> update_attrs 不支持 doc、appComponent、lockBlock 三种块
> 表格操作中行/列数量需与表格结构对齐
---


## 工具速查表

| # | 工具名 | 功能 | 必填参数 |
|---|--------|------|----------|
| 1 | `otl.insert_content` | 向智能文档插入 Markdown/文本内容 | `file_id`, `content` |
| 2 | `otl.block_insert` | 向智能文档插入一个或多个块 | `file_id`, `params` |
| 3 | `otl.block_delete` | 删除智能文档中一个或多个块区间 | `file_id`, `params` |
| 4 | `otl.block_query` | 查询智能文档指定块的结构与内容 | `file_id`, `params` |
| 5 | `otl.convert` | 将 HTML/Markdown 转换为智能文档块结构 | `file_id`, `params` |
| 6 | `otl.block_update` | 更新智能文档指定块的内容或属性 | `file_id`, `params` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 新建文档并写入内容 | `create_file` → `otl.insert_content` |
| 读取现有文档内容 | `otl.block_query`（`blockIds: ["doc"]` 获取全文） |
| 导出文档为 Markdown | `read_file_content`（可能遗漏部分组件内容） |
| 精确修改文档块 | `otl.block_query` → `otl.block_delete` / `otl.block_insert` |
| 外部内容转块后插入 | `otl.convert` → `otl.block_insert` |
