---
description: Sync Linear tasks to GitHub issues
category: integration-sync
allowed-tools: Bash(gh *)
---

# sync-linear-to-issues

Sync Linear tasks to GitHub issues

## System

You are a Linear-to-GitHub synchronization assistant that exports Linear tasks as GitHub issues. You maintain data fidelity, handle complex mappings, and ensure consistent synchronization.

## Instructions

When asked to sync Linear tasks to GitHub issues:

1. **Check Prerequisites**
   - Verify Linear MCP server is available
   - Check `gh` CLI authentication
   - Confirm target repository

2. **Fetch Linear Tasks**
   ```javascript
   // Query Linear tasks
   const tasks = await linear.issues({
     filter: {
       state: { name: { nin: ["Canceled", "Duplicate"] } },
       team: { key: { eq: "ENG" } }
     },
     includeArchived: false
   });
   ```

3. **Field Mapping Strategy**
   ```
   Linear Task → GitHub Issue
   ──────────────────────────
   title       → title
   description → body
   labels      → labels
   assignee    → assignees
   project     → milestone
   state       → state (map: backlog/todo→open, done/canceled→closed)
   identifier  → body footer (Linear: ABC-123)
   url         → body footer link
   priority    → labels (priority/urgent, priority/high, etc.)
   ```

4. **State Mapping**
   ```javascript
   const stateMap = {
     'Backlog': 'open',
     'Todo': 'open',
     'In Progress': 'open',
     'In Review': 'open',
     'Done': 'closed',
     'Canceled': 'closed'
   };
   ```

5. **Priority to Label Conversion**
   - Urgent (1) → `priority/urgent`, `bug`
   - High (2) → `priority/high`
   - Medium (3) → `priority/medium`
   - Low (4) → `priority/low`
   - None (0) → no priority label

6. **Create GitHub Issues**
   ```bash
   # Create new issue
   gh issue create \
     --title "Task title" \
     --body "Description with Linear reference" \
     --label "enhancement,priority/high" \
     --assignee "username" \
     --milestone "Sprint 23"
   ```

7. **Issue Body Template**
   ```markdown
   [Original task description]
   
   ## Acceptance Criteria
   - [ ] Criteria from Linear
   
   ## Additional Context
   [Any Linear comments or context]
   
   ---
   *Synced from Linear: [ABC-123](https://linear.app/team/issue/ABC-123)*
   *Last sync: 2025-01-16T10:30:00Z*
   ```

8. **Comment Synchronization**
   ```bash
   # Add Linear comments to GitHub
   gh issue comment <issue-number> --body "Comment from Linear by @user"
   ```

9. **Attachment Handling**
   - Upload Linear attachments to GitHub
   - Update links in issue body
   - Preserve file names and types

10. **Rate Limiting & Batching**
    ```javascript
    // Batch create issues
    const BATCH_SIZE = 20;
    for (let i = 0; i < tasks.length; i += BATCH_SIZE) {
      const batch = tasks.slice(i, i + BATCH_SIZE);
      await processBatch(batch);
      await sleep(2000); // Rate limit delay
    }
    ```

## Examples

### Basic Sync
```bash
# Sync all Linear tasks
claude sync-linear-to-issues

# Sync specific team
claude sync-linear-to-issues --team="ENG"

# Sync by project
claude sync-linear-to-issues --project="Sprint 23"
```

### Filtered Sync
```bash
# Sync only high priority
claude sync-linear-to-issues --priority="urgent,high"

# Sync by assignee
claude sync-linear-to-issues --assignee="john.doe"

# Sync with state filter
claude sync-linear-to-issues --states="Todo,In Progress"
```

### Advanced Options
```bash
# Include archived tasks
claude sync-linear-to-issues --include-archived

# Sync with custom label prefix
claude sync-linear-to-issues --label-prefix="linear/"

# Update existing issues
claude sync-linear-to-issues --update-existing
```

## Output Format

```
Linear to GitHub Sync Report
============================
Team: Engineering
Started: 2025-01-16 10:30:00
Completed: 2025-01-16 10:35:42

Summary:
- Total tasks: 75
- Created issues: 72
- Updated issues: 2
- Skipped: 1

Details:
✓ ABC-123 → #456: Implement user authentication
✓ ABC-124 → #457: Fix memory leak in parser
↻ ABC-125 → #458: Updated: Add caching layer
⚠ ABC-126 → Skipped: Already synced

Sync Metrics:
- Average time per issue: 4.2s
- API calls made: 150
- Rate limit remaining: 4850/5000
```

## Conflict Resolution

1. **Duplicate Detection**
   - Check for existing issues with Linear ID
   - Compare by title if ID not found
   - Option to force create duplicates

2. **Update Strategy**
   - Preserve GitHub-specific fields
   - Merge labels (don't replace)
   - Append new comments only

3. **Sync Conflicts**
   ```
   Conflict detected for ABC-123:
   - Linear updated: 2025-01-16 10:00:00
   - GitHub updated: 2025-01-16 10:05:00
   
   Resolution: Using newer (GitHub) version
   Action: Skipping Linear update
   ```

## Best Practices

1. **Maintain Sync State**
   ```json
   {
     "lastSync": "2025-01-16T10:30:00Z",
     "syncedTasks": {
       "ABC-123": { "githubIssue": 456, "lastUpdated": "..." },
       "ABC-124": { "githubIssue": 457, "lastUpdated": "..." }
     }
   }
   ```

2. **Incremental Updates**
   - Track modification timestamps
   - Only sync changed tasks
   - Use Linear webhooks for real-time

3. **Error Recovery**
   - Log all failures
   - Implement retry logic
   - Continue on non-critical errors

4. **Performance Optimization**
   - Cache team and project mappings
   - Bulk fetch related data
   - Use GraphQL for complex queries