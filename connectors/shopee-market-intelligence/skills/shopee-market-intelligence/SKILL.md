---
name: 知虾-Shopee大数据分析
description: 通过已完成 OAuth2 授权的知虾 Shopee MCP 查询站点、类目、商品、店铺、品牌和热搜词数据。
---

# 知虾 Shopee 市场数据分析

通过 `shopee-market-intelligence` MCP Server 提供的只读工具完成 Shopee 市场数据查询与分析。

## 授权规则

- 首次连接由 WorkBuddy 根据 MCP 的 `401 Unauthorized`、Protected Resource Metadata 和 Authorization Server Metadata 自动启动 OAuth2.1 Authorization Code + PKCE 授权。
- 不要求用户手动填写 API Key、Access Token、authorization code、refresh token 或 PKCE verifier。
- 授权失败或 Token 失效时，引导用户回到 WorkBuddy 连接器管理页面重新连接；不得要求用户在对话中发送凭证。
- 不在回复、日志、工具参数或错误说明中打印、复述或传播任何 Token、授权码或其他凭据。

## 使用规则

1. 先确认站点。常用站点代码包括 `tw`、`my`、`id`、`th`、`ph`、`sg`、`vn`、`br`。
2. 类目分析先查询一级、二级、三级类目并取得真实 `categoryId` 与层级，不凭名称猜测 ID。
3. 商品、店铺、品牌和热搜词分析先通过列表或榜单获取服务返回的真实标识，再调用详情或趋势工具。
4. 数据通常按 T+1 更新；用户要求“最新”时，以工具实际返回的最新可用日期为准并在结果中注明。
5. 趋势查询使用满足问题所需的最短合理区间；列表先以较小分页验证条件，再按需扩大。
6. 只根据 MCP 返回数据总结；失败、无权限、无数据或字段含义不明时如实说明。
7. 本连接器默认只读，不声称能够修改 Shopee 店铺、商品、广告或其他业务数据。

## 输出要求

- 开头注明站点、数据日期或时间范围、类目层级及主要筛选条件。
- 排名和对比优先使用表格，并保留接口返回的币种和单位。
- 趋势结论至少给出起止值或变化幅度，不能从单点数据推导趋势。
- 将客观数据与分析建议分开；若结果分页，注明当前页和覆盖范围。
