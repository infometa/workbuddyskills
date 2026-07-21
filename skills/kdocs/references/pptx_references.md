# 演示文稿（pptx / wpp）工具完整参考文档

本文件包含金山文档 Skill 中**演示文稿**相关工具的完整 API 说明、详细调用示例、参数说明和返回值说明。

**适用范围**：本文档中的 `wpp.*` 工具面向**在线演示（WPP）**内核能力，包括空白页插入、主题字体/配色设置、导出图片或 PDF 等。

---

## 通用说明

### 演示文稿工具概述

**在线演示（WPP）** 提供空白页插入、主题字体/配色设置、导出图片或 PDF 等能力，通过本文 **`wpp.*`** 工具描述；

### 使用场景

| 场景 | 说明 |
|------|------|
| 工作汇报 | 季度/年度演示材料 |
| 培训课件 | 结构化幻灯片内容 |
| 对外宣讲 | 导出 PDF / 图片 |

---

## 一、演示文稿与页面

### 1. wpp.insert_slide

#### 功能说明

在**已有**在线演示文稿中插入一页空白幻灯片。

**适用于**：已存在、可编辑的 WPP 演示（`file_id` 对应在线演示文档）。


#### 调用示例

在第 1 页后插入空白页：

```json
{
  "file_id": "string",
  "slide_idx": 1,
  "layer_type": 65538,
  "layout_Id": 134217788
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `slide_idx` (integer, 必填): 插入位置的幻灯片序号，**从 0 开始**
- `layer_type` (integer, 可选): 版式类型，固定值 `65538`
- `layout_Id` (integer, 可选): 指定模板版式 ID，从对应版式新建幻灯片（如结束页、标题页、内容页等）。版式 ID 与演示文稿模板中定义的版式一一对应，不同模板的可用 ID 不同

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "res": [
      {
        "cmdName": "slideInsert",
        "code": 0,
        "errName": "S_OK",
        "msg": "execute result",
        "token": "string"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 请求成功为 `ok` |
| `detail.res[].cmdName` | string | 内核命令名，如 `slideInsert` |
| `detail.res[].code` | integer | `0` 表示该条执行成功 |
| `detail.res[].errName` | string | 如 `S_OK` |
| `detail.res[].token` | string | 可选，会话/追踪用 |

---

## 二、主题（字体与配色）

### 2. wpp.set_font_presentation

#### 功能说明

将**整份**演示文稿应用指定主题字体方案。

**适用于**：WPP 演示全文换字体。


#### 调用示例

全文换为简约中等线体：

```json
{
  "file_id": "string",
  "font_theme": "简约中等线体"
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `font_theme` (string, 可选): 预设字体主题名；不传或不在列表内 → **经典黑体**

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "res": [
      {
        "cmdName": "modifyPresentation",
        "code": 0,
        "errName": "S_OK",
        "msg": "execute result"
      }
    ]
  }
}

```

---

### 3. wpp.set_font_slide

#### 功能说明

将**指定页**应用主题字体方案。

**适用于**：单页换字体。


#### 调用示例

第 2 页换为简约中等线体：

```json
{
  "file_id": "string",
  "slide_idx": 1,
  "font_theme": "简约中等线体"
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `slide_idx` (integer, 必填): 目标幻灯片序号，从 0 开始
- `font_theme` (string, 可选): 预设字体主题名；不传或不在列表内 → **经典黑体**

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "res": [
      {
        "cmdName": "modifySlideProps",
        "code": 0,
        "errName": "S_OK",
        "msg": "execute result"
      }
    ]
  }
}

```

---

### 4. wpp.set_color_presentation

#### 功能说明

将**整份**演示文稿应用指定主题配色方案。

**适用于**：WPP 全文换配色。


#### 调用示例

全文换为琥珀黄配色：

```json
{
  "file_id": "string",
  "color_theme": "琥珀黄"
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `color_theme` (string, 可选): 预设配色主题名；不传或未命中 → **默认配色**

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "res": [
      {
        "cmdName": "modifyPresentation",
        "code": 0,
        "errName": "S_OK",
        "msg": "execute result"
      }
    ]
  }
}

```

---

### 5. wpp.set_color_slide

#### 功能说明

将**指定页**应用主题配色方案。


#### 调用示例

单页换为嫩芽绿配色：

```json
{
  "file_id": "string",
  "slide_idx": 1,
  "color_theme": "嫩芽绿",
  "theme_color_mode": 1,
  "color_scheme_id": "19d485c844c"
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `slide_idx` (integer, 必填): 目标幻灯片序号，从 0 开始
- `color_theme` (string, 可选): 预设配色主题名；不传或未命中 → **默认配色**
- `theme_color_mode` (integer, 必填): 主题颜色模式，值必须与 `color_theme` 对应。`0` 恢复默认配色；`1` 浅色系配色（落日红、蜜橘橙、琥珀黄、嫩芽绿、湖水青、晴空蓝、丁香紫）；`3` 深色系配色（朱砂赤、南瓜橙、深麦黄、深松绿、深墨青、深海蓝、葡萄紫、胭脂红）。具体映射见附录「配色主题详表」
- `color_scheme_id` (string, 必填): 配色方案标识，格式参考 `19d485c844c`，为随机生成的唯一 ID，不与特定 `color_theme` 一一对应

#### 返回值说明

```json
{
  "result": "ok",
  "detail": {
    "res": [
      {
        "cmdName": "modifySlideProps",
        "code": 0,
        "errName": "S_OK",
        "msg": "execute result"
      }
    ]
  }
}

```

---


### 字体与配色约束

| 项 | 规则 |
|----|------|
| 字体主题 | 支持 **16** 种方案名：`现代雅黑体`、`简约等线体`、`经典宋体`、`清秀姚体`、`经典黑体`、`现代黑体`、`简约灵秀黑体`、`科技云技术体`、`经典楷体`、`典雅气质体`、`简约中等线体`、`古朴小隶体`、`传统书宋二体`、`圆润体`、`可爱傲娇体`、`飘逸青云体`。`font_theme` 未传或非法 → **经典黑体** |
| 配色主题 | 支持 **16** 种方案名，每种配色对应 `theme_color_mode` 值如下表 |

#### 配色主题详表

| `color_theme` | `theme_color_mode` | 说明 |
|---------------|-------------------|------|
| 默认配色 | 0 | 恢复默认配色 |
| 落日红 | 1 | 浅色暖色系 |
| 蜜橘橙 | 1 | 浅色暖色系 |
| 琥珀黄 | 1 | 浅色暖色系 |
| 嫩芽绿 | 1 | 浅色冷色系 |
| 湖水青 | 1 | 浅色冷色系 |
| 晴空蓝 | 1 | 浅色冷色系 |
| 丁香紫 | 1 | 浅色冷色系 |
| 朱砂赤 | 3 | 深色暖色系 |
| 南瓜橙 | 3 | 深色暖色系 |
| 深麦黄 | 3 | 深色暖色系 |
| 深松绿 | 3 | 深色冷色系 |
| 深墨青 | 3 | 深色冷色系 |
| 深海蓝 | 3 | 深色冷色系 |
| 葡萄紫 | 3 | 深色冷色系 |
| 胭脂红 | 3 | 深色暖色系 |

`color_theme` 未传或非法 → **默认配色**（`theme_color_mode: 0`）

## 三、下载与导出

### 6. wpp.export_image

#### 功能说明

将幻灯片导出为 **PNG** 或 **JPEG** 图片（同步接口，直接返回下载地址或 key）。

**适用于**：缩略图、逐页图片导出。


#### 调用示例

逐页、96 dpi、PNG、含水印：

```json
{
  "link_id": "string",
  "format": "png",
  "dpi": 96,
  "water_mark": true,
  "from_page": 1,
  "to_page": 100,
  "combine_long_pic": false,
  "use_xva": true,
  "client_id": "",
  "password": "",
  "store_type": ""
}
```


#### 参数说明

- `link_id` (string, 必填): 演示文稿的分享链接 ID（从分享链接 URL 中提取）
- `format` (string, 必填): `png` 或 `jpeg`
- `dpi` (integer, 可选): 如 `96`、`150`、`300`
- `water_mark` (boolean, 可选): 是否含水印
- `from_page` (integer, 可选): 起始页，从 0 开始
- `to_page` (integer, 可选): 结束页
- `combine_long_pic` (boolean, 可选): 是否合并为长图；`false` 表示逐页
- `use_xva` (boolean, 可选): 是否使用 XVA 渲染引擎
- `client_id` (string, 可选): 客户端标识
- `password` (string, 可选): 文档打开密码（若加密）
- `store_type` (string, 可选): 如 `ks3`、`cloud`

#### 返回值说明

```json
{
  "result": "ok",
  "url": "string",
  "key": "string",
  "file_id": "string",
  "without_attachment": false,
  "size": 0
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | 成功为 `ok` |
| `url` | string | 图片下载地址（有时效） |
| `key` | string | 导出文件标识 |
| `file_id` | string | 关联文件 ID |
| `size` | integer | 仅当请求要求返回大小时可能存在 |

失败时可能返回 `result` 为 `error` 且带 `data.code` / `data.message`，以实际响应为准。

---

### 7. wpp.export_pdf

#### 功能说明

异步导出 PDF **步骤一**：**创建导出任务**（`POST .../async-export`），返回 `task_id`。本工具传入 `task_id` 时会调用查询接口进行轮询。

**适用于**：需要可打印、可分享的 PDF 文件。

**步骤二**：传入 `task_id` 查询导出进度，`status` 为 `running` 时需等待后重试，`finished` 时返回下载链接。


#### 调用示例

步骤一：创建导出任务：

```json
{
  "file_id": "string",
  "format": "pdf",
  "multipage": 1,
  "opt_frame": true,
  "from_page": 1,
  "to_page": 9999,
  "client_id": "",
  "store_type": "ks3",
  "password": "",
  "export_open_password": "",
  "export_modify_password": ""
}
```

步骤二：查询导出进度：

```json
{
  "task_id": "string",
  "task_type": "normal_export"
}
```


#### 参数说明

- `file_id` (string, 必填): 演示文稿 file_id
- `format` (string, 必填): 固定 `pdf`
- `task_id` (string, 可选): 步骤一返回的任务 ID（步骤二查询进度时必填）
- `task_type` (string, 可选): 任务类型，固定 `normal_export`（步骤二查询时传入）
- `multipage` (integer, 可选): 是否多页合一类导出；`1` 表示是
- `opt_frame` (boolean, 可选): 是否优化帧
- `from_page` (integer, 可选): 起始页，从 0 开始
- `to_page` (integer, 可选): 结束页
- `client_id` (string, 可选): 客户端标识
- `store_type` (string, 可选): 存储类型
- `password` (string, 可选): 源文件密码
- `export_open_password` (string, 可选): 导出 PDF 打开密码
- `export_modify_password` (string, 可选): 导出 PDF 修改密码

#### 返回值说明

```json
步骤一返回：

```json
{
  "task_id": "string",
  "task_type": "normal_export"
}
```

步骤二返回（进行中）：

```json
{
  "status": "running",
  "data": null
}
```

步骤二返回（已完成）：

```json
{
  "status": "finished",
  "data": {
    "file_id": "string",
    "key": "string",
    "result": "ok",
    "url": "string",
    "without_attachment": false
  }
}
```

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 异步任务 ID，后续查询必填 |
| `task_type` | string | 固定为 `normal_export`（导出 PDF 场景） |
| `status` | string | `running` / `finished` |
| `data.url` | string | PDF 下载地址（`finished` 时，有时效） |

---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `wpp.insert_slide` | 演示文稿与页面 | 在已有演示中插入空白页 | `file_id`, `slide_idx` |
| 2 | `wpp.set_font_presentation` | 主题（字体与配色） | 全文更换字体 | `file_id` |
| 3 | `wpp.set_font_slide` | 主题（字体与配色） | 单页更换字体 | `file_id`, `slide_idx` |
| 4 | `wpp.set_color_presentation` | 主题（字体与配色） | 全文更换配色 | `file_id` |
| 5 | `wpp.set_color_slide` | 主题（字体与配色） | 单页更换配色 | `file_id`, `slide_idx`, `theme_color_mode`, `color_scheme_id` |
| 6 | `wpp.export_image` | 下载与导出 | 导出为图片 | `link_id`, `format` |
| 7 | `wpp.export_pdf` | 下载与导出 | 异步导出 PDF | `file_id`, `format` |

## 常用工作流

### 演示文稿导出 PDF

```
步骤 1: wpp.export_pdf(file_id="xxx", format="pdf")
        → 返回 task_id, task_type

步骤 2: wpp.export_pdf(task_id="xxx", task_type="normal_export")
        → 轮询（每 2-5 秒），status 判定：
          "finished" → data.url 即 PDF 下载地址（有时效）
          "running"  → 继续轮询
```

## 附录

### 错误响应

| 情况 | 说明或示例 |
|------|------------|
| 未登录 / 无权限 | 返回业务错误码或 `result` 非 `ok`，`msg` 含可读原因 |
| 内核执行失败 | 类似 `detail.res[].code` 非 `0`，或 `result` 为 `ExecuteFailed` 等（以实际为准） |
| HTTP 非 200 | 请求失败，检查鉴权（Cookie、Origin 等） |

### 与通用 MCP 包装

若网关将下列工具统一包装为外层 `code` / `msg` / `data`，**业务载荷**仍以本文「返回值说明」中的 JSON 为准，嵌套在 `data` 内；详见 `api_references.md` 中与各 `wpp.*` 工具的对接说明。
