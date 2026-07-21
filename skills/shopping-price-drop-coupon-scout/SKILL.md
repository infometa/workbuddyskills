---
name: shopping-price-drop-coupon-scout
description: 监控用户指定商品的价格变动并汇总官方优惠券与促销信息，全程只读、不登录账号、不加购物车、不下单、不处理支付。当用户希望设置降价提醒、整理可用优惠券清单，或获取某商品/商家的促销汇总（price alert / deal summary / coupon）时使用。
version: 1.0.0
homepage: https://github.com/openclaw/skills/tree/main/skills/codedao12/shopping-price-drop-coupon-scout
source_type: clawhub
clawhub_slug: shopping-price-drop-coupon-scout
display_name: "价格优惠监控助手"
display_name_en: "Price Drop & Coupon Scout"
description_zh: "为用户指定的商品提供只读的价格监控与优惠券汇总：设置目标价与提醒频率，输出价格监控清单、可用优惠券/促销码和降价提醒文案。全程不登录账号、不加购物车、不下单、不处理支付。"
description_en: "Read-only price monitoring and coupon roundup for the products you specify: set a target price and alert cadence, get a watch list, available coupons/promo codes and ready-to-use price-drop alerts. Never logs in, adds to cart, checks out or handles payment."
visibility: "public"
---

# 价格优惠监控助手

## 目标
为用户指定的商品提供安全、只读的价格监控与优惠券汇总，输出监控清单、可用优惠信息和提醒文案。全程不登录账号、不加购物车、不下单、不处理支付。

## 适用场景
- 用户提供了商品 URL、SKU 或商品名称。
- 用户希望设定目标价并制定降价提醒方案。
- 用户希望整理官方优惠券链接或促销码。

## 不适用场景
- 要求自动下单或自动加入购物车。
- 唯一可用的数据来源是被明确禁止的自动抓取。
- 要求提供或代填支付信息、登录凭据。

## 快速导航
- `references/overview.md`：工作流程与质量标准。
- `references/auth.md`：数据访问与凭据处理原则。
- `references/endpoints.md`：可选的外部集成与调用边界。
- `references/webhooks.md`：可选的异步事件处理。
- `references/ux.md`：信息采集问题与输出模板。
- `references/troubleshooting.md`：常见问题处理。
- `references/safety.md`：安全与隐私边界。

## 所需输入
- 商品清单：URL、SKU 或商品名称。
- 目标价阈值与币种（默认 ¥ 人民币）。
- 优先关注的电商平台或地区（如淘宝、京东、天猫、拼多多等，不限定单一平台）。
- 提醒频率与时区（默认中国标准时间 UTC+8）。

## 预期输出
- 带目标价阈值的价格监控清单。
- 用户提供历史价格时，给出价格走势小结。
- 来自官方渠道的优惠券或促销信息汇总。
- 可直接使用的降价提醒文案草稿。

## 运行说明
- 优先使用电商平台官方促销页、官方 API，或用户自行导出/提供的数据。
- 不抓取禁止自动访问的网站，遵守各平台 robots 协议与服务条款。
- 所有输出仅作参考建议，不构成下单指令。

## 安全说明
- 不处理任何支付信息（卡号、密码、验证码等）。
- 不登录用户账号，不读取或存储 cookie。
- 优惠券与价格仅作信息呈现，不引导下单返利、不诱导外跳。

## 安全模式
- 仅做价格跟踪与信息汇总。
- 提供优惠券清单与提醒文案，不涉及任何购买动作。

## 敏感操作（超出范围）
- 购买、结算、修改购物车等操作均不在本 Skill 范围内。

## 免责声明
- 价格与优惠券均为参考信息，可能存在延迟或变动，最终以电商平台结算页实际显示为准。
