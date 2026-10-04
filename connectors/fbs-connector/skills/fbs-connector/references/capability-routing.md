# 按真实工具与授权选择能力

账号核对与画像任务的首跳是 `member_whoami`（及 `fbs_capabilities`），不是 `skill_whoami`。旧目录中的“固定首工具”“同绑定旅程”仅适用于旧场景/进度请求，不得覆盖账号路径。当前已加载专家四字段从其包清单或随包 Agent 声明读取，不能从匿名 whoami 返回的缺失值反推本包未知，也不能省略字段绕过准入。

默认资源是 `https://api2.u3w.com/fbs-mcp/mcp`。同一 URL 同时承载旧业务工具与七个受 OAuth 保护的账号/画像工具，不能因地址未变就把画像统一标成 guidance_only。调用前以本轮宿主实际工具、输入 schema、连接器版本准入和授权为准；静态合同只用于核对。机器投影见[能力合同](capability-contract.json)，完整身份约定见[身份合同](../../fbs-mainline/references/identity-contract.json)。

2026-09-23 无凭据目录曾观察到 18 个原始名称：旧 11 工具加新 7 工具。原始目录中的 lebao_drop 仍由本包 policy 禁用，不能调用；不把 18 推算为宿主过滤后有 18 个可用工具，更不等于 18 个都已授权。服务能力、宿主可见、账号授权、用途同意和事实确认分别记录。

本候选本地版本是 package 2026.9.25-r7 / contract 1.3.0；它没有服务准入证明。前驱 package 2026.9.24 的首个只读目录核验曾返回 HTTP 426 / -32042；该历史拒绝与准入均不替代本候选的当前回执。遇拒绝停止调用，不能改为 2026.9.20、2026.9.10 或 26.8.20 冒充旧版，也不能删来源头绕过。

| 工具面 | 使用条件 | 不能据此推导 |
|---|---|---|
| skill_whoami、fbs_scene_pack_query、skill_consume 及原会话/乐包工具 | 当前目录/schema、旧 action envelope 与各技能前置均通过 | 会员账号认证、会员扣费、个人画像同意 |
| member_whoami、fbs_capabilities | 当前 canonical audience 的 OAuth + account:read | 会员权益/实名；无需强制先走旧场景链 |
| profile_status | OAuth + account:read + 完整真实专家四元组 | 已获用途同意；状态接口不返回事实值 |
| profile_read | OAuth + profile:read + 完整四元组 + 当前有效 contextRef/用途 | 自动确认事实、完整阅读或模型采用 |
| profile_propose | OAuth + profile:propose + 有效用途 + 用户本次愿意提出该项 | 本人已确认事实、已收费或已成交 |
| profile_manage_entry | OAuth + profile:manage + 完整四元组 + 用户选择用途 | 同意用途；它创建待同意元数据并返回本人页面 |
| profile_operation_receipt | OAuth + profile:manage + 完整四元组 + 原 operationId | 别的 grant 或网页操作回执；宿主已收到结果 |

当前服务器存在 synthetic 与 consented-account 两种账号访问政策；实际政策由服务决定。不能把历史合成账号白名单强加给当前普通账号，也不能仅凭账号 NORMAL 绕过画像总开关、授权代次、用途或产品元组准入。fbs_capabilities 是准确名称，不能造 member_capabilities。

账号级 member_whoami/fbs_capabilities 可在确无专家上下文时使用空参数对象；已知专家不得故意删四字段绕过准入。五个 profile 工具要求 productId、packageName、expertEntryId、packageVersion 全部来自实际加载包。当前源码快照包含研究员 26.9.14，但后继专家版本必须等自己的准入回执，不能冒充 26.9.14。knownExpertTuples 是产品目录，不是任何版本已获准的证明。

会员权益、积分、结算、需求 CRUD、组织/企业及服务目录 MCP 工具当前未在这七工具面开放；会员系统网页/API 的实现不等于模型可以代调。member_check_entitlement、member_credit_status、member_service_receipt、member_settle_service、member_case_*、member_request_*、member_enterprise_* 不做替代调用。需求通过已核实的本人网页处理，尊重其说明、提交、回复、撤回和联系许可。

历史 172a425 指的是 `/cjddh920-preview/fbs-mcp/oauth/mcp` 的独立预览，不是默认 canonical 的当前能力依据。它的三产品版本白名单、合成上游 core3 和“新 7 + core3 = 10”仅保留在 identity-contract 的 historicalPreviewGateway。不得把预览令牌、contextRef、grant、旧信封或其验收结论套给 canonical。技能不改 URL，不手工透传 Bearer。

画像参数/确认规则见[画像协议](../../fbs-profile/references/profile-purpose-and-provenance.md)。缺任一前置就说明对应缺口，并按当前专家原产品合同继续允许的首值；不让可选画像阻断本地交付，不覆盖专家已有的专用授权前置。
