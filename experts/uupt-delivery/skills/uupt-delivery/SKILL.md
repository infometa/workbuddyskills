---
name: uupt-delivery
description: >-
  UU跑腿同城配送服务。支持跑腿配送和帮忙服务两种订单类型，包括订单询价、发单下单、查询订单、取消订单、跑男实时追踪。当用户表达任何与"送"、"取"、"寄"、"跑腿"、"发单"、"配送"、"帮忙"、"帮我"、"代取号"、"代排队"、"搬东西"等配送或帮忙需求时使用此skill。
version: 1.0.7
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - node
        - python3
    homepage: https://open.uupt.com
    install:
      - kind: node
        package: axios
        bins: []
      - kind: python
        package: requests
        bins: []
---

# UU跑腿同城配送服务 Skill

UU跑腿同城配送服务为用户提供便捷的同城即时配送能力和现场帮忙服务，包括订单询价、发单、订单管理和跑男实时追踪等功能。

## 功能特性

- 📱 手机号一键注册（首次使用自动引导）
- 💰 订单询价（计算配送/帮忙服务费用）
- 📦 创建跑腿配送订单（从A地到B地）
- 🤝 创建帮忙服务订单（在指定地点获得现场协助）
- 💳 在线支付（余额不足时提供支付链接，支持微信/支付宝）
- 📋 查询订单详情
- ❌ 取消订单
- 🏃 跑男实时位置追踪

## 运行环境

本 skill 同时提供 **Node.js** 和 **Python** 两种版本，Agent 自动检测可用环境。

| 环境 | 依赖安装 | 脚本入口 |
|------|---------|---------|
| Node.js | `npm install` | `scripts/*.js`、`index.js` |
| Python | `pip install -r requirements.txt` | `uupt_delivery.py` |

> **命令格式约定**：下文命令示例默认使用 Node.js 版本，Python 版本只需将脚本路径换为 `python uupt_delivery.py <command>`，参数名中的 `--camelCase` 换为 `--kebab-case`（如 `--fromAddress` → `--from-address`），参数含义完全相同，不再重复列出。

## 触发条件与场景判断

收到用户请求后，先判断场景。Agent 需智能识别**跑腿配送(SEND)** vs **帮忙服务(HELP)**：

| 用户表达 | 识别为 | 判断依据 |
|---------|--------|---------|
| "从A送到B"、"把X寄到Y"、"配送" | 跑腿配送(SEND) | 两个不同地点之间的物品传递 |
| "帮我在X地点..."、"帮我搬/扔/装..." | 帮忙服务(HELP) | 只有一个地点，跑男在现场提供协助 |
| "帮我买个X送到Y" | 跑腿配送(SEND) | 本质是A到B的配送，用了"帮"字 |
| "帮我在医院挂个号"、"帮我在餐厅取号" | 帮忙服务(HELP) | 在现场执行特定任务，不涉及物品配送 |

**判断原则**：核心是从A到B传递物品 → 配送；核心是在某地点提供现场协助 → 帮忙。

**六大场景**：

| 场景 | 触发条件 | 所需信息 |
|------|---------|---------|
| 场景零：首次注册 | 执行脚本输出 `[REGISTRATION_REQUIRED]` | 手机号 / 开发者凭证 |
| 场景一：订单询价 | 用户想知道费用 | 地址信息（配送需起止地址，帮忙只需地点） |
| 场景二：创建订单 | 用户确认发单 | priceToken、收件人电话、帮忙内容(note) |
| 场景三：查询订单 | 用户想看订单状态 | 订单编号 |
| 场景四：取消订单 | 用户要取消订单 | 订单编号 |
| 场景五：跑男追踪 | 用户想看跑男位置 | 订单编号 |

---

## 场景零：首次注册

当执行任何脚本输出 `[REGISTRATION_REQUIRED]` 时自动触发。

### Step 1: 询问凭证

```
首次使用需要配置认证信息，请问您是否已有 UU跑腿开放平台的凭证（appId、appSecret、openId）？
- A: 已有凭证，直接配置
- B: 没有凭证，通过手机号注册
```

### Step 1A: 开发者模式（A）

请用户提供 `appId`、`appSecret`、`openId`，写入 `config.json`：

```json
{ "appId": "...", "appSecret": "...", "openId": "..." }
```

保存后告知「配置完成！」，**立即继续执行用户最初要求的功能**。

### Step 2: 手机号注册（B）

询问手机号，发送短信验证码：

```bash
node scripts/register.js --mobile="用户手机号"
```

处理结果：
- `[SMS_SENT]` → 验证码已发送，进入 Step 3
- `[IMAGE_CAPTCHA_REQUIRED]` → 输出包含 `IMAGE_DATA=data:image/png;base64,...`，将 base64 图片展示给用户识别数字后重试：
  ```bash
  node scripts/register.js --mobile="手机号" --imageCode="用户输入的数字"
  ```

### Step 3: 输入验证码完成授权

```bash
node scripts/register.js --mobile="手机号" --smsCode="用户输入的验证码"
```

处理结果：
- `[REGISTRATION_SUCCESS]` → 注册成功，openId 已保存，**立即继续执行用户最初的功能**
- `[REGISTRATION_FAILED]` → 从 Step 2 重试（无需重新输入手机号），最多 3 次

---

## 场景一：订单询价

计算配送/帮忙服务费用，用户可只询价不发单。

### 执行步骤

1. 判断订单类型（配送 vs 帮忙）
2. 获取地址：配送需起止地址，帮忙只需地点
3. 执行询价脚本，如输出 `[REGISTRATION_REQUIRED]` 则进入场景零后重试

### 命令

**跑腿配送：**
```bash
node scripts/order-price.js --fromAddress="起始地址" --toAddress="目的地址" --cityName="郑州市"
```

**帮忙服务：**
```bash
node scripts/order-price.js --fromAddress="帮忙地点" --toAddress="帮忙地点" --orderType="help"
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--fromAddress` | 起始地址（帮忙时为帮忙地点） | 是 |
| `--toAddress` | 目的地址（帮忙时为帮忙地点） | 是 |
| `--cityName` | 城市名称（需带"市"字，默认"郑州市"） | 否 |
| `--orderType` | `send`=配送(默认)，`help`=帮忙 | 否 |

### 回复模板

```
💰 {跑腿配送/帮忙服务}费用查询结果：

{起点/服务地点}：{fromAddress}
{终点（仅配送）：{toAddress}}
预估费用：{price/100} 元

📝 如需下单，请提供收件人电话{帮忙订单加：和具体帮忙内容}。
```

> 返回包含 `priceToken` 和价格信息（单位：分，展示时除以 100 转元）。

---

## 场景二：创建订单（发单）

用户明确要发单时，**询价后直接创建订单，无需二次确认**。

### 订单类型对比

| 维度 | 跑腿配送(SEND) | 帮忙服务(HELP) |
|------|---------------|---------------|
| 核心行为 | 物品从A送到B | 跑男在现场提供协助 |
| 地址 | 起始 ≠ 目的 | 起始 = 目的（同一地点） |
| 必填参数 | fromAddress, toAddress, receiverPhone | fromAddress, receiverPhone, **note** |
| 帮忙场景 | - | 帮取号、帮搬装、帮扔杂物、其他协助 |

### 执行步骤

1. 获取必要信息（地址、收件人电话、帮忙内容）
2. 调用询价接口获取 priceToken（参照场景一命令）
3. **立即创建订单**，不询问确认
4. 处理返回结果

### 创建订单命令

```bash
# 跑腿配送
node scripts/create-order.js --priceToken="xxx" --receiverPhone="13800138000"

# 帮忙服务（必须带 --note）
node scripts/create-order.js --priceToken="xxx" --receiverPhone="13800138000" --note="帮忙内容描述"

# 微信渠道：追加 --channel="wechat" 生成二维码
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--priceToken` | 询价返回的 token | 是 |
| `--receiverPhone` | 收件人手机号 | 是 |
| `--channel` | 渠道（wechat/feishu/dingtalk 等） | 否 |
| `--note` | 帮忙内容描述 | 帮忙必填 |

### 返回结果处理

**情况一：余额充足（订单创建成功）**

```
订单创建成功！

订单编号：{order_code}
{帮忙订单：帮忙内容：{note} | 服务地点：{fromAddress}}
配送费用：{price/100} 元

跑男正在接单中，请保持电话畅通。
```

**情况二：余额不足（`[PAYMENT_REQUIRED]`）**

关键输出：`ORDER_CODE`、`PAYMENT_URL`、`QRCODE_FILE`（仅 `--channel="wechat"` 时）。

**微信渠道**（链接无法直接打开，必须发二维码图片）：

```
message(action=send, channel="wechat", path="{QRCODE_FILE}", message="请扫码支付 {price/100} 元")
```

**其他渠道**：直接发送支付链接 `{PAYMENT_URL}`（支持微信/支付宝）。

用户返回后询问支付状态，确认后查询订单详情：

```bash
node scripts/order-detail.js --orderCode="{order_code}"
```

### 完整流程示例

```
用户：帮我从金水区送到二七区德化街，电话 13800138000
Agent：询价 → 创建订单 → 余额充足则返回成功，不足则引导支付

用户：帮我在郑州人民医院挂个号
Agent：识别帮忙服务 → 询价 → 获取电话 → 创建订单（带 --note）
```

---

## 场景三：查询订单详情

```bash
node scripts/order-detail.js --orderCode="UU123456789"
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--orderCode` | 订单编号 | 是 |

回复模板：
```
📋 订单详情：
订单编号：{order_code} | 状态：{status}
起点：{from_address} | 终点：{to_address}
配送费：{price/100} 元
跑男：{driver_name} {driver_phone}
```

---

## 场景四：取消订单

```bash
node scripts/cancel-order.js --orderCode="UU123456789" --reason="取消原因（可选）"
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--orderCode` | 订单编号 | 是 |
| `--reason` | 取消原因 | 否 |

---

## 场景五：跑男实时追踪

```bash
node scripts/driver-track.js --orderCode="UU123456789"
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--orderCode` | 订单编号 | 是 |

回复模板：
```
跑男实时位置：
跑男：{driver_name} | 电话：{driver_phone}
当前位置：{current_location} | 预计送达：{estimated_time}
```

---

## 配置管理

配置分为两层，优先级：**环境变量 > config.json > defaults.json**。

| 文件 | 内容 | 说明 |
|------|------|------|
| `defaults.json` | appId、appSecret、apiUrl | 内置凭证，**请勿修改** |
| `config.json` | openId（或完整凭证） | 注册后自动生成或手动创建 |

### 环境变量

| 变量 | 说明 |
|------|------|
| `UUPT_APP_ID` | 应用 ID |
| `UUPT_APP_SECRET` | 应用密钥 |
| `UUPT_OPEN_ID` | 用户唯一标识 |
| `UUPT_API_URL` | API 地址（可选，默认生产环境） |

### API 环境

| 环境 | URL |
|------|-----|
| 生产环境 | `https://api-open.uupt.com/openapi/v3/` |
| 测试环境 | `http://api-open.test.uupt.com/openapi/v3/` |

---

## 在代码中使用

### Node.js

```javascript
const { orderPrice, createOrder, orderDetail, cancelOrder, driverTrack } = require('./index');

// 配送询价
const price = await orderPrice({ fromAddress: '...', toAddress: '...', cityName: '郑州市' });
// 帮忙询价
const helpPrice = await orderPrice({ fromAddress: '...', orderType: 'help' });
// 创建订单
const order = await createOrder({ priceToken: price.body.priceToken, receiverPhone: '13800138000' });
// 帮忙订单（带 note）
const helpOrder = await createOrder({ priceToken: helpPrice.body.priceToken, receiverPhone: '13800138000', note: '帮忙内容' });
// 余额不足检测
if (order.body.orderUrl) console.log('支付链接:', order.body.orderUrl);
// 查询订单
const detail = await orderDetail({ orderCode: order.body.orderCode });
```

### Python

```python
from uupt_delivery import order_price, create_order, order_detail, cancel_order, driver_track

# 配送询价
price = order_price(from_address='...', to_address='...', city_name='郑州市')
# 帮忙询价
help_price = order_price(from_address='...', order_type='help')
# 创建订单
order = create_order(price_token=price['body']['priceToken'], receiver_phone='13800138000')
# 帮忙订单（带 note）
help_order = create_order(price_token=help_price['body']['priceToken'], receiver_phone='13800138000', note='帮忙内容')
# 余额不足检测
if order['body'].get('orderUrl'): print('支付链接:', order['body']['orderUrl'])
# 查询订单
detail = order_detail(order_code=order['body']['orderCode'])
```

---

## 注意事项

- **首次使用**：需通过手机号验证获取授权，之后无需重复。注册失败自动重试，最多 3 次（无需重新输入手机号）
- **图片验证码**：短信发送时若返回 `[IMAGE_CAPTCHA_REQUIRED]`，展示 base64 图片给用户识别后重试
- **询价有效期**：priceToken 有时效性，建议获取后尽快创建订单
- **价格单位**：API 返回的价格单位是分，展示时除以 100 转换为元
- **地址完整性**：地址越完整配送越准确。未指定城市默认"郑州市"
- **余额不足**：`[PAYMENT_REQUIRED]` 时，微信渠道用 `message` 发送二维码图片附件，其他渠道发送支付链接
- **帮忙订单**：必须传 `--note` 参数，fromAddress = toAddress；务必先确认帮忙内容再下单
- **配置文件**：`defaults.json` 为内置凭证，请勿修改或删除

## 相关链接

- [UU跑腿开放平台](https://open.uupt.com/#/development/agentSkill/quickStart)
- [GitHub地址](https://github.com/uupt-mcp/uupt-delivery-skill)
