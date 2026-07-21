# OpenClaw Email Skill 📧

A comprehensive email management and automation skill for OpenClaw, enabling seamless email sending, configuration, and integration across multiple email providers.

## Features

- **Multi-provider Support**: Gmail, Outlook/Office365, Yahoo, QQ Mail, and custom SMTP servers
- **Attachment Support**: Send emails with multiple file attachments
- **HTML & Plain Text**: Support for both HTML and plain text email formats
- **CC/BCC Recipients**: Full recipient management capabilities
- **Secure Connections**: TLS/SSL encryption for secure email transmission
- **OpenClaw Integration**: Native integration with OpenClaw's skill system
- **Test Functionality**: Built-in test email verification

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/awspace/openclaw-email-skill.git
   cd openclaw-email-skill
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Create a configuration file `email_config.json`:

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

### For Gmail Users

1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google," select "App passwords"
   - Generate a new app password for "Mail"
   - Use this 16-character password in your config

## Usage Examples

### Command Line

```bash
# Send a simple email
python email_sender.py --to "recipient@example.com" --subject "Hello" --body "This is a test email"

# Send email with attachment
python email_sender.py --to "recipient@example.com" --subject "Report" --body "Please find attached" --attachment "report.pdf"

# Send test email
python email_sender.py --to "your-email@gmail.com" --test
```

### OpenClaw Integration

When installed as an OpenClaw skill, you can use natural language commands:

```
"Send email to recipient@example.com with subject Meeting Notes and body Here are the notes from today's meeting"
"Send test email to verify configuration"
"Email the report.pdf file to team@company.com"
```

### Python API

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

## Supported Email Providers

| Provider | SMTP Server | Port | TLS | Notes |
|----------|-------------|------|-----|-------|
| Gmail | smtp.gmail.com | 587 | Yes | Requires App Password with 2FA |
| Outlook/Office365 | smtp.office365.com | 587 | Yes | - |
| Yahoo | smtp.mail.yahoo.com | 587 | Yes | - |
| QQ Mail | smtp.qq.com | 587 | Yes | - |
| Custom SMTP | your.smtp.server.com | 587/465 | As configured | - |

## File Structure

```
openclaw-email-skill/
├── SKILL.md                    # Main skill documentation
├── email_sender.py            # Core email functionality
├── config_template.json       # Configuration template
├── test_email.py              # Test script
├── openclaw_integration.md    # OpenClaw integration guide
├── _meta.json                 # Skill metadata
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Requirements

- Python 3.7+
- OpenClaw (for integration)
- Required Python packages:
  - `smtplib` (standard library)
  - `email` (standard library)

## Troubleshooting

### Common Issues

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

### Error Messages

- `SMTPAuthenticationError`: Invalid credentials
- `SMTPConnectError`: Cannot connect to SMTP server
- `SMTPDataError`: Server rejected message
- `TimeoutError`: Connection timeout

## Security Notes

- Never commit email credentials to version control
- Use environment variables for production deployments
- Regularly rotate app passwords
- Consider using dedicated email accounts for automation
- Store credentials in secure locations (not in code)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built for [OpenClaw](https://openclaw.ai) - The open-source AI assistant platform
- Inspired by the need for seamless email automation in AI workflows
- Thanks to all contributors and users

## Support

For issues, questions, or feature requests:
- Open an issue on [GitHub](https://github.com/awspace/openclaw-email-skill/issues)
- Check the [OpenClaw documentation](https://docs.openclaw.ai)
- Join the [OpenClaw community](https://discord.com/invite/clawd)

---

**Happy Emailing!** 📧✨