# slide_* 工具清单

上级：[SKILL.md](../SKILL.md) · [edit-existing](edit-existing.md) · [understand](understand.md)。工具名带 `slide_` 前缀。

```bash
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" list slide
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema <slide_tool>
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call <slide_tool> file_id=<id> page_index=0 ...
```

完整工具清单和参数以服务端 `tools/list` / `schema` 实时返回为准；本文只记录 slide 特有的操作约定。

> 调用任何 `slide_*` 工具前，必须先执行 `python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema <工具名>`，确认必填参数、0-based 索引、pt 单位和形状字段语义；下面的接口列表只用于选工具。
> 对参数拿不准时一律先查 schema，绝不凭记忆或下表摘要猜参数。复杂参数用 `--json '{...}'`。

## 坐标和索引

- `page_index`、`shape_index`、表格行列索引等全部是 0-based，和工具参数直接对齐。
- 页面坐标和尺寸单位是磅 `pt`。
- 选区信息里的 `page_index`、`shape_index`、表格行列索引等已经与工具参数对齐，无需额外 `+1` 或 `-1`。
- 不确定页面元素、层级、文本范围、表格结构时，先用 `slide_get_page_info`、`slide_get_shape_info`、`slide_get_table_info`、`slide_get_text` 查询。

## 插入和层级

- `slide_add_*` 新元素默认在最上层，可能遮盖已有元素。
- 需要调整遮挡关系时，用 `slide_reorder_shape` 或 `slide_reorder_shapes_in_group`。
- 插入形状时，`fill_color` / `border_color` 至少给一个；否则形状不可见，调用会被拒。
- 批量插入优先用批量工具：`slide_add_shapes`、`slide_add_texts`、`slide_add_line_shapes`、`slide_add_slides`。

## 接口列表

| 工具 | 说明 |
|---|---|
| `slide_add_anim` | Bind an entrance/exit animation onto a singl… |
| `slide_add_chart` | Add a chart |
| `slide_add_comment` | Create a NEW comment group |
| `slide_add_datetime` | Add a date/time placeholder onto the specifi… |
| `slide_add_footer` | Add or remove a footer placeholder shape on … |
| `slide_add_image` | Add an image (picture) onto a slide page |
| `slide_add_line_shape` | Add a line shape onto a slide page |
| `slide_add_line_shapes` | Batch-add multiple line shapes onto a single… |
| `slide_add_notes` | Create a speaker-notes |
| `slide_add_page_number` | Add a slide-number placeholder onto the spec… |
| `slide_add_section` | Add a new section at the specified position |
| `slide_add_shape` | Add a shape element onto a slide page |
| `slide_add_shapes` | Batch-add multiple shapes onto a single slid… |
| `slide_add_slide` | Add a new slide page into the presentation |
| `slide_add_slides` | Batch-add multiple new slide pages at a sing… |
| `slide_add_table` | Create a new empty table |
| `slide_add_text` | Create a brand-new textbox at an arbitrary p… |
| `slide_add_texts` | Batch-add multiple texts onto a single slide… |
| `slide_append_notes_text` | Append text to the end of the notes page att… |
| `slide_append_text` | Append text to the end of an existing shape'… |
| `slide_change_chart_type` | Change the chart type of an existing chart s… |
| `slide_delete_table_cols` | Delete one or more columns from an existing … |
| `slide_delete_table_rows` | Delete one or more rows from an existing tab… |
| `slide_duplicate_slide` | Duplicate (deep-copy) one or more slide pages |
| `slide_find_replace_text` | Find and replace text in all standalone shap… |
| `slide_get_chart_info` | Query the full structure of an existing char… |
| `slide_get_comments` | Get all comment groups in the presentation |
| `slide_get_group_info` | Query the children of a group shape on a sli… |
| `slide_get_info` | Get metadata and status of the current prese… |
| `slide_get_master_info` | Get information about slide master |
| `slide_get_notes_text` | Read the plain-text content of the notes pag… |
| `slide_get_page_info` | Get a concise summary of all shapes and anim… |
| `slide_get_sections` | Get all sections in the presentation |
| `slide_get_shape_info` | Get detailed information about a specific sh… |
| `slide_get_table_info` | Read-only query of an existing table shape's… |
| `slide_get_text` | Query the text content and formatting proper… |
| `slide_get_themes` | List all themes embedded in the current pres… |
| `slide_group_shapes` | Group multiple shapes into a single group sh… |
| `slide_insert_table_cols` | Insert one or more columns into an existing … |
| `slide_insert_table_rows` | Insert one or more rows into an existing tab… |
| `slide_list_anim_types` | List the animation kinds currently supported… |
| `slide_list_builtin_themes` | List all built-in |
| `slide_list_recent_ai_edits` | 列出当前 editor 实例最近通过 MCP 写工具产生的编辑 |
| `slide_merge_table_cells` | Merge a rectangular region of cells in an ex… |
| `slide_modify_comment` | Modify a comment group's properties |
| `slide_move_anim` | Move a single animation node within the defa… |
| `slide_move_section` | Move a section |
| `slide_move_slide` | Move one or more slide pages to a new positi… |
| `slide_remove_anim` | Remove a single animation node from a shape … |
| `slide_remove_comment` | Remove a comment group from a slide page |
| `slide_remove_section_with_slides` | Remove a section AND all its slides in one a… |
| `slide_remove_sections` | Remove one or more sections by their IDs |
| `slide_remove_shapes` | Remove |
| `slide_remove_slide` | Remove |
| `slide_rename_section` | Rename an existing section |
| `slide_reorder_shape` | Change the Z-order |
| `slide_reorder_shapes_in_group` | Reorder child shapes inside a group to a new… |
| `slide_reply_comment` | Add a reply to an EXISTING comment group |
| `slide_set_anim_properties` | Replace the TimeNode bound to an existing an… |
| `slide_set_anim_trigger` | Change how an existing animation on a shape … |
| `slide_set_cell_text` | Write plain UTF-8 text into a single cell |
| `slide_set_cell_style` | Set fill, alignment, margins, and borders on table cells |
| `slide_set_hyperlink` | 为形状文本的指定字符范围设置或清除超链接 |
| `slide_set_notes_text` | Replace the entire text content of the notes… |
| `slide_set_page_properties` | Set page-level properties of a slide, includ… |
| `slide_set_shape_properties` | 修改幻灯片中一个或多个形状的属性 |
| `slide_set_slide_size` | 设置演示文稿页面比例，并按策略缩放页面元素 |
| `slide_set_text` | Replace the text content of a shape on a sli… |
| `slide_set_text_property` | 在不修改文本内容的前提下，对形状内指定字符范围设置富文本样式（加粗、斜体、颜色、字号等） |
| `slide_set_theme` | Apply a theme to the presentation |
| `slide_undo_ai_edit` | 根据最近 AI 编辑记录中的 version 撤销指定编辑 |
| `slide_ungroup_shapes` | Dissolve a group shape, restoring its childr… |
| `slide_unmerge_table_cells` | Undo a previous merge over the given rectang… |
| `slide_update_chart_axis` | Modify, hide/show, or restyle one chart axis |
| `slide_update_chart_data` | Replace the data |
| `slide_update_chart_data_labels` | Hide, show, or configure data labels on the … |
| `slide_update_chart_gridlines` | Hide or show major gridlines on the value |
| `slide_update_chart_legend` | Modify or hide/show the chart's legend |
| `slide_update_chart_series_style` | Update the visual style of a single chart se… |
| `slide_update_chart_title` | Modify or hide/show the chart's title |
| `slide_update_chart_trendline` | Add, modify, or remove a trendline on a sing… |
| `slide_update_group_shape_properties` | Apply the same visual and/or transform prope… |
| `slide_update_guide_lists` | 原子更新演示文稿、母版和版式的参考线列表 |

> 参数 schema 以服务端 `tools/list` 实时返回为准；上表为一句话摘要。
