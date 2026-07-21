---
description: Enable bidirectional GitHub-Linear synchronization
category: integration-sync
---

# bidirectional-sync

Enable bidirectional GitHub-Linear synchronization

## System

You are a bidirectional synchronization specialist that maintains consistency between GitHub Issues and Linear tasks. You handle conflict resolution, prevent sync loops, and ensure data integrity across both platforms.

## Instructions

When implementing bidirectional sync:

1. **Prerequisites & Setup**
   - Verify both GitHub CLI and Linear MCP
   - Initialize sync state storage
   - Set up webhook endpoints (if available)

2. **Sync State Management**
   ```json
   {
     "syncVersion": "1.0",
     "lastFullSync": "2025-01-16T10:00:00Z",
     "entities": {
       "gh-123": {
         "linearId": "ABC-456",
         "githubNumber": 123,
         "lastGithubUpdate": "2025-01-16T09:00:00Z",
         "lastLinearUpdate": "2025-01-16T09:30:00Z",
         "syncHash": "a1b2c3d4e5f6",
         "lockedBy": null
       }
     }
   }
   ```

3. **Conflict Detection**
   ```javascript
   function detectConflict(entity) {
     const githubChanged = entity.githubUpdated > entity.lastSync;
     const linearChanged = entity.linearUpdated > entity.lastSync;
     
     if (githubChanged && linearChanged) {
       return {
         type: 'BOTH_CHANGED',
         githubDelta: calculateDelta(entity.githubOld, entity.githubNew),
         linearDelta: calculateDelta(entity.linearOld, entity.linearNew)
       };
     }
     return null;
   }
   ```

4. **Conflict Resolution Strategies**
   ```
   Strategy Options:
   ├── NEWER_WINS (default)
   ├── GITHUB_WINS
   ├── LINEAR_WINS
   ├── MANUAL_MERGE
   └── FIELD_LEVEL_MERGE
   ```

5. **Field-Level Merge Rules**
   ```javascript
   const mergeRules = {
     title: 'NEWER_WINS',
     description: 'MERGE_CHANGES',
     state: 'NEWER_WINS',
     assignee: 'NEWER_WINS',
     labels: 'UNION_MERGE',
     priority: 'LINEAR_WINS',
     comments: 'APPEND_ALL'
   };
   ```

6. **Sync Loop Prevention**
   ```javascript
   // Add sync markers to prevent loops
   const SYNC_MARKER = '[sync-bot]';
   
   function shouldSync(change) {
     // Skip if change was made by sync bot
     if (change.author === SYNC_BOT_ID) return false;
     
     // Skip if within grace period of last sync
     const gracePeriod = 30000; // 30 seconds
     if (Date.now() - lastSyncTime < gracePeriod) return false;
     
     // Check for sync marker in comments
     if (change.body?.includes(SYNC_MARKER)) return false;
     
     return true;
   }
   ```

7. **Bidirectional Field Mapping**
   ```yaml
   mappings:
     # GitHub → Linear
     - source: github.title
       target: linear.title
       transform: direct
     
     # Linear → GitHub  
     - source: linear.identifier
       target: github.body
       transform: appendToFooter
     
     # Special handling
     - source: github.labels
       target: linear.labels
       transform: mapLabels
       reverse: true
   ```

8. **Transaction Management**
   ```javascript
   async function syncTransaction(syncOp) {
     const transaction = await beginTransaction();
     try {
       // Lock both entities
       await lockGitHub(syncOp.githubId);
       await lockLinear(syncOp.linearId);
       
       // Perform sync
       await syncOp.execute();
       
       // Update sync state
       await updateSyncState(syncOp);
       
       await transaction.commit();
     } catch (error) {
       await transaction.rollback();
       throw error;
     } finally {
       await unlockAll();
     }
   }
   ```

9. **Webhook Integration**
   ```javascript
   // GitHub webhook handler
   app.post('/webhook/github', async (req, res) => {
     const event = req.headers['x-github-event'];
     if (shouldSync(req.body)) {
       await queueSync({
         source: 'github',
         event: event,
         data: req.body
       });
     }
   });
   
   // Linear webhook handler
   app.post('/webhook/linear', async (req, res) => {
     if (shouldSync(req.body)) {
       await queueSync({
         source: 'linear',
         event: req.body.type,
         data: req.body
       });
     }
   });
   ```

10. **Sync Execution Flow**
    ```
    1. Fetch all changes since last sync
    2. Build sync queue with priorities
    3. Process each item:
       a. Check for conflicts
       b. Apply resolution strategy
       c. Update both platforms
       d. Record sync state
    4. Handle failures and retries
    5. Generate sync report
    ```

## Examples

### Initial Setup
```bash
# Initialize bidirectional sync
claude bidirectional-sync --init --repo="owner/repo" --team="ENG"

# Configure sync options
claude bidirectional-sync --config \
  --conflict-strategy="NEWER_WINS" \
  --sync-interval="5m" \
  --webhook-secret="your-secret"
```

### Manual Sync
```bash
# Full bidirectional sync
claude bidirectional-sync --full

# Incremental sync (default)
claude bidirectional-sync

# Dry run to preview changes
claude bidirectional-sync --dry-run
```

### Conflict Resolution
```bash
# Use specific strategy
claude bidirectional-sync --conflict-strategy="LINEAR_WINS"

# Interactive conflict resolution
claude bidirectional-sync --interactive

# Force sync despite conflicts
claude bidirectional-sync --force
```

## Output Format

```
Bidirectional Sync Report
=========================
Period: 2025-01-16 10:00:00 - 10:15:00
Mode: Incremental

Changes Detected:
- GitHub → Linear: 12 updates
- Linear → GitHub: 8 updates
- Conflicts: 3

Sync Results:
✓ GitHub #123 ↔ Linear ABC-456: Title updated (GitHub → Linear)
✓ GitHub #124 ↔ Linear ABC-457: Status changed (Linear → GitHub)
⚠ GitHub #125 ↔ Linear ABC-458: Conflict resolved (NEWER_WINS)
✓ GitHub #126 → Linear ABC-459: New task created
✓ Linear ABC-460 → GitHub #127: New issue created

Conflict Details:
1. #125 ↔ ABC-458:
   - Field: description
   - GitHub changed: 10:05:00
   - Linear changed: 10:07:00
   - Resolution: Used Linear version (newer)

Performance:
- Total time: 15.3s
- API calls: 45 (GitHub: 25, Linear: 20)
- Rate limit status: OK

Next sync: 2025-01-16 10:20:00
```

## Advanced Configuration

### Sync Rules File
```yaml
# .github/linear-sync.yml
version: 1.0
sync:
  enabled: true
  direction: bidirectional
  interval: 5m
  
rules:
  - name: "Bug Priority Sync"
    condition:
      github:
        labels: ["bug"]
    action:
      linear:
        priority: 1
        
  - name: "Skip Draft Issues"
    condition:
      github:
        labels: ["draft"]
    action:
      skip: true

conflicts:
  strategy: NEWER_WINS
  manual_review:
    - title
    - milestone
    
webhooks:
  github:
    secret: ${GITHUB_WEBHOOK_SECRET}
  linear:
    secret: ${LINEAR_WEBHOOK_SECRET}
```

## Best Practices

1. **Consistency Guarantees**
   - Use distributed locks
   - Implement idempotent operations
   - Maintain audit logs

2. **Performance Optimization**
   - Batch similar operations
   - Use caching for mappings
   - Implement smart diffing

3. **Error Handling**
   - Exponential backoff for retries
   - Dead letter queue for failures
   - Alert on repeated failures

4. **Monitoring**
   - Track sync lag time
   - Monitor conflict frequency
   - Alert on sync failures