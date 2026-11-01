# 拆分镜后缺失资产补充（可选）

只在 `gui-script-video-storyboard.md` 的全部剧集拆分镜成功后、存在缺失资产时读取。这是可选步骤，不是拆分镜前置门：批量资产匹配是组合任务，服务端在匹配完成后自动拆分镜，拆分镜前没有资产数量确认，也不向 `episode parse` 传资产数量阈值。

按剧集检查 `episode match-result` 的 `characters[]`、`scenes[]`、`props[]`；`status=2` 计为已匹配，`status=1` 计为未定稿，`status=3` 计为缺失。按角色、场景、道具分别列出总数、已匹配数、未定稿数、缺失数和可智能补充数。补充只更新本集资产匹配，不承诺改写已生成的分镜草稿，也不会重新触发拆分镜。

### 智能补充候选条件

可智能补充项必须同时满足：资产类型是角色、场景或道具，存在 `resource_id`，`status=3`，`name` 非空，prompt 为空，`prompt_generating` 不为真，且 `prompt_blocked` 不为真。

## 未匹配项选择

没有缺失项时不读取本页，直接进入分镜确认；存在缺失项时，告知数量并提供以下可选项：

1. **智能补充缺失资产**：只处理可智能补充项。确认前必须展示目标数、本次实际图片参数、`qty=1`，以及「提示词补全暂估」和「资产生图预计」两条独立明细及可得总计。这一次确认同时授权提示词补全及后续自动生图；提示词成功后不再询问“是否生图”。
2. **重新匹配**：`resource match-reset`。先 `--dry-run` 并明确提示破坏性；一次选择只重跑一次。
3. **保持现状，进入分镜确认**：保留所有未匹配项，返回主流程步骤 3。用户不选择时按本项处理。

## 智能补充执行顺序

进入选项 1 的确认前，先用 `resource list` 分页查重，确定可复用正式资产和需要生图的目标。然后生成两类账单：

```bash
reelmate credits estimate --set scenario=asset_prompt_completion \
  --set selected_actionable_count=TARGET_COUNT --json
reelmate resource generate SP_ID RESOURCE_ID ... --set qty=1 --dry-run --json
reelmate credits estimate --set @image-estimate.json --json
reelmate credits balance --json
reelmate deeplink credits --json
```

提示词补全账单必须是 `source=provisional` 并写「暂估消耗」；生图账单使用每个预演的 `credits_estimate`，异构目标合并成 `requests[]`，只计无可复用正式资产的目标。两条账单都 `available=true` 时可以相加并写总计；任一条为 `unavailable` 时分别展示已知明细和不可估算原因，不编总计。确认消息还必须列出目标总数、复用数、需生图数、图片模型/画幅/分辨率/构图和 `qty=1`。

用户确认后按剧集执行，不能用首集成功代表全项目成功：

1. 用 `resource prompt-complete` 提交当集目标，再轮询 `resource prompt-complete-result`。同一 `resource_type + name` 有历史任务时取最新一次；只有 `item_status=2|3` 且 `candidates[0].visual_prompt` 是非空有效字符串的项才能继续。
2. 对每个提示词有效项按“类型 + 原名”保持目标集合，再用 `resource list` 分页复核确认前的查重结果。无可复用项时依次执行 `resource add`、`resource generate`、`task wait`、`resource generate-list`、`resource confirm-record`；有可复用的正式资产时直接复用，不重复生图。
3. `resource generate` 的 prompt 只能取上一步校验通过的 `visual_prompt`。风格、题材和角色构图沿用环节 3 已确认的图片参数；`style_uk_id`/`theme_uk_id` 带引号传 JSON 字符串。`GENERATE_TASK_ID` 只取本次 `resource generate` 返回值；`resource generate-list` 只取该任务产生的唯一成功记录。
4. 用当前匹配结果构造 `episode save-resource-matches` 的角色、场景、道具完整三数组快照：成功项替换对应占位项，失败项保留原未匹配条目。不得把提示词任务中的占位 `resource_id=-1` 当成已匹配资产写回。
5. 最后重新调用 `episode match-result`；只有本次成功目标已为 `status=2`，且 `resource_id/file_id` 与本次复用或定稿结果一致，才能宣称该项补充完成。

命令细节见 [resource.md](../../commands/resource.md) 与 [episode.md](../../commands/episode.md)。

## 智能补充失败处理

提示词补全、生图或定稿部分失败时，只推进和回写成功项，不重复提交已成功项。空 prompt 或无有效 `visual_prompt` 的项禁止调用 `resource generate`；失败项保持未匹配，报告数量和原因后回到现有 1/2/3 选择。不得自动调用 `resource match-reset`。

选 3，或补充完成后，返回 `gui-script-video-storyboard.md` 步骤 3 的分镜确认。
