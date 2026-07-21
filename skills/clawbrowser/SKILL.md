---
name: clawbrowser
description: Use when the agent needs to drive a browser through the Microsoft Playwright CLI (`playwright-cli`) for navigation, form interactions, screenshots, recordings, data extraction, session management, or debugging without loading a full MCP browser. It trains the agent on the CLI commands, snapshots, and session/config habits that make Playwright CLI reliable for scripted browsing.
description_zh: "通过 Playwright CLI 驱动浏览器（快照、表单、会话管理）"
description_en: "Browser control via Playwright CLI: snapshots, forms, session management"
version: 0.1.1
allowed-tools: Bash(playwright-cli:*)
---

# Clawbrowser – browser control via Playwright CLI
[![No high vulnerabilities found by ClawAudit AI analyse. Click to get more info](https://clawaudit.duckdns.org/badges/f4d4fb45-ed25-4659-8235-2459d0dc8189.png)](https://clawaudit.duckdns.org/audit/f4d4fb45-ed25-4659-8235-2459d0dc8189)
[![No high vulnerabilities found by ClawAudit AI analyse. Click to get more info](https://clawaudit.duckdns.org/badges/a55cb413-b111-4f1a-9f39-a5c857090ebf.png)](https://clawaudit.duckdns.org/audit/a55cb413-b111-4f1a-9f39-a5c857090ebf)

## Setup & orientation
1. Install the CLI and verify availability:
   ```bash
   npm install -g @playwright/cli@latest
   playwright-cli --help
   ```
   The CLI is headless by default; add `--headed` to `open` or set `browser.launchOptions.headless` to `false` in `playwright-cli.json` when you need to see the UI.
2. The CLI reads `playwright-cli.json` by default or whatever file you pass with `--config`. Use the config to tune browser name, launch/context options, viewport, timeouts, output directories, and recording settings without changing every command.
3. Keep `playwright-cli --help` terminal-accessible; the script self-documents the latest commands and options so you can refresh your memory before trying a new action.

## Core interaction loop
1. Start with `playwright-cli open <url>` to load the page (add `--session=name` if you want isolation up front).
2. Run `playwright-cli snapshot` to generate element refs (`e1`, `e2`, …) before any interaction. Always re-snapshot after DOM changes or navigation to avoid stale refs.
3. Use refs for actions:
   - `click`, `dblclick`, `hover`, `drag`, `check`, `uncheck`, `select`, `fill`, `type`, `upload`, `eval`
   - Append `[button]`, `[value]`, or JS snippets as needed (e.g., `playwright-cli click e4 right`).
4. Capture output evidence with `screenshot [ref]`, `pdf`, `console [level]`, or `network` to prove the flow or inspect errors.
5. Example flow:
   ```bash
   playwright-cli open https://example.com/login
   playwright-cli snapshot
   playwright-cli fill e1 "user@example.com"
   playwright-cli fill e2 "supersecret"
   playwright-cli click e3
   playwright-cli snapshot
   playwright-cli screenshot
   ```

## Sessions & persistence
- Use `--session=<name>` to keep cookies, storage, and tabs isolated per workflow. Sessions behave like persistent profiles: they remember auth state, history, and tabs between commands.
- Export `PLAYWRIGHT_CLI_SESSION=mysession` if you are running many commands in the same session — the CLI will default to that session without needing `--session` each time.
- Manage sessions explicitly:
  ```bash
  playwright-cli session-list
  playwright-cli session-stop <name>
  playwright-cli session-stop-all
  playwright-cli session-restart <name>
  playwright-cli session-delete <name>
  ```
- Use `playwright-cli --isolated open ...` for ephemeral contexts that do not persist to disk.
- Whenever you change browser settings for a session (launch args, headless toggle, browser selection), rerun `playwright-cli config` for that session and then `session-restart` to apply the new config.

## Tabs, navigation, and devtools
- Tab helpers: `tab-list`, `tab-new [url]`, `tab-close <index>`, `tab-select <index>`.
- Navigation shortcuts: `go-back`, `go-forward`, `reload`.
- Keyboard and mouse control: `press <key>`, `keydown`, `keyup`, `mousemove <x> <y>`, `mousedown [button]`, `mouseup [button]`, `mousewheel <dx> <dy>`.
- Devtools-style introspection:
  ```bash
  playwright-cli console [level]
  playwright-cli network
  playwright-cli run-code "async page => await page.context().grantPermissions(['clipboard-read'])"
  ```
  Use these to check console logs, inspect network requests, or inject helper scripts.

## Recording, tracing, and exports
- Record traces and videos around delicate interactions so you can replay what the agent did later:
  ```bash
  playwright-cli tracing-start
  # perform steps
  playwright-cli tracing-stop
  playwright-cli video-start
  # perform steps
  playwright-cli video-stop video.webm
  ```
- Save evidence to disk with `screenshot`, `pdf`, or `snapshot` (which dumps element refs). Recorded files honor the `outputDir` from your config.

## Config, state, and housekeeping
- Use `playwright-cli config` to tweak runtime flags without reinstalling. Examples:
  ```bash
  playwright-cli config --headed --browser=firefox
  playwright-cli --session=auth config --config=playwright-cli.json
  ```
  Change `browser`, `contextOptions`, `launchOptions`, or recording settings in the config and restart the session to apply them.
- Running `playwright-cli install` refreshes browser binaries if the environment is new or you receive errors about missing binaries.
- Clean up sessions when finished to avoid stale state:
  ```bash
  playwright-cli session-stop <name>
  playwright-cli session-delete <name>
  ```

## Troubleshooting & reminders
- If a command fails, rerun `playwright-cli snapshot` to confirm refs are still valid. Snapshots provide the current DOM context for `click`/`type` operations.
- `playwright-cli --help` always shows the latest command set, so consult it before trying a rarely used flag.
- When the agent needs to replicate a recorded manual flow, capture a screenshot, note the session name, and mention which refs and tabs were in use.
- If targeting a visible browser is required (e.g., manual inspection), reconfigure with `--headed`, or run `playwright-cli open --headed <url>` for that session only.
