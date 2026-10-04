# 原生授权时序与恢复

按本轮实际发生顺序区分：连接请求 → 工具发现/401 challenge → 授权 action_required → 宿主打开授权页 → 本人同意 → 服务准备回调 → 宿主接收回调 → 宿主保存令牌 → 受保护工具真实成功。浏览器先开、HTTP200、UI“已连接”、18个工具名或回调网页各只证明自己所在的阶段。

workbuddy:// 是宿主私有回调入口；http://127.0.0.1:<临时端口>/oauth/callback 是宿主本地监听回调。两者均以本次动态注册、redirect_uri 和宿主日志为准，不手工互换。127.0.0.1 页面显示“可以关闭此页面，回到 WorkBuddy 继续”可以是原生 loopback 回调正常结束，仍不能单独证明令牌保存或业务调用成功。模型不解析/复制地址中的 code/state，不运行自建 OAuth 脚本，不代填认证。

2026-09-24 独立 custom-mcp 客户端曾在私有 URI 被拒后走原生 loopback，取得回调/令牌保存/18工具就绪证据；client/source 不同，不能代替官方 fbs-connector 授权证明。原官方来源必须单列同 source 的完整时序及真实受保护调用。

遇 invalid_token，先区分匿名目录就绪与实际账号授权；核对脱敏 challenge、资源元数据、issuer、宿主 actionRequired/openExternal、回调接收和令牌保存。不反复调用业务工具驱动登录。用户已表达重连意愿时沿宿主正常流程有界恢复；解绑撤销既有连接，应遵循用户明确授权和宿主人工确认要求。

同意后报“授权确认页失效”时，不沿用旧页重复提交。维护者应比对全链最终响应头、POST Origin 和安全拒绝类别；曾出现应用 strict-origin 被 Nginx 追加 no-referrer 覆盖，导致真实表单 Origin:null。修复应删除授权路由上的重复冲突头，不能放宽 Origin/CSRF 校验；本说明不授权技能改服务或绕过认证。

只做一次本轮恢复，仍失败就保留阶段、UTC 窗口和安全诊断编号交维护者。浏览器、CLI、宿主可能不同出口，不能用 CLI 成功替代 WorkBuddy 可达；无动作证据保持 not_observed，不按旧推理补出中间事件。
