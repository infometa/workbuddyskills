# 无限画布：生成或调整图片

无限画布生图：用户提供图片提示词，可选引用已有图片节点、本地附件和资产名称。资产清单批量生图见文末；制片工坊多环节串联改走 [gui-script-video.md](gui-script-video.md)。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_models.md](_models.md)。GUI 网页单点改资产不在当前 CLI 范围，用 `deeplink project --set creation_mode=2`、`deeplink episode` 或 `deeplink asset-lib --json` 返回入口。无限画布项目页必须带 `creation_mode=2`，打开总览「无限画布」tab。

`group` 是画布节点组，用于批量生成。`pin-group` 只钉颜色，不交给 `group execute`。`team-group` 当前未注册。

## 当前包

| 探测 | 包 | 入口 |
|---|---|---|
| 没有工作区或画布 | `create-blank` | 步骤 1～7 |
| 已有画布且要新生成一张图 | `create-blank` | `node list` 后从步骤 3 继续，新建节点 |
| 已有画布且要改或重跑已有节点 | `edit-existing` / `regenerate` | [无限画布分诊](#无限画布分诊) |

```bash
reelmate node list --workspace WORKSPACE_ID --canvas CANVAS_ID --json
reelmate node get NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

`WORKSPACE_ID` / `CANVAS_ID` 取当次确认或上一步创建结果，不要读磁盘绑定。

## 步骤表（create-blank）

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/7 | 登录并绑定项目 | 已登录；已绑定无限画布 `WORKSPACE_ID`。无目标画布时先 `workspace list` 让用户选 `creation_mode=2` 的项；用户要新建或没有候选时，按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`：复述创作模式「无限画布」，确认剧目类型与画面比例。已绑定制片工坊项目不得直接当无限画布使用 |
| 2/7 | 创建画布 | 已有 `CANVAS_ID` |
| 3/7 | 先预检 `project.edit`，再 `hitl.paid-image-params` | `IMAGE_MODEL`、`RESOLUTION`、`RATIO` 已经用户确认，且模型当次 `visible=true` |
| 4/7 | 创建并回填图片节点 | `node get` 与确认值一致；参考连线或 `referenceAssets` 已按来源就位 |
| 5/7 | 预演并提交生成 | 返回 `task_id` |
| 6/7 | 等待终态 | 任务 `status=succeeded`，节点 `task_info.status=success`，结果含 ≥1 张图 |
| 7/7 | 交付 | 已输出画布深链 `href`；Agent 场景另有图片预览 |

数量固定 `qty=1`。写操作带 `--json` 和 `--idempotency-key`。

## 无限画布分诊

不走阶段机，不先跑 `workflow detect`，不套 GUI 环节 1→4。视频意图改走 [generate-video.md](generate-video.md)，不要在本场景提交 `node generate video`。

| 用户意图 | 命令 | 边界 |
|---|---|---|
| 改已有图的提示词或参数 | `node edit NODE_ID --set prompt=... --json` | 不新建工作流 |
| 对已有图片节点再生成 | 一张 `node generate image --node NODE_ID`；多张 `group create` + `group execute` | 清单 ≥2 不逐条 `node generate` |
| 批量打组并立即生成 | `group create` 后 `group execute` | 不用 `pin-group create` 生成 |
| 只钉颜色分组 | `pin-group create` | 不把 pin id 交给 `group execute` |
| 画布抽资产或拆分镜（单节点） | `script asset-extract` / `script storyboard`，必须同时传 `--canvas` 和 `--node` | 不用 `novel` 或 GUI `resource extract` |

`group execute` 返回执行摘要，不交给 `task wait`。单次 `node generate` 的 `data.task_id` 才交给 `task wait`。失败按 `needs_input` 追问，不切到 `workflow resume`。成功后交付 `node get` 与 `deeplink canvas`，不描述为阶段推进。

## 1. 登录并绑定项目

按 [_bootstrap.md](_bootstrap.md) 登录。无限画布场景只绑定或新建 `creation_mode=2` 的项目：先 `workspace list` 把已有画布项目列给用户选；没有候选或用户明确要新建时 `creation_mode=2`，按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`：复述创作模式「无限画布」，剧目类型与画面比例用网页展示名（国内仿真人剧、海外仿真人剧、2D/3D动漫；`9:16 竖屏`、`16:9 横屏`）。已绑定制片工坊项目不能直接当无限画布使用。

## 2. 创建画布

按 [_bootstrap.md](_bootstrap.md) 创建画布。名称可用「无限画布生图」。

## 3. 查询模型并确认参数

已有画布从本步继续时同样先预检。先预检 `project.edit`，通过后再查模型目录并进入 `hitl.paid-image-params`。`error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md)「权限拒绝」停止。

```bash
reelmate team permission --require project.edit --json
reelmate model list --sp-type MODEL_SP_TYPE --json
```

无参考图用 `text2image`，单张参考图用 `image2image`，多张用 `multi_reference`。只列 `visible=true`、`supported_modes` 含目标模式且 `params.generation.<mode>` 非空的图片模型。筛选规则见 [_models.md](_models.md)。

`hitl.paid-image-params`（无限画布）按 [_hard-gate.md](_hard-gate.md) 分步列全：只问图片模型、画幅、分辨率，不问风格、题材、角色构图。先按 `mode_order` 目标模式列全部图片模型，确认后再按 `resolution_options` 原序列 `label` 列分辨率（与画幅互不影响，可同轮）。剧厂推荐：目录含 `TGI 2` 时标它；模型确认后，画幅有 `16:9`、分辨率有 `2K` 时再标推荐；不在该规则里时改用默认值并仍列出全部枚举。新建项目的画面比例（如 `9:16`）不是本步生图画幅，即使项目是竖屏，生图画幅仍按模型 `ratios` 列全。用户已明确给出的项不重复追问；用户明确沿用上一次生图参数时整包跳过提问，但须先执行本步 `project.edit` 预检并复述实际值。用户指定的模型不可见时反馈实时目录，不自动替换。

`NODE_NAME`：用户提供的资产名称，否则从提示词提炼短名，不用整段提示词。

## 4. 创建图片节点并关联参考

```bash
reelmate node create image --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --set name=NODE_NAME --idempotency-key CREATE_KEY --json
reelmate node edit NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --set prompt=PROMPT --set model=IMAGE_MODEL --set count=1 \
  --set settings="{\"ratio\":\"RATIO\",\"quality\":\"RESOLUTION\"}" \
  --idempotency-key FILL_KEY --json
```

参考来源按所在位置分流：

- 已有画布图片节点：确认 `node_type=image` 且生成成功后，建立 `reference` 连线。不下载、不重传、不新建同名节点。
- 本地附件：`upload` 后 `material add --node NODE_ID --material-type image --source upload`。`FILE_ID` 只取 upload 成功 JSON；审核未通过时停止。
- 两种同时存在：先连线，再挂本地附件。

```bash
reelmate node --workspace WORKSPACE_ID --canvas CANVAS_ID --left REFERENCE_NODE_ID --right NODE_ID \
  --semantic reference --idempotency-key REFERENCE_EDGE_KEY --json
```

方向：源节点在左，本次新建节点在右。`material add` 会追加到 `params.referenceAssets`。

指定 `--node` 后，`node generate image` 会读入边上游图片节点的 `result.items[].fileId`，再合并本节点 `referenceAssets`，按 `uri` 去重。有图则自动走参考生图（`image2image` / 多张且模型支持时 `multi_reference`），不要再手工拼 `--set images=`，也不要改走纯文生图。已显式传入 `images` 时以命令行为准。超分、打光、宫格等专用 mode 不自动挂参考图。

`done_when`：`node get` 中名称、prompt、模型、分辨率、画幅与确认值一致；引用已有节点时 `connection_list` 含 `source=REFERENCE_NODE_ID`、`target=NODE_ID`、`type=reference`；本地附件时 `referenceAssets` 含本次 `FILE_ID`。

## 5. 提交图片生成

`node generate image` 不会自动读取节点已保存的生成参数，必须复用第 3～4 步同一组变量。指定 `--node` 后 CLI 会先把本次参数合并写回；写回失败时不提交。

```bash
reelmate node generate image --workspace WORKSPACE_ID --canvas CANVAS_ID --node NODE_ID \
  --set ai_model_mark=IMAGE_MODEL --set prompt=PROMPT \
  --set resolution=RESOLUTION --set ratio=RATIO --set qty=1 \
  --dry-run --json
```

指定 `--node` 且画布已有参考连线或 `referenceAssets` 时，不要再追加 `--set mode=` / `--set images=`；预演里核对这些值即可。

预演返回 `dry_run=true`。核对模型展示名、`resolution`、`radio_ui`、`qty` 以及算出的 `width`/`height`；有参考图时再核对 `images` 与 `endpoint` 为参考生图。提交前按 [_hard-gate.md](_hard-gate.md) 积分展示策略展示预估消耗、余额和积分明细链接，用户确认后再去掉 `--dry-run` 提交。`TASK_ID` 取返回值。不显式传参时 CLI 会按模型默认值兜底（例如 TGI 2 是 `1K` 和 `1:1`），本流程仍显式提交确认值。不要把 `id` / `ai_model_mark` 写给用户。

## 6. 等待终态

```bash
reelmate task wait TASK_ID --timeout 30m --json
reelmate task get TASK_ID --json
reelmate node get NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

`done_when`：任务 `status=succeeded`，节点 `task_info.status=success`，结果含至少一张图。只满足任务成功但节点仍 `processing` 时继续回读，不重复提交。超时先 `task get`。

## 7. 交付

```bash
reelmate deeplink canvas --canvas CANVAS_ID --episode EPISODE_ID \
  --navigation-source project-overview --json
```

同时可保存 `task get` / `node get` 到本地 JSON。需要本地文件时用 `task download TASK_ID --set path=outputs --json`。Agent 场景用绝对路径渲染图片预览。任务深链只用于排查。签名 URL 不写入长期文档。交付后必须输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。

## 批量生图

- 批量意图拆成单次节点回填；第 3 步参数澄清对整批只做一次。
- 清单每行至少有资产名称和提示词：名称作节点名，提示词作 `prompt`。
- 节点建好后可用 `group create` + `group execute` 一次执行整组。逐条提交时才把每个 `task_id` 交给 `task wait`。
- 整批 `done_when`：每个目标节点都满足第 6 步谓词；部分失败只重跑失败节点。
