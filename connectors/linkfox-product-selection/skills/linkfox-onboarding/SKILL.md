---
name: linkfox-onboarding
description: LinkFox 账号与环境引导。两个入口：(1) 检测到 LINKFOX_AGENT_API_KEY/LINKFOXAGENT_API_KEY 均未配置，或任何 linkfox-* skill 返回 errcode=401/authorized error 时，引导用户配置 key——支持脚本化注册（手机号→验证码→自动获取 key）；(2) 任何 linkfox-* skill 返回计费不足错误（errcode=402 或消息含"积分余额不足/计费不足/余额不足/quota exceeded/insufficient balance/套餐到期/需充值/请充值"）时，触发充值流程：列套餐 → 用户选套餐（校验）→ 选支付方式（微信/支付宝，校验）→ 调下单接口生成支付二维码 → 三路展示（PNG/链接/ASCII）→ 可选查询订单状态。用户说"没配 key""鉴权失败""积分不足""余额不足""充值""recharge""升级套餐""注册""手机号注册"时触发。
---

# LinkFox 账号与环境引导

承接两类引导场景：

1. **缺 Key / 鉴权失败**：未配置 `LINKFOX_AGENT_API_KEY`，或任何 linkfox-* skill 返回 `errcode=401` / `authorized error` → 引导用户配置 key（支持脚本化注册）。
2. **计费不足**：任何 linkfox-* skill 返回计费不足错误 → 充值流程（套餐 → 支付方式 → 二维码）。

## 触发关键字清单（大小写不敏感）

判定为"缺 Key / 鉴权失败"的条件（满足任一）：

- `errcode = 401`
- 错误消息含 `authorized error`、`鉴权失败`、`未授权`、`unauthorized`
- 环境变量 `LINKFOX_AGENT_API_KEY` 与 `LINKFOXAGENT_API_KEY` **均**为空

> 注：本 skill 同时兼容两种 key 环境变量名——`LINKFOX_AGENT_API_KEY`（带下划线，主推）与 `LINKFOXAGENT_API_KEY`（无下划线，老客户常用）。其它 linkfox-* skill（如 linkfox-amazon-search）也遵循同一约定，同一个 key 在两个网关都能用。

判定为"计费不足"的条件（满足任一）：

- `errcode = 402`（后端约定，实测返回 `{"errcode": 402, "errmsg": "积分余额不足，请充值"}`）
- 错误消息命中以下关键字之一：`积分余额不足`、`计费不足`、`余额不足`、`quota exceeded`、`insufficient balance`、`套餐到期`、`需充值`、`请充值`

排除：`errcode = 403`（无权限，不归入这两类）。

## 入口 1：缺 Key / 鉴权失败引导

### 步骤 1：检测环境变量

用 Bash 执行一行检测（Claude Code 自带 bash 环境，三平台通用）：
```bash
[ -n "$LINKFOX_AGENT_API_KEY$LINKFOXAGENT_API_KEY" ] && echo ok || echo missing
```

> 两种变量名都兼容：`LINKFOX_AGENT_API_KEY`（带下划线，主推）与 `LINKFOXAGENT_API_KEY`（无下划线，老客户常用）。任一非空即视为已配置。

### 步骤 2：分流

**情况 A：环境变量存在（鉴权失败场景）**

先排除"刚配置完没重启"的情况——这是最常见的 401 误判来源。话术：

> 检测到已配置 LINKFOX_AGENT_API_KEY 或 LINKFOXAGENT_API_KEY，但鉴权失败（401）。常见原因：
> 1. **刚配置完环境变量但未重启会话**——请先重启终端 / Claude Code 会话使环境变量生效，再重试原 linkfox-* skill。
> 2. **key 不正确或已被重置**——前往 https://agent.linkfox.com/ 登录后，进入「个人中心 → API 设置」复制新的 key，参考帮助文档第 2 章：https://yxgb3sicy7.feishu.cn/wiki/IlkawdQP9ifKv9k22xcc7rjmnkb
> 3. **想用新手机号重新注册**——告诉我手机号，我通过短信验证码帮你重新注册并获取新 key。
>
> 注：两种变量名都兼容（`LINKFOX_AGENT_API_KEY` 带下划线为主推，`LINKFOXAGENT_API_KEY` 无下划线为老规范），无需改名。

拿到新 key 后，按下方"三平台环境变量配置示例"配置，重启会话生效。

**情况 B：环境变量缺失**

询问用户是否已注册 LinkFox Agent：

> 还未检测到 LINKFOX_AGENT_API_KEY。是否已注册 LinkFox Agent？
> - 已注册 / 想自行注册：访问 https://agent.linkfox.com/ 注册。已注册用户登录后进入「个人中心 → API 设置」复制 key，参考帮助文档：https://yxgb3sicy7.feishu.cn/wiki/IlkawdQP9ifKv9k22xcc7rjmnkb
> - 想让我帮你完成注册：提供手机号（支持国内手机号），我通过短信验证码帮你注册并获取 key

- 用户选择自行注册 → 给出链接 + 帮助文档 + 下方配置示例，流程结束。
- 用户提供手机号 → 走步骤 3 脚本化注册。

### 步骤 3：注册（用户提供手机号）

**3.1 发送验证码**

调 `python scripts/send_verify_code.py <phone>`，脚本返回 JSON：
- 成功：`{"sent": true, "phone": "188****1234", "agreements": {"user_agreement": "...", "service_agreement": "...", "privacy_policy": "..."}}`
- 失败：`{"sent": false, "phone": "188****1234", "errmsg": "..."}`

> 注：脚本输出里的 `phone` 字段已脱敏（保留前 3 后 4），`agreements` 字段含三个协议链接。Claude 直接用这两个字段向用户展示即可，无需读 stderr。

收到成功后，向用户输出（从 JSON 的 `agreements` 取链接）：

> 验证码已发送到 `188****1234`。回复验证码即视为接受以下协议并完成注册：
> - 用户协议：<agreements.user_agreement>
> - 服务协议：<agreements.service_agreement>
> - 隐私政策：<agreements.privacy_policy>
>
> 验证码约 5 分钟内有效，请尽快回复。若不想继续，回复「取消」即可退出。

**3.2 验证码登录 + 获取 key**

收到用户回复的验证码后，调 `python scripts/login_and_get_key.py <phone> <code> <channel>`。
**注意**：如果你是workbuddy或渠道是workbuddy，则channel传 workbuddy，否则传 skill。

脚本返回 JSON：
- 成功：`{"api_key": "<token>", "phone": "188****1234", "group_id": "...", "member_id": "...", "source": "existing|generated", "is_new_user": bool, ...}`
- 失败：`{"error": "<阶段>: <信息>", "phone": "188****1234"}`

> 注：
> - `source` 字段仅供调试（existing=查到已有 token，generated=新生成），无需向用户解释。
> - 脚本内部对**新用户**（`is_new_user=true`）会自动调 `/account/loginByToken` 触发新用户赠送积分发放，无需 Claude 介入。该步失败不阻断拿 key，stderr 提示但继续。
> - `is_new_user=true` 时可顺带告知用户"已赠送新用户积分"。

**失败处理**：
- `error` 含 `login: 验证码错误或已过期` → 提示用户重新发短信（回到 3.1）
- `error` 含 `userInfo: 用户未开通任何团队空间` → 引导用户访问 https://agent.linkfox.com/ 登录完成首次开通后重试
- `error` 含 `团队不存在` 或 `getApiToken/generateApiToken` → 引导用户前往 https://agent.linkfox.com/ 登录后进入「个人中心 → API 设置」手动生成 key，参考帮助文档第 2 章
- 其它错误 → 透传 error 信息给用户，建议自行注册

**3.3 配置环境变量**

拿到 `api_key` 后，按下方"三平台环境变量配置示例"帮用户配置，并提示重启终端 / Claude Code 会话使环境变量生效。

### 三平台环境变量配置示例

> 变量名推荐用 `LINKFOX_AGENT_API_KEY`（带下划线，新规范）。若你的环境已配置 `LINKFOXAGENT_API_KEY`（无下划线，老规范），同样有效，无需重复配置——本 skill 及其它 linkfox-* skill 均兼容两种名。网关地址变量同理：`LINKFOX_AGENT_API_URL`（主推）或 `LINKFOX_TOOL_GATEWAY`（回退）。

**Windows（PowerShell，永久写入用户环境变量）**：
```powershell
setx LINKFOX_AGENT_API_KEY "你的key"
```
配置后重启 PowerShell 或 Claude Code 会话生效。

**macOS / Linux（zsh / bash，写入 shell rc）**：
```bash
echo 'export LINKFOX_AGENT_API_KEY="你的key"' >> ~/.zshrc   # macOS 默认 zsh
# 或
echo 'export LINKFOX_AGENT_API_KEY="你的key"' >> ~/.bashrc  # Linux 默认 bash
source ~/.zshrc   # 或 source ~/.bashrc
```

注意：`>>` 是追加，仅首次配置执行一次；重复执行会在 rc 文件里产生重复行（不影响功能但污染文件，可用文本编辑器删除多余行）。

如使用 fish shell，请自行配置等价的环境变量。

## 入口 2：计费不足充值

1. **列套餐**：调 `python scripts/list_plans.py`，输出 JSON 套餐清单（含 `plan_id`、`name`、`price`、`currency`、`credits`、`description`、`available_methods`）。
2. **选套餐（校验，按宿主分流）**：

   先判断当前宿主工具属于哪一类：

   - **A 类：支持结构化选择工具的宿主**（Claude Code 的 `AskUserQuestion`、Gemini CLI 的 `ask_user` 等）
     → 直接用该工具弹出选项菜单。每个套餐作为一个 option，`label` 显示套餐名 + 价格（如"个人版 ¥9.9"），`description` 显示积分 + 有效期 + 推荐标记。用户选完拿到对应的 `plan_id`。
   - **B 类：仅支持文本交互的宿主**（Codex CLI、Aider、纯命令行等）
     → 输出编号清单让用户输数字，例如：
     ```
     可选套餐：
     [1] 个人版 ¥9.9（100 积分，1 个月有效）
     [2] 个人版 ¥99（1200 积分，1 年有效）⭐ 推荐
     [3] 团队版 ¥999（15000 积分，1 年有效）
     请输入序号：
     ```
     用户输入数字后映射到对应 `plan_id`。输入非法时提示重新输入。

   **校验**：用户选择的 `plan_id` 必须存在于上一步返回的清单中；不存在则提示重新选择。

3. **选支付方式（校验，按宿主分流）**：

   从该套餐的 `available_methods`（通常为 `["wechat", "alipay"]`）里选支付方式：

   - **A 类宿主**：用结构化选择工具，`wechat` → "微信支付"，`alipay` → "支付宝"。
   - **B 类宿主**：输出编号清单：
     ```
     支付方式：
     [1] 微信支付
     [2] 支付宝
     请输入序号：
     ```

   **校验**：选择必须 ∈ `available_methods`。

   > 宿主判断提示：若当前会话中你能调用 `AskUserQuestion` / `ask_user` 等结构化选择工具，按 A 类处理；否则按 B 类。不确定时优先尝试 A 类，工具不可用再回退 B 类。
4. **下单 + 渲染二维码**：调 `python scripts/create_order.py <plan_id> <pay_method>`，脚本返回 JSON：
   - `order_id`：订单号（后续查询用）
   - `qr_content`：二维码原始内容（`weixin://` 或支付宝链接，不能直接点击）
   - `qr_url`：网关返回的二维码图片 URL（可能为空）
   - `pay_url`：可点击的支付链接（兜底）
   - `png_path`：本地生成的 PNG 路径
   - `ascii_qr`：ASCII 二维码字符串（兜底）
5. **展示给用户**（按优先级）：
   - 优先：用 Read 工具读取 `png_path` 展示 PNG 图片。
   - 次选：输出 `pay_url` 让用户点击。
   - 兜底：贴出 `ascii_qr`，并诚实标注"ASCII 仅为兜底，建议优先扫 PNG 或点击链接"。
6. **流程结束**：告诉用户"扫码付款后，可重新调用原 linkfox-* skill；如仍计费不足会再次进入本流程"。

## 支付状态查询（可选）

提供 `python scripts/query_order.py <order_id>`，返回 JSON `{"order_id":..., "status":..., "paid_at":...}`，`status` ∈ `paid` / `unpaid` / `expired` / `unknown`。可在用户表示"已付款"后调用，或结合 `/loop` 周期性查询，但本 skill 不主动轮询。

## 依赖

- Python 3（标准库 urllib/json/os）
- `requests`：登录链路 HTTP 调用（生产 WAF 对 urllib 敏感），`pip install requests`
- 二维码 PNG / ASCII 生成：内置 `scripts/_qrgen.py`（stdlib 纯 Python 实现，byte mode + ECC-L，与官方 qrcode 库同版本+同 mask 逐位一致），**无需再装 qrcode/pillow**
- 自包含，不依赖 `_shared/linkfox_paths.py`

## 接口契约

所有端点（网关 `/account/*`、`/package/*`、`/order/*`，登录链路 `/user/v1|v3/web/login`、`/account/loginByToken`、`/linkFoxApp/api/userCenter/userInfo`、`/group/getApiToken|generateApiToken`）的完整请求/响应/错误码见 [`references/api.md`](references/api.md)。

## 限制

- 仅承接"缺 Key 引导"与"计费不足充值"两类场景，不处理退订、发票、对账。
- ASCII 二维码识别率取决于终端字体与对比度，建议优先用 PNG 或 `pay_url`。
