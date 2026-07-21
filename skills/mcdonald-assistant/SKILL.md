---
name: mcdonald-assistant
display_name: "麦当劳点餐助手"
display_name_en: "McDonalds China Ordering Assistant"
description: 麦当劳中国点餐与优惠助手。用户提到麦当劳、麦麦、麦当劳外卖、点餐、查菜单、领麦当劳优惠券、查麦当劳积分/订单/活动时使用。依赖 WorkBuddy 已配置并信任的麦当劳 MCP Server（streamable HTTP：https://mcp.mcd.cn）和用户自己的 MCP Token；本 skill 不包含脚本，也不保存凭据。
description_zh: "支持麦当劳点餐下单、菜单与门店查询、优惠券领取和比价、订单状态跟踪，并可提供营养成分/热量搭配建议、活动咨询、积分查询与兑换。"
description_en: "McDonalds China Ordering Assistant for menu browsing, coupon management, order placement, nutrition info, and loyalty points redemption via MCP Server."
version: 1.0.0
author: xinocwang
visibility: "public"
---

# mcdonald-assistant

麦当劳中国点餐与优惠助手，用于通过已配置的麦当劳 MCP Server 协助用户查询配送地址、浏览菜单、查询/领取优惠券、计算价格、创建外送订单、查询订单、查询积分和活动日历。

## When to use

当用户提出以下需求时使用：

- “帮我点个麦当劳/麦麦外卖”
- “查一下附近麦当劳菜单/有什么活动/有什么优惠券”
- “帮我领麦当劳优惠券”
- “查我的麦当劳积分/订单状态/配送进度”
- “帮我对比用券和不用券哪个划算”
- “最近有什么活动/麦当劳活动日历/今天有什么促销”
- “这个套餐多少大卡/帮我搭配 500 大卡以内/查营养成分”

## Preconditions

1. WorkBuddy 需要已配置麦当劳 MCP Server：
   - Server URL: `https://mcp.mcd.cn`
   - Transport/type: `streamablehttp`
   - Header: `Authorization: Bearer <用户自己的 MCP Token>`
2. MCP Token 需由用户自行在麦当劳 MCP 平台获取：优先提供官方文档入口 `https://open.mcd.cn/mcp/doc`；如用户需要平台入口，也可提示 `https://mcp.mcd.cn`。当用户要求初始化但没有提供 Token 时，必须先给出获取入口，并提示用户获取后再继续配置。
3. 配置 MCP 后不会自动生效，必须提醒用户打开 WorkBuddy 连接器管理页的“自定义连接器”，找到 `mcd-order` 并点击“信任”，然后刷新或重启当前会话。
4. 如果当前会话没有出现麦当劳相关 MCP 工具，先提示用户检查 MCP 配置、连接器信任状态，并重启/刷新 WorkBuddy。
5. 不要在对话中展示、记录、复述用户 Token。

## Initialization config

当用户要求“初始化配置”时，先检查是否已提供 MCP Token。若未提供，先输出 Token 获取入口 `https://open.mcd.cn/mcp/doc`，说明需要用户自行获取并提供，不要猜测或生成 Token。若用户提供了 Token，读取并合并 `~/.workbuddy/mcp.json`，不要覆盖已有 `mcpServers`。推荐新增配置如下（用用户 Token 替换占位符，不要在回复中复述 Token）：

```json
{
  "mcpServers": {
    "mcd-order": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer <MCP_TOKEN>"
      },
      "disabled": false
    }
  }
}
```

配置后验证 JSON 可解析、`mcd-order` 存在、`type` 为 `streamablehttp`、`url` 为 `https://mcp.mcd.cn`、认证头存在且未在输出中泄露。配置完成后必须明确给出后续启用步骤：

1. 打开 WorkBuddy 连接器管理页。
2. 进入“自定义连接器”。
3. 找到 `mcd-order`。
4. 点击“信任”。
5. 刷新或重启当前 WorkBuddy 会话。

如果用户已经点击信任但工具仍不可见，提示用户刷新/重启会话后再测试“查麦当劳优惠券”或“查我的麦当劳积分”。

## Workflow

1. 明确用户意图：点餐、查菜单、查优惠券、领券、查订单、查积分、查活动。
2. 点餐前先查询或确认配送地址；如果需要新增地址，必须让用户明确确认地址信息后再执行。
3. 查询门店菜单，向用户展示候选餐品、规格和价格。价格接口返回单位可能是“分”，展示给用户前换算为“元”。
4. 查询可用优惠券；如用户同意，可领取优惠券并重新计算价格。
5. 给出清晰的价格对比：不用券、用券、积分/活动等方案。不要替用户默认选择高风险或高金额方案。
6. 创建订单前必须二次确认：收货地址/门店、餐品、数量、优惠券、应付金额、取餐方式、是否预约、预约时间/预计送达时间（如有），并说明创建后通常需要在约 15 分钟内完成支付。
7. 创建订单后如果返回 `payH5Url`，必须立即帮用户打开支付页面，同时在回复中保留支付链接，方便用户手动打开。
8. 创建订单后必须醒目展示支付截止时间 `expirePayTime`（如接口返回），并写清楚“请在该时间前完成支付，超时订单可能自动失效”。如果接口未返回 `expirePayTime`，按经验提示“通常约 15 分钟内需支付，以页面展示为准”。不要代替用户完成支付。
9. 查询订单时，如果用户提供订单号，直接查询状态；不要泄露其他订单或个人信息。

## Capability workflows

### 优惠券

- 查询“有什么券/今天有什么优惠/可以领什么券”时，先调用 `available-coupons` 展示当前可领取优惠券，再询问是否一键领取。
- 用户明确说“帮我领券/一键领券/全部领取”时，调用 `auto-bind-coupons`，并展示总数、成功数、失败数、失败原因（如有）。
- 查询“我的券/已领券/卡包”时，调用 `query-my-coupons`，展示券名、用券价格或优惠、有效期、当前是否可用、到店/外送标签；不要承诺一定适用于当前订单。
- 下单前查询当前门店可用券时，调用 `query-store-coupons`，按券 ID 分组展示券名、有效期、适用商品和商品编码。

### 活动日历

- 查询“最近有什么活动/这个月有什么活动/麦当劳活动/促销活动”时，调用 `campaign-calendar`。
- 输出时区分进行中、即将开始、已结束活动；展示活动名称、日期/时间、参与状态或订阅状态（如接口返回）。
- 涉及时效判断时，可先调用 `now-time-info` 获取 MCP 服务器当前时间；不要自行猜测活动是否仍有效。

### 营养与热量搭配

- 查询“热量/卡路里/营养成分/蛋白质/脂肪/碳水/钠/帮我搭配 X 大卡”时，调用 `list-nutrition-foods`。
- 输出营养表时优先展示：餐品名称、能量/热量、蛋白质、脂肪、碳水化合物、钠；如字段缺失，明确标注接口未返回。
- 帮用户按目标热量搭配时，先用营养数据筛选候选餐品，再结合门店菜单确认可售；给出“约 X 大卡”的估算并提醒以官方返回为准。

### 积分与兑换

- 查询“我的积分/积分余额/过期积分”时，调用 `query-my-account`。
- 查询“积分可以兑换什么/积分商城”时，调用 `mall-points-products`；查看详情时调用 `mall-product-detail`。
- 积分兑换下单必须先确认 SKU、数量、积分是否充足、虚拟/实物属性和配送地址（实物必填），再调用 `mall-create-order`；不得凭已有信息直接声称兑换成功。

### 错误处理

- 如果工具返回 Token expired、Unauthorized、认证失败、401/403 等信息，提示用户重新获取 MCP Token，并按初始化配置流程更新、信任连接器、刷新会话。
- 如果工具返回 Rate limited 或请求过于频繁，提示稍后重试，不要循环重试。
- 如果工具不可见，先检查是否完成 MCP 配置、自定义连接器信任、刷新/重启会话。
- 如果接口返回字段为空或与预期不一致，明确说明“接口未返回该信息”，不要补编原因或替用户做高风险决定。

## Output formats

- 优惠券：用表格/清单展示券名、优惠、有效期、适用场景、当前可用性。
- 活动：按“进行中/即将开始/已结束”分组展示活动名称、时间、参与方式或链接（如有）。
- 营养：用表格展示餐品、热量、蛋白质、脂肪、碳水、钠。
- 订单：展示门店、取餐/配送方式、商品明细、优惠、实付、订单状态、支付链接、支付截止时间。

## Safety rules

- 创建地址、领取优惠券、创建订单、积分兑换下单都属于外部账户操作，必须先获得用户明确确认。
- 不保存、不打印、不转发 MCP Token、手机号、地址、订单号等敏感信息。
- 如果工具返回异常、价格不一致或优惠券编码不匹配，停止下单并说明需要人工确认。
- 若用户要求替换套餐内饮品/小食，必须先用餐品详情确认可选项；如果详情只返回默认项或创建订单工具不支持传入选配项，需明确告知无法通过当前 MCP 直接替换，获得用户接受默认项或改选商品的确认后再下单。
- 当前 MCP 未暴露修改/取消订单工具；用户想改预约时间、门店、餐品或取餐方式时，先查询订单状态。若未支付，可提示用户不要支付、等待订单超时或在麦当劳 App 自行取消，再经二次确认创建新订单。
- 不承诺优惠一定可用；以 MCP Server 返回结果为准。
- 不处理未成年人、他人账户或未经授权账户的点餐/支付请求。

## Common tool intents

麦当劳 MCP Server 可能暴露以下能力，具体以当前连接器返回的工具为准：

- 查/新增配送地址
- 查询门店菜单和餐品详情
  - 到店自取先用 `query-nearby-stores`。若 `searchType=1` 收藏餐厅为空，应请用户提供城市+门店名/地标，并改用 `searchType=2` 搜索。
  - `beType=1` 到店自取返回门店通常没有 `beCode`，后续 `query-meals`、`query-store-coupons`、`calculate-price` 不传 `beCode`；`beType=5` 得来速才需要传返回的 `beCode`。
- 查询门店可用券、可领券、我的优惠券
  - `available-coupons`：查询当前可领取的麦麦省优惠券。
  - `auto-bind-coupons`：一键领取当前可用优惠券；用户明确说“领券/一键领券/帮我领券”后可使用。
  - `query-my-coupons`：查询用户卡包中已有优惠券，不校验当前门店/渠道是否可用。
  - `query-store-coupons`：查询指定门店和订单类型下可用优惠券。
- 计算价格
- 创建订单（到店/外送）
  - `create-order` 返回 `payH5Url` 时，立即打开该支付链接，并在回复里同步展示链接。
  - `create-order` 返回 `expirePayTime` 时，必须突出展示支付截止时间；麦当劳订单通常约 15 分钟内需支付。
- 查询订单状态
- 查询营养信息
  - `list-nutrition-foods`：查询常见餐品能量、蛋白质、脂肪、碳水、钠等，用于营养问答和按热量搭配。
- 查询账户积分、积分商品和积分兑换下单
  - `query-my-account`：查询积分账户、余额和过期积分。
  - `mall-points-products`：查询可兑换商品/餐品券。
  - `mall-product-detail`：查询积分商品 SKU 和详情。
  - `mall-create-order`：创建积分兑换订单，必须先确认 SKU 和数量。
- 查询活动日历
  - `campaign-calendar`：查询当月进行中、未来和历史活动。
  - `now-time-info`：在判断活动有效期、当前时段、预约时间时获取服务器当前时间。

## Pitfalls

- 官方文档页可能需要登录或只返回标题，无法通过普通网页抓取获取完整配置；此时以已知 MCP 参数和用户提供的 Token 配置，不要猜测其他字段。
- `~/.workbuddy/mcp.json` 可能已有其他连接器，必须合并新增 `mcd-order`，不要整体重置配置。
- 验证配置时只能输出脱敏结果，例如是否存在认证头，不能打印 `Authorization` 的值。
- 预约下单必须先确认门店 `reservation=true` 且 `reservationTimeOptions` 覆盖用户目标时间；不支持预约的门店不要强行传 `reservationDate` 创建订单。
- 创建订单后若未主动打开支付链接、未提示 15 分钟支付窗口或未展示 `expirePayTime`，视为流程缺陷，必须立即补充说明并打开支付页。
- 外部资料可能使用裸工具名、旧工具名或 curl 示例（如 `my-coupons`、`campaign-calender`）；在 WorkBuddy 中优先使用当前会话可见的 MCP 工具名（如 `query-my-coupons`、`campaign-calendar`），不要改用 curl 直连 MCP，避免泄露 Token 或绕过连接器信任机制。

## Verification

使用前确认：

1. 当前 WorkBuddy 已信任并启用麦当劳 MCP Server；若刚完成配置，用户已在自定义连接器中点击“信任”并刷新/重启会话。
2. 当前会话可见麦当劳相关 MCP 工具。
3. 用户已授权本次操作，且高风险动作前完成二次确认。
4. 订单金额用元展示，必要时标注“接口返回单位为分，已换算”。
5. 下单后已打开支付链接，并在回复中展示支付链接。
6. 下单后已突出展示支付截止时间；如接口未返回截止时间，已提示通常约 15 分钟支付有效期。
