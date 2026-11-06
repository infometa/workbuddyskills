---
name: zhizai-note
version: 1.0.0
description: 使用智在记录 CLI 查询、创建（文字）、更新和删除笔记，并查看处理进度。
---

# 智在记录笔记

通过官方 `zhizai` CLI 完成真实操作。参数与字段说明见仓库内 `skills/zhizai-open-platform/references/note.md`。

## 已可用

| 意图 | 命令 |
|---|---|
| 笔记列表 | `zhizai notes -o json` |
| 笔记详情 | `zhizai note get <id> -o json` |
| 创建文字笔记 | `zhizai note create --title <标题> --content <正文> -o json` |
| 更新笔记 | `zhizai note update <id> --title/--abstract/--summary -o json` |
| 删除笔记 | `zhizai note delete <id> --yes -o json` |
| 处理进度 | `zhizai note status <id> -o json` |

说明：

- `create` 当前仅支持 `--type text`（默认）。录音/文档/图片/链接依赖 `file upload`，尚未开放。
- `delete` 必须带 `--yes`。
- `update` 的 `--abstract` 对应接口字段 `abstractContent`。

## 尚未实现（勿调用）

| 意图 | 命令 |
|---|---|
| 上传文件 | `zhizai file upload <path>` |
| 问答总结 | `zhizai ask "<问题>"` |
