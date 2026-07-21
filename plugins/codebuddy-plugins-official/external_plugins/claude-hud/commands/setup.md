---
description: Configure claude-hud as your Claude Code statusline
---

# Claude HUD Setup

Configure claude-hud as your Claude Code statusline by adding the following configuration to your settings.

## Configuration

Add this to your `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node ${CLAUDE_PLUGIN_ROOT}/dist/index.js"
  }
}
```

## What This Does

The HUD displays real-time session information:

- **Session Info**: Model name, context usage bar (color-coded), config counts, session duration
- **Tool Activity**: Running tools with spinner, completed tools with counts
- **Agent Tracking**: Active subagents with descriptions and runtime
- **Todo Progress**: Current task and completion metrics

## Manual Setup

If automatic configuration doesn't work, you can manually:

1. Open `~/.claude/settings.json`
2. Add or update the `statusLine` section
3. Restart Claude Code

## Troubleshooting

If the HUD doesn't appear:

1. Ensure Node.js 18+ is installed
2. Check that the plugin is properly installed
3. Verify the statusLine configuration in settings.json
4. Try running `node ${CLAUDE_PLUGIN_ROOT}/dist/index.js` manually to check for errors

## First-Time Build

If this is a fresh installation, build the TypeScript:

```bash
cd ${CLAUDE_PLUGIN_ROOT}
npm install
npm run build
```
