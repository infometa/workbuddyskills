# analysis dashboard-daily-report update

Use when the user wants to create or update a dashboard daily report configuration.

Do not use to send immediately. Use `dashboard-daily-report send`.

Command:

```bash
ae-cli analysis dashboard-daily-report update --project-id <project_id> --dashboard-id <dashboard_id> [--enable-send true] [--send-time <time>] [--enable-email true] [--email-new <emails>] [--payload '{...}']
```

The command is a patch-style upsert:

- If the dashboard has no saved configuration, the backend creates one and applies defaults for omitted fields.
- If a configuration exists, omitted fields remain unchanged.
- Pass an explicit boolean to enable or disable a saved channel.
- Pass an empty string or array to clear a saved destination.

SMTP transport is not caller-selectable. For direct email addresses, the backend uses company SMTP when configured and otherwise uses the default mail service.

When enabling Feishu, pass `--enable-feishu true --feishu-info '{"app_id":"cli_xxx","app_secret":"secret_xxx","webhook":["https://open.feishu.cn/open-apis/bot/v2/hook/..."]}'`. Treat `app_secret` and webhook URLs as sensitive.

Use `dashboard-daily-report get` before a selective update when the current state matters. The get response redacts secrets and webhook URLs, so do not copy the full response back as an update payload.

Output is the gateway envelope. `data` contains the saved daily report configuration result.
