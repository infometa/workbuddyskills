# 借款管理（管理员）

## 何时使用

管理员视角的借款大盘：看全公司待还/还款中汇总 → 首页汇总；看明细/谁还欠多少 → 首页列表；向借款人发还款提醒 → **写操作**，先 prepare 再 apply。借款模块需要管理员身份登录。

| 用户意图 | operation | 风险 |
|---|---|---|
| 「全公司待还款/还款中多少钱」「借款大盘」 | `fna.loan.main.page` | read |
| 「列出所有借款单」「谁还欠多少」 | `fna.loan.main.list` | read |
| 「提醒某人/批量提醒还款」 | `fna.loan.remind.repay.prepare` / `.apply` | **write** |

## 输入要点

- `fna.loan.main.list` 必填：`current`/`pageSize`（正整数）+ `menuCode`/`permissionSetCode`。借款菜单示例 `fesx_fna_borrowingManagement` / `fesx_fna_borrowingManagement.default`，**实际值需与用户环境借款管理菜单一致**，不确定先向用户核对。
- 分页：`current` 递增直到 `hasMore=false`；页面默认分页大小 `pageSizeFromPageUid`（如 20）。
- 金额两套：`rows`（displayData）金额已格式化、`createTime` 已转字符串，**展示与回传都用 rows**；不要用原始精度列。
- 若 `total=0` 且 rows 为空 → 提示「暂无借款记录」。

## 数据流：提醒还款（写操作）

1. `fna.loan.main.list` 取目标借款单 → `rows` 中选中行（含 `id`/`workflowId`/`jkrPersonName`/`dhkAmount`）。
2. `fna.loan.remind.repay.prepare`，入参 `data` = 选中 displayData 行数组（1~200 条，原样回传不裁剪）。
3. prepare 返回 `{status:'AWAITING_CONFIRMATION', preview:{count,borrowers,totalDhkAmount,ids}, continuation}`：**向用户展示条数、借款人、剩余待还合计，取得明确确认**。
4. 用户确认后 `fna.loan.remind.repay.apply`，入参 `data`（与 prepare 相同的行）+ `confirm:true` + `continuation`（10 分钟内有效）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.loan.main.page --input-json '{"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
weaver-work-cli --profile eteams --json fna run fna.loan.main.list --input-json '{"current":1,"pageSize":20,"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
weaver-work-cli --profile eteams --json fna run fna.loan.remind.repay.prepare --input 'C:\path\to\loan-rows.json'
weaver-work-cli --profile eteams --json fna run fna.loan.remind.repay.apply --input 'C:\path\to\loan-apply.json'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.loan.main.page --input-json '{"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
weaver-work-cli --profile eteams --json fna run fna.loan.main.list --input-json '{"current":1,"pageSize":20,"menuCode":"fesx_fna_borrowingManagement","permissionSetCode":"fesx_fna_borrowingManagement.default"}'
weaver-work-cli --profile eteams --json fna run fna.loan.remind.repay.prepare --input /tmp/loan-rows.json
weaver-work-cli --profile eteams --json fna run fna.loan.remind.repay.apply --input /tmp/loan-apply.json
```

复杂多行 JSON（displayData 行对象字段多）建议写入 UTF-8 JSON 文件后走 `--input <path>`。

## 写操作失败决策树

- `confirmation.required`（exit 10）→ 用户尚未明确确认：先向用户展示 prepare 预览，确认后带 `confirm:true` 重新 apply。
- `target_changed` / `continuation_expired` / `context_mismatch` → 目标或会话与 prepare 不一致：重新执行 prepare 后再 apply。
- `partial.write_uncertain` / `network.*`（请求已发出结果不确定）→ **立即停止，禁止自动重试**；用 `fna.loan.main.list` 回查该借款人是否收到提醒，向用户说明并让其决定是否重新发起。
- `business_error`（如「请选择提醒还款记录!」）→ 停止并按 msg 提示修正入参。

## 注意

- remindRepay 只发送提醒，不改变借款/还款金额；「确认已还 confirmRepay」等按钮能力未实现（见 schema `withheldOperations`），不得编造接口。
- prepare/apply 之间不得切换租户或账号；行集合必须与 prepare 快照一致。
