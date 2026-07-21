#!/bin/bash
# agent-browser setup script
# Detects OS and delegates to the proper installer under templates/.
# Runs automatically when CodeBuddy loads this plugin for the first time.

set -e

PLUGIN_ROOT="${CODEBUDDY_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
INIT_FLAG="${PLUGIN_ROOT}/.initialized"

# Already initialized
if [ -f "$INIT_FLAG" ]; then
    exit 0
fi

# Already installed -> just mark initialized
if command -v agent-browser >/dev/null 2>&1; then
    echo "agent-browser is already installed"
    touch "$INIT_FLAG"
    exit 0
fi

# Detect Windows (Git Bash / MSYS / Cygwin environments on Windows host)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    PS1_SCRIPT="${PLUGIN_ROOT}/templates/install-windows.ps1"
    if [ ! -f "$PS1_SCRIPT" ]; then
        echo "install-windows.ps1 not found at $PS1_SCRIPT"
        exit 1
    fi
    echo "Detected Windows, running PowerShell installer..."
    if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_SCRIPT"
    else
        powershell -NoProfile -ExecutionPolicy Bypass -File "$PS1_SCRIPT"
    fi
    RC=$?
    if [ $RC -eq 0 ]; then
        touch "$INIT_FLAG"
    fi
    exit $RC
fi

# Unix (macOS / Linux)
UNIX_SCRIPT="${PLUGIN_ROOT}/templates/install-unix.sh"
if [ ! -f "$UNIX_SCRIPT" ]; then
    echo "install-unix.sh not found at $UNIX_SCRIPT"
    exit 1
fi

echo "Detected Unix, running install-unix.sh..."
bash "$UNIX_SCRIPT"
RC=$?
if [ $RC -eq 0 ]; then
    touch "$INIT_FLAG"
fi
exit $RC
