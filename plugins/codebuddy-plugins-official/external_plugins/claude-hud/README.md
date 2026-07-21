# Claude HUD

Real-time statusline HUD for Claude Code that displays context usage, tool activity, agent tracking, and todo progress.

## Features

- **Session Info**: Model name, context usage bar (color-coded), config counts, session duration
- **Tool Activity**: Running tools with spinner, completed tools with counts
- **Agent Tracking**: Active subagents with descriptions and runtime
- **Todo Progress**: Current task and completion metrics

## Installation

Install from the BuildWithClaude marketplace:

```bash
/plugin marketplace add davepoon/buildwithclaude
/plugin install claude-hud
```

Then run the setup command:

```bash
/claude-hud:setup
```

## Manual Configuration

Add this to your `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node /path/to/plugin/dist/index.js"
  }
}
```

## Building from Source

```bash
cd plugins/claude-hud
npm install
npm run build
```

## Requirements

- Claude Code v1.0.80 or later
- Node.js 18+

## Credits

Based on [claude-hud](https://github.com/jarrodwatts/claude-hud) by Jarrod Watts.

## License

MIT
