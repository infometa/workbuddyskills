# 布局速查表

## 画板尺寸公式

```
board_width  = pad*2 + cols * cell_w + (cols-1) * gap
board_height = pad*2 + title_h + rows * cell_h + (rows-1) * gap
rows         = ceil(item_count / cols)
```

## 子节点位置公式（相对画板左上角）

```
row, col = divmod(index, cols)
child_x  = pad + col * (cell_w + gap)
child_y  = pad + title_h + row * (row_h + gap)

# row_h 取决于是否显示 caption：
row_h = cell_h + caption_h   # 有 caption 时
row_h = cell_h               # 无 caption 时
```

## Caption 文字节点

caption 显示素材标题，放在每个素材下方。

**关键约束：** text 节点不能作为 artboard 子节点，caption 使用绝对坐标放置。

```
caption_x = board_x + child_x        # 绝对坐标
caption_y = board_y + child_y + cell_h + 2   # 素材底边下方 2px
```

默认样式：`fontSize=14, fontWeight=400, color="#cccccc", width=cell_w`

开启方式：
- CLI: `--captions`
- rules.json 全局: `"show_captions": true`
- rules.json 组级别: 在组定义中添加 `"show_captions": true/false` 覆盖全局设置

布局参数（可在 `layout` 中自定义）：
| 参数 | 默认值 | 说明 |
|---|---|---|
| `caption_h` | 28 | caption 行高（含间距） |
| `caption_font_size` | 14 | 字号 |
| `caption_color` | #cccccc | 字体颜色 |
| `caption_max_len` | 20 | 标题截断长度（超出部分用 … 省略） |

## 画板标题位置（独立 text 节点）

标题不是画板子节点，而是独立 text 节点，放在画板**外部上方**：

```
title_x = board_x + pad     # 与画板左侧对齐
title_y = board_y - 80      # 画板上方 80px
```

text 节点推荐样式：`fontSize=40, fontWeight=700, color="#ffffff", width=600`。

## 常用尺寸配置

| 场景 | cell | cols | 单板宽度 |
|---|---|---|---|
| 人物资产（需要看清脸） | 320×320 | 4 | ~1400 |
| 风格参考 / 分镜图 | 280×280 | 5~7 | 1500 ~ 2100 |
| 视频库（16:9） | 360×203 | 3 | ~1200 |
| 缩略图墙 | 180×180 | 8~10 | 1600 ~ 2000 |

## 横向总宽度估算

```
total_width = sum(board_w) + (n-1) * board_gap
```

对 5 个典型画板（cols=4/5/4/6/3），总宽约 **6000 ~ 8000 px**，WorkRally 无限画布可以轻松承载。

## 画板数量建议

- **< 3 个画板**：整理意义不大，考虑不分板
- **3 ~ 6 个画板**：最佳区间，横向一屏可浏览
- **> 8 个画板**：考虑分两行（y 轴错开），或用 "大类 + 子分类" 命名来提示结构

## 两行布局（可选扩展）

如果画板太多需要换行，可以修改 `build_nodes` 让 y 方向也堆叠：

```python
# 伪代码
MAX_WIDTH = 8000
if x_cur + board_w > MAX_WIDTH:
    x_cur = 0
    y_cur += max_row_height + board_gap + 200  # 200 为标题空间
```
