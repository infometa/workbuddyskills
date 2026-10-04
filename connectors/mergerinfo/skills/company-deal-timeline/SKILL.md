---
name: company-deal-timeline
display_name: 企业交易动态
display_name_en: Company Deal Timeline
description: 查询指定企业近一年的并购相关事件与角色变化。当用户问「XX 公司最近有什么动向」「这家公司这一年发生了什么交易」时使用。依赖 MergerInfo 连接器提供的 MCP 工具。
description_zh: 查询指定企业近一年的并购事件，以及它在每笔交易中的角色。
description_en: Retrieve a company's M&A events over the past year and its role in each deal.
version: 0.2.0
author: MergerInfo
---

# 企业交易动态

工具：`get_company_timeline`。按时间倒序返回该企业相关的并购事件，并标注企业在每个事件中的角色。

## 前置条件

该工具由 MergerInfo 连接器提供。若当前会话不存在此工具，说明连接器尚未安装或未连接，请提示用户先在「专家·技能·连接器 → 连接器」中安装 MergerInfo，**不要凭模型知识编造企业交易历史**。

## 调用方式

传入企业名称即可，支持曾用名：

```
get_company_timeline({ "company_name": "NVIDIA", "months": 12 })
```

用户给的是简称或中文译名时，先确认完整英文名再查；查不到不要自行改写名称反复重试，请让用户确认企业全称。

参数：`months` 默认 12；`limit` 返回事件数上限；`offset` 分页游标，仅付费等级可用（`data.next_offset` 为 `null` 时不要再翻页）。

## 角色

每条事件的 `company_role` 表示该企业在这笔交易中的身份：

| 值 | 含义 |
|---|---|
| `target` | 标的/被收购方 |
| `buyer` | 买方 |
| `seller` | 卖方 |
| `advisor` | 顾问 |
| `well_known_company` | 作为知名公司被提及 |

转述时带上角色，「作为标的被收购」和「作为买方收购别人」是完全不同的事。

## 回答时必须遵守

**匹配方式的局限要说清楚。** `coverage.match_method` 为 `company_name`，事件是按传入的公司名称匹配的，**不是企业主键关联**。因此可能误配同名企业，也可能遗漏改过名的企业。用户依赖结果做判断时，提示这一点。

**覆盖区间要如实说。** `coverage.window_from` / `window_to` 是实际覆盖的区间，可能明显短于用户请求的 12 个月（事件库有起始日期）。`notes` 会给出实际最早记录日期，请一并转述，例如「事件库最早记录到 2025-12，实际覆盖约 9 个月」。

**没有记录 ≠ 没有发生。** 空结果时只说「当前可见范围内未找到该企业的记录」。不要说「这家公司近一年没有任何交易」，也不要暗示隐藏了多少条记录。

**预览模式要标明。** `data.preview_only` 为 `true` 时，返回的是近期事件预览而非完整年度时间线，必须这样告诉用户，不能称之为「完整时间线」。同一家企业在配额窗口内返回的预览是固定的，改时间区间、换别名或换平台都不会刷新出更多记录。

**总结只能基于本次返回的事件。** 需要做年度综述时，只总结 `data.events` 里实际返回的内容并带上引用，不要基于模型知识补充这家公司的其他交易。

## 额度

每查询一家新企业会占用一个「企业槽位」。空结果不占用槽位，但仍计请求次数。`quota.timeline_companies` 显示剩余可查询的企业数。额度不足时转达 `next_actions` 的引导链接。

## 示例

用户：NVIDIA 近一年有什么动向？
调用：`get_company_timeline({ "company_name": "NVIDIA" })`
回答：按时间列出事件、日期与角色，说明实际覆盖区间，若 `preview_only` 为 true 则标明这是近期事件预览。
