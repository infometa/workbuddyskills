# 分类规则配置 (rules.json)

规则文件驱动 `organize_canvas.py` 的分类逻辑。完整结构如下：

```json
{
  "groups": [ /* 画板定义数组，顺序决定从左到右 */ ],
  "layout": { /* 全局布局参数，可省略用默认值 */ }
}
```

## `groups[*]` 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | 画板唯一 ID，将作为 `parentId` 关联子节点（如 `board_roles`） |
| `title` | ✅ | 画板上方显示的文字（支持 emoji） |
| `cols` | ⭕ | 网格列数（默认 5，建议 3 ~ 7） |
| `match` | ✅ | 匹配规则对象，见下 |
| `title_size` | ⭕ | 标题字号，默认 40 |
| `title_weight` | ⭕ | 标题字重，默认 700 |
| `title_color` | ⭕ | 标题颜色，默认 `#ffffff` |

## `match.type` 的 6 种模式

### 1. `asset_type` — 按素材类型

```json
{ "type": "asset_type", "value": "video" }
```
用于把所有视频（或音频）归到一个画板。`value` 可选 `image` / `video` / `audio`。

### 2. `title_prefix` — 按标题前缀

```json
{ "type": "title_prefix", "prefix": "迪金斯" }
```

或支持多个前缀：

```json
{ "type": "title_prefix", "prefix": ["迪金斯", "Deakins"] }
```

### 3. `title_keywords` — 按标题关键词（包含即可）

```json
{ "type": "title_keywords", "keywords": ["韩团风", "清凉造型", "角色"] }
```

### 4. `title_regex` — 按标题正则

```json
{ "type": "title_regex", "regex": "^[0-9a-f]{32}\\.(jpg|png)$" }
```
常用于识别 hash 命名的散图。

### 5. `fallback` — 兜底组

```json
{ "type": "fallback" }
```
⚠️ **必须放在 `groups` 数组的最后**，未被前面规则匹配上的素材会进这里。

### 6. `and` / `or` — 组合条件

```json
{
  "type": "and",
  "conditions": [
    { "type": "asset_type", "value": "image" },
    { "type": "title_prefix", "prefix": "太空电梯" }
  ]
}
```

```json
{
  "type": "or",
  "conditions": [
    { "type": "title_keywords", "keywords": ["角色", "人物"] },
    { "type": "title_prefix", "prefix": "char_" }
  ]
}
```

## `layout` 参数

| 字段 | 默认 | 说明 |
|---|---|---|
| `cell_w` | 280 | 每格宽度（px） |
| `cell_h` | 280 | 每格高度（px） |
| `gap` | 20 | 单元格之间间距 |
| `pad` | 40 | 画板内边距（上/下/左/右） |
| `title_h` | 60 | 画板内顶部预留给标题的高度（空白，非真实文字） |
| `board_gap` | 200 | 画板之间横向间距 |

> 说明：画板标题不是放在画板**内**，而是独立 `text` 节点，置于画板**外部上方 80px** 处。`title_h` 是为了让子节点在画板顶部留白，视觉上对齐标题。

## 匹配优先级

`groups` 数组按顺序遍历，**每个 asset 只会归入第一个匹配的组**。因此更具体的规则应放在前面，`fallback` 放最后。

## 常用模板

### 模板 A：人物 / 风格 / 视频 / 散图（4 板）

```json
{
  "groups": [
    {
      "id": "board_roles", "title": "🎭 人物资产", "cols": 4,
      "match": { "type": "title_keywords", "keywords": ["韩团风", "清凉造型"] }
    },
    {
      "id": "board_style", "title": "🎬 风格参考", "cols": 5,
      "match": { "type": "title_prefix", "prefix": "迪金斯" }
    },
    {
      "id": "board_videos", "title": "🎥 视频库", "cols": 3,
      "match": { "type": "asset_type", "value": "video" }
    },
    {
      "id": "board_misc", "title": "📦 杂项", "cols": 6,
      "match": { "type": "fallback" }
    }
  ]
}
```

### 模板 B：只按素材类型 3 分（图/视/音）

```json
{
  "groups": [
    { "id": "board_images", "title": "🖼️ 图片", "cols": 7,
      "match": { "type": "asset_type", "value": "image" } },
    { "id": "board_videos", "title": "🎥 视频", "cols": 3,
      "match": { "type": "asset_type", "value": "video" } },
    { "id": "board_audio", "title": "🎵 音频", "cols": 4,
      "match": { "type": "asset_type", "value": "audio" } }
  ]
}
```
