# 理解已有 PPT / 问答

读懂一份已经存在的 `.ppt` / `.pptx`，并回答关于它的问题（某一页讲什么、全文结构、某段文字在哪一页等）。

这不是风格抽取，也不是质量评测，也不是重新生成一版。要改内容则转 [edit-existing](edit-existing.md)。

## 调用约定

所有读操作经本 Skill 的 `edsdk.py`，路径必须带 `${CODEBUDDY_SKILL_DIR}`（Bash 的 cwd 是 workspace 根，裸 `edsdk.py` 会找不到文件）：

```bash
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" list slide
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" schema <工具名>
python3 "${CODEBUDDY_SKILL_DIR}/scripts/edsdk.py" call <工具名> ...
```

打开、拿 `file_id`、预览规则与编辑分支相同，见 [edit-existing](edit-existing.md)「工作流」。拿到 `file_id` 后再读，不要凭路径猜。

调用任何 `slide_*` 前必须先 `schema` 该工具；工具清单见 [slide-tools.md](slide-tools.md)。

## 读侧常用工具

从 [slide-tools.md](slide-tools.md) 按需挑选，典型问答用这些：

| 意图 | 工具 |
|---|---|
| 演示文稿元数据 / 页数 | `slide_get_info` |
| 某一页有哪些形状、动画 | `slide_get_page_info` |
| 某形状上的文字 | `slide_get_text` |
| 某形状详情 | `slide_get_shape_info` |
| 表格结构 | `slide_get_table_info` |
| 备注 | `slide_get_notes_text` |
| 章节 | `slide_get_sections` |

不确定页码或元素时，先 `slide_get_info` / `slide_get_page_info` 再精读，不要一次性拉全量。

读完用自然语言回答用户；不要把内部工具名、`file_id`、pt 坐标讲给用户。
