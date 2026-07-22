# Platform Authentication

## Required References

- `language-policy.md`
- `cli/cli-reference.md#authentication`

## Verify Before Login

Use `scripts/shifu-cli.py`; never read tokens directly, construct authentication headers, or make raw platform API calls. Write every user-facing login prompt and failure explanation according to `language-policy.md`.

Run `verify` before deciding whether login is needed:

- Exit `0`: continue the requested platform operation without logging in.
- Exit `1`: run one SMS login session.
- Exit `2`: report a network or service problem and retry `verify` later; do not send an SMS code.

If any authenticated command returns token error `1001`, `1004`, or `1005`, run `verify` and apply the same decision again. After a successful login, run `verify` once before continuing.

## Agent SMS Login Flow

Protect the SMS quota: one phone number can receive at most five codes per day. Send one code per login session unless the user has entered three consecutive wrong codes.

1. In one short turn, explain that login uses SMS without a password, a four-digit code will arrive, the user should reply with it next, the saved local token completes login, and a new phone number creates an account on first use. Ask for the phone number in that same turn.
2. Run `login --phone <phone>` exactly once.
3. Ask only for the four-digit code.
4. Run `login --phone <phone> --sms-code <code>`.
5. On success, run `verify` once and continue the original operation.

Do not insert readiness checks, account-status questions, acknowledgements, recaps, or other pauses between these steps. Each user turn supplies only the next required value.

## SMS Failure Handling

| Result | Agent action |
| --- | --- |
| SMS send succeeds | Wait for the code; do not send another SMS. |
| User asks to resend before entering three wrong codes | Explain that delivery can take 60 seconds and wait. |
| `smsSendTooFrequent` | Wait 60 seconds, then retry the same command without asking for the phone again. |
| First or second wrong code | Ask the user to re-enter the code; do not resend. |
| Third consecutive wrong code | Run `login --phone <phone>` once more; this is the final SMS for the session. |
| Login or verification has a network failure | Stop the login attempt and retry `verify` later; do not spend another SMS slot. |
