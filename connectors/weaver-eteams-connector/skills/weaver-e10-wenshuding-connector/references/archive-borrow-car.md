# 借阅车

## 什么时候读取

用户要查看借阅车、要把检索结果加入借阅车时读取本文件。加入借阅车是**免确认写操作**，直接调用即可，不需要高风险确认链。

## Operation

| 想做什么 | Operation | 必填输入 |
| --- | --- | --- |
| 查看列表 | `archive.borrow-car.list` | 可选 `pageNo`（默认 1）、`pageSize`（默认 10） |
| 加入借阅车（免确认） | `archive.borrow-car.add` | `formAndIds`（`[{ formId, ids: [...] }]`） |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'

weaver-work-cli --profile eteams --json archive run archive.borrow-car.add --input-json '{"formAndIds":[{"formId":"1190991330335571989","ids":["1252600626189156465"]}]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'

weaver-work-cli --profile eteams --json archive run archive.borrow-car.add --input-json '{"formAndIds":[{"formId":"1190991330335571989","ids":["1252600626189156465"]}]}'
```

## 结果展示（默认样式限定：表格）

借阅车列表给用户时**一律用 Markdown 表格渲染**，不要用卡片、普通编号列表或 JSON：

| 序号 | 题名 | 类型 | 分类 | 形成日期 |
| :---: | :---: | :---: | :---: | :---: |
| 1 | …（超长省略） | 电子原文 | 销售合同 | 2025-06-27 |

- 列取 `title` / `className` / `categoryNames` / `fileDate` 等可读字段，最多先给 10 条；不要把 `dataId`、`arcDangan` 等内部 ID 作为展示列。
- 表格样式：所有列（表头与内容）居中显示。
- 无值列留空或用 `-`；题名过长时截断。

## 列表字段

- 首选自定义接口，返回 `title`（题名）、`categoryNames`（分类）、`className`（类型）、`archivalCode`（档号）等可读字段，以及 `dataId`、`arcDangan`（`{档案ID}_{表单ID}`）供后续操作复用。
- 自定义接口未发布时 CLI 自动回退 ebuilder 链路，行内提供 `fields`/`display`，可读字段更少；此时不要向用户解释内部链路差异，直接按可读字段展示。
- 列表展示不依赖全宗信息，不要把全宗字段作为展示列；全宗只在预归档上传时需要查询。

## 注意

- `archive.borrow-car.add` 是**低风险写操作，不需要 prepare / apply / 用户确认链**；用户表达“加入借阅车/加入车/收藏”意图后直接提交，执行完用 `archive.borrow-car.list` 复核即可。
- `formAndIds` 必须按 `formId` 分组且 `ids` 非空；同表单的多个档案合并到同一组，不要一条一组地重复提交。
- 加入借阅车是写操作，出现网络中断或结果不确定时按 `partial/write_uncertain` 决策树处理，不要自动重放。
