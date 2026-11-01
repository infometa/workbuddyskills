---
name: reelmate-cli-skill
description: "调用 reelmate 写入剧厂或无限画布，或询问 reelmate / 万兴剧厂 / 剧厂 CLI 怎么用、有哪些功能、使用教程、能做什么、新手引导时使用：绑定或建项、导入剧本、回填资产或分镜、生成或重跑图视频。只要文案或方案、不跑 CLI、也不是使用咨询时不使用。"
---

# ReelMate CLI

用 `reelmate` 完成剧厂 GUI 与无限画布工作流。发布态只依赖当前二进制帮助、本 Skill 和随包命令文档。

<HARD-GATE>
1. 询问 reelmate / 万兴剧厂 / 剧厂 CLI 怎么用、功能介绍、使用教程、能做什么、新手引导，且本轮没有写剧本、生图、生视频、回填、出片等创作任务：只读 [user-guide.md](manual/user-guide.md)，**原样返回**全部内容，不删减、不改写；不执行任何 reelmate 命令，不加载其它场景、协议或 `commands/*.md`。用户接着提出实际创作需求时，不再走本条，改按下表选定创作场景。
2. 先按路由表选定恰好一个场景文档，再读该场景涉及的 `commands/*.md`。未选定前不跑写命令。
3. 执行契约只读 [_hard-gate.md](manual/workflow/_hard-gate.md)。登录、建项、建画布读 [_bootstrap.md](manual/workflow/_bootstrap.md)。阶段与命名 HITL 读 [_stage-machine.md](manual/workflow/_stage-machine.md)。有限选项呈现读 [_hitl-present.md](manual/workflow/_hitl-present.md)。
4. 进度分母来自场景文档写死的步骤表。对用户报告写 `进度 n/m：动作`，不临场发明计划或步数。
5. 场景文档的 `done_when` 全部满足才报告完成。报告完成前必须输出 [_hard-gate.md](manual/workflow/_hard-gate.md) 的固定完成总结；「积分消耗」仅当流水全匹配（M=T）时输出，积分明细链接始终保留。缺必填行先补查，不算完成；未全匹配时不得为凑「积分消耗」一行而编数字或改写为预估。
6. Agent 本地中间文件只写当前工作目录下的 `outputs/`。不新建带日期、随机后缀或项目拼音的目录。
7. 积分不足阻塞付费步骤时，用户可见回复只认 [_hard-gate.md](manual/workflow/_hard-gate.md)「余额不足（用户可见）」；禁止向用户贴续跑 shell、`workspace_id` / `canvas_id` / `node_id` / `task_id` 等内部常量（用户明确要求自己在终端执行时除外）。
</HARD-GATE>

## 路由

自上而下只匹配一行，条件必须同时成立。询问怎么用、功能介绍、教程且没有实际创作任务时，走 [user-guide.md](manual/user-guide.md)，原样返回全部内容，不执行命令。已有无限画布文本节点且要拆资产、拆分镜、上传剧本或出片时，先走 [generate-script.md](manual/workflow/generate-script.md) 交接段再进制片四环节，不要当 5/5 续写。一句话写剧本、一键生成剧本，且未点名制片工坊或四环节出片时，默认无限画布并走 [generate-script.md](manual/workflow/generate-script.md)，不要问「制片工坊还是无限画布」。对不上才问「制片工坊还是无限画布」，以及手上是剧本、提示词表、图片包还是分镜表；选定前不写。`_stage-machine.md`、`_hard-gate.md`、`_hitl-present.md`、`_bootstrap.md`、`_models.md`、`_backfill-contract.md` 是共享协议，不是场景。

| 选定条件 | 场景 | 排除 |
|---|---|---|
| 询问 reelmate / 剧厂 / CLI 怎么用、功能介绍、教程、能做什么、新手引导，且本轮没有写剧本、生图、生视频、回填、出片 | [user-guide.md](manual/user-guide.md) | 不要执行 reelmate；不要进创作场景 |
| 无限画布已有文本节点，且要拆资产、拆分镜、上传剧本或出片 | [generate-script.md](manual/workflow/generate-script.md) | 不要当 5/5 续写；不要新建工坊项目 |
| 一句话写剧本、一键生成剧本，或在文本节点续聊（未点名制片工坊时默认无限画布） | [generate-script.md](manual/workflow/generate-script.md) | 不要四环节出片；不要生图/生视频 |
| 无限画布 + 图片提示词、图片文件或已有图片节点（单张或批量节点） | [generate-image.md](manual/workflow/generate-image.md) | 不是制片工坊资产页；不要 `resource extract` |
| 无限画布 + 视频提示词或已有视频节点 | [generate-video.md](manual/workflow/generate-video.md) | 不是制片工坊分镜表 |
| 无限画布 + 分镜 Excel / 批量分镜提示词要生视频 | 无独立场景：停止并说明缺口 | 不改走 `generate-video` 或 GUI 分镜回填；`node table import` 待实测 |
| 制片工坊 + 资产提示词表且要生图 | [gui-backfill-asset-prompt.md](manual/workflow/gui-backfill-asset-prompt.md) | 不是已有图片包；不要剧本提取 |
| 制片工坊 + 已有资产图片包且不生图 | [gui-backfill-asset-image.md](manual/workflow/gui-backfill-asset-image.md) | 不是提示词表 |
| 制片工坊 + 分镜 Excel 且要生视频 | [gui-backfill-shot-video.md](manual/workflow/gui-backfill-shot-video.md) | 不跑剧本拆解或资产提取 |
| 制片工坊 + 有剧本要出片，或四环节进度不明 / 要从中间环节续跑 | [gui-script-video.md](manual/workflow/gui-script-video.md) | 先 `workflow detect`，再只加载当前阶段文件 |

回填字段只认 [_backfill-contract.md](manual/workflow/_backfill-contract.md)。模型现查 [_models.md](manual/workflow/_models.md)，只用当次 `model list` / `model search` 的展示名。资产提示词表用 `resource prompt-template` 生成官方空表；用户回传自带清单时先由 Agent 转成该模板格式，再 `resource prompt-sheet-read` 回读。分镜提示词表用 `storyboard prompt-template` 生成官方空表；GUI 分镜回填只认三列：`剧集号`、`分镜号`、`视频提示词`。用户回传自带分镜清单时先由 Agent 转成该模板格式，再 `storyboard sheet-read` 回读。

## 准备

stderr 出现「发现新版本」或 `reelmate version check --json` 的 `update_available` 为 true 时：**先完成本轮付费写操作**，再按 zip 内 `INSTALL.md` 钉死版本重装，并用 `reelmate skill-path` 整目录替换当前宿主 Skill。不要只跑 npm，不要落地 zip 解压出的 Skill。

登录、绑定与 `--workspace` / `--space` 见 [_bootstrap.md](manual/workflow/_bootstrap.md)。凭据不进入命令、日志或仓库。脚本和 Agent 使用 `--json`；stdout 只消费业务数据，进度从 stderr 读取。成功 envelope 为 `{ok:true,data,links}`，失败为 `{ok:false,error}`。完成判定与积分现查只认 [_hard-gate.md](manual/workflow/_hard-gate.md)。有限选项 HITL 的呈现只认 [_hitl-present.md](manual/workflow/_hitl-present.md)。

## 按需参考

| 分支 | 指南 |
|---|---|
| 命令失败或恢复 | [进程退出码](manual/error-codes.md) |
| shell 管道 | [管道说明](manual/pipes/README.md)、[管道错误处理](manual/pipes/error-handling.md) |
| 项目与作用域 | [workspace](commands/workspace.md)、[account](commands/account.md)、[team](commands/team.md) |
| 剧本与剧集 | [upload](commands/upload.md)、[episode](commands/episode.md) |
| 资产与主体 | [resource](commands/resource.md)、[subject](commands/subject.md)、[asset-lib](commands/asset-lib.md) |
| 分镜与素材 | [storyboard](commands/storyboard.md)、[material](commands/material.md) |
| 模型与任务 | [model](commands/model.md)、[task](commands/task.md) |
| 深链与导出 | [deeplink](commands/deeplink.md)、[export](commands/export.md) |
| 画布节点 | [canvas](commands/canvas.md)、[node](commands/node.md)、[script](commands/script.md)、[group](commands/group.md) |

`--set` / `--update` 边界见 [节点类型](commands/node.md#节点类型)。连线见 [edge](commands/edge.md)。
