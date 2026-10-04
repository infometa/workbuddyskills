# ihr-cli workflow ledger

## 目的

通过 workflow shortcut 查询审批台账。数量查询返回 `response.totalElements`；列表查询默认 `page=1, rows=10`，返回 `response.content` 并带 `totalElements`。

## 关键口径

release 前端 `approval-list/list-v2/basic-com/table.tsx` 的 `transferParamFormat` 会发送：

```json
{
  "page": 1,
  "rows": 10,
  "groupCode": "GROUP_ATTENDANCE",
  "tabCode": "INITIATE",
  "isAbnormal": false,
  "keyword": ""
}
```

release 后端 `ProcessUtil.handleTabCode(groupCode, tabCode, queryReq)` 会把 `tabCode` 转成实际查询条件：

`tabCode` 使用两类公开查询口径：

- 固定页签：`ALL`、`INITIATE`、`HANDLE`、`ABNORMAL`
- 具体小类：`VACATION`、`ENTRANCE`、`PAYROLL` 等 `ApprovalModelShowType`
- 为了让 dry-run 与线上筛选口径一致，shortcut 会显式携带异常过滤：`INITIATE`/`HANDLE` -> `isAbnormal=false`，`ABNORMAL` -> `isAbnormal=true`。

CLI 会统一完成中文大类、固定页签和具体小类到公开查询参数的映射；Agent 不拆成多次请求。

## `workflow ledger +count` / `workflow ledger +list`

### 命令

```bash
ihr-cli workflow ledger +count --category "考勤假期" --status "审批中"
ihr-cli workflow ledger +list --category "考勤假期" --status "审批中"
ihr-cli workflow ledger +list --category "人事相关" --tab "入职"
ihr-cli workflow ledger +count --tab-code VACATION
```

### 公共参数

| Flag | 类型 | 必填 | 默认值 | 值/格式 | 请求映射 |
| --- | --- | --- | --- | --- | --- |
| `--category` | string | 条件必填 | 无 | `考勤假期`、`人事相关`、`招聘相关`、`薪资福利`、`智搭云`、`其他`；也支持 group code | `request.groupCode` |
| `--group` | string | 条件必填 | 无 | `--category` 的别名 | `request.groupCode` |
| `--group-code` | string | 条件必填 | 无 | `GROUP_ATTENDANCE`、`GROUP_PERSONNEL`、`GROUP_RECRUIT`、`GROUP_SALARY_BENEFIT`、`GROUP_SMART_APP`、`OTHER` | `request.groupCode` |
| `--status` | string | 可选 | `审批中` | `审批中`/`INITIATE`、`办理中`/`HANDLE`、`异常`/`ABNORMAL`、`全部`/`ALL` | `request.tabCode` |
| `--tab` | string | 可选 | 无 | 具体小类中文名，例如 `休假`、`入职`、`录用审批-单个` | `request.tabCode` |
| `--tab-code` | string | 可选 | 无 | ApprovalModelShowType 或固定页签 code | `request.tabCode` |
| `--model-show-type` | string | 可选 | 无 | 兼容旧入参，等价于 `--tab-code` | `request.tabCode` |
| `--keyword` | string | 可选 | 无 | 普通文本 | `request.keyword` |
| `--department-id` | string | 可选 | 无 | 逗号分隔部门 ID；名称先用 `master-data +search --type DEPARTMENT --permission-code approval.list.view` 解析 | `request.departmentId[]` |
| `--approval-month-start` | string | 可选 | 无 | `yyyy-MM` | `request.approvalMonthStart` |
| `--approval-month-end` | string | 可选 | 无 | `yyyy-MM` | `request.approvalMonthEnd` |

## `workflow ledger +list` 分页参数

以下参数只适用于列表命令：

| Flag | 类型 | 必填 | 默认值 | 值/格式 | 请求映射 |
| --- | --- | --- | --- | --- | --- |
| `--page` | int | list only | `1` | 从 1 开始 | `request.page` |
| `--rows` | int | list only | `10` | 最大 `100` | `request.rows` |
| `--pageSize` | int | list only | `10` | `--rows` 别名 | `request.rows` |
| `--page-size` | int | list only | `10` | `--rows` 别名 | `request.rows` |

`approvalMonthStart/approvalMonthEnd` 在鉴权和远端调用前做本地校验；两者存在时开始月份不得晚于结束月份。非法格式或反向范围返回 exit `2`。

如果只传具体小类 `--tab/--tab-code/--model-show-type`，shortcut 会按小类推断 `groupCode`。

用户给的是部门名称而不是数字 ID 时，必须先执行统一 Resolver：

```bash
ihr-cli master-data +search --type DEPARTMENT --keyword "研发3组" --permission-code approval.list.view
ihr-cli workflow ledger +list --category "考勤假期" --department-id 1001
```

不能用 `organization +orgTree` 替代第一步。`--category` 使用中文大类，或改用显式 `--group-code GROUP_ATTENDANCE`；不要传非契约值 `attendance`。

## 大类映射

| 中文大类 | groupCode |
| --- | --- |
| 考勤假期 | `GROUP_ATTENDANCE` |
| 人事相关 | `GROUP_PERSONNEL` |
| 招聘相关 | `GROUP_RECRUIT` |
| 薪资福利 | `GROUP_SALARY_BENEFIT` |
| 智搭云 | `GROUP_SMART_APP` |
| 其他 | `OTHER` |

## 固定页签映射

| 用户说法 | tabCode |
| --- | --- |
| 全部 | `ALL` |
| 审批中 | `INITIATE`，并显式发送 `isAbnormal=false` |
| 办理中 | `HANDLE`，并显式发送 `isAbnormal=false` |
| 异常 | `ABNORMAL`，并显式发送 `isAbnormal=true` |

### 结果状态展示映射

| 后端状态 | 中文展示 |
| --- | --- |
| `INITIATE` | 审批中 |
| `HANDLE` | 办理中 |
| `ABNORMAL` | 异常 |
| `ALL` | 全部 |
| `PASS` | 通过 |
| `DENIED` | 驳回 |
| `ABANDONED` | 作废 |
| `WITHDRAW` | 已撤回 |
| `CANCEL` | 取消 |
| `DRAFT` | 草稿 |

## 具体小类映射

| 中文小类 | tabCode |
| --- | --- |
| 休假 | `VACATION` |
| 销假 | `MELT_VACATION` |
| 加班 | `OVER_TIME` |
| 组合加班 | `COMBINATION_OVERTIME` |
| 外出 | `FIELD_WORK` |
| 销外出 | `MELT_FIELD_WORK` |
| 出差 | `EVECTION` |
| 销出差 | `MELT_EVECTION` |
| 补卡 | `APPEAL` |
| 外勤打卡 | `OUT_SIGN` |
| 调班 | `SHIFT_ADJUSTMENT` |
| 请假-调休 | `LEAVE_ADJUST` |
| 组合请假-调休 | `LEAVE_ADJUST_GROUP` |
| 借调 | `SECONDMENT` |
| 新增岗位 | `ATT_ADD_POSITION` |
| 变更岗位 | `ATT_CHANGE_POSITION` |
| 需求变更 | `ATT_REQUIREMENT_CHANGE` |
| 排班 | `SCHEDULE` |
| 入职 | `ENTRANCE` |
| 离职 | `QUIT` |
| 转正 | `POSITIVE` |
| 调动 | `TRANSFER` |
| 合同续签 | `RENEW_CONTRACT_APPROVAL` |
| 黑名单 | `BLACKLIST` |
| 编制申请 | `HEADCOUNT_APPROVE` |
| 薪资费用审批 | `PAYROLL` |
| 福利费用审批 | `BENEFIT` |
| 薪资台账撤回 | `PAYROLL_CANCEL` |
| 福利台账撤回 | `BENEFIT_CANCEL` |
| 单人调薪审批 | `SINGLE_SALARY_ADJUST` |
| 批量调薪审批 | `BATCH_SALARY_ADJUST` |
| 调整转正薪资 | `ADJUST_REGULAR_SALARY` |
| 招聘需求-单个 | `RECRUIT_SINGLE` |
| 招聘需求-批量 | `RECRUIT_BATCH` |
| 录用审批-单个 | `OFFER_APPROVE` |
| 录用审批-批量 | `BATCH_OFFER_APPROVE` |
| 智搭云 | `SMART_APP` |
| 用户自定义 | `USER_CUSTOMIZATION` |

## JSON 输入

```bash
ihr-cli workflow ledger +count --json '{"category":"考勤假期","status":"审批中"}'
ihr-cli workflow ledger +list --json '{"groupCode":"GROUP_ATTENDANCE","tabCode":"INITIATE","rows":10}'
```

不要混用 `--json`/`--stdin` 和普通 flags。

## 输出

`+count` 返回：

- `summary`：shortcut 返回原始页签 code；回复用户时按“结果状态展示映射”转中文，例如 `考勤假期审批中共有 3707 条审批单。`
- `totalElements`：审批台账总记录数
- `statusSummary`：仅 `tabCode=ALL` 的数量查询返回，基于完整分页响应 `content[].status` 和 `isAbnormal/abnormal` 聚合 raw 状态码，至少包含 `INITIATE`、`HANDLE`、`ABNORMAL`、`PASS`、`DENIED`、`ABANDONED`、`ALL`，并保留响应中出现的其他 raw 状态码。回复用户时必须按“结果状态展示映射”转中文；不要把 `PASS/DENIED/ABANDONED/WITHDRAW/CANCEL/DRAFT` 当 `tabCode/status` 再发起 `+count`。
- `groupCode`
- `tabCode`
- `sourceApi`

`+list` 返回：

- `summary`：shortcut 返回原始页签 code；回复用户时按“结果状态展示映射”转中文，例如 `考勤假期审批中共有 3707 条审批单，当前展示第 1 页前 10 条中的 10 条。`
- `items`：面向用户展示的精简列表，每条包含 `序号`、`审批编号`、`审批名称`、`类型`、`发起人`、`当前处理人`、`状态`、`发起时间`、`摘要`；其中 `状态` 按“结果状态展示映射”转中文后展示
- `totalElements`：审批台账总记录数
- `content`：业务原始列表，仅用于排查或补充字段，不要默认原样展示给用户
- `page`
- `rows`

对用户输出时必须优先使用 `summary/items`，不要把 CLI 的完整 JSON envelope 或 `content` 原样贴给用户。

列表回复必须渲染成带表头的 Markdown 表格，字段顺序建议为：

| 字段 | 来源 |
| --- | --- |
| 序号 | `response.items[].序号` |
| 审批编号 | `response.items[].审批编号` |
| 审批名称 | `response.items[].审批名称` |
| 类型 | `response.items[].类型` |
| 发起人 | `response.items[].发起人` |
| 当前处理人 | `response.items[].当前处理人` |
| 状态 | `response.items[].状态` |
| 发起时间 | `response.items[].发起时间` |
| 摘要 | `response.items[].摘要` |

未指定条数时，`+list` 默认 `rows=10`。回复时应展示 `response.items` 中的全部记录，默认就是 10 条；不要只展示第一条或前三条。不要使用没有表头的 `编号 | 名称 | 类型` 拼接格式，因为用户无法判断每一列的含义。
当原始记录 `isAbnormal`/`abnormal` 为 true 时，`response.items[].状态` 的 raw code 为 `ABNORMAL` 或 `ABNORMAL(<原因>)`；回复用户时展示为 `异常` 或 `异常(<中文原因>)`，不应展示成普通 `审批中`。非异常记录的结果状态按上表展示。
