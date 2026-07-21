# Changelog

All notable changes to the plugin-finder plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-18

### Added
- Initial release of plugin-finder
- **Skill: plugin-discovery** - Core knowledge for plugin discovery and management
- **Command: search** - Intelligent plugin search with AI semantic matching
- **Command: install** - Manual plugin installation with batch support
- **Command: multi-run** - Multi-plugin parallel execution and comparison
- **Command: wish** - Plugin wish feature to request new plugins
- **Agent: plugin-recommender** - Autonomous plugin recommendation agent
- **Hook: UserPromptSubmit** - Auto-detect plugin needs and trigger recommendations
- **Script: search-plugins.sh** - Shell script for quick plugin searches
- Support for both CodeBuddy and Claude plugin ecosystems
- User configuration via .local.md file
- Comprehensive README with usage examples
- Configuration example file
- Plugin wish feedback mechanism to CodeBuddy team

### Features
- AI-powered semantic plugin matching (not just keyword matching)
- Multi-select UI for installing multiple plugins
- Batch installation support
- Detailed comparison reports for multi-plugin testing
- Automatic restart reminders after installation
- Configurable auto-recommendation behavior
- Search across all installed marketplaces
- Support for preferred marketplaces and plugins
- **Plugin wish system** - Users can request new plugins via email
- Automated wish email generation with detailed requirement analysis

### Documentation
- Complete README.md with feature overview
- Detailed skill documentation with references
- Command documentation with argument hints
- Agent documentation with triggering examples
- Configuration examples and usage guide
- CHANGELOG for version tracking

## [Unreleased]

### Added
- **Command: info** - View detailed plugin information including components, functionality, and implementation
- **Script: analyze-plugin-info.sh** - Analyze plugin structure and extract component metadata
- Support for viewing plugin details from all marketplaces (installed or not)
- Component-level breakdown (commands, agents, skills, hooks, mcp)
- Implementation overview extraction from README

### Features
- Comprehensive plugin information display
- Component statistics and detailed descriptions
- Support for both simple (`plugin-name`) and qualified (`plugin-name@marketplace`) queries
- Automatic marketplace search when marketplace not specified

### Planned
- Web UI for plugin browsing and management
- Plugin update notifications
- Plugin dependency resolution
- Favorite plugins list
- Recent plugins history
- Plugin usage analytics
- Custom plugin collections
- Team plugin recommendations

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security fixes
