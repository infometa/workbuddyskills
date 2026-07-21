# Agent Browser Plugin

Browser automation plugin for CodeBuddy using `vercel-labs/agent-browser` CLI, with first-class Windows support.

Upstream: https://github.com/vercel-labs/agent-browser

## What It Does

This skill teaches an agent to use `agent-browser` for browser automation:

- Open webpages
- Capture screenshots
- Extract rendered page content
- Click elements
- Fill forms
- Run simple web flow checks

## Platform Support

- macOS ARM64 / x64
- Linux ARM64 / x64
- Windows x64

## Files

- `SKILL.md`: Standard skill definition and usage guide.
- `references/windows-support.md`: Windows support notes.
- `references/troubleshooting.md`: Symptom-to-rule map for environment issues.
- `templates/install-windows.ps1`: Windows PowerShell install helper.
- `templates/install-unix.sh`: macOS / Linux install helper.
- `scripts/setup.sh`: Plugin lifecycle entry; auto-runs on first load.

## Plugin Lifecycle (inside marketplace)

When CodeBuddy loads this plugin for the first time, `scripts/setup.sh` runs automatically:

- On macOS / Linux it invokes `templates/install-unix.sh`.
- On Windows (Git Bash / MSYS / Cygwin) it invokes `templates/install-windows.ps1` via PowerShell.
- After a successful install it writes `$CODEBUDDY_PLUGIN_ROOT/.initialized` to skip reinstall on later loads.

If you are consuming this skill outside the marketplace, follow the manual steps under [Quick Install](#quick-install) instead.

## Quick Install

Windows PowerShell:

```powershell
npm install -g agent-browser
agent-browser install
```

macOS / Linux:

```bash
npm install -g agent-browser
agent-browser install
```

## Quick Test

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```
