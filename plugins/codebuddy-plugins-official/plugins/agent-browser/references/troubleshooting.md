# Troubleshooting

This page does not re-explain every possible failure. It maps observed symptoms back to the two rules that would have prevented them:

- **Prerequisite**: `node -e "console.log('ok')"` must print `ok`. If not, the Node on PATH is broken; override PATH for the command.
- **Execution Principle**: use agent-browser's own install channel. Do not run `npx playwright install` in parallel.

If a symptom is not listed here, read the actual error, then ask: does this violate the Prerequisite, the Execution Principle, or neither?

---

## Symptom → Rule

| Symptom | Which rule was violated | Action |
|---|---|---|
| Exit 133 / SIGILL / "Illegal instruction" | Prerequisite (Node on PATH is broken) | Run the Node check. If it fails, prepend a working Node to PATH for this command: `PATH="/path/to/working-node/bin:$PATH" agent-browser ...` |
| `Daemon process exited during startup with no error output` | Usually Prerequisite (the Node the daemon spawns is broken), even if `agent-browser --version` works | Run the Node check. `--debug` often shows nothing here because the child Node crashes before producing output. |
| `browserType.launch: Executable doesn't exist` / mismatched Chromium revision | Execution Principle (install channel) | Re-run `agent-browser install`. If still mismatched, use the bundled CLI: `node "$(npm root -g)/agent-browser/node_modules/playwright-core/cli.js" install chromium` (Windows path: `$(npm root -g)\agent-browser\node_modules\playwright-core\cli.js`) |
| `npx playwright install` SIGTERM / timeout | Execution Principle (wrong channel) | Stop using `npx playwright install`. Go back to `agent-browser install` or the bundled `playwright-core` CLI above. |
| `agent-browser` command not found after install | Neither rule, shell/PATH issue | Restart the shell. Verify `npm config get prefix`; ensure its `bin` (Unix) or root (Windows) is on PATH. |
| Linux browser launch fails with missing system libraries | Neither rule, OS dependencies | `agent-browser install --with-deps`, or install the missing libs via the system package manager. |
| `scripts/setup.sh` finished but `agent-browser` is still "command not found" | Neither rule, shell PATH was not refreshed | Restart the shell or open a new terminal; confirm `agent-browser --version` works there before continuing with the workflow. |

---

## Notes

- `agent-browser --version` passing is not proof that the environment works. The version command does not spawn the Node child process that runs the daemon; the Prerequisite check (`node -e`) does.
- `file /path/to/node` showing `arm64` is not proof that Node executes correctly. The Mach-O / ELF header only tells the loader it can load the binary; the Prerequisite check is the authoritative test.
- This skill does not pin Node, npm, or Chromium versions. Pin nothing the runtime does not strictly require.
- Always end any task with `agent-browser close`, even after failures.
