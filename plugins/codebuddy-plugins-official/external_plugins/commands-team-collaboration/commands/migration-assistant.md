---
description: Assist with system migration planning
category: team-collaboration
argument-hint: "Valid actions: plan, analyze, migrate, verify, rollback"
---

# Migration Assistant

Assist with system migration planning

## Instructions

1. **Check Prerequisites**
   - Verify GitHub CLI (`gh`) is installed and authenticated
   - Check if Linear MCP server is connected
   - Ensure sufficient permissions in both systems
   - Confirm backup storage is available

2. **Parse Migration Parameters**
   - Extract action and options from: **$ARGUMENTS**
   - Valid actions: plan, analyze, migrate, verify, rollback
   - Determine source and target systems
   - Set migration scope and filters

3. **Initialize Migration Environment**
   - Create migration workspace directory
   - Set up logging and audit trails
   - Initialize checkpoint system
   - Prepare rollback mechanisms

4. **Execute Migration Action**
   Based on the selected action:

   ### Plan Action
   - Analyze source system structure
   - Map fields between systems
   - Identify potential conflicts
   - Generate migration strategy
   - Estimate time and resources
   - Create detailed migration plan

   ### Analyze Action
   - Count items to migrate
   - Check data compatibility
   - Identify custom fields
   - Assess attachment sizes
   - Calculate migration impact
   - Generate pre-migration report

   ### Migrate Action
   - Create full backup of source data
   - Execute migration in batches
   - Transform data between formats
   - Preserve relationships
   - Handle attachments and media
   - Create progress checkpoints
   - Log all operations

   ### Verify Action
   - Compare source and target data
   - Validate all items migrated
   - Check relationship integrity
   - Verify custom field mappings
   - Test cross-references
   - Generate verification report

   ### Rollback Action
   - Load rollback checkpoint
   - Restore original state
   - Clean up partial migrations
   - Verify rollback completion
   - Generate rollback report

## Usage
```bash
migration-assistant [action] [options]
```

## Actions
- `plan` - Create migration plan
- `analyze` - Assess migration scope
- `migrate` - Execute migration
- `verify` - Validate migration results
- `rollback` - Revert migration

## Options
- `--source <system>` - Source system (github/linear)
- `--target <system>` - Target system (github/linear)
- `--scope <items>` - Items to migrate (all/issues/prs/projects)
- `--dry-run` - Simulate migration
- `--parallel <n>` - Parallel processing threads
- `--checkpoint` - Enable checkpoint recovery
- `--mapping-file <path>` - Custom field mappings
- `--preserve-ids` - Maintain reference IDs
- `--archive-source` - Archive after migration

## Examples
```bash
# Plan GitHub to Linear migration
migration-assistant plan --source github --target linear

# Analyze migration scope
migration-assistant analyze --scope all

# Dry run migration
migration-assistant migrate --dry-run --parallel 4

# Execute migration with checkpoints
migration-assistant migrate --checkpoint --backup

# Verify migration completeness
migration-assistant verify --deep-check

# Rollback if needed
migration-assistant rollback --transaction-id 12345
```

## Migration Phases

### 1. Planning Phase
- Inventory source data
- Map data structures
- Identify incompatibilities
- Estimate migration time
- Generate migration plan

### 2. Preparation Phase
- Create full backup
- Validate permissions
- Set up target structure
- Configure mappings
- Test connectivity

### 3. Migration Phase
- Transfer data in batches
- Maintain relationships
- Preserve metadata
- Handle attachments
- Update references

### 4. Verification Phase
- Compare record counts
- Validate data integrity
- Check relationships
- Verify attachments
- Test functionality

### 5. Finalization Phase
- Update documentation
- Redirect webhooks
- Archive source data
- Generate reports
- Train users

## Data Mapping Configuration
```yaml
mappings:
  github_to_linear:
    issue:
      title: title
      body: description
      state: status
      labels: labels
      milestone: cycle
      assignees: assignees
    
    custom_fields:
      - source: "custom.priority"
        target: "priority"
        transform: "map_priority"
      
    relationships:
      - type: "parent-child"
        source: "depends_on"
        target: "parent"
    
  linear_to_github:
    issue:
      title: title
      description: body
      status: state
      priority: labels
      cycle: milestone
```

## Migration Safety Features

### Pre-Migration Checks
- Storage capacity verification
- API rate limit assessment
- Permission validation
- Dependency checking
- Conflict detection

### During Migration
- Transaction logging
- Progress tracking
- Error recovery
- Checkpoint creation
- Performance monitoring

### Post-Migration
- Data verification
- Integrity checking
- Performance testing
- User acceptance
- Rollback readiness

## Checkpoint Recovery
```json
{
  "checkpoint": {
    "id": "mig-20240120-1430",
    "progress": {
      "total_items": 5000,
      "completed": 3750,
      "failed": 12,
      "pending": 1238
    },
    "state": {
      "last_processed_id": "issue-3750",
      "batch_number": 75,
      "error_count": 12
    }
  }
}
```

## Rollback Capabilities
- Point-in-time recovery
- Selective rollback
- Relationship preservation
- Audit trail maintenance
- Zero data loss guarantee

## Performance Optimization
- Batch processing
- Parallel transfers
- API call optimization
- Caching strategies
- Resource monitoring

## Migration Reports
- Executive summary
- Detailed item mapping
- Error analysis
- Performance metrics
- Recommendation list

## Common Migration Scenarios

### GitHub Issues → Linear
1. Map GitHub labels to Linear labels/projects
2. Convert milestones to cycles
3. Preserve issue numbers as references
4. Migrate comments with user mapping
5. Handle attachments and images

### Linear → GitHub Issues
1. Map Linear statuses to GitHub states
2. Convert cycles to milestones
3. Preserve Linear IDs in issue body
4. Map Linear projects to labels
5. Handle custom fields

## Required MCP Servers
- mcp-server-github
- mcp-server-linear

## Error Handling
- Automatic retry with backoff
- Detailed error logging
- Partial failure recovery
- Manual intervention points
- Comprehensive error reports

## Best Practices
- Always run analysis first
- Use dry-run for testing
- Migrate in phases for large datasets
- Maintain communication with team
- Keep source data until verified
- Document custom mappings
- Test rollback procedures

## Compliance & Audit
- Full audit trail
- Data retention compliance
- Privacy preservation
- Change authorization
- Migration certification

## Notes
This command creates a complete migration package including backups, logs, and documentation. The migration can be resumed from checkpoints in case of interruption. All migrations are reversible within the retention period.