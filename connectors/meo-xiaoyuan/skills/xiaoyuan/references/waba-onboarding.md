# 企业自有 WABA：YCloud 开通、换号与授信

WorkBuddy 经小元服务端办理企业 WhatsApp 开通。服务端持有 YCloud 授权并将企业 Key 解析为供应商身份及 partnerCustomerId；客户端不直接调用 YCloud／Meta，不读取通道密钥，也不要求用户提供内部 ID。此流程面向企业自有号，与平台 TradeAgent 猎客号分别管理。

## 创建或复用开通链接

1. 读取本企业的当前通道绑定状态。用户仅查状态时只返回状态；已有正常绑定且用户要发消息时转 whatsapp-send.md。
2. 需要首次开通时，查询本企业 PENDING 链接；有效期内可复用。用户明确新增或更换 WABA 时创建新的开通请求，不把历史绑定误当本次选择。
3. 调用实际的开通链接工具，由服务端创建 Partner Direct Link。默认 onboardingType=WHATSAPP_BUSINESS_PLATFORM；用户明确要 Business App 时使用 WHATSAPP_BUSINESS_APP。中文 locale=zh_CN，其他语言按工具支持的 en_US、es_ES、pt_BR、id_ID、ru_RU 等值。
4. 读取真实 onboardingUrl、expiresAt 和状态；把链接私下交给本企业授权操作者。按返回的到期时间说明有效期；基线为 2 小时，但不硬编码覆盖返回值。一条链接对应一次 WABA 开通，完成前刷新重试仍可复用。
5. 操作者打开链接，按 Continue with Meta 流程选择或创建企业、WABA 和号码并完成验证。设备与耗时以实际页面要求为准，不承诺固定十分钟或只能手机操作。

## 绑定完成后的核对

由服务端接收 whatsapp.business_account.updated / PARTNER_ADDED 等绑定事件，更新企业与 WABA、发送号的映射。WorkBuddy 查询服务端状态，不轮询 YCloud，也不改本地环境文件。

CONNECTED 与 paymentMethodAttached 分开核对：绑定成功不等于授信完成。服务端确认授信与发送通道可用后，再列该 WABA 下的号码和模板。旧号与新号的模板、会话窗口不混用；用户换号后重新查询。

## 错误与恢复

- 企业身份解析失败：按 account-credit.md 核对连接器企业 Key；不按公司名编造 partnerCustomerId。
- 无绑定或 WABA_REQUIRED：进入开通流程，复用有效链接，不反复创建。
- 429：按 retryAfter／Retry-After 等待；先确认原创建结果，允许重试时只重试一次。
- locale／type 参数错误：按工具定义修正，不把技术 JSON 交给普通用户填写。
- 绑定成功但授信未完成：报告这两个状态，并给真实的下一步处理入口。
- 链接包含短期凭据，不写入公共文档、公告或日志；过期后通过服务端重新申请，不复用截图中的历史链接。
