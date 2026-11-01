# GUI 剧本生视频四环节工作流

制片工坊（`--scope studio`）。用户可从环节 1 开始，或指定从项目创建、剧本导入、资产生成、拆分镜任一环节继续。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_stage-machine.md](_stage-machine.md)、[_backfill-contract.md](_backfill-contract.md)、[_models.md](_models.md)。

## 当前包

```bash
reelmate workflow detect --scope studio --json
```

用户指定中间起点时，先映射为 `project`、`script`、`asset`、`storyboard` 或 `render`：

```bash
reelmate workflow resume --scope studio --from STAGE --workspace SP_ID --json
reelmate workflow detect --scope studio --workspace SP_ID --json
```

`resume` 只记录意图。按 `data.stage` / `data.missing[].goto_stage` 只加载下表**一个**阶段文件，不预读其它环节。

| 当前包 | 文件 | 步骤分母 |
|---|---|---|
| `project` 或 missing 含 `sp_id` | [gui-script-video-project.md](gui-script-video-project.md) | 1 |
| `script` 或 missing 含 `episode` | [gui-script-video-script.md](gui-script-video-script.md) | 1 |
| `asset` 或 missing 含 `resource` | [gui-script-video-asset.md](gui-script-video-asset.md) | 4 |
| `storyboard` / `render` 或视频未生成 | [gui-script-video-storyboard.md](gui-script-video-storyboard.md) | 3 |

对用户报告进度时写 `进度 n/m：动作`，`m` 取上表该阶段分母（项目 1、剧本 1、资产 4、分镜 3）。不要把四环节写成 `进度 2/4` 或「环节 n/4」。

从 [generate-script.md](generate-script.md) 交接进入时，`SP_ID` / `WORKSPACE_ID` 已是当前画布项目：detect 必须带 `--workspace SP_ID`。禁止加载 [gui-script-video-project.md](gui-script-video-project.md)，禁止 `workspace create`。同一项目可同时有画布剧集与工坊剧集；本流程只操作工坊侧。

参数包与命名 HITL 见 [_stage-machine.md](_stage-machine.md)。阶段探测、`hitl.asset-list-confirm`、`hitl.asset-result-confirm`、`hitl.shot-result-confirm` 不能因“沿用历史参数”跳过。

远端目录必须在本次执行中查询。批量业务使用对应批量接口。模型现查 [_models.md](_models.md)，只用当次目录的展示名。
