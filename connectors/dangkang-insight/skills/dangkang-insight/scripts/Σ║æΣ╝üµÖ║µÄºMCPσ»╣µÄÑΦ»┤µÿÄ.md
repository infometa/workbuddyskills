# 云企智控财税合规检测 —— MCP 对接说明

> 本技能**不直连平台 OpenAPI**：不需要 AK/SK，也不依赖 `gmssl`。
> 所有业务接口经 **网关 MCP**（JSON-RPC 2.0 / streamable HTTP）调用，网关地址配置在
> `../config/mcp.ini` 的 `[mcp] url`。

## 一、接口 ↔ MCP 工具映射

| 步骤 | 接口 | 平台路径 | MCP 工具 | 脚本命令 |
|------|------|----------|----------|----------|
| 1.1 | 发送短信验证码 | `/gg/org/auth/riskDet/smsCodeSend` | `riskdet-sms-code-send` | `1` |
| 1.2 | 上传验证码登录 | `/gg/org/auth/riskDet/smsCodeUpload` | `riskdet-sms-code-upload` | `2` |
| 2.1 | 获取电局登录二维码 | `/gg/org/auth/riskDet/getQrcode` | `riskdet-get-qrcode` | `6` |
| 2.2 | 扫码状态查询 | `/gg/org/auth/riskDet/scanCode` | `riskdet-scan-code` | `7`（脚本内轮询） |
| 1.3 | 查询授权状态及报告 | `/znfk/qyfxgl/saas/yqzk/querySqztBgxx` | `riskdet-query-status` | `3` |
| 1.4 | 付费报告申请 | `/gg/org/auth/report/apply` | `riskdet-report-apply` | `4` |
| 1.5 | 获取风险检测概览 | `/znfk/qyfxgl/saas/zsr/getQyfxjcglxx` | `riskdet-risk-overview` | `5` |
| 辅助 | 当前用户信息 | `/ggyw/sys/user/info` | `sys-user-info` | `info` |
| 辅助 | 查询订单 | `/znfk/qyfxgl/saas/yqzk/queryOrder` | `query-order` | `order` |

> 平台侧路径前缀说明：网关把 `/gg/...` 映射为 yfp-ggyw 服务的 `/ggyw/...`；
> `/znfk/...` 走 znfk-fxmxgl 服务（`server.config.baseUrlZnfk`）。

## 二、网关侧前置条件

1. **1.3 / 1.4 / 1.5 三个工具需要在网关配置里新增**（`tools` + `allowTools`），
   直接使用交付的 `gateway_新增工具_1.3_1.4_1.5.yaml`。
   未启用时报错形如：`JSON-RPC 错误：{"code": -32602, "message": "unknown tool: riskdet-risk-overview"}`。

2. **登录态映射（关键）**：
   - `1.1 / 1.2 / 2.1 / 2.2 / 1.4` 由网关转发到 **yfp-ggyw** 服务，该服务受登录态保护；
     网关必须把调用方身份映射成该服务的登录会话（服务端会话 / `login-user` 头），
     否则这些工具会返回 `401 账号未登录`（实测复现）。
   - `1.3 / 1.5` 走 **znfk-fxmxgl** 服务，是纯查库接口，**不依赖登录态**（实测通过）。

3. **二维码展示**：`riskdet-get-qrcode` 把二维码作为 Markdown 图片塞在一行超长文本里，
   助手无法可靠地转抄。技能脚本会自己经 MCP 取码并**重编码为 196×196 的 1bit 迷你 PNG**
   （base64 约 700 字符）后输出内联卡片片段，因此**不要**把 `riskdet-get-qrcode` 改成
   返回 `image` 内容块以外的格式（若网关支持返回 `image` 内容块，见文件末尾的说明）。

## 三、参数自动取齐链路

脚本不要求调用方手工准备账号类 / 订单类参数，会自动经 MCP 补齐：

```
sys-user-info ─┬─ userId            → 各接口 userId / query-order 的 czrId
               ├─ zhid              → 各接口 customerId（必须与 userId 配套）
               ├─ companyTaxNo      → nsrsbh 默认值
               └─ companyName       → nsrmc 默认值
query-order(czrId=userId) ─┬─ ddbh     （选中订单的订单编号）
                           └─ cpfwDm   （商品服务代码，如 MFSY_0000）
```

优先级：**命令行显式传入 > MCP 自动取参 > `config/mcp.ini` 的 `[business]` 兜底值**。

`qdbm` 默认 `1033`；`sqInfo` 由脚本内置固定文案的 base64（后端仅校验非空）。

## 四、配置

`config/mcp.ini`：

```ini
[mcp]
url = https://<你的域名>/ggyw/mcp
access_token =            # 网关要求鉴权时填；留空则不发送 Authorization 头
timeout = 60

[business]                # 可选兜底，仅当上面两个工具不可用时才需要
ddbh =
cpfwbh =
qdbm = 1033
product_id =
product_attr_unique =
```

也可用环境变量 `DKI_MCP_TOKEN` 覆盖 `access_token`，避免令牌落盘。

## 五、常见情况排错

| 现象 | 原因 / 处理 |
|------|-------------|
| `401 账号未登录` | 网关未把调用方身份映射为 yfp-ggyw 的登录态（见 §二.2） |
| `unknown tool: riskdet-query-status` | 1.3/1.4/1.5 工具未在网关配置里启用 |
| 2.1 返回 `9999` 且 `msg` 为 null | `ssdq` 填了地级市码；只认省级码与计划外单列市码，辽宁用 `2100` |
| `qrcode_widget_ready=false` | 二维码点阵解码失败（图片格式非预期）；改用 `qrcode_png` 路径走兜底展示 |
| 报告一直查不到 | 先确认 1.1/2.1 已成功授权（`sqztDm=02`）；1.3 只返回「授权成功」的记录 |
| 命令7 一直等到超时 | 守护进程被宿主的进程回收机制杀掉；命令6 已用「分离进程」机制规避，若仍复现查 `logs/daemon.out` |

## 六、二维码改用 MCP image 内容块（可选增强）

若网关支持在工具响应里返回 MCP `image` 内容块：

```json
{"type": "image", "data": "<png base64>", "mimeType": "image/png"}
```

宿主会直接把图片渲染在工具调用卡片里，二维码天然落在对话流中，此时可以完全省掉本地脚本的
二维码重编码步骤。注意 Go `text/template` 无法给 base64 折行，指望「模板里把 base64 换行输出」
这条路走不通。
