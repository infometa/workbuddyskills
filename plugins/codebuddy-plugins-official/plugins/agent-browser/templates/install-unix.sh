#!/usr/bin/env bash
set -euo pipefail

if command -v agent-browser >/dev/null 2>&1; then
    echo "agent-browser is already installed"
    exit 0
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Please install Node.js 18+ first: https://nodejs.org/"
    exit 1
fi

echo "Installing agent-browser..."
npm install -g agent-browser

echo "Installing browser runtime..."
agent-browser install

echo "agent-browser installation completed"
