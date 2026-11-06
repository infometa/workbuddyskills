---
name: fxy-financial
version: 1.0.0
description: 使用纷析云 MCP 查询账务、报表和凭证，生成凭证草稿，并在用户确认后保存；用户提到纷析云、账套、凭证、科目、余额表、明细账、报表、结账或财务查询时使用。
description_zh: 使用纷析云 MCP 查询账务、报表和凭证，生成并保存凭证。
description_en: Query FXY accounting data and draft or save vouchers through MCP.
author: 纷析云
---

# 纷析云连接器

连接采用 OAuth 授权：用户在 WorkBuddy 点击连接后浏览器登录纷析云并同意授权即可，无需填写 API 密钥。

## 账套

- 连接未指定账套，默认处于「全局工作区」，`getAccountContext` 会提示没有默认账套，这是正常现象。
- 先调用 `listAccountSets` 拿到用户名下的 `accountSetsId` 与名称，让用户明确要操作哪个账套；**禁止替用户默认选择或自行取第一项**（账套多时先展示再确认）。
- 账套确定后，所有账套级操作通过 `callApi` 的保留参数 `accountSetId` 指定，例如
  `callApi(name="Voucher_list", argumentsJson={"accountSetId":"735079029572375852","voucherDate":{"start":"2026-08-01","end":"2026-08-31"}})`
  （`accountSetId` 只作为账套头，不会传给业务接口）。

## 常用工具

- 账套列表：`listAccountSets`
- 当前账套：`getAccountContext`（需已指定账套）
- 科目：`listSubjects`
- 科目余额：`querySubjectBalance`
- 科目明细：`queryAccountDetail`
- 凭证列表：`queryVoucher`
- 凭证草稿：`draftVoucher`
- 保存凭证：`saveVoucher`
- 其他能力：先用 `searchApi` 一次搜索一个业务关键词，再用 `callApi` 调用精确返回的接口；不要猜接口名或参数。

`listSubjects`、`querySubjectBalance`、`queryAccountDetail`、`queryVoucher` 等核心工具只能在已确定的账套工作区内使用；全局工作区下请改用 `callApi` 带 `accountSetId`。

## 凭证流程

1. 先确定账套，并读取末级科目与必填辅助核算；缺业务信息时再询问用户。
2. 调用 `draftVoucher`。金额用字符串，ID 保持字符串；每条分录只填写借方或贷方一侧。
3. `valid=false` 时根据 `errors` 修正，禁止保存。
4. 向用户展示 `voucherPreview` 并取得明确保存意图后，才调用 `saveVoucher`。
5. `saveVoucher` 返回审批卡片后等待用户确认；不得声称尚未确认的凭证已保存。

## 安全规则

- 查询可直接执行。
- 任何创建、修改、删除、结账、反结账或其他写操作，都必须在调用写工具前展示影响并取得用户明确确认。
- `callApi` 的 WRITE 接口同样遵守确认规则；审批卡片不能替代调用前的业务确认。
- 不输出、不转存授权凭证；授权失效时引导用户在 WorkBuddy 中重新连接。
- 工具返回权限不足、账期关闭或参数错误时，原样说明原因并停止，不绕过校验。
