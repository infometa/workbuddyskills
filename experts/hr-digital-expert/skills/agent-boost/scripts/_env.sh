#!/usr/bin/env bash
# ============================================================
# agent-boost 地址默认值 —— 唯一定义源
#
# 消费方：
#   register-agent.sh — AGENT_SERVER_URL（dev 默认，prod-deploy.sh 覆盖为生产值）
#   prod-deploy.sh    — PROD_AGENT_SERVER_URL, mcp_url()
# ============================================================

# ---- Agent Server ----
# dev 直连地址（绕过 Gateway/OA，接受 X-Staff-Name）
DEV_AGENT_SERVER_URL="${DEV_AGENT_SERVER_URL:-http://21.139.192.211:3000}"
# 生产地址
PROD_AGENT_SERVER_URL="${PROD_AGENT_SERVER_URL:-http://agent-server.prod.hrainative.woa.com}"
# register-agent.sh 默认用 dev（/agent-boost 在 dev 执行），prod-deploy.sh 覆盖为 prod
AGENT_SERVER_URL="${AGENT_SERVER_URL:-${DEV_AGENT_SERVER_URL}}"

# ---- MCP 服务域名规则（唯一定义源）----
#   dev  后缀 app.hrainative.woa.com（默认）
#   prod 部署脚本覆盖为 prod.hrainative.woa.com
MCP_SVC_SUFFIX="${MCP_SVC_SUFFIX:-app.hrainative.woa.com}"
mcp_url() { echo "http://$1-internal-mcp-service.${MCP_SVC_SUFFIX}/mcp"; }
