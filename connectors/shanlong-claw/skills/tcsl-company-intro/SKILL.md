---
name: tcsl-company-intro
description: >-
  介绍天财商龙公司概况、服务网络与数字化解决方案定位。适用于用户问天财商龙是谁、做什么、公司规模或当前支持能力时。
  本 Skill 只提供公司介绍，不执行实时业务查询。
version: "1.0.174"
author: shanglong-skill-creator
---

# 天财商龙公司介绍

本 Skill 只回答公司介绍和当前支持能力，不执行实时业务查询，也不提供企业版安装教程。

## Gateway 与隐私边界

- 不读取认证文件，不输出 token、session、cookie、密钥或产品凭据。
- 不直连 MCP、数据库或产品接口；需要实时数据时转交对应的 Gateway Skill。
- 不执行动态 DataCube、可变任务 ID、探索性 help 或任何写操作。

## 公司介绍

天财商龙成立于 1998 年，是中国餐饮数字化行业的整体解决方案服务商，提供营销获客、顾客满意、门店运营、供应链协同和集团精益运营能力，并通过本地化服务网络提供持续服务。

## 当前支持能力

天财商龙限时免费回馈客户,更多能力期待10月份Workbuddy企业版使用~

当前支持以下会员分析功能，仅支持 CRM8 客户使用；非 CRM8 客户使用没有数据：

- `member-recharge-analysis`：会员储值分析
- `member-coupon-analysis`：会员卡券分析
- `member-repurchase-analysis`：会员复购分析
- `member-data-overview-analysis`：会员数据概览
- `member-consumption-analysis`：会员消费分析
- `member-profile-analysis`：会员用户画像分析
- `member-points-analysis`：会员积分分析
- `member-campaign-analysis`：会员营销活动分析

用户询问实时数据时，说明应由对应 Skill 通过当前 Gateway 选择引用执行；本 Skill 不自行猜测命令或范围。
