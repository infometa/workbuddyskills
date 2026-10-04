---
name: uupt-skill
description: >-
  UU跑腿同城配送服务。支持帮我送、帮我取、帮我买、帮我办等多种服务，覆盖订单询价、发单下单、查询订单、取消订单、跑男实时追踪、领取优惠券。当用户要真实发起同城配送、代办交易或领取优惠券时使用：「同城配送」「同城急送」「同城快送」「同城跑腿」「跑腿」「发单」「帮送/帮取/帮买」「代购」「代取号」「代排队」「陪诊」「取寄快递」「送文件」「送钥匙」「送花」「送蛋糕」「取东西」「取快递」「取文件」「去XX取」「帮我买」「买奶茶」「买咖啡」「买药」「买饭」「买烟」「搬东西」「装卸」「小时工」「打扫卫生」「布置场地」「琐事代办」「领优惠券」「领券」「领取优惠券」「有优惠券吗」「有什么优惠」「有什么活动」「参加活动」等。通过 MCP 连接器工具调用。
version: "1.0.1"
author: "UU跑腿开放平台"
---

# UU跑腿 Skill（MCP 版）

本 Skill 通过 MCP 连接器提供的工具，调用 UU跑腿 同城跑腿配送（帮送 / 帮取 / 帮买）和帮帮服务（陪诊、搬抬、代办等）。WorkBuddy 连接本 Connector 时会自动走 OAuth 浏览器授权；之后所有业务操作都调用 MCP 工具，不要使用 CLI 或直连 HTTP API。

## 调用方式

连接器提供 6 个 MCP 工具：`uupt_order_price`、`uupt_create_order`、`uupt_order_detail`、`uupt_cancel_order`、`uupt_driver_track`、`uupt_receive_coupon_packages`。

不要猜测参数。地址、电话、订单号必须来自用户或上一步工具的返回值。价格字段单位是分，展示给用户时除以 100 转为元。

## 场景判断

先判断用户要的是跑腿配送还是帮帮服务：

| 用户表达 | 类型 | 判断依据 |
|---------|------|---------|
| 从 A 送到 B、寄文件、取快递再送到家、帮买后送达 | 跑腿配送 `send` | 物品在两个地点之间传递 |
| 陪诊、搬抬、代排队、现场保洁、只去驿站代取不另送 | 帮帮服务 `help` | 在同一地点提供现场协助 |

- 配送：必须有不同的起点和终点
- 帮帮：询价时 fromAddress 与 toAddress 填同一地点；服务细节（事项、时长、人数、特殊要求）先在对话中与用户确认清楚

## 工具说明

### 1. 询价 `uupt_order_price`

```json
{ "fromAddress": "郑州市金水区花园路1号", "toAddress": "郑州市二七区大学路100号", "cityName": "郑州市" }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| fromAddress | string | 是 | 起点；帮帮时填写服务地点 |
| toAddress | string | 是 | 终点；帮帮与起点相同 |
| cityName | string | 是 | 城市名，必须是完整行政区划名并以「市」结尾，如「郑州市」；用户未明确城市时从地址识别或沿用会话中最近确认的城市 |

**返回**：`body.priceToken`、`body.needPayMoney` / `body.totalMoney`（分）、`body.distance`（米）、`body.feeDetailList`（费用明细）。

**priceToken 有效期 20 分钟**（`body.expiresIn`，单位秒），拿到后尽快下单，过期需重新询价。

回复用户时展示元，并确认下单所需的电话（帮帮再确认具体事项）。

### 2. 下单 `uupt_create_order`

用户明确要发单时：先询价拿 `priceToken`，再立即创建订单，不要二次确认。

```json
{ "priceToken": "TOKEN_FROM_PRICE", "receiverPhone": "13800138000" }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| priceToken | string | 是 | 询价返回的 token |
| receiverPhone | string | 是 | 收件人 / 联系人手机号 |

> 注意：当前 MCP 版 create_order **不支持物品备注（note）**。帮买场景的商品规格、帮帮场景的服务细节、易碎品的「轻拿轻放」等要求，先在对话中与用户确认清楚并写入最终回复提醒，或提示用户在 UU跑腿 App 订单中补充、电话联系跑男。

**成功**：返回 `body.orderCode`，`body.orderUrl` 为空表示无需支付（余额已扣），直接告知用户订单创建成功。

**余额不足**：返回中 `body.orderUrl` 非空（支付链接，支持微信 / 支付宝）。必须把支付链接展示给用户并提示完成支付；用户确认已支付后，立刻调用 `uupt_order_detail` 查询订单状态；若用户未完成支付，终止流程，不要重复下单。

下单成功后，把订单编号、费用（元）一并告知用户；调用 `uupt_order_detail` 可补充取件码 / 确认码 / 预估时间。

### 3. 查询订单 `uupt_order_detail`

```json
{ "orderCode": "260911153210379000060411" }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| orderCode | string | 是 | 订单编号 |

返回：`body.orderCode`、`body.state`、`body.orderPrice`（分）、`body.fromAddress` / `body.toAddress`、`body.driverName` / `body.driverMobile`、`body.pickupCode`（取件码，跑男取件时核对）、`body.confirmCode`（确认码，收件人签收时核对）、`body.expectedArriveTime` / `body.userExpectedFinishTime`（预估取件 / 送达时间）。

订单状态：`1` 下单成功，`3` 已接单，`4` 已到达，`5` 已取件，`6` 送达中，`10` 已完成，`11` 已取消，`20` 异常。

取件码和确认码要在订单创建后主动告知用户。

### 4. 取消订单 `uupt_cancel_order`

```json
{ "orderCode": "UU123456789" }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| orderCode | string | 是 | 订单编号 |

取消前先用 `uupt_order_detail` 查看状态：跑男已接单后取消可能产生取消费（`cancelFee` 字段），先向用户说明再取消。

### 5. 跑男追踪 `uupt_driver_track`

```json
{ "orderCode": "UU123456789" }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| orderCode | string | 是 | 订单编号 |

返回跑男姓名 / 电话、经纬度、距离。向用户转述当前位置和联系方式，不要原样倾倒坐标。

### 6. 领取优惠券 `uupt_receive_coupon_packages`

```json
{ "source": 1 }
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| source | int | 否 | 领取来源（决定可领哪些券包），默认 1，一般无需传入 |

用户要领券或询问优惠（「领券」「领优惠券」「有优惠券吗」「有什么优惠」「有什么活动」「参加活动」）时直接执行，无需额外信息。

**返回字段**（JSON `body`）：

| 字段 | 说明 |
|------|------|
| `newlyClaimed` | 是否本次新领取：true-本次新领取；false-今天已领过（返回当日记录） |
| `couponList` | 领取的优惠券列表，每项含 `packageName`（券包名称，可为空）、`couponDetail`（优惠券信息）、`expireDate`（过期时间 yyyy-MM-dd） |
| `thursdayJoinAble` | 是否可参与淡定星期四活动。为 true 时按场景 D 展示，与 `displayContents` 无关 |
| `displayContents` | 发券结果和淡定星期四之间要展示的内容，**由接口控制**。数组按顺序包含文字和图片：`type=text` 时读 `text`（保留换行）；`type=image` 时读 `imageUrl` 和 `alt` |

**回复顺序**固定为三截，淡定星期四的话术和二维码保持原样。回复严格按话术模板输出，不得改动任何标点、空行、换行位置，不得输出触发条件或任何 JSON 字段名。

1. 发券结果：`couponList` 为空或 null → 场景 C；`newlyClaimed=false` 且列表非空 → 场景 B；其他且列表非空 → 场景 A。
2. 接口展示内容：`displayContents` 非空时，紧接在发券结果之后、场景 D 之前，按数组顺序原样渲染。没有该字段或为空数组时，这一截不输出。
3. 淡定星期四：`thursdayJoinAble=true` 时追加场景 D。

#### 场景 A：领券成功（`newlyClaimed=true` 且 `couponList` 非空）

```
🎉 一键领券完成！本次共领取 N 张优惠券

| 券名称 | 优惠券信息 | 过期时间 |
|--------|---------|--------|
| [packageName] | [couponDetail] | [expireDate] |
```

> N = couponList 条数；表格按 couponList 逐行输出；packageName 为空时填「优惠券」。
>
> 仅当响应**没有** `displayContents` 字段时，表格后再原样追加这一句：`可以在UU跑腿App优惠券列表查看所有券详情。`

#### 场景 B：当日已领过券（`newlyClaimed=false` 且 `couponList` 非空）

```
您今天已经领过UU跑腿的优惠券啦，这是今日领取的优惠详情：

| 券名称 | 优惠券信息 | 过期时间 |
|--------|---------|--------|
| [packageName] | [couponDetail] | [expireDate] |
```

> 仅当响应**没有** `displayContents` 字段时，表格后再原样追加这一句：`有新的优惠我第一时间通知你 🔔`

#### 场景 C：无可领券（`couponList` 为空或 null）

> 仅当响应**没有** `displayContents` 字段时，原样输出：

```
当前UU跑腿暂无优惠券，有新券上线我第一时间通知你 🔔
```

> 响应含 `displayContents` 时，场景 C 不输出上面这句，直接渲染展示内容。

#### 展示内容（`displayContents` 非空，放在发券结果和淡定星期四之间）

按数组顺序逐条渲染，条与条之间空一行。不得改写、不得摘要、不得调换顺序，不得输出 `type` / `text` / `imageUrl` 这些字段名。渲染完再进入场景 D，不要把星期四话术写进这段内容。

- `type=text`：把 `text` 原样输出，保留其中的空行和 emoji。
- `type=image`：用 `![alt](imageUrl)` 真实展示图片。`alt` 为空时用「图片」。图片无法展示时，输出图注文字和可点击的 `imageUrl`。
- `displayContents` 为空或没有该字段：不输出这一截，发券结果之后直接进入场景 D（若 `thursdayJoinAble=true`）。

#### 场景 D：淡定星期四活动（`thursdayJoinAble=true`，附加在发券结果和展示内容之后）

在上述内容之后追加以下话术，并用远程图片 `https://otherfiles.uupt.com/skills/thursday-qrcode.jpg` 以 `![淡定星期四活动](链接)` 形式真实展示，不能只输出 URL 文本。图片无法展示时，输出活动说明文字和可点击链接，引导用户微信自行打开。

```
另外你还可以参与「淡定星期四」活动，下单1元起！用微信扫描下方二维码即可参与 👇
```

## 认证说明

- 用户在 WorkBuddy 中点击连接后，WorkBuddy 的 OAuth 管理器自动完成动态客户端注册并打开浏览器授权页（OAuth 2.1 + PKCE），用户用 UU跑腿 账号完成登录授权
- 授权凭据由 WorkBuddy 加密保存在本机，后续请求自动携带 Bearer Token
- access_token 过期时 WorkBuddy 自动用 refresh_token 续期并重试原请求，对用户透明；refresh_token 也失效时，业务工具会返回 401 类错误，引导用户在连接器管理页重新授权
- 不要把 Token、完整 openId 展示给用户

## 注意事项

- 所有业务操作通过 MCP 工具执行，不要直接调用开放平台 HTTP API
- 地址越完整越准确，尽量精确到门牌号；未说清起止地址时先向用户追问
- 帮买：在对话中确认商品、规格、缺货如何处理；鲜花、蛋糕等易碎品提醒用户电话告知跑男或在 App 补充（MCP 暂不支持 note）
- 帮帮：服务地点、事项、时长或人数、特殊要求先确认清楚再询价下单
- 查询结果以工具返回的 JSON 为准，不要编造跑男位置或费用
- 领取优惠券需先完成授权；同一用户同一来源当天只能新领一次，重复领取返回当日记录（`newlyClaimed=false`）；回复顺序是发券结果、接口 `displayContents`、淡定星期四。`displayContents` 有内容时插在中间，文字原样输出，图片用 `imageUrl` 远程渲染。`thursdayJoinAble=true` 时场景 D 保持原样，用 `https://otherfiles.uupt.com/skills/thursday-qrcode.jpg` 真实展示活动二维码
- 下单是真实付费操作，下单后把订单编号、取件码、确认码、预估时间完整告知用户

## English summary

Use the uupt MCP tools for UU same-city delivery (`send`) and on-site help (`help`). Price first with `uupt_order_price` to get `priceToken` (valid 20 minutes), then create with `uupt_create_order`. Amounts are in cents — divide by 100 before displaying. If `orderUrl` is returned, show it as the payment link and confirm payment before proceeding. Run `uupt_receive_coupon_packages` when the user asks for coupons. Reply in this order: coupon result (A/B/C), then `displayContents` text and images verbatim when present, then the Thursday activity QR when `thursdayJoinAble` is true. Auth is OAuth 2.1 + PKCE handled by WorkBuddy on connect; tokens refresh transparently. The MCP version has no `note` parameter — confirm item/service details in conversation instead. Always share orderCode, pickupCode, and confirmCode after creating an order.
