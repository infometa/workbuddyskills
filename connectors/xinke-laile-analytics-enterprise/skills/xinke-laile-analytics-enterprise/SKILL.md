---
name: xinke-laile-analytics-enterprise
display_name: 新客来了数据分析企业版
display_name_en: Xinke Laile Analytics Enterprise
description: Analyze tenant-scoped lead trends, source performance, and push delivery through the Xinke Laile MCP service.
description_zh: 通过新客来了 MCP 服务分析当前企业的线索趋势、渠道来源和推送效果。
description_en: Analyze tenant-scoped lead trends, source performance, and push delivery through the Xinke Laile MCP service.
version: 1.0.0
author: 星跃智能科技有限公司
---

# 新客来了数据分析企业版

使用本 Skill 回答与当前企业线索数据、来源表现和推送效果相关的问题。所有数据必须来自已连接的新客来了 MCP 工具。

## 工具选择

- 当指标含义、可用维度或统计口径不明确时，先调用 `list_metrics`。
- 查询每日新增数量或一段时间内的变化趋势时，调用 `analyze_lead_trend`。
- 比较不同平台的线索数量、占比或来源表现时，调用 `analyze_source_performance`。
- 查询推送成功数、失败数或成功率时，调用 `analyze_push_delivery`。

## 调用规则

1. 从用户问题中提取日期范围；用户未说明时，先询问或使用明确说明的合理默认范围。
2. 单次查询范围不得超过 90 天；超过时请用户缩短范围或拆分查询。
3. 不向工具传递 `tenant_id`、SQL、数据库表名、手机号、Token、密码或其他秘密信息。
4. 不要求用户在对话中粘贴 Token；凭证只通过 WorkBuddy 连接器配置页填写。
5. 回答时明确说明查询日期范围、指标口径和必要的分组维度。
6. 只解释工具实际返回的数据，不臆造成本、ROI、线索质量、转化率或其他未返回指标。
7. 需要比较多个时间段时，分别调用工具并标明每个时间段，避免混用口径。

## 异常处理

- 认证失败或 Token 无效：提示用户重新连接，并在新客来了“数据报表 → MCP 数据连接”中创建或检查 Token。
- 会员已过期：说明 MCP 仅在会员有效期内可用，提示用户先续费或联系管理员。
- 权限或工具范围不足：说明当前连接没有相应查询权限，提示用户检查套餐和连接权限。
- 参数错误或日期超过限制：修正参数或请用户缩小范围。
- 对同一认证、会员或权限错误不要反复重试。

## 输出要求

优先给出结论，再列关键数据和变化。数据不足时明确指出限制，不将缺失值推断为零。不得展示或推断其他租户的数据。
