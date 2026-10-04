# 通讯录与人员查询

## 何时使用

查询通讯录在职人员、获取可展示字段、按名称解析部门/岗位等 ID、查询过生日人员、查询人员状态变更台账时使用。全部为只读操作。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `ehr.hr.contact.fields` | 无 | 通讯录可展示字段及 key，是 `contact.search` 的前置步骤 |
| `ehr.hr.contact.sa` | 无 | 高级搜索条件定义与可选项 |
| `ehr.hr.contact.search` | 无 | 分页查询在职人员 |
| `ehr.hr.contact.count` | 无 | 只统计数量，不返回列表 |
| `ehr.hr.browser.complete` | `type`,`searchValue` | 按名称查部门/分部/岗位/职级/职务/上级的 id |
| `ehr.hr.birthday.conditions` | 无 | 生日查询的条件定义 |
| `ehr.hr.birthday.list` | 无 | 过生日人员查询 |
| `ehr.hr.empchange.conditions` | 无 | 状态变更的筛选字段定义 |
| `ehr.hr.empchange.list` | 无 | 人员状态变更台账 |

`ehr.hr.browser.complete` 的 `type` 取值：`department`、`subcompany`、`position`、`resource`、`jobsetid`、`grade`。该值必须取自 `ehr.hr.contact.sa` 返回的字段定义，不要臆造。

`ehr.hr.empchange.list` 的 `changeType` 取值：`trial`、`hire`、`extend`、`redeploy`、`dismiss`、`retire`、`quit`、`rehire`、`custom`。

## 命令

先取字段，再查询：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.contact.fields --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.contact.fields --input -
```

按姓名查询在职人员：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.contact.search --input-json '{"username":"张三"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"username":"张三"}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.contact.search --input -
```

查询某人（含离职）的状态变更记录：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.empchange.list --input-json '{"resourceId":123,"changeDateStart":"2026-01-01","changeDateEnd":"2026-03-31"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"resourceId":123,"changeDateStart":"2026-01-01","changeDateEnd":"2026-03-31"}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.empchange.list --input -
```

## 输出处理

- 分页信息在 `meta.page`。注意 `contact.search`、`birthday.list` 的 `pageSize` 被页面配置固定为 100，**全量数据必须递增 `current` 翻页**，改 `pageSize` 无效。
- `ehr.hr.browser.complete` 返回 `candidates`、`total` 和 `requiresDisambiguation`。当 `requiresDisambiguation=true` 时必须列出候选让用户选择。
- 人员状态变更的 `changeDateStart` 与 `changeDateEnd` 必须用两个独立字段传起止，传 `changeDate` 数组格式无效。

## 注意

- **默认人员范围相反**（2026-09-04 实测，差异很大）：`contact.search` 默认只查**在职**，实测 `total=646`；传 `personnelStatus=["all"]` 后 `total=1392`。`contact.count` 同样（646 / 1392）。而 `empchange.list` 默认**包含离职人员**（`total=2843`）。查「某人是否已离职」要用 `empchange.list`，不要用 `contact.search` 反复试。
- 不要用 `["normal","6"]` 这类组合去查离职，实测无法覆盖离职人员；查离职请用 `empchange.list` 或 `contact.search` 传 `personnelStatus=["all"]` 再自行判断。
- **`containUnavailable` 实测无效**：`empchange.list` 传 `true`/`false`/不传，`total` 均为 2843，服务端忽略该字段（已确认字段被正确透传——同接口的 `changeType` 生效：`dismiss` 544 / `trial` 29 / `hire` 1065）。**不要依赖它过滤离职人员**。
- `empchange.list` 的每页条数是 **100**（不是其他接口的 20/10），`changeType` 各类型实测：默认 2843、dismiss 544、trial 29、hire 1065、日期区间 2124。
- 姓名、工号都是**模糊匹配**，多人命中时必须列出候选让用户确认，不得自动取第一条。查特定个人优先用 `resourceId`。
- `birthday.conditions` 与 `empchange.conditions` 只能通过 GET 调用，CLI 已固定为 GET，不要尝试改方法。
- 通讯录含个人联系方式等敏感信息，回复用户时只给必要字段，不要原样粘贴完整列表。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 失败处理

- `search_value_required`：`browser.complete` 缺少 `searchValue`。
- `enum_invalid`：`type`、`sex`、`changeType` 等取值不在允许集合内。
- `date_range_incomplete`：`empchange.list` 的起止日期只提供了一个。
- `date_range_invalid`：开始日期晚于结束日期。
- 认证类错误：引导用户断开并重新连接本连接器。
