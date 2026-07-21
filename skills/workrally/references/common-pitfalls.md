# 常见问题与易错点

本文档汇总 AI Agent 使用 WorkRally CLI 时最容易犯的错误和混淆点，帮助避免常见陷阱。

---

## ❌ 错误 1：混淆"项目"和"画布"

### 问题

```bash
# ❌ 错误：把项目 ID 当画布 ID 用
workrally generate image --prompt "..." --model <id> --project-id <project_list返回的ID>
```

### 正确做法

```bash
# ✅ 先获取画布 ID
workrally canvas list -o json
# 再传画布 ID
workrally generate image --prompt "..." --model <id> --project-id <canvas_list返回的canvas_id>
```

### 区分规则

| 获取方式 | 返回的是 | 传给谁 |
|----------|---------|--------|
| `workrally project list` | 项目 ID | `asset create --project-id`、`asset search --project-id` |
| `workrally canvas list` | 画布 ID | `generate image --project-id`、`generate video --project-id`、`canvas build-draft` |

---

## ❌ 错误 2：硬编码模型 ID

### 问题

```bash
# ❌ 错误：猜测或硬编码模型 ID
workrally generate image --prompt "..." --model "kontext_v2"
```

### 正确做法

```bash
# ✅ 动态获取
workrally generate image-models -o json
# 从返回结果中读取 model_id
workrally generate image --prompt "..." --model <从返回结果中获取的model_id>
```

> 模型列表是**动态下发**的，不同环境的可用模型可能完全不同。

---

## ❌ 错误 3：自行拼接前端 URL

### 问题

```bash
# ❌ 错误：自己拼接 URL（域名和路由因环境而异）
echo "https://workrally.qq.com/workrally/toolbox/canvas/abc123"
```

### 正确做法

```bash
# ✅ 使用 url build 命令
workrally url build "无限画布" --params '{"id":"abc123"}'
```

---

## ❌ 错误 4：生成后手动调用 build-draft

### 问题

```bash
# ❌ 不必要：在画布中生成图片后，又手动创建节点
workrally generate image --prompt "..." --model <id> --project-id <canvas_id> --poll
# 然后又调用 build-draft 创建节点 ← 多余操作
workrally canvas build-draft <canvas_id> --nodes '[...]'
```

### 正确理解

传入 `--project-id` 后，系统**自动**在画布创建 running 状态的占位节点。**无需手动 build-draft。**

### build-draft 的正确使用场景

- 在画布上放置**已有素材**（非 AI 生成的图片/视频/音频）
- 管理**画板布局**（创建画板、调整子节点位置）
- 添加**文本**或**涂鸦**节点
- **删除**画布上的节点
- **重新排列**已有节点

---

## ❌ 错误 5：上传素材缺少入库步骤

### 问题

```bash
# ❌ 错误：上传后直接使用 CDN URL
workrally upload ./file.png -o json
# 然后直接把 cdn_url 作为 asset_id 用 ← 这不是 asset_id！
```

### 正确做法

```bash
# ✅ 上传后必须入媒资库
workrally upload ./file.png -o json
workrally asset create --url <cdn_url> --project-id <project_id> -o json
# 现在才有 asset_id
```

> 上传只是把文件传到 CDN，**必须**调用 `asset create` 入库才能被系统使用。

---

## ❌ 错误 6：资产库挂载缺少关键字段

### 问题

```bash
# ❌ 错误：JSON 中缺少 material_id 或 material_detail
workrally material add --json-list '[{"material_name":"素材","material_type":2,"parent_id":"role_person"}]'
# 素材不会在资产库列表中显示！
```

### 正确做法

```bash
# ✅ 必须在 JSON 中传 material_id（=asset_id）和完整的 material_detail（=asset_details）
workrally material add --json-list '[{
  "material_id": "<asset_id>",
  "material_name": "素材名",
  "material_type": 2,
  "parent_id": "<parent_id>",
  "material_detail": <完整的 asset_details 对象>
}]' --project-ids <project_id>
```

---

## ❌ 错误 7：画板内放入不允许的节点类型

### 问题

```bash
# ❌ 错误：把文本节点放入画板
workrally canvas build-draft <id> --nodes '[
  {"id":"board","type":"artboard","position":{"x":0,"y":0},"data":{},"style":{"width":600,"height":800}},
  {"id":"txt","type":"text","position":{"x":20,"y":20},"data":{"text":{"content":"标题"}},"parentId":"board"}
]'
# 服务端会拒绝！
```

### 正确理解

画板只接受 `image`、`video`、`audio` 类型的子节点。

---

## ❌ 错误 8：给画板子节点设置 extent

### 问题

```json
{
  "id": "img1",
  "type": "image",
  "parentId": "board",
  "extent": "parent"
}
```

### 后果

子节点被 ReactFlow 锁定在画板内，用户无法拖出。服务端会自动清除此属性，但不要主动设置。

---

## ❌ 错误 9：混淆 material_id 和 role_id

### 问题

```bash
# ❌ 错误：用 material_id 查角色详情
workrally role get "abc_0"
# material_id 格式: "abc_0" (带后缀)
# role_id 格式: "abc" (不带后缀)
```

### 正确做法

```bash
# ✅ 先获取 role_id
workrally material get "abc_0" -o json
# 从返回结果中找到 role_id 字段
workrally role get "abc" -o json
```

---

## ❌ 错误 10：音视频 URL 使用 original_url

### 问题

```bash
# ❌ 错误：音视频使用 original_url（不含访问凭证）
# original_url 是原始 CDN 路径，音视频无法直接访问
```

### 正确做法

始终使用 `url` 或 `download_url`，这些是可直接访问的临时 URL。过期后通过 `asset get` 重新获取即可，返回的新 URL 可直接作为其他工具的 URL 参数传入。

---

## 常见判断速查表

| 场景 | 需要什么 |
|------|---------|
| "上传一张图片" | `upload` → `asset create` (2步) |
| "上传到人物角色" | `upload` → `asset create` → `material add` (3步) |
| "在画布上生成图片" | `generate image --project-id <画布ID> --poll` (1步) |
| "把已有图片放到画布上" | `asset search` → `canvas build-draft` |
| "生成4张图片" | `generate image --count 4 --poll` |
| "查看生成进度" | `generate task <task_id> --poll` |
| "创建一个画板放三张图" | `canvas build-draft` (一次传画板+3个子节点) |
| "删除画布上的某个节点" | `canvas build-draft --delete-node-ids "node_id"` |
| "清空整个画布" | `canvas build-draft --nodes '[]' --mode overwrite` |
| "查看角色的 LoRA 版本" | `material get` → `role get` |
| "搜索项目中的视频素材" | `asset search --project-id <id>` |

---

## 通用工具透传

当高级封装命令无法满足需求时，使用通用透传直接调用任何 MCP 工具：

```bash
# 列出所有可用工具
workrally tools list -o json

# 查看某个工具的参数 schema
workrally tools describe <tool_name>

# 直接调用（适合复杂参数场景）
workrally tools call <tool_name> --json-args '{"key":"value"}'
```

---

## 输出格式建议

| 格式 | 用途 | 命令 |
|------|------|------|
| `json` | **Agent 推荐** — 结构化数据便于解析 | `-o json` |
| `table` | 人类阅读 — 表格格式 | `-o table` |
| `text` | 管道/脚本 — 纯文本 | `-o text` |

设置全局默认格式：
```bash
workrally config set output_format json
```
