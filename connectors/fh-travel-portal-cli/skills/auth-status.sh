#!/bin/sh
# Launcher next to SKILL.md. Runs node on cli/cli.js. There is no fh executable.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd) || exit 1
node "$SCRIPT_DIR/cli/cli.js" --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth status
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "[fh] status failed exit=$RC. This file is next to SKILL.md."
  echo "[fh] It runs: node \"$SCRIPT_DIR/cli/cli.js\". node must be on PATH."
  echo "[fh] Do not search the disk. exit 3 means not logged in. Then run sh auth-login.sh in the foreground."
fi
exit "$RC"
