# Guard Rails — 10 Mandatory Production Rules

> 框架级规范。所有 PPT 生成必须遵守，违反任何一条会导致文件损坏或视觉缺陷。

## Rule 1: Bottom Bar Spacing（内容与底栏间距）

**问题**：内容紧贴底部摘要栏，视觉上融为一体。

**必须**：内容底部与底栏之间至少 **0.15"** 间距。

```python
BOTTOM_BAR_GAP = Inches(0.2)
bar_y = last_content_bottom + BOTTOM_BAR_GAP  # ✅
```

**验证**：`bottom_bar_y >= last_content_bottom + Inches(0.15)`

## Rule 2: Content Overflow Protection（内容溢出保护）

**必须**：
1. 右边距：`element.left + element.width ≤ Inches(0.8) + Inches(11.733) = Inches(12.533)`
2. 底边距：`element.top + element.height ≤ Inches(6.95)`
3. 文字在色块内时，文字框必须从色块边缘内缩至少 0.15"

```python
# ✅ 多栏宽度计算（避免负宽度）
col_w = (CW - gap * (num_cols - 1)) / num_cols  # NOT CW / num_cols
```

## Rule 3: No Bottom Whitespace（消除底部空白）

**必须**：底部摘要栏位置在 `Inches(6.1)` 到 `Inches(6.4)` 之间。

```python
bar_y = max(content_bottom + Inches(0.15), Inches(6.1))
bar_y = min(bar_y, Inches(6.4))  # ✅
```

## Rule 4: Legend Color Consistency（图例颜色一致）

**必须**：图例标识符必须使用与图表完全相同颜色的色块（`add_rect()`），不得用纯文字 "■"。

```python
# ✅ 颜色匹配的图例色块
add_rect(s, lgx, legend_y, Inches(0.15), Inches(0.15), NAVY)
add_text(s, lgx + Inches(0.2), ..., '基准值', ...)
```

## Rule 5: Title Style Uniformity（标题样式统一）

**必须**：所有内容页使用 `add_action_title()` / `aat()`（白底+黑字+下划线）。

**禁止**：`add_navy_title_bar()` 在内容页使用（已废弃）。

内容起始 y 值：使用 `add_action_title()` 后，内容从 **Inches(1.25)** 开始（不是 Inches(1.0)）。

## Rule 6: Axis Label Centering（坐标轴标签居中）

**必须**：矩阵/网格图的坐标轴标签必须在整个轴的跨度上居中，不得用固定偏移。

```python
# ✅ Y轴标签垂直居中于完整网格高度
add_text(s, LM, grid_top, Inches(1.8), grid_h,
         'Y轴↑', alignment=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
```

## Rule 7: Image Placeholder Required（图片占位符）

**必须**：8页以上的 PPT，至少1张幻灯片含图片占位符（`add_image_placeholder()` 或自定义灰色框）。

推荐位置：前2–3张内容页之后（作为视觉缓冲）。

## Rule 8: Dynamic Sizing（动态尺寸计算）

**必须**：数量可变的版式（清单行、流程节点、封面多行标题）必须动态计算尺寸。

```python
# ✅ 水平排列：动态宽度
item_w = (CW - gap * (n - 1)) / n

# ✅ 垂直排列：动态高度
item_h = min(MAX_ITEM_H, available_h / max(n, 1))
```

**禁止**：`stage_w = Inches(2.0)` 固定宽度用于 N 个节点。

## Rule 9: BLOCK_ARC for Circular Charts（圆形图表用 BLOCK_ARC）

**必须**：环形图、饼图、仪表盘必须使用 `BLOCK_ARC` 原生形状（3–5 个形状/图表）。

**禁止**：用 `add_rect()` 循环堆砌模拟圆弧（会产生数百到数千个形状，文件巨大且渲染慢）。

详见 `references/layouts/charts-circular.md`。

## Rule 10: Horizontal Item Overflow Protection（水平项溢出保护）

**必须**：水平排列 N 项时，用动态计算防止负宽度。

```python
MIN_GAP = Inches(0.35)
max_item_w = (CW - MIN_GAP * max(n - 1, 1)) / max(n, 1)
item_w = min(PREFERRED_W, max_item_w)  # ✅ 确保非负
```

**影响方法**：`process_chevron()`, `metric_cards()`, `icon_grid()`, `four_column()`。

---

## Anti-Corruption Rules（防止文件损坏）

1. **禁止使用 `add_connector()`** — 会产生 `<p:style>` 导致文件损坏，用 `add_hline()` 代替
2. **所有形状必须调用 `_clean_shape()`** — 删除 p:style 防止效果引用
3. **`eng.save()` 包含 full_cleanup** — 自动清理，无需手动操作
4. **中文文本必须调用 `set_ea_font()`** — 设置 KaiTi 东亚字体

```python
# ✅ 安全的形状创建
shape.fill.solid()
shape.fill.fore_color.rgb = BG_GRAY
shape.line.fill.background()  # 移除边框
_clean_shape(shape)            # 移除 p:style
```
