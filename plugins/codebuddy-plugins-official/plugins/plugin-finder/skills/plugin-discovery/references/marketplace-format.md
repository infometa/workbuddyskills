# Marketplace Format Reference

Complete reference for marketplace.json structure and plugin metadata formats.

## Marketplace.json Structure

### Top-Level Fields

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Owner Name",
    "email": "owner@example.com"
  },
  "metadata": {
    "description": "Marketplace description",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [...]
}
```

**Fields:**
- `name` (required): Unique marketplace identifier (kebab-case)
- `owner` (required): Marketplace maintainer information
  - `name` (required): Maintainer name
  - `email` (optional): Contact email
- `metadata` (optional): Additional marketplace information
  - `description`: Marketplace purpose
  - `version`: Marketplace version
  - `pluginRoot`: Base directory for plugin sources
- `plugins` (required): Array of plugin entries

## Plugin Entry Structure

### Minimal Plugin Entry

```json
{
  "name": "plugin-name",
  "source": "./plugins/plugin-name",
  "description": "Plugin description"
}
```

### Complete Plugin Entry

```json
{
  "name": "plugin-name",
  "description": "Comprehensive plugin functionality description",
  "version": "1.2.0",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "source": "./plugins/plugin-name",
  "category": "productivity",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "tags": ["tag1", "tag2"],
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/user/plugin",
  "license": "MIT",
  "strict": true
}
```

**Plugin Fields:**

- `name` (required): Plugin identifier (kebab-case, no spaces)
- `source` (required): Plugin location (see Source Types below)
- `description` (required): What the plugin does
- `version` (optional): Semantic version (MAJOR.MINOR.PATCH)
- `author` (optional): Plugin author information
  - `name`: Author name
  - `email`: Contact email
  - `url`: Author website
- `category` (optional): Plugin classification
- `keywords` (optional): Search and discovery tags (array)
- `tags` (optional): Additional metadata (array)
- `homepage` (optional): Documentation URL
- `repository` (optional): Source code URL
- `license` (optional): SPDX license identifier
- `strict` (optional): Requires independent plugin.json (default: true)

## Source Types

### Relative Path

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin"
}
```

Plugin located relative to marketplace root.

### GitHub Repository

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/plugin-repo"
  }
}
```

Plugin hosted on GitHub.

### Git URL

```json
{
  "name": "git-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

Plugin at any Git URL.

### Git with Branch/Tag

```json
{
  "name": "versioned-plugin",
  "source": {
    "source": "git",
    "url": "https://github.com/user/plugin.git",
    "branch": "develop"
  }
}
```

Or:

```json
{
  "source": {
    "source": "git",
    "url": "https://github.com/user/plugin.git",
    "tag": "v1.2.0"
  }
}
```

## Categories

Standard plugin categories:

| Category | Description |
|----------|-------------|
| `development` | Development tools and language support |
| `productivity` | Workflow and productivity tools |
| `security` | Security analysis and checking |
| `testing` | Testing frameworks and tools |
| `database` | Database integration and management |
| `deployment` | Deployment and CI/CD tools |
| `design` | Design and UI tools |
| `monitoring` | Monitoring and observability |
| `learning` | Educational and learning tools |

## Known Marketplaces Structure

The `known_marketplaces.json` file tracks installed marketplaces:

### CodeBuddy Format

```json
{
  "marketplace-name": {
    "type": "git|directory|github",
    "source": {
      "source": "git|directory|github",
      "url": "https://...",
      "path": "/local/path",
      "repo": "owner/repo"
    },
    "installLocation": "/path/to/marketplace",
    "description": "Marketplace description",
    "lastUpdated": "2026-01-18T10:00:00.000Z",
    "autoUpdate": true|false,
    "manifest": {
      ...full marketplace.json content...
    }
  }
}
```

**Fields:**
- `type`: How marketplace is sourced (git, directory, github)
- `source`: Source location details
- `installLocation`: Local filesystem path
- `description`: Marketplace description
- `lastUpdated`: ISO timestamp of last update
- `autoUpdate`: Whether to auto-update marketplace
- `manifest`: Complete marketplace.json content (includes all plugins)

### Claude Format

```json
{
  "marketplace-name": {
    "source": {
      "source": "github",
      "repo": "owner/repo"
    },
    "installLocation": "/path/to/marketplace",
    "lastUpdated": "2026-01-18T10:00:00.000Z"
  }
}
```

Simpler structure, manifest may need to be loaded separately.

## Installed Plugins Structure (Claude Only)

The `~/.claude/plugins/installed_plugins.json` tracks installed plugins:

```json
{
  "version": 2,
  "plugins": {
    "plugin-name@marketplace-name": [
      {
        "scope": "user|project",
        "installPath": "/path/to/cached/plugin",
        "version": "1.0.0",
        "installedAt": "2026-01-18T10:00:00.000Z",
        "lastUpdated": "2026-01-18T10:00:00.000Z",
        "gitCommitSha": "abc123..." (if git source)
      }
    ]
  }
}
```

**Fields:**
- `version`: File format version
- `plugins`: Object keyed by "plugin-name@marketplace-name"
  - Array allows multiple installs (different versions/scopes)
  - `scope`: Installation scope (user or project)
  - `installPath`: Where plugin files are cached
  - `version`: Installed version
  - `installedAt`: Initial installation timestamp
  - `lastUpdated`: Last update timestamp
  - `gitCommitSha`: Git commit (if git source)

## Parsing Strategies

### Reading Marketplace Data

**Strategy 1: From known_marketplaces.json**
```bash
# CodeBuddy
cat ~/.codebuddy/plugins/known_marketplaces.json | jq '.[] | .manifest.plugins'

# Claude
cat ~/.claude/plugins/known_marketplaces.json | jq
```

Advantage: All data in one file (CodeBuddy), fast access.

**Strategy 2: From marketplace files directly**
```bash
# Find marketplace.json files
find ~/.codebuddy/plugins/marketplaces -name "marketplace.json"

# Read each
cat /path/to/marketplace/.codebuddy-plugin/marketplace.json
```

Advantage: Always current, no cache issues.

### Extracting Plugin Information

**Get all plugins from all marketplaces:**
```bash
for market in $(jq -r 'keys[]' ~/.codebuddy/plugins/known_marketplaces.json); do
  echo "Marketplace: $market"
  jq -r ".\"$market\".manifest.plugins[] | .name + \" - \" + .description" \
    ~/.codebuddy/plugins/known_marketplaces.json
done
```

**Search by keyword:**
```bash
jq -r '
  .[] | .manifest.plugins[] | 
  select(.keywords // [] | contains(["keyword"])) |
  .name
' ~/.codebuddy/plugins/known_marketplaces.json
```

**Filter by category:**
```bash
jq -r '
  .[] | .manifest.plugins[] | 
  select(.category == "productivity") |
  .name + " - " + .description
' ~/.codebuddy/plugins/known_marketplaces.json
```

## Schema Validation

### Required Fields Check

Plugin entry must have:
- `name` (string, kebab-case)
- `source` (string or object)

Marketplace must have:
- `name` (string, kebab-case)
- `owner.name` (string)
- `plugins` (array)

### Common Issues

**Issue 1: Invalid source**
```json
{
  "source": "invalid-format"
}
```
Must be relative path starting with `./` or source object.

**Issue 2: Missing required fields**
```json
{
  "name": "plugin"
  // Missing source
}
```
Both name and source required.

**Issue 3: Invalid name format**
```json
{
  "name": "My Plugin"  // Has spaces
}
```
Must be kebab-case, no spaces.

## Examples

### Minimal Marketplace

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "John Doe"
  },
  "plugins": [
    {
      "name": "simple-plugin",
      "source": "./plugins/simple-plugin",
      "description": "A simple plugin"
    }
  ]
}
```

### Full-Featured Marketplace

```json
{
  "name": "enterprise-tools",
  "owner": {
    "name": "Enterprise Team",
    "email": "team@enterprise.com"
  },
  "metadata": {
    "description": "Internal enterprise tools",
    "version": "2.1.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "code-analyzer",
      "description": "Advanced code analysis and quality metrics",
      "version": "1.5.0",
      "author": {
        "name": "Security Team",
        "email": "security@enterprise.com"
      },
      "source": "./plugins/code-analyzer",
      "category": "development",
      "keywords": ["analysis", "quality", "security"],
      "tags": ["internal", "required"],
      "homepage": "https://docs.enterprise.com/code-analyzer",
      "repository": "https://git.enterprise.com/tools/code-analyzer",
      "license": "Proprietary"
    },
    {
      "name": "deployment-tools",
      "description": "Automated deployment to production",
      "version": "2.0.0",
      "source": {
        "source": "git",
        "url": "https://git.enterprise.com/tools/deployment.git",
        "branch": "stable"
      },
      "category": "deployment",
      "keywords": ["deploy", "production", "automation"],
      "strict": true
    }
  ]
}
```

## Version History

- **v2** (current): Added `manifest` embedding in known_marketplaces.json (CodeBuddy)
- **v1**: Original format, separate marketplace files

## References

- Official schema: https://anthropic.com/claude-code/marketplace.schema.json
- Plugin specification: /Users/laurentzhou/CodeBuddy/plugin_marketplace/docs/specifications/claude-code-plugin-specification-zh.md
