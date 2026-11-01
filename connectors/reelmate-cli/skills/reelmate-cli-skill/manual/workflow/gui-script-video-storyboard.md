# GUI 环节 4：拆分镜与视频生成

只在当前包为 `storyboard` / `render` 或视频未生成时读取。前置：项目已创建、剧本已解析，并完成 `hitl.asset-ready`。缺项回环节 1/2/3。模型现查 [_models.md](_models.md)。从画布剧本交接进入时同样走本页 1/3、2/3；分镜拆解成功后必须 `hitl.shot-result-confirm`，未确认不得 `storyboard batch-generate`。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/3 | 创建全部正式剧集 | `episode list` 覆盖全部拆集结果；收集 `ALL_EP_IDS` |
| 2/3 | 先预检 `episode.edit` 与 `storyboard.edit`，再确认视频参数、匹配并拆解 | 每集 `parse-result` 为 `status=2` 且 `list` 非空；本轮已跑不带 `--episode` 的 `deeplink episode` 与带 `--episode` 的 `deeplink episode` 且两条 `href` 均非空 |
| 3/3 | `hitl.shot-result-confirm` 后逐集 `batch-generate` | 全部目标 `task wait` 终态成功；不带 `--episode` 的 `deeplink episode` 与带 `--episode` 的 `deeplink episode` 均已输出 |

不得把首集成功描述为全项目成功。

## 1. 批量创建剧集

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate episode split-list SP_ID --json
reelmate episode list --workspace SP_ID --json
```

正式剧集不存在时，把全部拆集结果一次落成剧集：

```bash
reelmate episode batch-create --workspace SP_ID --set @episodes.json --dry-run --json
reelmate episode batch-create --workspace SP_ID --set @episodes.json \
  --idempotency-key KEY --json
reelmate episode list --workspace SP_ID --json
```

`episodes.json.items[]` 包含 `sort`、`name`、`s_script_id`。收集全部 `ALL_EP_IDS`，后续不得只处理第一集。

## 2. 查询分镜参数并匹配、拆解

先预检 `episode.edit`，再预检 `storyboard.edit`。任一返回 `error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md)「权限拒绝」停止，不要查目录，也不要进入 `hitl.paid-video-params`。

```bash
reelmate team permission --require episode.edit --json
reelmate team permission --require storyboard.edit --json
reelmate workspace info --workspace SP_ID --json
reelmate model list video --sp-type MODEL_SP_TYPE --json
```

`MODEL_SP_TYPE` 只给 `model list`（动漫/真人二分类，海外仿真人也是 `2`）。`episode prompt-templates` **不要传 `--sp-type MODEL_SP_TYPE`**：Web 用项目 `currentSeriesDetail.sp_type`（海外仿真人是 `3`）拉目录，有 `--workspace` 时 CLI 会自己读。把 `2` 传给海外项目会列出国内「天幕分镜大师1.3」，选中后拆分镜解析出 0 条。

`hitl.paid-video-params` 按 [_hard-gate.md](_hard-gate.md) 分步列全：先确认视频模型，再同时查询三类完整模板目录，按下节合并成一个模板确认项，与画幅、分辨率同轮确认。模板来源由选中条目确定。改选模型时清除旧模板、画幅及分辨率选择，重新查询并确认。

并行执行以下三条只读查询；工作流模版和一步流都与视频模型无关：

```bash
# AI拆分镜工作流模版
reelmate episode prompt-templates --workspace SP_ID --set source=workflow --set all=true --json
# 自定义工作流：AI拆分镜一步流模版
reelmate episode prompt-templates --workspace SP_ID --set source=team-onestep --set lang=zh-CN --set all=true --json
# 官方工作流
reelmate episode prompt-templates --workspace SP_ID --set source=official --set model=VIDEO_MODEL --json
```

`lang` 只用于一步流，与 Web 当前界面语言一致，默认 `zh-CN`；查询与匹配必须沿用同一个值。工作流的 `workflow_id` 与一步流的 `uk_id` 都写入 `prompt_ukid`，但 `prompt_use_type` 分别是 `3` 和 `2`，不得混用。

- 视频模型：列出 `params.script_to_scene_refer` 非空且 `visible=true` 的全部条目，按 `mode_order.script_to_scene_refer` 排序。该子集展示名含 `Seedance 2.0 VIP` 时标推荐；禁止把列表第一项当默认。不要用 `params.storyboard_reference_video` 非空或画布 `supported_modes` / `mode_order.universal_reference` 判断能不能拆分镜。本场景 0 条时停止并说明当前项目没有可拆分镜的参考生视频模型。候选里 `need_vip=true` 时，账号没有 VIP 会导致后面的自动拆分镜静默失败或 400。
- 画幅：列出所选模型 `params.storyboard_reference_video.ratios[]`；项目 `data.ratio` 落在其中时标推荐。
- 官方提示词模板：列出所选模型对应 `resolved.candidates[]` 的全部 `name` 原文；推荐用当次 `resolved.default_name`，禁止写死模板名。`candidates` 为空时按下节空目录规则处理，不猜 `prompt_type`。
- AI拆分镜工作流模版：列出 `source=workflow` 完整 `list[]` 的全部 `name` 原文，不按视频模型过滤、不人为推荐第一项。同名项保留独立序号，可附 `description` 帮助区分；内部保存序号到字符串 `workflow_id` 的映射，不能把名称当 ID。`total_points` 不展示给用户，也不能当作计价模板 ID。
- 团队一步流模板：列出完整 `list[]` 的全部 `name` 原文，不按视频模型过滤、不人为推荐第一项。同名项保留独立序号，可附描述或语言模型帮助区分；内部保存序号到字符串 `uk_id` 的映射，不能把名称当 ID。目录完整性与空目录按下节处理。团队模板内的 `language_model` 由模板配置决定，不当成视频模型再提交。
- 分辨率：按所选模型 `params.storyboard_reference_video.resolution_options` 原序列 `label`，有 `default_resolution` 时把对应 label 标推荐。`--set resolution=` 交展示名，由 CLI 解析。不要误用 `params.generation.first_frame`，也不要改走 `storyboard batch-generate-video`。
- 数量：固定每镜 `qty=1`。

接口把某个模板标进某个模型的候选列表，不代表这个组合在后端真的跑得通。

### 模板合并与选择

三类查询均成功且目录完整后，标题写「请选择提示词模板：」，在同一确认项中按「AI拆分镜工作流模版」「自定义工作流—AI拆分镜一步流模版」「官方工作流」的顺序分组，组内保持接口顺序。全列表连续编号，每个模板独占一行，保留名称原文；推荐标记不改变分组顺序。选择器不能保留分组、顺序或全部选项时，按 [_hitl-present.md](_hitl-present.md) 使用文本回退。

某类成功返回空目录时，在该组标明「暂无可用模板」，仍让用户从其它组明确选择；三类均空时停止。任一查询失败或工作流、一步流目录 `has_more=true` 时，先补查到成功且完整，再展示可选列表；不把失败当空目录、不静默丢弃该组。

内部保留每个序号到来源与模板标识的映射，同名项不去重，分组标明来源，必要时附描述或语言模型消歧。用户仅回复重名名称时，请其用序号明确选择。选定后先清除旧 `prompt_type` / `prompt_ukid`：工作流条目设 `prompt_use_type=3`，将字符串 `workflow_id` 写入 `prompt_ukid`；一步流条目设 `prompt_use_type=2`，将字符串 `uk_id` 写入 `prompt_ukid` 并沿用查询 `lang`；官方条目设 `prompt_use_type=1`，将该条目的模板 ID 写入 `prompt_type`。不再追加来源确认，提交时模板标识互斥。

### 提交资产匹配

确认后一次提交全部剧集的资产匹配。批量匹配是组合任务：服务端在每集资产匹配完成后自动继续拆分镜，Web 没有资产匹配确认环节。提交匹配即同时授权资产匹配和拆分镜两笔费用。

提交前逐集取得本集原始剧本文本，生成资产匹配和拆分镜两类账单，在同一条确认消息中展示各集两项小计、总计、首次权益、余额和积分明细链接，并写明「提交后服务端会在匹配完成后自动拆分镜，两笔费用都会发生」。`text` 必须是原始提交文本，不得改用提示词或摘要：

```bash
reelmate credits estimate --set scenario=asset_match --set text='EPISODE_SCRIPT' --json
reelmate credits estimate --set scenario=script_split --set text='EPISODE_SCRIPT' \
  --set language=LANGUAGE --set prompt_tpl_id=PROMPT_TPL_ID \
  --set storyboard_mode=true --json
reelmate credits balance --json
reelmate deeplink credits --json
```

拆分镜计价模板 ID：官方来源取所选官方模板 ID（即提交的 `prompt_type`），匹配后 `episode get` 回读的 `prompt_tpl_id` 与之相同。团队一步流在提交前取不到可验证的计价模板 ID，拆分镜一项写「当前无法在提交前取得拆分镜计价依据」，禁止拿 `uk_id` 或 `workflow_id` 代替，也不借用其它模板价格；资产匹配账单、余额和积分明细链接照常展示。

全部账单 `available=true` 时相加得到本次总计；任一项 `unavailable` 时逐集展示已知结果和不可估算原因，不编总计。

```bash
reelmate episode match-resources --workspace SP_ID \
  --set 'ep_ids=["EP_ID_1","EP_ID_2"]' \
  --set generate_mode=1 --set refer2video_model=VIDEO_MODEL \
  --set prompt_use_type=1 --set prompt_type=PROMPT_TYPE \
  --dry-run --json
```

上例为官方来源；团队一步流把模板参数替换为 `--set prompt_use_type=2 --set 'prompt_ukid="TEAM_UK_ID"' --set lang=zh-CN`，移除 `prompt_type`。AI拆分镜工作流模版替换为 `--set prompt_use_type=3 --set 'prompt_ukid="WORKFLOW_ID"'`，不传 `lang`。只提交 ID，不传 `prompt_template` / `language_model` / `total_points`。CLI 的预演及正式提交会重新验证当前启用目录；模板已失效时回到来源内重新选，不擅自换模板。

确认后用唯一幂等键提交。批量响应虽有 `data.task_id`，但不能由通用 `task get/wait` 稳定查询；逐集轮询 `episode match-result` 至 `data.status=2`（资产匹配完成），再逐集轮询 `episode parse-result` 至终态。拆分镜由组合任务自动启动，不要逐集调用 `episode parse`。

```bash
reelmate episode match-result EP_ID --json
reelmate episode parse-result EP_ID --workspace SP_ID --json
reelmate episode get EP_ID --json
```

### 自动拆分镜未启动时补调

只有同时满足以下条件，才对该集补调一次 `episode parse`：`match-result` 为 `status=2`，`episode get` 的 `is_any_parse=false`，`parse-result` 仍为 `status=0`，且间隔一段时间复查后三者仍成立。补调费用已在提交匹配时一并确认；补调不传 `character_importance` / `scene_importance` / `prop_importance`，仍须先预演：

```bash
reelmate episode parse EP_ID --workspace SP_ID --dry-run --json
reelmate episode parse EP_ID --workspace SP_ID --idempotency-key KEY --json
```

`is_any_parse=true`，或 `parse-result` 为 `status=1`/`2` 的剧集禁止调用 `episode parse`，否则会重复下单扣费。

### 拆分镜结果判定

每集都必须 `parse-result` `status=2` 且 `list` 非空才算成功。`parse-result.list[]` 里的分镜此时还是草稿（字段是 `esd_id`）。成功时 `success_num` 可能为 0、`episode get` 的 `split_task_id` 可能为 `"0"`、草稿 `video_prompt` 可能为空，这些都不作为失败判据。失败不得回退到旧的“单集匹配”链路。

- `status=2` 但 `list` 为空或 `null`：判为拆分镜失败并停止。常见原因是 `match-resources` 选的模型与模板组合在后端不兼容。选项：新建一集换模板或换模型后重走匹配。批量提交多集前先用其中一集验证模型+模板组合。
- `status=3`：按 [episode.md](../../commands/episode.md) 的 `episode parse-retry` 处理；返回 `740015` 表示服务端没有可重试的任务，同样新建一集换配置重走匹配。

### 拆分镜后可选补充缺失资产

全部剧集拆分镜成功后，按 `episode match-result` 统计缺失资产。存在缺失项时，在交付深链的同一条消息里告知数量，并提供可选的智能补充或重新匹配，细节读取 [_storyboard-asset-match.md](_storyboard-asset-match.md)。这一步不是拆分镜前置门；用户不选择时直接进入步骤 3 的分镜确认。

全部剧集拆解成功后，本轮先交付两条深链（缺一不可）。第一集 `EP_ID` 取 `episode list` 工坊剧集里 `sort` 最小的那条（通常是第 1 集）：

```bash
reelmate deeplink episode --workspace SP_ID --json
reelmate deeplink episode --workspace SP_ID --episode FIRST_EP_ID --json
```

只消费当次 `data.href` 或 `links[0].href`。项目页应为 `/episode-list?sp_id=SP_ID&tab=workshop`，首集链接应为 `/series-manage/episode/FIRST_EP_ID?navigationSource=project-overview`。不要手拼 URL，也不要用 `deeplink project` 的总览地址代替项目页。任一条 `ok=false` 或 `href` 为空时先补齐 `missing[]`。

## 3. 分镜确认与批量视频生成

`hitl.shot-result-confirm`：同一条用户可见消息必须带上步骤 2 的**项目页** `href`、**首集链接** `href`，再问是否确认分镜单。两条链接都没有不得提问。未确认不得生成视频。确认后沿用步骤 2 已确认的视频模型、分辨率、项目画幅和 `qty=1`。

Web“立即批量生成”对应 `storyboard batch-generate`（`is_store_draft=true` 会在同一次付费操作中创建正式分镜并提交视频任务），不是 `storyboard batch-generate-video`。

每集显式构造 `nums`（取草稿在当前完整列表中的一基序号，不能传空数组），先执行 `storyboard batch-generate --dry-run --json`。预演会按实际草稿的模型、时长、分辨率、画幅、参考图数量、提示词长度和 `qty` 分组生成 `data.credits_estimate.requests[]`；把所有剧集的请求组合后交给 `credits estimate`，不得再手拼一份通用 `refer_image_to_video` 参数：

```bash
reelmate storyboard batch-generate EP_ID --workspace SP_ID \
  --set ai_model_mark=VIDEO_MODEL --set generate_type=1 \
  --set ratio=RATIO --set resolution=RESOLUTION --set qty=1 \
  --set 'nums=[1,2]' --dry-run --json
reelmate credits estimate --set @video-estimate.json --json
reelmate credits balance --json
reelmate deeplink credits --json
```

按 [_hard-gate.md](_hard-gate.md) 展示价格分组数、全部选中分镜数、每组参数、业务数量、小计和汇总总价，再展示余额和积分明细链接。用户确认后每集使用唯一幂等键提交。响应会为该集全部正式分镜返回记录，只有 `nums` 命中的记录带非空 `task_id`；未选中记录的 `task_id=""` 不代表失败。只收集非空任务 ID 并统一等待：

```bash
reelmate task wait TASK_ID_1 TASK_ID_2 --timeout 30m --json
```

提交成功后先用 `storyboard list EP_ID --json` 确认正式分镜已生成。参考图是否生效只看 `link-draft` 的 `images` 是否非空；时长和首帧也可读 `link-draft`，`video_gen_prompt` 为空不得当作失败。生视频只走 `storyboard batch-generate`。所有目标任务终态成功后再次跑：

```bash
reelmate deeplink episode --workspace SP_ID --json
reelmate deeplink episode --workspace SP_ID --episode FIRST_EP_ID --json
```

两条 `href` 都要写进用户可见回复。完成总结的「剧厂项目链接」写项目页 `href`，同一条总结后追加「首集链接」写该集 `href`。然后输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。

## 失败恢复

- 异步超时先查询原任务；已有任务不得重新提交。
- 批量部分失败只重跑失败项。
- 模型、风格、题材或模板不可见时重新查询目录。
- `preset-list`、`model list` 和 `prompt-templates` 只在本轮参数确认中有效。
- 任一续跑点先重新 `workflow detect`；远端已前进时不得拉回旧阶段。
- 主资产、子资产或分镜结果未确认时停在对应 HITL。
