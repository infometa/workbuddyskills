# GUI 回填：资产提示词清单 + 批量生图

用户填写或已持有角色、场景、道具提示词清单，回填到资产操作台并批量生图。支持主形态和子形态。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_stage-machine.md](_stage-machine.md)、[_backfill-contract.md](_backfill-contract.md)、[_models.md](_models.md)。

主形态定稿必须排在子形态生图之前。这是流程顺序：批量定稿主形态后，Web 会把该父级下的子形态勾进待生成列表，同时定稿确定“这一组用哪张主图”。接口只要求参考图是有效 `file_id`。

本流程对齐资产页空态中的“生成角色 / 生成场景 / 生成道具”，不调用“AI 智能提取资产”，因此不需要剧本、`et_id`、`eed_id`、`draft-import` 或 `batch-draft-generate`。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/10 | 定位唯一项目 | 已确定唯一 `SP_ID` |
| 2/10 | 先预检 `resource.edit`，再 `hitl.paid-image-params` | 六项已确认或明确不设 |
| 3/10 | 生成官方模板；收下用户表 | 已有官方空表路径；用户已回传 `.xlsx`（官方表或自带清单均可） |
| 4/10 | 转成官方格式后 `prompt-sheet-read` | `data.batches[]` 可用；缺数据已补问并重跑 |
| 5/10 | 能力门 + 主形态 `resource add` | 每个主形态有真实 `resource_id` |
| 6/10 | 主形态 `resource generate` | 目标记录 `task_status=3` 且有 `file_id`；本轮已跑 `deeplink project` 且 `href` 非空；看图再跑本轮 `deeplink asset` |
| 7/10 | `hitl.asset-result-confirm` 后主形态定稿 | 确认问句与本轮项目页 `href` 在同一条用户可见消息里；目标主形态 `status=2`；需存主体的角色有 `subject_id` |
| 8/10 | 子形态创建并图生图 | 无子形态则跳到 10；有则目标子形态 `task_status=3` 且有 `file_id`；本轮已跑 `deeplink project` 且 `href` 非空；看图再跑本轮 `deeplink asset` |
| 9/10 | `hitl.asset-result-confirm` 后子形态定稿 | 确认问句与本轮项目页 `href` 在同一条用户可见消息里；目标子形态 `status=2`；需存主体的角色有 `subject_id` |
| 10/10 | 交叉证明并交付 | 见下方 `done_when` |

`resource list` / `generate-list` 先看 `has_more`。

## 1. 定位项目

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate workspace show --json
```

无项目则停止并回到 [gui-script-video-project.md](gui-script-video-project.md)。多个候选让用户选择。本流程不要求已有剧集。

## 2. 确认图片生成入参

这是本流程唯一的参数澄清节点，排在取表和写入之前。先预检 `resource.edit`，通过后再查目录和提问。`error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md)「权限拒绝」停止。

```bash
reelmate team permission --require resource.edit --json
reelmate workspace info --workspace SP_ID --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=1 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=2 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=3 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=theme --set lang=zh-CN --json
reelmate resource generate-image-types --json
reelmate model list --type image --sp-type MODEL_SP_TYPE --json
```

`reelmate resource --help` 没有 `preset-list` 或 `generate-image-types` 时停止。`preset-list` 的 `lang` 一律 `zh-CN`，海外仿真人项目也一样。`MODEL_SP_TYPE` 从 `workspace info` 推出，见 [_bootstrap.md](_bootstrap.md)。风格目录按三类分别查询，HITL 只展示一份风格展示名（按名称映射到各类 `uk_id`）。模型现查 [_models.md](_models.md)。角色构图现查 `reelmate resource generate-image-types --json`，只展示返回的 `list[].name`。

`hitl.paid-image-params` 按 [_hard-gate.md](_hard-gate.md) 分步列全：先同轮确认风格、题材、角色构图、图片模型。图片模型只列 `params.studio_asset_image` 非空且 `visible=true` 的条目，按 `mode_order.studio_asset_image` 排展示名；角色、场景、道具共用这一套。禁止再按 `mode_order` 目标模式或画布 `text2image` 当本步成员判定。本场景 0 条时停止并说明当前项目没有可资产生图的模型，不改走画布清单。候选展示名含 `TGI 2` 时标推荐；禁止把列表第一项当默认（常见第一项是 TGI 2.5 Flare）。模型确认后再按所选模型 `params.generation.text2image` 列**一次**画幅，并按 `resolution_options` 原序列 `label` 列分辨率；本轮不问画质。对齐 Web 批量生成弹窗：比例条只有一条，角色/场景/道具共用，提交同一 `radio_ui`，不要拆成角色画幅/场景画幅/道具画幅。风格和题材只提交 `uk_id`；场景允许不设置时把「不设置」写成列表一项。构图用 `generate-image-types` 返回的 `recommended`；模型确认后，画幅有 `16:9`、选项含 `2K` 时再标推荐。新建项目的画面比例不是资产生图画幅：项目可以是 `9:16`，本步仍按模型 `ratios` 列全并按上面规则标推荐。

## 3. 生成官方模板并收下用户表

```bash
reelmate resource prompt-template outputs/asset-prompts.xlsx --json
```

把 `data.path` 交给用户，说明也可直接回传已有资产清单。模板由 Go 代码实时生成，字段见 [_backfill-contract.md](_backfill-contract.md)。用户已经附上 `.xlsx` 时不要再等他们填空表，进入步骤 4。

## 4. 转成官方格式再回读

先对用户回传文件跑：

```bash
reelmate resource prompt-sheet-read /ABSOLUTE/PATH/USER.xlsx --json
```

已得到 `data.batches[]` 则继续步骤 5。官方五列与四列方言（`资产类型` / `资产名称` / `主子资产属性` / `生图提示词`，形态填 `主` 或 `子`）由 CLI 直接读取，不必转写。返回缺少必填列或「不符合模板」时，**不要**让用户按空模板重填，按下述转写：

1. 用宿主能跑的表格工具读用户工作簿（如 Python `openpyxl` / `pandas`）。读全部有数据的 Sheet，不要只看第一页。
2. 把每一行映射到官方五列后，写入步骤 3 生成的 `outputs/asset-prompts.xlsx` 的「资产提示词清单」，从第 5 行起填；不要改表头，不要动「填写示例」。超过 100 行继续往下写。已有官方空表时用 `--set overwrite=true` 重新生成再写入，避免脏文件。
3. 对转写后的官方表再跑 `prompt-sheet-read`。只消费这一次的 `data.batches[]`。

列映射（有则用，无则留空并按契约补问）：

| 官方列 | 用户表常见来源 |
|---|---|
| 资产类型（必填） | `类型` / `资产类型`；Sheet 名或单元格为 `角色`/`场景`/`道具` |
| 资产名称（必填） | `名称` / `资产名称` / `资产名` / `角色名` / `场景名` / `道具名` |
| 形态（必填） | `形态` / `主子形态` / `主子资产属性`；取值 `主形态`/`子形态` 或 `主`/`子` |
| 所属主形态名称（子形态必填） | `所属主形态` / `主形态名称` / `父资产` / `所属角色`；主形态留空。四列方言可无此列：CLI 用子名称前缀绑唯一主形态 |
| 提示词（必填） | `提示词` / `描述` / `生图提示词` / `外观` / `外貌`；多个描述列用原文加原列名拼接 |

转写禁令：不编名称或提示词；不默认第一行是主形态；不按名称相似合并；形态列整表没有时问一次「全部按主形态还是由你标主子」，不要默填。单元格缺值仍按 Sheet、行号和字段补问后重跑转写与 `prompt-sheet-read`。

## 5. 能力门与主形态回填

帮助必须列出 `prompt-template`、`prompt-sheet-read`、`preset-list`、`generate-image-types`、`add`、`generate` 和 `generate-list`。缺少任一项则停止。

只选择 `parent_state_id` 为空的主形态，按类型 `resource add` 创建未定稿资产：

```bash
reelmate resource add SP_ID --set @character-main-assets.json --dry-run --json
reelmate resource add SP_ID --set @character-main-assets.json --idempotency-key KEY --json
```

从 `data.succeeded[]` 读取 `resource_id`，并与 `state_id` / `group_id` 保持映射。后续生图只用这些 `resource_id`。

## 6. 批量生成主形态图片

三类分别组织提交：

```bash
reelmate resource generate SP_ID MAIN_RESOURCE_ID \
  --set type=character|scene|prop --set prompt=PROMPT \
  --set ai_model_mark=IMAGE_MODEL --set resolution=RESOLUTION \
  --set radio_ui=RATIO --set qty=1 --dry-run --json
```

风格按资源类型取对应 `uk_id`；用户选择不设置时不传。角色已确认构图时追加 `--set generate_image_type=...`，角色主形态和子形态都必须同时追加。`style_uk_id` / `theme_uk_id` 带引号传 JSON 字符串。确认预演后按 [_hard-gate.md](_hard-gate.md) 积分展示策略展示预估消耗、余额和积分明细链接，用户确认后再提交。用 `task wait` 再 `resource generate-list`。所有主形态目标记录均为 `task_status=3` 且存在 `file_id` 才进入下一步；部分失败只重跑失败的 `resource_id`。

本流程通常没有剧本上下文，主图确认前必须先现跑项目页深链，再按本轮生成类型跑资产页深链（`1=角色`、`2=场景`、`3=道具`）：

```bash
reelmate deeplink project --workspace SP_ID --set creation_mode=1 --json
reelmate deeplink asset --workspace SP_ID --set resource_type=1 --json
reelmate deeplink asset --workspace SP_ID --set resource_type=2 --json
reelmate deeplink asset --workspace SP_ID --set resource_type=3 --json
```

只消费当次 `data.href` 或 `links[0].href`。项目页应为 `/series-manage/SP_ID?tab=workshop`。不要手拼 URL。`deeplink project` 的 `ok=false` 或 `href` 为空时先补齐 `missing[]`，不得进入确认提问。有真实剧本文件名和 `episode_total` 时，看图可改用 `deeplink asset-result`，但仍必须先交项目页。不用 `deeplink asset-lib`。

## 7. 主形态定稿与保存主体

不得与步骤 6 的图片确认合并省略，也不得推迟到子形态生成之后。问 `hitl.asset-result-confirm` 时，**同一条用户可见消息必须带上本轮 `deeplink project` 的 `href`；本轮生成了哪些类型就再带哪些 `deeplink asset` 的 `href`**，再问齐：是否批量定稿（默认本轮全部主形态）；是否把角色保存为 Seedance 主体。没有项目页链接不得提问。

定稿每条必须使用用户选中的 `generate_id`：

```bash
reelmate resource confirm-record SP_ID MAIN_RESOURCE_ID \
  --set generate_id=GENERATE_ID --set name=ASSET_NAME --dry-run --json
```

保存主体的角色传 `sync_subject=true`，再：

```bash
reelmate subject save-from-resource SP_ID ROLE_RESOURCE_ID \
  --set name=ROLE_NAME --set generate_id=GENERATE_ID \
  --set subject_type=1 --set 'files=["FILE_ID"]' \
  --set 'business_list=[3]' --idempotency-key=SUBJECT_KEY --json
```

`files` 必须是同一 `generate_id` 对应的 `file_id`。同名主体已存在时接口返回既有 `subject_id`。审核驳回属于 `moderation`，禁止自动重试。

回读 `resource list` 确认目标主形态均为 `status=2`、需保存主体的角色都有 `subject_id` 且 `support_business` 包含 `3`，再进入步骤 8。用户选择不定稿的组不进入子形态生图。解析结果里没有子形态时跳到步骤 10。

## 8. 子形态图生图

先为每个子形态 `resource add` 得到 `CHILD_RESOURCE_ID`，再引用同组已定稿主形态图片：

```bash
reelmate resource generate SP_ID CHILD_RESOURCE_ID \
  --set type=character|scene|prop --set prompt=CHILD_PROMPT \
  --set ai_model_mark=IMAGE_MODEL --set parent_file_id=MAIN_FILE_ID \
  --dry-run --json
```

沿用步骤 2 已确认的参数，不重新澄清。`MAIN_FILE_ID` 必须是步骤 7 定稿时选中的那张主形态图片，从 `confirmed_records[]` 或同一 `generate_id` 的 `generate-list` 读取。预演会把 `mode` 显示为 `refer-image-to-image`。全部目标子形态 `task_status=3` 且有 `file_id` 后，按步骤 6 再跑 `deeplink project` 与对应 `deeplink asset`，把新的 `href` 写进同一条确认消息，再问子形态定稿与保存主体。没有项目页链接不得提问。

## 9. 子形态定稿与保存主体

问 `hitl.asset-result-confirm` 时，**同一条用户可见消息必须带上本轮 `deeplink project` 的 `href` 与步骤 8 的资产页 `href`**，再问齐：是否批量定稿（默认本轮全部子形态）；是否把角色保存为 Seedance 主体。没有项目页链接不得提问。步骤 7 已定稿的主形态不得重复提交。

定稿每条必须使用用户选中的 `generate_id`：

```bash
reelmate resource confirm-record SP_ID CHILD_RESOURCE_ID \
  --set generate_id=GENERATE_ID --set name=ASSET_NAME --dry-run --json
```

保存主体的角色传 `sync_subject=true`，再：

```bash
reelmate subject save-from-resource SP_ID CHILD_RESOURCE_ID \
  --set name=ROLE_NAME --set generate_id=GENERATE_ID \
  --set subject_type=1 --set 'files=["FILE_ID"]' \
  --set 'business_list=[3]' --idempotency-key=SUBJECT_KEY --json
```

`files` 必须是同一 `generate_id` 对应的 `file_id`。同名主体已存在时接口返回既有 `subject_id`。审核驳回属于 `moderation`，禁止自动重试。

回读 `resource list` 确认目标子形态均为 `status=2`、需保存主体的角色都有 `subject_id` 且 `support_business` 包含 `3`，再进入步骤 10。

## 10. 交付

```bash
reelmate resource list SP_ID --json
```

`done_when`：所有目标资产均为 `status=2`；需保存主体的角色都存在 `subject_id` 且 `support_business` 包含 `3`；已输出项目页 `href`。部分失败只重跑失败项。然后输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。
