---
description: Manage cross-platform reference links
category: integration-sync
argument-hint: "Valid actions: audit, repair, map, validate, export"
---

# Cross-Reference Manager

Manage cross-platform reference links

## Instructions

1. **Check Tool Availability**
   - Verify GitHub CLI (`gh`) is installed and authenticated
   - Check if Linear MCP server is connected
   - If either tool is missing, provide setup instructions

2. **Parse Command Arguments**
   - Extract the action from command arguments: **$ARGUMENTS**
   - Valid actions: audit, repair, map, validate, export
   - Parse any additional options provided

3. **Initialize Reference Database**
   - Create or load existing reference mapping database
   - Structure should track:
     - GitHub issue ID ↔ Linear task ID
     - GitHub PR ID ↔ Linear task ID
     - Comment references
     - User mappings
     - Timestamps and sync history

4. **Execute Selected Action**
   Based on the action provided:

   ### Audit Action
   - Scan all GitHub issues and PRs for Linear references
   - Query Linear for all tasks with GitHub references
   - Identify:
     - Orphaned references (deleted items)
     - Mismatched references
     - Duplicate mappings
     - Missing bidirectional links
   - Generate detailed audit report

   ### Repair Action
   - Fix identified reference issues:
     - Update Linear tasks with missing GitHub links
     - Add Linear references to GitHub items
     - Remove references to deleted items
     - Consolidate duplicate mappings
   - Create backup before making changes
   - Log all modifications

   ### Map Action
   - Display current reference mappings
   - Show visual representation of connections
   - Include statistics on reference health
   - Highlight problematic mappings

   ### Validate Action
   - Perform deep validation of references
   - Check that linked items actually exist
   - Verify field consistency
   - Test bidirectional navigation
   - Report validation results

   ### Export Action
   - Export reference data in multiple formats
   - Support JSON, CSV, and Markdown
   - Include metadata and history
   - Provide import instructions

## Usage
```bash
cross-reference-manager [action] [options]
```

## Actions
- `audit` - Scan and report on reference integrity
- `repair` - Fix broken or missing references
- `map` - Display reference mappings
- `validate` - Verify reference consistency
- `export` - Export reference data

## Options
- `--scope <type>` - Limit to specific types (issues, prs, tasks)
- `--fix-orphans` - Automatically fix orphaned references
- `--dry-run` - Preview changes without applying
- `--deep-scan` - Perform thorough validation
- `--format <type>` - Output format (json, csv, table)
- `--since <date>` - Process items created after date
- `--backup` - Create backup before modifications

## Examples
```bash
# Audit all references
cross-reference-manager audit

# Repair broken references with preview
cross-reference-manager repair --dry-run

# Map references for specific date range
cross-reference-manager map --since "2024-01-01"

# Deep validation with orphan fixes
cross-reference-manager validate --deep-scan --fix-orphans

# Export reference data
cross-reference-manager export --format json > refs.json
```

## Features
- **Reference Integrity Checking**
  - Verify bidirectional links
  - Detect orphaned references
  - Identify duplicate mappings
  - Check reference format validity

- **Smart Reference Repair**
  - Reconstruct missing references from metadata
  - Update outdated reference formats
  - Merge duplicate references
  - Remove invalid references

- **Comprehensive Mapping**
  - GitHub Issue ↔ Linear Issue
  - GitHub PR ↔ Linear Task
  - Comments and attachments
  - User mappings

- **Audit Trail**
  - Log all reference modifications
  - Track reference history
  - Generate integrity reports
  - Monitor reference health

## Reference Storage
```json
{
  "mappings": {
    "github_issue_123": {
      "linear_id": "LIN-456",
      "type": "issue",
      "created": "2024-01-15T10:30:00Z",
      "last_verified": "2024-01-20T14:00:00Z",
      "confidence": 0.95
    }
  },
  "metadata": {
    "last_audit": "2024-01-20T14:00:00Z",
    "total_references": 1543,
    "broken_references": 12
  }
}
```

## Error Handling
- Automatic retry for API failures
- Batch processing to avoid rate limits
- Transaction-like operations with rollback
- Detailed error logging

## Best Practices
- Run audit weekly to maintain integrity
- Always use --dry-run before repair operations
- Export references before major changes
- Monitor reference health metrics

## Integration Points
- Works with bidirectional-sync command
- Supports sync-status monitoring
- Compatible with migration-assistant
- Provides data for analytics

## Required MCP Servers
- mcp-server-github
- mcp-server-linear

## Notes
This command maintains a local reference database for performance and reliability. The database is automatically backed up before modifications.