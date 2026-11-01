---
name: ycloud-whatsapp
description: >-
  引导用户通过 YCloud Partner Direct Link 完成 WhatsApp Business 账号（WABA）绑定配置。
  当用户说「配置 WhatsApp、开通 WhatsApp、连接 WhatsApp、绑定 WABA、WhatsApp 入驻、
  WhatsApp 注册、onboarding、Continue with Meta、WhatsApp 链接过期、重新连接 WhatsApp、
  Partner Direct Link、SDK Button」时使用。用 scripts/get_onboarding_url.py 获取
  Onboarding Link，再按 Direct Link 或 SDK Button 完成 Meta 托管注册。
version: "1.1.0"
author: "Meorient"
display_name: "YCloud WhatsApp 账号配置"
---

# YCloud WhatsApp 账号配置（Partner Direct Link）

Partner Direct Link 帮助技术合作伙伴（TP）快速接入 WhatsApp：

- TP **无需成为 Meta 官方合作伙伴**
- 只需成为 YCloud Tech partner，借助 Partner Direct Link，即可在 partner 产品/服务中接入 WhatsApp
- 由服务端拿到一次性 Onboarding Link 后，可通过以下任一方式完成注册：
  - **SDK Button（推荐）**：在 TP 网页中放置按钮，经 YCloud SDK 打开注册窗口
  - **Direct Link**：客户点击后直接进入托管注册页，无需集成 SDK

> 推荐先用 **Direct Link** 联调/引导终端用户完成绑定，再按需接入 SDK Button。

**本 skill 取链方式**：一律用本目录脚本 `scripts/get_onboarding_url.py`（DealClaw 封装）。拿到 `onboardingUrl` 之后的打开方式、客户操作、Webhook、错误重试，均按下文接入指南执行。

## Agent 工作流（必循）

```
WhatsApp 配置进度:
- [ ] 1. 确认意图（首次连接 / 链接过期重试 / 换绑新增）
- [ ] 2. 调 xiaoyuan_get_company_basic_info 取 companyId → 作为 partnerCustomerId
- [ ] 3. 运行 get_onboarding_url.py 拿到 onboardingUrl
- [ ] 4. 按 Direct Link（默认）或 SDK Button 引导完成注册
- [ ] 5. 确认结果（以 Webhook / 业务侧状态为准）
```

### 硬约束

- `onboardingUrl` 是短期安全凭证：一对一交给当前客户，**禁止**写入公开日志、分析平台、群聊或公开页面。
- 一个链接仅用于**一个客户的一次 WABA 连接**；默认有效期 **2 小时**。绑定成功后不能再绑其他 WABA。
- 创建/获取链接只能走服务端（本 skill = 脚本）；**不要把 YCloud API Key 放在浏览器或 App 中**，也不要向终端用户索取 API Key。
- 页面/SDK 回调只作前端提示；**最终绑定结果以服务端 Webhook 为准**。
- `partnerCustomerId` **必须**用当前用户的 `companyId`（见 §3.1），不要向用户索要，也不要把企业 API Key 当 customerId。

---

## 1. 接入前准备工作（TP 侧，平台已具备时可跳过）

请确认：

1. YCloud 已为账号开通 Partner Direct Link（申请 Tech partner：https://www.ycloud.com/tech-partner）。
2. 已在 **Developers > API Key** 创建 API Key。
3. 已在 **Developers > Webhooks** 配置接收地址，并订阅 `whatsapp.business_account.updated`。
4. 创建链接的接口只能由服务端调用（本环境由 DealClaw + 脚本完成）。

终端用户只做「拿链接 → 打开 → Continue with Meta」时，Agent 不必展开本节，除非排障需要。

## 2. 配置 Partner Direct Link（TP Dashboard）

进入 YCloud Dashboard → **Developers > Partner Direct Link**，完成 Basic settings：

| 配置项 | 是否必填 | 说明 |
| --- | --- | --- |
| Display name | 是 | 客户在托管注册页看到的 TP 名称 |
| Partner logo | 否 | 客户看到的 TP Logo |
| Redirect URL (Direct Link only) | 否 | Direct Link 成功后的跳转地址，须完整 HTTPS URL；未配置则展示带 TP 品牌的成功页 |
| Allowed SDK origins (SDK Button only) | 否 | 使用 SDK Button 时必须配置。填写承载 SDK 的网页 Origin，如 `https://app.example.com`，不要填路径 |

Allowed SDK origins 注意事项：

- 必须精确填写「协议 + 域名 + 可选端口」，例如 `https://app.example.com`
- 生产环境使用 **HTTPS**；HTTP 仅允许 `localhost` 本地调试
- 不支持通配符；不同子域名或端口需分别添加
- 未配置时 Direct Link 仍可用，但 SDK Button 不可用

## 3. 获取 Onboarding Link（本 skill 固定方式）

### 3.1 取得 partnerCustomerId（= companyId）

`partnerCustomerId` 传当前用户的 **companyId**。先调小元 MCP 工具（无参数）：

```
xiaoyuan_get_company_basic_info
```

从返回中读取 `companyId`（企业 ID / supplierId），原样作为 `--customer-id` / `partnerCustomerId`。

- 身份由连接器里的企业 API Key 解析，**不要**向用户询问 companyId / supplierId / partnerCustomerId
- `companyId` 仅用于脚本取链与工具间流转，**不要**在最终回复里展示给用户（对外用公司名等可读信息）
- 调用失败（401/403 等）→ 按小元 skill 引导更新 API Key；不要猜测或编造 companyId
- YCloud 会在绑定成功 Webhook 中原样返回该 `partnerCustomerId`

### 3.2 运行脚本

```bash
python scripts/get_onboarding_url.py --customer-id <companyId>
```

可选：`--raw` 打印完整响应；`--base-url` / `--timeout` 按需覆盖。

脚本请求：

```
GET https://dealclaw.datathink.com/whatsapp/api/whatsapp/wabas?partnerCustomerId={customerId}
```

### 3.3 解读脚本输出

成功且待绑定（节选字段）：

```json
{
  "ok": true,
  "already_connected": false,
  "partnerCustomerId": "customer_001",
  "onboardingUrl": "https://connect.ycloud.com/open/whatsapp/onboard#token=...",
  "expiresAt": 1791459090754,
  "expiresAtIso": "2026-10-08T11:31:30.754Z",
  "status": "PENDING",
  "locale": "zh_CN",
  "onboardingType": "WHATSAPP_BUSINESS_PLATFORM"
}
```

| 输出情况 | Agent 动作 |
| --- | --- |
| `ok: true` 且有 `onboardingUrl` | 交给用户；说明 `expiresAtIso`；进入第 4 或第 5 节 |
| `already_connected: true`（已有 `wabaId`） | **不要再发引导链接**；告知已连接。若要测发送，改走小元 `list_whatsapp_templates` / 确认后 `send_whatsapp_template` |
| `ok: false` / 无可用链接 | 核对 `partnerCustomerId`、网络；勿伪造链接；勿循环狂刷 |

接口响应中 `wabas[]` 常见字段：`onboardingUrl`、`expiresAt` / `expiresAtIso`、`status`、`onboardingType`、`locale`、`wabaId`、`phoneNumberId`、`paymentMethodAttached` 等。脚本会优先返回未过期且带 URL 的待绑定项。

### 3.4 与指南原文「创建 Link」的对应关系

YCloud 原文创建接口为：

```bash
curl -X POST 'https://api.ycloud.com/v2/partner/embeddedSignup/links' \
  -H 'X-API-Key: YOUR_YCLOUD_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "partnerCustomerId": "customer_001",
    "onboardingType": "WHATSAPP_BUSINESS_PLATFORM",
    "locale": "en_US"
  }'
```

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `partnerCustomerId` | 是 | 客户唯一标识；Webhook 原样返回 |
| `onboardingType` | 是 | `WHATSAPP_BUSINESS_PLATFORM`（API WABA）；`WHATSAPP_BUSINESS_APP`（SMB WABA） |
| `locale` | 否 | 托管页语言，默认 `en_US` |

支持的 `locale`（区分大小写，其他值 HTTP 400）：

| 值 | 语言 |
| --- | --- |
| `en_US` | English |
| `zh_CN` | 简体中文 |
| `es_ES` | Español |
| `pt_BR` | Português (Brasil) |
| `id_ID` | Bahasa Indonesia |
| `ru_RU` | Русский |

原文响应：`{ "onboardingUrl", "expiresAt" }`。本 skill **不**让 Agent/浏览器直调该 POST；DealClaw + `get_onboarding_url.py` 已封装取链。拿到的 `onboardingUrl` / `expiresAt` 语义与原文一致。

向用户交付时：

1. 给出完整可点击的 `onboardingUrl`
2. 说明过期时间
3. 提醒本人在有效期内打开，勿转发无关人员

---

## 4. 使用方式一：Direct Link（引导终端用户时默认）

拿到 `onboardingUrl` 后：在客户系统提供「连接 WhatsApp」并跳转/新窗口打开该地址；或通过安全的一对一渠道发送给对应客户。不要公开展示或批量共享。

客户依次完成：

1. 打开托管注册页面
2. 点击 **Continue with Meta**
3. 在 Meta 窗口中选择或创建业务、WABA 和号码
4. YCloud 完成绑定并展示成功结果
5. 如已配置 Redirect URL，页面跳转并附加 `status=connected` 查询参数

链接生命周期：

- 一个链接仅用于一个客户的一次 WABA 连接
- 默认有效期 **2 小时**
- 注册完成前，有效期内可刷新或重新尝试，无需立刻重新取链
- 同一链接可换浏览器打开；成功绑定后不能再用于绑定其他 WABA
- 更换或新增 WABA 时，重新运行 `get_onboarding_url.py`（由平台侧决定是否新建）

Agent 话术补充：弹窗被拦截时，允许弹窗后重试。

---

## 5. 使用方式二：SDK Button（推荐用于 TP 自有网页）

让客户停留在 TP 网页中，通过弹窗完成注册。开始前须在 **Allowed SDK origins** 中添加该网页 Origin。

### 5.1 从服务端获取链接

浏览器应调用你们自己的后端；后端再用 DealClaw/`get_onboarding_url.py` 同源能力取 `onboardingUrl` 返回给前端。**不要**在前端直接调用 YCloud 创建接口。

### 5.2 加载 SDK 并打开注册窗口

```html
<script src="https://connect.ycloud.com/open/sdk/v1.js"></script>

<button id="yc-onboarding" type="button">Continue with Meta</button>

<script>
  document.getElementById('yc-onboarding').addEventListener('click', async function () {
    // 由你们的后端取链（对应本 skill 的 get_onboarding_url.py / DealClaw）
    const response = await fetch('/api/ycloud/onboarding-link', { method: 'POST' });
    const { onboardingUrl } = await response.json();

    YCloudOnboarding.open({
      onboardingUrl,
      onStatus: function (result) {
        if (result.state === 'CONNECTED') {
          console.log('WhatsApp connected', result.wabaId);
        }
      },
      onError: function (error) {
        console.error('Unable to open onboarding', error);
      },
      onClose: function (event) {
        console.log('Customer closed the onboarding window', event.reason);
      }
    });
  });
</script>
```

### 5.3 JavaScript 回调

`onStatus(result)` — 成功示例：

```json
{
  "state": "CONNECTED",
  "wabaId": "{WABA_ID}",
  "phoneNumberId": "{PHONE_NUMBER_ID}"
}
```

失败示例：

```json
{
  "state": "RETRYABLE_FAILED",
  "errorCode": "{ERROR_CODE}",
  "retryable": true,
  "requestId": "{REQUEST_ID}"
}
```

| 字段 | 说明 |
| --- | --- |
| `state` | `CONNECTED` 表示连接成功；其他表示未完成或失败 |
| `wabaId` | 仅成功时返回 |
| `phoneNumberId` | 成功时可能返回 |
| `errorCode` | 失败时可能返回 |
| `retryable` | 是否可在当前注册窗口重试 |
| `requestId` | 排查时可提供给技术支持 |

`onError(error)` — SDK 未能打开窗口，例如：

```json
{
  "code": "POPUP_BLOCKED",
  "message": "The onboarding popup was blocked by the browser"
}
```

`code` 可能为 `POPUP_BLOCKED` 或 `INVALID_ONBOARDING_URL`。

`onClose(event)` — 仅在客户尚未获得最终结果便关闭窗口时触发：

```json
{
  "reason": "USER_CLOSED"
}
```

这些回调只用于更新前端提示；请以服务端 Webhook 作为最终绑定结果。

---

## 6. 接收绑定成功 Webhook

绑定成功后，YCloud 向已配置地址推送 `whatsapp.business_account.updated`：

```json
{
  "id": "evt_6a990157f7a61232eb60000a",
  "type": "whatsapp.business_account.updated",
  "apiVersion": "v2",
  "createTime": "2026-09-03T05:10:47.773Z",
  "whatsappBusinessAccount": {
    "id": "{WABA_ID}",
    "name": "{WABA_NAME}",
    "currency": "AUD",
    "messageTemplateNamespace": "{WABA_NAMESPACE}",
    "accountReviewStatus": "APPROVED",
    "businessId": "{BUSINESS_ID}",
    "businessStatus": "APPROVED",
    "businessName": "{BUSINESS_NAME}",
    "businessVerificationStatus": "verified",
    "whatsappBusinessManagerMessagingLimit": "TIER_2K",
    "ownershipType": "CLIENT_OWNED",
    "primaryFundingId": "{PRIMARY_FUNDING_ID}",
    "timezoneId": "42",
    "updateEvent": "PARTNER_ADDED",
    "paymentMethodAttached": true,
    "isOnBizApp": false,
    "partnerCustomerId": "test_customer_001"
  }
}
```

处理规则：

- `whatsappBusinessAccount.updateEvent` 为 `PARTNER_ADDED` 时，按新增 WABA 处理
- 用 `partnerCustomerId` 关联客户，并保存 `whatsappBusinessAccount.id`
- `paymentMethodAttached` 为 `true` 表示授信成功、WABA 可正常使用；`false` 表示授信尚未完成
- 使用事件 `id` 做幂等；成功接收后返回 HTTP 2xx

对终端用户：页面已成功 → 告知平台会经 Webhook 落库，稍后在业务侧查看通道是否可用。`paymentMethodAttached == false` 时说明可能尚不可正常发信。

---

## 7. 错误与重试

| 情况 | 处理建议 |
| --- | --- |
| 客户关闭 Meta 窗口或流程中断 | 原链接有效期内重新打开，再点 **Continue with Meta** |
| 页面提示链接过期或无效 | 重新运行 `python scripts/get_onboarding_url.py --customer-id <id>` |
| SDK 提示 Origin 无效 | 检查当前网页 Origin 是否已精确加入 Allowed SDK origins |
| 创建/取链返回 HTTP 429 | 按 `Retry-After` 等待后重试，避免循环创建链接 |
| 页面显示成功，但业务系统未更新 | 检查 Webhook 配置、订阅事件与接收日志；最终以 Webhook 为准 |
| 脚本失败 / 无 wabas | 核对 `partnerCustomerId` 与网络；不要伪造链接 |

## 安全与隐私

- 可把当前用户自己的 `onboardingUrl` 交给本人；不要把文档/历史示例中的 token 当作有效链接
- 不要把完整 token 链贴进会进公开日志的渠道
- 内部字段（event id、funding id 等）除非排障，不必向用户展开
