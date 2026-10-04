# 预归档上传

## 什么时候读取

用户要把本地文件上传到预归档电子文件库时读取本文件。写操作前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 准备上传 | `archive.upload.prelib.prepare` | `file`、`fondsId`；可选 `treeId` |
| 确认上传 | `archive.upload.prelib.apply` | `continuation`、`confirm=true` |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.upload.prelib.prepare --input-json '{"file":"./档案.pdf","fondsId":"1042286256822697531"}'

weaver-work-cli --profile eteams --json archive run archive.upload.prelib.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.upload.prelib.prepare --input-json '{"file":"./档案.pdf","fondsId":"1042286256822697531"}'

weaver-work-cli --profile eteams --json archive run archive.upload.prelib.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 前置参数

- `fondsId` 取 `archive.fonds.list` 返回的全宗 `id`（不是 `fonds_code`）。
- `treeId` 取 `archive.prelib.tree` 返回的电子文件库节点 `id`；不传时 CLI 自动取唯一节点，存在多个节点会要求显式传入。
- `file` 是本地文件路径，CLI 会校验存在性、非空和大小上限（200MB）。

## 注意

- 涉及附件、图片、本地文件：执行前必须提醒用户，**文件内容会被上传到 E10 文书定档案系统，并可能进入当前大模型上下文**用于理解和处理；必须等待用户明确确认后才调用 `.apply`。用户仅提供文件路径或文件名不等于同意上传。
- 目标全宗和电子文件库节点必须明确；`archive.prelib.tree` 返回多个电子文件库节点时，先让用户选择再上传，不要自行猜测。
- 上传链路为 `preUploadCheck` → `module/upload` → `saveFile`；任一步失败会直接报错，不要自动重放 `.apply`。
- 默认不覆盖、不删除本地文件；上传成功后返回 `fileId`、`docId`、`fileName`、`treeId`、`fondsId`。
