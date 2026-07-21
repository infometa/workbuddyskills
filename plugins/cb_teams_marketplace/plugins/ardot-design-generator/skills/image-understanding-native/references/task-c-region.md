# 任务 C：区域语义描述

`analysis_type: "region_description"`

当用户指出截图的某个区域，输出区域内容、元素列表、功能推断、设计属性。

## Schema

```json
{
  "analysis_type": "region_description",
  "region_reference": "用户描述的区域",
  "region": {
    "summary": "区域功能和内容概述",
    "content_type": "navigation | form | data_display | media | action_bar | settings | card | list_item | modal | mixed",
    "bbox": {"x": 0, "y": 0, "width": 100, "height": 7.1},
    "text_content": ["区域内所有可读文字"],
    "elements": [
      {
        "type": "元素类型",
        "label": "内容",
        "bbox": {"x": 0, "y": 0, "width": 0, "height": 0},
        "width": "设计宽度",
        "height": "设计高度",
        "interactive": true,
        "visual_traits": "视觉特征"
      }
    ],
    "function_inference": {
      "purpose": "功能用途",
      "user_actions": ["用户可执行的操作"],
      "navigation_role": "global | local | contextual | none"
    },
    "design_traits": {
      "background": "#FFFFFF",
      "foreground_color": "#111827",
      "has_border": true,
      "border_detail": "底部 1px #E5E7EB",
      "has_shadow": false,
      "width": "fill",
      "height": "64px",
      "layout_direction": "horizontal | vertical",
      "alignment": "left | center | right | space_between",
      "padding": "0 24px",
      "gap": "16px"
    }
  }
}
```

## 分析方法论

1. **定位区域**：根据用户描述确定目标
2. **内容分析**：区域 bbox、文字列表、元素清点（类型/数量/bbox）
3. **功能推断**：用途、可执行操作、导航角色
4. **设计属性**：背景色、边框/阴影、尺寸（bbox% × viewport → px）、padding/gap

用户描述不精确时说明理解范围后继续。
