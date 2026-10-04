# 发票核销（财务/管理员）

## 何时使用

财务/管理员视角的发票核销：看金额分布 → 金额 tab 汇总；看明细/谁还有多少没核销 → 核销列表；对未到票的预付流程发催票 → **写操作**，先 prepare 再 apply。`writeOffList`/`callTicket` 需财务/管理员登录，`writeOffPageTab` 公开权限（仍需登录态定租户）。

| 用户意图 | operation | 风险 |
|---|---|---|
| 「发票核销还有多少没核销」「核销中/部分核销多少」 | `fna.invoice.writeoff.summary` | read |
| 「列出所有发票核销单」「谁还有多少没核销」 | `fna.invoice.writeoff.list` | read |
| 「催一下这几笔预付的票」「批量催票」 | `fna.invoice.writeoff.callticket.prepare` / `.apply` | **write** |

## 输入要点

- `fna.invoice.writeoff.list` 必填 `current`/`pageSize`；筛选 `invoiceStatus`：`unWritten`(未核销)/`unarrivedTicket`(未到票)/`dealing`(核销中)/`callTicket`(催票)。
- `menuCode`/`permissionSetCode` 示例 `inv_write_off_financial` / `inv_write_off_financial.default`，需与环境核对。
- 常用金额列（rows 内）：`totalAmount`(总金额)/`arrivedAmount`(已核销)/`verificationAmount`(核销中)/`notArrivedAmount`(未核销)，均为格式化字符串；`requestId` = `id`（催票回传用）。
- `total=0`、rows 为空 → 提示「暂无发票核销记录」。

## 数据流：催票（写操作）

1. `fna.invoice.writeoff.list`（可用 `invoiceStatus=unarrivedTicket` 或 `callTicket` 过滤）取目标预付流程行。
2. 提取行的 `requestId` 组装 `requestids` 数组（1~200 条，必须来自列表真实返回，禁止凭空构造）。
3. `fna.invoice.writeoff.callticket.prepare` 入参 `{"requestids":[...]}` → 返回预览（条数 + 前 20 个 ID）+ continuation：**向用户展示目标流程（建议连同列表行的申请名称/未核销金额一起展示），取得明确确认**。
4. 确认后 `fna.invoice.writeoff.callticket.apply` 入参 `requestids` + `confirm:true` + `continuation`。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.summary --input-json '{"invoiceStatus":"unWritten","menuCode":"inv_write_off_financial","permissionSetCode":"inv_write_off_financial.default"}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.list --input-json '{"current":1,"pageSize":20,"invoiceStatus":"unarrivedTicket"}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.callticket.prepare --input-json '{"requestids":["1305356190451253248","1304611911414513664"]}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.callticket.apply --input-json '{"requestids":["1305356190451253248","1304611911414513664"],"confirm":true,"continuation":"PASTE_TOKEN_FROM_PREPARE"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.summary --input-json '{"invoiceStatus":"unWritten","menuCode":"inv_write_off_financial","permissionSetCode":"inv_write_off_financial.default"}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.list --input-json '{"current":1,"pageSize":20,"invoiceStatus":"unarrivedTicket"}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.callticket.prepare --input-json '{"requestids":["1305356190451253248","1304611911414513664"]}'
weaver-work-cli --profile eteams --json fna run fna.invoice.writeoff.callticket.apply --input-json '{"requestids":["1305356190451253248","1304611911414513664"],"confirm":true,"continuation":"PASTE_TOKEN_FROM_PREPARE"}'
```

## 写操作失败决策树

- `confirmation.required` → 用户尚未确认：展示 prepare 预览后带 `confirm:true` 重新 apply。
- `target_changed` / `continuation_expired` / `context_mismatch` → 与 prepare 快照不一致或已过期：重新 prepare。
- `partial.write_uncertain` / `network.*` → **立即停止，禁止自动重试**；用 `fna.invoice.writeoff.list`（`invoiceStatus=callTicket`）回查是否已催票，向用户说明。
- `business_error` → 停止并按 msg 修正（如 requestids 含非法流程）。

## 注意

- callTicket 只发送催票通知，不改变核销金额状态；核销明细等按钮能力未实现（见 schema `withheldOperations`）。
- 翻页时保持 `invoiceStatus`/`menuCode`/`permissionSetCode` 等筛选条件。
