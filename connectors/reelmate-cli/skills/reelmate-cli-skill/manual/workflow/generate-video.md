# 无限画布：生成或调整视频

无限画布视频生成：用户提供视频提示词，可选一张本地图片。资产清单批量生视频不在本流程。画布分镜 Excel 无独立场景，停止并报缺口。制片工坊多环节串联或分镜批量生视频改走 [gui-script-video.md](gui-script-video.md) 或 [gui-backfill-shot-video.md](gui-backfill-shot-video.md)。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_models.md](_models.md)。

## 当前包

| 探测 | 包 | 入口 |
|---|---|---|
| 没有工作区或画布 | `create-blank` | 步骤 1～7 |
| 已有画布且要新生成一条视频 | `create-blank` | `node list` 后从步骤 3 继续，新建 `video` 节点 |
| 已有画布且要改或重跑已有视频节点 | `edit-existing` / `regenerate` | [无限画布分诊](#无限画布分诊) |

```bash
reelmate node list --workspace WORKSPACE_ID --canvas CANVAS_ID --json
reelmate node get NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

## 步骤表（create-blank）

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/7 | 登录并绑定项目 | 已登录；已绑定无限画布 `WORKSPACE_ID`。无目标画布时先 `workspace list` 让用户选 `creation_mode=2` 的项；用户要新建或没有候选时，按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`：复述创作模式「无限画布」，确认剧目类型与画面比例。已绑定制片工坊项目不得直接当无限画布使用 |
| 2/7 | 创建画布 | 已有 `CANVAS_ID` |
| 3/7 | 先预检 `project.edit`，再 `hitl.paid-video-params` | 模型、时长、画幅、分辨率已经用户确认，且模型当次可见并支持该模式 |
| 4/7 | 创建并回填视频节点 | `node get` 与确认值一致；有图时 `referenceAssets` 含本次 `FILE_ID` |
| 5/7 | 提交生成 | 返回 `task_id`；有图时命令含 `mode` 与 `images` |
| 6/7 | 等待终态 | 任务 `status=succeeded`，节点 `task_info.status=success`，结果含可预览视频 |
| 7/7 | 交付 | 已输出画布深链 `href`；Agent 场景另有媒体预览 |

数量固定 `qty=1`。写操作带 `--json` 和 `--idempotency-key`。

## 无限画布分诊

不走阶段机，不先执行 `workflow detect`，不套 GUI 环节 1→4。

| 用户意图 | 执行方式 | 边界 |
|---|---|---|
| 在已有画布新生成一条视频 | 从步骤 3 继续，新建空白 `video` 节点 | 不覆盖已有节点 |
| 修改已有视频节点的提示词或参数 | `node edit NODE_ID --set ... --json` | 编辑不会自动提交生成 |
| 对已有视频节点重新生成一次 | 先按步骤 3 确认参数，再执行一次 `node generate video` | 提交前确认，避免重复扣费 |
| 多条视频一起生成 | `group create` 后 `group execute` | 清单任务不逐条 `node generate` |

`group execute` 不交给 `task wait`。成功后交付 `node get` 与 `deeplink canvas`，不描述为阶段推进。

## 1. 登录并绑定项目

按 [_bootstrap.md](_bootstrap.md) 登录。无限画布场景只绑定或新建 `creation_mode=2` 的项目：先 `workspace list` 把已有画布项目列给用户选；没有候选或用户明确要新建时 `creation_mode=2`，按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`：复述创作模式「无限画布」，剧目类型与画面比例用网页展示名（国内仿真人剧、海外仿真人剧、2D/3D动漫；`9:16 竖屏`、`16:9 横屏`）。已绑定制片工坊项目不能直接当无限画布使用。项目画面比例是步骤 3 视频画幅的推荐值（须仍列出该模型全部 `ratios`），不是 CLI 未传参时的兜底值。

## 2. 创建画布

按 [_bootstrap.md](_bootstrap.md) 创建画布。

## 3. 查询模型并确认参数

重跑回到本步时同样先预检。先预检 `project.edit`，通过后再查模型目录并进入 `hitl.paid-video-params`。`error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md)「权限拒绝」停止。

```bash
reelmate team permission --require project.edit --json
reelmate model list --sp-type MODEL_SP_TYPE --json
```

先定模式：只给提示词 → `text2video`；一张图 → `image2video`（首帧语义为 `first_frame`）；首尾帧 → `first_last_frame`；多素材参考 → `universal_reference`。只列 `visible=true`、`supported_modes` 含目标模式且对应规则非空的模型。模型不支持该模式时 CLI 直接报错，不自动换模式或换模型。筛选规则见 [_models.md](_models.md)。

`hitl.paid-video-params`（无限画布）按 [_hard-gate.md](_hard-gate.md) 分步列全：先按 `mode_order` 目标模式列全部视频模型并确认，再按该模型规则同轮列出画幅、分辨率、时长：

| 参数 | 剧厂推荐 | 来源 |
|---|---|---|
| 视频模型 | 目标模式候选含 `Seedance 2.0 VIP` 时选它 | 当次目录 |
| 分辨率 | 有 `default_resolution` 时用对应 `label`；选项含 `1080P优惠版` 时标它 | 所选模式 `resolution_options` 原序列 `label` |
| 画幅 | 项目 `data.ratio` 且落在所选模型 `ratios` 中时标推荐 | 必须列出该规则全部 `ratios`；键缺失或项目画幅不在枚举中时不标推荐。新建项目画面比例与未传参时的 CLI 兜底无关 |
| 时长 | 所选模式默认档；无默认则用 `durations` 第一项 | 用户已提到时长且落在 `durations` 中则取该值；合法值取所选模式 `durations`，不要写死 5 秒 |

`1080P优惠版`、`480P` 只出现在部分模型的参考生视频 `resolution_options` 里。画布图生视频下 Seedance 2.0 VIP 只有 `720P` 与 `1080P`。`ratios` 非空时提交值必须落在其中；为空表示该模式没有画幅枚举。用户指定的模型或参数不可用时反馈实时目录，不自动替换。

## 4. 创建视频节点

```bash
reelmate node create video --workspace WORKSPACE_ID --canvas CANVAS_ID --set name=NODE_NAME \
  --idempotency-key CREATE_KEY --json
reelmate node edit NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --set prompt=PROMPT --set model=VIDEO_MODEL --set count=1 \
  --set settings="{\"ratio\":\"RATIO\",\"resolution\":\"RESOLUTION\",\"duration\":DURATION}" \
  --idempotency-key FILL_KEY --json
```

`NODE_NAME` 用用户名称，否则从提示词提炼短名。本地图片先 `upload`，再 `material add --node NODE_ID --material-type image --source upload`。`FILE_ID` 只取 upload 成功 JSON；审核未通过时停止。不为附件额外创建图片节点。

`node generate video` 不会自动把 `referenceAssets` 转成生成入参。图片要生效，步骤 5 必须显式传 `--set mode=image2video --set 'images=[{"uri":"FILE_ID"}]'`。多素材改用 `universal_reference`，结构见 [node.md](../../commands/node.md)。

`done_when`：`node get` 中名称、prompt、模型、时长、画幅、分辨率与确认值一致；有图时 `referenceAssets` 含本次 `FILE_ID`。

## 5. 提交视频生成

必须复用步骤 3～4 同一组变量。指定 `--node` 后 CLI 先合并写回；写回失败时不提交。

```bash
reelmate node generate video --workspace WORKSPACE_ID --canvas CANVAS_ID --node NODE_ID \
  --set ai_model_mark=VIDEO_MODEL --set prompt=PROMPT \
  --set duration=DURATION --set resolution=RESOLUTION --set ratio=RATIO \
  --set qty=1 --idempotency-key GENERATE_KEY --json
```

有图时同一条命令追加：

```bash
  --set mode=image2video --set 'images=[{"uri":"FILE_ID"}]'
```

`TASK_ID` 取返回值。提交前先 `--dry-run`，并按 [_hard-gate.md](_hard-gate.md) 积分展示策略展示预估消耗、余额和积分明细链接，用户确认后再付费提交。不显式传参时 CLI 兜底 `duration=5`、`resolution=720p`、`ratio=16:9`。本流程必须显式提交步骤 3 确认值；项目画面比例（常为 `9:16`）与该兜底无关，漏传会落到 `16:9`。`--set ai_model_mark=` 填写目录展示名；不要同时传两个模型字段，也不要把提交标识写给用户。

## 6. 等待终态

```bash
reelmate task wait TASK_ID --timeout 30m --json
reelmate task get TASK_ID --json
reelmate node get NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

`done_when`：任务 `status=succeeded`，节点 `task_info.status=success`，结果含至少一条可预览视频。节点仍 `processing` 时继续回读，不重复提交。超时先 `task get`。

## 7. 交付

```bash
reelmate deeplink canvas --canvas CANVAS_ID --episode EPISODE_ID \
  --navigation-source project-overview --json
```

需要本地文件时用 `task download TASK_ID --set path=outputs --json`。Agent 场景用绝对路径渲染媒体预览。任务深链只用于排查。签名 URL 不写入长期文档。交付后必须输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。
