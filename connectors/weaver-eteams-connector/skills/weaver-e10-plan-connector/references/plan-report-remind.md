# 发送报告提交提醒

## 何时使用

- 查询发现部分人员在指定周期没有报告，用户确认需要提醒时；
- 用户直接要求「提醒某某交报告」「催一下团队交周报」。

对应 operation：`plan.report.remind.prepare` → `plan.report.remind.apply`（**仅标准版链路**）。

## 触发前提

1. 先用 `plan.report.get` 按周期确认目标人员在该周期确实没有报告（逐人确认，缺省创建人参数需替换为目标人员 ID）。
2. 把「哪些人缺少该周期报告」摘要给用户，并询问 **是否需要向提交人发送提交提醒**。
3. 用户明确确认后，才进入 `prepare → apply`。

不要未经确认就批量发送提醒。

## 输入要点

| 字段 | 说明 |
| --- | --- |
| `personIds` | 需要提醒的人员 ID（`["1001","1002"]` 数组或 `"1001,1002"` 英文逗号拼接字符串）。**必须由 weaver-e10-hrm-connector 解析姓名得到真实人员 ID，禁止传姓名** |
| `year` | 报告年份；缺省取本年 |
| `type` | `week` / `month` / `season` / `halfYear` / `year`（必填） |
| `serialNumber` | 报告周期（必填） |
| `content` | 提醒文案；缺省按周期生成默认文案 |

## 默认提醒文案

用户未指定文案时使用动态默认文案，年份与周期随实际条件替换：

| 报告类型 | 默认文案 |
| --- | --- |
| 周报 | 请提交{年份}年第{N}周的报告 |
| 月报 | 请提交{年份}年{N}月的报告 |
| 季报 | 请提交{年份}年第{N}季度的报告 |
| 年中报告 | 请提交{年份}年年中报告 |
| 年报 | 请提交{年份}年年度报告 |

## 命令

准备发送（含默认文案）：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.remind.prepare --input-json '{"personIds":["PLACEHOLDER_PERSON_ID"],"year":2026,"type":"week","serialNumber":36}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.remind.prepare --input-json '{"personIds":["PLACEHOLDER_PERSON_ID"],"year":2026,"type":"week","serialNumber":36}'
```

指定文案：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.remind.prepare --input-json '{"personIds":"PLACEHOLDER_PERSON_ID,PLACEHOLDER_PERSON_ID_2","type":"month","serialNumber":9,"content":"请在今天 18:00 前提交9月月报"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.remind.prepare --input-json '{"personIds":"PLACEHOLDER_PERSON_ID,PLACEHOLDER_PERSON_ID_2","type":"month","serialNumber":9,"content":"请在今天 18:00 前提交9月月报"}'
```

用户确认后发送：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json plan run plan.report.remind.apply --input-json '{"confirm":true,"continuation":"PLACEHOLDER_CONTINUATION"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json plan run plan.report.remind.apply --input-json '{"confirm":true,"continuation":"PLACEHOLDER_CONTINUATION"}'
```

## 输出处理

`prepare` 返回 `preview`：`personIds`（人员 ID 列表）、`targets`（年份/类型/周期）、`content`（实际文案）、`messageEventCode`（固定 14）以及 `continuation`。

必须把「提醒对象 + 周期 + 实际文案」摘要给用户后再执行 `apply`。

`apply` 返回 `status: COMPLETE` 与 `personIds`、`content`。

## 注意

- 人员 ID 必须来自 weaver-e10-hrm-connector 的 `id` / `employeeId`，**禁止使用 `userId`，禁止直接传姓名**。
- 提醒接口为标准版链路专属；eb 链路返回 `policy/link_unsupported`，如实告知用户当前链路无法发送提交提醒。
- 提醒属于对外发送动作，必须在用户明确确认后才 `apply`。

## 失败处理

- `policy/link_unsupported`：当前租户走 eb 链路，无提交提醒接口。
- `validation/ids_invalid` / `ids_required`：人员 ID 不合法或为空。
- `confirmation/required`：未取得用户确认。
- `partial` / `write_uncertain`：提醒是否已发送不确定，**禁止自动重试**，先向用户说明并询问是否重发。
- `api/business_error`：接口返回业务失败，按 `error.message` 说明。
