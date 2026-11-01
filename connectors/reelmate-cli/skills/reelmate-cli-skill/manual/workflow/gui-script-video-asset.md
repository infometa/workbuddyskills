# GUI 环节 3：资产生成

只在当前包为 `asset` 或 `missing` 含 `resource` 时读取。前置：项目已创建、剧本已上传并解析。模型现查 [_models.md](_models.md)。角色构图现查 `reelmate resource generate-image-types --json`。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/4 | 提取与 `hitl.asset-list-confirm` | 用户已确认清单；或用户确认已有定稿资产可进环节 4 |
| 2/4 | `hitl.paid-image-params` | 风格、题材、模型、分辨率、角色构图、画幅已确认或明确不设 |
| 3/4 | 主形态生图、`hitl.asset-result-confirm`、定稿 | 目标主资产 `resource list` 已定稿；需保存主体的角色已保存；本轮已跑 `deeplink project` 且 `href` 非空；确认问句与项目页 `href` 在同一条用户可见消息里 |
| 4/4 | 子形态生图、确认、定稿 | 无子形态则跳过；有则目标子资产已定稿；本轮已跑 `deeplink project` 且 `href` 非空；确认问句与项目页 `href` 在同一条用户可见消息里 |

`resource list` / `draft-list` / `generate-list` 单页上限 100 条。`has_more=true` 时继续取页，不能把首页当成全库。

## 1. 提取与清单确认

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate resource list SP_ID --json
reelmate resource extract-status SP_ID --json
```

| 状态 | 动作 |
|---|---|
| 已有全部所需定稿资产 | `hitl.asset-ready`；确认后可进入环节 4 |
| `status=1` | 只执行 `extract-wait` |
| `status=2` | 直接查清单 |
| `status=3\|4` | 预演并只重做失败任务 |
| 没有提取任务 | 新建提取任务 |

新建或重做资产清单提取前，先按当前剧本字数生成统一账单并展示；首次免费权益由 CLI 查询，不能自行假定。`word_count` 使用与 Web 相同的剧本文本计数结果：

```bash
reelmate credits estimate --set scenario=asset_extract --set word_count=WORD_COUNT --json
reelmate credits balance --json
reelmate deeplink credits --json
```

```bash
reelmate resource extract SP_ID --set task_type=1 --set generate_mode=1 --dry-run --json
reelmate resource extract SP_ID --set task_type=1 --set generate_mode=1 \
  --idempotency-key KEY --json
reelmate resource extract-wait SP_ID --set et_id=ET_ID --timeout 30m --json
```

只提交过 `task_type=1` 时，顶层 `status` 会一直停在 `1` 直到超时。CLI 同时看 `detail.extraction_list` 子任务状态，不必再靠 `draft-list` 判断是否完成。

状态为 `2` 后查询三类草稿，并返回资产确认页：

```bash
reelmate resource draft-list SP_ID --set resource_type=1 --json
reelmate resource draft-list SP_ID --set resource_type=2 --json
reelmate resource draft-list SP_ID --set resource_type=3 --json
reelmate deeplink asset-confirm --workspace SP_ID \
  --name SCRIPT_FILE_NAME --set episode_total=EPISODE_TOTAL --json
```

`hitl.asset-list-confirm`：把 `deeplink asset-confirm` 的 `data.href` 交给用户，请其在资产确认页核对角色、场景、道具清单；未确认不得继续。`href` 必须与确认问句在同一条用户可见消息里。

本步不要在对话里列出角色、场景、道具名单。清单以资产确认页为准：提取出几十到几百条资产是常态，在对话里复述名单只会把确认问句和 `href` 挤出用户视野，反而更难确认。`draft-list` 的三次查询用于确认提取已完成和拿到条数，不是为了逐条念给用户听；需要时只报三类各自的条数。

## 2. 查询图片参数并确认

清单确认后生成三类资产提示词并等待成功。`task_type=5` 默认带 `need_voice=1`（同步生成角色音色描述）；不要生成音色时再 `--set need_voice=2`。

该动作当前 Web 已隐藏旧价格。提交前仍须查询并展示统一账单的 `source=unavailable` 和原因，同时展示余额与积分明细链接，不能省略或沿用资产提取价格：

```bash
reelmate credits estimate --set scenario=asset_prompt --json
reelmate credits balance --json
reelmate deeplink credits --json
```

```bash
reelmate resource extract SP_ID --set task_type=5 --dry-run --json
reelmate resource extract SP_ID --set task_type=5 --idempotency-key KEY --json
reelmate resource extract-wait SP_ID --set et_id=ET_ID --timeout 30m --json
```

```bash
reelmate workspace info --workspace SP_ID --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=1 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=2 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=style --set res_type=3 --set lang=zh-CN --json
reelmate resource preset-list SP_ID --set kind=theme --set lang=zh-CN --json
reelmate resource generate-image-types --json
reelmate model list image --sp-type MODEL_SP_TYPE --json
```

`preset-list` 的 `lang` 一律 `zh-CN`，海外仿真人项目也一样，不要按 `sp_type` 改成 `en-US`。`MODEL_SP_TYPE` 从 `workspace info` 的 `data.sp_type` 推出。风格目录仍按角色、场景、道具分别查询（`res_type=1/2/3`，同名条目的 `uk_id` 不同）；HITL 只展示一份风格展示名，对齐 Web 的单一「创作风格」入口，跨三类按名称映射。选择后各类提交匹配到的 `uk_id`。题材只查一次。

`hitl.paid-image-params` 按 [_hard-gate.md](_hard-gate.md) 分步列全：先同轮确认风格、题材、角色构图、图片模型。图片模型只列 `params.studio_asset_image` 非空且 `visible=true` 的条目，按 `mode_order.studio_asset_image` 排展示名；角色、场景、道具共用这一套。禁止再按 `mode_order` 目标模式或画布 `text2image` 当本步成员判定。本场景 0 条时停止并说明当前项目没有可资产生图的模型，不改走画布清单。候选展示名含 `TGI 2` 时标推荐；禁止把列表第一项当默认（常见第一项是 TGI 2.5 Flare）。模型确认后再按所选模型 `params.generation.text2image` 列**一次**画幅和 `resolution_options` 原序列 `label`；本轮不问画质。对齐 Web 批量生成弹窗：比例条只有一条，角色/场景/道具共用，提交同一 `radio_ui`，不要拆成角色画幅/场景画幅/道具画幅。构图 `recommended=true` 的项标推荐；模型确认后，画幅有 `16:9`、分辨率有 `2K` 时再标推荐。推荐展示名不在实时目录中时，只从实际返回项中选。新建项目的画面比例不是资产生图画幅：项目可以是 `9:16`，本步仍按模型 `ratios` 列全并按上面规则标推荐。

`reelmate resource --help` 没有 `preset-list` 或 `generate-image-types` 时停止并报告能力缺口。

## 3. 主形态生图与定稿

从三类默认 `draft-list` 顶层条目收集主形态 `eed_id` 与 `resource_generate_preview.preview_status`，只凭这两项判断是否需要生图。回包 `prompt` 可能为空串：空 prompt 不得停止，也不得 `--set prompt=`。主形态批次不要启用包含全部形态的查询参数。角色、场景、道具各调用一次批量接口，同类不得逐个下单：

```bash
reelmate resource batch-draft-generate SP_ID \
  --set res_type=RESOURCE_TYPE --set 'eed_ids=["MAIN_EED_ID"]' \
  --set ai_model_mark=IMAGE_MODEL --set resolution=RESOLUTION \
  --set radio_ui=RATIO --set qty=1 \
  --set 'style_uk_id="STYLE_UK_ID"' --set 'theme_uk_id="THEME_UK_ID"' \
  --set generate_image_type=ROLE_COMPOSITION --dry-run --json
```

`style_uk_id` / `theme_uk_id` 必须带引号传成 JSON 字符串。角色主形态和子形态都必须带 `generate_image_type`；场景、道具不传。把三次预演各自的 `data.credits_estimate` 合并为一个 `requests[]` 后执行 `credits estimate`；每组 `count` 等于对应类型的 `eed_ids` 数量，`params.qty=1` 表示每个资产生成 1 张图。按 [_hard-gate.md](_hard-gate.md) 展示每组小计、总计、余额和积分明细链接，用户确认后再分别用唯一幂等键提交。循环查询三类 `draft-list`：`preview_status=3` 继续等待，`4|5` 为成功，`2` 为失败；全部主形态离开进行中且没有未处理失败项才进入确认。

```bash
reelmate deeplink project --workspace SP_ID --set creation_mode=1 --json
reelmate deeplink asset-result --workspace SP_ID \
  --name SCRIPT_FILE_NAME --set episode_total=EPISODE_TOTAL --json
```

只消费当次 `data.href` 或 `links[0].href`。项目页应为 `/series-manage/SP_ID?tab=workshop`。不要手拼 URL。`deeplink project` 的 `ok=false` 或 `href` 为空时先补齐 `missing[]`，不得进入确认提问。`deeplink credits` 的积分明细不得代替项目页。

`hitl.asset-result-confirm`：同一条用户可见消息必须带上 `deeplink project` 的 `href`；看图再交 `deeplink asset-result` 的 `href`。没有项目页链接不得提问。再问是否定稿，以及哪些角色保存为 Seedance 主体。确认后按角色与场景/道具分批定稿：

```bash
reelmate resource batch-confirm SP_ID \
  --set 'resource_ids=["ROLE_RESOURCE_ID"]' --set 'business_list=[3]' \
  --dry-run --json
reelmate resource batch-confirm SP_ID \
  --set 'resource_ids=["SCENE_RESOURCE_ID","PROP_RESOURCE_ID"]' \
  --dry-run --json
```

`resource_id` 必须取生成后的草稿结果，不能用 `eed_id`。用 `resource list` 确认目标主资产均已定稿并保存主体后再生成子资产。

## 4. 子形态生图与定稿

当前接口不会把子形态嵌套在主形态的 `sub_list` 中。`is_all` 必须传 JSON 布尔值 `true`，不能写成数字 `1`：

```bash
reelmate resource draft-list SP_ID --set resource_type=1 \
  --set appearance_order=1 --set is_all=true --json
```

角色、场景、道具各查一次。只处理 `data.list[]` 中 `main_eed_id` 非空且不为 `"0"` 的子形态；其父形态是同一列表中 `eed_id == CHILD.main_eed_id` 的条目。子形态同样只收集 `eed_id` 与生成状态：空 prompt 不得停止，也不得 `--set prompt=`。沿用步骤 2 已确认的全部图片参数。`MAIN_FILE_ID` 必须来自该父形态已确认的正式资产结果：

```bash
reelmate resource batch-draft-generate SP_ID \
  --set res_type=RESOURCE_TYPE --set 'eed_ids=["CHILD_EED_ID"]' \
  --set ai_model_mark=IMAGE_MODEL --set resolution=RESOLUTION \
  --set radio_ui=RATIO --set qty=1 \
  --set 'style_uk_id="STYLE_UK_ID"' --set 'theme_uk_id="THEME_UK_ID"' \
  --set alg_code=refer_image_to_image --set refer_image_type=1 \
  --set 'images=[{"mark":"","name":"","index":0,"uri":"MAIN_FILE_ID","category":RESOURCE_TYPE,"prompt_template":""}]' \
  --dry-run --json
```

`images` 对本次请求内全部 `eed_ids` 生效，因此按“资产类型 + `MAIN_FILE_ID`”分组提交；不同父形态的子资产不能放进同一请求。把所有分组预演的 `data.credits_estimate` 合并为一个 `requests[]` 后执行 `credits estimate`，按分组展示小计和总计，再执行 `credits balance`、`deeplink credits` 并让用户确认。查询到全部子资产成功后，再跑 `deeplink project` 与 `deeplink asset-result`，这是子资产的 `hitl.asset-result-confirm`。只消费当次 `data.href` 或 `links[0].href`。项目页应为 `/series-manage/SP_ID?tab=workshop`。不要手拼 URL。同一条用户可见消息必须带上项目页 `href`；看图再交资产结果页 `href`。没有项目页链接不得提问。`deeplink credits` 的积分明细不得代替项目页。用户确认后用 `resource batch-confirm` 分批定稿；需要保存为主体的角色批次传 `business_list=[3]`。

子形态定稿后变成独立正式资产并拥有自己的 `resource_id`。正式资产结果没有字段记录父子关系，因此保存 `child eed_id -> main_eed_id -> child resource_id` 映射，不能指望正式资产接口回填。

本轮任务到此结束（用户只要资产、或下一环节未继续）时，输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。继续拆分镜则不在这里输出。
