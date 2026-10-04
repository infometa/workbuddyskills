# TextIn AppKey Setup

This page covers the legacy standalone AppKey flow. For Device OAuth and browser
PKCE, use [authentication.md](authentication.md).

## When to Configure

- Free daily limit exceeded (40001 error)
- File size exceeds 10MB limit (40302 error)
- Want unlimited quota for production use

## Purchase Paid Credits

Purchase or recharge paid PDF-to-Markdown credits through the account's regional
portal. When the current service returns an `upgrade_url`, use that exact URL;
otherwise contact the account's regional support. Never reuse a purchase URL
from another service region.
Purchasing credits or configuring credentials does not authorize automatic paid
usage. Run the paid API only when the user explicitly selects `--api paid`.

## Setup Steps

### Option 1: Interactive standalone setup

```bash
xparse-cli auth app-key
```

Follow the prompts to enter your `APP_ID` and `SECRET_CODE` from the TextIn
Console associated with the current region and account. Credentials are saved
to `~/.xparse-cli/config.yaml`. Do not collect credentials in the conversation;
the user must enter them directly in the local CLI prompt.

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

- [TextIn Documentation](https://docs.textin.com/)
- [Authentication](authentication.md)
- [Structured error handling](error-handling.md)
