---
name: workrally-batch-image-gen
description: WorkRally MCP 批量生图工作流。用于一次提交
  N（10-100+）个图片生成任务、并发轮询拉取结果、并发下载到本地的标准化流程。覆盖关键技巧：MCP
  天然 fire-and-forget 提交（canvas_generate_image 立即返回 task_ids）、通过
  asset_search 的 page_size=100 + title 前缀过滤批量匹配资产、ThreadPoolExecutor
  并发 curl 下载、缺失任务多轮自愈重提。适用于「网站需要 N 张统一风格示例图」「品类 ×
  形态矩阵」「色板对比图组」「分镜批量出图」等场景。全程通过 WorkRally MCP 工具完成，不依赖 workrally CLI。
description_zh: WorkRally 批量生图
description_en: WorkRally batch image gen
agent_created: true
version: 1.1.0
---

# workrally-batch-image-gen

> **执行通道**：本 skill 全程使用 **WorkRally MCP 工具**（`mcp__workrally1__*`）。
> **不要**调用 `workrally` CLI，也不要依赖 `WORKRALLY_API_KEY`——鉴权由 MCP 连接器托管。
> 迁移对照：原 CLI 的 `workrally gen image` → `canvas_generate_image`；`workrally gen task` → `canvas_get_task`；`workrally asset search` → `asset_search`；`workrally upload` → `upload_file` + `asset_create`。

## When to use

触发条件（任一即用）：
- 用户要求「批量生成 N 张图」「N 个变体」「品类 × 形态矩阵」「色板对比」等需要 ≥6 张同风格示例图的任务
- 网站/演示页需要十几张到上百张统一风格的产品图、KV、分镜样片
- 之前只能一次跑 1-3 张时，现在需要规模化加速

不要用于：
- 单张图（直接调一次 `canvas_generate_image`，`count=1`）
- 需要参考图（`input_images`）的复杂任务（要单独处理，最大参考图数量取决于模型的 `kontext_config.max_input_images`）

## Steps

### 1. 准备项目 ID 与模型

```text
project_list()                  → 取短番项目 ID（没有指定就用名为「默认项目」的那个）
canvas_image_model_list()       → 取 models[].model_id / name / en_name /
                                  resolution_options / aspect_ratios /
                                  infer_quality_options / kontext_config.max_input_images
```

**默认项目 ID 通常是 `4mp05r3qiwtkt3a5a18dkj6`**（用户 moke 的「默认项目」），但每次仍应先 `project_list` 核实。
常用模型的人读名：**GPT2 (gpt-image-2)**、**贝宝PRO**、**贝宝2**、**nano-banana 4K** 等。
⚠️ **model_id 必须从 `canvas_image_model_list` 的返回里取，不要硬编码**；不同环境可用模型不同。

> ⚠️ **必做：模型探针（提交成功 ≠ 能出图）**。某些环境模型列表是脱敏别名（贝宝/维宝/元宝…），且 **`gpt-image-2`(gpt2) 可能"提交通过但执行必 state=5 失败"**（错误信息："请求时遇到了一些问题/请联系支持同学"）。批量前务必先用目标模型跑 1 张探针，`sleep 90` 后 `canvas_get_task` 查到 **state=4** 才算可用；若 state=5，换别名模型实测。**2026-07 实测可用别名：`w6uxmppxi0`(贝宝pro)、`uoifr1f6z2`(贝宝2) 均成功出图**。

### 2. 批量提交（MCP 天然 fire-and-forget）

`canvas_generate_image` **本身就是异步的**——提交后立刻返回 `task_ids`，不阻塞。因此**不需要** CLI 时代的 `--poll` 技巧：

```text
canvas_generate_image(
  prompt                  = "<prompt>",
  model                   = "<model_id>",
  aspect_ratio            = "16:9",
  resolution              = <该模型 resolution_options[].value>,
  count                   = 1,              # 每个变体一次调用，一次只出 1 张
  task_name               = "CAT01_FMCG_TVC",
  short_series_project_id = "<短番项目ID>"
)
→ task_ids: ["<id>"]
```

**提交节奏**：逐条串行调用（每条约几秒），或按小批（每批 4 个、批间隔 12 秒）提交。
⚠️ **不要一次并发轰炸 60-90 个**——会触发服务端限速与审核，首轮大量 state=5（这不是"丢失"，是真失败）。

批量清单可以用 `scripts/make_batch_plan.py` 生成（`name` + `prompt` 两列 JSONL），再按清单逐条提交。
把每次提交返回的 `task_id` **记到本地 ledger 文件**（`name → task_id`），后面查状态和补漏都靠它。

### 3. 等待 + 批量查询

后端单任务约 60–180 秒。同时间提交大批量任务时，远端会限速并行处理。**等约 3 分钟**后开始查询。

查**任务状态**（最可靠，按 ledger 里的 task_id 逐个查）：
```text
canvas_get_task(task_id="<id>")   → state 1=排队 2=运行 3=暂停 4=成功 5=失败 6=已取消
```

查**已入库素材**（用来批量拿 URL 下载）：
```text
asset_search(project_id="<短番项目ID>", material_type=["image"], page_size=100, page=1)
```
**重要**：`page_size` 默认 20，批量必须显式传 **100**（最大值）；超过 100 条要翻页。

把 `asset_search` 的返回**原样落盘**为 `/tmp/workrally/assets.json`，再交给下载脚本处理。

### 4. 并发下载

```bash
python3 scripts/download_assets.py /tmp/workrally/assets.json ./out/ CAT01_,CAT02_,AI_TIER
```
脚本做的事：读 `assets[]` → 按 `title` 前缀过滤 → 从 `asset_details.url` 取带签名地址 → 20 线程并发 `curl` 落盘。

> ⚠️ 若 `asset_search` 的返回里 `asset_details.url` 缺失或已过期（签名约 10 小时），用 `asset_detail(asset_ids=[...])`（一次最多 50 个 ID）重新取 URL。

### 5. 找出缺失，多轮自愈重提

```python
expected = ["CAT01_FMCG_TVC", "CAT02_AUTO_CG", ...]   # 你的清单
found    = {k for k, _, _ in items}                    # 已下载到的
missing  = [e for e in expected if e not in found]
print("Missing:", missing)
```

对缺失项**重新提交**（同一 `canvas_generate_image` 调用，`task_name` 加后缀 `_R` / `_R2` 避免同名去重）：
- 每轮小批（每批 ≤ 4 个，批间隔 12 秒）重提 → 等 170 秒 → 重新 `asset_search` → 再算 missing
- 循环 6–8 轮。绝大多数会在 2–4 轮内补齐，最后 3–5 张顽固失败的单独处理

### 6. 下载验证

```bash
ls ./out/ | wc -l            # 与预期数对齐
file ./out/*.jpg | head -5   # 实际是 PNG（magic bytes），浏览器按内容识别正常
```

## Pitfalls

- **不要使用 `workrally` CLI** —— 本 skill 的提交/查询/下载全部走 MCP 工具。
- **不要在批量提交时并发轰炸** —— 服务端限速 + 内容审核会让首轮大量 state=5。小批（每批 ≤4）、批间隔 12 秒。
- **`upload_file` 不能大规模并行** —— 参考图上传要**串行**（每张几秒），并发抢上传凭证会全部卡死无返回。放后台跑 + 读结果文件监控进度。
- **`page_size` 默认 20** —— 大批量必须传 `100`（最大值）。
- **远端入库可能延迟 30s+** —— 提交后立即查 asset 可能没有，等 3 分钟再开始轮询。
- **URL 带签名、约 10 小时过期** —— 用 `asset_details.url` / `download_url` 直接 curl 即可；过期后经 `asset_detail` 重取。
- **`task_ids` 不能直接用于下载** —— `task_ids` 只能用 `canvas_get_task` 查状态；下载素材必须等入库后从 `asset_details` 拿 url。
- **5-10% 任务可能丢失** —— 大批量提交时部分任务在远端被丢弃（无返回入库），需要单独重试。
- **文件实际是 PNG** —— 输出文件 magic bytes 是 PNG，扩展名用 `.jpg` 也能被浏览器正常识别。
- **同名提交会去重** —— `task_name` 重复时远端可能合并为一条记录。重试时加后缀 `_R` `_R2`。
- **大批量失败率可高达 80%** —— 同一时刻提交 60-90 个任务时，后端限速 + 审核会让首轮大量 state=5 FAILED（不是"丢失"，是真失败）。务必用「多轮自愈循环」：每轮 fetch → 算 missing → 小批重提 → 等 170s，循环 6-8 轮。
- **内容审核挡词** —— 提示词含 `vomit / vomiting / urinate / cockroach / blood / toilet` 等词更易被审核拒（持续 FAILED，有时明确报"输入提示词敏感或违反平台规定"）。改写为中性措辞（如 "slumped at a wall corner" 替代 vomiting、"raised tiled platform / utility room" 替代 toilet、"placing a bottle" 替代弹烟灰）后即可成功。顽固失败先怀疑提示词用词。
- **图生图保持一致（`input_images`）** —— 传公开短链 URL 数组（prompt 里用「第一张图片」「第二张图片」引用对应位置），用于跨镜头角色/场景一致：人物特写引用 face 九宫格、纯环境引用 scene master、人在场景中传双 ref（甚至三 ref）。prompt 里加 "Keep the exact same face identity from the reference" 强化身份锁定，效果显著。配合五锁管线（先出九宫格 face_ref + 场景 master，再引用出关键帧）可成体系产出一致资产。最大张数取决于模型的 `kontext_config.max_input_images`，不要写死。
- **去重正则要用 `\d\d` 不是 `\d2`** —— 从 asset title 提取基名 `SXX_YY` 时，正则务必写 `(S\d\d_\d\d)`；曾误写 `\d2`（匹配字面"2"）导致重试图全部以 `_R5` 后缀名落地、基名匹配失败。重试时用 `task_name` 加后缀(`_R/_F/_K`)，下载后需按基名 `re.match(r'(s\d\d_\d\d)',f)` 归并为规范文件名 `sXX_YY.jpg`（取最新 mtime 的有效 PNG），再清理后缀文件。
- **轮询不要在并发线程里堆同步等待** —— 更稳的做法：提交拿 `task_ids` 落 ledger → `sleep 30-150s` → 并发对每个 `task_id` 调 `canvas_get_task`（只认 state=4 下载、5 放弃重提），成功后再从 `output_assets` 取 url。
- **`asset_search` 只返回最新约 100-200 条** —— 翻页 page 1-3 基本就是最近提交的；早期任务可能翻不到，靠 `task_id` 直接查 `canvas_get_task` 更可靠。

## state 码对照

`canvas_get_task` 返回的 `state`：**1=排队中，2=运行中，3=暂停，4=成功(SUCCESS)，5=失败(FAILED)，6=已取消**。
轮询时只认 `4` 下载、`5` 放弃重提、其余继续等。

## 任务查询命令与字段（务必用对）

- 查询单任务状态：**`canvas_get_task(task_id=...)`**。
- 成功(state=4)时，出图 URL 在返回 JSON 的 **`output_assets[0].url`**（公开短链 `https://workrally.qq.com/s/xxx`，直接 curl 即可）；`output_assets[0].title` 是提交时 `task_name` + `.png`。
- 自愈脚本取 URL 时字段优先级建议：`output_assets` → `results` → `outputs` → `images`，再兜底用正则从整个 JSON 里 grep `https://\S+\.(jpg|jpeg|png|webp)`。

## Verification

- `ls ./out/ | wc -l` 等于预期数量
- 抽检 3 张图打开看：`file ./out/xxx.jpg`（PNG image data）
- HTML 引用时用 `<img src="...jpg" loading="lazy" onerror="this.style.opacity='0.2'">` 给降级体验

## 参考脚本

- `scripts/make_batch_plan.py` —— 批量提交计划生成器（输出 JSONL：`{"name":..., "prompt":...}`）
- `scripts/download_assets.py` —— 按前缀过滤 + 并发下载（输入为 `asset_search` 落盘的 JSON）
