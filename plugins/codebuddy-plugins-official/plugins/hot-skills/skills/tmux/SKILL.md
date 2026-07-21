---
name: tmux
description: Remote-control tmux sessions for interactive CLIs by sending keystrokes and scraping pane output.
---

# tmux Skill

Use tmux only when you need an interactive TTY. Prefer bash background mode for long-running, non-interactive tasks.

## Quickstart (isolated socket)

```bash
SOCKET_DIR="${TMPDIR:-/tmp}/codebuddy-tmux-sockets"
mkdir -p "$SOCKET_DIR"
SOCKET="$SOCKET_DIR/codebuddy.sock"
SESSION=codebuddy-python

tmux -S "$SOCKET" new -d -s "$SESSION" -n shell
tmux -S "$SOCKET" send-keys -t "$SESSION":0.0 -- 'PYTHON_BASIC_REPL=1 python3 -q' Enter
tmux -S "$SOCKET" capture-pane -p -J -t "$SESSION":0.0 -S -200
```

## Socket convention

- Default socket dir: `${TMPDIR:-/tmp}/codebuddy-tmux-sockets`
- Default socket path: `"$SOCKET_DIR/codebuddy.sock"`

## Targeting panes

- Target format: `session:window.pane` (defaults to `:0.0`)
- Keep names short; avoid spaces.

## Finding sessions

- List sessions: `{baseDir}/scripts/find-sessions.sh -S "$SOCKET"`
- Scan all sockets: `{baseDir}/scripts/find-sessions.sh --all`

## Sending input safely

- Literal sends: `tmux -S "$SOCKET" send-keys -t target -l -- "$cmd"`
- Control keys: `tmux -S "$SOCKET" send-keys -t target C-c`

## Watching output

- Capture recent: `tmux -S "$SOCKET" capture-pane -p -J -t target -S -200`
- Wait for prompts: `{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern'`

## Cleanup

- Kill session: `tmux -S "$SOCKET" kill-session -t "$SESSION"`
- Kill all: `tmux -S "$SOCKET" kill-server`

## Helper: wait-for-text.sh

```bash
{baseDir}/scripts/wait-for-text.sh -t session:0.0 -p 'pattern' [-F] [-T 20] [-i 0.5] [-l 2000]
```
