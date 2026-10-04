# system member-password reset

Use when the user needs to reset one company member password.

Do not use it to change the current login's own password or when the company and target member have
not been explicitly identified.

The plaintext password is accepted only from stdin or a permission-protected local file. The CLI
encrypts it locally with the TA-compatible RSA public key and sends only `encrypted_password`.
Never place the password directly on argv, in JSON input, logs, or chat.

Command:

```bash
printf '%s\n' "$NEW_PASSWORD" | ae-cli system member-password reset --dry-run --company-id <company-id> --target-user-id <target-user-id> --password-stdin
printf '%s\n' "$NEW_PASSWORD" | ae-cli system member-password reset --company-id <company-id> --target-user-id <target-user-id> --password-stdin --yes
```

Capability id: `system.member_password.reset`.

Run `--dry-run` first, summarize the target and impact without reproducing ciphertext, then wait for
explicit user confirmation before rerunning the unchanged target with global `--yes`.

The response uses `ok`, `data`, and `meta`. Preserve `request_id` and `invocation_id` when present.

## Parameters

| Parameter | Required | Description |
|---|---|---|
| `--company-id` | Yes | Company ID. |
| `--target-user-id` | Yes | Target member user ID. |
| `--password-stdin` or `--password-file` | Yes | Protected plaintext source; never accepted directly on argv. |
