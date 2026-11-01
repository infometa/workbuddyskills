# WhatsApp 发送：企业发送号、正文模板与会话窗口

先识别用户所用通道。本文件覆盖的是经小元 MCP 的 WhatsApp 直发域工具：发送号是**本企业绑定的 WhatsApp 号**（运营在平台侧为企业绑定后生效），模板与自由文本都从这个号发出。AI 猎客的任务化平台号发送见 ai-hunter.md，邮件见 mail.md。

## 发送号状态（先查再发）

1. 首次发信或发送失败时先调 `xiaoyuan_whatsapp_sender_info`（无参数），读 `senderNumber`、`wabaId`、`phoneStatus`。
2. 失败码 40401=发送号未配置：告诉用户需联系运营开通，不要重试发送；40402=号码未接入 YCloud：指引先完成 WABA 接入（见 waba-onboarding.md）。查询成功（无 40401/40402）即号码可用，可继续发送。
3. 不向用户索取发送号或 WABA 参数，不自选号码；发送号由服务端按企业绑定解析。

## 模板发送（窗口外唯一通道）

1. `xiaoyuan_list_whatsapp_templates` 无参数，返回本企业发送号能发的已审核正文模板（发送号 WABA 域内，列表可见即可发）。读取 templateName、language、category、bodyText、bodyParamNames（正文占位符名，按出现顺序，含 {{name}} 具名式）；同名多语言分别处理。
2. 根据用户意图选模板；已有真实资料的变量自动回填，缺少的信息一次询问。发送前让用户核对收件号、模板和填好后的完整正文；已明确授权的范围不反复确认。
3. `xiaoyuan_send_whatsapp_template` 接收 to、template_name、language、body_parameters。template_name 与 language 必须来自列表返回值。变量为字符串数组，严格按 bodyParamNames 顺序对位（{{1}} 序号式与 {{name}} 具名式均按位填充），数量等于 bodyParamCount；无变量不传。
4. 只发列表里的正文模板，不发图文头、轮播或动态按钮模板；需要这些类型时如实说明本通道不支持。
5. 发送成功返回 externalId（agwa: 前缀）——后续查状态就用它。受理（accepted）≠送达，向用户报告时说明已受理、送达以状态查询为准。

## 自由文本发送（仅 24h 会话窗口内）

1. 先调 `xiaoyuan_list_whatsapp_conversations` 找到对端会话，读 `windowOpen`：true 表示最近买家入站<24h，可发自由文本。
2. windowOpen=false 或无会话记录时，直接走上面的模板通道，不要发文本。
3. `xiaoyuan_send_whatsapp_text` 接收 to、text。会真实发给收件人，重复调用会再发一条；发送前让用户核对收件号与文案。
4. **受理≠送达**：窗口外的文本发送不会被同步拦截，仍返回受理成功，随后被 WhatsApp 上游异步拒绝（错误码如 131047）——发送文本后必须按 externalId 查 `xiaoyuan_whatsapp_message_status` 确认终态，FAILED 且错误含 24 hours/window 字样即窗口拦截，改走模板通道。仅 YCloud 同步拒绝时才直接返回 40901。

## 消息状态与回执（externalId 落点）

1. 发送工具返回 externalId 后，用 `xiaoyuan_whatsapp_message_status`（参数 external_id）查询状态：ACCEPTED/SENT/DELIVERED/READ/FAILED，含各时间戳与失败原因。非终态时服务端会自动向 YCloud 刷新。
2. 「结果未知」的处理落点就是本工具：发送后未收到明确结果时，先按 externalId 查状态，避免盲目重发。
3. 同一请求重复调用发送工具可能重复发信；不要把失败重试做成连续重发。

## 会话与消息流

1. `xiaoyuan_list_whatsapp_conversations`（参数 cursor、limit）列本企业全部会话：contactMobile、lastMessageSnippet、lastMessageAt、lastDirection、windowOpen、unreadCount。
2. `xiaoyuan_list_conversation_messages`（参数 contact_mobile，翻页 cursor、limit）查单个会话双向消息流；调用即把该会话入站消息置已读。
3. `xiaoyuan_list_whatsapp_messages`（参数 to、status、cursor、limit）按条件查消息记录，适合核对发送历史。
4. 买家回信的关联处理与回复规范见 replies.md；发送后要持续等回信时，按 replies.md 的定时回查注册周期回查，新回信到达时提醒用户。

## 错误分支

40401=发送号未配置（联系运营开通）；40402=号码未接入 YCloud（先完成 WABA 接入）；40901=窗口外发自由文本被 YCloud 同步拒绝（改用模板；注意多数窗口拦截是上游异步的，形态为状态查询见 FAILED+131047，不返回 40901）；50901=发送失败（读失败信息，修完再发，不连续重发）；40001=参数非法（按提示修正）。已受理的发送不因后续查询超时再次发送。
