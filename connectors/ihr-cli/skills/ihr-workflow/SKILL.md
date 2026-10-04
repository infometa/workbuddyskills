---
name: ihr-workflow
description: "iHR360 审批流台账查询。按大类、状态、小类、部门查询数量或列表；用户给部门名称而非 departmentId 时，必须先调用 ihr-master-data 解析，不能改用组织树。"
metadata:
  requires:
    bins: ["ihr-cli"]
  cliHelp: "ihr-cli workflow --help"
---

# iHR360 审批流

用于 workflow 审批台账数据查询。当前支持两类业务意图：

- 查询数量/总数：例如“我想查看考勤假期审批中的数量是多少”
- 查询列表：例如“查看考勤假期审批中的列表”

如果用户按部门名称提出筛选，而目标字段需要 `departmentId`，必须先使用 [`ihr-master-data`](../ihr-master-data/SKILL.md) 解析 `DEPARTMENT`；用户已有数字部门 ID、下游只需要 ID，或列表已经返回部门名称时不解析。Workflow 命令保持 raw，不增加增强 flag。

部门名称筛选的固定流程：

1. 执行 `ihr-cli master-data +search --type DEPARTMENT --keyword "<部门名称>" --permission-code approval.list.view`。
2. 唯一候选才把数字 ID 传给 `workflow ledger +count/+list --department-id`；多候选先向用户消歧。
3. 不得改用 `organization +orgTree`、nameMap 或 raw API 查部门 ID。

台账数量必须使用 `workflow ledger +count`，不改用 raw HTTP。

## 命令路由

| 用户意图 | 优先命令 | 参考文档 |
| --- | --- | --- |
| 查询审批台账数量/总数 | `ihr-cli workflow ledger +count` | [`references/ihr-workflow-ledger-count.md`](references/ihr-workflow-ledger-count.md) |
| 查询审批台账列表 | `ihr-cli workflow ledger +list` | [`references/ihr-workflow-ledger-list.md`](references/ihr-workflow-ledger-list.md) |

## 自然语言封装规则

先从用户提示词中识别意图、大类、页签/状态或具体小类，再调用 shortcut。中文只作为 shortcut 入参，不能直接作为接口 payload。

| 自然语言片段 | 封装规则 |
| --- | --- |
| “数量”“总数”“多少” | 使用 `ihr-cli workflow ledger +count` |
| “各状态”“状态分别多少条”“按状态统计” | 使用 `ihr-cli workflow ledger +count --status "全部"`，读取 `response.statusSummary`；结果状态按 reference 转中文展示，不要对 `PASS`/`DENIED`/`ABANDONED`/`WITHDRAW`/`CANCEL`/`DRAFT` 分别调用 `+count` |
| “列表”“明细”“前几条” | 使用 `ihr-cli workflow ledger +list`；未指定条数时不要传 `--rows`，默认 10 |
| “考勤假期” | `--category "考勤假期"`，接口映射为 `groupCode=GROUP_ATTENDANCE` |
| “人事相关” | `--category "人事相关"`，接口映射为 `groupCode=GROUP_PERSONNEL` |
| “招聘相关” | `--category "招聘相关"`，接口映射为 `groupCode=GROUP_RECRUIT` |
| “薪资福利” | `--category "薪资福利"`，接口映射为 `groupCode=GROUP_SALARY_BENEFIT` |
| “智搭云” | `--category "智搭云"`，接口映射为 `groupCode=GROUP_SMART_APP` |
| “其他” | `--category "其他"`，接口映射为 `groupCode=OTHER` |
| “审批中” | `--status "审批中"`，接口映射为 `tabCode=INITIATE` |
| “办理中” | `--status "办理中"`，接口映射为 `tabCode=HANDLE` |
| “异常” | `--status "异常"`，接口映射为 `tabCode=ABNORMAL` |
| “全部” | `--status "全部"`，接口映射为 `tabCode=ALL` |
| “休假”“入职”“录用审批-单个”等具体小类 | `--tab "<小类中文名>"`，接口映射为对应 ApprovalModelShowType `tabCode` |
| 明确的 `VACATION`、`SMART_APP` 等 code | `--tab-code <code>`，或兼容使用 `--model-show-type <code>` |

示例：

```bash
ihr-cli workflow ledger +count --category "考勤假期" --status "审批中"
ihr-cli workflow ledger +list --category "考勤假期" --status "审批中"
ihr-cli workflow ledger +list --category "人事相关" --tab "入职"
ihr-cli workflow ledger +count --tab-code VACATION
```

例如“查询研发3组的考勤假期审批台账列表”必须先执行上面的 `master-data +search`，然后执行：

```bash
ihr-cli workflow ledger +list --category "考勤假期" --department-id 1001
```

不要把 `--category` 写成 `attendance`；自然语言大类使用表中的中文值，或者显式使用 `--group-code GROUP_ATTENDANCE`。

用户说“我想查看考勤假期审批中的数量是多少”时，必须封装为：

```bash
ihr-cli workflow ledger +count --category "考勤假期" --status "审批中"
```

需要确认参数或返回语义时读取本 Skill 的 reference 和命令 help；Agent 不自行拼接底层请求 payload。

## 使用规则

1. 审批台账数量和列表查询优先使用 shortcut，不直接调 raw HTTP。
2. 大类映射为 `groupCode`；状态页签和具体小类都映射为 `tabCode`。
3. 不要让 Agent 自己拼请求 payload；由 shortcut 统一完成中文到英文 code 的映射。
4. 不向用户索要 `companyId`、`userId`、token 或 cookie；身份上下文由 gateway/session 提供。
5. 对用户回复时不要原样输出 JSON。优先使用 shortcut 返回的 `response.summary`；其中页签和结果状态 code 必须按 reference 的“结果状态展示映射”转成中文。列表场景再把 `response.items` 渲染成简洁列表。
6. `response.content` 是业务原始数据，只用于排查或补充字段，不作为默认用户展示内容。
7. 列表场景未指定返回条数时，shortcut 默认 `rows=10`，回复时必须展示 `response.items` 中的全部记录；不要只展示 1 条或 3 条。
8. 需要确认精确参数或返回语义时，读取 [`references/ihr-workflow-ledger.md`](references/ihr-workflow-ledger.md) 和命令 help。

## 回复规范

数量查询：

```text
考勤假期审批中共有 3707 条审批单。
```

列表查询：

```markdown
考勤假期审批中共有 3707 条审批单，当前展示第 1 页前 10 条中的 10 条。

| 序号 | 审批编号 | 审批名称 | 类型 | 发起人 | 当前处理人 | 状态 | 发起时间 | 摘要 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 202607160002 | 外出1 | 外出 | 飘零半生 | U01 | 审批中 | 2026-07-16 11:08:10 | 时间区间:2026-07-16 11:00-2026-07-16 12:07 1小时\|地点:wqwq\|申请事由:wqwq |
| 2 | 202607150005 | 加班（批量拆单） | 加班 | U12 | 飘零半生 | 审批中 | 2026-07-15 13:53:49 | 加班类型:工作日加班\|时间区间:2026-07-13 03:00-2026-07-13 04:00 1小时\|申请事由:颠三倒四 |
```

列表字段从 `response.items[]` 读取：`序号`、`审批编号`、`审批名称`、`类型`、`发起人`、`当前处理人`、`状态`、`发起时间`、`摘要`。回复时必须用表头标注字段含义，不能用 `审批编号 | 审批名称 | 类型` 这种无表头拼接。字段为空时跳过或留空，不要展示 `null`、`undefined` 等占位。示例只展示两条格式，真实回复按 `response.items` 全量渲染；默认场景通常是 10 条。

## 对外 Shortcut

| Shortcut | 用途 |
| --- | --- |
| `workflow ledger +count` | 按 `groupCode + tabCode` 查询审批台账数量。 |
| `workflow ledger +list` | 按 `groupCode + tabCode` 查询审批台账列表，默认返回前 10 条。 |

## HR 流程代理与流程设置

本 skill 也覆盖 HR 管理端流程代理和流程设置的只读查询。所有身份上下文仍由 gateway/session 提供，不向用户索要 `companyId`、`userId`、token 或 cookie。

| 用户意图 | 优先命令 | 参考文档 |
| --- | --- | --- |
| 查询谁代理了谁、某人被谁代理、某人代理了谁 | `ihr-cli workflow proxy +list` | [`references/ihr-workflow-proxy.md`](references/ihr-workflow-proxy.md) |
| 查询流程设置模板总数、某分组下多少模板 | `ihr-cli workflow setting +count` | [`references/ihr-workflow-setting.md`](references/ihr-workflow-setting.md) |

### 流程代理路由

| 自然语言片段 | 封装规则 |
| --- | --- |
| “谁代理了谁”“流程代理关系” | `ihr-cli workflow proxy +list` |
| “张三被谁代理” | 先执行 `ihr-cli base +selectStaffs --searchKeyword "张三" --pageNo 1 --pageSize 10`；唯一命中后取 `response.data.dataList[0].id`，再执行 `ihr-cli workflow proxy +list --client-staff-id <id>` |
| “李四代理了谁” | `ihr-cli workflow proxy +list --proxy-staff-name "李四"` |
| “请假流程有哪些代理” | `ihr-cli workflow proxy +list --approval-setting-name "请假"` |

姓名解析规则：

1. 用户问“某人被谁代理”时，不要把姓名当 `staffId`，也不要直接猜员工 ID。
2. 先用 `base +selectStaffs` 搜索候选；只有唯一候选时才用 `--client-staff-id` 精确查询。
3. 候选超过 1 个时，先让用户确认具体员工。
4. 没有候选时，可以退化为 `--client-staff-name` 姓名模糊查询，并在回答里说明不是精确 staffId 查询。
5. 后端 `ProxySearchRequest` 当前没有 `proxyStaffId` 查询字段，所以“某人代理了谁”仍按 `--proxy-staff-name` 查询。

### 流程设置路由

| 自然语言片段 | 封装规则 |
| --- | --- |
| “一共有多少模板”“流程设置多少模板” | `ihr-cli workflow setting +count` |
| “考勤假期分组下有多少模板” | `ihr-cli workflow setting +count --group-name "考勤假期"` |
| “启用模板有多少”“可用模板有多少” | 加 `--status 启用` |
| “禁用模板有多少”“停用模板有多少” | 加 `--status 禁用` |

流程设置默认模板数按 `approvalSettingListVos` 长度统计；启用模板数按 `processSum` 统计；禁用模板数按 `approvalSettingListVos[].status == DISABLE` 统计。用户没有明确说“启用/可用/禁用”时，不要加 `--status`，但可以在回答里同时展示启用数和禁用数。`--enabled-only` 仅作为旧兼容入口，不要在新路由中优先使用。

## HR 只读边界

1. 流程代理只暴露 `proxy +list` 查询，不调用新增、编辑、删除接口。
2. 流程设置只暴露 `setting +count` 统计，不调用发布、删除、启停或保存接口。
3. 需要精确参数或返回语义时，分别读取对应 reference 和命令 help。
