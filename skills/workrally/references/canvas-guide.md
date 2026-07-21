# 无限画布操作指南

本文档帮助 AI Agent 正确操作 WorkRally 无限画布（Infinite Canvas）。画布基于 Yjs 协同编辑引擎，CLI 写入的内容会**实时同步**给所有在线用户，无需刷新页面。

---

## 1. 核心概念

### 两种"项目"（容易混淆，务必区分）

| 概念 | 管理命令 | 用途 | 必要性 |
|------|---------|------|--------|
| **项目** (project) | `workrally project list/create/get` | 所有素材都必须归属一个项目，范围更大 | **必须** — 素材不关联项目则在 web 端不可见 |
| **画布** (canvas) | `workrally canvas list/create/get` | 无限画布空间，可在其中排布节点 | **可选** — 仅当用户要在画布中操作时才需要 |

> ⚠️ **两者的 ID 不能互相替代！**
> - `workrally project list` 返回的是项目 ID
> - `workrally canvas list` 返回的是画布 ID
> - 在画布场景下，素材需要**同时关联两者**

### 判断用户意图

| 用户说 | 含义 | 使用命令 |
|--------|------|---------|
| "我的项目"、"项目列表" | 项目 | `workrally project list` |
| "我的画布"、"画布列表" | 无限画布 | `workrally canvas list` |
| "在画布上生成图片" | 画布 + AI 生成 | `workrally generate image --project-id <画布ID>` |
| "上传到项目" | 仅入媒资库 | `upload` → `asset create` |
| "在画布上展示素材" | 需要 build-draft | `upload` → `asset create` → `canvas build-draft` |

---

## 2. 画布节点类型 (8 种)

### 类型一览

| type | 说明 | 必填 data 字段 | 可放入画板 |
|------|------|---------------|-----------|
| `image` | 图片素材 | `data.asset.id` (已有素材) 或 `data.task` (生成中占位) | ✅ |
| `video` | 视频素材 | `data.asset.id` 或 `data.task` | ✅ |
| `audio` | 音频素材 | `data.asset.id` (**必须**，音频无生成器) | ✅ |
| `imageGenerator` | 图片生成器 | 无必填（params 可选） | ❌ |
| `videoGenerator` | 视频生成器 | 无必填（params 可选） | ❌ |
| `artboard` | 画板容器 | 无（建议设置 `style.width/height`） | ❌ (画板不可嵌套) |
| `text` | 文本 | `data.text.content` (字符串，最大2000字符) | ❌ |
| `freehand` | 画笔涂鸦 | `data.freehand.points` + `data.freehand.initialSize` | ❌ |

### 节点通用结构

```json
{
  "id": "node_unique_id",
  "type": "image",
  "position": { "x": 100, "y": 200 },
  "data": { },
  "style": { "width": 512, "height": 512 },
  "parentId": "artboard_id",
  "measured": { "width": 512, "height": 512 }
}
```

**字段说明**：
- `id` — 节点唯一标识，可使用任意唯一字符串
- `position` — 节点左上角坐标（缺失时堆叠在原点 0,0）
- `style` — 节点显示尺寸
- `parentId` — 仅画板内子节点需要，指向父画板的 id
- `measured` — 渲染尺寸，可选，缺失时服务端自动补全

---

## 3. 各节点类型详细说明

### 3.1 图片/视频节点 (image / video)

两种来源：
1. **已有素材** — 必须有 `data.asset.id`
2. **生成中占位** — 必须有 `data.task`（由 AI 生成命令自动创建，通常不需要手动构造）

```json
{
  "id": "img_001",
  "type": "image",
  "position": { "x": 0, "y": 0 },
  "data": {
    "asset": { "id": "asset_abc123" }
  },
  "style": { "width": 512, "height": 512 }
}
```

**带生成任务标记的节点**（用于"再次编辑"功能）：
```json
{
  "id": "gen_img_001",
  "type": "image",
  "position": { "x": 0, "y": 0 },
  "data": {
    "asset": { "id": "asset_abc123" },
    "task": { "taskId": "task_xyz789", "status": "success" }
  },
  "style": { "width": 512, "height": 512 }
}
```

> 💡 `data.task` 字段决定前端是否显示"再次编辑"按钮。AI 生成的图片/视频应包含此字段。

### 3.2 音频节点 (audio)

音频**没有生成器**，不支持 task 占位，必须有 `data.asset.id`。

```json
{
  "id": "audio_001",
  "type": "audio",
  "position": { "x": 0, "y": 0 },
  "data": {
    "asset": { "id": "asset_audio_456" }
  },
  "style": { "width": 260, "height": 80 }
}
```

> 建议尺寸 **260×80**（与前端默认一致）。

### 3.3 画板节点 (artboard)

画板是**容器**，子节点通过 `parentId` 关联到画板。

```json
{
  "id": "board_001",
  "type": "artboard",
  "position": { "x": 0, "y": 0 },
  "data": {},
  "style": { "width": 600, "height": 800 }
}
```

**画板子节点示例** — 在画板内放置一张图片：
```json
{
  "id": "img_in_board",
  "type": "image",
  "position": { "x": 20, "y": 20 },
  "data": { "asset": { "id": "asset_abc123" } },
  "style": { "width": 256, "height": 256 },
  "parentId": "board_001"
}
```

**画板规则**：
- ✅ `image`、`video`、`audio` 可以放入画板
- ❌ `imageGenerator`、`videoGenerator`、`text`、`freehand` 不可放入画板
- ❌ 画板不可嵌套（画板内不能放画板）
- ❌ **不要设置 `extent: "parent"`**，否则子节点会被锁定在画板内无法拖出
- 画板缺少尺寸时自动补全为 **600×800**

### 3.4 文本节点 (text)

```json
{
  "id": "text_001",
  "type": "text",
  "position": { "x": 0, "y": 0 },
  "data": {
    "text": {
      "content": "这是一段文本",
      "fontSize": 24,
      "fontWeight": 400,
      "textAlign": "left",
      "color": "#ffffff"
    }
  },
  "style": { "width": 200 }
}
```

**必填**: `data.text.content`（字符串，最大2000字符）
**可选**（有默认值）: `fontSize`(24), `fontWeight`(400, 加粗用700), `textAlign`("left"), `color`("#ffffff")
建议设置 `style.width`（默认200）。

### 3.5 画笔涂鸦节点 (freehand)

```json
{
  "id": "freehand_001",
  "type": "freehand",
  "position": { "x": 0, "y": 0 },
  "data": {
    "freehand": {
      "points": [[10, 20, 0.5], [30, 40, 0.7], [50, 60, 0.5]],
      "initialSize": { "width": 200, "height": 200 },
      "color": "rgba(242,72,34,1)",
      "size": 7
    }
  }
}
```

**必填**: `data.freehand.points`（二维数组，每个点为 `[x, y, pressure]`）、`data.freehand.initialSize`（`{width, height}`）
**可选**: `color`（默认红色 `rgba(242,72,34,1)`）、`size`（画笔粗细 1-100，默认7）
`pressure` 值范围 0-1，超出自动截断。

### 3.6 生成器节点 (imageGenerator / videoGenerator)

> ⚠️ **通常不需要手动创建！** `workrally generate image/video --project-id <画布ID>` 会**自动**在画布中创建 running 状态的占位节点。

仅在极特殊场景（如手动构建已完成的生成器节点）才需要：

```json
{
  "id": "gen_001",
  "type": "imageGenerator",
  "position": { "x": 0, "y": 0 },
  "data": {
    "task": { "taskId": "task_abc", "status": "success" },
    "params": {}
  },
  "style": { "width": 512, "height": 512 }
}
```

---

## 4. build-draft 操作模式

### 4.1 增量合并（默认模式）

```bash
workrally canvas build-draft <canvas_id> --nodes '[...]'
```

规则：
- **同 id → 覆盖更新**：传入的节点 id 与已有节点相同时，用新数据替换旧数据
- **新 id → 追加**：已有画布中不存在的 id 会被添加
- **未提及 → 保留**：已有节点不在传入列表中的，原样保留

### 4.2 删除节点

```bash
workrally canvas build-draft <canvas_id> --delete-node-ids "id1,id2"
```

可与 `--nodes` 同时使用（先删除，再合并新节点）：

```bash
workrally canvas build-draft <canvas_id> --nodes '[...]' --delete-node-ids "old1,old2"
```

### 4.3 全量覆盖

```bash
workrally canvas build-draft <canvas_id> --nodes '[...]' --mode overwrite
```

**清空画布**后仅保留传入的节点。传 `--nodes '[]' --mode overwrite` 可清空整个画布。

> ⚠️ 全量覆盖会删除所有已有节点，包括其他用户的内容。在多人协作场景下应优先使用增量合并。

### 4.4 从文件加载节点

```bash
workrally canvas build-draft <canvas_id> --file nodes.json
```

适合节点数据量大或结构复杂的场景。

---

## 5. 常见工作流示例

### 场景 A：在画布上排列已有素材

```bash
# 1. 搜索项目中的素材
workrally asset search --project-id <project_id> -o json

# 2. 从搜索结果中获取 asset_id，构建节点写入画布
workrally canvas build-draft <canvas_id> --nodes '[
  {"id":"n1","type":"image","position":{"x":0,"y":0},"data":{"asset":{"id":"<asset_id_1>"}},"style":{"width":512,"height":512}},
  {"id":"n2","type":"image","position":{"x":600,"y":0},"data":{"asset":{"id":"<asset_id_2>"}},"style":{"width":512,"height":512}}
]'
```

### 场景 B：创建画板并放入多张图片

```bash
workrally canvas build-draft <canvas_id> --nodes '[
  {"id":"board","type":"artboard","position":{"x":0,"y":0},"data":{},"style":{"width":800,"height":600}},
  {"id":"img1","type":"image","position":{"x":20,"y":20},"data":{"asset":{"id":"<id1>"}},"style":{"width":350,"height":250},"parentId":"board"},
  {"id":"img2","type":"image","position":{"x":420,"y":20},"data":{"asset":{"id":"<id2>"}},"style":{"width":350,"height":250},"parentId":"board"}
]'
```

### 场景 C：更新画布中某个节点的位置

```bash
# 只传需要修改的节点，其他节点自动保留
workrally canvas build-draft <canvas_id> --nodes '[
  {"id":"existing_node_id","type":"image","position":{"x":300,"y":400},"data":{"asset":{"id":"<asset_id>"}},"style":{"width":512,"height":512}}
]'
```

### 场景 D：删除部分节点并添加新节点

```bash
workrally canvas build-draft <canvas_id> \
  --nodes '[{"id":"new1","type":"text","position":{"x":0,"y":0},"data":{"text":{"content":"新标题","fontSize":48,"fontWeight":700,"color":"#00ff00"}},"style":{"width":400}}]' \
  --delete-node-ids "old_node_1,old_node_2"
```

---

## 6. 服务端自动修正

服务端会对传入的节点进行以下自动修正（不需要 Agent 操心）：

| 场景 | 自动行为 |
|------|---------|
| 画板缺少 style | 补全 600×800 |
| 文本节点缺少样式属性 | 补全 fontSize=24, fontWeight=400, textAlign=left, color=#ffffff |
| 文本节点缺少 style.width | 补全 200 |
| 文本内容为空 | 填充"在此输入文本" |
| 画笔节点缺少颜色/大小 | 补全 color=rgba(242,72,34,1), size=7 |
| 画笔 size 超出范围 | 截断到 1-100 |
| 画笔 pressure 超出范围 | 截断到 0-1 |
| 子节点设置了 extent | 自动清除（防止锁定） |

**但以下关键字段缺失会被拒绝**：

| 场景 | 错误 |
|------|------|
| image/video 既没有 asset.id 也没有 task | ❌ 空节点 |
| audio 没有 asset.id | ❌ 音频无生成器 |
| text 没有 data.text.content 或类型非字符串 | ❌ |
| text 内容超过 2000 字符 | ❌ |
| freehand 缺少 points 或 initialSize | ❌ |
| 不允许的节点类型（如 group） | ❌ |
| 画板子节点类型不是 image/video/audio | ❌ |
