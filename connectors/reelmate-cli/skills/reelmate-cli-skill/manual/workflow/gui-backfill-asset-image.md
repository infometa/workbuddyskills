# GUI 回填：资产图文件包

用户已准备好角色、场景、道具图片文件，批量上传并创建为项目资产。本流程不执行 AI 生图。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_stage-machine.md](_stage-machine.md)。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/6 | 定位唯一项目 | 已确定唯一 `SP_ID` |
| 2/6 | 分析文件并确认映射 | 每行含 `path`、`type`、`name`、是否存主体；分类不清已停下 |
| 3/6 | CLI 能力门 | `reelmate resource --help` 列出 `file-import` |
| 4/6 | 上传图片 | 每个成功文件有 `FILE_ID`；失败项单列 |
| 5/6 | 按类型 `file-import`，可选保存主体 | `success_list[]` 已读取；选中角色的 `batch-confirm` 已成功或未选择 |
| 6/6 | 交叉证明并交付 | 见下方 `done_when` |

## 1. 定位项目

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate workspace show --json
```

无项目则停止并回到 [gui-script-video-project.md](gui-script-video-project.md)。多个候选让用户选择。

## 2. 分析文件并确认映射

先只读扫描，不上传、不创建资产。支持文件夹分类（顶层 `character` / `scene` / `prop`）或映射表（每行至少 `path`、`type`、`name`）。

必须经过 HITL：

1. 分类或命名不清、同一文件落入多个分类时，让用户修正。不凭图片内容猜类型。
2. 确认“各图片名称去掉扩展名后就是资产名称”，或提供 `path → name` 映射。
3. 确认是否把角色保存为 Seedance 主体：不保存 / 全部角色 / 明确名称列表。场景和道具不能保存为主体。

空名称、重名、重复路径、不支持的扩展名或文件不存在时列出问题项并停下。

## 3. CLI 能力门

```bash
reelmate resource --help
```

帮助必须列出 `file-import`。缺少则停止并报告“当前 CLI 缺少 resource file-import”。不把 `file_id` 作为额外字段传给 `resource add`，不用 `resource import` 做本地图导入，也不把“已创建空资产”报成回填完毕。

## 4. 上传图片

```bash
reelmate upload IMAGE_FILE --json
```

从每条 `data.file_id` 建立 `path → FILE_ID`。失败文件单列；已成功的不重复上传。同一资产多张图时，把多个 `file_id` 拼成逗号分隔的单个字符串，不要改成数组。

## 5. 按类型 file-import

按确认后的映射组装条目，再按 `type` 分组。同一次 `file-import` 只允许一种类型。Web 单次最多 20 条是前端限制，CLI 不截断；可按 20 条拆批。每批先预演再提交：

```bash
reelmate resource file-import SP_ID --set @characters.json --dry-run --json
reelmate resource file-import SP_ID --set @characters.json --idempotency-key KEY --json
```

从 `data.success_list[]` 读取最终 `resource_id`、`name`、`resource_type`、`status`、`file_id`。后端可能因重名改名，后续匹配以 `success_list` 为准。`file-import` 成功即已定稿，不必再调 `resource confirm`。

用户选中要保存为主体的角色，用返回的 `resource_id`：

```bash
reelmate resource batch-confirm SP_ID \
  --set 'resource_ids=["ROLE_RESOURCE_ID"]' \
  --set 'business_list=[3]' --dry-run --json
```

未选择保存主体的角色，以及场景、道具，不要传 `business_list`。`file-import` 本身不传 `business_list`。不用 `subject from-resource` 重复创建已经存在的项目资产。

## 6. 交叉证明与交付

```bash
reelmate resource list SP_ID --json
```

先确认 `data.has_more=false`，否则按 `data.next_page` 继续取或加 `--set resource_type=`。

`done_when`：

- 每个输入文件都能在 `success_list` 与 `resource list` 中交叉证明到项目资产（用返回的 `resource_id` / `name`）；
- 资产类型与确认后的映射一致；
- `success_list` 中的 `file_id` 覆盖本批上传结果；
- 被用户选中的角色已经保存为 Seedance 主体，或相应 `batch-confirm` 已成功返回。

任一项无法证明时不报完成。部分失败只重跑失败项。

有剧本上下文时用 `deeplink asset-result`（需真实的剧本名和集数）；否则用 `deeplink project`。不编造参数，不用全局 `deeplink asset-lib` 冒充当前项目资产库。交付 `data.href`、成功 `resource_id`、失败项，以及实际保存为主体的角色列表，并输出 [_hard-gate.md](_hard-gate.md) 固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留；导入类无生成 `task_id` 时不输出积分消耗）。
