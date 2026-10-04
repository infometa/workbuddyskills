# 薪酬查询

## 何时使用

需要查询工资单、社保公积金福利、调薪记录、社保台账或员工薪资明细时使用。全部为只读操作。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `ehr.salary.bill.list` | 无 | 分页查询**当前登录人**的工资单；也用于取得详情接口的 `salaryInfoId` |
| `ehr.salary.bill.get` | `salaryInfoId` | 查看某一张**已发放**工资单的完整展示数据 |
| `ehr.salary.welfare.list` | 无 | 社保、公积金及其他福利缴费汇总与动态明细 |
| `ehr.salary.adjustment.list` | 无 | 薪资项目调整记录；`startYear` 与 `endYear` 必须成对提供 |
| `ehr.salary.siaccount.query` | 至少一个范围条件 | 社保台账详情，需薪酬社保台账权限 |
| `ehr.salary.employee.list` | 无 | 员工薪资明细，需薪酬统计权限 |

`ehr.salary.bill.list` 与 `ehr.salary.employee.list` 的月份参数只接受 1 或 2 项（`[开始月, 结束月]`）。超过 2 项时服务端仅保留第 1 项，CLI 会直接拒绝，避免静默返回错误范围。

`ehr.salary.siaccount.query` 不分页且返回高度敏感数据，CLI 强制要求至少提供月份范围或人员/组织 ID 之一，否则拒绝执行。

`billStatus` 取值 `0`（未归档）/`1`（已归档）；`paymentStatusList` 取值 `0` 正常缴纳、`1` 补缴、`2` 代缴、`3` 退差、`4` 补差。**这两个枚举在运行时校验**：传非法值会直接报 `enum_invalid` 而不发请求。这一点很重要——早期版本未校验时，非法值会被服务端静默忽略并返回空数组，调用方会误判为"没有数据"。

`startBillMonth` 与 `endBillMonth` 是**月份**（`YYYY-MM`），必须成对提供，否则报 `month_range_incomplete`；倒序报 `month_range_invalid`。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.salary.bill.list --input-json '{"current":1,"pageSize":20}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"current":1,"pageSize":20}' | weaver-work-cli --profile eteams --json ehr run ehr.salary.bill.list --input -
```

按薪资月份查询工资单：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.salary.bill.list --input-json '{"salaryYearMonth":["2026-01","2026-03"]}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"salaryYearMonth":["2026-01","2026-03"]}' | weaver-work-cli --profile eteams --json ehr run ehr.salary.bill.list --input -
```

## 输出处理

- 成功 JSON 顶层是 `ok=true` 与 `data`；分页信息在 `meta.page`。
- `bill.list` 返回的记录中 `status=0` 表示未发放。查看未发放的工资单会失败，只有已发放的才能取详情。
- 工资单含高度敏感的个人薪酬数据。回复用户时给摘要和关键字段，不要原样粘贴完整 JSON。
- `welfare.list` 与 `adjustment.list` 在无数据时返回 `data: null`（**不是**空数组，也不是缺省 `data` 键）。判断是否"无记录"要看 `data` 是否为 `null` 或空数组，不要只看键是否存在。
- `bill.get` 返回的 `employeeInformation`、`salaryGroups`、`salaryTemplate`、`formData` 都是**模板驱动的动态结构**，字段随企业配置变化，消费时按实际返回处理，不要写死字段名。稳定字段有 `tenantName`、`sendTime`、`ackStatus`、`ackAutoStatus`、`feedbackStatus`、`senderId`、`sendMsgId`、`countdown`。
- `bill.get` 是读取操作，但**会记录首次查看时间及查看环境信息，不是完全无痕查询**；只有用户明确要查看详情时才调用。
- 该接口只查"我的"工资单：`salaryInfoId` 必须来自 `bill.list` 返回的当前用户记录，**不要尝试查询他人记录**。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 注意

- `ehr.salary.bill.get` 会记录首次查看时间，**不是完全无痕查询**。执行前先向用户说明这一点。
- `ehr.salary.employee.list` 的 `idNo` 是身份证号，属于敏感字段，非必要不要传入，也不要把返回值中的身份证号回显给用户。
- `ehr.salary.siaccount.query` 与 `ehr.salary.employee.list` 需要管理权限，当前登录人没有权限时会返回业务失败，不要反复重试。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 二次身份验证 token（重要，2026-09-04 补齐）

工资单相关的 **4 个接口**都要求携带 `token`，它用于二次身份验证，**与登录凭证无关**，也不由认证链路提供：

| operation | token 位置 |
|---|---|
| `ehr.salary.bill.list` | body |
| `ehr.salary.bill.get` | query |
| `ehr.salary.welfare.list` | query |
| `ehr.salary.adjustment.list` | query |

规则：

- 用户**主动提供**了二次验证 token 时使用原值；
- 用户**未提供时** CLI 自动补固定协议值 **`DONT_NEED`**；
- **不得传空值，也不得自行构造其他值**；
- 不要尝试从登录态或认证链路获取该值。

`ehr.salary.siaccount.query` 与 `ehr.salary.employee.list` **不需要** token。

相关错误码：

| 错误码 | 含义 | 处理 |
|---|---|---|
| `checkSecondFailNoToken` | `token` 缺失或为空 | CLI 已自动补 `DONT_NEED`，出现此错误说明该环境不接受缺省值 |
| `checkSecondFail` | 二次验证失败，或传入值不被当前环境接受 | 用户已提供 token 时请其确认有效性；用 `DONT_NEED` 仍失败则如实返回，**没有 Skill 能自动获取真实 token** |
| `checkSecondError` | 二次验证服务异常 | 停止并说明异常，**不得绕过验证读取数据** |

> 关键陷阱（2026-09-04 修复）：这些失败码到达时 HTTP 仍是 **200 且 `status` 仍为 `true`**，仅 `msg` 变为失败码、`data` 缺失。CLI 已在业务成功判定**之前**按 `msg` 精确识别并抛出明确 API 错误（`second_auth_token_missing` / `second_auth_failed` / `second_auth_error`），**不再**把这些失败静默吞成 `data: null`。代理看到上述子类型错误即代表二次验证失败，应如实反馈给用户，不要误读为"查询成功但没有数据"。

安全要求：用户提供的真实 token 属敏感信息，**不得记录、回显或长期缓存**。

## 失败处理

- `month_range_invalid`：月份格式不是 `YYYY-MM`，或数量超过 2 项，或开始月晚于结束月。
- `year_range_incomplete`：`startYear` 与 `endYear` 只提供了一个。
- `siaccount_scope_required`：社保台账查询未提供任何范围条件，必须补月份范围或人员/组织 ID。
- `salary_info_id_required` / `salary_info_id_invalid`：`salaryInfoId` 缺失或不是数字 ID。
- 认证类错误：引导用户断开并重新连接本连接器，不要读取或解析认证目录。
