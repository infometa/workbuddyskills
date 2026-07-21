# 任务 A：全页面结构分析

`analysis_type: "page_structure"`

输出页面类型、布局结构树（sections → elements）、设计概要。每个 section 和关键 element 必须有 `bbox`（百分比坐标）和 `width`/`height`（px 或语义值）。

## Schema

```json
{
  "analysis_type": "page_structure",
  "page_type": "dashboard | web_app | mobile_app | landing_page | form | article | e_commerce | settings | login | other",
  "platform": "iOS | Android | Web | macOS | Windows | unknown",
  "viewport": {"width": 1440, "height": 900},

  "layout": {
    "structure": "sidebar_main | vertical_stack | horizontal_split | grid | tab_based | single_column | free_form",
    "direction": "top_to_bottom | left_to_right",
    "sections": [
      {
        "name": "区域语义名称",
        "type": "navigation | header | hero | content | sidebar | card_grid | list | form | footer | modal | tab_bar | toolbar | banner",
        "bbox": {"x": 0, "y": 0, "width": 16.7, "height": 100},
        "width": "240px",
        "height": "fill",
        "layout_direction": "horizontal | vertical | grid",
        "gap": "16px",
        "padding": "24px",
        "background": "#FFFFFF",
        "elements": [
          {
            "type": "button | text | heading | icon | image | logo | input | link | divider | badge | avatar | card | card_group | chip | tab | menu_item",
            "label": "元素内容",
            "bbox": {"x": 1.1, "y": 7, "width": 14.6, "height": 4.4},
            "width": "fill",
            "height": "40px",
            "visual_traits": "视觉特征简述",
            "interactive": true,
            "state": "default | active | disabled | hover | selected",
            "children": []
          }
        ]
      }
    ]
  },

  "design_summary": {
    "primary_color": "#4F46E5",
    "background_color": "#F9FAFB",
    "surface_color": "#FFFFFF",
    "text_color": "#111827",
    "text_secondary_color": "#6B7280",
    "font_family": "Inter",
    "visual_density": "compact | normal | spacious",
    "overall_style": "minimal | material_design | flat | brutalist | corporate | playful",
    "dark_mode": false,
    "has_shadows": true,
    "has_rounded_corners": true,
    "corner_radius_style": "none | subtle(2-4px) | moderate(6-8px) | rounded(12-16px) | pill"
  },

  "content_summary": "一句话概括页面功能和内容"
}
```

**必填字段**：analysis_type, page_type, platform, viewport, layout(含 sections), sections[].name/type/bbox/width/height/elements, elements[].bbox, design_summary, content_summary。

## 分析方法论

1. **整体感知**：页面类型、平台、主题、密度、视口尺寸
2. **布局骨架**：判断布局模式（sidebar_main / vertical_stack / grid...），划分顶层 bbox
3. **逐区域分析**：
   - 命名 + 分类 + bbox + 设计尺寸
   - 设计属性：background、padding、gap、layout_direction
   - 元素清点（3-8 个最显著）：type、label、bbox、width/height、visual_traits
   - 尺寸计算：`bbox% × viewport → px`，对齐 4/8px 倍数
4. **设计概要**：主色（CTA）、背景色（最大面积）、文字色、风格、阴影/圆角
5. **内容概要**：一句话
6. **bbox 校验**：覆盖完整、无重叠、子在父内、等分一致
