# TextIn AppKey Setup

This page covers the legacy standalone AppKey flow. For Device OAuth, browser
PKCE, and WorkBuddy login, use [authentication.md](authentication.md).

## When to Configure

- Free daily limit exceeded (40001 error)
- File size exceeds 10MB limit (40302 error)
- Want unlimited quota for production use

## Setup Steps

### Option 1: Interactive standalone setup

```bash
xparse-cli auth app-key
```

Follow the prompts to enter your `APP_ID` and `SECRET_CODE` from [TextIn Console](https://www.textin.com/console/dashboard/setting). Credentials are saved to `~/.xparse-cli/config.yaml`. Do not use this flow to collect credentials inside WorkBuddy; reconnect the Connector instead.

Bare `xparse-cli auth` also exposes this option from its terminal menu. For
scripts and piped input, bare `auth` preserves the previous direct AppKey
prompt behavior.

### Option 2: Environment Variables

For CI/automation, set environment variables:

```bash
export XPARSE_APP_ID=<your_app_id>
export XPARSE_SECRET_CODE=<your_secret_code>
```

### Verify Setup

```bash
xparse-cli auth --show
xparse-cli parse <FILE> --api paid --auth-method app-key
```

Credential priority: CLI flags → env vars → `~/.xparse-cli/config.yaml`

## Troubleshooting

For all error codes and recovery actions, see [error-handling.md](error-handling.md).

## References

- [TextIn Console](https://www.textin.com/console/dashboard/setting)
- [TextIn Documentation](https://docs.textin.com/)
