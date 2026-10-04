# 授权与恢复

本包的 canonical `mcp.json` 指向 `https://api2.u3w.com/fbs-mcp/mcp`。2026-09-23 该资源的 OAuth protected-resource metadata 指向 `cjddh920-preview` 授权服务器；独立审核预览画像资源仍是另一 URL，不能把两者授权或服务准入互相代用。实际可调用能力按[能力门](capability-routing.md)及本轮工具、scope、准入回执确定。WorkBuddy宿主处理OAuth发现、浏览器授权与刷新；模型不接收、抄写或持久化授权码、Token、Cookie、密码或client_secret，不启动本地OAuth守护进程，也不跨资源透传用户Bearer。

服务端必须从经验证且面向本资源的授权确定账户；模型不得填写 `subject_id` 或任意 userId 替代认证。MCP session、匿名绑定、昵称、静态请求头和产品 ID 均不能证明本人账号，不自动合并旧匿名记录。平台第三方应用授权与福帮手会员 OAuth 分属不同授权，不互传令牌。

缺工具时分别核对：未连接/未就绪、未授权、本轮未暴露、服务未实现。仅宿主支持时允许一次有界只读重新发现；仍缺失即停止自动重试。不要从一个缺失名字断言整个平台没有能力。授权取消不循环弹窗；刷新失败/撤销时引导用户重新连接，不降级为匿名读取私有资料。若宿主呈现 `invalid_token`，按[原生时序](native-oauth-sequence.md)核对事件顺序，先核对受保护工具的原始 HTTP 401 challenge、资源元数据和授权服务器发现阶段；匿名 `initialize/tools/list` 的 200 与 UI“已连接”不证明有可用 Bearer。授权服务器元数据拒绝或回退路径返回非 JSON 时，停止同一工具重试并转交连接器/服务维护者处理。

OAuth只确认本次福帮手账号授权，不等于自然人实名。画像用途、逐项事实确认、企业权限、费用和外部联系分别批准；用户拒绝画像不取消原有权益。新资源的PROFILE_CONSENT_REQUIRED是用途未同意，不是OAuth scope不足，不循环重新登录或扩大scope。

同一grant的未决MCP操作先按原operationId查询profile_operation_receipt；刷新令牌不能换业务号。不同grant需要新的服务contextRef和独立用途同意；当前未实现跨grant恢复授权工具，不能读旧grant回执或继承其写批准。需要核对旧操作时给本人网页入口，不生成新号重做。

网页确认、纠正、撤回与MCP授权分开。单客户端解绑不删除本人事实；其他有同用途有效同意的客户端可继续。用途撤回覆盖本人同上下文/用途的各grant，重新同意不复活旧值。本人仍可登录网页纠正或撤回；当前无hard-delete/导出实现，不承诺这些流程。
