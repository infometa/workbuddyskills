# 表格文档/智能表格（xlsx & ksheet）工具完整参考文档

本文件包含金山文档 Skill 中表格相关工具的完整 API 说明、详细调用示例、参数说明和返回值说明。

**适用范围**：本文档中的所有 `sheet.*` 工具同时适用于 Excel（.xlsx）和智能表格（.ksheet）。

---

### 表格工具概述

表格工具专门用于操作金山文档中的在线表格，提供工作表信息的查询、范围数据的获取以及批量更新等功能。支持两种表格类型：

- **Excel（.xlsx）**：传统在线表格
- **智能表格（.ksheet）**：高级结构化表格

### 创建表格文件

#### 创建 Excel 文件

通过 `create_file` 创建，`name` 须带 `.xlsx` 后缀，`file_type` 设为 `file`：

```json
{
  "name": "销售数据表.xlsx",
  "file_type": "file",
  "parent_id": "folder_abc123"
}
```

#### 创建智能表格

通过 `create_file` 创建，`name` 须带 `.ksheet` 后缀，`file_type` 设为 `file`：

```json
{
  "name": "项目任务跟踪表.ksheet",
  "file_type": "file",
  "parent_id": "folder_abc123"
}
```

### Excel vs 智能表格（ksheet）对比

| 特性 | Excel | 智能表格 ksheet |
|------|-------|----------------|
| 数据组织 | 传统行列表格 | 结构化字段+记录 |
| 视图 | 单一表格视图 | 多视图（表格/看板/日历/甘特图等） |
| 字段类型 | 通用单元格 | 丰富字段类型（单选/多选/日期/附件/关联等） |
| 适用场景 | 数据计算、报表、财务报表 | 项目管理、CRM、任务跟踪、库存管理 |
| 工作表/数据接口 | 使用 `sheet.*` 工具 | **同样使用 `sheet.*` 工具** |

### 使用场景

#### Excel 适用场景

| 场景 | 说明 |
|------|------|
| 数据记录 | 销售数据、财务报表 |
| 数据分析 | 结构化数据的读取与处理 |
| 报表汇总 | 多维度数据汇总 |
| 公式计算 | 需要复杂公式和数据透视 |

#### 智能表格 适用场景

| 场景 | 说明 |
|------|------|
| 项目管理 | 任务分配、进度跟踪 |
| CRM 管理 | 客户信息、跟进记录 |
| 资产管理 | 库存台账、设备管理 |
| 审批台账 | 合同风险排查台账等 |

### 类型选择建议

- 需要公式计算、数据透视 → 选 **Excel**
- 需要多视图、字段管理、看板展示 → 选 **ksheet**
- 需要做任务管理/项目跟踪 → 选 **ksheet**
- 需要做财务报表 → 选 **Excel**

> **注意**：无论是 Excel 还是 ksheet，工作表管理和数据操作都使用相同的 `sheet.*` 接口。只需将对应的文件 ID 传入即可。

---

## 一、工作表管理

### 1. sheet.get_sheets_info

#### 功能说明

获取指定表格文件的所有工作表信息，包含每个工作表的名称、索引、数据区域范围等。


#### 调用示例

获取工作表信息：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID

#### 返回值说明

```json
{
  "sheetsInfo": [
    {
      "isEmpty": false,
      "colFrom": 0,
      "colTo": 5,
      "isVisible": true,
      "maxCol": 16383,
      "maxRow": 1048575,
      "rowFrom": 0,
      "rowTo": 50,
      "sheetId": 3,
      "sheetIdx": 0,
      "sheetName": "Sheet1",
      "sheetType": "et"
    }
  ]
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheetsInfo[].sheetId` | integer | 工作表 ID |
| `sheetsInfo[].sheetIdx` | integer | 工作表索引 |
| `sheetsInfo[].sheetName` | string | 工作表名称 |
| `sheetsInfo[].sheetType` | string | 工作表类型（见下表） |
| `sheetsInfo[].isEmpty` | boolean | 是否为空 |
| `sheetsInfo[].isVisible` | boolean | 是否可见 |
| `sheetsInfo[].maxRow` | integer | 最大行数（工作表总容量） |
| `sheetsInfo[].maxCol` | integer | 最大列数 |
| `sheetsInfo[].rowFrom` | integer | 数据区域起始行 |
| `sheetsInfo[].rowTo` | integer | 数据区域结束行（比 `maxRow` 更有参考价值） |
| `sheetsInfo[].colFrom` | integer | 数据区域起始列 |
| `sheetsInfo[].colTo` | integer | 数据区域结束列 |

**sheetType 工作表类型：**

| sheetType | 说明 |
|-----------|------|
| `et` | 普通电子表格 |
| `db` | 数据表 |
| `airApp` | 应用表 |
| `oldDb` | 旧的数据表 |
| `dbDashBoard` | 数据表的仪表盘 |
| `etDashBoard` | 普通表格的仪表盘 |
| `workbench` | 工作台 |

> rowTo/colTo 比 maxRow/maxCol 更有参考价值，表示实际数据区域
---

### 2. sheet.add_sheet

#### 功能说明

在指定表格文件中新增工作表。可指定名称、数量、插入位置和默认列宽。


#### 调用示例

在末尾新增工作表：

```json
{
  "file_id": "string",
  "name": "销售数据",
  "end": true
}
```

在指定工作表前插入：

```json
{
  "file_id": "string",
  "name": "新工作表",
  "before": {
    "sheetId": 3
  },
  "count": 1,
  "defColWidth": 1335
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `name` (string, 可选): 工作表名称
- `count` (integer, 可选): 新增数量；默认值：`1`
- `before` (object, 可选): 在指定工作表之前插入，格式 `{"sheetId": <id>}`。与 `after`、`end` 三选一
- `after` (object, 可选): 在指定工作表之后插入，格式 `{"sheetId": <id>}`。与 `before`、`end` 三选一
- `end` (boolean, 可选): 在末尾插入。与 `before`、`after` 三选一
- `defColWidth` (integer, 可选): 默认列宽（单位：缇，1 pixel ≈ 15 twip）

#### 返回值说明

```json
{
  "sheetId": 4
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `sheetId` | integer | 新建的工作表 ID |

---

## 二、数据操作

### 3. sheet.get_range_data

#### 功能说明

获取指定工作表中某个矩形区域内的单元格数据。行列索引均为 0-based。


#### 调用示例

读取 A1:F11 区域：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "range": {
    "rowFrom": 0,
    "rowTo": 10,
    "colFrom": 0,
    "colTo": 5
  }
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `sheetId` (integer, 必填): 工作表 ID
- `range` (object, 必填): 查询范围
  - `rowFrom` (integer, 必填): 起始行（0-based）
  - `rowTo` (integer, 必填): 结束行
  - `colFrom` (integer, 必填): 起始列（0-based）
  - `colTo` (integer, 必填): 结束列

#### 返回值说明

```json
{
  "rangeData": [
    {
      "cellText": "广州",
      "originalCellValue": "广州",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "numFormat": "G/通用格式",
      "isCellPic": false,
      "fmlaText": ""
    }
  ]
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `rangeData[].cellText` | string | 单元格显示文本 |
| `rangeData[].originalCellValue` | string | 原始值 |
| `rangeData[].rowFrom` | integer | 起始行 |
| `rangeData[].rowTo` | integer | 结束行 |
| `rangeData[].colFrom` | integer | 起始列 |
| `rangeData[].colTo` | integer | 结束列 |
| `rangeData[].numFormat` | string | 数字格式 |
| `rangeData[].isCellPic` | boolean | 是否为图片 |
| `rangeData[].fmlaText` | string | 公式文本 |

---

### 4. sheet.update_range_data

#### 功能说明

批量更新单元格选区数据，支持写值/公式、设置格式、合并单元格、写入图片。每项操作必须包含 `rowFrom`、`rowTo`、`colFrom`、`colTo`。


#### 调用示例

写入值：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "formula",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "formula": "Hello"
    }
  ]
}
```

设置格式：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "format",
      "rowFrom": 0,
      "rowTo": 0,
      "colFrom": 0,
      "colTo": 0,
      "xf": {
        "font": {
          "name": "微软雅黑",
          "dyHeight": 220,
          "bls": true,
          "color": {
            "type": 2,
            "value": 16777215
          }
        },
        "alcH": 2,
        "alcV": 1,
        "wrap": true
      }
    }
  ]
}
```

合并单元格：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "merge",
      "rowFrom": 2,
      "rowTo": 3,
      "colFrom": 0,
      "colTo": 3,
      "type": "MergeCenter"
    }
  ]
}
```

写入图片：

```json
{
  "file_id": "string",
  "sheetId": 3,
  "rangeData": [
    {
      "opType": "picture",
      "rowFrom": 0,
      "colFrom": 1,
      "cellPicInfo": {
        "tag": "url",
        "url": "https://example.com/image.png"
      }
    }
  ]
}
```


#### 参数说明

- `file_id` (string, 必填): Excel 或 ksheet 文件 ID
- `sheetId` (integer, 必填): 工作表 ID
- `rangeData` (array[object], 必填): 操作列表，每项必须包含 `opType` 和坐标字段，详见下方 rangeData 字段表

**rangeData 每项字段：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `opType` | string | 是 | 操作类型（见下表） |
| `rowFrom` | integer | 是 | 起始行（0-based） |
| `rowTo` | integer | 是 | 结束行 |
| `colFrom` | integer | 是 | 起始列（0-based） |
| `colTo` | integer | 是 | 结束列 |
| `formula` | string | 否 | 值或公式（`formula` 类型时使用） |
| `xf` | object | 否 | 格式对象（`format` 类型时使用） |
| `type` | string | 否 | 合并类型（`merge` 类型时使用） |
| `cellPicInfo` | object | 否 | 图片信息（`picture` 类型时使用） |

**opType 操作类型：**

| opType | 说明 | 需要的字段 |
|--------|------|-----------|
| `formula` | 写值/公式 | `formula` |
| `format` | 设置格式 | `xf` |
| `merge` | 合并单元格 | `type` |
| `picture` | 写入图片 | `cellPicInfo` |

**merge type 合并类型：**`MergeCenter`（居中合并）/ `MergeAcross`（跨越合并）/ `MergeCells`（合并单元格）

**cellPicInfo 图片信息：**

```json
{
  "tag": "url",
  "url": "https://example.com/image.png"
}
```

**xf 格式对象：**

```json
{
  "font": {
    "name": "微软雅黑",
    "dyHeight": 220,
    "charSet": 134,
    "bls": false,
    "italic": false,
    "strikeout": false,
    "uls": 0,
    "sss": 0,
    "themeFont": 2,
    "color": {"type": 2, "value": 16777215}
  },
  "wrap": false,
  "shrinkToFit": false,
  "locked": true,
  "hidden": false,
  "alcH": 0,
  "alcV": 1,
  "indent": 0,
  "readingOrder": 0,
  "trot": 0,
  "dgLeft": 0,
  "dgRight": 0,
  "dgTop": 0,
  "dgBottom": 0,
  "numfmt": "G/通用格式",
  "fill": {
    "type": 1,
    "back": {"type": 2, "value": 4294967040},
    "fore": {"type": 255}
  }
}
```

- `alcH`：水平对齐（1=左, 2=居中, 3=右, 4=填充, 5=两端, 6=跨列, 7=分散）
- `alcV`：垂直对齐（0=上, 1=中, 2=下, 3=两端, 4=分散）
- `dgLeft/dgRight/dgTop/dgBottom`：边框线型（0=无, 1=细线, 2=中等, 3=虚线, 4=点线, 5=粗线, 6=双线, 7=细虚线）

**颜色 color 参数：**

| type | 说明 |
|------|------|
| `0` | ICV 颜色模式 |
| `1` | THEME 颜色主题 |
| `2` | ARGB 颜色模式 |
| `254` | 无颜色（用于背景） |
| `255` | 自动颜色（用于前景，如字体和边框） |


#### 返回值说明

```json
{}

```


#### 操作约束

- **前置检查**：get_range_data 读取目标区域现有数据，确认覆盖范围
- **提示**：每项必须包含 rowFrom/rowTo/colFrom/colTo 四个坐标
---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `sheet.get_sheets_info` | 工作表管理 | 获取工作表列表 | `file_id` |
| 2 | `sheet.add_sheet` | 工作表管理 | 新增工作表 | `file_id` |
| 3 | `sheet.get_range_data` | 数据操作 | 获取选区数据 | `file_id`, `sheetId`, `range` |
| 4 | `sheet.update_range_data` | 数据操作 | 批量更新选区数据 | `file_id`, `sheetId`, `rangeData` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 读表格（矩形区域） | `sheet.get_sheets_info` → `sheet.get_range_data` |
| 写表格（批量改单元格） | `sheet.get_range_data`（可选对照）→ `sheet.update_range_data` → `sheet.get_range_data` 验证 |

---

## 错误速查表

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| 表格读不到或结构不明 | 未先取工作表列表 / 区域错误 | 先 `sheet.get_sheets_info`，再 `sheet.get_range_data` |

---

## 附录

### 错误响应

| 情况 | 响应示例 |
|------|---------|
| 命令不支持 | `{"msg":"core not support","result":"unSupport"}` |
| 内核错误 | `{"errno":-1880935404,"msg":"Invalid request","result":"ExecuteFailed"}` |
| HTTP 状态非 200 | 请求本身失败，检查鉴权信息（Cookie/Origin） |
