#!/bin/bash
# Setup script for 乐享 MCP Skill (ClawHub 外部版本)

set -e

echo "🚀 设置乐享 MCP Skill..."
echo ""

echo "请访问以下地址获取配置信息："
echo "👉 https://lexiangla.com/mcp"
echo ""

read -p "请输入你的企业标识 (company_from): " COMPANY_FROM
read -p "请输入你的访问令牌 (access_token，如 lxmcp_xxx): " ACCESS_TOKEN

if [ -z "$COMPANY_FROM" ] || [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ 企业标识和访问令牌不能为空"
    exit 1
fi

# 配置文件路径
MCPORTER_CONFIG="$HOME/.mcporter/mcporter.json"
mkdir -p "$(dirname "$MCPORTER_CONFIG")"

if [ -f "$MCPORTER_CONFIG" ]; then
    echo ""
    echo "⚠️  配置文件已存在: $MCPORTER_CONFIG"
    read -p "是否覆盖现有配置？(y/N): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "ℹ️  跳过配置写入"
        exit 0
    fi
fi

cat > "$MCPORTER_CONFIG" <<EOF
{
  "mcpServers": {
    "lexiang": {
      "url": "https://mcp.lexiang-app.com/mcp?company_from=$COMPANY_FROM&access_token=$ACCESS_TOKEN&preset=meta",
      "transport": "http"
    }
  }
}
EOF

echo "✅ 配置已写入: $MCPORTER_CONFIG"
echo ""
echo "🎉 设置完成！"
