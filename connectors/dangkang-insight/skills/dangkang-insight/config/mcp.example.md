# ============================================================
# dangkang-insight —— 网关 MCP 对接配置（示例模板）
# 用法：复制本文件为 config/mcp.ini，填入真实值后即可使用。
#       真实配置文件 config/mcp.ini 已被 .gitignore 忽略，请勿提交含令牌的版本。
# ============================================================

[mcp]
# 网关 MCP 入口（streamable HTTP / JSON-RPC 2.0）。
# 指向你部署的 gateway 服务，例如：
#   https://<你的域名>/ggyw/mcp
url = https://lxyq.cssyq.com.cn/ggyw/mcp

# 访问令牌（Bearer），可留空。
#   - 网关要求 OAuth 鉴权时：填一个可用的 access token
#   - 网关做了来源放行时：留空（脚本不会发送 Authorization 头）
# 也可用环境变量 DKI_MCP_TOKEN 覆盖，避免令牌写进文件。
access_token =

# 单次 MCP 调用超时秒数
timeout = 60

[business]
# 可选兜底值。正常情况下脚本会经 MCP 自动取参：
#   userId / customerId / nsrsbh / nsrmc  ← sys-user-info
#   ddbh / cpfwbh                          ← query-order(czrId=userId)
# 只有当上面的工具在当前网关不可用（例如未打通登录态、返回 401）时，才需要在这里兜底。
ddbh =
cpfwbh =
qdbm = 1033
product_id =
product_attr_unique =
