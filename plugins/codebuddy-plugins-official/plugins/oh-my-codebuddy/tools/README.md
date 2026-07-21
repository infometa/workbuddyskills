# Tools from oh-my-codebuddy

This directory contains documentation for tools implemented in the oh-my-codebuddy OpenCode plugin. These tools are **code-based implementations** and cannot be directly converted to CodeBuddy format.

## Available Tools

1. **LSP Tools** (11 tools) - Full IDE capabilities for code navigation and refactoring
   - See [LSP_TOOLS.md](LSP_TOOLS.md) for details

2. **AST-Grep Tools** (2 tools) - AST-aware code search and replacement
   - See [AST_GREP.md](AST_GREP.md) for details

3. **Session Manager Tools** (4 tools) - Navigate and search OpenCode session history
   - See [SESSION_MANAGER.md](SESSION_MANAGER.md) for details

## Important Notes

### For CodeBuddy Users

These tools are implemented as part of the oh-my-codebuddy OpenCode plugin. To use them in CodeBuddy, you would need:

1. **OpenCode Installation**: Install OpenCode (https://opencode.ai)
2. **Plugin Installation**: Install oh-my-codebuddy plugin
3. **CodeBuddy Migration**: Use OpenCode instead of CodeBuddy

### Tool Categories

| Category | Tool Count | Requires Plugin |
|----------|------------|-----------------|
| LSP | 11 | Yes (oh-my-codebuddy) |
| AST-Grep | 2 | Yes (oh-my-codebuddy) |
| Session Manager | 4 | Yes (oh-my-codebuddy) |
| Background Tasks | 3 | Yes (oh-my-codebuddy) |
| Interactive Bash | 1 | Yes (oh-my-codebuddy) |

## Alternative Approaches

If you want similar functionality in CodeBuddy without installing OpenCode:

1. **LSP Tools**: Some LSP functionality may be available through VS Code extensions or custom CodeBuddy plugins
2. **AST-Grep**: Can be used via command-line through bash commands
3. **Session Management**: May need custom implementation or third-party tools

## Recommendation

For the full experience of all agents, tools, and hooks working together, we recommend using **oh-my-codebuddy with OpenCode** rather than trying to replicate functionality in CodeBuddy.

See the main [README.md](../README.md) for more information about the complete oh-my-codebuddy system.


