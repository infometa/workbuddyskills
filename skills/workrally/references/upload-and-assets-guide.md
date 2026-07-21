# 上传与素材管理指南

本文档帮助 AI Agent 正确执行文件上传和素材管理流程。WorkRally 有两套素材体系，理解它们的关系是正确操作的前提。

---

## 1. 两套素材体系

### 媒资库 (Asset) — 项目级文件池

- **管理命令**: `workrally asset search/create/get/update`
- **本质**: 扁平的文件列表，每个素材必须归属一个项目
- **特点**: 视频/音频为**私有读存储**，必须入库后才能正常访问
- **何时使用**: 所有素材都**必须**经过媒资库（`asset create`）才能被系统使用

### 资产库 (Material) — 树形目录管理

- **管理命令**: `workrally material list/add/update/get/breadcrumb`
- **本质**: 树形文件夹结构，对媒资库素材的**组织视图**
- **三个预设根目录**: `role_person`(人物)、`role_prop`(道具)、`role_scene`(场景)
- **附加根目录**: `root`(用户自建网盘文件夹)
- **何时使用**: 仅当用户要将素材"归档到角色/道具/场景/文件夹"时才需要

### 数据层次关系

```
资产 (material_type=0)
 └─ 角色状态 (material_type=5)
     ├─ 图片素材 (material_type=2)
     ├─ 视频素材 (material_type=3)
     └─ 音频素材 (material_type=4)
```

---

## 2. 三步上传流程

这是 WorkRally 最核心的文件处理流程，**严格按顺序执行**：

### 步骤 1: 上传文件到 CDN

```bash
workrally upload ./character.png -o json
```

返回：
```json
{
  "url": "https://cdn.example.com/path/to/file.png",
  "original_url": "https://cdn.example.com/path/to/file.png",
  "signed_url": "https://cdn.example.com/path/to/file.mp4?sign=..."
}
```

**URL 字段说明**：
- `url` — 可直接访问的地址。图片为公开 URL；音视频为临时访问 URL
- `original_url` — 原始 CDN 路径（不含访问凭证），图片可直接访问，音视频无法直接访问
- `signed_url` — 仅音视频返回，与 `url` 相同

> ⚠️ 音视频文件为私有读存储，**必须使用 `url` 或 `signed_url`**，不要使用 `original_url`。

### 步骤 2: 入媒资库（必须！）

> 🔒 `--url` 仅接受 WorkRally 官方媒资 URL（即 `upload` 返回值或媒资库 URL），详见 SKILL.md 规则 9。

```bash
workrally asset create --url <cdn_url> --project-id <project_id> -o json
```

返回：
```json
{
  "id": "asset_abc123",
  "asset_details": {
    "url": "https://signed.url/...",
    "download_url": "https://signed.download.url/...",
    "width": 1024,
    "height": 1024,
    "format": "png"
  }
}
```

**重要返回值**：
- `id` — 即 `asset_id`，后续所有操作都需要这个 ID
- `asset_details` — 完整素材元数据，**步骤 3 必须完整传入**

> ⚠️ `asset_details.url` 和 `asset_details.download_url` 为临时访问 URL，过期后需通过 `workrally asset get` 重新获取。获取到的 URL 可直接作为其他工具的 URL 参数传入。

### 步骤 3: 挂载到资产库（按需）

```bash
workrally material add --json-list '[{
  "material_id": "<asset_id>",
  "material_name": "角色名_状态",
  "material_type": 2,
  "parent_id": "<目标位置的 material_id>",
  "material_detail": <完整的 asset_details 对象>
}]' --project-ids <project_id>
```

**关键字段**（JSON 数组中每个对象）：
- `material_id` — **必须**传 `asset_id`（步骤 2 返回的 `id`）
- `material_detail` — **必须**传完整的 `asset_details`（步骤 2 返回的 `asset_details` 对象）
- `material_type` — 素材类型：`2`=图片，`3`=视频，`4`=音频，`1`=文件夹
- `parent_id` — 目标位置：`role_person`/`role_prop`/`role_scene` 或已有文件夹/状态的 `material_id`

> ⚠️ 步骤 3 如果 JSON 中缺少 `material_id` 或 `material_detail`，素材不会在资产库列表中显示！

---

## 3. 判断需要几步

| 用户意图 | 所需步骤 | 说明 |
|----------|---------|------|
| "上传文件" / "上传图片" | 步骤 1 → 2 | 入媒资库即可在 web 端查看 |
| "上传到角色/道具/场景" | 步骤 1 → 2 → 3 | 还需挂载到资产库树形目录 |
| "上传到文件夹" | 步骤 1 → 2 → 3 | 同上，parent_id 为文件夹的 material_id |
| "把媒资素材添加到资产库" | 仅步骤 3 | 素材已在媒资库，只需挂载 |
| "在画布上放一张已有图" | 无需上传 | 直接 `asset search` 找到 asset_id → `canvas build-draft` |
| "上传并放到画布上" | 步骤 1 → 2 → `build-draft` | 入媒资库后用 build-draft 写入画布 |

---

## 4. 画布场景下的素材上传

画布素材需要**同时关联项目和画布**：

```bash
# 步骤 1: 上传
workrally upload ./file.png -o json

# 步骤 2: 入媒资库（必须传 project-id）
workrally asset create --url <cdn_url> --project-id <项目ID> -o json

# 步骤 3: 写入画布节点（使用返回的 asset_id）
workrally canvas build-draft <画布ID> --nodes '[
  {"id":"node1","type":"image","position":{"x":0,"y":0},"data":{"asset":{"id":"<asset_id>"}},"style":{"width":512,"height":512}}
]'
```

> 📌 项目 ID 通过 `workrally project list` 获取。用户未指定项目时，查找名为"默认项目"的项目。

---

## 5. 资产库目录操作

### 查看各根目录下的内容

```bash
# 查看人物列表
workrally material list role_person -o json
# 查看道具列表
workrally material list role_prop -o json
# 查看场景列表
workrally material list role_scene -o json
# 查看网盘文件夹列表
workrally material list root -o json
```

### 查看角色的状态列表

```bash
# parent-id 传角色的 material_id
workrally material list <角色的material_id> -o json
```

### 查看某状态下的素材文件

```bash
# parent-id 传状态的 material_id
workrally material list <状态的material_id> -o json
```

### 创建文件夹

```bash
workrally material add --json-list '[{"material_name":"新文件夹","material_type":1,"parent_id":"role_person"}]'
```

### 获取角色详情（含 LoRA/提示词）

```bash
# 注意：role get 需要 role_id，不是 material_id
# material_id 格式如 "abc_0"，role_id 格式如 "abc"
# 先通过 material get 获取 role_id
workrally material get <material_id> -o json
# 返回中有 role_id 字段，再查角色详情
workrally role get <role_id> -o json
```

> ⚠️ `material_id`（如 "abc_0"，带 `_0` 后缀）≠ `role_id`（如 "abc"）。如果只有 `material_id`，先通过 `material get` 获取 `role_id`。

---

## 6. 素材 URL 访问说明

| 素材类型 | 存储策略 | URL 行为 |
|----------|---------|---------|
| 图片 | **公开读** | `url` 可直接访问 |
| 视频 | **私有读** | `url` 为临时访问地址，过期后需重新获取 |
| 音频 | **私有读** | `url` 为临时访问地址，过期后需重新获取 |

> 📎 媒资 API 返回的素材 URL 可直接作为其他工具的 URL 参数传入，**无需手动处理**。如遇"非法或已过期"提示，通过下列命令重新获取即可。

过期后重新获取：
```bash
workrally asset get <asset_id> -o json
# 返回中的 url 和 download_url 为新的可访问地址
```

---

## 7. 批量操作

### 批量创建素材到资产库

`material add` 支持 `--json-list` 参数传入 JSON 数组，一次添加多个素材。也可通过 `tools call` 直接调用底层 MCP 工具：

```bash
workrally tools call material_manage --json-args '{
  "action": "add",
  "material_list": [
    {"material_id":"asset_id_1","material_name":"素材1","material_type":2,"parent_id":"<状态ID>","material_detail":{...}},
    {"material_id":"asset_id_2","material_name":"素材2","material_type":3,"parent_id":"<状态ID>","material_detail":{...}}
  ],
  "project_ids": ["<project_id>"],
  "source": 1
}'
```

### 批量获取素材详情

```bash
workrally asset get <id1> <id2> <id3> -o json
# 最多 50 个 ID
```

### 搜索媒资库

```bash
workrally asset search --project-id <id> -o json
# 可选筛选: --keyword "关键词" --type image/video/audio
```
