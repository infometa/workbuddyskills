---
name: workrally
description: WorkRally CLI (workrally) — 面向 AI Agent 的 AIGC 漫剧视频创作全流程工具集。 支持 AI 生图、AI 生视频、项目管理、资产库、媒资管理、无限画布、文件上传下载等。 Use when user asks to generate images, generate videos, manage projects, upload files, download assets, manage materials, or interact with WorkRally platform via command line.
description_zh: WorkRally AI 内容创作（生图、生视频、画布、素材管理）
description_en: "WorkRally AI content creation: image/video generation, canvas, asset management"
version: 2.4.0
homepage: "https://workrally.qq.com"
metadata: "{"openclaw":{"emoji":"🎬","requires":{"bins":["workrally"],"env":["WORKRALLY_API_KEY","WORKRALLY_ENDPOINT","WORKRALLY_CONFIG_DIR","WORKRALLY_NO_UPDATE_CHECK"]},"primaryEnv":"WORKRALLY_API_KEY","credentials":{"storage":"~/.workrally/config.json","configDirEnv":"WORKRALLY_CONFIG_DIR","description":"workrally auth login 写入的 API Key 持久化文件，JSON 格式，仅存储 api_key 和 endpoint。非持久化容器中可通过 WORKRALLY_CONFIG_DIR 环境变量指定配置目录"},"install":[{"id":"npm","kind":"node","package":"workrally","bins":["workrally"],"label":"Install WorkRally CLI (npm)"}],"category":"AIGC","tags":["workrally","aigc","cli","video-generation","image-generation","ai-tools","story","shot","series"]}}"
license: MIT-0
author: WorkRally Team
user-invocable: true
---

# WorkRally CLI (workrally)

面向 AI Agent 的 AIGC 漫剧视频创作全流程命令行工具，封装 WorkRally 平台 30+ 核心能力，支持项目/剧集/场次的完整 CRUD、AI 生图/生视频、画布、资产库、媒资管理、文件上传等。

## 安装 & 配置

```bash
npm install -g workrally

# 配置 API Key（三选一）
workrally auth login                          # 交互式登录（推荐）
workrally auth login --token <YOUR_API_KEY>   # 命令行传入
export WORKRALLY_API_KEY=<YOUR_API_KEY>       # 环境变量（仅推荐 CI/CD，Agent/子进程可能读不到 shell 配置）
# ↑ auth login 自动将 Token 写入配置文件：
#   若 WORKRALLY_CONFIG_DIR 已设置 → $WORKRALLY_CONFIG_DIR/config.json
#   否则 → ~/.workrally/config.json

workrally auth status                         # 验证登录状态
```

API Key 申请：[龙虾配置](https://workrally.qq.com/open-api)

## 命令速查

```bash
# === 项目（project）— list / get / create / update（软删除无子命令，见下） ===
workrally project list [--search "关键词"]    # 列出/搜索项目
workrally project get <id>                    # 项目详情
workrally project create "项目名"             # 创建项目
workrally project update <id> --name "新名称" # 更新项目
workrally tools call project_delete --json-args '{"project_id":"<id>"}'   # 软删除单个项目（→回收站）
# 批量：workrally tools describe project_delete  # 使用 project_ids 数组

# === 剧集（series）— 全新命令组（CRUD 完整） ===
workrally series list --project-id <id>                                 # 剧集列表
workrally series get <series_id> --project-id <id>                      # 剧集详情
workrally series create --project-id <id> --name "第一集"                # 创建剧集
workrally series update <series_id> --project-id <id> --name "新名称"    # 更新剧集
workrally series delete <ids...>                                        # 软删除（→回收站）

# === 场次（shot/story）— 短番制作核心单元 ===
# --- CRUD 五件套 ---
workrally shot list --series-id <id>                                              # 场次列表
workrally shot get <story_id>                                                     # 场次详情
workrally shot create --series-id <id> --json-list '[{"image_prompt":"..."}]'     # 批量创建
workrally shot update <story_id> --image-prompt "..." --animation-prompt "..."    # 单条更新
workrally shot update <story_id> --story-num "EP01-SC01"                          # 单条改名（story_num）
workrally shot update --batch '[{"story_id":"...","image_prompt":"..."}]'         # 批量更新
workrally shot delete <story_ids...>                                              # 软删除（→回收站）
# --- 业务语义糖（CRUD 之外）---
workrally shot sort --series-id <id> --order id1,id2,id3                                # 重排
workrally shot image-models                                                              # ⭐ 场次专用图片模型（≠ canvas）
workrally shot video-models                                                              # ⭐ 场次专用视频模型（固定 mode=9）
workrally shot set-model [--story-ids id1,id2] --video-provider 1 --duration 5 --aspect-ratio 16:9   # 配置视频模型（推荐）
workrally shot set-model [--story-ids id1,id2] --image-model <en_name> --aspect-ratio 16:9          # 配置图片模型
workrally shot bind --story-id <id> --type image --assets '[{...}]'                     # 绑定参考资产
workrally shot recognize --project-id <id> --series-id <id> [--scope all|project]       # 识别角色
workrally shot generate-image --story-ids id1,id2 [--count N]                           # 仅提交；无 --poll/--model；查结果 shot get-result --type image [--watch]
workrally shot generate-video --story-ids id1,id2 [--count N]                          # 同上；--type video。无 --model/duration/ratio/--poll


# === 上传 / 下载 ===
workrally upload ./file.png -o json           # 上传文件 (COS SDK 直传)
workrally download <asset_id> [-d ./output/]  # 下载素材 (自动处理访问凭证)

# === AI 生图 ===
workrally generate image-models               # 查看可用模型（必须先调用！）
workrally generate image --prompt "描述" --model <model_id> [--aspect-ratio 16:9] [--input-images "url"] --poll

# === AI 生视频 (4 种驱动模式) ===
workrally generate video-models               # 查看可用模型（必须先调用！）
workrally generate video --prompt "描述" --model <provider_id> --poll                        # 纯文生视频（默认 Text 模式）
workrally generate video --prompt "描述" --model <provider_id> --single-image-url "url" --poll  # 图生视频（Text 模式 + 参考图）
workrally generate video --mode FirstLastFrame --prompt "描述" --model <provider_id> --first-frame-url "url" --poll  # 首尾帧
# 其他模式: FrameSequence(--sequence-frames)  SubjectToVideo(--reference-assets)
# --mode 默认 Text；通用选项: --duration <秒> --count 1-4 --enable-sound --poll

# === 媒资库 (asset) — 项目级媒体文件池 ===
workrally asset create --url <cdn_url> --project-id <id> -o json  # 入库（返回可访问 URL）
workrally asset search --project-id <id>      # 搜索
workrally asset get <asset_id>                # 详情
workrally asset update <asset_id> --name "新名称"  # 更新素材 (目前仅支持改名)

# === 资产库 (material) — 树形管理：人物/道具/场景/网盘 ===
workrally material list role_person           # 人物  |  role_prop 道具  |  role_scene 场景  |  root 网盘文件夹
workrally material add ...                    # 创建素材/文件夹（从媒资库挂载）
workrally material get <material_id>          # 素材详情
workrally role get <role_id>                  # 角色详情（LoRA/提示词/版本）

# === 画布 ===
workrally canvas list                         # 列出画布
workrally canvas create "名称"                # 创建画布
workrally canvas build-draft <canvas_id> --file nodes.json          # 增量合并（默认保留已有节点）
workrally canvas build-draft <canvas_id> --nodes '[...]'            # 同上，直接传 JSON
workrally canvas build-draft <canvas_id> -d "id1,id2"               # 删除指定节点
workrally canvas build-draft <canvas_id> -n '[...]' -d "old1"       # 同时增删改
workrally canvas build-draft <canvas_id> -n '[...]' --mode overwrite  # 全量覆盖（清空后重建）

# === 任务查询 ===
workrally generate task <task_id> [--poll]    # 查询/轮询生成任务状态

# === 通用透传（调用任意 MCP 工具）===
workrally tools list                          # 列出所有工具
workrally tools describe <tool_name>          # 查看参数 schema
workrally tools call <tool_name> --arg key=value [--json-args '{}']

# === URL / 升级 ===
workrally url build "页面名" [--params '{}']  # 构建 WorkRally 前端链接
workrally url parse <url>                     # 解析 URL
workrally upgrade [--check]                   # 升级 / 仅检查
```

输出格式: `-o json`(默认, Agent 推荐) | `-o table`(人类阅读) | `-o text`(管道/脚本) | `workrally config set output_format <fmt>`

## 关键工作流：上传文件

**概念**：媒资库(asset) = 项目级文件池；资产库(material) = 树形目录(人物/道具/场景/网盘文件夹)。资产库的素材只能从媒资库挂载。

```bash
# 步骤 1: 上传 → CDN URL
workrally upload ./character.png -o json
# 步骤 2: 入媒资库（必须！返回 asset_id + asset_details）
workrally asset create --url <cdn_url> --project-id <project_id> -o json
# 步骤 3（按需）: 挂载到资产库（必传 asset_id + 完整 asset_details）
workrally material add --json-list '[{"material_id":"<asset_id>","material_name":"名称","material_type":2,"parent_id":"<target_id>","material_detail":<asset_details_json>}]' \
  --project-ids <project_id>
```

> **步骤 1→2 强制绑定**，上传后必须入媒资库。视频/音频为私有读，需经媒资库才能正常访问。
>
> **步骤 3 由 Agent 判断**："上传文件" → 两步 | "上传到角色/道具/场景/文件夹" → 三步 | "媒资素材添加到资产库" → 仅步骤 3

## 关键工作流：场次创作



## ⚠️ 重要规则

1. **前端链接必须用 `workrally url build` 生成**，严禁自行拼接 URL
2. **模型 ID 必须动态获取**：`image-models` / `video-models`，严禁猜测或硬编码
3. **`canvas` ≠ `project`**：画布用 `canvas`，项目用 `project`，两者 ID 不能互换
4. **`build-draft` 实时协同**：写入后所有在线用户立即看到变更，默认增量合并（只传变更节点），支持多人并发安全操作
5. **`build-draft` 节点校验**：8种节点类型各有必填字段，详见 [`canvas-guide.md`](references/canvas-guide.md)
6. **AI 生成自动占位**：`generate image/video` 传入 `--project-id`（画布ID）后自动在画布创建占位节点，**无需**再手动 `build-draft`
7. **素材命名**：`--name` 传入"画布名_素材特征"（画布场景）或 prompt 关键词（非画布场景）
8. **不确定参数时**用 `--help` 或 `tools describe` 自行探索
9. **URL 白名单**：所有 URL 类参数（生图/生视频的 `--*-url` / `--*-assets` / `--*-images`、`asset create --url` 等）仅接受 WorkRally 官方媒资 URL。合法来源：① `workrally upload` 返回值 ② `asset get/search` 返回值（可直接传入） ③ 用户已提供的官方 URL。本地文件或第三方 URL 必须先 `workrally upload`。如遇"非法或已过期"提示，通过 `asset get/search` 重新获取即可。

## 📚 深度指南 (references/)

本 Skill 附带详细参考文档，覆盖复杂工作流：

| 文档 | 内容 |
|------|------|
| [`references/shot-guide.md`](references/shot-guide.md) | 场次操作 — CRUD/排序、提示词、模型、生成与结果；**§9** 场次创作工作流与专项规则（原 SKILL 正文迁入） |
| [`references/canvas-guide.md`](references/canvas-guide.md) | 无限画布操作 — 8种节点类型、画板嵌套、build-draft 增量/覆盖模式、协同编辑 |
| [`references/upload-and-assets-guide.md`](references/upload-and-assets-guide.md) | 上传与素材管理 — 三步上传流程、媒资库 vs 资产库、树形目录操作 |
| [`references/ai-generation-guide.md`](references/ai-generation-guide.md) | AI 生成 — Kontext 生图、4种视频驱动模式、模型动态获取、任务轮询 |
| [`references/common-pitfalls.md`](references/common-pitfalls.md) | 常见易错点 — 项目/画布混淆、模型硬编码、上传缺步骤等10类典型错误 |

> 遇到画布、上传、AI生成相关的复杂操作时，请优先查阅对应的参考文档。

## 环境变量

- `WORKRALLY_API_KEY` — API Key (Bearer Token)
- `WORKRALLY_ENDPOINT` — API 端点 (默认 `https://workrally.qq.com/zenstudio/api/mcp`)
- `WORKRALLY_CONFIG_DIR` — 配置文件目录 (默认 `~/.workrally`，非持久化容器建议指向持久卷)
- `WORKRALLY_NO_UPDATE_CHECK=1` — 禁用自动版本检查 (CI/CD 推荐)
