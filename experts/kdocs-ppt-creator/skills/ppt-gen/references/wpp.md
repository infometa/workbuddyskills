# 演示文稿（pptx / wpp）工具完整参考文档

本文件包含金山文档 Skill 中**演示文稿**相关工具的完整 API 说明、详细调用示例、参数说明和返回值说明。

**适用范围**：本文档中的 `wpp.*` 工具面向**在线演示（WPP）**内核能力，包括空白页插入、主题字体/配色设置、导出图片或 PDF 等。

---

## 通用说明

### 演示文稿工具概述

**在线演示（WPP）** 提供幻灯片操作（添加/删除/复制）、形状插入、主题字体/配色设置、导出图片或 PDF 等能力，通过本文 **`wpp.*`** 工具描述；

- 若只是读取幻灯片正文/结构，优先使用 `read_file`（返回 `content_format=kdc` 的结构化数据）

### 使用场景

| 场景 | 说明 |
|------|------|
| 工作汇报 | 季度/年度演示材料 |
| 培训课件 | 结构化幻灯片内容 |
| 对外宣讲 | 导出 PDF / 图片 |

### 文档定位

除创建空白演示 / 纯任务查询外，`wpp.*` 统一传 `url` / `link_id` / `file_id` **三选一**。

### 结构化工具

| 能力域 | 工具 |
|--------|------|
| 幻灯片 | `wpp.read_slide` / `wpp.write_slide` |
| 形状 | `wpp.read_shape` / `wpp.write_shape` |
| 演示文稿属性 | `wpp.read_presentation` / `wpp.write_presentation` |
| 母版 | `wpp.read_master` / `wpp.write_master` |

`wpp.write_shape` 的 `insert_picture` action 用于在幻灯片上插入图片形状，需传 `image_url`（公网可访问的图片 URL）及 `slide_id`、位置尺寸等参数；也可通过 `body` 传入完整请求体。

---

## 一、演示文稿与页面

> 页面级插入与整篇结构操作

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.insert_slide`](wpp/slide.md) | 在已有演示中插入空白页 | `url`\|`link_id`\|`file_id`, `slide_idx` |
| [`wpp.import_slides`](wpp/slide.md) | 将外部 PPTX 的指定页面导入到已有演示文稿 | `url`\|`link_id`\|`file_id`, `object_url`, `slide_idx`, `source_idxs` |

## 二、主题（字体与配色）

> 演示文稿或单页的字体与配色方案设置

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.set_font_presentation`](wpp/theme.md) | 全文更换字体 | `url`\|`link_id`\|`file_id` |
| [`wpp.set_font_slide`](wpp/theme.md) | 单页更换字体 | `url`\|`link_id`\|`file_id`, `slide_idx` |
| [`wpp.set_color_presentation`](wpp/theme.md) | 全文更换配色 | `url`\|`link_id`\|`file_id` |
| [`wpp.set_color_slide`](wpp/theme.md) | 单页更换配色 | `url`\|`link_id`\|`file_id`, `slide_idx`, `theme_color_mode`, `color_scheme_id` |

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

> 导出 PDF / 图片

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.export_image`](wpp/export.md) | 导出为图片 | `url`\|`link_id`\|`file_id`, `format` |
| [`wpp.export_pdf`](wpp/export.md) | 异步导出 PDF | `url`\|`link_id`\|`file_id`, `format` |

## 四、幻灯片

> 幻灯片、备注与标签的查询与编辑

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.read_slide`](wpp/doc_slide.md) | 查询演示文稿幻灯片相关信息 | `url`\|`link_id`\|`file_id`, `action` |
| [`wpp.write_slide`](wpp/doc_slide.md) | 插入、移动、复制或删除演示文稿幻灯片，以及管理幻灯片标签 | `url`\|`link_id`\|`file_id`, `action` |

## 五、形状

> 幻灯片上形状的查询与编辑

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.read_shape`](wpp/doc_shape.md) | 查询幻灯片上的形状对象（图形、文本框、线条等） | `url`\|`link_id`\|`file_id`, `action`, `slide_id` |
| [`wpp.write_shape`](wpp/doc_shape.md) | 在幻灯片上插入、修改或删除形状对象 | `url`\|`link_id`\|`file_id`, `action`, `slide_id` |

## 六、演示文稿属性

> 演示文稿级属性的查询与编辑

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.read_presentation`](wpp/doc_presentation.md) | 查询演示文稿整体属性与标签 | `url`\|`link_id`\|`file_id`, `action` |
| [`wpp.write_presentation`](wpp/doc_presentation.md) | 更新演示文稿整体属性与标签 | `url`\|`link_id`\|`file_id`, `action` |

## 七、母版

> 母版的查询与编辑

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wpp.read_master`](wpp/doc_master.md) | 查询演示文稿母版属性 | `url`\|`link_id`\|`file_id`, `action` |
| [`wpp.write_master`](wpp/doc_master.md) | 更新或删除演示文稿母版属性 | `url`\|`link_id`\|`file_id`, `action` |

## 常用工作流

#### 演示文稿导出 PDF

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

若网关将下列工具统一包装为外层 `code` / `msg` / `data`，**业务载荷**仍以本文「返回值说明」中的 JSON 为准，嵌套在 `data` 内；详见 `drive.md` 中与各 `wpp.*` 工具的对接说明。
