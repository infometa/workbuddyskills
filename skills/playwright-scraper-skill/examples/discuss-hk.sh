#!/bin/bash
# 範例：爬取 Discuss.com.hk 熱門話題

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "🕷️  Discuss.com.hk 爬蟲範例"
echo ""
echo "使用 Playwright Stealth（已驗證成功）"
echo ""

cd "$SKILL_DIR" && \
WAIT_TIME=10000 \
SCREENSHOT_PATH=/tmp/discuss-hk.png \
SAVE_HTML=true \
node scripts/playwright-stealth.js "https://m.discuss.com.hk/#hot"
