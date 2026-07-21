---
description: Resolve synchronization conflicts automatically
category: integration-sync
argument-hint: "Set up conflict detection parameters"
---

# Sync Conflict Resolver

Resolve synchronization conflicts automatically

## Instructions

1. **Initialize Conflict Detection**
   - Check GitHub CLI and Linear MCP availability
   - Load existing sync metadata and mappings
   - Parse command arguments from: **$ARGUMENTS**
   - Set up conflict detection parameters

2. **Parse Resolution Strategy**
   - Extract action (detect, resolve, analyze, configure, report)
   - Determine resolution strategy from options
   - Configure auto-resolve preferences
   - Set priority system if specified

3. **Execute Selected Action**
   Based on the action provided:

   ### Detect Action
   - Scan all synchronized items
   - Compare GitHub and Linear versions
   - Identify field-level conflicts
   - Flag timing conflicts
   - Generate conflict list

   ### Resolve Action
   - Apply selected strategy to conflicts
   - Handle field merging if enabled
   - Create backups before changes
   - Log all resolutions
   - Update sync metadata

   ### Analyze Action
   - Study conflict patterns
   - Identify frequent conflict types
   - Suggest process improvements
   - Generate analytics report

   ### Configure Action
   - Set default resolution strategies
   - Configure field priorities
   - Define merge rules
   - Save preferences

   ### Report Action
   - Generate detailed conflict report
   - Show resolution history
   - Provide conflict statistics
   - Export findings

## Usage
```bash
sync-conflict-resolver [action] [options]
```

## Actions
- `detect` - Identify synchronization conflicts
- `resolve` - Apply resolution strategies
- `analyze` - Deep analysis of conflict patterns
- `configure` - Set resolution preferences
- `report` - Generate conflict reports

## Options
- `--strategy <type>` - Resolution strategy (latest-wins, manual, smart)
- `--interactive` - Prompt for each conflict
- `--auto-resolve` - Automatically resolve using rules
- `--dry-run` - Preview resolutions without applying
- `--backup` - Create backup before resolving
- `--priority <system>` - Prioritize GitHub or Linear
- `--merge-fields` - Merge non-conflicting fields

## Examples
```bash
# Detect all conflicts
sync-conflict-resolver detect

# Resolve with latest-wins strategy
sync-conflict-resolver resolve --strategy latest-wins

# Interactive resolution with backup
sync-conflict-resolver resolve --interactive --backup

# Analyze conflict patterns
sync-conflict-resolver analyze --since "30 days ago"

# Configure auto-resolution rules
sync-conflict-resolver configure --auto-resolve
```

## Conflict Types
1. **Field Conflicts**
   - Title differences
   - Description mismatches
   - Status discrepancies
   - Priority conflicts
   - Assignee differences

2. **Structural Conflicts**
   - Deleted in one system
   - Duplicated items
   - Circular references
   - Parent-child mismatches

3. **Timing Conflicts**
   - Simultaneous updates
   - Out-of-order syncs
   - Version conflicts
   - Race conditions

## Resolution Strategies

### Latest Wins
- Uses most recent modification
- Configurable per field
- Maintains audit trail

### Smart Resolution
- Field-level intelligence
- Preserves important data
- Merges compatible changes
- User preference learning

### Manual Resolution
- Interactive prompts
- Side-by-side comparison
- Selective field merging
- Custom resolution rules

## Conflict Detection Algorithm
```yaml
detection:
  - compare_timestamps
  - check_field_hashes
  - verify_relationships
  - analyze_change_patterns
  
analysis:
  - identify_conflict_type
  - determine_severity
  - suggest_resolution
  - calculate_impact
```

## Resolution Rules Configuration
```json
{
  "rules": {
    "title": {
      "strategy": "latest-wins",
      "priority": "linear"
    },
    "description": {
      "strategy": "merge",
      "preserve_sections": ["## Requirements", "## Acceptance Criteria"]
    },
    "status": {
      "strategy": "smart",
      "mapping": {
        "github_closed": "linear_completed",
        "github_open": "linear_in_progress"
      }
    },
    "assignee": {
      "strategy": "manual",
      "notify": true
    }
  },
  "global": {
    "backup_before_resolve": true,
    "log_level": "detailed"
  }
}
```

## Merge Algorithm
1. Identify non-conflicting changes
2. Apply field-specific merge strategies
3. Preserve formatting and structure
4. Validate merged result
5. Create resolution record

## Conflict Prevention
- Implement field locking
- Use optimistic concurrency
- Add sync timestamps
- Enable change notifications

## Reporting Features
- Conflict frequency analysis
- Resolution success rates
- Common conflict patterns
- Team conflict hotspots
- Time-based trends

## Integration Workflow
1. Run after sync operations
2. Process conflict queue
3. Apply resolutions
4. Update reference manager
5. Notify affected users

## Required MCP Servers
- mcp-server-github
- mcp-server-linear

## Error Handling
- Transaction-based resolution
- Automatic rollback on failure
- Detailed conflict logs
- Resolution history tracking

## Best Practices
- Review conflict patterns monthly
- Adjust resolution rules based on patterns
- Train team on conflict prevention
- Monitor resolution success rates
- Keep manual intervention minimal

## Notes
This command maintains a conflict history database to improve resolution accuracy over time. Machine learning capabilities can be enabled for advanced pattern recognition.