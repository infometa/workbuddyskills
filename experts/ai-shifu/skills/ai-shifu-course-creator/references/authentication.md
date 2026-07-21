# Platform Authentication

Read this file before any CLI-backed course-target, deployment, management, or analytics task.

## Verify First

Always use `scripts/shifu-cli.py`. Never read tokens directly, construct authentication headers, or make raw platform API calls.

1. Run `shifu-cli.py verify` before considering login.
2. Handle the exit code:
   - Exit `0`: the token is valid; continue without logging in.
   - Exit `1`: guide the user through one SMS login session using `cli/cli-reference.md#agent-login-flow`.
   - Exit `2`: treat this as a network problem and retry later; do not start a new login.
3. Never re-login because token state is uncertain; `verify` is the source of truth.
4. Protect the SMS quota: each phone number receives at most five codes per day, so do not create duplicate login sessions.

After login, rerun `verify` once before continuing the requested workflow.
