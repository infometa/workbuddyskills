# linkfox-onboarding 接口契约

本 skill 调用 5 个网关端点（JWT 解码在本地，无需后端）。所有端点均挂在 `LINKFOX_AGENT_API_URL`（生产 `https://tool-gateway.linkfox.com`，测试 `https://test-sz-tool-gateway.linkfox.com`）下。

## 通用约定

| 项 | 值 |
|----|-----|
| 鉴权 | Header `Authorization: <LINKFOX_AGENT_API_KEY>`。key 从环境变量读：`LINKFOX_AGENT_API_KEY` 优先，回退 `LINKFOXAGENT_API_KEY`（无下划线，老客户常用） |
| Content-Type | `application/json;charset=UTF-8` |
| 响应信封 | `{"errcode": 200, "errmsg": "ok", ...}`，`errcode != 200` 表示业务错误。**部分接口字段直接在顶层，无 data 信封** |
| 重试 | 408/429/5xx 自动重试 3 次，指数退避 1s→2s→4s |

## 错误码约定

| errcode | 含义 | 本 skill 处理 |
|---------|------|--------------|
| 200 | 成功 | 正常返回 |
| 401 | 鉴权失败 | 提示检查 `LINKFOX_AGENT_API_KEY`，引导走入口 1（缺 Key 引导） |
| **402** | **积分余额不足** | **触发入口 2 充值流程**（实测返回 `{"errcode": 402, "errmsg": "积分余额不足，请充值"}`） |
| 403 | 无权限 | 抛错并提示，不归入计费不足 |
| 404 | 接口未实现 | 抛错并提示路径错误 |
| 408/429/5xx | 临时错误 | 重试 3 次，指数退避 |
| 其它 | 业务错误 | 抛错，stderr 输出完整 errcode/errmsg |

---

## 接口 0：JWT base64 解码（本地）

**用途**：从 `LINKFOX_AGENT_API_KEY` 的 JWT payload 解出 uid，作为下单接口的 `memberId`。

**实现**：
```python
import base64, json
parts = key.split(".")
payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
# payload = {"sid","uid","name","type","role","refresh","extend","exp"}
```

**返回字段示例**：
```json
{
  "sid": "NzmcGdC*************JrVpE",
  "uid": "PzwC**********uyL8M_cWZyM***ca94A",
  "name": "用户1234",
  "type": "API",
  "role": "",
  "refresh": false,
  "exp": 4926132474
}
```

---

## 接口 1：GET `/account/currentByAPI`

**用途**：拿当前用户信息，关键字段 `isTeamUser`（决定查个人还是团队套餐）与 `currentGroupId`（下单接口的 `groupId`）。

**请求**：

| 项 | 值 |
|----|-----|
| Method | GET |
| Path | `/account/currentByAPI` |
| Header | `Authorization: <key>` |
| Body | 无 |

**响应**（字段直接在顶层，**无 data 信封**）：

```json
{
  "errcode": 200,
  "nickName": "用户1234",
  "errmsg": "ok",
  "phoneNum": "188****1234",
  "avatar": "https://cdn.linkfox.com/...",
  "userId": "2008*******328",
  "hasAddedWechat": false,
  "bindWechat": false,
  "isTeamUser": true,
  "verifyStatus": true,
  "activationStatusInt": 1,
  "bx": false,
  "ax": true,
  "currentGroupId": "4h2gg********M6Qu66",
  "id": "cWZy******a94A"
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `isTeamUser` | bool | **核心字段**：true 团队 / false 个人 |
| `nickName` | string | 用户昵称，展示用 |
| `phoneNum` | string | 脱敏手机号 |
| `currentGroupId` | string | 用户当前 groupId，下单接口需要 |
| `userId` | string | 用户数字 ID |
| `id` | string | 用户字符串 ID（对应 JWT uid 最后一段） |

---

## 接口 2：POST `/package/getByTypeByAPI`

**用途**：按用户类型查套餐清单。`packageType` 取值：1 个人 / 5 个人积分加购 / 7 团队 / 8 团队积分加购。本 skill 用 1（个人）或 7（团队）。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/package/getByTypeByAPI` |
| Header | `Authorization: <key>`、`Content-Type: application/json;charset=UTF-8` |
| Body | `{"packageType": 1 或 7}` |

**响应**（`packageList` 直接在顶层，**无 data 信封**）：

```json
{
  "errcode": 200,
  "total": 9,
  "errmsg": "ok",
  "packageList": [/* 套餐对象数组 */]
}
```

**套餐对象字段**：

| 接口字段 | spec 字段 | 类型 | 说明 |
|---------|----------|------|------|
| `packageId` | `plan_id` | string | 唯一标识，如 `pkg_basic`、`pkg_team_basic` |
| `packageName` | `name` | string | 展示名，如 `基础版`、`团队版` |
| `packagePrice` | `price` | number | 价格（CNY），如 299.0 |
| `packagePriceString` | `price_string` | string | 已格式化价格 `¥299.00` |
| `originalPrice` | `original_price` | number | 原价（划线价） |
| `originalPriceString` | `original_price_string` | string | 已格式化原价 |
| `creditAmount` | `credits` | number | 充值后积分数 |
| `validityPeriod` | `validity_period` | string | 有效期数值，如 `"1"`、`"3"`、`"12"` |
| `validityPeriodType` | `validity_period_type` | string | 有效期单位，如 `MONTH`、`YEAR`、`DAY` |
| `description` | `description` | string | 套餐描述 |
| `extJson` | — | string (JSON) | 嵌套 JSON 字符串，含 `isRecommend`/`features`/`logo` 等 |
| `extJson.isRecommend` | `is_recommend` | bool | 是否推荐套餐 |
| `extJson.features` | `features` | array | 权益列表（前端展示用） |
| `extJson.logo` | `logo_url` | string | 套餐图标 URL |
| `packageType` | — | number | 1/5/7/8 |
| `isActive` | — | bool | 是否启用 |
| `sortOrder` | — | number | 排序权重 |

**支付方式**：接口**不返回** `available_methods`，脚本写死 `["wechat", "alipay"]`（对应后端的 `WX_PAY`/`ALI_PAY`）。

**套餐过滤规则**：`packagePrice == 0` 的免费版（如 `pkg_free`）在充值场景过滤掉。

**实测套餐数据**（个人 type=1，9 个含免费版，过滤后 8 个）：

| plan_id | name | price | original_price | credits | validity |
|---------|------|-------|---------------|---------|----------|
| pkg_basic | 基础版 | 299 | 598 | 26250 | 1 MONTH |
| pkg_basic_3 | 基础版 | 897 | 1794 | 78750 | 3 MONTH |
| pkg_basic_6 | 基础版 | 1794 | 3588 | 157500 | 6 MONTH |
| pkg_basic_12 | 基础版 | 2870.40 | 7176 | 315000 | 12 MONTH |
| pkg_premium_1m | 高级版 | 699 | 1398 | 65000 | 1 MONTH |
| pkg_premium_3m | 高级版 | 2097 | 4194 | 195000 | 3 MONTH |
| pkg_premium_6m | 高级版 | 4194 | 8388 | 390000 | 6 MONTH |
| pkg_premium_12m | 高级版 | 6710.40 | 16776 | 780000 | 12 MONTH |

**实测套餐数据**（团队 type=7，3 个，无免费版）：

| plan_id | name | price | original_price | credits | validity |
|---------|------|-------|---------------|---------|----------|
| pkg_team_basic | 团队版 | 4790.40 | 9580.80 | 530000 | 1 YEAR |
| pkg_team_medium | 团队版 | 8143.68 | 16287.36 | 1060000 | 1 YEAR |
| pkg_team_advance | 团队版 | 19161.60 | 38323.20 | 2650000 | 1 YEAR |

---

## 接口 3：POST `/order/createByAPI`（个人下单）

**用途**：个人用户创建订单并返回支付二维码。

**触发条件**：`/account/currentByAPI` 返回 `isTeamUser=false` 时使用此端点。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/order/createByAPI` |
| Header | `Authorization: <key>`、`Content-Type: application/json;charset=UTF-8` |
| Body | 见下 |

**请求 body**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `packageId` | string | ✓ | 来自接口 2 的 `packageId` |
| `payType` | string | ✓ | `WX_PAY` 微信 / `ALI_PAY` 支付宝 |
| `payDeviceType` | string | ✓ | 固定 `PC` |
| `memberId` | string | ✓ | 来自 JWT 解码的 `uid` |
| `groupId` | string | ✓ | 来自 `/account/currentByAPI` 的 `currentGroupId` |

**Body 示例**：
```json
{"packageId":"pkg_basic","payType":"ALI_PAY","payDeviceType":"PC","memberId":"cWZy*****94A","groupId":"JWBziY********oxerC"}
```

**响应**（字段直接在顶层，**无 data 信封**）：

```json
{
  "errcode": 200,
  "orderId": "Aq9ZWV*******FbebM",
  "payUrl": "weixin://wxpay/bizpayurl?pr=DCx****",
  "payQrcode": "weixin://wxpay/bizpayurl?pr=DCxG*****",
  "payType": "WX_PAY",
  "payPrice": "¥0.01",
  "originalPrice": "¥9,580.80",
  "discountPrice": "¥9,580.79",
  "state": "wait_pay",
  "timeLeft": 899,
  "expireDate": "2026-07-06 15:25:19",
  "tradeNo": "PH0020260706151*******21",
  "product": "团队版",
  "productId": "pkg_team_basic",
  "errmsg": "ok"
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `orderId` | string | 订单号，传给查询接口 |
| `payQrcode` | string | 二维码原始内容（扫码协议，微信 `weixin://`，支付宝 `https://mclient.alipay.com/...`）。脚本用它本地生成 PNG |
| `payUrl` | string | 通常与 `payQrcode` 相同 |
| `payPrice` | string | 实付价格（已格式化） |
| `state` | string | 订单状态，初始 `wait_pay` |
| `timeLeft` | number | 剩余支付秒数（约 899 秒 ≈ 15 分钟） |
| `expireDate` | string | 过期时间 |
| `tradeNo` | string | 交易号 |

**错误码**：
- `errcode=501, errmsg="团队用户请使用团队订单入口购买"`：用户类型不匹配，应改调 `/order/createTeamOrderByAPI`

---

## 接口 4：POST `/order/createTeamOrderByAPI`（团队下单）

**用途**：团队用户创建订单。

**触发条件**：`/account/currentByAPI` 返回 `isTeamUser=true` 时使用此端点。

**请求**：与接口 3 完全相同（method/path 不同，body 字段一致）。

**响应**：与接口 3 结构一致。

---

## 接口 5：POST `/order/getByAPI`（订单查询）

**用途**：查询订单支付状态。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/order/getByAPI` |
| Header | `Authorization: <key>`、`Content-Type: application/json;charset=UTF-8` |
| Body | `{"orderId": "..."}` |

**响应**（字段直接在顶层，与下单响应基本一致）：

```json
{
  "errcode": 200,
  "orderId": "Aq9ZWVYpwT****FbebM",
  "state": "wait_pay",
  "payDate": "",
  "timeLeft": 870,
  "payPrice": "¥0.01",
  "tradeNo": "PH0020260706151*****021",
  "errmsg": "ok"
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `state` | string | 订单状态枚举，见下 |
| `payDate` | string | 支付时间（支付成功后非空） |
| `timeLeft` | number | 剩余秒数（递减） |

**state 枚举**（实测 + 推测）：

| 值 | 含义 |
|----|------|
| `wait_pay` | 待支付（已实测） |
| `paid` | 已支付（待实测） |
| `expire` / `expired` | 已过期 |
| `cancel` / `cancelled` | 已取消 |

脚本将 `state` 映射到 spec 的 `status`：`wait_pay`→`unpaid`、`paid`→`paid`、`expire*`→`expired`、`cancel*`→`cancelled`、其它→`unknown`。

---

## 接口 6：POST `/user/v1/web/login`（发送验证码）

**用途**：发送注册/登录短信验证码。域名 `https://api.linkfox.com`（env `LINKFOX_LOGIN_API_URL` 可覆盖）。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/user/v1/web/login` |
| Header | `source: ai-linkfox-web`、`Content-Type: application/json;charset=UTF-8`、`uid: eyJhX2lkIjoiNmEyMmM4YjA1YmM5MTZhIiwiZF9pZCI6IiJ9`（固定常量，env `LINKFOX_LOGIN_FIXED_UID` 可覆盖） |
| Body | `{"type":"sms","method":"getVerifyCode","data":{"authPhone":"<phone>","areaCode":"+86"}}` |

**响应**：
```json
{"requestId":"...","code":"OK","message":"成功","data":{},"success":true}
```

**错误**：`code != "OK"` 时 `message` 含错误原因（手机号格式、频率限制等）。

---

## 接口 7：POST `/user/v3/web/login`（验证码登录，首次登录即注册）

**用途**：用验证码登录，首次登录自动注册。域名同接口 6。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/user/v3/web/login` |
| Header | 同接口 6，**uid 必需**（不传返回 `00500 服务器繁忙`） |
| Body | `{"type":"sms","method":"login","systemId":"LinkFoxAgent","data":{"areaCode":"+86","authPhone":"<phone>","authCode":"<code>","sourceChannel":"skill"}}` |

**响应**：
```json
{
  "code": "OK",
  "message": "成功",
  "data": {
    "userId": "2074679****403968",
    "userName": "用户1234",
    "phoneNum": "188****1234",
    "accessToken": "eyJhIjoi...JWT...",
    "expireAt": 1784082485513,
    "refreshToken": "...",
    "newUser": false,
    "isFirstRegister": null
  },
  "success": true
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.accessToken` | string | JWT，后续接口的 `authorization` header。JWT header 含 `a`（a_id）和 `u`（userId） |
| `data.refreshToken` | string | 刷新 token，loginByToken 接口需要 |
| `data.userId` | string | 用户数字 ID，后续 uid header 的 `d_id` |
| `data.newUser` | bool | 是否首次注册 |
| `data.isFirstRegister` | bool/null | 同上 |

**错误**：
- `code=00400, message="验证码错误或已过期"`：验证码错或过期，重新发短信
- 这是登录即注册的接口，**不会返回"用户已存在"**

---

## 接口 7.5：POST `/account/loginByToken`（新用户触发送积分）

**用途**：仅新用户（`newUser=true`）调用，触发新用户赠送积分发放。老用户调了无副作用但也无收益，故跳过。域名 `https://agent-api.linkfox.com`（同接口 9）。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/account/loginByToken` |
| Header | `authorization: <accessToken>`、`source: agent-linkfox-web`、`Content-Type: application/json`、`Origin: https://agent.linkfox.com`、`Referer: https://agent.linkfox.com/` |
| Body | `{"token":"<accessToken>","refreshToken":"<refreshToken>","device":{"aid":"3026344186","did":"","type":"Windows","os":"10","model":"149.0.0.0","brand":"Chrome"}}` |

**body 字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `token` | string | ✓ | 登录响应的 `accessToken` |
| `refreshToken` | string | ✓ | 登录响应的 `refreshToken` |
| `device` | object | ✓ | 设备信息，`aid` 实测可用固定值 `3026344186`（后端不校验唯一性） |
| `device.aid` | string | ✓ | 设备指纹，固定值即可 |
| `device.type` | string | ✓ | `Windows` |
| `device.os` | string | ✓ | `10` |
| `device.model` | string | ✓ | `149.0.0.0` |
| `device.brand` | string | ✓ | `Chrome` |

**响应**：
```json
{"errcode":200,"errmsg":"ok"}
```

**错误**：
- `errcode=400, errmsg="device 为必填参数"`：缺 device 字段
- 其它非 200 错误透传给 Claude 提示

---

## 接口 8：POST `/linkFoxApp/api/userCenter/userInfo`（拿团队信息）

**用途**：拿用户的 agent 团队信息，从 teamList[0] 取 `agentTeamId`（groupId）和 `agentMemberId`（memberId）。域名 `https://api.linkfox.com`（同登录）。

**请求**：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/linkFoxApp/api/userCenter/userInfo` |
| Header | `authorization: <accessToken>`、`source: agent-linkfox-web`、`Content-Type: application/json`、`uid: <base64({"a_id":"<token JWT header.a>","d_id":"<userId>"})>`、`Origin: https://agent.linkfox.com`、`Referer: https://agent.linkfox.com/` |
| Body | `{}` |

**uid header 构造规则**（实测）：
1. 解 accessToken JWT 第一段（header），取 `a` 字段值
2. 取登录响应的 `userId`
3. 拼 `{"a_id":"<a>","d_id":"<userId>"}`，紧凑 JSON（无空格）
4. base64 编码（标准 base64，含 `==` 填充）

示例：accessToken 的 JWT header `{"a":"6a22c8b0***16a","u":"2074679****56403968","alg":"HS256"}` + userId `207467****6403968` → uid = `base64({"a_id":"6a22c*****c916a","d_id":"20746794*****403968"})` = `eyJhX2lkIjoiNmEyMmM4YjA1YmM5MTZhIiwiZF9pZCI6********NDU2NTY0MDM5NjgifQ==`

**响应**：
```json
{
  "code": "OK",
  "message": "成功",
  "data": {
    "id": "207467944*****968",
    "nickName": "用户1234",
    "phoneNum": "188****1234",
    "teamList": [
      {
        "teamId": "2074679445*****560",
        "teamName": "用户1234的个人空间",
        "aiTeamId": "2074679*****560",
        "agentTeamId": "207467944*****0560",
        "agentMemberId": "207467944*****4864",
        "role": "1",
        "teamType": 1,
        "ownerId": "207467944****03968"
      }
    ]
  },
  "timestamp": 1783477806480
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.teamList[0].agentTeamId` | string | **groupId**，传给接口 9 |
| `data.teamList[0].agentMemberId` | string | **memberId** |
| `data.teamList[0].teamName` | string | 团队名，展示用 |

**错误**：`code != "OK"` 时 `message` 含原因。若 `teamList` 为空 → 用户未开通任何团队空间，引导访问 https://agent.linkfox.com/ 开通。

---

## 接口 9：POST `/group/getApiToken` + `/group/generateApiToken`（查/生成 API key）

**用途**：先查已有 API token，无则生成。域名 `https://agent-api.linkfox.com`（env `LINKFOX_AGENT_USER_API_URL` 可覆盖）。

**请求**（两接口完全一致，仅 path 不同）：

| 项 | 值 |
|----|-----|
| Method | POST |
| Path | `/group/getApiToken` 或 `/group/generateApiToken` |
| Header | `authorization: <accessToken>`、`tid: <groupId>`、`source: agent-linkfox-web`、`Content-Type: application/json;charset=UTF-8`、`uid: <同接口 8 格式>`、`Origin: https://ai.linkfox.com`、`Referer: https://ai.linkfox.com/` |
| Body | `{"id":"<groupId>"}` |

**调用顺序**：先调 `getApiToken`，若返回 `token` 非空则用之；否则调 `generateApiToken` 生成。

**响应**（实测）：

getApiToken 查无时：
```json
{"errcode":200,"errmsg":"ok","key":"","token":"","createDate":""}
```

generateApiToken 生成成功（getApiToken 查到时也返回同样结构）：
```json
{
  "errcode": 200,
  "errmsg": "ok",
  "key": "goRJmQN6****4hi3UU",
  "token": "eyJhbGciOiJSUzI1NiIs...JWT...",
  "createDate": "2026-07-08 10:41:49"
}
```

**关键字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `token` | string | **API key 本体**（JWT），作为 `LINKFOX_AGENT_API_KEY` 配置。空字符串表示无 token |
| `key` | string | 短 id（非 API key，展示用） |
| `createDate` | string | 生成时间 |

**错误**：
- `errcode=501, errmsg="团队不存在"`：该用户在 agent 系统未开通团队 token。引导用户前往 https://agent.linkfox.com/ web 端手动生成 key，参考帮助文档第 2 章。

---

## 端到端调用顺序

**入口 1 脚本化注册流程**：

1. 调 `POST /user/v1/web/login`（method=getVerifyCode）发短信
2. 用户回复验证码后，调 `POST /user/v3/web/login`（method=login）拿 `accessToken` + `refreshToken` + `userId`
3. **仅新用户（newUser=true）**：调 `POST /account/loginByToken` 触发新用户送积分
4. 用 accessToken + userId 构造 uid header，调 `POST /linkFoxApp/api/userCenter/userInfo` 拿 `agentTeamId`（groupId）+ `agentMemberId`
5. 调 `POST /group/getApiToken`，有 token 则用；无则调 `POST /group/generateApiToken` 生成
6. 拿到 token 即为 `LINKFOX_AGENT_API_KEY`，按三平台示例配置环境变量

**入口 2 充值流程**：

1. 调 `GET /account/currentByAPI` 拿 `isTeamUser` + `currentGroupId`
2. 按 `isTeamUser` 选 `packageType`（1 个人 / 7 团队），调 `POST /package/getByTypeByAPI` 拿套餐清单
3. 用户选套餐 + 支付方式后，解码 JWT 拿 `memberId`（uid）
4. 按 `isTeamUser` 调对应下单接口（接口 3 或 4），body 含 `packageId`/`payType`/`payDeviceType=PC`/`memberId`/`groupId`
5. 拿响应里的 `payQrcode` 本地渲染 PNG + ASCII 二维码，展示给用户扫码
6. （可选）调 `POST /order/getByAPI` body `{"orderId": "..."}` 查询支付状态
