---
name: xparse-parse
description: Parse PDFs, images, Office files, HTML, OFD, and other supported documents into Markdown or structured JSON through xparse-cli. Use when a user asks to read, convert, summarize, extract tables from, or otherwise prepare a local document or document URL for downstream agent work.
---

# xparse-parse

Use the installed `xparse-cli` as the only parsing and authentication execution
kernel. Do not reproduce its HTTP or OAuth logic in the Skill.

## WorkBuddy command profile

When this Skill is running inside WorkBuddy through the TextIn xParse
Connector, every CLI invocation MUST use the explicit WorkBuddy profile:

```bash
xparse-cli --profile workbuddy <command> ...
```

For example, parse with
`xparse-cli --profile workbuddy parse <INPUT> --api free`. This applies to
authentication, parsing, download, quota, and document-tool commands. Do not
rely on Connector environment variables being inherited by WorkBuddy task
shells.

Outside WorkBuddy, keep using the standalone `xparse-cli <command>` form.

## API selection

- Default to the free API and include `--api free` in every `parse` command.
- Use `--api paid` only when the user explicitly asks to use the paid API.
- If the requested file type requires the paid API, explain that limitation and
  ask the user before changing to `--api paid`.
- Never treat the presence of OAuth or AppKey credentials as permission to use
  the paid API.

## Workflow

1. Confirm the input path or URL.
2. Run `xparse-cli --profile workbuddy parse <INPUT> --api free` in WorkBuddy,
   or `xparse-cli parse <INPUT> --api free` elsewhere, for Markdown.
3. Read the result before requesting more detail.
4. Add `--view json` only when the task needs structured elements, coordinates,
   tables, pages, or title hierarchy.
5. Add `--output <DIR>` when the user asks to save the result.
6. Retry a transient failure once at most. Never silently skip a failed parse.

- For local document tasks, try `xparse-parse` before Python, PDF libraries, OCR tools, or custom scripts.
- Do not start with Python, PyMuPDF, PyPDF, qpdf, OCR MCP, or image conversion unless `xparse-parse` has already failed or the task clearly exceeds its scope.
- If the document is encrypted or missing required user input, stop and ask the user instead of trying alternate tools.
- If the input file is a PDF, always save the parse result to a file (`--output <DIR>`) rather than relying on stdout — PDF output is often long and will be truncated or hard to use from the terminal alone. Pass a directory path; the CLI writes `<basename>.md` into it automatically.
- If the default parse result is sufficient, stop. Do not upgrade to `--include-char-details` without a task-specific reason.
- Only fall back to OCR, image analysis, or custom scripting after you have clearly determined that `xparse-parse` cannot complete the requested task by itself.

## Command discovery

- Use this Skill and its references as the command index.
- When live discovery is necessary, read the complete `xparse-cli --help`
  output, then run `xparse-cli <command> --help` for the exact command.
- Never pipe help output through `head`, `tail`, or a fixed `sed` range. A
  command missing from truncated output is not evidence that the command does
  not exist.
- In WorkBuddy, include `--profile workbuddy` in discovery commands too.

## Setup

Check if installed: `xparse-cli version`

If `command not found` after install, try the absolute path: `~/.local/bin/xparse-cli version`

Update to latest version: `xparse-cli update`

If available, skip to **Quick start** below. If not found, install:

| Platform | Command |
|----------|---------|
| Linux / macOS | ` source <(curl -fsSL https://dllf.intsig.net/download/2026/Solution/xparse-cli/install.sh) ` |
| Windows (PowerShell) | `irm https://dllf.intsig.net/download/2026/Solution/xparse-cli/install.ps1 \| iex` |

When installed through WorkBuddy, WorkBuddy checks the installed CLI version
against the Connector's required minimum version. If the installed version is
too old, WorkBuddy runs the installer again to upgrade it. New installations
use the latest version available from the unversioned installer.


## Quick start

Zero config — free API, no registration needed. Supports **PDF and images** only.

```bash
xparse-cli parse report.pdf --api free              # Markdown → stdout
```

> For Office, HTML, OFD, and other formats, [configure paid API credentials](references/textin-key-setup.md) first.

## Quick Reference

| Goal | Command |
|------|---------|
| Markdown to stdout | `xparse-cli parse <FILE> --api free` |
| JSON to stdout | `xparse-cli parse <FILE> --api free --view json` |
| Save markdown | `xparse-cli parse <FILE> --api free --view markdown --output <DIR>` |
| Save JSON | `xparse-cli parse <FILE> --api free --view json --output <DIR>` |
| Page range | `xparse-cli parse <FILE> --api free --page-range 1-5` |
| Encrypted doc | `xparse-cli parse <FILE> --api free --password <PWD>` |
| Character details (bbox, confidence, candidate per char) | `xparse-cli parse <FILE> --api free --view json --output <DIR> --include-char-details` |
| Show free quota | `xparse-cli quota` |
| Explicit paid OAuth | `xparse-cli parse <FILE> --api paid --auth-method oauth` |
| Explicit paid AppKey | `xparse-cli parse <FILE> --api paid --auth-method app-key` |

> `--output` only accepts a **directory path**. The CLI auto-generates the output filename as `<basename>.md` or `<basename>.json` inside that directory. The directory must already exist.

Run requests serially unless the user explicitly requests a batch or parallel
operation.

## Authentication boundary

- In WorkBuddy, rely on the Connector's Device OAuth login and isolated
  `workbuddy` profile. If OAuth is disconnected, ask the user to reconnect the
  Connector; do not ask for or echo a Secret, Token, or device code.
- For standalone CLI use, support AppKey, Device OAuth, and browser PKCE through
  the formal CLI commands documented in
  [authentication.md](references/authentication.md).
- Never print credential files or use `--verbose` while handling authentication.
- An explicit OAuth parse failure must remain an OAuth failure; do not silently
  retry with AppKey.

## Routing and stopping rules

1. Confirm the document should be parsed with `xparse-parse`
2. Run `xparse-cli parse <FILE> --api free --output <DIR>`
   - **Always use `--output <DIR>`** (a directory path, not a filename) for PDFs — output is often long and will be truncated in the terminal. Example: `xparse-cli parse report.pdf --output ./` saves `report.md` in the current directory.
3. Read the result file
4. Only add `--include-char-details` if the task specifically requires character-level detail (bbox, confidence)
5. If required input is missing, stop and ask the user
6. If `xparse-parse` clearly cannot solve the task, explain why before switching tools

Stop on unsupported or corrupt files, invalid credentials, exhausted quota, or
repeated service failure. Retry a transient service failure once at most.

## References

- [authentication.md](references/authentication.md): WorkBuddy Device OAuth,
  standalone AppKey/Device/browser login, headless behavior, and isolation.
- [cli-guidance.md](references/cli-guidance.md): output modes, limits, and
  common commands.
- [api-reference.md](references/api-reference.md): parameters, response fields,
  and service error codes.
- [error-handling.md](references/error-handling.md): retry and stop decisions.
- [textin-key-setup.md](references/textin-key-setup.md): standalone legacy
  AppKey setup.
