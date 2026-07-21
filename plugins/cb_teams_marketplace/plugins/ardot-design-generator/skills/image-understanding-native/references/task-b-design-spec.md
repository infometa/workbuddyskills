# 任务 B：设计风格提取

`analysis_type: "design_spec"`

提取完整的设计风格规范，**所有参数格式直接对齐 ardot design-mcp API**：
- **colors** — 双格式（hex 给人读 + rgba 给 `apply_variables`）
- **variables** — 可**原样**传给 `apply_variables`，无需转换
- **typography.scale** — 每个字段直接对齐 `batch_edit` 文本属性
- **shadows.system[].effects** — 可直接作为 `batch_edit` 的 effects 参数
- **style_direction.tags** — 可直接传给 `fetch_style_guide(tags)`

覆盖 10 个维度：style_direction / colors / variables / typography / spacing / corner_radius / shadows / borders / icons / layout

## Schema

```json
{
  "analysis_type": "design_spec",

  "style_direction": {
    "name": "Japanese Swiss Minimal Light",
    "description": "2-3 句话描述整体设计语言",
    "key_aesthetics": ["最多 5 个关键特征，每个 1 句话"],
    "tags": ["5-10 个标签，必须从 ALL_STYLE_GUIDE_TAGS 选取"],
    "platform": "webapp | mobile | desktop",
    "dark_mode": false,
    "visual_density": "compact | normal | spacious"
  },

  "colors": {
    "backgrounds": {
      "page": {"hex": "#F5F5F5", "rgba": {"r": 0.96, "g": 0.96, "b": 0.96, "a": 1}, "role": "Page Background"},
      "surface": {"hex": "#FFFFFF", "rgba": {"r": 1, "g": 1, "b": 1, "a": 1}, "role": "Card Surface"}
    },
    "text": {
      "primary": {"hex": "#000000", "rgba": {"r": 0, "g": 0, "b": 0, "a": 1}, "role": "正文标题"},
      "secondary": {"hex": "#999999", "rgba": {"r": 0.6, "g": 0.6, "b": 0.6, "a": 1}, "role": "辅助文字"}
    },
    "borders": {
      "default": {"hex": "#E5E5E5", "rgba": {"r": 0.9, "g": 0.9, "b": 0.9, "a": 1}, "role": "默认边框"}
    },
    "accents": {
      "primary": {"hex": "#4F46E5", "rgba": {"r": 0.31, "g": 0.27, "b": 0.90, "a": 1}, "role": "CTA/Active"},
      "success": {"hex": "#22C55E", "rgba": {"r": 0.13, "g": 0.77, "b": 0.37, "a": 1}, "role": "成功"},
      "error": {"hex": "#EF4444", "rgba": {"r": 0.94, "g": 0.27, "b": 0.27, "a": 1}, "role": "错误"}
    }
  },

  "variables": {
    "Design Tokens": {
      "modes": ["Default"],
      "variables": {
        "page-bg": {"type": "COLOR", "value": {"r": 0.96, "g": 0.96, "b": 0.96, "a": 1}},
        "surface": {"type": "COLOR", "value": {"r": 1, "g": 1, "b": 1, "a": 1}},
        "text-primary": {"type": "COLOR", "value": {"r": 0, "g": 0, "b": 0, "a": 1}},
        "accent-primary": {"type": "COLOR", "value": {"r": 0.31, "g": 0.27, "b": 0.90, "a": 1}},
        "border-default": {"type": "COLOR", "value": {"r": 0.9, "g": 0.9, "b": 0.9, "a": 1}},
        "spacing-base": {"type": "FLOAT", "value": 8},
        "radius-md": {"type": "FLOAT", "value": 8}
      }
    }
  },

  "typography": {
    "families": [
      {"name": "Inter", "role": "primary", "usage": "所有文字", "ardot_fontName": {"family": "Inter", "style": "Regular"}}
    ],
    "scale": [
      {"level": "heading_1", "fontSize": 32, "fontWeight": "700", "fontFamily": "Inter", "letterSpacing": {"value": -1, "unit": "PIXELS"}, "lineHeight": {"value": 40, "unit": "PIXELS"}, "usage": "一级标题"},
      {"level": "heading_2", "fontSize": 24, "fontWeight": "600", "fontFamily": "Inter", "lineHeight": {"value": 30, "unit": "PIXELS"}, "usage": "二级标题"},
      {"level": "body", "fontSize": 16, "fontWeight": "400", "fontFamily": "Inter", "lineHeight": {"value": 24, "unit": "PIXELS"}, "usage": "正文"},
      {"level": "caption", "fontSize": 12, "fontWeight": "500", "fontFamily": "Inter", "lineHeight": {"value": 16, "unit": "PIXELS"}, "usage": "标签"}
    ],
    "weights_used": ["400", "500", "600", "700"],
    "text_case_convention": "default | uppercase | lowercase | snake_case"
  },

  "spacing": {
    "base_unit": 8,
    "scale": [4, 8, 12, 16, 20, 24, 32, 48, 64],
    "patterns": {
      "screen_width": 1440,
      "content_padding": 24,
      "section_gap": 32,
      "card_gap": 16,
      "card_padding": 24,
      "inline_gap": 8
    }
  },

  "corner_radius": {
    "system": "zero | subtle | moderate | rounded | pill | mixed",
    "scale": {"none": 0, "sm": 4, "md": 8, "lg": 12, "xl": 16, "pill": 9999},
    "card": 8,
    "button": 8,
    "input": 8,
    "avatar": 9999,
    "tab_bar": 100
  },

  "shadows": {
    "has_shadows": true,
    "system": [
      {
        "level": "sm",
        "effects": [{"type": "DROP_SHADOW", "color": {"r": 0, "g": 0, "b": 0, "a": 0.05}, "offset": {"x": 0, "y": 1}, "radius": 2, "visible": true, "blendMode": "NORMAL", "showShadowBehindNode": true, "boundVariables": {}}]
      },
      {
        "level": "md",
        "effects": [{"type": "DROP_SHADOW", "color": {"r": 0, "g": 0, "b": 0, "a": 0.1}, "offset": {"x": 0, "y": 4}, "radius": 6, "spread": -1, "visible": true, "blendMode": "NORMAL", "showShadowBehindNode": true, "boundVariables": {}}]
      }
    ]
  },

  "borders": {
    "has_borders": true,
    "default_weight": 1,
    "emphasis_weight": 2,
    "patterns": {
      "card": {"weight": 1, "color_ref": "border-default", "style": "solid"},
      "divider": {"weight": 1, "color_ref": "border-default", "style": "solid"},
      "active": {"weight": 2, "color_ref": "accent-primary", "style": "solid"}
    }
  },

  "icons": {
    "style": "Lucide | custom",
    "stroke_weight": 1.5,
    "sizes": {"nav": 22, "action": 20, "inline": 16, "small": 14},
    "color_states": {"active": "#000000", "inactive": "#C4C4C4"}
  },

  "layout": {
    "type": "sidebar_main | vertical_stack | tab_based | grid",
    "sidebar_width": 240,
    "header_height": 64,
    "screen_width": 1440,
    "screen_height": 900
  },

  "matched_style_guide": null
}
```

---

## ardot API 对齐说明

### 颜色双格式

每个颜色输出 `hex`（给人读）+ `rgba`（给 `apply_variables`，0~1 浮点，2 位小数）。转换：`r = parseInt(hex.slice(1,3), 16) / 255`。

### variables 直传 apply_variables

`variables` 字段可**原样**作为 `apply_variables` 工具参数。变量名 kebab-case（`page-bg`、`text-primary`）。

### typography.scale 对齐 batch_edit

| scale 字段 | batch_edit 属性 | 格式 |
|-----------|----------------|------|
| fontSize | fontSize | 纯数字 px |
| fontWeight | fontWeight | 数字字符串 `"300"`~`"900"` |
| fontFamily | fontName.family | 字体族名 |
| letterSpacing | letterSpacing | `{value, unit: "PIXELS"}` 或省略 |
| lineHeight | lineHeight | `{value, unit: "PIXELS"}` |
| textCase | textCase | `"UPPER"` 或省略 |

### shadows.effects 直传 batch_edit

每个 effects 条目含 ardot 全部必填字段，可直接 `U("nodeId", {effects: design_spec.shadows.system[0].effects})`。

---

## 必填字段

| 字段 | 必须 | 最低要求 |
|------|------|---------|
| style_direction + tags | 是 | 5-10 个 tags |
| colors.backgrounds | 是 | >= 2 个（page + surface） |
| colors.text | 是 | >= 2 个（primary + secondary） |
| colors.accents | 是 | >= 1 个（primary） |
| variables | 是 | >= 5 COLOR + >= 2 FLOAT |
| typography.families | 是 | >= 1 个 |
| typography.scale | 是 | >= 3 级 |
| spacing | 是 | base_unit + >= 3 patterns |
| corner_radius | 是 | system + >= 2 值 |
| shadows.has_shadows | 是 | 明确 true/false |
| layout | 是 | type + screen_width |
| borders / icons | 否 | 有时输出 |

---

## 提取方法论（9 步）

### Step 1：整体风格感知

判断平台、色调、风格、氛围、密度。从 `ALL_STYLE_GUIDE_TAGS`（约 160 个）选 5-10 个 tags，涵盖不同维度。

### Step 2：色彩系统

按功能角色扫描，输出双格式（hex + rgba）：

**backgrounds**：page（最大面积底色）、surface（卡片背景）、elevated（hover 层）、sidebar（如有）

**text**：primary（标题正文）、secondary（描述文字）、tertiary（placeholder）、disabled

**accents**：primary（CTA）、secondary（次要强调）、success、error、warning

**borders**：subtle（分割线）、default（边框）、strong（强调）

hex → rgba：`r = parseInt(hex[1:3], 16) / 255`，保留 2 位小数，a 默认 1。

### Step 3：variables 生成

kebab-case 命名（`page-bg`、`text-primary`、`accent-primary`、`spacing-base`、`radius-md`）。COLOR 用 rgba，FLOAT 用数字。与 colors 中的 rgba 值保持一致。

### Step 4：字体系统

**字族**：判断单/双/三字体，记录 `ardot_fontName: {family, style}`。

**字阶**：按大小排列，每级记录 fontSize(数字) / fontWeight(数字字符串) / fontFamily / letterSpacing({value, unit}) / lineHeight({value, unit}) / textCase(可选)。

典型层级：display(32-42) → heading_1(26-32) → heading_2(20-24) → heading_3(18) → body(15-16) → body_small(13-14) → caption(11-12) → section_label(10-11, 大写) → tab_label(9-10)

### Step 5：间距系统

识别 base_unit（4/8px）→ 提取 scale → 按角色记录 patterns（screen_width / content_padding / section_gap / card_gap / card_padding / inline_gap）。

### Step 6：圆角系统

判断 system 类型：zero / subtle(2-4) / moderate(6-8) / rounded(12-24) / pill(100+) / mixed。提取各组件具体值。

### Step 7：阴影系统

判断 has_shadows → 按强度分级，每级输出完整 effects 对象（type / color{r,g,b,a} / offset{x,y} / radius / visible:true / blendMode:"NORMAL" / showShadowBehindNode:true / boundVariables:{}）。

### Step 8：布局和图标

布局：type + 关键尺寸。图标：style(Lucide/custom) / stroke_weight / sizes / color_states。

### Step 9：输出前校验

1. 必填字段完整（对照上方必填字段表）
2. rgba 值 0~1 且 2 位小数，fontWeight 是数字字符串
3. variables 与 colors 的 rgba 一致
4. tags 全部来自 `ALL_STYLE_GUIDE_TAGS`
