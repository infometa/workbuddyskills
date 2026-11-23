---
name: qiaocai-finance
display_name: 翘财
display_name_en: QiaoCai
description: 通过自然语言查询翘财 SaaS 的会计科目、凭证明细和余额报表，辅助记账核对、凭证审核与余额检查。
description_zh: 通过自然语言查询翘财 SaaS（总账 gls）的会计科目、凭证明细与科目/辅助核算余额表，辅助记账核对、凭证审核与余额检查。
description_en: Query account subjects, voucher details, and subject/auxiliary balances from QiaoCai SaaS via natural language.
version: 0.3.0
author: 微海咨询
category: 财务
---

# 翘财查询

指导 AI 正确使用「翘财」连接器的 MCP 工具，查询翘财 SaaS（总账 gls）的业务数据。

## 前置条件

- 首次连接时 WorkBuddy 会自动打开浏览器，用户登录翘财（选择企业）完成授权，访问令牌由系统自动签发与续期，用户无需手动填写；
- 所有查询结果均限定在用户授权时选择的企业范围内，无需向用户询问租户；
- 授权过期时服务返回 HTTP 401，客户端会自动用刷新令牌续期并重试，通常用户无感；若连续 401（如授权被撤销），提示用户「请在 WorkBuddy 连接器中断开并重新连接『翘财』，浏览器中重新登录授权即可」。

## 工具列表

WorkBuddy 中工具名会自动加服务器前缀，实际形如 `qiaocai-finance_queryAccountSubjects`。

**参数结构**：所有工具的参数都包在一层 `query` 对象下（服务端参数对象化的 schema 形态），调用形如 `queryAccountSubjects(query={keyword:"银行"})`，扁平传参会导致参数绑定失败。

### qiaocai-finance_queryAccountSubjects — 查询会计科目

| 参数（query 下） | 类型 | 必填 | 说明 |
|---|---|---|---|
| keyword | string | 否 | 科目编码或名称关键字，模糊匹配；为空返回全部（分页） |
| page | integer | 否 | 页码，从 1 开始，默认 1 |
| size | integer | 否 | 每页条数，默认 20，最大 200 |

返回科目列表：编码、名称、余额方向（借/贷）、层级、是否启用。适用于：记账辅助、科目核对、凭证生成前确认科目。

示例：「帮我查一下会计科目，关键字"银行"」→ `queryAccountSubjects(query={keyword:"银行"})`。

### qiaocai-finance_queryVoucherDetail — 查询凭证明细

| 参数（query 下） | 类型 | 必填 | 说明 |
|---|---|---|---|
| voucherId | integer | 二选一 | 凭证 ID |
| voucherNo | string | 二选一 | 凭证号（如 记-2026-09-0042）；用户给出凭证号时直接传凭证号，无需换算 |

返回凭证头（凭证号、日期、摘要、附单据数）与全部分录行（科目、借方金额、贷方金额、辅助核算项）。适用于：凭证审核、异常排查。未查询到凭证时服务会明确返回"未查询到"，请如实告知用户并确认凭证号与所属企业。

### qiaocai-finance_querySubjectBalance — 查询科目余额表

| 参数（query 下） | 类型 | 必填 | 说明 |
|---|---|---|---|
| year | integer | 否 | 会计年度，如 2026；不传默认当前年度 |
| startMonth | integer | 否 | 起始月份 1-12，默认 1 |
| endMonth | integer | 否 | 结束月份 1-12，默认 12 |
| keyword | string | 否 | 科目编码或名称关键字，为空=全部科目 |
| level | integer | 否 | 科目级次：1=仅一级科目汇总（默认），2=末级明细 |
| accountBookName | string | 否 | 账簿名称关键字，为空=默认账簿 |
| includeUnposted | boolean | 否 | 是否包含未记账凭证，默认否 |
| topN | integer | 否 | 返回条数上限，默认 50，最大 100（按期末余额绝对值降序） |

按年度与月份区间返回各科目的期初余额、本期借方发生额、本期贷方发生额、期末余额，默认一级科目汇总、按期末余额绝对值从大到小。适用于：余额核对、试算平衡、财务检查。用户说「某月科目余额」「今年以来各科目余额」时使用。

示例：「看看今年以来各科目的期末余额」→ `querySubjectBalance(query={year:2026})`。

### qiaocai-finance_queryAuxiliaryBalance — 查询辅助核算余额账

参数与科目余额表完全相同。按辅助核算维度（客户、供应商、部门、项目等）汇总余额，行内附带辅助核算维度信息。适用于：往来核对、专项跟踪。

## 通用规则

- 结果为空或未查询到时如实告知"未查询到数据"，不要编造；
- 金额一律保留原始精度与单位，不做换算；
- 服务端返回"无数据权限"提示时，如实转告用户该报表需要先在翘财系统中开通对应权限；
- 查询失败（超时/5xx）时建议用户稍后重试；连续失败时按前置条件中的授权失效流程处理。
