# Excalidraw JSON Structure

## Minimal file shape

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#FFFFFF",
    "gridSize": 20
  },
  "files": {}
}
```

## Required top-level fields

| Field | Type | Notes |
|---|---|---|
| `type` | string | 固定为 `excalidraw` |
| `version` | number | 目前常用 `2` |
| `source` | string | 通常为 `https://excalidraw.com` |
| `elements` | array | 所有图形元素 |
| `appState` | object | 画布背景、网格等状态 |
| `files` | object | 嵌入文件资源，没有就用空对象 |

## Common element fields

多数元素都会包含这些字段：

- `id`
- `type`
- `x`, `y`, `width`, `height`
- `strokeColor`, `backgroundColor`
- `strokeWidth`, `strokeStyle`, `fillStyle`
- `roughness`, `opacity`, `angle`
- `seed`, `version`, `versionNonce`
- `isDeleted`, `updated`, `locked`

## Text-specific fields

文本元素额外常见：

- `text`
- `originalText`
- `fontSize`
- `fontFamily`
- `textAlign`
- `verticalAlign`
- `lineHeight`
- `containerId`

建议默认：

- `fontFamily: 3`
- `roughness: 0`
- `opacity: 100`

## Arrow-specific fields

箭头元素额外常见：

- `points`
- `startBinding`
- `endBinding`
- `startArrowhead`
- `endArrowhead`

如果是复杂转向箭头，给 `points` 增加中间折点，不要硬穿内容区。

## Good defaults

```json
{
  "appState": {
    "viewBackgroundColor": "#FFFFFF",
    "gridSize": 20
  }
}
```

## Validation checklist

生成后至少确认：

1. `type` 是否正确
2. `elements` 是否非空
3. 所有 `id` 是否唯一
4. 箭头引用的绑定对象是否真实存在
5. `text` 字段里只有可读文本，不要塞无关结构
