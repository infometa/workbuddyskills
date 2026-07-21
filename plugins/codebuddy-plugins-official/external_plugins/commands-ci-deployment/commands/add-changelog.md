---
description: Generate and maintain project changelog
category: ci-deployment
argument-hint: 1. **Changelog Format (Keep a Changelog)**
allowed-tools: Bash(git *), Bash(npm *)
---

# Add Changelog Command

Generate and maintain project changelog

## Instructions

Setup and maintain changelog following these steps: **$ARGUMENTS**

1. **Changelog Format (Keep a Changelog)**
   ```markdown
   # Changelog
   
   All notable changes to this project will be documented in this file.
   
   The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
   and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
   
   ## [Unreleased]
   ### Added
   - New features
   
   ### Changed
   - Changes in existing functionality
   
   ### Deprecated
   - Soon-to-be removed features
   
   ### Removed
   - Removed features
   
   ### Fixed
   - Bug fixes
   
   ### Security
   - Security improvements
   ```

2. **Version Entries**
   ```markdown
   ## [1.2.3] - 2024-01-15
   ### Added
   - User authentication system
   - Dark mode toggle
   - Export functionality for reports
   
   ### Fixed
   - Memory leak in background tasks
   - Timezone handling issues
   ```

3. **Automation Tools**
   ```bash
   # Generate changelog from git commits
   npm install -D conventional-changelog-cli
   npx conventional-changelog -p angular -i CHANGELOG.md -s
   
   # Auto-changelog
   npm install -D auto-changelog
   npx auto-changelog
   ```

4. **Commit Convention**
   ```bash
   # Conventional commits for auto-generation
   feat: add user authentication
   fix: resolve memory leak in tasks
   docs: update API documentation
   style: format code with prettier
   refactor: reorganize user service
   test: add unit tests for auth
   chore: update dependencies
   ```

5. **Integration with Releases**
   - Update changelog before each release
   - Include in release notes
   - Link to GitHub releases
   - Tag versions consistently

Remember to keep entries clear, categorized, and focused on user-facing changes.