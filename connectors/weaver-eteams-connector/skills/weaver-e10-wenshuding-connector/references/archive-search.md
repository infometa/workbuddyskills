# 全文检索可借档案

## 什么时候读取

用户要按关键词查找档案、要为“加入借阅车/发起借阅”准备档案标识时读取本文件。

## Operation

| Operation | 必填输入 | 说明 |
| --- | --- | --- |
| `archive.search.run` | `key`；可选 `pageNo`（从 0 开始，默认 0）、`pageSize`（默认 10）、`type1`、`type2` | 返回命中行的 `id`、`formId`、`title`、`content` 等 |

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
```

## 结果展示（默认样式限定：卡片视图）

检索命中结果的**默认返回显示样式是「卡片视图」**：标题可点击、每条固定三段（`序号.【类型】 可点击题名` / 命中高亮 / `全宗·分类·日期`）。除用户明确要求 text / html / 表格等其他样式外，一律用本样式，不要退化成普通表格或贴 JSON。直接让 CLI 渲染卡片即可（自动注入当前 baseUrl）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams archive search --key 会计凭证 --page-size 10 --format card
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams archive search --key 会计凭证 --page-size 10 --format card
```

`--format` 还支持 `text`（终端纯文本）与 `html`（可 `--output <path>` 落 HTML 文件）；不带 `--format` 时默认输出 JSON envelope，仅供后续 operation 取参数用。

### 手工拼卡片时的排版红线（否则序号会全部渲染成 1）

卡片的第二、三段（命中摘要、`全宗·分类·日期`）**必须缩进 3 空格**，与 `1. ` 之后的内容列对齐：

```text
1. **【原文】** [题名](https://host/sp/custom/archive/archiveView?arcId=...&arcFormId=...)

   命中正文摘要（**高亮词**）

   全宗：xxx　分类：xxx　文件形成时间：2026-01-23
```

不缩进时，Markdown 会把这两段判定为列表外段落，下一条 `2.` 被当成**新列表的起点**，渲染结果里所有序号都显示成 1。因此优先直接用 CLI 的 `--format card` 输出（已内置缩进），不要手工重排。

## 结果复用

- 结果行的 `id` 是档案数据 ID，`formId` 是所属表单 ID；两者组合成 `{档案ID}_{表单ID}`，可直接用于 `archive.info.get`、`archive.flow.search.prepare` 的 `arcIds`。
- 加入借阅车时按 `formId` 分组：`formAndIds: [{ formId, ids: [档案ID...] }]`，同表单的多条档案合并到一组。

## 注意

- 检索结果只用于展示和用户选择；不要把内部 ID 当作最终展示内容，也不要让用户手工背诵 ID。
- 用户没有要求全量时不要自动翻页到底；先取 `pageSize=10`，按 `pageNo` 继续。
- 只看摘要不足以判断可借性时，再用 `archive.info.get` 查看档案基本信息。
