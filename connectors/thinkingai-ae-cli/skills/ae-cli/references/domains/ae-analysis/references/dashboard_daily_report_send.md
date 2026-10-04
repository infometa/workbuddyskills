# analysis dashboard-daily-report send

Use when the user wants to send a dashboard daily report immediately.

Do not use for configuration changes. Use `dashboard-daily-report update`.

Command:

```bash
ae-cli analysis dashboard-daily-report send --project-id <project_id> --dashboard-id <dashboard_id> [--email-new <emails>] [--dd-url '["https://..."]'] [--need-csv true] [--payload '{...}']
```

Behavior:

- Destination fields infer channels. Do not pass `enable_email`, `enable_smtp`, or other channel switches.
- Email fields select email, `dd_url` selects DingTalk, `wx_url` selects WeCom, `feishu_info` selects Feishu, `kim_url` selects KIM, and `slack_url` selects Slack.
- If no destination field is provided, the command reuses saved destinations. Other fields such as `need_csv`, title, language, or timezone may still override the saved configuration for this send.
- If a destination field is explicitly provided but empty or invalid, the command fails instead of falling back to saved destinations.
- Direct email addresses use company SMTP when configured and otherwise use the default mail service.
- Feishu requires `app_id`, `app_secret`, and at least one webhook because the backend uploads the dashboard image before calling the group bot. Treat credentials and webhook URLs as sensitive.

Output `data.task_id` identifies the asynchronous delivery task. Inspect it with:

```bash
ae-cli analysis dashboard-daily-report send-status --project-id <project_id> --task-id <task_id>
```
