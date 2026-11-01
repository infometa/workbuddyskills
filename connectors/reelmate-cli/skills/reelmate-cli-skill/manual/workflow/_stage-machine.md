# 工作流阶段机

阶段探测、缺项回引、命名 HITL 和断点续跑。发布态以当前二进制 `--help`、本 Skill 和命令文档为契约。身份、写入和完成门见 [_hard-gate.md](_hard-gate.md)。

## 先探测，再动作

开始、续跑和任何写操作前都执行：

```bash
reelmate workflow detect --scope studio --json
# 画布链路：
reelmate workflow detect --scope canvas --json
```

只读 `data.stage`、`completed`、`pending`、`missing` 和 `next_command`。探测只发只读请求，不改变远端状态。未确认项目前的首次探测可以不加 `--workspace`；确认后的 detect 必须带 `--workspace SP_ID` 或 `--workspace WORKSPACE_ID`。

把探测结果当成当前包，不凭对话记忆推断阶段。对用户报告进度时写 `进度 n/m：动作`，不要写「当前步」。内部记录仍用：

```text
current_step: <stage 或 missing[].goto_stage>
hitl: <本步点名的 HITL id，无则省略>
next_command: <data.next_command>
done_when: <当前场景文档该步谓词>
```

无限画布生图或生视频不走本页阶段机。

## 阶段定义

阶段顺序为 `project -> script -> asset -> storyboard -> render`，`stage` 表示第一个未完成阶段。

同一项目可同时承载工坊剧集与画布剧集。studio 阶段只认工坊侧（`canvas_id` 为空或 `"0"`）；画布那一集不算 `script` / `storyboard` 完成。

| 阶段 | GUI（studio）完成条件 | 画布（canvas）完成条件 |
|---|---|---|
| `project` | 已绑定项目（交接路径即当前画布项目的 `WORKSPACE_ID`） | 已绑定画布 |
| `script` | 已有正式工坊剧集或剧本拆集结果 | 已有文本节点 |
| `asset` | 已有已定稿资产 | 已有拆资产或图片节点 |
| `storyboard` | 批量拆分镜组合任务成功，且**每个正式剧集**的拆解结果均为 `status=2`、列表非空 | 已有拆分镜或表格节点 |
| `render` | 视频任务完成由调用方用任务查询判定 | 组执行任务完成由调用方判定 |

`workflow detect` 负责定位入口，不保存所有异步任务的完成记录。GUI 视频生成以所有 `task wait` 返回终态成功为准。视频成功后四环节工作流完成；合并导出是阶段机外的可选追加步骤。

## Studio 只读证据

| 要确认的内容 | 命令 | 判定 |
|---|---|---|
| 当前阶段 | `reelmate workflow detect --scope studio --json` | `data.stage` 与 `data.missing` |
| 项目 | `reelmate workspace show --json` | 有 `workspace_id` |
| 剧本 | `episode list --set creation_mode=1`；为空再查 `episode split-list SP_ID` | 工坊剧集或拆集任一非空，不重复上传；仅有画布剧集仍须上传 |
| 提取任务 | `resource extract-status SP_ID` | `1` 进行中、`2` 成功、`3/4` 失败或失效 |
| 已定稿资产 | `resource list SP_ID`（单页上限 100 条，先看 `has_more`） | 目标资产存在且定稿；`has_more=true` 时"查不到"不能判成缺失 |
| 分镜 | 对工坊 `episode list --set creation_mode=1` 返回的**每个** `EP_ID` 执行 `storyboard list` / `episode parse-result` | 每集均非空且成功 |
| 视频 | `task wait TASK_ID...` 或逐个 `task get` | 所有目标任务终态成功 |

画布阶段从 `canvas get` 的 `node_list` 判断：`text` 对应剧本，`asset/image` 对应资产，`script/table` 对应分镜。

## 缺项回引

`data.missing[].goto_stage` 决定回到哪一环节；回引后仍要重新探测。

| 缺项 | GUI 回引 | 入口 |
|---|---|---|
| `sp_id` | 环节 1 | `workspace create` 或绑定已有项目 |
| `episode` | 环节 2 | `upload` 后 `episode split` |
| `resource` | 环节 3 | `resource extract-status`，未开始才 `resource extract` |
| `storyboard` | 环节 4 | 创建全部剧集后，用 `episode match-resources --set ep_ids=[...]` 提交批量组合任务 |
| 视频未生成 | 环节 4 | 分镜草稿确认后逐集 `storyboard batch-generate`（`generate_type=1`、`is_store_draft=true`），同一次请求物化正式分镜并提交视频任务，再统一 `task wait` |

## 命名 HITL

只执行本步点名的节点。用户明确提供参数或明确要求沿用历史值时，跳过**对应参数包**的澄清，并先复述实际值。阶段探测、缺项回引和结果确认不能因此跳过。远端目录参数在没有明确复用指令时必须重新查询。

| id | 何时 | 问什么 |
|---|---|---|
| `hitl.project-create` | 新建项目前；须先通过 [_bootstrap.md](_bootstrap.md) 的 `project.create` 预检 | 对齐 Web 新建项目：创作模式、剧目类型、画面比例必须用网页展示名列全（场景可钉死创作模式并复述）。项目名称按 [_bootstrap.md](_bootstrap.md) 从上下文推断，推不出来才问。不要问 Web「自定义」剧目类型 |
| `hitl.paid-image-params` | 付费生图前。资产提示词回填先预检 `resource.edit`；无限画布生图步骤 3 先预检 `project.edit`。工坊资产提取先跑 `resource extract`，不预检 | 制片工坊：风格/题材/构图/图片模型（互不影响可同轮），确认模型后再列画幅与分辨率。无限画布：只问图片模型、画幅、分辨率，不问风格/题材/构图 |
| `hitl.paid-video-params` | 付费生视频前。拆分镜先预检 `episode.edit` 再预检 `storyboard.edit`；分镜回填只预检 `storyboard.edit`；无限画布生视频步骤 3 预检 `project.edit` | 无限画布：先视频模型，确认后再列画幅、分辨率、时长。制片工坊剧本拆分镜：先视频模型，再按拆分镜场景合并三类完整模板目录，同轮确认模板、画幅、分辨率；回填场景无模板则仍须列画幅与分辨率；时长按场景文档 |
| `hitl.asset-list-confirm` | 资产提取成功后 | 角色/场景/道具清单是否确认 |
| `hitl.asset-result-confirm` | 主/子资产生图成功后 | 同一条可见消息先交 `deeplink project` 的 `href`，再问是否定稿、哪些角色保存为 Seedance 主体。没有项目页链接不得提问。看图再交场景规定的资产页。积分明细不得代替项目页 |
| `hitl.asset-ready` | 进入拆分镜或分镜回填前 | 本次引用的资产图片是否已准备完毕 |
| `hitl.shot-result-confirm` | 分镜拆解成功后 | 分镜单是否确认，未确认不生视频 |
| `hitl.cli-needs-input` | CLI 返回 `needs_input` | 只按 `missing[]` 补字段 |

图片参数包：`style_uk_id`、`theme_uk_id`、`ai_model_mark`、`resolution`、画幅（角色/场景/道具共用一次 `radio_ui`）、`generate_image_type`。分镜视频参数包：`refer2video_model`、模板来源 `prompt_use_type`、官方 `prompt_type` 或团队字符串 `prompt_ukid`（一步流为 `uk_id`，工作流模版为 `workflow_id`，互斥）、一步流查询语言 `lang`、画幅、`resolution`、`qty`。模板来源由合并列表中的选中条目确定，改选模板清除旧模板标识；切换模型重新查询并确认下游参数。角色构图现查 `reelmate resource generate-image-types --json`。问用户时只列展示名，括号只允许 `（推荐）`。呈现见 [_hitl-present.md](_hitl-present.md)。构图查询不返回数字；提交把名称交给 `generate_image_type`。模型查询不返回 `id` / `ai_model_mark`，提交把展示名交给 `--set ai_model_mark=`。所有确认项按硬门列全并分步，不能只问推荐配置，也不能在模型未定时把画幅、分辨率或模板一并抛出。

合并成片并下载不是默认阻塞 HITL。四环节向用户报告完成时必须先输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留），然后再问是否合并；没有回复或拒绝时直接结束，不创建合并任务。

## 断点续跑

```bash
reelmate workflow resume --scope studio --from STAGE --workspace SP_ID --json
# STAGE: project、script、asset、storyboard、render
reelmate workflow detect --scope studio --workspace SP_ID --json
```

`--from` 表示用户想从哪里继续，不证明前置条件已满足。实时探测发现缺项时必须回引。

## 写入与恢复

1. 批量或付费写操作先 `--dry-run --json`。
2. 确认后对同一请求使用唯一 `--idempotency-key`。
3. 异步提交后查询到终态成功再推进，超时先查状态。
4. 批量部分失败只重跑 `failed[]`，成功项不得重复提交。
5. 重跑前再次探测；远端已经前进时不得拉回旧阶段。
