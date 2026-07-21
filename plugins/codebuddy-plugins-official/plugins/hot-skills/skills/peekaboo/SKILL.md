---
name: peekaboo
description: Capture and automate macOS UI with the Peekaboo CLI.
---

# Peekaboo

Peekaboo is a full macOS UI automation CLI: capture/inspect screens, target UI elements, drive input, and manage apps/windows/menus.

## Features

Core: `bridge`, `capture`, `clean`, `config`, `image`, `learn`, `list`, `permissions`, `run`, `sleep`, `tools`
Interaction: `click`, `drag`, `hotkey`, `move`, `paste`, `press`, `scroll`, `swipe`, `type`
System: `app`, `clipboard`, `dialog`, `dock`, `menu`, `menubar`, `open`, `space`, `window`
Vision: `see`

## Quickstart
```bash
peekaboo permissions
peekaboo list apps --json
peekaboo see --annotate --path /tmp/peekaboo-see.png
peekaboo click --on B1
peekaboo type "Hello" --return
```

## Targeting parameters
- App/window: `--app`, `--pid`, `--window-title`, `--window-id`, `--window-index`
- Snapshot: `--snapshot` (ID from `see`)
- Element/coords: `--on`/`--id`, `--coords x,y`

## Examples
```bash
peekaboo see --app Safari --annotate --path /tmp/see.png
peekaboo click --on B3 --app Safari
peekaboo type "user@example.com" --app Safari
peekaboo image --mode screen --screen-index 0 --retina --path /tmp/screen.png
peekaboo app launch "Safari" --open https://example.com
peekaboo menu click --app Safari --item "New Window"
peekaboo hotkey --keys "cmd,shift,t"
```

Notes
- Requires Screen Recording + Accessibility permissions.
- Use `peekaboo see --annotate` to identify targets before clicking.
