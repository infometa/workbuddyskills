# 查询报告详情、报告列表与评论

## 何时使用

- 用户要看某份报告的内容（「看看小A 2026年第33周的报告」「本周我交报告了吗」）；
- 用户要看共享给自己的报告、下属的报告、团队成员的报告（「共享给我的报告」「下属这周交了吗」）；
- 用户在查看报告详情后要求查看评论内容。

对应 operation：`plan.report.get`、`plan.report.page`、`plan.comment.list`。

## 输入要点

### plan.report.get

| 字段 | 说明 |
| --- | --- |
| `id` | 报告 id；与周期参数二选一，给了 `id` 就忽略周期参数 |
| `year` | 报告年份；缺省取本年 |
| `type` | `week` / `month` / `season` / `halfYear` / `year` |
| `serialNumber` | 报告周期（正整数） |
| `creatorUserId` | 报告创建人 id；缺省为当前登录人。**禁止传 userId 之外的 ID 形态，需由 weaver-e10-hrm-connector 解析姓名** |
| `withComments` | 标准版链路下是否同时查询评论总条数，默认 `true` |

按周期查询时 `type` + `serialNumber` 必填，`year` 缺省取本年；`creatorUserId` 缺省为当前登录人。CLI 内部按周期查询为标准版链路要求，缺省值会自动补齐。

### plan.report.page

| 字段 | 说明 |
| --- | --- |
| `scope` | `share`（共享给我的，默认）/ `mine`（我自己及他人共享给我的，eb 链路按创建人筛选） |
| `unreadOnly` | 仅看未读（标准版专属，eb 链路不支持） |
| `year` / `type` / `serialNumber` | 报告筛选条件 |
| `creatorUserId` | 报告创建人 id（eb 链路支持；标准版分页接口不支持按创建人筛选，会返回警告） |
| `onlyIncludeSubs` | 是否只包含下属（标准版专属） |
| `pageNo` / `pageSize` | 默认 1 / 10，`pageSize` 最大 100；不自动翻页 |

### plan.comment.list

| 字段 | 说明 |
| --- | --- |
| `reportId` | 报告 id（必填） |
| `pageNo` / `pageSize` | 默认 1 / 10 |

## 命令

查询某份报告（按周期，本周周报）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"year":2026,"type":"week","serialNumber":36}'
```

按报告 id 查询：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"id":"PLACEHOLDER_REPORT_ID"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.get --input-json '{"id":"PLACEHOLDER_REPORT_ID"}'
```

分页查询共享给我的报告：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.page --input-json '{"pageNo":1,"pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.page --input-json '{"pageNo":1,"pageSize":10}'
```

只查下属、只看未读（标准版链路）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.page --input-json '{"unreadOnly":true,"onlyIncludeSubs":true,"pageNo":1,"pageSize":20}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.page --input-json '{"unreadOnly":true,"onlyIncludeSubs":true,"pageNo":1,"pageSize":20}'
```

查看评论内容（仅标准版链路）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.comment.list --input-json '{"reportId":"PLACEHOLDER_REPORT_ID","pageNo":1,"pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.comment.list --input-json '{"reportId":"PLACEHOLDER_REPORT_ID","pageNo":1,"pageSize":10}'
```

## 输出处理

### plan.report.get

- `exists`：报告是否存在。`false` 表示该人员该周期没有报告（用于判断是否提交）。
- `report`：统一的业务报告结构（`reportId` / `title` / `content` / `summary` / `plans` / `year` / `type` / `typeLabel` / `serialNumber` / `postStatus` / `postStatusLabel` / `postTime` / `postTimeStatus` / `creator`）。
- `detailUrl`：可直接跳转的报告详情页链接，必须呈现给用户。
- `commentCount` / `commentHint`：仅在**标准版链路且评论总条数大于 0** 时出现。

### 评论处理规则（查询单份报告详情时生效）

1. 评论总条数 = 0：只返回报告详情，**完全忽略评论模块**，不输出任何评论相关文字。
2. 评论总条数 > 0：返回报告详情，并附加提示「该报告下共有 {N} 条评论，是否需要查看评论内容？」，**禁止直接输出评论内容**。
3. 只有收到用户明确的查看评论类指令后，才调用 `plan.comment.list` 展示全部评论详情。

### plan.report.page

`rows` 中每行都是统一业务报告结构，并带 `detailUrl`。必须用表格呈现，固定列：

| 报告名称 | 报告创建人名称 | 发布时间 |
| --- | --- | --- |

- 报告名称渲染为指向 `detailUrl` 的可点击链接。
- `count` 为本页返回行数；`pageSize` 最大 100，不做自动翻页。
- `warnings` 非空时要向用户简要说明（例如标准版链路忽略 `creatorUserId`）。

## 注意

- 「某某某的报告」需要先由 weaver-e10-hrm-connector skill 把姓名解析为人员 ID，再作为 `creatorUserId` 传入；禁止把姓名直接当 ID 传。
- 标准版链路的报告列表接口语义是「共享给我的报告」，它不能按创建人过滤；需要按人筛选时改用 eb 链路或按 `plan.report.get` 精确查询。
- eb 链路未提供报告评论接口，`plan.comment.list` 会返回 `policy/link_unsupported`；此时如实告知用户该链路无法查询评论。
- 不要在只读查询场景调用业务模块采集数据。

## 失败处理

- `not_found`：目标报告不存在。按周期查询时 `exists:false` 是正常结果，不是错误。
- `validation/type_invalid` / `validation/serial_number_invalid` / `validation/year_invalid`：入参不合法，按提示修正后重试一次。
- `policy/link_unsupported`：该能力在当前链路不可用，按 `message` 说明告知用户。
- `authentication` / `session_expired`：引导用户断开并重新连接本连接器以重新登录。
