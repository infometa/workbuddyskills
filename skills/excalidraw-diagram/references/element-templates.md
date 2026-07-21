# Excalidraw Element Templates

以下模板用于快速拼装常见元素。颜色请从 `color-palette.md` 中替换，不要直接照抄所有示例值。

## 1. Free-floating text

```json
{
  "id": "title_text",
  "type": "text",
  "x": 120,
  "y": 80,
  "width": 280,
  "height": 32,
  "text": "Streaming Protocol",
  "fontSize": 24,
  "fontFamily": 3,
  "textAlign": "left",
  "verticalAlign": "middle",
  "strokeColor": "#111827",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 1001,
  "version": 1,
  "versionNonce": 2001,
  "isDeleted": false,
  "boundElements": null,
  "updated": 0,
  "link": null,
  "locked": false,
  "containerId": null,
  "originalText": "Streaming Protocol",
  "lineHeight": 1.25
}
```

## 2. Rectangle node

```json
{
  "id": "process_rect",
  "type": "rectangle",
  "x": 360,
  "y": 180,
  "width": 220,
  "height": 96,
  "strokeColor": "#334155",
  "backgroundColor": "#F8FAFC",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 1002,
  "version": 1,
  "versionNonce": 2002,
  "isDeleted": false,
  "boundElements": [],
  "updated": 0,
  "link": null,
  "locked": false
}
```

## 3. Ellipse node

```json
{
  "id": "input_ellipse",
  "type": "ellipse",
  "x": 80,
  "y": 190,
  "width": 140,
  "height": 80,
  "strokeColor": "#027A48",
  "backgroundColor": "#ECFDF3",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 1003,
  "version": 1,
  "versionNonce": 2003,
  "isDeleted": false,
  "boundElements": [],
  "updated": 0,
  "link": null,
  "locked": false
}
```

## 4. Diamond decision

```json
{
  "id": "decision_diamond",
  "type": "diamond",
  "x": 660,
  "y": 176,
  "width": 160,
  "height": 100,
  "strokeColor": "#C4320A",
  "backgroundColor": "#FFF7ED",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 1004,
  "version": 1,
  "versionNonce": 2004,
  "isDeleted": false,
  "boundElements": [],
  "updated": 0,
  "link": null,
  "locked": false
}
```

## 5. Arrow connection

```json
{
  "id": "flow_arrow",
  "type": "arrow",
  "x": 220,
  "y": 230,
  "width": 140,
  "height": 0,
  "strokeColor": "#475467",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 1005,
  "version": 1,
  "versionNonce": 2005,
  "isDeleted": false,
  "boundElements": null,
  "updated": 0,
  "link": null,
  "locked": false,
  "points": [[0, 0], [140, 0]],
  "startBinding": null,
  "endBinding": null,
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

## 6. Evidence block

适合真实 JSON、方法名、代码片段。

```json
[
  {
    "id": "evidence_box",
    "type": "rectangle",
    "x": 120,
    "y": 360,
    "width": 360,
    "height": 180,
    "strokeColor": "#344054",
    "backgroundColor": "#101828",
    "fillStyle": "solid",
    "strokeWidth": 1,
    "strokeStyle": "solid",
    "roughness": 0,
    "opacity": 100,
    "angle": 0,
    "seed": 1006,
    "version": 1,
    "versionNonce": 2006,
    "isDeleted": false,
    "boundElements": [],
    "updated": 0,
    "link": null,
    "locked": false
  },
  {
    "id": "evidence_text",
    "type": "text",
    "x": 144,
    "y": 388,
    "width": 300,
    "height": 96,
    "text": "POST /events\\n{\\n  \"type\": \"STATE_DELTA\"\\n}",
    "fontSize": 16,
    "fontFamily": 3,
    "textAlign": "left",
    "verticalAlign": "top",
    "strokeColor": "#F8FAFC",
    "backgroundColor": "transparent",
    "fillStyle": "solid",
    "strokeWidth": 1,
    "roughness": 0,
    "opacity": 100,
    "angle": 0,
    "seed": 1007,
    "version": 1,
    "versionNonce": 2007,
    "isDeleted": false,
    "boundElements": null,
    "updated": 0,
    "link": null,
    "locked": false,
    "containerId": null,
    "originalText": "POST /events\\n{\\n  \"type\": \"STATE_DELTA\"\\n}",
    "lineHeight": 1.25
  }
]
```

## Practical notes

- 大图用可读 ID，例如 `agent_box`、`ui_arrow`、`json_payload_text`。
- 同类节点用一致尺寸，跨层级节点用明显尺寸差。
- 如果是时间线或树形结构，优先用 `line + text`，不要全部包成卡片。
