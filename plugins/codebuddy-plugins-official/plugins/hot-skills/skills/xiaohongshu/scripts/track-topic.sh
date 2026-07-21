#!/bin/bash
# 小红书热点跟踪工具

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/track-topic.py" "$@"
