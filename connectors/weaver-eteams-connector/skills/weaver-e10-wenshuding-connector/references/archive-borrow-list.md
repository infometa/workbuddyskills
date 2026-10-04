# 借阅单

## 什么时候读取

用户要查看自己的借阅单、要看借阅单明细、要为下载或续借准备参数时读取本文件。

## Operation

| Operation | 必填输入 | 说明 |
| --- | --- | --- |
| `archive.borrow-list.list` | 可选 `pageNo`（默认 1）、`pageSize`（默认 10） | 借阅单列表，含 `dataId`、`workflowId`、借阅/归还时间、状态与是否超期 |
| `archive.borrow-list.detail` | `dataId` | 借阅单详情，含明细的原文借阅方式与可下载判定 |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.borrow-list.list --input-json '{"pageNo":1,"pageSize":10}'

weaver-work-cli --profile eteams --json archive run archive.borrow-list.detail --input-json '{"dataId":"1302806508947652629"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.borrow-list.list --input-json '{"pageNo":1,"pageSize":10}'

weaver-work-cli --profile eteams --json archive run archive.borrow-list.detail --input-json '{"dataId":"1302806508947652629"}'
```

## 结果展示（默认样式限定：表格）

借阅单列表给用户时**一律用 Markdown 表格渲染**，不要用卡片、普通编号列表或 JSON：

| 序号 | 题名 | 借阅时间 | 归还时间 | 归还状态 | 是否超期 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | …（超长省略） | 2026-08-01 | 2026-08-31 | 借阅中 | 否 |

- 列取借阅单返回的可读字段（题名、借阅/归还时间、状态、`expired` 等），最多先给 10 条；不要把 `dataId`、`workflowId` 等内部 ID 作为展示列。
- 表格样式：所有列（表头与内容）居中显示。
- 无值列留空或用 `-`；题名过长时截断。

## 字段复用

- `dataId` 是借阅单主表 ID，用于查看详情、下载和续借。
- `workflowId` 是流程 requestId，下载打包任务需要；CLI 会自动取用，Agent 不需要手工传。
- 列表行带 `expired`（是否已超期）；详情带 `downloadable`（是否存在可下载电子原文）与 `borrowTypes`。

## 注意

- 列表同样优先自定义接口，未发布时自动回退 ebuilder 链路，回退行提供 `fields`/`display`。
- 借阅单状态以“借阅时间/归还时间/是否超期/归还状态”等可读字段展示；不要把 `workflowId` 等内部 ID 直接展示给用户。
- 下载前必须先确认未超期且存在可下载原文，这一步由 `archive.borrow-list.download.prepare` 统一校验，不要跳过。
