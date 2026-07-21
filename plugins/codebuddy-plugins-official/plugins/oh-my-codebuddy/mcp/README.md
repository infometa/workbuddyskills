# MCP Configuration

Model Context Protocol (MCP) servers configuration for CodeBuddy.

## Overview

This package includes 2 MCP servers from oh-my-codebuddy:

1. **context7** - Official documentation lookup
2. **grep_app** - Ultra-fast GitHub code search

## Configuration File

The MCP configuration is in `.mcp.json`:

```json
{
  "mcpServers": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp"
    },
    "grep_app": {
      "type": "remote",
      "url": "https://mcp.grep.app"
    }
  }
}
```

## Installation

### Option 1: Fresh Installation

If you don't have an existing `.mcp.json`:

```bash
cp .mcp.json ~/.codebuddy/.mcp.json
```

### Option 2: Merge with Existing

If you already have `.mcp.json`, manually merge:

1. Open your existing `~/.codebuddy/.mcp.json`
2. Add the servers from this package:

```json
{
  "mcpServers": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp"
    },
    "grep_app": {
      "type": "remote",
      "url": "https://mcp.grep.app"
    },
    // ... your existing servers ...
  }
}
```

## MCP Servers

### context7

**Purpose**: Official documentation lookup for popular libraries and frameworks

**URL**: `https://mcp.context7.com/mcp`

**Use Cases**:
- Find official documentation for libraries
- Get API reference information
- Look up best practices
- Find usage examples

**Example Usage**:
```
Ask @librarian to find React hooks documentation
```

The librarian agent will automatically use context7 to retrieve official docs.

---

### grep_app

**Purpose**: Ultra-fast GitHub code search across public repositories

**URL**: `https://mcp.grep.app`

**Use Cases**:
- Search for implementation examples
- Find code patterns in open source
- Discover usage examples
- Research how others solved problems

**Example Usage**:
```
Ask @librarian to find JWT authentication examples in GitHub
```

The librarian agent will use grep.app for fast code search.

---

## Verification

After installation, verify MCP servers are connected:

1. Restart CodeBuddy
2. Check CodeBuddy logs for MCP connection status
3. Try using agents that rely on MCPs (librarian)

## Troubleshooting

### MCP Not Connecting

1. **Check JSON format**:
   ```bash
   cat ~/.codebuddy/.mcp.json | jq
   ```
   Should parse without errors

2. **Verify URLs**:
   - context7: `https://mcp.context7.com/mcp`
   - grep_app: `https://mcp.grep.app`

3. **Check network**:
   ```bash
   curl -I https://mcp.context7.com/mcp
   curl -I https://mcp.grep.app
   ```

4. **Restart CodeBuddy**: MCPs are loaded on startup

### MCP Not Available in Agents

- Ensure agents are installed correctly
- Check that librarian agent is available
- Verify MCP servers appear in CodeBuddy settings

## Advanced Configuration

### Authentication

If MCP servers require authentication, add to config:

```json
{
  "mcpServers": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### Custom Timeout

```json
{
  "mcpServers": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "timeout": 30000
    }
  }
}
```

## See Also

- [MCP Specification](https://modelcontextprotocol.io/)
- [CodeBuddy MCP Documentation](https://code.codebuddy.com/docs/mcp)
- [oh-my-codebuddy MCP Source](../src/mcp/) - Original implementation


