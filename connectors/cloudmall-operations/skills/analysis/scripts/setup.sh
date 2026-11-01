#!/usr/bin/env bash
# Read-only dependency check. Never installs packages.
set -euo pipefail
python3 --version
node --version
node -e 'try { require("puppeteer-core"); } catch (_) { require("puppeteer"); }'
