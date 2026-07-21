---
name: himalaya
description: "CLI to manage emails via IMAP/SMTP. Use `himalaya` to list, read, write, reply, forward, search, and organize emails from the terminal. Supports multiple accounts and message composition with MML (MIME Meta Language)."
---

# Himalaya Email CLI

Himalaya is a CLI email client that lets you manage emails from the terminal using IMAP, SMTP, Notmuch, or Sendmail backends.

## References

- `references/configuration.md` (config file setup + IMAP/SMTP authentication)
- `references/message-composition.md` (MML syntax for composing emails)

## Prerequisites

1. Himalaya CLI installed (`himalaya --version` to verify)
2. A configuration file at `~/.config/himalaya/config.toml`
3. IMAP/SMTP credentials configured (password stored securely)

## Configuration Setup

Run the interactive wizard to set up an account:
```bash
himalaya account configure
```

Or create `~/.config/himalaya/config.toml` manually:
```toml
[accounts.personal]
email = "you@example.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "imap.example.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@example.com"
backend.auth.type = "password"
backend.auth.cmd = "pass show email/imap"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.example.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@example.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "pass show email/smtp"
```

## Common Operations

### List Folders
```bash
himalaya folder list
```

### List Emails
```bash
himalaya envelope list
himalaya envelope list --folder "Sent"
himalaya envelope list --page 1 --page-size 20
```

### Search Emails
```bash
himalaya envelope list from john@example.com subject meeting
```

### Read an Email
```bash
himalaya message read 42
himalaya message export 42 --full
```

### Reply/Forward
```bash
himalaya message reply 42
himalaya message reply 42 --all
himalaya message forward 42
```

### Write a New Email
```bash
himalaya message write
himalaya message write -H "To:recipient@example.com" -H "Subject:Test" "Message body here"
```

### Move/Copy/Delete
```bash
himalaya message move 42 "Archive"
himalaya message copy 42 "Important"
himalaya message delete 42
```

### Flags
```bash
himalaya flag add 42 --flag seen
himalaya flag remove 42 --flag seen
```

## Multiple Accounts
```bash
himalaya account list
himalaya --account work envelope list
```

## Attachments
```bash
himalaya attachment download 42
himalaya attachment download 42 --dir ~/Downloads
```

## Output Formats
```bash
himalaya envelope list --output json
himalaya envelope list --output plain
```

## Tips

- Use `himalaya --help` or `himalaya <command> --help` for detailed usage.
- Message IDs are relative to the current folder; re-list after folder changes.
- For composing rich emails with attachments, use MML syntax (see `references/message-composition.md`).
- Store passwords securely using `pass`, system keyring, or a command that outputs the password.
