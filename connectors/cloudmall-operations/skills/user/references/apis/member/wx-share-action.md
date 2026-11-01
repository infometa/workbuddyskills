# 会员域 — 微信分享链接写操作契约

> 概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-support.md`。
> 生成类操作（无数据变更，但消耗微信接口配额）。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。
> 能力索引：member.wx-share.short-link 生成小程序短链 · member.wx-share.url-link 生成 URL Link · member.wx-share.qrcode 生成小程序太阳码

---

## ✅ 生成小程序短链 — ops.member.wx-share.short-link

- **仅微信内可用**；依赖租户小程序配置，未配置时生成失败

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageUrl | String | ✅ | 小程序页面路径（如 `pages/index/index`） |
| params | String | ✅ | 拼接到页面路径后的参数（如 `inviterUid=123&channel=points_mall`） |
| pageTitle | String | — | 页面标题（微信展示用） |
| envVersion | String | — | **仅支持 `release`**（微信短链接口限制，传 trial/develop 直接报错）；短链无环境参数概念 |

### 出参（原始返回）

对象含生成的短链 URL（`shortLink` 字段）。短链有有效期与访问量限制（微信侧规则），失败时如实转达错误信息。

### 调用示例

```json
{"capability":"ops.member.wx-share.short-link","input":{"pageUrl":"pages/index/index","params":"channel=points_mall","pageTitle":"积分商城"},"summary":"生成积分商城页面的微信短链"}
```

---

## ✅ 生成小程序 URL Link — ops.member.wx-share.url-link

- **微信外可用**（短信/邮件/网页直接跳转小程序）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pagePath | String | ✅ | 小程序页面路径（字段名不用 `path`：网关把 `path` 视为路由保留字段会拒绝，服务端自动映射回后端 `path`） |
| query | String | — | 页面查询参数（如 `channel=sms&pageId=456`） |
| envVersion | String | — | `release`（默认）/ `trial` / `develop`。**生产投放链接必须用 release**；trial/develop 仅限内部验证 |

### 出参（原始返回）

对象含生成的 URL Link（**`urlLink` 字段**，形如 `https://wxaurl.cn/xxx`）。URL Link 有有效期（微信侧规则），失败时如实转达错误信息。

### 调用示例

```json
{"capability":"ops.member.wx-share.url-link","input":{"pagePath":"pages/index/index","query":"channel=sms"},"summary":"生成短信投放用的小程序URL Link"}
```

---

## ⛔ 生成小程序太阳码 — ops.member.wx-share.qrcode（暂未对 Agent 开放）

> ⛔ **当前未对 Agent 开放（调用会被确定性拒绝），不要调用；用户要太阳码时，说明请到管理后台「微信分享」生成并下载，或改用短链 / URL Link。** 以下契约仅作保留，重新开放后适用。

> ⚠️ **交付规则（重新开放后适用）**：返回值是超长 base64，**不要解码、不要写文件、不要拼进命令、不要说"我帮你解码保存为图片"**——这些做法会让对话卡死超时。调用成功后只告知用户"已生成 + 页面/参数/宽度 + 对话内无法展示图片，请到管理后台微信分享下载"，然后结束回复。


- **返回 base64 data URL**（非 COS 链接，体积很大）。**禁止**把返回值拼进 shell/python 命令或自行解码落盘（命令超长会卡死超时）；当前对话没有图片通道，调用成功后直接告知用户：太阳码已生成（页面路径 + 参数 + 宽度），对话内无法展示图片，需要图片请到管理后台「微信分享」生成并下载；不要复述 base64 内容

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageUrl | String | ✅ | 小程序页面路径（**不能带参数**，参数放 params） |
| params | String | ✅ | 页面参数（≤500 字符，如 `channel=poster&inviterUid=123`） |
| pageTitle | String | — | 页面标题（业务用途记录，非微信接口参数） |
| envVersion | String | — | `release`（默认）/ `trial` / `develop`。**生产投放必须用 release** |
| width | Integer | — | 太阳码宽度 px，默认 280，范围 280~1280 |

### 出参（原始返回）

对象含 `qrcode`（base64 data URL 字符串，可直接作为 `<img src>` 使用或解码落盘）。

### 调用示例

```json
{"capability":"ops.member.wx-share.qrcode","input":{"pageUrl":"pages/index/index","params":"channel=poster","pageTitle":"积分商城"},"summary":"生成积分商城太阳码"}
```
