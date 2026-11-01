# 登录、项目与画布

共享引导步骤。场景文档需要“已登录 / 已绑定项目 / 已有画布”时读本页，不在各场景重写。

## 登录

```bash
reelmate account info --json
```

已登录则复用。未登录或鉴权失败：

```bash
reelmate login
reelmate account info --json
```

成功后 CLI 只保存凭据摘要。不要把令牌、授权回调或 `user_data` 写进命令、日志或仓库。

## 空间

空间通常可由登录账号或工作区绑定解析。默认空间可用时不设置 `SPACE_ID`，命令里也不加 `--space`。CLI 返回未确定空间、无权限或 `missing[]` 含空间时，再向用户或管理员取空间 ID 并显式传入。

## 定位或创建项目

已有可用项目时定位并绑定，不重复创建。不要把当前目录已绑定的项目直接当成目标：先 `workspace show` / `workspace list`，按本场景的创作模式筛选。

同一项目可同时承载两类剧集：制片工坊（`canvas_id` 为空或 `"0"`）与无限画布（`canvas_id>0`）。`creation_mode` 是项目主模式 / 默认入口，只影响候选列表和画布命令组能否使用，不是互斥锁。

- 制片工坊场景默认只把 `creation_mode=1` 列为候选。从无限画布 `generate-script` 交接进入四环节时，使用已确认的 `WORKSPACE_ID`，不要再按 `creation_mode=1` 筛选并另建项目。
- 无限画布场景（生剧本 / 生图 / 生视频）只把 `creation_mode=2` 列为候选。已绑定制片工坊项目不能拿来写无限画布。
- 字段对照：创作模式 `creation_mode`，剧目类型 `sp_type`，画面比例 `ratio`。展示名、列全规则和提交值只认 [_hard-gate.md](_hard-gate.md)，本页不重写选项。

```bash
reelmate workspace show --json
reelmate workspace list --json
```

多个候选时列出名称和 ID，让用户选择，不自行选最近项目。没有候选或用户明确要新建时才进入 `hitl.project-create`。

无项目且本场景需要新建时，先预检创建权限，通过后再完成 `hitl.project-create`，然后创建。预检：

```bash
reelmate team permission --require project.create --json
```

`error.kind=permission` 时按 [_hard-gate.md](_hard-gate.md) 的「权限拒绝」停止，不要询问剧目类型或画面比例。退出码 0（包括 `permission_ready` 为 false）再提问。问什么见 [_hard-gate.md](_hard-gate.md)，怎么呈现见 [_hitl-present.md](_hitl-present.md)。项目名称优先从上下文推理，推不出来才留空问用户。场景已钉死创作模式时只复述展示名：制片工坊场景提交 `creation_mode=1`，无限画布场景提交 `2`。`sp_type` 建成后不能改；它决定后续 `model list --sp-type` 分区：2D/3D动漫 `1`，国内和海外仿真人剧都是 `2`。

```bash
reelmate workspace create NAME --space SPACE_ID \
  --set creation_mode=MODE --set sp_type=SP_TYPE --set ratio=RATIO \
  --dry-run --json
reelmate workspace create NAME --space SPACE_ID \
  --set creation_mode=MODE --set sp_type=SP_TYPE --set ratio=RATIO \
  --idempotency-key KEY --json
reelmate workspace show --json
reelmate env info --json
```

`MODE`：制片工坊 `1`，无限画布 `2`。`WORKSPACE_ID` / `SP_ID` 取返回的 `data.workspace_id`。用户选定已有项目时取所选 ID。`--space` 仅在已取得空间 ID 时使用。新建成功后不要执行 `workspace use`。

## 任务内项目常量

用户选定已有项目或 `workspace create` 返回后，把当次 `WORKSPACE_ID`（制片工坊场景也写作 `SP_ID`）当作本任务常量。无限画布再把当次 `CANVAS_ID` 当作常量。这两个值只存在于本任务会话，不要写入磁盘绑定。

确认之后，需要工作区的读/写业务命令必须带 `--workspace WORKSPACE_ID`（或该命令已有的位置参数 `SP_ID`）。无限画布的 `node` 命令同时带 `--canvas CANVAS_ID`。不要用环境变量 `REELMATE_WORKSPACE_ID` 代替 flag，不要加 `--global`，不要执行 `workspace use`。

探测步（未确认前的 `workspace list` / `workspace show` / 首次 `workflow detect`）保持只读，可以不加 `--workspace`。

## 创建画布

仅无限画布场景在已有 `WORKSPACE_ID` 且没有目标画布时执行：

```bash
reelmate canvas create CANVAS_NAME \
  --workspace WORKSPACE_ID --space SPACE_ID \
  --idempotency-key CANVAS_KEY --json
```

`CANVAS_ID` 取 `data.data.canvas_id` 或 `data.canvas_id`。同一返回通常还有 `episode_id`，生成剧集画布深链时使用。忘记画布 ID 时用 `canvas list --workspace WORKSPACE_ID --json` 现查。

## 模型目录分区

已有项目时用 `reelmate workspace info --workspace ID --json` 的 `data.sp_type` 推出 `MODEL_SP_TYPE`，不按项目名猜。服务端没返回 `sp_type` 或 `ratio` 时不要当成 `0` 或 `16:9`。模型现查 [_models.md](_models.md)，只取当次 `model list` 的 `visible=true` 展示名。
