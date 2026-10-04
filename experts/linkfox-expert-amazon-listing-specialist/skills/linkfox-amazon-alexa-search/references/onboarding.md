# 解决认证和积分问题

调用本 skill 时若网关返回 **auth** 或 **billing** 错误，走本 skill 自带的 `scripts/onboarding.py` 完成引导。

**auth 场景**：`errcode=401` 或消息含 `authorized error`/`鉴权失败`/`未授权`/`unauthorized`；或 `LINKFOX_AGENT_API_KEY` 与 `LINKFOXAGENT_API_KEY` 均为空。
1. 若已配置 key → 先让用户重启会话（最常见误判），仍失败让用户重新取 key 或换手机号重注册
2. 未配置 → 询问：自助去 https://agent.linkfox.com/ 取 key，或提供手机号让脚本注册
3. 手机号路径：
   - `python scripts/onboarding.py send-code <phone>` → 展示 JSON 里的 phone/agreements
   - 收到验证码后：`python scripts/onboarding.py login <phone> <code> --channel workbuddy`（注意：--channel workbuddy 是**必须**的）
   - 拿到 `api_key` 后把下面三平台配置转发给用户，提示重启会话生效：
     - Windows PowerShell（永久）：`setx LINKFOX_AGENT_API_KEY "<key>"`
     - macOS zsh：`echo 'export LINKFOX_AGENT_API_KEY="<key>"' >> ~/.zshrc && source ~/.zshrc`
     - Linux bash：`echo 'export LINKFOX_AGENT_API_KEY="<key>"' >> ~/.bashrc && source ~/.bashrc`
     - 变量名 `LINKFOX_AGENT_API_KEY`（主推）或 `LINKFOXAGENT_API_KEY`（老规范）任一即可

**billing 场景**：`errcode=402` 或消息含 `积分/余额/quota/insufficient/充值/套餐到期`。
- `python scripts/onboarding.py list-plans` → 有 AskUserQuestion 就弹菜单，否则输出编号清单让用户选
- 校验 `plan_id` ∈ 清单、支付方式 ∈ 该套餐 `available_methods`（通常 `wechat/alipay`）
- `python scripts/onboarding.py order <plan_id> <method>` → 展示优先级 PNG > `pay_url` > `ascii_qr`（标注兜底）
- 已付款可选调 `python scripts/onboarding.py query <order_id>`，不主动轮询

排除 `errcode=403`（无权限，不归入这两类）。所有子命令输出 stdout JSON，`error` 字段已含阶段前缀，透传给用户即可。完整用法：`python scripts/onboarding.py --help`。

