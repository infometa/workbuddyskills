---
name: hanyi-fonts
description: 查询汉仪企业签约主体、合同覆盖字体和权益摘要，并生成字体预览
version: "0.1.0"
author: "Hanyi Fonts"
---

# 汉仪字库权益查询

本 Skill 使用当前用户已经授权的 HanyiDeliver 身份，查询其有权访问的签约主体、合同覆盖字体和单款字体权益摘要，并为当前有效字体生成选型预览。

## 推荐调用流程

1. 先调用 `list_my_font_accounts`。只有一个签约主体时可以继续；有多个时先请用户选择。
2. 需要找字体时调用 `search_my_entitled_fonts`。`next_cursor` 非空时，按用户需要继续翻页。
3. 需要查看期限、授权范围摘要、依据或资源入口时，调用 `get_my_font_entitlement`。
4. 需要查看指定文字的字体效果时，选择 `active` 且 `preview_available=true` 的字体，再调用 `preview_my_entitled_font`。用返回的 `preview_url` 作为普通 HTTPS 图片地址展示，不要转换为 Base64 或 data URL。

## 可用工具

### `list_my_font_accounts`

列出当前 OAuth 用户可访问的企业和签约主体。无业务参数。

### `search_my_entitled_fonts`

在一个签约主体的合同覆盖字体中搜索。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `account_ref` | 是 | `list_my_font_accounts` 返回的安全引用 |
| `query` | 否 | 字体名称关键词 |
| `status` | 否 | `active`、`not_started`、`expired`、`revoked` 或 `unknown` |
| `page_size` | 否 | 1–100 |
| `cursor` | 否 | 继续上一页时使用服务返回的 `next_cursor` |

### `get_my_font_entitlement`

返回一款字体的状态、期限、授权范围安全摘要、依据引用和资源入口。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `account_ref` | 是 | 当前用户选择的签约主体安全引用 |
| `font_ref` | 是 | 搜索结果返回的字体安全引用 |

### `preview_my_entitled_font`

为当前有效且支持预览的字体生成单行 PNG。结果地址最多保留 5 分钟，仅用于字体选型。

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `account_ref` | 是 | 当前用户选择的签约主体安全引用 |
| `font_ref` | 是 | 搜索结果返回且 `preview_available=true` 的字体安全引用 |
| `text` | 是 | 1–40 个字符的单行预览文字 |
| `font_size` | 否 | 24–96，默认 48 |

## 授权与安全边界

- 首次连接由 WorkBuddy 打开汉仪 OAuth 页面；短期 Access Token 失效时由 WorkBuddy 使用 Refresh Token 自动续期，Refresh Token 失效或被撤销时提示用户重新连接并授权。
- “合同当前有效”不等于办公、广告、视频、网站等具体用途已经获得允许。
- 对具体使用场景保留工具返回的 `needs_review`，不得由模型推断、扩展或虚构授权。
- 资源链接用于交付，不代表获得所有用途授权。
- 字体预览只用于选型，不代表办公、广告、视频、网站等具体使用场景已经获得授权。
- 预览必须使用工具返回的短期 HTTPS `preview_url`；不要把图片转换成 Base64、data URL 或长期保存地址。
- 不要求用户提供 HanyiDeliver Token、原始企业标识、合同编号或任意用户 ID。
- 引用无效或不属于当前用户时，不猜测对象身份；让用户重新列出签约主体和字体。
- 上游不可用时明确说明暂时无法取得权威结果，不使用缓存或常识替代授权事实。

## English guidance

- Start with `list_my_font_accounts` and ask the user to choose when multiple accounts are available.
- Use `search_my_entitled_fonts` for entitled-font discovery and follow `next_cursor` only when more results are needed.
- Use `get_my_font_entitlement` for dates, scope summaries, evidence references, and resource links.
- Use `preview_my_entitled_font` only for an active font with `preview_available=true`, then display its temporary HTTPS `preview_url` directly. Do not convert it to Base64 or a data URL.
- Never turn an active contract status into an allowed usage decision. Keep specific-use conclusions at `needs_review` unless authoritative structured data says otherwise.
