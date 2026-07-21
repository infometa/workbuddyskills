# SLIDE 编辑引擎 API 参考

本文件包含腾讯文档 SLIDE 编辑引擎（slideengine）的所有工具 API 说明。这些工具专用于演示文稿（PPT）的精细化编辑操作，包括幻灯片管理、形状插入、文本编辑、表格操作、图表管理、批注、节管理、分组、动画、主题设置、演讲者备注等。

---

## 🚨 强制路由规则（必读）

> **凡是涉及 PPT / 幻灯片 / slide / 演示文稿的"编辑 / 修改 / 添加 / 删除 / 查询"操作，必须使用 `slide-mcp` 服务的 `slide_*` 工具，不要使用 `tencent-docs` 的通用工具或 `doc_*` 工具。**

### 命中本文档的判定条件

只要满足以下任一条件，**必须立即跳转使用本文档的 `slide_*` 工具**，并通过 `slide-mcp` 服务调用：

1. 用户提供的文档链接形如 `https://docs.qq.com/slide/<id>`
2. 用户提及"PPT" / "幻灯片" / "演示文稿" / "slide" / "投影片" 等关键词
3. 用户的目标文档 `file_type` 为 `slide` / `tencentslide`
4. 任务涉及"幻灯片页 / shape / 形状 / 文本框 / 表格 / 图表 / 批注 / 动画 / 主题 / 演讲者备注 / 母版 / 节"等 PPT 专属概念的"编辑 / 修改 / 增删查改"

### 严禁的反模式

- ❌ **禁止**用 `doc_*`（docengine）系列工具去改 PPT —— 它们只支持 Word 类文档（smartcanvas / doc / tencentdoc），对 slide 文件返回的内容 / 行为均不正确。
- ❌ **禁止**用 `tencent-docs` 主服务里的"通用编辑"思路绕过 `slide-mcp` —— 通用工具不暴露 slide 内部结构（shape_id / page_index / 母版等）。
- ❌ **禁止**先用 `manage.async_import` 把 PPT 导出为其他格式再编辑，除非用户**明确**要做格式转换。

### 正确路径

1. 通过 `mcporter list slide-mcp` 确认目标工具存在
2. 调用：`mcporter call "slide-mcp" "slide_<工具名>" --args '<JSON>'`
3. 入参用 `file_url`（直接传 https 链接）或 `file_id`（二选一）

> 💡 如果用户要的是"AI 生成整份 PPT"（不是精细编辑已有 PPT），改去看 `references/slide_references.md`（PPT AI 生成）。本文档专门服务"对已有 PPT 做精细编辑"。

---

> ⚠️ **注意**：本文档中的工具仅适用于 **演示文稿（幻灯片/PPT）** 类型，不适用于 Word 文档或智能文档等其他类型。

---

## 服务信息

| 项目     | 说明                                                                                    |
| -------- | --------------------------------------------------------------------------------------- |
| 所属服务 | `slide-mcp`                                                                             |
| 服务地址 | `https://docs.qq.com/api/v6/slide/mcp`                                                  |
| 工具前缀 | `slide_*`（如 `slide_add_shape`、`slide_find_text`、`slide_set_notes_text` 等）          |
| 调用方式 | 通过 MCP 协议调用，使用 slide-mcp 服务的 Authorization Token                              |
| 文档类型 | 仅支持演示文稿（幻灯片/PPT）类型                                                         |
| 工具总数 | **73**                                                                                  |

> ⚠️ **所有 `slide_*` 工具均使用 `file_id` 或 `file_url` 标识文档**（二选一）。若用户提供的是文档链接（形如 `https://docs.qq.com/slide/<id>`），可直接传入 `file_url`，服务端自动解析。

---

## 通用说明

### 文档标识

所有 slideengine 工具都支持通过 `file_id` 或 `file_url` 标识文档（二选一）：

- `file_id` (string): 文档唯一标识符，形如 `300000000$WKxxx`
- `file_url` (string): 腾讯文档的分享链接（形如 `https://docs.qq.com/slide/...`），服务端自动解析为 file_id

### 版本参数

所有 slideengine 工具都支持可选的 `version_info` 参数，用于指定基于哪个版本进行操作（不传时默认基于最新版本）：

- `version_info` (object, 可选):
  - `base_version` (int64, 可选): 基准版本号，通常使用上一步读类接口返回的 `version` 值。值为 0 表示不指定。
  - `is_latest` (bool, 可选): 是否基于最新版本操作。设为 `true` 时忽略 `base_version`。

> 💡 连续多步编辑时，建议将上一步接口返回的 `version` / `new_version` 传入下一步的 `version_info.base_version`，以避免并发冲突。

### 页面索引

- `page_index` (integer): 幻灯片页索引，**从 0 开始计数**。第 1 页对应 `page_index = 0`。

### 形状标识

- `shape_id` (string): 形状的唯一 ID，通过 `slide_get_shape_info` / `slide_get_page_info` 等读类接口获取。

### 坐标与尺寸单位

- **坐标（x, y）和尺寸（w, h）**：单位为 **磅（pt）**。标准 PPT 页面尺寸为 **960×540 pt**（16:9）或 **720×540 pt**（4:3）。
- **边框宽度（border_width）**：单位为 **pt**（磅）
- **旋转角度（rotation）**：单位为 **度**
- **EMU 换算**：`1 pt = 12700 EMU`（部分底层接口的偏移 / 渐变等字段使用 EMU，如 `slide_set_page_properties` 的 `tile_tx`/`tile_ty`）
- **透明度（fill_alpha, border_alpha）**：取值 0~100000（与 OOXML 对齐，100000 表示完全不透明）；部分简化接口取值 0~100

### 颜色

颜色值统一使用 6 位十六进制 RRGGBB 格式（**不含** `#` 前缀），如 `FF0000` 表示纯红。

### 响应结构

编辑类（写类）API：

- 大部分写类工具返回空 Rsp 消息（实际编辑结果通过 MCP TextContent 中的 JSON 透出）
- 部分工具（如表格类）返回结构化响应，包含 `new_version` / `base_version` 等

读类 API 返回结构化数据，包含：

- `version` (int64): 文档当前版本号
- 业务数据字段

---

## 工具列表

### 页面工具组（Page）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_add_slide | 写 | 在演示文稿中插入一张新幻灯片 |
| slide_add_slides | 写 | 在同一位置批量插入多张幻灯片，所有页共用同一布局模板 |
| slide_remove_slide | 写 | 删除指定位置的幻灯片 |
| slide_duplicate_slide | 写 | 深拷贝一张或多张幻灯片，副本插入在各自原始页的紧后方，保留所有形状、文本、动画和样式 |
| slide_move_slide | 写 | 移动一张或多张幻灯片到指定位置 |
| slide_get_info | 读 | 获取演示文稿元数据：幻灯片总数、有序 slide_ids、幻灯片尺寸（EMU 和磅 pt） |
| slide_get_page_info | 读 | 获取指定幻灯片上所有形状的摘要信息，包含每个形状的 id / 类型 / 位置 / 尺寸 / 文本 / 填充色 / 边框等 |
| slide_get_master_info | 读 | 获取演示文稿中母版页的详细信息，包含母版 ID、页眉页脚状态、布局列表及母版上的形状 |
| slide_set_page_properties | 写 | 设置幻灯片页面级属性，包括背景填充（纯色/图片/渐变）和可见性 |
| slide_add_page_number | 写 | 在指定幻灯片插入页码占位符，位置和样式从布局/母版继承 |
| slide_add_datetime | 写 | 在指定幻灯片插入日期时间占位符 |
| slide_add_notes | 写 | 为指定幻灯片创建演讲者备注页并写入文本内容 |
| slide_add_footer | 写 | 在指定幻灯片添加或移除页脚占位符 |

### 形状工具组（Shape）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_add_shape | 写 | 在指定幻灯片插入一个普通形状（rect / ellipse / triangle 等图形预设块） |
| slide_add_shapes | 写 | 批量在同一幻灯片插入多个形状 |
| slide_add_line_shape | 写 | 在指定幻灯片插入一根线形 / 方向性箭头线条（从 (x1,y1) 起点到 (x2,y2) 终点） |
| slide_add_line_shapes | 写 | 批量在同一幻灯片插入多根线形 / 方向性箭头线条 |
| slide_add_image | 写 | 在指定幻灯片插入一张图片。图片来源二选一： |
| slide_add_text | 写 | 在指定幻灯片插入一个文本框 |
| slide_add_texts | 写 | 批量在同一张幻灯片插入多个文本框，单次产生一个 SlideCommand（一次广播），比循环调用 slide_add_text 更高效 |
| slide_reorder_shape | 写 | 调整指定形状的 z-order 层级 |
| slide_remove_shapes | 写 | 从指定幻灯片删除一个或多个形状 |
| slide_get_shape_info | 读 | 查询指定幻灯片中某个形状的详细信息（包含 type / preset_geom / bounds / text / fill / border / 字体属性 等 16 个字段） |
| slide_set_shape_properties | 写 | 修改指定形状的视觉 / 变换属性，仅传入需要修改的字段，未传字段保持不变 |

### 文本工具组（Text）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_append_text | 写 | 向指定 shape 文本末尾追加文本 |
| slide_insert_text | 写 | 在指定 shape 文本位置插入文本 |
| slide_delete_text | 写 | 删除指定 shape 文本区间 |
| slide_find_text | 读 | 在演示文稿中查找文本 |
| slide_find_replace_text | 写 | 在指定页查找并替换文本 |
| slide_set_text_property | 写 | 设置指定文本区间富文本属性 |
| slide_get_text | 读 | 获取指定 shape 的文本内容与样式区间 |

### 表格工具组（Table）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_add_table | 写 | 在指定幻灯片页创建空表格，page_index 从 0 开始计数 |
| slide_insert_table_rows | 写 | 在表格 shape 中插入一行或多行 |
| slide_insert_table_cols | 写 | 在表格 shape 中插入一列或多列 |
| slide_delete_table_rows | 写 | 从表格 shape 中删除一行或多行，从 index 指定的行开始 |
| slide_delete_table_cols | 写 | 从表格 shape 中删除一列或多列，从 index 指定的列开始 |
| slide_merge_table_cells | 写 | 合并表格 shape 中的矩形单元格区域，区域由 start_row/start_col 和 row_span/col_span 指定 |
| slide_unmerge_table_cells | 写 | 取消表格 shape 中指定矩形区域的单元格合并，区域由 start_row/start_col 和 row_span/col_span 指定 |
| slide_set_cell_text | 写 | 向表格 shape 的单个单元格写入纯文本 |

### 图表工具组（Chart）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_add_chart | 写 | 在指定幻灯片上添加图表 |
| slide_update_chart_style | 写 | 增量更新指定图表样式 |
| slide_change_chart_type | 写 | 更改指定图表类型 |
| slide_update_chart_data | 写 | 替换指定图表的内嵌数据 |
| slide_get_chart_info | 读 | 获取指定图表结构信息 |

### 分组工具组（Group）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_get_group_info | 读 | 获取指定 group shape 的子 shape 列表 |
| slide_group_shapes | 写 | 将同一页多个 shape 组合成 group shape |
| slide_ungroup_shapes | 写 | 解散指定 group shape |
| slide_reorder_shapes_in_group | 写 | 调整分组内子 shape 层级 |
| slide_update_group_shape_properties | 写 | 更新分组视觉或变换属性 |

### 动画工具组（Animation）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_add_anim | 写 | 为指定幻灯片中的某个形状添加动画效果 |
| slide_list_anim_types | 读 | 列出所有支持的动画类型，包含类型名称、分类（entrance / exit / emphasis）以及是否支持方向参数 |
| slide_remove_anim | 写 | 移除指定形状的某个动画 |
| slide_move_anim | 写 | 移动指定形状的动画在序列中的位置（从 from_index 移到 to_index） |
| slide_set_anim_properties | 写 | 修改指定形状某个动画的类型和方向 |
| slide_set_anim_trigger | 写 | 修改指定形状某个动画的触发方式 |

### 主题工具组（Theme）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_get_themes | 读 | 获取当前演示文稿中嵌入的所有主题列表，返回每个主题的 theme_id 和 theme_name |
| slide_list_builtin_themes | 读 | 列出服务端所有内置（预置）主题，返回每个主题的 theme_id 和 theme_name |
| slide_set_theme | 写 | 设置演示文稿的主题 |

### 批注工具组（Comment）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_get_comments | 读 | 获取全部批注或指定页批注 |
| slide_add_comment | 写 | 在指定幻灯片上添加批注锚点 |
| slide_remove_comment | 写 | 删除指定批注分组 |
| slide_modify_comment | 写 | 修改指定批注分组属性 |
| slide_reply_comment | 写 | 向已有批注分组追加一条回复 |

### 节工具组（Section）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_get_sections | 读 | 获取演示文稿中的全部节 |
| slide_add_section | 写 | 在指定位置添加新节 |
| slide_remove_sections | 写 | 删除一个或多个节但保留节内幻灯片 |
| slide_remove_section_with_slides | 写 | 删除指定节及其幻灯片 |
| slide_move_section | 写 | 移动指定节到新的节序号位置 |
| slide_rename_section | 写 | 修改指定节的名称 |
| slide_move_slides_to_section | 写 | Move one or more slides into a target section. The slides are appended |

### 演示文稿级工具组（Presentation）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_set_slide_size | 写 | 设置演示文稿页面尺寸，仅支持 16:9 和 4:3 两种比例 |
| slide_set_default_font | 写 | 设置演示文稿默认字体 |

### 备注工具组（Notes）

| 工具名称 | 类型 | 功能说明 |
|---------|------|---------|
| slide_set_notes_text | 写 | 设置或覆盖指定幻灯片的备注页（演讲者备注）文本，page_index 从 0 开始计数 |

---

## 工具详细说明

## 页面工具组（Page）

### slide_add_slide

#### 功能说明

在演示文稿中插入一张新幻灯片。index 为 0-based 插入位置，必须落在 [0, 当前页数] 区间（等于当前页数即追加到末尾，不支持 -1，越界会报 page insert index out of range）；不确定当前页数时先调 slide_get_info 拿 slide_count；layout_index 为首个母版下的布局序号（0=标题，1=标题+内容 等），默认 0

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `index` | number | 否 | 0-based 插入位置，必须 ∈ [0, 当前页数]（=当前页数即追加到末尾），不支持 -1。不确定时先调 slide_get_info 拿 slide_count。 |
| `layout_index` | number | 否 | 布局序号（0=标题，1=标题+内容 等），默认 0 |

---

### slide_add_slides

#### 功能说明

在同一位置批量插入多张幻灯片，所有页共用同一布局模板。index 为 0-based 插入位置，必须落在 [0, 当前页数] 区间（=当前页数即追加到末尾，不支持 -1）；不确定当前页数时先调 slide_get_info 拿 slide_count。count 必须 >= 1

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `index` | number | 否 | 0-based 插入位置，必须 ∈ [0, 当前页数]（=当前页数即追加到末尾），不支持 -1。不确定时先调 slide_get_info 拿 slide_count。 |
| `count` | number | 否 | 要插入的页数，必须 >= 1 |
| `layout_index` | number | 否 | 布局序号（0=标题，1=标题+内容 等），默认 0 |

---

### slide_remove_slide

#### 功能说明

删除指定位置的幻灯片。page_index 为 0-based 页索引

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 待删除幻灯片的 0-based 页索引 |

---

### slide_duplicate_slide

#### 功能说明

深拷贝一张或多张幻灯片，副本插入在各自原始页的紧后方，保留所有形状、文本、动画和样式

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_indices` | array | 否 | 待复制幻灯片的 0-based 页索引列表（整数数组），长度 >= 1 |
| `target_page_num` | number | 否 | 副本插入位置（1-based 页码），不传或 0 表示默认（紧跟在被复制页后方） |

---

### slide_move_slide

#### 功能说明

移动一张或多张幻灯片到指定位置。移动后第一张被移动的幻灯片将出现在 to_index 处

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_indices` | array | 否 | 待移动幻灯片的 0-based 页索引列表（整数数组），长度 >= 1 |
| `to_index` | number | 否 | 目标位置（0-based），第一张被移动页将出现在此位置 |

---

### slide_get_info

#### 功能说明

获取演示文稿元数据：幻灯片总数、有序 slide_ids、幻灯片尺寸（EMU 和磅 pt）。在添加或编辑幻灯片前使用此工具了解结构

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |

---

### slide_get_page_info

#### 功能说明

获取指定幻灯片上所有形状的摘要信息，包含每个形状的 id / 类型 / 位置 / 尺寸 / 文本 / 填充色 / 边框等

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |

---

### slide_get_master_info

#### 功能说明

获取演示文稿中母版页的详细信息，包含母版 ID、页眉页脚状态、布局列表及母版上的形状。可选传 page_index 仅返回该页关联的母版

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 可选：指定幻灯片 0-based 页索引，仅返回该页关联的母版；省略时返回所有母版 |

---

### slide_set_page_properties

#### 功能说明

设置幻灯片页面级属性，包括背景填充（纯色/图片/渐变）和可见性。仅修改传入的属性，未传的保持不变。

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片 0-based 页索引 |
| `visible` | bool | 否 | 可见性：true=显示，false=隐藏；省略不修改 |
| `fill_type` | string | 否 | 背景填充类型：solid / image / gradient；省略不修改背景 |
| `fill_color` | string | 否 | fill_type=solid 时的背景色（RRGGBB）；空串清除背景 |
| `fill_alpha` | number | 否 | 背景透明度 0~100（0=不透明，100=全透明）； |
| `image` | string | 否 | fill_type=image 时的图片（data URI / 本地路径） |
| `stretch` | bool | 否 | fill_type=image 时是否拉伸；默认 true |
| `tile_alignment` | string | 否 | 平铺对齐锚点 |
| `tile_flip` | string | 否 | 平铺翻转模式 |
| `tile_tx` | number | 否 | 平铺水平偏移（EMU） |
| `tile_ty` | number | 否 | 平铺垂直偏移（EMU） |
| `tile_sx` | number | 否 | 平铺水平缩放（1/100000） |
| `tile_sy` | number | 否 | 平铺垂直缩放（1/100000） |
| `gradient_stops` | array | 否 | fill_type=gradient 时的色标列表（至少 2 项），每项含 color(RRGGBB) 和 pos(0~100000) |
| `gradient_angle` | number | 否 | 渐变角度（1/60000 度） |

---

### slide_add_page_number

#### 功能说明

在指定幻灯片插入页码占位符，位置和样式从布局/母版继承

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片 0-based 页索引 |

---

### slide_add_datetime

#### 功能说明

在指定幻灯片插入日期时间占位符。display_text 为可选的显示文本，如 2026/05/11；为空时引擎保留空内容

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片 0-based 页索引 |
| `display_text` | string | 否 | 可选的显示文本，如 "2026/05/11"；空串时引擎保留空内容 |

---

### slide_add_notes

#### 功能说明

为指定幻灯片创建演讲者备注页并写入文本内容。text 为空串时创建空白备注页

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片 0-based 页索引 |
| `text` | string | 否 | 备注页文本；空字符串时创建空白备注页 |

---

### slide_add_footer

#### 功能说明

在指定幻灯片添加或移除页脚占位符。show=true（默认）时插入页脚占位符并写入 display_text；show=false 时移除已有页脚占位符。位置和样式从布局/母版继承

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片 0-based 页索引 |
| `show` | bool | 否 | true（默认）=添加/显示页脚；false=移除/隐藏页脚 |
| `display_text` | string | 否 | 页脚文本内容，如 "Confidential" 或 "© 2026 Acme Corp"；仅 show=true 时生效 |

---

## 形状工具组（Shape）

### slide_add_shape

#### 功能说明

在指定幻灯片插入一个普通形状（rect / ellipse / triangle 等图形预设块）。【重要 — 箭头消歧】本工具不支持画两点之间的方向性箭头线条，仅支持 rightArrow / leftArrow 这两种固定方向的图形预设箭头块；如需画"从起点到终点的箭头线"，请改用 slide_add_line_shape 并设置 line_type=arrow / doubleArrow。当用户说"加箭头"时，请先询问要的是"线条箭头"（带起点终点）还是"图形箭头"（固定方向的图形块）再决定调哪个工具。page_index 从 0 开始；x/y/w/h 单位为磅（pt，1pt = 12700 EMU）；fill_alpha / border_alpha 取值 0~100；border_width 单位为 pt

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `x` | number | 否 | 形状左上角横坐标（磅 pt，1pt = 12700 EMU） |
| `y` | number | 否 | 形状左上角纵坐标（磅 pt，1pt = 12700 EMU） |
| `w` | number | 否 | 形状宽度（磅 pt，1pt = 12700 EMU），必须 > 0 |
| `h` | number | 否 | 形状高度（磅 pt，1pt = 12700 EMU），必须 > 0 |
| `shape_type` | string | 否 | 形状预设类型，如 rect / ellipse / triangle / rightArrow / leftArrow 等；空串默认 rect。注意：rightArrow / leftArrow 是固定方向的图形预设箭头块，不能指定起点终点；如需画两点之间的方向性箭头线条，请改用 slide_add_line_shape |
| `fill_color` | string | 否 | 填充颜色（RRGGBB，无 # 前缀）；空串表示无填充 |
| `fill_alpha` | number | 否 | 填充透明度 0~100，默认 100 |
| `border_color` | string | 否 | 边框颜色（RRGGBB）；空串表示无边框 |
| `border_dash` | string | 否 | 边框线型，如 solid / dash / dot；空串默认 solid |
| `border_width` | number | 否 | 边框宽度（pt）；<= 0 取默认 1.0 |
| `border_alpha` | number | 否 | 边框透明度 0~100，默认 100 |

---

### slide_add_shapes

#### 功能说明

批量在同一幻灯片插入多个形状。shapes 为对象数组，单个对象的字段含义同 slide_add_shape（不再接受 file_id 等顶层字段）。长度必须 >= 1。【重要 — 箭头消歧，与 slide_add_shape 完全一致】本工具仅支持 rightArrow / leftArrow 这两种图形预设箭头块；批量画"从起点到终点的箭头线"请改用 slide_add_line_shapes 并设置 line_type=arrow / doubleArrow。用户说"加箭头"时请先确认要"线条箭头"还是"图形箭头"

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shapes` | array | 否 | 待插入的形状列表，单元素字段：x / y / w / h / shape_type / fill_color / fill_alpha / border_color / border_dash / border_width / border_alpha。shape_type 可选 rect / ellipse / triangle / rightArrow / leftArrow 等；方向性箭头线条请改用 slide_add_line_shapes |

---

### slide_add_line_shape

#### 功能说明

在指定幻灯片插入一根线形 / 方向性箭头线条（从 (x1,y1) 起点到 (x2,y2) 终点）。这是绘制"两点之间的箭头线"的正确工具：line_type=arrow 单端箭头、doubleArrow 双端箭头、line 普通直线。slide_add_shape 不能画这种线条箭头，它只支持 rightArrow / leftArrow 两种固定方向的图形块预设。x1/y1 / x2/y2 单位为磅（pt，1pt = 12700 EMU）；width 单位为 pt

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `x1` | number | 否 | 起点横坐标（磅 pt，1pt = 12700 EMU） |
| `y1` | number | 否 | 起点纵坐标（磅 pt，1pt = 12700 EMU） |
| `x2` | number | 否 | 终点横坐标（磅 pt，1pt = 12700 EMU） |
| `y2` | number | 否 | 终点纵坐标（磅 pt，1pt = 12700 EMU） |
| `line_type` | string | 否 | 线形类型：line / arrow / doubleArrow；空串默认 line |
| `color` | string | 否 | 颜色（RRGGBB）；空串默认 000000 |
| `dash` | string | 否 | 线型：solid / dash / dot；空串默认 solid |
| `width` | number | 否 | 线宽（pt）；<= 0 取默认 1.0 |

---

### slide_add_line_shapes

#### 功能说明

批量在同一幻灯片插入多根线形 / 方向性箭头线条。lines 为对象数组，单元素字段含义同 slide_add_line_shape。长度必须 >= 1。这是批量绘制"两点之间的方向性箭头线"的正确工具（line_type=arrow / doubleArrow）；slide_add_shapes 不能批量画线条箭头，它只支持 rightArrow / leftArrow 两种图形预设块

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `lines` | array | 否 | 待插入的线形列表，单元素字段：x1 / y1 / x2 / y2 / line_type / color / dash / width |

---

### slide_add_image

#### 功能说明

在指定幻灯片插入一张图片。图片来源二选一：
(1) content 传图片的 base64 编码字符串（不含 data URI 前缀），仅适合图片体积较小的场景，由服务端完成上传；若图片过大导致 base64 内容超出 MCP 单次传输限制，必须改用 image_id 方式。
(2) image_id 传图片上传后返回的加密 ID 字符串（有效期为一天），适合图片体积较大、base64 内容超出 MCP 单次传输限制的场景。

【image_id 推荐获取方式】调用 tencent-docs MCP 的 `upload_image` 工具，它会接收图片的 base64 编码并返回 image_id。调用示例：
```json
{
  "name": "upload_image",
  "arguments": {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "file_name": "photo.png"
  }
}
```
返回结构：`{"image_id": "...", "error": "", "trace_id": "..."}`，取 `image_id` 字段值传入此处即可。

【限制】
- 单张图片大小不超过 10MB；
- 支持 PNG / JPG / JPEG / GIF / BMP / WEBP / SVG 格式；
- `image_base64` 必须传图片文件的实际 base64 编码内容，不要传文件路径或 URL；
- `file_name` 必须带扩展名（如 `photo.png`）以便服务端识别格式；
- 返回的 image_id 仅对当前账号有效，且自上传起 1 天后过期；过期后需重新上传。

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `x` | number | 否 | 图片左上角横坐标（磅 pt，1pt = 12700 EMU） |
| `y` | number | 否 | 图片左上角纵坐标（磅 pt，1pt = 12700 EMU） |
| `w` | number | 否 | 图片宽度（磅 pt，1pt = 12700 EMU），<=0 时使用图片自身原始宽度 |
| `h` | number | 否 | 图片高度（磅 pt，1pt = 12700 EMU），<=0 时使用图片自身原始高度 |
| `image_id` | string | 否 | 已上传图片的加密 ID（有效期一天），与 content 二选一。适合图片体积较大、base64 内容超出 MCP 单次传输限制的场景。  【推荐获取方式】调用 tencent-docs MCP 的 `upload_image` 工具，传入： - `image_base64`：图片文件的实际 base64 编码内容（不含 data URI 前缀，不要传文件路径或 URL），≤10MB； - `file_name`：带扩展名的图片文件名（如 `photo.png`），支持 PNG / JPG / JPEG / GIF / BMP / WEBP / SVG。 返回结构 `{"image_id": "...", "error": "", "trace_id": "..."}`，将 `image_id` 字段值传入此处。  【兜底获取方式】如果图片体积过大，连 `upload_image` 的 `image_base64` 入参也超出 MCP 单次传输限制，请引导用户走腾讯文档开放平台 OpenAPI 上传图片： 1. 提示用户访问 [https://docs.qq.com/open/developers/?nlc=1#/login](https://docs.qq.com/open/developers/?nlc=1#/login) 登录开放平台后台，完成 OAuth 授权流程后获取以下 3 个凭证并交给本工具调用方：`Access-Token`、`Client-Id`、`Open-Id`； 2. 调用方拿到 3 个凭证后，使用 multipart/form-data 形式直接传图片文件（无需 base64 编码，不受 MCP 单次传输限制约束），示例命令： ```bash curl --location --request POST 'https://docs.qq.com/openapi/resources/v2/images' \   --header 'Access-Token: ACCESS_TOKEN' \   --header 'Client-Id: CLIENT_ID' \   --header 'Open-Id: OPEN_ID' \   --form 'image=@"/path/to/your/image.png"' ``` 3. 从返回 JSON 中取 `imageID` 字段值传入此处即可。  【限制】image_id 仅对当前账号有效，自上传起 1 天后过期；过期后需重新上传。 |
| `content` | string | 否 | 图片的 base64 编码内容（不含 data URI 前缀），与 image_id 二选一。适合图片体积较小的场景；若图片过大导致 base64 内容超出传输限制，请改用 image_id 方式 |

---

### slide_add_text

#### 功能说明

在指定幻灯片插入一个文本框。x/y/w/h 单位为磅（pt，1pt = 12700 EMU），w/h 必须 > 0；text 为空串表示空文本框；font_color / fill_color / border_color 均为 6 位 hex（无 # 前缀）；font_size 单位为 pt，<= 0 取默认字号；border_width 单位为 pt，<= 0 取默认 1.0

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `x` | number | 否 | 文本框左上角横坐标（磅 pt，1pt = 12700 EMU） |
| `y` | number | 否 | 文本框左上角纵坐标（磅 pt，1pt = 12700 EMU） |
| `w` | number | 否 | 文本框宽度（磅 pt，1pt = 12700 EMU），必须 > 0 |
| `h` | number | 否 | 文本框高度（磅 pt，1pt = 12700 EMU），必须 > 0 |
| `text` | string | 否 | 文本内容；空串表示空文本框 |
| `font_color` | string | 否 | 字体颜色（RRGGBB，无 # 前缀）；空串使用默认色 |
| `font_name` | string | 否 | 字体名称；空串使用默认字体 |
| `font_size` | number | 否 | 字号（pt）；<= 0 时使用默认字号 |
| `fill_color` | string | 否 | 文本框背景填充色（RRGGBB）；空串表示透明无填充 |
| `border_color` | string | 否 | 文本框边框色（RRGGBB）；空串表示无边框 |
| `border_dash` | string | 否 | 边框线型，如 solid / dash / dot；空串默认 solid |
| `border_width` | number | 否 | 边框宽度（pt）；<= 0 取默认 1.0 |

---

### slide_add_texts

#### 功能说明

批量在同一张幻灯片插入多个文本框，单次产生一个 SlideCommand（一次广播），比循环调用 slide_add_text 更高效。texts 为对象数组，单元素字段含义同 slide_add_text（不再接受 file_id 等顶层字段）。长度必须 >= 1

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `texts` | array | 否 | 待插入的文本框列表，单元素字段：x / y / w / h / text / font_color / font_name / font_size / fill_color / border_color / border_dash / border_width |

---

### slide_reorder_shape

#### 功能说明

调整指定形状的 z-order 层级。op 取值：0=置于顶层 / 1=置于底层 / 2=上移一层 / 3=下移一层。shape_ids 为待调整顺序的形状 ID 列表，长度必须 >= 1

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_ids` | array | 否 | 待调整 z-order 的形状 ID 字符串数组，长度 >= 1 |
| `op` | number | 否 | z-order 操作类型：0=置顶 / 1=置底 / 2=上移 / 3=下移 |

---

### slide_remove_shapes

#### 功能说明

从指定幻灯片删除一个或多个形状。shape_ids 为待删除的形状 ID 列表，长度必须 >= 1

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_ids` | array | 否 | 待删除的形状 ID 字符串数组，长度 >= 1 |

---

### slide_get_shape_info

#### 功能说明

查询指定幻灯片中某个形状的详细信息（包含 type / preset_geom / bounds / text / fill / border / 字体属性 等 16 个字段）。仅支持 SHAPE / CONNECTOR / PICTURE 三种类型；其他类型（如 GROUP / TABLE / CHART）返回的 type 字段会标识为对应类型，但部分字段（fill / border 等）可能为空

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |

---

### slide_set_shape_properties

#### 功能说明

修改指定形状的视觉 / 变换属性，仅传入需要修改的字段，未传字段保持不变。同时支持 visual（fill_color / fill_alpha / border_color / border_alpha / border_width / border_dash）与 transform（x / y / w / h / rotation），cgo 内部合并为单一 SlideCommand。坐标 / 尺寸单位为磅（pt，1pt = 12700 EMU）；rotation 单位为度；border_width 单位为磅（pt）；fill_alpha / border_alpha 取值 0~100000（与 OOXML 对齐，100000 为完全不透明）；border_dash 为 OOXML STPresetLineDashVal 字符串（如 "solid" / "dash" / "dashDot"）。所有可选属性集中放在 properties 对象内，仅传需要修改的字段

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `properties` | object | 否 | 待修改的形状属性集合，仅传需要修改的字段。支持字段：fill_color (string, 6 位 hex，如 "FF0000")、fill_alpha (number, 0~100000)、border_color (string, 6 位 hex)、border_alpha (number, 0~100000)、border_width (number, pt)、border_dash (string, OOXML STPresetLineDashVal)、x / y / w / h (number, pt，1pt = 12700 EMU)、rotation (number, 度) |

---

## 文本工具组（Text）

### slide_append_text

#### 功能说明

向指定 shape 文本末尾追加文本

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | shape ID |
| `text` | string | 否 | 追加文本 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_insert_text

#### 功能说明

在指定 shape 文本位置插入文本

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | shape ID |
| `index` | integer | 否 | 插入位置 |
| `text` | string | 否 | 插入文本 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_delete_text

#### 功能说明

删除指定 shape 文本区间

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | shape ID |
| `index` | integer | 否 | 起始位置 |
| `count` | integer | 否 | 删除长度 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_find_text

#### 功能说明

在演示文稿中查找文本

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `search` | string | 否 | 搜索文本 |

---

### slide_find_replace_text

#### 功能说明

在指定页查找并替换文本

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `search` | string | 否 | 搜索文本 |
| `replace` | string | 否 | 替换文本 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_set_text_property

#### 功能说明

设置指定文本区间富文本属性

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | shape ID |
| `index` | integer | 否 | 起始字符偏移（utf-16 code unit） |
| `count` | integer | 否 | 区间字符数 |
| `color` | string | 否 | 文字颜色 RRGGBB |
| `font_size` | number | 否 | 字号 pt；<=0 表示不修改 |
| `font_name` | string | 否 | 字体名 |
| `bold` | bool | 否 | 粗体 |
| `italic` | bool | 否 | 斜体 |
| `underline` | string | 否 | 下划线类型，如 single / double / none |
| `strikethrough` | string | 否 | 删除线类型，如 single / double / none |
| `letter_spacing` | number | 否 | 字符间距 |
| `baseline` | number | 否 | 基线偏移 |

---

### slide_get_text

#### 功能说明

获取指定 shape 的文本内容与样式区间

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | shape ID |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

## 表格工具组（Table）

### slide_add_table

#### 功能说明

在指定幻灯片页创建空表格，page_index 从 0 开始计数；坐标与尺寸单位为磅（pt，1pt = 12700 EMU）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `x` | number | 否 | 表格左上角 X 坐标，单位为磅（pt，1pt = 12700 EMU） |
| `y` | number | 否 | 表格左上角 Y 坐标，单位为磅（pt，1pt = 12700 EMU） |
| `w` | number | 否 | 表格总宽度，单位为磅（pt），会在列之间均分 |
| `h` | number | 否 | 表格总高度，单位为磅（pt），会在行之间均分 |
| `rows` | number | 否 | 表格行数，必须大于 0 |
| `cols` | number | 否 | 表格列数，必须大于 0 |

---

### slide_insert_table_rows

#### 功能说明

在表格 shape 中插入一行或多行。index 是间隙位置：对 N 行表格，有效范围为 [0, N]；count 未传时默认 1；reference_row_index 指定复制高度的已有行

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `index` | number | 否 | 插入间隙位置；0 表示表格顶部，N 表示表格底部 |
| `reference_row_index` | number | 否 | 复制高度的已有行索引，从 0 开始；必须显式指定 |
| `count` | number | 否 | 插入行数，未传时默认 1，必须大于 0 |

---

### slide_insert_table_cols

#### 功能说明

在表格 shape 中插入一列或多列。index 是间隙位置：对 M 列表格，有效范围为 [0, M]；count 未传时默认 1；插入后表格总宽度保持不变并重新均分列宽

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `index` | number | 否 | 插入间隙位置；0 表示最左侧，M 表示最右侧 |
| `count` | number | 否 | 插入列数，未传时默认 1，必须大于 0 |

---

### slide_delete_table_rows

#### 功能说明

从表格 shape 中删除一行或多行，从 index 指定的行开始；count 未传时默认 1，index + count 不能超过当前行数

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `index` | number | 否 | 起始删除行索引，从 0 开始 |
| `count` | number | 否 | 删除行数，未传时默认 1，必须大于 0 |

---

### slide_delete_table_cols

#### 功能说明

从表格 shape 中删除一列或多列，从 index 指定的列开始；count 未传时默认 1，index + count 不能超过当前列数

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `index` | number | 否 | 起始删除列索引，从 0 开始 |
| `count` | number | 否 | 删除列数，未传时默认 1，必须大于 0 |

---

### slide_merge_table_cells

#### 功能说明

合并表格 shape 中的矩形单元格区域，区域由 start_row/start_col 和 row_span/col_span 指定；合并后内容来自左上角单元格

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `start_row` | number | 否 | 合并区域左上角行索引，从 0 开始 |
| `start_col` | number | 否 | 合并区域左上角列索引，从 0 开始 |
| `row_span` | number | 否 | 合并区域行跨度，必须大于 0 |
| `col_span` | number | 否 | 合并区域列跨度，必须大于 0 |

---

### slide_unmerge_table_cells

#### 功能说明

取消表格 shape 中指定矩形区域的单元格合并，区域由 start_row/start_col 和 row_span/col_span 指定

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `start_row` | number | 否 | 区域左上角行索引，从 0 开始 |
| `start_col` | number | 否 | 区域左上角列索引，从 0 开始 |
| `row_span` | number | 否 | 区域行跨度，必须大于 0 |
| `col_span` | number | 否 | 区域列跨度，必须大于 0 |

---

### slide_set_cell_text

#### 功能说明

向表格 shape 的单个单元格写入纯文本。row 和 col 从 0 开始计数；文本可为空，不需要传入段落结束符

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始计数 |
| `shape_id` | string | 否 | 目标表格 shape id |
| `row` | number | 否 | 目标单元格行索引，从 0 开始 |
| `col` | number | 否 | 目标单元格列索引，从 0 开始 |
| `text` | string | 否 | 写入单元格的纯文本，可为空 |

---

## 图表工具组（Chart）

### slide_add_chart

#### 功能说明

在指定幻灯片上添加图表

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `<addChartArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

### slide_update_chart_style

#### 功能说明

增量更新指定图表样式

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `<chartStyleArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

### slide_change_chart_type

#### 功能说明

更改指定图表类型

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | 图表 shape ID |
| `new_chart_type` | string | 否 | 目标图表类型 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_update_chart_data

#### 功能说明

替换指定图表的内嵌数据

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | 图表 shape ID |
| `categories` | array | 否 | 分类标签 |
| `series` | array | 否 | 数据系列 |
| `sub_chart_index` | integer | 否 | 子图表索引 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_get_chart_info

#### 功能说明

获取指定图表结构信息

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_id` | string | 否 | 图表 shape ID |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

## 分组工具组（Group）

### slide_get_group_info

#### 功能说明

获取指定 group shape 的子 shape 列表

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `group_id` | string | 否 | group shape ID |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_group_shapes

#### 功能说明

将同一页多个 shape 组合成 group shape

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `shape_ids` | array | 否 | shape ID 列表 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_ungroup_shapes

#### 功能说明

解散指定 group shape

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `group_id` | string | 否 | group shape ID |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_reorder_shapes_in_group

#### 功能说明

调整分组内子 shape 层级

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `group_id` | string | 否 | group shape ID |
| `shape_ids` | array | 否 | 子 shape ID 列表 |
| `to_index` | integer | 否 | 目标层级序号 |
| `page_index` | integer | 否 | 幻灯片页索引（0-based） |

---

### slide_update_group_shape_properties

#### 功能说明

更新分组视觉或变换属性

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `<groupPropertyArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

## 动画工具组（Animation）

### slide_add_anim

#### 功能说明

为指定幻灯片中的某个形状添加动画效果。anim_type 为动画类型整数值（通过 slide_list_anim_types 获取可用值）；anim_subtype 为方向/子类型（仅 FLY_IN/FLY_OUT 等需要，0 表示不需要）；index 为动画在该页动画序列中的插入位置（0-based，必须 >= 0；想追加到末尾时填一个 >= 当前动画数量的值即可，例如 9999；不支持 -1）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `anim_type` | number | 否 | 动画类型整数值 |
| `anim_subtype` | number | 否 | 动画方向/子类型整数值，0 表示不需要 |
| `index` | number | 否 | 动画在该页动画序列中的插入位置，0-based，必须 >= 0。想追加到末尾时填一个 >= 当前动画数量的值即可（例如 9999），不支持 -1。 |

---

### slide_list_anim_types

#### 功能说明

列出所有支持的动画类型，包含类型名称、分类（entrance / exit / emphasis）以及是否支持方向参数。返回的 type 整数值可直接用于 slide_add_anim 的 anim_type 参数

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一（仅用于 ticket 校验） |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |

---

### slide_remove_anim

#### 功能说明

移除指定形状的某个动画。index 为动画在形状动画序列中的位置（0-based）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `index` | number | 否 | 要移除的动画索引（0-based） |

---

### slide_move_anim

#### 功能说明

移动指定形状的动画在序列中的位置（从 from_index 移到 to_index）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `from_index` | number | 否 | 动画当前索引（0-based） |
| `to_index` | number | 否 | 动画目标索引（0-based） |

---

### slide_set_anim_properties

#### 功能说明

修改指定形状某个动画的类型和方向。index 为动画在序列中的索引（0-based）；anim_type 为新动画类型；anim_subtype 为新方向（0 表示不需要）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `index` | number | 否 | 要修改的动画索引（0-based） |
| `anim_type` | number | 否 | 新的动画类型整数值 |
| `anim_subtype` | number | 否 | 新的动画方向整数值，0 表示不需要 |

---

### slide_set_anim_trigger

#### 功能说明

修改指定形状某个动画的触发方式。trigger_shape_id 为触发形状 ID，空串表示设为默认触发（即"单击"播放，跟随默认序列）

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `page_index` | number | 否 | 目标幻灯片页索引，从 0 开始 |
| `shape_id` | string | 否 | 目标形状的 shape_id |
| `index` | number | 否 | 要修改的动画索引（0-based） |
| `trigger_shape_id` | string | 否 | 触发形状 ID，空串表示设为默认触发 |

---

## 主题工具组（Theme）

### slide_get_themes

#### 功能说明

获取当前演示文稿中嵌入的所有主题列表，返回每个主题的 theme_id 和 theme_name

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |

---

### slide_list_builtin_themes

#### 功能说明

列出服务端所有内置（预置）主题，返回每个主题的 theme_id 和 theme_name；不依赖文档状态，可在调用 slide_set_theme 前用于查询可用的内置主题 ID

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 可选，仅用于 trace/log |

---

### slide_set_theme

#### 功能说明

设置演示文稿的主题。支持两种模式：(1) switch：传入已存在于文档中的 theme_id，切换到该主题；(2) builtin：is_builtin=true，传入内置主题 ID（可通过 slide_list_builtin_themes 获取），由服务端自动加载内置 ThemeElements

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `theme_id` | string | 否 | 目标主题 ID（必填） |
| `is_builtin` | bool | 否 | 是否使用内置主题（true 时 theme_id 须为内置主题 ID） |

---

## 批注工具组（Comment）

### slide_get_comments

#### 功能说明

获取全部批注或指定页批注

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | integer | 否 | 页索引，-1 表示全部页 |

---

### slide_add_comment

#### 功能说明

在指定幻灯片上添加批注锚点

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `<commentArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

### slide_remove_comment

#### 功能说明

删除指定批注分组

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `<commentKeyArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

### slide_modify_comment

#### 功能说明

修改指定批注分组属性

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `text` | string | 否 | 批注文本 |
| `author_name` | string | 否 | 作者名称 |
| `<commentKeyArgs>` | object | 否 | 更多参数详见 mcporter list slide-mcp 的 schema |

---

### slide_reply_comment

#### 功能说明

向已有批注分组追加一条回复

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | integer | 否 | 页索引 |
| `group_id` | string | 否 | 批注分组 ID |
| `text` | string | 否 | 回复文本 |
| `author_name` | string | 否 | 作者名称 |

---

## 节工具组（Section）

### slide_get_sections

#### 功能说明

获取演示文稿中的全部节

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |

---

### slide_add_section

#### 功能说明

在指定位置添加新节。提供 before_slide_index 或 after_section_id 之一来指定插入位置。\n- before_slide_index: 新节将拥有目标页及其后续页面（直到下一个节边界）。原来拥有该页的节将从下一页开始。\n- after_section_id: 新节作为空节插入到指定节之后，不会接管任何页面。

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片URL，与 file_id 二选一 |
| `before_slide_index` | number | 否 | 0-based slide 索引，新节插入到该 slide 之前并拥有它（该 slide 成为新节的第一页）。原来包含该 slide 的节将从下一页开始。与 after_section_id 互斥 |
| `after_section_id` | string | 否 | 已有节的 ID，新节作为空节插入到该节之后（不接管任何页面）；传空字符串表示在最开头插入空节。与 before_slide_index 互斥。使用 slide_get_sections 获取有效的 section ID |
| `name` | string | 否 | 节名称 |

---

### slide_remove_sections

#### 功能说明

删除一个或多个节但保留节内幻灯片

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `section_ids` | array | 否 | 节 ID 列表 |

---

### slide_remove_section_with_slides

#### 功能说明

删除指定节及其幻灯片

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `section_id` | string | 否 | 节 ID |

---

### slide_move_section

#### 功能说明

移动指定节到新的节序号位置

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `section_id` | string | 否 | 节 ID |
| `to_section_index` | integer | 否 | 目标节序号 |

---

### slide_rename_section

#### 功能说明

修改指定节的名称

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `section_id` | string | 否 | 节 ID |
| `name` | string | 否 | 节名称 |

---

### slide_move_slides_to_section

#### 功能说明

Move one or more slides into a target section. The slides are appended 

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_indices` | array | 否 | 要移动的幻灯片 0-based 索引列表 |
| `section_id` | string | 否 | 目标节 ID |

---

## 演示文稿级工具组（Presentation）

### slide_set_slide_size

#### 功能说明

设置演示文稿页面尺寸，仅支持 16:9 和 4:3 两种比例

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `aspect_ratio` | number | 否 | 页面宽高比：1=4:3, 2=16:9（必填） |
| `scale_mode` | string | 否 | 缩放模式：default（等比缩放）/ no_scale（不缩放，居中）/ enlarge（向放大方向缩放） |
| `scale_master_layout` | bool | 否 | 是否缩放母版版式 |

---

### slide_set_default_font

#### 功能说明

设置演示文稿默认字体

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `latin_font` | string | 否 | 西文字体名 |
| `ea_font` | string | 否 | 东亚字体名 |
| `font_size` | number | 否 | 默认字号 pt |
| `font_color` | string | 否 | 字体颜色 RRGGBB |
| `options` | object | 否 | 额外字体选项（bold / italic / spacing 等） |

---

## 备注工具组（Notes）

### slide_set_notes_text

#### 功能说明

设置或覆盖指定幻灯片的备注页（演讲者备注）文本，page_index 从 0 开始计数；text 为空字符串时表示清空备注页文本

#### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_id` | string | 否 | 文档ID，与 file_url 二选一 |
| `file_url` | string | 否 | 在线幻灯片的URL链接，与 file_id 二选一 |
| `page_index` | number | 否 | 待设置备注的幻灯片页索引，从 0 开始计数 |
| `text` | string | 否 | 备注页文本；空字符串表示清空当前备注 |

---

## 典型工作流示例

### 在幻灯片中添加带文字的形状

```
1. 调用 slide_add_shape 创建形状，获取 shape_id
2. 调用 slide_append_text 向形状内添加文本
3. 调用 slide_set_text_property 设置文本样式（可选）
```

### 创建带数据的表格

```
1. 调用 slide_add_table 创建空表格，获取 shape_id
2. 循环调用 slide_set_cell_text 填充每个单元格的数据
3. 如需要，调用 slide_merge_table_cells 合并表头单元格
```

### 查找并替换文本

```
1. 调用 slide_find_text 查找目标文本，获取所有匹配位置
2. 确认需要替换的页面后，调用 slide_find_replace_text 在指定页执行替换
```

### 批量添加多个元素到同一页

```
1. 使用 slide_add_shapes 批量插入形状（比循环调用 slide_add_shape 更高效）
2. 使用 slide_add_texts 批量插入文本框
3. 使用 slide_add_line_shapes 批量插入连接线
```

### 管理演示文稿节

```
1. 调用 slide_get_sections 查看现有节结构
2. 调用 slide_add_section 添加新节
3. 调用 slide_move_section 调整节顺序
4. 调用 slide_rename_section 修改节名称
```

### 为形状添加动画

```
1. 调用 slide_list_anim_types 查看支持的动画类型
2. 调用 slide_add_anim 为目标形状添加动画
3. 调用 slide_set_anim_trigger 设置触发方式（可选）
```

### 切换主题

```
1. 调用 slide_list_builtin_themes 查看可用的内置主题
2. 调用 slide_set_theme（设置 is_builtin=true + 内置主题 ID）切换主题
```

### 添加图表

```
1. 调用 slide_add_chart 创建带数据的图表
2. 调用 slide_update_chart_style 调整样式（标题/图例/坐标轴等）
3. 如需修改数据，调用 slide_update_chart_data
4. 如需更改图表类型，调用 slide_change_chart_type
```

### 插入图片

```
1.（推荐）调用 tencent-docs MCP 的 upload_image 工具上传图片，拿到 image_id
2. 调用 slide_add_image，传入 image_id（与 content 二选一）
3. 如需调整位置 / 大小，调用 slide_set_shape_properties
```

---

## 注意事项

- 仅支持演示文稿（幻灯片/PPT）类型
- `page_index` 从 0 开始计数，第 1 页 = `page_index: 0`
- 坐标与尺寸单位为 **磅（pt）**，标准页面尺寸 960×540 pt（16:9）/ 720×540 pt（4:3）
- 边框宽度单位为 **pt**（磅）；EMU 换算：`1 pt = 12700 EMU`
- 操作前需确保拥有文档的编辑权限
- 写类工具大部分返回空消息（实际结果通过 MCP TextContent 透出）
- 批量操作（`slide_add_shapes` / `slide_add_texts` / `slide_add_line_shapes`）比循环单个调用更高效，建议优先使用
- 连续多步编辑时，建议将上一步返回的 `version` / `new_version` 传入下一步的 `version_info.base_version`
- `slide_find_text` 全文搜索，`slide_find_replace_text` 按页替换
- 表格操作需要先通过 `slide_add_table` 获取 `shape_id`，后续所有行列操作都基于该 `shape_id`
- **动画类型整数值必须通过 `slide_list_anim_types` 实时查询，不要硬编码**：其 `type` 字段已与底层 `AnimType` 枚举一一对应（如 FLY_IN=6 / FADE_OUT=2 / SCALE=3），若客户端硬编码旧映射会与底层枚举错位，实际执行的动画与预期完全不同
- `slide_add_anim` 的 `index` 必须 **≥ 0**：虽然部分老文档/工具描述里出现过"-1 表示追加到末尾"的说法，当前底层 `AddAnimationRequest` 会拒绝负值。追加到末尾请先调读类拿到当前动画数 N，再传 `index=N`
- 形状的 `shape_id` 通过读类接口（如 `slide_get_shape_info` / `slide_get_page_info`）获取
- 颜色值统一使用 6 位十六进制 RRGGBB 格式（不含 `#` 前缀）
- 图片插入推荐通过 tencent-docs MCP 的 `upload_image` 拿 `image_id`，避免大 base64 撑爆 MCP 单次传输
- 本文档由 `slideengine_mcp_tools.go` 自动派生（参考脚本 `.tmp/gen_slideengine_md.py`）。如与 `mcporter list slide-mcp` 返回的 schema 冲突，以 schema 为准。
