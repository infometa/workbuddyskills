# 场次操作指南

本文档帮助 AI Agent 通过 `workrally shot` / `workrally series` 命令完成场次的全生命周期管理。

---

## 1. 概念图谱

```
项目 (project)
 └─ 剧集 (series)
     └─ 场次 (shot/story) ← 本文档主角
         ├─ ⭐ 图片提示词 (image_prompt)            ← 核心字段：决定关键帧画面
         ├─ ⭐ 视频提示词 (animation_prompt)         ← 核心字段：决定动效/运镜
         ├─ 角色绑定 (role_data_json / video_role_data_json)
         ├─ 模型配置 (animation_model / animation_duration / image_model)
         ├─ 分镜 (layer) × N    ← 本期 shot 命令族不封装图层操作；如需修改请用 `tools call layer_batch_*`
         └─ [deprecated] 描述 (story_description)   ← 已废弃，前端不再展示
```

---

## 2. 标准工作流

### 2.1 从零搭建一个剧集

`series create` → `shot create`（带 image_prompt 和/或 animation_prompt）→ `shot recognize` → `shot set-model` → `shot generate-image / generate-video --story-ids id1,id2,...` → `shot get-result --watch`（按场次按类型分别拉结果）

```bash
# 1) 新建项目
PROJECT_ID=$(workrally project create "我的短番" -o json | jq -r '.project_id')

# 2) 新建剧集
SERIES_ID=$(workrally series create --project-id $PROJECT_ID --name "第一集" -o json | jq -r '.series_id')

# 3) 批量创建场次（按用户意图填提示词）
workrally shot create --series-id $SERIES_ID --json-list \
  '[{"image_prompt":"古风庭院全景","animation_prompt":"镜头缓推"},
    {"image_prompt":"两位侠客对峙","animation_prompt":"推近脸部特写"},
    {"image_prompt":"日落远景","animation_prompt":"镜头慢慢拉远"}]'

# 4) 自动识别角色
workrally shot recognize --project-id $PROJECT_ID --series-id $SERIES_ID

# 5) 配置模型
workrally shot video-models -o json    # 先动态获取场次专用视频模型
workrally shot set-model --series-id $SERIES_ID --video-provider <N> --duration 5 --aspect-ratio 16:9

# 6) 拿到全部场次 ID（用 -o json 拼成逗号串）后多场次一起发起生成
STORY_IDS=$(workrally shot list --series-id $SERIES_ID -o json \
  | jq -r '[.story_list[].story_id] | join(",")')
workrally shot generate-image --story-ids "$STORY_IDS"
workrally shot generate-video --story-ids "$STORY_IDS"

# 7) 按场次 + 类型分别等结果（图片和视频是两条独立进度）
for sid in $(echo "$STORY_IDS" | tr ',' ' '); do
  workrally shot get-result --story-id $sid --type image --watch
  workrally shot get-result --story-id $sid --type video --watch
done
```

### 2.2 把小说/剧本拆成场次

CLI 不内置"小说拆分"能力，由 Agent 自行：

1. 用 LLM 把小说按场景拆段
2. **根据用户意图按需生成提示词**：
   - 用户要漫画/插画 → 每个场次只写 `image_prompt`
   - 用户要短视频/动效 → 每个场次只写 `animation_prompt`
   - 用户要漫剧（图+视频）→ 两个都写
3. `shot create --json-list '[{image_prompt}, {animation_prompt}, ...]'` 一次入库
4. `shot recognize` 自动识别角色（按填的提示词路数：1 路或 2 路）

### 2.3 改写已有场次

```bash
# 改一个场次
workrally shot update <story_id> --image-prompt "..." --animation-prompt "..."

# 改一个场次的编号（单条改名）
workrally shot update <story_id> --story-num "EP01-SC01"

# 批量改多个场次（含批量改名：每条传 story_num 即可）
workrally shot update --batch \
  '[{"story_id":"st_1","image_prompt":"水墨风格的古城"},
    {"story_id":"st_2","animation_prompt":"运镜从近到远"},
    {"story_id":"st_3","story_num":"EP01-SC03"}]'
```

注意：CLI 写入的是文本字段；`extra.image_prompt_json` / `extra.animation_prompt_json`（lexical 富文本）由前端编辑器保存时同步。

---

## 3. 模型与时长配置

> ⚠️ **场次模型 ≠ 画布模型**：场次用 `workrally shot image-models / video-models`（专用接口），不是 `workrally generate image-models / video-models`（那是画布的）。两者底层 schema 不同，不能混用。

```bash
# 必须先动态获取场次专用模型（严禁硬编码）
workrally shot image-models -o json    # → 拿到 models[].en_name（图片模型）
workrally shot video-models -o json    # → 拿到 models[].provider（视频 provider 数字，固定 mode=9）

# 全部场次统一配置（不传 --story-ids 时需要 --series-id 拉取全集）
workrally shot set-model --series-id <sid> --video-provider 1 --duration 5 --aspect-ratio 16:9 --enable-sound

# 部分场次覆盖
workrally shot set-model --story-ids st_1,st_2 --duration 10
```

### 3.1 字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| `--video-provider` ⭐ | `shot video-models` 的 `models[].provider` 数字 | **推荐**写法。CLI 自动拼成 `"9,${provider}"` 写入场次 `animation_model` 字段 |
| `--animation-model` | 完整 `"mode,provider"` 字符串如 `"9,1"` | 高级用法，与 `--video-provider` 互斥 |
| `--duration` | 模型的 `models[].duration_options` | 视频时长（秒） |
| `--image-model` ⭐ | `shot image-models` 的 `models[].en_name` | 图片模型，如 `kontext_pro` |
| `--aspect-ratio` | 模型的 `models[].ratio_options` | 视频/图片宽高比，CLI 同步拆成 `generate_width/generate_height` |
| `--enable-sound` | 模型 `models[].support_audio === true` 才生效 | 音画直出 |

### 3.2 视频模型为何要 `mode + provider` 拼接？

场次的视频生成走 `TvShortSeries.GenerateStoryAnimation`，后端按 `animation_model` 字段（格式 `"<mode>,<provider>"`）路由到具体的视频驱动算法。前端 `useShotDuration` 也按这个格式存储。

**场次固定使用 `mode=9 (ANIMATION_SUBJECT_TO_VIDEO，参考主体生视频)`** — 这是产品决策（场次模式天然依赖角色绑定+提示词驱动）。

CLI 的 `--video-provider` 是为这个场景做的语义糖：用户只需选 provider 数字，CLI 自动补上 `mode=9`。如果要走非 9 的模式（如首尾帧 mode=1），需用 `--animation-model "1,N"` 直传。

### 3.3 画布模型 vs 场次模型 — 速记表

| 维度 | canvas（画布） | shot（场次） |
|------|---------------|-------------|
| 列模型 | `workrally generate image-models / video-models` | `workrally shot image-models / video-models` |
| 图片模型 ID 字段 | `model_id` | `en_name` |
| 视频模型 ID 字段 | 单个 `provider` 字符串 | `"mode,provider"` 拼接，如 `"9,1"` |
| 调生成时是否传 model | 是（`--model`） | **否**（用场次自身字段，先 `set-model` 写入） |
| 多场次/批量 | 在画布里独立任务 | `--story-ids id1,id2,id3` 一次触发多个 |

---

## 4. 资产识别（recognize）

```bash
# scope=project：仅本项目资产库（推荐，默认值）
workrally shot recognize --project-id <pid> --series-id <sid> --scope project

# scope=all：在全资产库中匹配
workrally shot recognize --project-id <pid> --series-id <sid> --scope all

# 仅识别部分场次
workrally shot recognize --project-id <pid> --series-id <sid> --story-ids st_1,st_2
```

工具内部对每个场次执行：

1. 取 `image_prompt` / `animation_prompt`（不再读 `story_description`，已废弃）
2. **两次** `MatchContentRole` 并发请求（图片提示词 / 视频提示词）
3. 写回 `role_data_json`（图片提示词识别结果）/ `video_role_data_json`（视频提示词识别结果）

> 识别完成后，前端打开场次会自动显示绑定的角色 tag。
>
> 💡 **两路独立**：只填了 `image_prompt` → 仅识别图片侧角色；只填了 `animation_prompt` → 仅识别视频侧角色；两个都没填才整体跳过。

---

## 5. AI 生成与结果查询

> ⭐ **生成前必做**：先 `shot get <story_id>` 确认场次的模型/时长/比例字段已配置；缺字段直接调 `generate-*` 后端会拒绝。
>
> ⚠️ **场次生成 ≠ 画布生成**：`shot generate-*` 调的是 `TvShortSeries.GenerateStoryAnimation`，**只表示"提交是否成功"，不返回 task_id，不能用 `canvas_get_task` 轮询**；进度归属于「场次 + 类型」维度，必须用 `shot get-result --story-id <id> --type image|video` 查。

### 5.1 三步流程（确认 → 配置 → 生成 → 查结果）

```bash
# Step 1: 检查场次字段是否齐全
workrally shot get <story_id> --project-id <pid> -o json
# 关注:
#   生图前：image_model（非空）/ image_generate_width / image_generate_height
#   生视频前：animation_model（"9,N" 格式）/ animation_duration / generate_width / generate_height

# Step 2: 字段不全则先用 set-model 配置（先 image-models / video-models 拿可选项）
workrally shot image-models -o json    # 选 en_name
workrally shot video-models -o json    # 选 provider 数字
workrally shot set-model --story-ids <story_id> \
  --image-model <en_name> --video-provider <N> --duration 5 --aspect-ratio 16:9

# Step 3: 触发生成（CLI 只接受 --story-ids + --count，不传 model/duration/ratio，也不传 project/series）
workrally shot generate-image --story-ids <story_id> --count 3
workrally shot generate-video --story-ids <story_id>

# Step 4: 按场次 + 类型分别查结果
workrally shot get-result --story-id <story_id> --type image            # 单次拉一页
workrally shot get-result --story-id <story_id> --type image --watch    # 持续轮询直到全部任务结束
workrally shot get-result --story-id <story_id> --type video --watch
```

### 5.2 多场次并发生成

```bash
# 单场次生 3 张图（每场次 count 张 = 3 个后端任务）
workrally shot generate-image --story-ids st_1 --count 3

# 多场次一起生视频（每场次 1 个任务，handler 内部循环并发提交）
workrally shot generate-video --story-ids st_1,st_2,st_3

# 等结果：图片 / 视频是两条独立进度，需要按 story + type 分别 watch
for sid in st_1 st_2 st_3; do
  workrally shot get-result --story-id $sid --type video --watch --interval 5
done
```

> 💡 `shot generate-image / generate-video` **只接受 `--story-ids` + `--count`**：下游 `GenerateStoryAnimation` 仅按 `story_id` 路由，**不接受 `--project-id` / `--series-id`**，也不接受 `--model / --duration / --aspect-ratio / --enable-sound` 等运行时参数（这些必须先用 `shot set-model` 写入场次字段）。这与 canvas 的 `generate image/video --model <id>` 行为有意区分（场次走持久化配置）。

### 5.3 `shot get-result` 字段速览

`shot get-result --story-id <id> --type <image|video>` 返回的关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `state` | `'all_done' \| 'running' \| 'no_data'` | ⭐ 顶层判定字段，`all_done` 即该场次该类型下没有进行中的任务（成功 / 失败都算结束） |
| `doing_count` | number | 进行中任务数（=0 时 `state` 不再是 `running`） |
| `done_count` | number | 已成功的产物数（即 `results.length`） |
| `failed_count` | number | 失败任务数（即 `failed_tasks.length`） |
| `results[]` | `{asset_id, asset_url, asset_title, material_poster, created_at}` | 已完成产物 |
| `doing_tasks[]` | `{task_id, percentage, process_desc, status}` | 进行中明细 |
| `failed_tasks[]` | `{task_id, failed_reason, status}` | 失败明细 |

> 💡 `--watch` 时 CLI 会按 `--interval` 秒（默认 5）轮询本工具，直到 `state === 'all_done'`；如果连续 6 次返回 `no_data`（后端入队还没完成）才会兜底退出。

---

## 6. 资产绑定（bind）

```bash
# 把图片资产绑定为参考主体
workrally shot bind --story-id st_1 --type image \
  --assets '[{"asset_id":"a1","url":"https://..."},{"asset_id":"a2","url":"https://..."}]'

# 替换而非追加
workrally shot bind --story-id st_1 --type image --mode replace --assets '[...]'

# 视频资产
workrally shot bind --story-id st_1 --type video --assets '[{...}]'
```

> `image`/`audio` 写入 `role_data_json`；`video` 写入 `video_role_data_json`。

---

## 7. 删除与恢复

```bash
# 软删除（默认行为，→回收站）
workrally tools call project_delete --json-args '{"project_id":"<pid>"}'
workrally series delete <sid>
workrally shot delete <story_id_1> <story_id_2>

# 查回收站 / 恢复 / 彻底删
workrally tools call recycle_bin_list --json-args '{"entity_type":"project"}'
workrally tools call recycle_bin_restore --json-args '{"entity_type":"project","entity_id":"<pid>"}'
workrally tools call recycle_bin_delete --json-args '{"entity_type":"project","entity_id":"<pid>"}'   # 彻底删
```

> ⚠️ CLI `delete` 命令**不暴露** `--permanent` flag，避免误删；如确需彻底删除，请显式调 `tools call recycle_bin_delete`。

---

## 8. 易错点

| 错误 | 正确做法 |
|------|----------|
| 直接 `workrally tools call story_batch_update` 漏字段 | 改用 `shot update` / `shot update --batch`，自动先查后改 |
| 用 `generate image-models / video-models` 给场次配模型 | 那是画布的；场次必须用 `shot image-models / video-models`（schema 不同） |
| 用 `shot generate-video --model <provider>` 临时覆盖 | 不接受；模型必须先 `shot set-model --video-provider <N>` 写入场次字段 |
| `shot generate-*` 还想传 `--project-id / --series-id` | 不接受；下游 `GenerateStoryAnimation` 仅按 `story_id` 路由，只用 `--story-ids` + `--count` |
| `shot set-model --animation-model <provider>` 只传 provider 数字 | 该字段要 `"mode,provider"` 字符串；推荐改用 `--video-provider <N>`，CLI 自动拼成 `"9,N"` |
| `shot generate-*` 直接调，没 `shot get` 检查 | 后端会拒绝（缺 model/duration/ratio）；先 `shot get` 验字段 → 缺则 `shot set-model` 写入 |
| 模型 ID 硬编码 | 必须先 `shot image-models` / `shot video-models` 动态获取 |
| 等待 `shot generate-*` 返回 `task_id` 然后用 `generate task` / `canvas_get_task` 轮询 | 场次生成接口 `GenerateStoryAnimation` 不返回 task_id；查结果必须用 `shot get-result --story-id <id> --type image\|video [--watch]` |
| 用一次 `shot get-result` 同时查图片和视频 | image / video 是两条独立进度；必须分别用 `--type image` 和 `--type video` 各拉一次 |
| 想批量改场次编号但找不到 `shot rename` | 本期不提供；单条 `shot update <id> --story-num "..."`，批量 `shot update --batch '[{"story_id":"...","story_num":"..."}]'` |
| 想增删图层但找不到 `shot add-layer/delete-layer` | 本期不提供；直接 `workrally tools call layer_batch_add_update / layer_batch_delete` |
| 把场次和分镜（图层）混淆 | 场次=story；分镜=layer。图层操作走 `tools call layer_batch_*` |
| 误删项目/剧集/场次 | `delete` 默认软删→回收站。用 `tools call recycle_bin_list` + `recycle_bin_restore` 恢复 |
| 想彻底删除项目/剧集 | 项目：`tools call project_delete`（软删）后如需彻底删用 `recycle_bin_delete`；剧集/场次：`series delete` / `shot delete` 仅软删；彻底删用 `tools call recycle_bin_delete --json-args '{"entity_type":"project","entity_id":"..."}'` 等 |
| 用 `shot update --description` 改描述 | `story_description` 已废弃，CLI 不暴露此参数；改用 `--image-prompt` / `--animation-prompt` |
| 仅填 `image_prompt` 后又调 `generate-video` | 该场次没填 `animation_prompt`，会被后端拒绝。要么补 `animation_prompt` 要么改用 `generate-image` |

---

## 9. 场次创作工作流 Skill 迁入

以下与主 `SKILL.md` 中的「关键工作流：场次创作」及「重要规则」第 10–15 条对齐，便于单文件查阅。

**概念层级**：项目 (project) → 剧集 (series) → 场次 (shot/story)。一个场次 = 一段连续画面，**核心由提示词承载**：图片提示词（image_prompt）和/或视频提示词（animation_prompt）+ 角色绑定。

> ⚠️ **场次描述（story_description）已废弃**，前端不再展示。请用 `image_prompt` 和/或 `animation_prompt` 表达场次内容。
>
> 💡 **按需填写**：根据用户意图判断要图、要视频、还是图+视频；不强制两个都填。

```bash
# 步骤 1: 创建剧集（如已有可跳过）
workrally series create --project-id <pid> --name "第一集" -o json

# 步骤 2: 批量创建场次 — 三种典型用法
# A) 用户要静态图/漫画/插画 → 仅填 image_prompt
workrally shot create --series-id <sid> --json-list \
  '[{"image_prompt":"古风庭院全景，月光皎洁"},
    {"image_prompt":"两位侠客剑指对方，剑光交错"}]'
# B) 用户要短视频/动效 → 仅填 animation_prompt
workrally shot create --series-id <sid> --json-list \
  '[{"animation_prompt":"镜头从院门缓推至中景"},
    {"animation_prompt":"快速推近至脸部特写"}]'
# C) 漫剧（图+视频均要）→ 两个都填
workrally shot create --series-id <sid> --json-list \
  '[{"image_prompt":"古风庭院全景","animation_prompt":"镜头缓推"},
    {"image_prompt":"两位侠客对峙","animation_prompt":"推近脸部特写"}]'

# 步骤 3: 基于提示词自动识别角色（两路独立 fallback：填什么识别什么）
workrally shot recognize --project-id <pid> --series-id <sid>

# 步骤 4: 配置模型 — 与提示词一一对应（**必须先动态获取场次专用模型列表**）
# ⚠️ 场次的模型与 canvas 不同：
#   - canvas 用 `workrally generate image-models / video-models`
#   - shot   用 `workrally shot image-models / video-models`（schema 不同）
workrally shot image-models -o json    # 拿到 models[].en_name（图片模型 ID）
workrally shot video-models -o json    # 拿到 models[].provider（视频模型 provider 数字）

# 用法 A：仅图
workrally shot set-model --image-model <en_name> --aspect-ratio 16:9
# 用法 B：仅视频（推荐 --video-provider 数字，CLI 自动拼成 mode=9,provider）
workrally shot set-model --video-provider 1 --duration 5 --aspect-ratio 16:9
# 用法 C：图+视频
workrally shot set-model --image-model <en_name> --video-provider 1 --duration 5 --aspect-ratio 16:9

# 步骤 5: 多场次一起生图 / 一起生视频
# ⭐ **生成前先用 `shot get` 确认场次已配置模型/时长/比例**：
#   - 生图前查 image_model / image_generate_width / image_generate_height
#   - 生视频前查 animation_model（应为 "9,N" 格式）/ animation_duration / generate_width / generate_height
workrally shot get <story_id> --project-id <pid> -o json    # 检查上述字段是否非空
# 缺字段时回到步骤 4 用 set-model 写入；都齐全后仅提交（无 --poll；接口不返回 task_id）：
workrally shot generate-image --story-ids st_1,st_2,st_3 [--count 1]   # 仅 --story-ids / --count / -o；模型从场次字段读
workrally shot generate-video --story-ids st_1,st_2,st_3 [--count 1]   # 同上；勿传 --model / --duration / --aspect-ratio
# 进度与产物：按场次、按类型分别查（多场次可 shell 循环）
workrally shot get-result --story-id st_1 --type image --watch
workrally shot get-result --story-id st_1 --type video --watch
```

> **多场次生成**: `--story-ids` 逗号分隔多个 ID，handler 内部并发提交；**仅返回是否提交成功**，不返回 `task_id`，**无 `--poll` 参数**。查进度与产物必须用 `shot get-result --story-id <id> --type image|video`（可加 `--watch`）。本期不提供独立的 `batch-generate` 命令。
>
> **批量编辑提示词**: `shot update --batch '[{...}]'` 一次更新多个场次，比逐个 `shot update <id>` 高效得多。
>
> **批量改名**: 多条 `shot update --batch '[{"story_id":"...","story_num":"EP01-SC01"}]'` 即可，本期不提供独立的 `rename` 命令。
>
> **删除 = 软删除**: 项目用 `tools call project_delete`；`series delete` / `shot delete` 为 CLI 子命令。默认均移入回收站，可通过 `recycle_bin_*` 恢复或彻底删除。

场次侧**没有** `generate-* --poll`；轮询与结果一律以本文 **§5** 的 `shot get-result [--watch]` 为准。

### 场次专项规则 10-15

10. **场次内容核心字段**：`image_prompt`（决定关键帧）+ `animation_prompt`（决定动效）。**不强制都填**，按用户意图判断（仅图 / 仅视频 / 图+视频）。`story_description` 已废弃，CLI 不暴露 `--description`
11. **场次模型 ≠ 画布模型**：
    - 画布（canvas）用 `workrally generate image-models / video-models`
    - **场次（shot）用 `workrally shot image-models / video-models`**（schema 不同，不要混用）
    - 场次视频固定 `mode=9 (SUBJECT_TO_VIDEO)`；CLI 用 `--video-provider <N>` 数字时会自动拼成 `"9,N"` 写入 `animation_model`
12. **生成前必须先用 `shot get` 确认模型已配置**：
    - 生图前：`image_model`、`image_generate_width`、`image_generate_height` 都非空
    - 生视频前：`animation_model`（"9,N" 格式）、`animation_duration`、`generate_width`、`generate_height` 都非空
    - 缺字段直接调 `shot generate-*` 后端会拒绝；先 `shot set-model` 写入再生成
13. **多场次生成不要找 batch 命令**：`shot generate-image / generate-video` 的 `--story-ids` 直接接 `id1,id2,id3` 即可一次性触发多个场次的生成任务，本期不提供 `shot batch-generate`
14. **`shot generate-image / generate-video` 仅支持 `--story-ids`、`--count`、`-o`**：无 `--poll`；不接受 `--model` / `--duration` / `--aspect-ratio` 等运行时覆盖（均从场次字段读，先用 `shot set-model` 写入）。提交后用 `shot get-result --type image|video [--watch]` 查结果
15. **删除是软删除**：项目无 `workrally project delete`，用 `tools call project_delete`；`series`/`shot` 的 `delete` 子命令默认移入回收站，可通过 `tools call recycle_bin_restore` 恢复；彻底删除请用 `tools call recycle_bin_delete`
