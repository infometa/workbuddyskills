#!/bin/bash
# 簡單測試腳本

set -e

echo "🧪 Playwright Scraper Skill 測試"
echo ""

# 測試 1: Playwright Simple
echo "📝 測試 1: Playwright Simple (Example.com)"
node scripts/playwright-simple.js https://example.com > /tmp/test-simple.json
if grep -q "Example Domain" /tmp/test-simple.json; then
  echo "✅ Simple 模式正常"
else
  echo "❌ Simple 模式失敗"
  exit 1
fi
echo ""

# 測試 2: Playwright Stealth
echo "📝 測試 2: Playwright Stealth (Example.com)"
node scripts/playwright-stealth.js https://example.com > /tmp/test-stealth.json
if grep -q "Example Domain" /tmp/test-stealth.json; then
  echo "✅ Stealth 模式正常"
else
  echo "❌ Stealth 模式失敗"
  exit 1
fi
echo ""

# 測試 3: 環境變數
echo "📝 測試 3: 環境變數 (WAIT_TIME)"
WAIT_TIME=1000 node scripts/playwright-simple.js https://example.com > /tmp/test-env.json
if grep -q "Example Domain" /tmp/test-env.json; then
  echo "✅ 環境變數正常"
else
  echo "❌ 環境變數失敗"
  exit 1
fi
echo ""

# 清理
rm -f /tmp/test-*.json screenshot-*.png

echo "✅ 所有測試通過！"
