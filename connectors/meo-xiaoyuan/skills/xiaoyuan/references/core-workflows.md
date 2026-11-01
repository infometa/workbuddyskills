# 小元数据查询与原有模板通道：完整路由

本技能是连接器「出海精灵·小元」的入口技能。能力通过 MCP 服务器 `meo-xiaoyuan`（工具前缀 `mcp__xiaoyuan__*`）提供。查询类工具只读；本文件的原有 WhatsApp 工具只发送已审核正文模板，按用户确认的范围执行。企业 WABA 丰富消息见 whatsapp-send.md，邮件见 mail.md，账户和充值见 account-credit.md。

各工具完整参数、必填组合与默认值见 `api_references.md`，按需读取，不要把整份参数表贴进回复。

## 前置检查：鉴权与连接

WorkBuddy 使用用户自填 Token 模式：用户在连接器配置表单填写 `API_KEY` 后，客户端把它注入远程 MCP 请求头 `Authorization: Bearer ${API_KEY}`。不要让用户配置环境变量，也不要在对话里索要或回显完整 Key。

获取入口：https://xyconsole.tradechina.com/key （出海精灵·小元 → Key与平台 → 复制 API Key）。

**连接异常时按以下顺序排查：**

1. 需要诊断连接时用 `xiaoyuan_ping` 探测（回显 pong 即正常）；不把 ping 或余额查询作为每次任务的前置条件。
2. 调用返回 401 / 403 / token 失效类错误时：
   - 不盲目重试，不编造数据；按响应区分 Key 失效、企业权限与通道权限。
   - 确为企业 Key 失效时，引导用户打开 WorkBuddy **连接器管理 → 出海精灵·小元 → 配置**，在「服务对接配置」中更新 API Key 后保存；通道权限问题转对应业务配置，不反复换 Key。
3. 超时 / 网络不可达：告知用户稍后重试或检查连接器是否已启用。多数工具秒级返回；`xiaoyuan_wa_unlock` 等会话锁最长可等待 90 秒，属预期慢等待，勿提前判为超时，也不要连续盲重试。
4. 参数错误 / 校验失败：按工具原文错误说明缺了什么，对照 `api_references.md` 补齐必填项后再调；禁止用猜测值硬填。
5. 工具整体不可见 / 连接器未启用时，提示用户在连接器管理中信任并启用该连接器。

## 意图路由

| 用户意图 | 工具 |
|----------|------|
| 调试连接、ping 探测 | `xiaoyuan_ping` |
| 多条件搜买家（产品词/国家/展会/预注册） | `xiaoyuan_search_buyers` |
| 按买家类型筛（先查维度 id） | `xiaoyuan_list_buyer_type` → `xiaoyuan_search_buyers`（`buyer_type_ids`） |
| 按完整公司名查买家 | `xiaoyuan_search_buyers_by_name` |
| 买家公司详情与联系人（联系人在 `cdpContactVO`；须用户明确要看联系方式再调） | `xiaoyuan_get_buyer_detail` |
| 一客一档、出口国、贸易记录 | `xiaoyuan_get_customer_file` → `xiaoyuan_get_trade_records` / `xiaoyuan_get_export_trend` |
| 搜同行、竞品展商 | `xiaoyuan_get_colleague_categories` → `xiaoyuan_search_colleagues` |
| 本企业资料、订购展信息 | `xiaoyuan_get_company_basic_info` |
| 看当前能发哪些 WhatsApp 模板 | `xiaoyuan_list_whatsapp_templates` |
| 查 WhatsApp 发送号状态 | `xiaoyuan_whatsapp_sender_info` |
| 给指定号码发 WhatsApp 模板（须先确认） | `xiaoyuan_list_whatsapp_templates` → 用户确认 → `xiaoyuan_send_whatsapp_template` |
| 会话窗口内发 WhatsApp 自由文本（须先确认） | `xiaoyuan_list_whatsapp_conversations` 看 windowOpen → 用户确认 → `xiaoyuan_send_whatsapp_text` |
| 查 WhatsApp 会话与消息流 | `xiaoyuan_list_whatsapp_conversations` → `xiaoyuan_list_conversation_messages` |
| 查单条 WhatsApp 消息发送状态 | `xiaoyuan_whatsapp_message_status`（用发送返回的 externalId） |
| HS 编码出口额 / 双边贸易数据 | `xiaoyuan_comtrade_get` |
| 关税（WITS） | `xiaoyuan_wits_tariff` |
| WTO 贸易壁垒 / SPS / TBT / 补贴通报 | `xiaoyuan_wto_eping` / `xiaoyuan_wto_qrs` / `xiaoyuan_wto_tfad` |
| 按域名 / 公司找邮箱（Hunter） | `xiaoyuan_hunter_domain_search` / `xiaoyuan_hunter_email_finder` |
| 邮箱有效性校验 | `xiaoyuan_hunter_email_verifier` |
| 按人名 / 公司找人（Hunter） | `xiaoyuan_hunter_people_find` / `xiaoyuan_hunter_companies_find` |
| 发现相似公司 | `xiaoyuan_hunter_discover` |
| 海外企业画像（AroundDeal） | `xiaoyuan_arounddeal_list_enums` → `xiaoyuan_arounddeal_enrich_company` / `xiaoyuan_arounddeal_search_companies` / `xiaoyuan_arounddeal_company_intel` |
| 海外决策人画像（AroundDeal） | `xiaoyuan_arounddeal_search_people` / `xiaoyuan_arounddeal_enrich_person` |
| 付费找联系方式（AroundDeal，按条计费） | `xiaoyuan_arounddeal_find_contacts` / `xiaoyuan_arounddeal_search_sourcing_contacts` / `xiaoyuan_arounddeal_search_brand_contacts` |
| 联系人校验 / LinkedIn 关联 | `xiaoyuan_arounddeal_verify_contact` / `xiaoyuan_arounddeal_email_to_linkedin` / `xiaoyuan_arounddeal_check_relationship` |
| 查询人物履历（resume enrichment） | `xiaoyuan_arounddeal_resume_enrichment` |

## 典型调用与返回

调用示例（搜德国咖啡机买家）：

```json
{
  "tag_keyword": "coffee machine",
  "countries": ["DE"],
  "page_num": 1,
  "page_size": 20
}
```

返回优先读 `response.data`：列表为 `page.records`，另看 `hasNext` / `backendParam`；翻页必须同时把 `page_num` 改为目标页，并把上一轮 `data.backendParam` 原样回传为 `backend_param`。只改其中一个不生效。详情用列表项里的 `companyCdpId`（仅工具间流转，不要展示给用户），联系人读详情返回的 `cdpContactVO`。

## 推荐链式调用

```
搜买家(search_buyers) → 详情(get_buyer_detail，联系人在 cdpContactVO)
联系人缺邮箱 → AroundDeal find_contacts 或 Hunter email_finder
搜同行(get_colleague_categories → search_colleagues) → 同行买家 → search_buyers
市场研究：comtrade_get → wits_tariff → wto_*（生成报告/选品决策）
一客一档：get_customer_file → get_trade_records / get_export_trend
WhatsApp：sender_info 确认发送号可用 → list_whatsapp_templates → 向用户确认收件号、模板和变量 → send_whatsapp_template；窗口内自由文本：conversations 看 windowOpen → 确认 → send_whatsapp_text；结果未知按 externalId 查 message_status
```

## WhatsApp 直发（企业发送号）

发送号是本企业绑定的 WhatsApp 号（`xiaoyuan_whatsapp_sender_info` 查状态；40401=未配置联系运营、40402=未接入 YCloud）。只发该号能发的正文模板，不自拟模板、不选发送号。图文头、轮播、动态按钮模板不会出现在列表里，也不要尝试发送。

1. 先调 `xiaoyuan_list_whatsapp_templates`（无参数）。每条用 `templateName`、`language`、`bodyText`、`bodyParamNames` 向用户说明能发什么；同名多语言各算一条。
2. 让用户选定模板，并补齐收件 WhatsApp 号码和正文变量。变量按 `bodyParamNames` 的顺序对位填写（`{{1}}` 序号式与 `{{name}}` 具名式均按位），个数必须等于 `bodyParamCount`；没有变量就不要传。
3. 发送前用可读信息向用户确认：收件号、模板、把变量填进正文后的完整文案。用户明确同意后再调 `xiaoyuan_send_whatsapp_template`。未确认不要发，也不要为了试通而发。
4. 调用参数：`to`（可带或不带 `+`）、`template_name`（须来自列表）、同名多语言时必填的 `language`、`body_parameters`（字符串数组，顺序对位 `bodyParamNames`）。
5. 成功时告诉用户已受理，并记录返回的 `externalId`；受理≠送达，结果未知或需确认送达时用 `xiaoyuan_whatsapp_message_status` 查状态，不盲目重发。重复调用会再发一条，不要把失败重试做成连续重发。列表里没有的模板不要编造。
6. 会话窗口内（`xiaoyuan_list_whatsapp_conversations` 的 `windowOpen=true`）可经用户确认后调 `xiaoyuan_send_whatsapp_text` 发自由文本；窗口外的拦截多为上游异步（状态查得 FAILED+131047，少数同步返回 40901），都改走模板。完整流程、会话与回执见 `references/whatsapp-send.md`。

## 核心规范

### 响应解析

- 报错时准确说明业务原因及未完成动作，保留排障所需错误码，但隐藏密钥和内部敏感标识；**禁止编造数据**，无来源的信息标「待确认」。
- 同行搜索用 `xiaoyuan_search_colleagues` 的 `search_type`（1 无结果再试 2）；勿混用其他工具的 tagId。
- 搜买家翻页须同时改 `page_num` 并透传 `backend_param`；产品词优先 `tag_keyword`（英文），无结果再 `profile_keyword`。
- 本届展会买家须核对 `preExhibitionIds` 含目标展会 ID；预注册买家 `features` 含 21，到展买家含 5。

### 付费与敏感操作

- **WhatsApp 发送会真实触达收件人**：模板必须先 `xiaoyuan_list_whatsapp_templates`，把收件号、模板和填好的正文给用户确认后才能调 `xiaoyuan_send_whatsapp_template`；自由文本必须先确认窗口（`windowOpen`）并把收件号与文案给用户确认后才能调 `xiaoyuan_send_whatsapp_text`。
- **AroundDeal `find_contacts` / `search_sourcing_contacts` / `search_brand_contacts` 按条计费**：`limit` ≤ 5，调用前必须向用户确认。
- 原工具文档将 Hunter `email_finder` 标为找不到不扣费；调用时仍以当前企业计费规则和回执为准。
- 买家详情的 `cdpContactVO` 涉及联系方式，须用户明确要看联系方式后再调 `xiaoyuan_get_buyer_detail`。
- 展示联系人信息时仅输出职位、邮箱、电话等业务字段。

### 输出约束

- 内部 ID 类字段（`companyCdpId`、内部租户／数据标识、cursor 等）仅在工具间流转，不在普通用户回复中暴露；任务编号和邮件回执编号可用于用户追踪；对外一律使用公司名、职位、国家等可读信息，多候选时用序号 + 可读信息构造列表。
- 列表结果默认摘要（公司 + 关键标签 + 国家）；用户下钻时再展开单家公司详情。
