# 借阅单原文下载

## 什么时候读取

用户要下载借阅单里的电子原文（zip）时读取本文件。写操作前也读取共享高风险协议：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## Operation

| 阶段 | Operation | 必填输入 |
| --- | --- | --- |
| 准备下载 | `archive.borrow-list.download.prepare` | `dataId`；可选 `exportType`、`exportStructure`、`groupField`、`documentField`、`output` |
| 确认下载 | `archive.borrow-list.download.apply` | `continuation`、`confirm=true` |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.prepare --input-json '{"dataId":"1302806508947652629"}'

weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.prepare --input-json '{"dataId":"1302806508947652629"}'

weaver-work-cli --profile eteams --json archive run archive.borrow-list.download.apply --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

分组导出示例（按条目导出，条目分组字段用档号）：

```json
{"dataId":"1302806508947652629","exportType":"1","exportStructure":"0","groupField":"archival_code","documentField":""}
```

## 执行过程

1. `.prepare` 校验两项前置条件：未超期、存在可下载电子原文；任一不满足直接报错，不要绕过。
2. `.apply` 提交异步打包任务，每 2 秒轮询一次进度，完成后取文件 ID 下载 zip。
3. 默认保存到当前用户的「下载」目录，文件名由服务端返回；已存在同名文件时自动加序号，不覆盖已有文件。
4. 返回 `savedPath`、`fileName`、`fileId`、`size`；把保存路径告诉用户。

## 注意

- 下载是异步任务，`.apply` 可能持续一段时间；进度只在终端以进度条形式反馈，Agent 不要因为等待就中断并重试。
- 打包完成前中断会浪费一次服务端任务；中断后如需继续，重新执行 `.prepare` 再 `.apply`。
- 涉及本地文件写入：下载到的 zip 可能包含敏感档案内容，**必须先提醒用户文件内容会落到本地磁盘并可能进入当前大模型上下文，等待用户明确确认后才执行 `.apply`**。
- `exportType=0`（直接导出）时其余三个分组字段必须为空；`exportType=1` 时按结构补齐分组字段，字段取值只能取档案基础字段候选。
