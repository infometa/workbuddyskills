---
name: moka-policies
display_name: Moka 政策制度
display_name_en: Moka Policies
description: 企业政策制度的搜索、阅读与送达跟踪。员工按关键词搜索制度文档并读取正文全文与附件，基于原文回答制度问题；制度管理员查某份制度的历史推送记录与已读未读情况。当用户问「年假要提前多久申请」「报销制度是什么」或「这份制度推送过几次、还有多少人未读」时使用。
description_zh: 面向两类用户的企业制度能力。全体员工：按关键词搜索政策制度文档库（员工手册、规章制度、办事指南等），读取文档正文全文与附件，严格基于原文回答制度咨询。制度管理员（人事）：查某份制度文档的历史推送记录——推送时间、操作人、推送状态与已读/未读人数。当用户问「年假要提前多久申请」「报销制度怎么规定的」（员工），或「这份制度以前推送过几次」「上次推送还有多少人未读」（管理员）时使用。
description_en: "Company policy capabilities for two audiences. All employees: search the policy document library (employee handbook, rules, how-to guides) by keyword, read a document's full text and attachments, and answer policy questions strictly from the original text. Policy administrators (HR): check a document's delivery history — push time, operator, status, and read/unread counts. Use for questions like \"how far in advance must annual leave be requested\" (employee) or \"how many times has this policy been pushed and who hasn't read it\" (admin)."
category: productivity
version: 1.0.0
author: Moka
---

# 制度

帮员工找到制度依据、帮制度管理员跟踪送达情况。只编排以下两个工具：

- `mcp__moka__search_policy_documents`
- `mcp__moka__get_policy_delivery_records`

## 员工查制度（全体员工）

制度咨询走固定的两段式：

1. **先搜索**：用 `mcp__moka__search_policy_documents` 按 keyword 在文档标题与正文中检索；keyword 留空则按更新时间浏览全部可见文档。
2. **再读全文**：把搜索结果里的 documentId 回传同一工具，读取该文档的正文全文与附件清单，然后严格基于原文作答，回答时说明依据的是哪篇制度。

检索要点：

- 搜索是精确子串匹配，不是语义搜索：同义词不会自动扩展，建议用更短、更通用的关键词多试几次（如搜「年假」而非「年休假申请提前期」）。
- 搜索结果的摘要片段只是匹配位置的上下文或正文开头节选，不是全文，不能只凭片段回答；回答前必须读全文。
- keyword 与 documentId 二选一，不能同传。
- 返回条数等于每页条数时可能还有下一页，需要完整清单就翻页；结果按置顶优先、更新时间倒序排列。

作答要点：

- 正文是从富文本提取的纯文本，表格与图片内容会丢失；正文明显不完整时，提示用户到 Moka「政策制度」页面查看原文档。
- 附件里的文字工具读不到：正文没有答案而文档带附件时，把附件名与下载地址给用户自行打开，不要猜测或转述附件内容。
- 附件下载地址有时效，过期后重新调用工具获取新地址即可。
- 换关键词重试仍无命中，或正文未提及所问事项时，如实告知制度库中没有找到相关规定，**绝不能**基于常识编造或补全企业制度。

## 人事查送达（制度管理员）

面向负责制度管理的用户，回答「这份制度推送得怎么样」：

- 用 `mcp__moka__get_policy_delivery_records` 按 policyId 查一份制度文档的历史推送记录：每次推送的时间、执行推送的操作人、推送状态，以及已读与未读人数。
- policyId 与 `mcp__moka__search_policy_documents` 返回的 documentId 指向同一制度文档：用户只给出制度名称时，先用 `mcp__moka__search_policy_documents` 搜索定位到目标文档，再查其送达记录。
- 最多返回 50 条推送记录并标明是否截断；截断时按返回口径汇报，不要把已返回条数说成全部。
- 该能力需要制度管理功能权限，普通员工调用会被明确拒绝，如实转述。
- 只读且只到人数层面：不支持发起推送、催读、编辑制度，也查不到「具体谁已读谁未读」的名单；用户要这些操作时，说明需到 Moka 管理端完成。

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展同义词或追加筛选条件。
3. documentId / policyId 只用工具返回的值，不猜测编造。
4. 制度问题默认走完两段式再作答：搜索命中多篇时，优先读与问题最相关的一两篇，并说明你做了取舍。
5. 用户问「休年假合不合规」这类组合问题时，制度原文由本技能取证，用户自己的余额与考勤数据交给对应能力，不要用制度推断个人数据。
6. 读取全文会计入员工本人的「最近浏览」记录（与本人在页面查看一致），属正常行为，无需额外提示。

## 结果与权限

- 搜索只返回当前员工有权查看的已发布文档：结果为空表示可见范围内没有匹配文档，按「未返回数据」处理，不得反推为无权限。
- 结果自带的 notices 说明匹配机制、正文提取局限与不编造约束，组织回答前先读，与结论相关的提醒如实转达。
- 制度有时效：结果带最近修改时间，回答时可提示用户以最新版本为准。
- 送达记录的推送状态以返回文本为准，不要自行归类或翻译成其他状态说法。
- 送达记录为空表示该制度当前没有可返回的历史推送记录，不解释为制度不存在或无权限。
- 工具返回的拒绝或提示 message 如实转达，不自行改写归因。

## 安全边界

- 员工侧数据面是本人可见的制度文档；管理员侧数据面是其有权管理的制度送达记录，两者都只读。
- 附件下载地址在有效期内无需再登录即可打开：只发给用户本人，提醒不要长期保存或转发到公开渠道。
- 不向用户展示访问令牌、内部标识符或原始技术响应。
- 不虚构工具未返回的制度内容、推送记录或人数；制度里没写的，就说没有相关规定。
- 面向用户只用业务语言，不引用参数名、字段名或状态码。
- 出现未登录或授权失效时，提示用户重新连接 Moka 连接器后重试。
