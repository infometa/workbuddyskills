---
name: email-daily-summary
description: Automatically logs into email accounts (Gmail, Outlook, QQ Mail, etc.) and generates daily email summaries. Use when the user wants to get a summary of their emails, check important messages, or create daily email digests.
allowed-tools: Bash(browser-use:*), Bash(echo:*), Bash(date:*)
display_name: "email-daily-summary"
display_name_en: "email-daily-summary"
description_zh: "Automatically logs into email accounts (Gmail, Outlook, QQ Mail, etc.) and generates daily email summaries. Use when the user wants to get a summary of their emails, check important messages, or create daily email digests."
description_en: "Automatically logs into email accounts (Gmail, Outlook, QQ Mail, etc.) and generates daily email summaries. Use when the user wants to get a summary of their emails, check important messages, or create daily email digests."
visibility: "public"
---

# Email Daily Summary Skill

这个技能帮助你自动登录邮箱，获取邮件内容，并生成每日邮件总结。

## 功能特性

- 🔐 支持多种邮箱登录（Gmail、Outlook、QQ 邮箱、163 邮箱等）
- 📧 自动获取最新邮件列表
- 📝 智能生成邮件摘要
- 🏷️ 按重要性/发件人/主题分类
- 📊 生成每日邮件统计报告

## 前置要求

1. 安装 browser-use CLI：
```bash
uv pip install browser-use[cli]
browser-use install
```

2. 确保已在浏览器中登录过邮箱（使用 real 模式可直接复用登录状态）

## 使用方法

### 方式一：使用已登录的浏览器（推荐）

使用 `--browser real` 模式可以复用你 Chrome 浏览器中已登录的邮箱会话：

```bash
# Gmail
browser-use --browser real open https://mail.google.com

# Outlook
browser-use --browser real open https://outlook.live.com

# QQ 邮箱
browser-use --browser real open https://mail.qq.com

# 163 邮箱
browser-use --browser real open https://mail.163.com
```

### 方式二：手动登录流程

如果需要手动登录，使用 `--headed` 模式查看操作过程：

```bash
# 打开邮箱登录页面（以 Gmail 为例）
browser-use --headed open https://accounts.google.com

# 查看页面元素
browser-use state

# 输入邮箱地址（根据 state 返回的索引）
browser-use input <email_input_index> "your-email@gmail.com"
browser-use click <next_button_index>

# 输入密码
browser-use input <password_input_index> "your-password"
browser-use click <login_button_index>

# 跳转到邮箱
browser-use open https://mail.google.com
```

## 获取邮件列表

登录成功后，获取邮件列表：

```bash
# 获取当前页面状态，查看邮件列表
browser-use state

# 截图保存当前邮件列表
browser-use screenshot emails_$(date +%Y%m%d).png

# 使用 JavaScript 提取邮件信息（Gmail 示例）
browser-use eval "
  const emails = [];
  document.querySelectorAll('tr.zA').forEach((row, i) => {
    if (i < 20) {
      const sender = row.querySelector('.yX.xY span')?.innerText || '';
      const subject = row.querySelector('.y6 span')?.innerText || '';
      const snippet = row.querySelector('.y2')?.innerText || '';
      const time = row.querySelector('.xW.xY span')?.innerText || '';
      emails.push({ sender, subject, snippet, time });
    }
  });
  JSON.stringify(emails, null, 2);
"
```

## 使用 Python 生成邮件总结

```bash
# 初始化邮件数据收集
browser-use python "
emails_data = []
summary_date = '$(date +%Y-%m-%d)'
"

# 滚动页面加载更多邮件
browser-use python "
for i in range(3):
    browser.scroll('down')
    import time
    time.sleep(1)
"

# 提取邮件数据（需要根据实际邮箱 DOM 结构调整）
browser-use python "
import json

# 获取页面 HTML 进行解析
html = browser.html

# 这里需要根据具体邮箱服务解析 HTML
# 示例：统计基本信息
print(f'=== 邮件日报 {summary_date} ===')
print(f'页面 URL: {browser.url}')
print(f'页面标题: {browser.title}')
"

# 截图保存
browser-use python "
browser.screenshot(f'email_summary_{summary_date}.png')
print(f'截图已保存: email_summary_{summary_date}.png')
"
```

## 完整的每日邮件总结脚本

创建一个完整的总结流程：

```bash
#!/bin/bash
# email_daily_summary.sh

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
OUTPUT_DIR="./email_summaries"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "📧 邮件日报生成中..."
echo "日期: $DATE $TIME"
echo "=========================================="

# 1. 打开邮箱（使用已登录的浏览器）
browser-use --browser real open https://mail.google.com

# 2. 等待页面加载
sleep 3

# 3. 获取页面状态
echo ""
echo "📋 当前邮箱状态:"
browser-use state

# 4. 截图保存邮件列表
echo ""
echo "📸 保存截图..."
browser-use screenshot "$OUTPUT_DIR/inbox_$DATE.png"

# 5. 提取邮件数据
echo ""
echo "📊 邮件统计:"
browser-use eval "
(() => {
  const unreadCount = document.querySelectorAll('.zE').length;
  const totalVisible = document.querySelectorAll('tr.zA').length;
  return JSON.stringify({
    unread: unreadCount,
    visible: totalVisible,
    timestamp: new Date().toISOString()
  });
})()
"

# 6. 关闭浏览器
echo ""
echo "✅ 完成！截图保存至: $OUTPUT_DIR/inbox_$DATE.png"
browser-use close
```

## 支持的邮箱服务

| 邮箱服务 | 登录 URL | 收件箱 URL |
|---------|---------|-----------|
| Gmail | https://accounts.google.com | https://mail.google.com |
| Outlook | https://login.live.com | https://outlook.live.com |
| QQ 邮箱 | https://mail.qq.com | https://mail.qq.com |
| 163 邮箱 | https://mail.163.com | https://mail.163.com |
| 126 邮箱 | https://mail.126.com | https://mail.126.com |
| 企业微信邮箱 | https://exmail.qq.com | https://exmail.qq.com |

## 生成 AI 邮件摘要

如果配置了 API Key，可以使用 AI 自动生成邮件摘要：

```bash
# 使用 AI 提取邮件摘要（需要 BROWSER_USE_API_KEY）
browser-use --browser real open https://mail.google.com
browser-use extract "提取前 10 封邮件的发件人、主题和摘要，按重要性排序"
```

## 定时任务设置

### macOS/Linux (crontab)

```bash
# 编辑 crontab
crontab -e

# 添加每日早上 9 点执行的任务
0 9 * * * /path/to/email_daily_summary.sh >> /path/to/logs/email_summary.log 2>&1
```

### macOS (launchd)

创建 `~/Library/LaunchAgents/com.email.dailysummary.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.email.dailysummary</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/email_daily_summary.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/email_summary.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/email_summary_error.log</string>
</dict>
</plist>
```

加载任务：
```bash
launchctl load ~/Library/LaunchAgents/com.email.dailysummary.plist
```

## 输出示例

生成的邮件总结报告格式：

```
==========================================
📧 邮件日报 - 2026-01-30
==========================================

📊 统计概览:
- 未读邮件: 12 封
- 今日新邮件: 28 封
- 重要邮件: 5 封

🔴 重要邮件:
1. [工作] 来自 boss@company.com
   主题: 项目进度汇报 - 紧急
   时间: 09:30

2. [财务] 来自 finance@bank.com
   主题: 账单提醒
   时间: 08:15

📬 今日邮件分类:
- 工作相关: 15 封
- 订阅通知: 8 封
- 社交媒体: 3 封
- 其他: 2 封

💡 建议操作:
- 回复 boss@company.com 的邮件
- 处理 3 封需要审批的邮件

==========================================
```

## 安全提示

⚠️ **重要安全建议**：

1. **不要在脚本中明文保存密码**，优先使用 `--browser real` 模式复用已登录会话
2. **敏感信息使用环境变量**存储
3. **定期检查授权应用**，移除不需要的第三方访问
4. **启用两步验证**保护邮箱安全
5. **日志文件不要包含敏感信息**

## 故障排除

**登录失败？**
```bash
# 使用 headed 模式查看登录过程
browser-use --browser real --headed open https://mail.google.com
```

**页面元素找不到？**
```bash
# 等待页面完全加载
sleep 5
browser-use state
```

**会话过期？**
```bash
# 关闭所有会话重新开始
browser-use close --all
browser-use --browser real open https://mail.google.com
```

## 清理

完成后记得关闭浏览器：

```bash
browser-use close
```
