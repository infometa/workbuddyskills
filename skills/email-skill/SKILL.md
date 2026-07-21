---
name: email-skill
description: Email management and automation. Send, read, search, and organize emails across multiple providers.
description_zh: "邮件管理与自动化，支持多邮件服务商收发搜索"
description_en: "Email management and automation across multiple providers"
version: 0.1.0
metadata:
  clawdbot:
    emoji: "📧"
    always: true
    requires:
      bins:
        - python3
---

# Email 📧

Email management and automation with attachment support.

## Features

- Send emails with attachments
- Support for multiple email providers (Gmail, Outlook, Yahoo, etc.)
- HTML and plain text email support
- CC and BCC recipients
- Test email functionality
- Secure TLS/SSL connections

## Setup Instructions

### 1. Configure Email Credentials

Create a configuration file `email_config.json` in your workspace:

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "username": "your-email@gmail.com",
  "password": "your-app-password",
  "sender_name": "OpenClaw Assistant",
  "use_tls": true,
  "use_ssl": false
}
```

### 2. For Gmail Users (Recommended)

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google," select "App passwords"
   - Generate a new app password for "Mail"
   - Use this 16-character password in your config

### 3. Alternative: Environment Variables

Set these environment variables instead of using a config file:

```bash
# Windows
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set EMAIL_USERNAME=your-email@gmail.com
set EMAIL_PASSWORD=your-app-password
set EMAIL_SENDER_NAME="OpenClaw Assistant"

# macOS/Linux
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export EMAIL_USERNAME=your-email@gmail.com
export EMAIL_PASSWORD=your-app-password
export EMAIL_SENDER_NAME="OpenClaw Assistant"
```

## Usage Examples

### Send a Simple Email
```bash
python email_sender.py --to "recipient@example.com" --subject "Hello" --body "This is a test email"
```

### Send Email with Attachment
```bash
python email_sender.py --to "recipient@example.com" --subject "Report" --body "Please find attached" --attachment "report.pdf" --attachment "data.xlsx"
```

### Send Test Email
```bash
python email_sender.py --to "your-email@gmail.com" --test
```

### Using with OpenClaw Commands
```
"Send email to recipient@example.com with subject Meeting Notes and body Here are the notes from today's meeting"
"Send test email to verify configuration"
"Email the report.pdf file to team@company.com"
```

## Supported Email Providers

| Provider | SMTP Server | Port | TLS |
|----------|-------------|------|-----|
| Gmail | smtp.gmail.com | 587 | Yes |
| Outlook/Office365 | smtp.office365.com | 587 | Yes |
| Yahoo | smtp.mail.yahoo.com | 587 | Yes |
| QQ Mail | smtp.qq.com | 587 | Yes |
| Custom SMTP | your.smtp.server.com | 587/465 | As configured |

## Python API Usage

```python
from email_sender import EmailSender

# Initialize with config file
sender = EmailSender("email_config.json")

# Send email with attachment
result = sender.send_email(
    to_email="recipient@example.com",
    subject="Important Document",
    body="Please review the attached document.",
    attachments=["document.pdf", "data.csv"]
)

if result["success"]:
    print(f"Email sent with {result['attachments']} attachments")
else:
    print(f"Error: {result['error']}")
```

## Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Verify your username and password
   - For Gmail: Use app password instead of regular password
   - Check if 2FA is enabled

2. **Connection Refused**
   - Verify SMTP server and port
   - Check firewall settings
   - Try different port (465 for SSL)

3. **Attachment Too Large**
   - Most providers limit attachments to 25MB
   - Consider compressing files or using cloud storage links

## Security Notes

- Never commit email credentials to version control
- Use environment variables for production deployments
- Regularly rotate app passwords
- Consider using dedicated email accounts for automation
