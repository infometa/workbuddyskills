---
name: market-expert-gateway
description: 通过腾讯汽车行业营销网关（Market Expert Gateway）完成真实 CDP 人群圈选/预估/创建/拆包/导出、PA 三方洞察、企微客户群发、短信触达、内容中心检索生成与分发、落地页、公众号阅读数据与舆情查询。用户提到圈人群、人群预估、PA 画像、企微群发、发短信、生成/分发文章、落地页、阅读数据、舆情时使用。
---

# 腾讯汽车行业营销网关（Market Expert Gateway）

本 Skill 配合 `market-expert-gateway` MCP Server（streamableHttp，MCP OAuth 2.1 / VCam 登录模式）使用。所有工具均由网关代理真实业务系统，凭证与 access_token 始终由 WorkBuddy 与后端管理。

连接入口 `https://iautomark.sdm.qq.com/market-expert/mcp` 已内置在 `mcp.json` 中（云原生网关 HTTPS 域名）。首次连接时 WorkBuddy 会打开浏览器跳转 VCam 登录，登录完成后自动保存并刷新令牌，用户无需填写任何令牌或地址。若网关迁移，只需修改 `mcp.json` 的 `url`。

- 未登录或登录已失效时返回 `401`，应提示用户在连接器中重新连接（重新走 VCam 登录），不要重试，也不要索要令牌。
- 网关为无状态 Streamable HTTP：`initialize` 直接返回 JSON、不下发 session id，调用工具时无需回传会话头。

## 通用规则

- 所有 `start_*` / `prepare_*` 只做预估或预览，不产生写副作用；所有 `confirm_*` / `distribute_*` 会产生真实写操作，**必须先向用户展示预览并获得明确确认**后再调用，且只使用 prepare/estimate 返回的一次性 `confirmation_token`。
- 返回 `running` / `preparing` 时按 `retry_after_seconds` 串行轮询对应 `get_*_status`，不得把运行中当作完成，也不得重复提交 confirm。
- 结果未知（超时、网络错误）时先查状态，不要重试 confirm。
- 不在对话、日志或画布中输出 Token、`qrToken`、`package_code`、手机号明文、腾讯云模板/签名 ID。

## 工具分组

### 1. CDP 人群
| 工具 | 说明 |
|---|---|
| `get_audience_rules` | 每个新圈选任务必须先调用，获取治理规则 |
| `search_audience_metadata` | 检索属性、标签、客户身份候选（条件必须落地到真实元数据） |
| `start_audience_estimate` → `get_audience_status` | 校验 AudiencePlan 并预估人数，不创建 |
| `confirm_audience_creation` | 用户看过预估并确认后创建人群（拆包时为每个子包创建） |
| `start_audience_split` / `start_audience_exclude` | 对已创建人群拆包预估 / 子包互斥排重 |
| `start_audience_portrait` → `get_audience_portrait_status` | 一方画像分析 |
| `start_audience_export` → `get_audience_export_status` | 导出分群，`identifiers` 只能是 `external_userid` 或 `phone` 之一 |
| `list_audience_export_external_userids` / `list_audience_export_phones` | 分页读取导出结果（手机号固定脱敏） |

### 2. PA 三方洞察（人群创建成功后）
`get_pa_crowd_intake_options` → `prepare_pa_crowd_intake` → **确认** → `confirm_pa_crowd_intake` → `get_pa_crowd_intake_status` → `get_pa_insight_tag_catalog` → **确认标签与积分** → `confirm_pa_insight_tags` → `start_pa_portrait_insight` → `get_pa_portrait_insight_status` → `get_pa_portrait_insight_result`。标签最多 25 个，且必须来自真实目录。

### 3. 企业微信客户群发
- 查询：`list_wecom_customers`、`get_wecom_customer`
- 发送：`prepare_wecom_customer_mass_send` → **确认** → `confirm_wecom_customer_mass_send`（成员仍需在企微客户端确认发送）
- 结果：`get_wecom_groupmsg_tasks`、`get_wecom_groupmsg_send_results`、`get_wecom_execution_summary`

### 4. 短信触达（会产生费用）
`list_sms_templates` → `prepare_sms_campaign_send`（服务端内部取号，不返回手机号）→ `get_sms_campaign_status` → **确认** → `confirm_sms_campaign_send` → `get_sms_delivery_summary`。参数须按模板 `parameter_names` 精确提供；`UNKNOWN` 不自动重发。

### 5. 内容中心
- 检索：`search_content_articles_by_title`、`search_content_materials`、`search_content_vehicles`、`get_content_vehicle_images`、`get_content_vehicle_detail`、`compare_content_vehicles`
- 生成与审核：`generate_content_article`（较慢；含 `${...}` 未渲染占位符不可发布）、`review_content_article`、`adapt_content_article`
- 账号扫码：`start_content_platform_qrcode_login` → `get_content_platform_qrcode_login_status` → `confirm_content_platform_qrcode_login`
- 分发：**确认后** `distribute_content_article`（需真实 `accountId`）→ `get_published_content_article`；微信扫码用 `get_content_publish_scan_status` / `confirm_content_publish_scan`
- 公众号数据：`register_wechat_publish_task`（仅发布成功后登记）→ `get_content_publish_analytics`
- AI 回复评测：`start_content_reply_evaluation` → `get_content_reply_evaluation`（间隔 ≥ 30 秒）

### 6. 落地页
`upload_landing_image` / `create_landing_image_upload_ticket` / `import_landing_source_image` → `create_landing_page`（同 requestId 幂等）→ `list_landing_pages`、`get_landing_page_stats`

### 7. 舆情（只读）
`get_public_opinion_context`：按品牌 / 车系 / 车型 / 事件或 `topic_id` 获取高频问题、负面信号与文章覆盖；找不到 TOPIC 时只给创建建议。

## 典型流程

1. 圈人群：`get_audience_rules` → `search_audience_metadata` → `start_audience_estimate` → 轮询 → 展示预估 → 用户确认 → `confirm_audience_creation`。
2. 企微触达：人群创建 → `start_audience_export`（`external_userid`）→ 轮询 → 生成文案 → `prepare_wecom_customer_mass_send` → 用户确认 → `confirm_wecom_customer_mass_send`。
3. 短信触达：人群创建 → `list_sms_templates` → `prepare_sms_campaign_send` → 展示脱敏预览与条数 → 用户确认 → `confirm_sms_campaign_send` → `get_sms_delivery_summary`。
