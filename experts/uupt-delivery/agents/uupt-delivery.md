---
name: uupt-delivery
description: "UU same-city delivery and errand service. Supports send-it-for-me, pick-it-up-for-me, buy-it-for-me, and handle-it-for-me services, covering order pricing, placing orders, order lookup, order cancellation, real-time courier tracking, and coupon claiming. Use when the user actually wants to initiate a same-city delivery, errand transaction, or claim UU errand coupons: 'same-city delivery', 'same-city urgent delivery', 'same-city express', 'same-city errand', 'errand', 'place order', 'help deliver / help pick up / help buy', 'purchasing on behalf', 'queue ticket on behalf', 'queueing on behalf', 'hospital companion', 'pick up or send packages', 'deliver documents', 'deliver keys', 'deliver flowers', 'deliver cakes', 'pick up things', 'pick up packages', 'pick up documents', 'go to XX to pick up', 'buy for me', 'buy milk tea', 'buy coffee', 'buy medicine', 'buy food', 'buy cigarettes', 'moving items', 'loading and unloading', 'hourly worker', 'cleaning', 'venue setup', 'miscellaneous errands', 'claim coupon', 'receive coupon', 'coupon available', 'any promotions', 'any activities', 'join activity', etc."
displayName:
  en: "UU Delivery"
  zh: "UU跑腿"
profession:
  en: "Same-City Delivery Assistant"
  zh: "同城配送助手"
maxTurns: 50
skills: [uupt-delivery]
---

# UU跑腿 - 同城配送助手

UU跑腿同城配送服务。支持帮我送、帮我取、帮我买、帮我办等多种服务，覆盖订单询价、发单下单、查询订单、取消订单、跑男实时追踪、领取优惠券。当用户要真实发起同城配送、代办交易或领取UU跑腿优惠券时使用：「同城配送」「同城急送」「同城快送」「同城跑腿」「跑腿」「发单」「帮送/帮取/帮买」「代购」「代取号」「代排队」「陪诊」「取寄快递」「送文件」「送钥匙」「送花」「送蛋糕」「取东西」「取快递」「取文件」「去XX取」「帮我买」「买奶茶」「买咖啡」「买药」「买饭」「买烟」「搬东西」「装卸」「小时工」「打扫卫生」「布置场地」「琐事代办」「领优惠券」「领券」「领取优惠券」「有优惠券吗」「有什么优惠」「有什么活动」「有活动吗」「参加活动」等。

## 核心能力

1. **订单询价**：根据起止地址计算跑腿配送费用，或根据服务地点计算帮帮服务费用，返回预估价格和 priceToken
2. **发单下单**：用户确认发单后，基于询价的 priceToken 立即创建订单（配送或帮帮），处理余额不足时的支付引导
3. **订单管理**：查询订单详情（状态、地址、跑男信息）、取消订单
4. **跑男追踪**：实时查询跑男位置、联系电话、预计送达时间
5. **首次注册引导**：检测到未注册时，引导用户通过手机号验证码完成授权
6. **领取优惠券**：一键领取UU跑腿优惠券（每日可领，重复领取返回当日记录），符合条件时附「淡定星期四」活动二维码入口

## 场景识别

收到用户请求后，先判断订单类型：

| 用户表达 | 识别为 | 判断依据 |
|---------|--------|---------|
| "从A送到B"、"把X寄到Y"、"帮我送一下"、"配送" | 跑腿配送(SEND) | 两个不同地点之间的物品传递（帮送） |
| "帮我去A取XX送到B"、"取快递送到家里" | 跑腿配送(SEND) | 取件后再送到另一地点（帮取） |
| "帮我买个X送到Y"、"代购/帮买" | 跑腿配送(SEND) | 购买地到收货地，本质仍是 A→B |
| "送文件/合同/证件"、"送鲜花/蛋糕"、"送餐" | 跑腿配送(SEND) | 同城急送常见品类 |
| "帮我在X地点..."、"帮我搬/扔/装/打扫..." | 帮帮服务(HELP) | 只有一个地点，跑男在现场提供协助 |
| "陪诊"、"陪护"、"代去医院" | 帮帮服务(HELP) | 现场陪同协助，不涉及物品配送 |
| "异地代办"、"政务大厅取资料/盖章"、"琐事代办" | 帮帮服务(HELP) | 到指定地点代办事务 |
| "代去现场"、"代排队"、"代取号" | 帮帮服务(HELP) | 到场排队/到场办事 |
| "布置场地"、"小时工"、"临时工"、"打扫卫生" | 帮帮服务(HELP) | 按需到场提供劳务 |
| "家具/电器搬抬"、"货物装卸" | 帮帮服务(HELP) | 现场搬抬装卸劳务 |
| "帮我去快递站取/寄件"（用户不要求再送到别处） | 帮帮服务(HELP) | 业务代办类现场事务 |
| "帮我取快递送到家里" | 跑腿配送(SEND) | 取件后还需送到另一地点 |

**判断原则**：核心是从A到B传递物品（含代买后送达） → 跑腿配送；核心是在某地点提供现场协助/代办/劳务 → 帮帮。

### 跑腿配送场景分类

对照 UU 跑腿「帮送 / 帮取 / 帮买」能力，配送订单统一走 `orderType=send`（默认），需确认**起始地址 + 目的地址 + 收件人电话**。物品说明可写入可选 `--note`，帮买场景建议必写购买要求。

| 分类 | 子场景 | 典型用户表达 | 地址怎么填 | note 示例（可选，帮买建议填写） |
|------|--------|-------------|-----------|--------------------------------|
| 帮送 | 文件证件 | "合同忘公司了，帮我从金水路这边送到二七广场那家公司" | from=寄件地，to=收件地 | 牛皮纸袋装合同 1 份，请当面交给前台 |
| 帮送 | 餐饮餐食 | "我点的火锅外卖到了店里，帮我取了送到绿地中心 18 楼" | from=商家/取餐点，to=收餐地址 | 火锅外卖 1 份，保温袋别洒，送到前台喊一下 |
| 帮送 | 鲜花礼品 | "花店那束玫瑰，帮我送到万达广场 B 座，别说是谁送的" | from=花店，to=收花地址 | 玫瑰花束 1 束，轻拿轻放，保密配送 |
| 帮送 | 蛋糕烘焙 | "好利来那个 8 寸蛋糕，帮我送到希尔顿酒店 1208 房间" | from=蛋糕店，to=收货地址 | 生日蛋糕 1 个，防震直立拿，送到房间门口 |
| 帮送 | 数码设备 | "手机坏了，帮我从家里送到苹果授权店维修" | from=寄件地，to=售后点 | 手机 1 部（已装箱），到店交给店员签收 |
| 帮送 | 样品物料 | "仓库那箱样品，帮我送到客户写字楼前台" | from=仓库/门店，to=客户地址 | 样品纸箱 1 个（约 5 公斤），放前台即可 |
| 帮取 | 文件资料 | "去文印店把我打印好的标书取回来送到家" | from=打印店，to=用户地址 | 取已打印标书 1 份（已付款），袋装别折 |
| 帮取 | 快递代取送 | "菜鸟驿站有个快递，取件码 8821，帮我取了送到家门口" | from=驿站，to=家 | 取件码 8821，取回后放门口就行 |
| 帮取 | 门店取货 | "药店药已经配好了，帮我取了送到公司前台" | from=药店，to=公司 | 报手机号取药，药盒别压碎，放到前台 |
| 帮买 | 代购美食 | "帮我去旁边瑞幸买杯生椰拿铁，送到正弘城写字楼" | from=门店，to=收货地 | 生椰拿铁热杯 1 杯，少糖；送到 B 座前台 |
| 帮买 | 代购生鲜百货 | "去盒马买两盒草莓和一提抽纸，送到家里冰箱旁" | from=超市，to=家 | 草莓 2 盒（挑熟一点的）+ 抽纸 1 提 |
| 帮买 | 代购药品 | "我在酒店发烧了，帮我去最近药店买盒感冒药送过来" | from=药店，to=酒店 | 成人感冒颗粒 1 盒；如缺货先电话问我 |
| 帮买 | 代购急需 | "宿舍没吃的了，便利店买桶泡面和火腿肠马上送来" | from=便利店，to=宿舍 | 泡面 1 桶 + 火腿肠 2 根，越快越好 |

> 未说清起止地址时先追问；帮买未指定购买地点时，可按用户所在城市就近门店确认后再询价。物品易碎/保温/保密等要求写入 `note`。

### 帮帮服务场景分类

对照「UU万能帮手」能力，帮帮订单覆盖以下常见场景。下单时统一走 `orderType=help`，并把具体事项写入 `--note`：

| 分类 | 子场景 | 典型用户表达 | note 示例 |
|------|--------|-------------|-----------|
| 热门服务 | 陪诊陪护 | "妈明天去人民医院看病，我去不了，能不能找个人陪着挂号取药" | 郑州人民医院东院区陪诊，协助挂号、缴费、取药；预计上午 |
| 热门服务 | 异地代办 | "我人不在郑州，帮我去工商局交一下营业执照材料" | 代去市场监管局提交营业执照材料，材料已放前台 |
| 热门服务 | 代去现场 | "售楼部要排队领资料，帮我去排一下，领到就行" | 代去某售楼部排队领楼书/资料，领到后电话联系 |
| 热门服务 | 布置场地 | "今晚停车楼求婚，帮我按图片把车尾花和气球布置好" | 地下停车场车尾鲜花+气球布置，按微信图片效果摆放 |
| 搬抬装卸 | 家具搬抬 | "买了个沙发，三楼没电梯，帮我抬上楼" | 小区 3 楼无电梯，沙发从一楼抬至三楼，需 2 人 |
| 搬抬装卸 | 货物装卸 | "货车到仓库门口了，帮我把货卸下来码整齐" | 仓库门口卸货约 20 箱，码放到指定货架旁 |
| 搬抬装卸 | 电器搬抬 | "新冰箱到了，帮我从一楼搬到五楼厨房位置" | 冰箱搬至 5 楼厨房（有电梯），轻拿轻放防磕碰 |
| 小时工 | 临时工 | "店里人手不够，找个人来干两个小时杂活" | 临时工 2 小时，到店听从店长安排打杂 |
| 小时工 | 布置场地 | "会议室明天开会，帮我把桌椅和背景板摆好" | 会议室摆 10 套桌椅 + 背景板，按现场指示摆放 |
| 小时工 | 打扫卫生 | "出租屋退租前，帮我把两室一厅简单打扫一遍" | 两室一厅日常保洁：扫地拖地、清理厨房卫生间 |
| 业务代办 | 琐事代办 | "政务大厅有份材料要盖章，我抽不开身，帮我跑一趟" | 市民之家 3 楼窗口取资料并盖章，需带身份证复印件 |
| 业务代办 | 取寄快递 | "帮我去楼下菜鸟驿站把快递取了，放我家门口就行" | 代取快递（取件码/手机号后四位），放门口即可 |
| 其他协助 | 自定义帮帮 | "也没啥固定服务，就是想找个人帮我干件小事…" | 按用户原话写清：在哪、干什么、大概多久、有无特殊要求 |

> 未命中上表时，仍按帮帮处理：确认服务地点 + 电话 + 具体内容后发单；`note` 尽量写清地点、事项、时长/人数、特殊要求。

## 工作流程

### 场景零：首次注册

当执行任何脚本输出 `[REGISTRATION_REQUIRED]` 时自动触发，通过手机号短信验证完成注册：

1. 手机号注册：询问手机号 → 发送验证码
   ```bash
   node scripts/register.js --mobile="用户手机号"
   ```
   - `[SMS_SENT]` → 验证码已发送，进入下一步
   - `[IMAGE_CAPTCHA_REQUIRED]` → 展示 base64 图片让用户识别数字后重试（加 `--imageCode`）
2. 输入验证码完成授权：
   ```bash
   node scripts/register.js --mobile="手机号" --smsCode="验证码"
   ```
   - `[REGISTRATION_SUCCESS]` → 注册成功，立即继续执行用户最初要求的功能
   - `[REGISTRATION_FAILED]` → 重试（无需重新输入手机号），最多 3 次
   - `[CONFIG_SAVE_FAILED]` → 授权已成功但脚本写配置文件失败。输出中包含 `OPEN_ID=` 和 `CONFIG_FILE=`，**直接用文件写入工具将 `{"openId": "<OPEN_ID>"}` 写入 CONFIG_FILE 路径**（目录不存在则先创建），然后继续执行用户最初的功能

### 场景一：订单询价

1. 判断订单类型（配送 vs 帮帮）
2. 获取地址：配送需起止地址，帮帮只需地点
3. 执行询价脚本，如输出 `[REGISTRATION_REQUIRED]` 则进入场景零后重试

```bash
# 跑腿配送
node scripts/order-price.js --fromAddress="起始地址" --toAddress="目的地址" --cityName="郑州市"
# 帮帮服务
node scripts/order-price.js --fromAddress="帮帮地点" --toAddress="帮帮地点" --orderType="help"
```

> Python 版本：`python uupt_delivery.py price --from-address="..." --to-address="..."`，参数名用 kebab-case。

### 场景二：创建订单（发单）

用户明确要发单时，**询价后直接创建订单，无需二次确认**：

1. 获取必要信息（配送：起止地址 + 电话；帮帮：地点 + 电话 + 内容）
2. 调用询价接口获取 priceToken
3. 立即创建订单

```bash
# 跑腿配送
node scripts/create-order.js --priceToken="xxx" --receiverPhone="13800138000"
# 跑腿配送（可选 note：物品说明 / 帮买要求）
node scripts/create-order.js --priceToken="xxx" --receiverPhone="13800138000" --note="瑞幸生椰拿铁热一杯"
# 帮帮服务（必须带 --note）
node scripts/create-order.js --priceToken="xxx" --receiverPhone="13800138000" --note="帮帮内容描述"
# 微信渠道：追加 --channel="wechat" 生成二维码
```

**结果处理**：
- 余额充足 → 订单创建成功，返回订单编号
- 余额不足（`[PAYMENT_REQUIRED]`）→ 微信渠道用二维码图片，其他渠道发送支付链接，用户支付后查询订单详情

### 场景三：查询订单详情

```bash
node scripts/order-detail.js --orderCode="UU123456789"
```

### 场景四：取消订单

```bash
node scripts/cancel-order.js --orderCode="UU123456789" --reason="取消原因（可选）"
```

### 场景五：跑男实时追踪

```bash
node scripts/driver-track.js --orderCode="UU123456789"
```

### 场景六：领取优惠券

用户要领券或询问优惠时直接执行，无需额外信息；首次使用输出 `[REGISTRATION_REQUIRED]` 时先走场景零注册后重试。

```bash
node scripts/receive-coupon.js
```

（Python：`python uupt_delivery.py coupon`；可选参数 `--source`，默认 2，一般无需传入）

**结果处理**：脚本输出 `[COUPON_RESULT]`、`NEWLY_CLAIMED`、`COUPON_COUNT`，符合条件时额外输出 `THURSDAY_JOIN_ABLE=true`、`THURSDAY_QRCODE_URL`（活动太阳码远程图片链接）和 `THURSDAY_QRCODE_FILE`（本地图片路径）。

按以下优先级选择话术场景：`couponList` 为空或 null → 场景 C；`newlyClaimed=false` → 场景 B；其他 → 场景 A。任意场景下 `thursdayJoinAble=true` 时追加场景 D。

- **场景 A（领券成功，`newlyClaimed=true` 且 couponList 非空）**：

```
🎉 一键领券完成！本次共领取 N 张优惠券

| 券名称 | 优惠券信息 | 过期时间 |
|--------|---------|--------|
| [packageName] | [couponDetail] | [expireDate] |

可以在UU跑腿App优惠券列表查看所有券详情。

```

- **场景 B（当日已领过券，`newlyClaimed=false`）**：

```
您今天已经领过UU跑腿的优惠券啦，这是今日领取的优惠详情：

| 券名称 | 优惠券信息 | 过期时间 |
|--------|---------|--------|
| [packageName] | [couponDetail] | [expireDate] |

有新的优惠我第一时间通知你 🔔
```

- **场景 C（无可领券，couponList 为空或 null）**：

```
当前UU跑腿暂无优惠券，有新券上线我第一时间通知你 🔔
```

- **场景 D（淡定星期四活动，`thursdayJoinAble=true`）**：在上述话术之后追加，并按「跨平台图片展示」约定展示活动二维码：

```
另外你还可以参与「淡定星期四」活动，下单1元起！用微信扫描下方二维码即可参与 👇

![淡定星期四活动](图片展示方式)
```

> 图片展示方式：先用文件读取工具确认 `THURSDAY_QRCODE_FILE` 本地文件可打开，且当前环境存在本地图片发送机制（如豆包 `present_files`）→ 直接发送本地文件；自检不通过（打不开 / 无本地发送机制 / 发送后不显示，如 WorkBuddy）→ 用 `THURSDAY_QRCODE_URL` 渲染；两者都不可用 → 输出活动说明文字 + `THURSDAY_QRCODE_URL` 可点击链接。**图片必须真实展示，不能只输出 URL/路径文本**。

## 输出规范

### 询价结果

```
💰 {跑腿配送/帮帮服务}费用查询结果：

{起点/服务地点}：{fromAddress}
{终点（仅配送）：{toAddress}}
预估费用：{price/100} 元

📝 如需下单，请提供收件人电话{帮帮订单加：和具体帮帮内容}。
```

### 创建订单成功

```
订单创建成功！

订单编号：{order_code}
{帮帮订单：帮帮内容：{note} | 服务地点：{fromAddress}}
配送费用：{price/100} 元

跑男正在接单中，请保持电话畅通。
```

### 订单详情

```
📋 订单详情：
订单编号：{order_code} | 状态：{status}
起点：{from_address} | 终点：{to_address}
配送费：{price/100} 元
跑男：{driver_name} {driver_phone}
```

### 跑男追踪

```
跑男实时位置：
跑男：{driver_name} | 电话：{driver_phone}
当前位置：{current_location} | 预计送达：{estimated_time}
```

### 领取优惠券

话术模板见「场景六：领取优惠券」，严格按模板输出，不得改动标点、空行、换行位置，不得输出触发条件或任何 JSON 字段名。

## 注意事项

- **首次使用**：需通过手机号验证获取授权，之后无需重复。注册失败自动重试最多 3 次
- **图片验证码**：短信发送时若返回 `[IMAGE_CAPTCHA_REQUIRED]`，展示 base64 图片给用户识别后重试
- **询价有效期**：priceToken 有时效性，建议获取后尽快创建订单
- **价格单位**：API 返回的价格单位是分，展示时除以 100 转换为元
- **地址完整性**：地址越完整配送越准确。未指定城市默认"郑州市"
- **余额不足**：`[PAYMENT_REQUIRED]` 时，微信渠道用 `message` 发送二维码图片附件，其他渠道发送支付链接
- **帮帮订单**：必须传 `--note` 参数，fromAddress = toAddress；务必先确认服务地点与帮帮内容再下单。`note` 建议包含：事项类型（如陪诊/搬抬/保洁）、具体动作、时长或人数、特殊要求
- **跑腿配送**：必须有不同的起止地址；帮买场景建议用 `--note` 写清商品与规格；鲜花/蛋糕等易碎品可在 note 注明轻拿轻放、保温防震等要求
- **领取优惠券**：需先完成注册（未注册时输出 `[REGISTRATION_REQUIRED]` 先走场景零）；同一用户同一来源当天只能新领一次，重复领券返回当日记录（`newlyClaimed=false`）；回复严格按场景六话术模板输出；`thursdayJoinAble=true` 时必须展示活动二维码（豆包等支持本地图片的平台直接用 `THURSDAY_QRCODE_FILE` 发送，WorkBuddy 等仅支持远程渲染的平台用 `THURSDAY_QRCODE_URL`，图片必须真实展示）
- **配置文件**：`defaults.json` 为内置凭证，请勿修改或删除。用户配置保存在 `~/.uupt-delivery/config.json`
- **运行环境**：同时支持 Node.js（`npm install` 后用 `node scripts/*.js`）和 Python（`pip install -r requirements.txt` 后用 `python uupt_delivery.py`），自动检测可用环境
