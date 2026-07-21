---
name: agent-browser
version: 1.3.0
description: Use this skill when the user needs browser automation, including opening web pages, taking screenshots, extracting page content, clicking elements, filling forms, or testing web flows. This skill uses the open source vercel-labs/agent-browser CLI and supports macOS, Linux, and Windows x64.
---

# Agent Browser

Use `agent-browser` CLI for full browser automation tasks. It is suitable when a page needs JavaScript rendering, real browser interaction, screenshots, or form automation.

Upstream project: https://github.com/vercel-labs/agent-browser

## Platform Support

`vercel-labs/agent-browser` provides native builds for:

- macOS ARM64 / x64
- Linux ARM64 / x64
- Windows x64

Windows support in this skill targets Windows 11 x64 with PowerShell and Node.js 18+.

## Prerequisites

- Node.js 18+
- npm available in PATH
- Network access to install `agent-browser` and download Chromium
- About 500 MB free disk space for Chromium
- **The `node` binary on PATH must actually execute code**, not just print a version. `agent-browser` spawns a Node child process internally; if that Node is broken, the daemon will crash with no useful output even when `agent-browser --version` works.

  Quick check:
  ```bash
  node -e "console.log('ok')"
  ```
  If this does not print `ok` (SIGILL / exit 133 / any crash), the Node on PATH is unusable. Fix it, or run `agent-browser` with a known-good Node prepended to PATH for that command only:
  ```bash
  PATH="/path/to/working-node/bin:$PATH" agent-browser open <url>
  ```
  Inspect which Node would be picked up with `which -a node`.

## Installation

> Inside the CodeBuddy marketplace, `scripts/setup.sh` auto-runs these steps on first load. The commands below are for manual setup or reinstall.

### Windows PowerShell

```powershell
npm install -g agent-browser
agent-browser install
```

### macOS / Linux

```bash
npm install -g agent-browser
agent-browser install
```

### Linux missing dependencies

```bash
agent-browser install --with-deps
```

## Required Command Sequence

The current upstream `agent-browser` CLI does not require a separate `launch` command. `agent-browser open <url>` starts or connects to the browser daemon automatically.

Always follow this order:

1. Open target URL.
2. Wait for page load when needed.
3. Inspect page with `snapshot` or `snapshot -i`.
4. Interact with the page.
5. Close browser when done.

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

## Session Model

`agent-browser` runs a persistent background daemon. Understand this before planning multi-step tasks:

- The first `agent-browser open` starts a daemon; subsequent commands auto-connect to the same daemon.
- Within one session, cookies, localStorage and login state are preserved across commands.
- Multiple `open` calls in the same session navigate the existing browser (no need to close between URLs).
- `agent-browser close` ends the daemon. Only call it when the whole task is finished, not between steps of the same task.

Implication: for a task that visits N URLs, do **one** `open ... snapshot ...` chain per URL and **one** `close` at the very end, not N `open`/`close` pairs.

## Execution Principles

Apply these when running command sequences, especially in multi-step tasks:

- **`close` is mandatory in finally**: whether the task succeeds or fails midway, always run `agent-browser close` at the end to avoid zombie daemons and leaked Chromium processes.
- **`wait` is optional and degradable**: `wait --load networkidle` can hang on SPAs that never go idle. If a wait stalls, fall back to `wait --load load` or skip waiting and `snapshot` directly. Do not block the whole task on `wait`.
- **Reuse the daemon**: in the same task, do not `close` between intermediate steps. Open once, navigate/interact multiple times, close at the end.
- **Prefer `snapshot -i` for interaction**: when you need to click or type, get interactive element IDs first via `snapshot -i`, then act on them. Do not guess CSS selectors blindly.
- **Use agent-browser's own install channel**: for Chromium, runtime, or dependency issues, stay inside agent-browser's own tooling — `agent-browser install`, or the `playwright-core` CLI bundled under `$(npm root -g)/agent-browser/node_modules/playwright-core`. Do not run `npx playwright install` in parallel; it can fetch a revision that does not match what agent-browser expects and may time out downloading browsers agent-browser never uses.
- **Fail fast on environment errors**: if the very first `open` fails with daemon / Chromium / SIGILL errors, do not retry the same command repeatedly. Verify the Prerequisite Node check, then consult `references/troubleshooting.md`.

## When NOT to Use

`agent-browser` launches a real Chromium and consumes hundreds of MB plus a few seconds of cold start. Pick the lighter tool whenever possible:

| Need | Recommended tool |
|------|------------------|
| Fetch static HTML, plain text, or markdown of a page | WebFetch |
| Call a JSON / REST API | curl, fetch, or HTTP client |
| Read content already present in raw HTML | WebFetch |
| Render JavaScript-driven pages before reading | agent-browser |
| Click, type, login, or any multi-step interaction | agent-browser |
| Take a visual screenshot for review | agent-browser |
| Reproduce a real user flow end-to-end | agent-browser |

Rule of thumb: if `curl <url>` already contains the target content in plain HTML, do not start `agent-browser`.

## Essential Commands

| Command | Description |
|---------|-------------|
| `agent-browser open <url>` | Start or connect to the browser daemon and navigate to a URL. |
| `agent-browser wait --load networkidle` | Wait until network activity is idle. Useful after opening dynamic pages. |
| `agent-browser snapshot` | Get page content as text. |
| `agent-browser snapshot -i` | Get page content with element IDs for interaction. |
| `agent-browser screenshot` | Take a screenshot. |
| `agent-browser click <selector>` | Click an element. |
| `agent-browser type <selector> <text>` | Type text into an input. |
| `agent-browser close` | Close browser and free resources. |

## Common Workflows

### View webpage content

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

### Take screenshot

```bash
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser screenshot
agent-browser close
```

### Fill form and submit

First get interactive element IDs:

```bash
agent-browser open https://example.com/login
agent-browser wait --load networkidle
agent-browser snapshot -i
```

Then interact with stable selectors or element IDs:

```bash
agent-browser type "#username" "myuser"
agent-browser type "#password" "mypassword"
agent-browser click "#submit"
agent-browser close
```

### Extract data from a JavaScript-rendered page

```bash
agent-browser open https://example.com/data
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

## Windows Notes

On Windows, prefer PowerShell for installation and verification:

```powershell
npm install -g agent-browser
agent-browser install
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser close
```

If the command is not found after installation, restart PowerShell or confirm npm global bin is in PATH:

```powershell
npm config get prefix
```

## Troubleshooting

For environment problems (daemon won't start, Chromium revision mismatch, SIGILL / Exit 133, install timeouts, etc.), see [`references/troubleshooting.md`](./references/troubleshooting.md). It is organized by symptom so you can diagnose against the actual error message instead of following a fixed script.

Quick checks before going there:

- `agent-browser` not found after install: restart shell, confirm npm global bin is in PATH (`npm config get prefix`).
- Linux browser launch missing system libs: `agent-browser install --with-deps`.
- Always run `agent-browser close` when a task ends, even on failure paths.
