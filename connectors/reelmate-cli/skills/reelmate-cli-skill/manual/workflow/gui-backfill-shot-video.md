# GUI 回填：Excel 分镜视频提示词清单 + 批量生视频

用户已用自己的 Skill 产出 Excel 分镜视频提示词清单，批量回填到工作台并提交生视频。不执行剧本拆分、资产提取或无限画布单节点修改。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_stage-machine.md](_stage-machine.md)、[_backfill-contract.md](_backfill-contract.md)、[_models.md](_models.md)。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/7 | 定位项目并完成 `hitl.asset-ready` | 唯一 `SP_ID`；用户确认本次引用的资产图已准备 |
| 2/7 | 先预检 `storyboard.edit`，再 `hitl.paid-video-params` | 视频模型、画幅与分辨率已列全并经用户确认；时长按本页默认 |
| 3/7 | 索取并读取 Excel | `sheet-read` 的 `data.episodes` / `data.rows` 可用 |
| 4/7 | 创建缺失分集 | 每个 `episode_no` 有 `EP_ID`；空白正式分镜已出现或已按镜号清多余 |
| 5/7 | 建正式分镜、草稿回填、可选匹配 | 目标镜号都在 `storyboard list` |
| 6/7 | 批量生视频 | 全部目标任务终态成功 |
| 7/7 | 交付 | `deeplink episode` 的 `href` 已输出 |

## 1. 定位项目并检查前置

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate workspace show --json
reelmate resource list SP_ID --json
```

无项目则停止并回到 [gui-script-video-project.md](gui-script-video-project.md)。多个候选让用户选择。`has_more=true` 时向用户说明 `data.count`，不能把首页当成整个资产库。

`hitl.asset-ready`：资产列表非空不等于用户已确认图片可用。未确认则停止，引导到 [gui-backfill-asset-image.md](gui-backfill-asset-image.md)、[gui-backfill-asset-prompt.md](gui-backfill-asset-prompt.md) 或 [gui-script-video-asset.md](gui-script-video-asset.md)。

## 2. 确认视频生成入参

先预检 `storyboard.edit`。本场景写入的是分镜草稿和 `batch-generate`，不调用 `episode match-resources`，不要预检 `episode.edit`。`error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md)「权限拒绝」停止，不要查目录，也不要提问。

```bash
reelmate team permission --require storyboard.edit --json
reelmate workspace info --workspace SP_ID --json
reelmate model list --type video --sp-type SP_TYPE --json
```

只允许 `params.storyboard_reference_video` 非空的条目。不要用画布 `supported_modes` 是否含 `universal_reference` 来筛。筛选规则见 [_models.md](_models.md)。

`hitl.paid-video-params` 按 [_hard-gate.md](_hard-gate.md) 分步列全：只列 `params.storyboard_reference_video` 非空的条目，按 `mode_order.universal_reference` 排序（筛选用分镜规则，不要用画布 `supported_modes` 是否含 `universal_reference`）。先确认视频模型，再同轮列出该模型 `storyboard_reference_video` 的全部 `ratios` 与 `resolution_options` 原序列 `label`。推荐：目录含 `Seedance 2.0 VIP` 时标它；模型确认后，选项里有 `1080P优惠版` 时标它，项目 `data.ratio` 落在所选模型 `ratios` 中时标它，否则不标推荐。画幅必须列全确认，不得因项目比例可用就跳过。数量固定 `qty=1`。时长见步骤 3「时长」规则。项目画幅不在所选模型 `ratios` 内时停下让用户改画幅或换模型。本场景无提示词模板确认项。

始终把同一 `ai_model_mark` 传给 `draft-import`。`mouth_drive`、`idle`、`is_store_draft`、`width/height`、`web_search` 不是澄清项。

## 3. 读取 Excel

用户已有官方三列表时直接索取回传。没有现成表时先生成空表：

```bash
reelmate storyboard prompt-template outputs/shots.xlsx --json
```

把 `data.path` 交给用户，说明也可直接回传已有分镜清单。只接受 `.xlsx` / `.xlsm`。不要提供十列表格样式模板或 Skill 内本地模板路径。列契约见 [_backfill-contract.md](_backfill-contract.md)。用户已经附上表格时不要再等他们填空表，进入回读。

先对用户回传文件跑：

```bash
reelmate storyboard sheet-read /ABSOLUTE/PATH/USER.xlsx --json
```

已得到 `data.episodes` / `data.rows` 则继续步骤 4。返回缺少必填列或「不符合模板」时，**不要**让用户按空模板重填，按下述 **转写与读取规则** 处理后再 `sheet-read`。

### 转写与读取规则

**1. 表头**

- 必须能映射出 **剧集号、分镜号、视频提示词**（含别名，见 [_backfill-contract.md](_backfill-contract.md)）。
- **集号 / 分镜号** 缺失时可智能补齐（例如 Sheet 名为 `第N集`、按行序补镜号），补齐值写入对应单元格，不改编其他列文案。
- **视频提示词** 语义列不存在时停止，请用户指定哪一列或补充内容；不得编造提示词。
- 除 **剧集号、分镜号、视频提示词、时长** 外，用户表其它列（角色、场景、道具、参考资产等）**一律告知用户：本次不会使用**。不要读入、不要转写进官方表。

**2. 视频提示词**

- 对提示词正文 **不作任何格式要求**（不要求【时长】【参考资产】等）。
- 已有单一「视频提示词 / 提示词」列：**原样复制**到官方「视频提示词」，禁止增删改、禁止加标签、禁止把时长列拼进提示词。
- 多个画面描述列（如「画面描述 + 台词」）：**默认合并为一列**，按表头从左到右 **仅直接拼接各单元格原文**，不插入列名、标点、分隔符、标签或任何额外字符，不改变原文内部格式。

**3. 时长**

- **场景一（文件里有时长）**：`sheet-read` 从 **单独「时长」列**（若存在）或 **视频提示词中的自然表述** 解析秒数；优先时长列。转写官方表时，可保留用户时长列为第四列，**不要**为写时长而修改视频提示词单元格。
- **场景二（文件里没有任何时长）**：向用户索取 **整批统一默认时长**，提交 `draft-import` 时传 `--set duration=SECONDS`；若仅部分行缺时长，按行号 `needs_input` 补问。

**4. 转写产物**

1. 用宿主表格工具读用户工作簿全部有数据的 Sheet。
2. 写入 `outputs/shots.xlsx` 的「分镜提示词清单」第 5 行起；表头用 `prompt-template` 生成的官方三列表头，**可按行附带「时长」第四列**（与用户时长列一致，不写入提示词）。不要动「填写示例」。
3. 对转写后的表或仍含时长列的用户表再跑 `sheet-read`，只消费本次 JSON。

转写禁令：不编剧集号、分镜号；不默认整表属于第 1 集（整表无集号列时问一次）；不按镜号或文案相似合并行。同一集内镜号重复、整数非法时停止。后续 `draft-import` 只用 `sheet-read` 消费过的表路径。

## 4. 创建缺失分集

```bash
reelmate episode list --workspace SP_ID --json
reelmate episode split-list SP_ID --json
```

典型项目没有导入过剧本，`split-list` 返回 400 `740015` 是正常结果，按“没有拆分结果”继续。将 `sheet-read.data.episodes[]` 与现有分集对照：优先按有效正整数 `sort`；`sort` 为 0 时按唯一且完全一致的分集名称。存在拆分结果却找不到唯一匹配时停止。只为缺失分集生成 `episodes.json`，先预演再提交。提交后必须重新 `episode list`。

新建分集后服务端会异步补一条空白正式分镜，实测滞后 35～45 秒。`episode list` 已返回分集时它往往还没出现。建集后先等这条空白分镜出现再进步骤 5，或在步骤 5 末尾按 Excel 镜号复核总数，用 `storyboard batch-delete` 清掉多余空白分镜。紧接着用空的 `storyboard list` 去 `batch-add` 会多出一镜。

## 5. 创建正式分镜并回填草稿

逐集 `storyboard list`，以 Excel 镜号为目标：复用镜号相同的正式分镜，只为缺失镜号 `storyboard batch-add`。读到的列表必须已经包含步骤 4 的异步空白分镜。

```bash
reelmate storyboard draft-import EP_ID --workspace SP_ID \
  --set file=/ABSOLUTE/PATH/SHOTS.xlsx --set episode_no=EPISODE_NO \
  --set ai_model_mark=VIDEO_MODEL --dry-run --json
```

`ai_model_mark` 必须是步骤 2 确认的模型。不传 `duration` 时逐镜使用 `sheet-read` 解析到的时长（时长列或提示词）。场景二整批统一时长时必须传 `--set duration=`。同一集不要重复执行 `draft-import`：本流程通常没跑过 `episode parse`，该接口恒为空列表，重跑会给同一镜号留下多条草稿。要改内容时用 `storyboard draft-batch-update` 按 `esd_id` 改（改时长必须同时传 `--set ai_model_mark=`），或先 `draft-delete` 再导入。`succeeded[].esd_id` 必须留存。

提示词中显式参考资产名单解析失败（缺失、重名、未定稿或无图）时返回 `needs_input`。无显式名单时从正文匹配已定稿资产名；匹配不上仍写入原样提示词和空 `images`。

回填后还要把同一规整提示词和时长同步到对应正式分镜：`storyboard edit` 写 `desc`，`storyboard ext` 写 `storyboard_description`、`video_gen_prompt` 和 `duration`。两步都先 dry-run。

显式名单或正文匹配资产成功时，`draft-import` 已按资产名写好 `images`，`match-assets` 可跳过：本流程没跑过 `episode parse` 时它会退化到正式分镜列表，预演里常见 `esd_id=""`、`medias=0`。只有导入后仍无参考图、需靠 AI 打标时才执行：

```bash
reelmate storyboard match-assets EP_ID --workspace SP_ID --dry-run --json
```

`failed[]` 非空时只重跑失败镜号。匹配仍失败时停止，列出失败镜号让用户选择，不自行改提示词。不用 `episode match-resources` 或画布 `script asset-match` 替代。

逐集核对 `storyboard list` 中目标镜号都存在即可宣称 5/7 完成。`desc` / `video_gen_prompt` 为空不得停止，也不得因此拒绝 `batch-generate`。不要等 `link-draft` 带回提示词或图。`link-draft` 的 `images` 为空不得当成导入失败（步骤 6 提交前为空是中间态；草稿详情仍可能有图）。`episode parse-result` 返回 `status=0` 或空列表时，不能据此宣称 GUI 已回填。

## 6. 批量提交生视频

```bash
reelmate credits balance --json
reelmate credits estimate --set alg_code=refer_image_to_video \
  --set 'params="{\"ai_model_mark\":\"VIDEO_MODEL\",\"duration\":SECONDS,\"resolution\":\"RESOLUTION\",\"ratio\":\"RATIO\",\"qty\":1}"' \
  --json
```

`params` 必须是 JSON **字符串**。按 [_hard-gate.md](_hard-gate.md) 积分展示策略把预计消耗、余额和积分明细链接返回给用户确认后再提交。对每集显式传该集要生成的全部镜号，`nums` 不能为空：

```bash
reelmate storyboard batch-generate EP_ID --workspace SP_ID \
  --set ai_model_mark=VIDEO_MODEL --set generate_type=1 \
  --set resolution=RESOLUTION --set ratio=RATIO --set qty=1 \
  --set 'nums=[1,2]' --dry-run --json
```

只收集非空 `task_id`，然后只做一轮聚合 `task wait`。未命中的 `task_id=""` 不是失败。`is_store_draft=true` 会在这一次请求里把草稿物化到正式分镜；提交前 `link-draft` 读到 `images` 为空属于正常中间态。`duration` 已在草稿导入时写入，不属于 `batch-generate` 入参。

`done_when`：所有目标任务进入成功终态。超时先 `task get`；部分失败只重跑失败镜号。

## 7. 交付

```bash
reelmate storyboard list EP_ID --json
reelmate deeplink episode --workspace SP_ID --json
```

交付项目总剧集页 `data.href`、各集 `EP_ID` 与实际提交的镜号、聚合等待结果，并输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。`storyboard total-list` 不能作为完成判据。链接必须由 `deeplink episode` 生成。不自动合并、导出或下载。
