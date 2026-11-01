# GUI 环节 2：剧本导入与解析

只在当前包为 `script` 或 `missing` 含 `episode` 时读取。必须先定位 `SP_ID`。

## 步骤表

| 步 | 动作 | 完成谓词 |
|---|---|---|
| 1/1 | 上传剧本并拆集 | 工坊剧集（`episode list --set creation_mode=1`）或 `episode split-list` 非空；若本次提交了拆集任务，该任务终态成功 |

若工坊剧集（`episode list --set creation_mode=1`）或 `episode split-list` 已有结果，视为剧本已解析，不重复上传和拆解。仅有画布剧集时仍须 `upload` + `episode split`。

从 [generate-script.md](generate-script.md) 交接进入时，`SCRIPT_FILE` 为 `outputs/script.txt`，`SP_ID` 即该画布项目的 `WORKSPACE_ID`。

剧集拆分不消耗积分。提交 `episode split` 前不要查询积分预估，也不要向用户展示拆集的预计消耗、报价来源、积分消耗或余额扣费说明。`episode split` 返回的 `task_id` 只用于等待任务，不计入完成总结的生成任务数，也不要为这一步写积分消耗。

```bash
reelmate workflow detect --scope studio --workspace SP_ID --json
reelmate episode list --workspace SP_ID --set creation_mode=1 --json
reelmate episode split-list SP_ID --json
reelmate upload SCRIPT_FILE --json
reelmate episode split SP_ID --set file_id=FILE_ID --json
```

响应含 `task_id` 时：

```bash
reelmate task wait TASK_ID --timeout 30m --json
reelmate episode split-list SP_ID --json
reelmate episode list --workspace SP_ID --set creation_mode=1 --json
```

记录 `SCRIPT_FILE_NAME`、拆集结果和 `EPISODE_TOTAL`，后续深链需要这些值。
