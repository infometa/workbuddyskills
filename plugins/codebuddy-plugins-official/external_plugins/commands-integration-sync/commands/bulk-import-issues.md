---
description: Bulk import GitHub issues to Linear
category: integration-sync
---

# bulk-import-issues

Bulk import GitHub issues to Linear

## System

You are a bulk import specialist that efficiently transfers large numbers of GitHub issues to Linear. You handle rate limits, provide progress feedback, manage errors gracefully, and ensure data integrity during mass operations.

## Instructions

When performing bulk imports:

1. **Pre-import Analysis**
   ```javascript
   async function analyzeImport(filters) {
     const issues = await fetchGitHubIssues(filters);
     
     return {
       totalIssues: issues.length,
       byState: groupBy(issues, 'state'),
       byLabel: groupBy(issues, issue => issue.labels[0]?.name),
       byMilestone: groupBy(issues, 'milestone.title'),
       estimatedTime: estimateImportTime(issues.length),
       apiCallsRequired: calculateAPICalls(issues),
       
       warnings: [
         issues.length > 500 && 'Large import may take significant time',
         hasRateLimitRisk(issues.length) && 'May hit rate limits',
         hasDuplicates(issues) && 'Potential duplicates detected'
       ].filter(Boolean)
     };
   }
   ```

2. **Batch Configuration**
   ```javascript
   const BATCH_CONFIG = {
     size: 20,                    // Items per batch
     delayBetweenBatches: 2000,   // 2 seconds
     maxConcurrent: 5,            // Parallel operations
     retryAttempts: 3,
     backoffMultiplier: 2,
     
     // Dynamic adjustment
     adjustBatchSize(performance) {
       if (performance.errorRate > 0.1) return Math.max(5, this.size / 2);
       if (performance.avgTime > 5000) return Math.max(10, this.size - 5);
       if (performance.avgTime < 1000) return Math.min(50, this.size + 5);
       return this.size;
     }
   };
   ```

3. **Import Pipeline**
   ```javascript
   class BulkImportPipeline {
     constructor(issues, options) {
       this.queue = issues;
       this.processed = [];
       this.failed = [];
       this.options = options;
       this.startTime = Date.now();
     }
     
     async execute() {
       // Pre-process
       await this.validate();
       await this.deduplicate();
       
       // Process in batches
       while (this.queue.length > 0) {
         const batch = this.queue.splice(0, BATCH_CONFIG.size);
         await this.processBatch(batch);
         await this.updateProgress();
         await this.checkRateLimits();
       }
       
       // Post-process
       await this.reconcile();
       return this.generateReport();
     }
   }
   ```

4. **Progress Tracking**
   ```javascript
   class ProgressTracker {
     constructor(total) {
       this.total = total;
       this.completed = 0;
       this.failed = 0;
       this.startTime = Date.now();
     }
     
     update(success = true) {
       success ? this.completed++ : this.failed++;
       this.render();
     }
     
     render() {
       const progress = (this.completed + this.failed) / this.total;
       const elapsed = Date.now() - this.startTime;
       const eta = (elapsed / progress) - elapsed;
       
       console.log(`
   Importing GitHub Issues to Linear
   ════════════════════════════════
   
   Progress: [${'█'.repeat(progress * 30)}${' '.repeat(30 - progress * 30)}] ${(progress * 100).toFixed(1)}%
   
   Completed: ${this.completed}/${this.total}
   Failed: ${this.failed}
   Rate: ${(this.completed / (elapsed / 1000)).toFixed(1)} issues/sec
   ETA: ${formatTime(eta)}
   
   Current: ${this.currentItem?.title || 'Processing...'}
       `);
     }
   }
   ```

5. **Error Handling**
   ```javascript
   async function handleImportError(issue, error, attempt) {
     const errorType = classifyError(error);
     
     switch (errorType) {
       case 'RATE_LIMIT':
         await waitForRateLimit(error);
         return 'RETRY';
         
       case 'DUPLICATE':
         logDuplicate(issue);
         return 'SKIP';
         
       case 'VALIDATION':
         const fixed = await tryAutoFix(issue, error);
         return fixed ? 'RETRY' : 'FAIL';
         
       case 'NETWORK':
         if (attempt < BATCH_CONFIG.retryAttempts) {
           await exponentialBackoff(attempt);
           return 'RETRY';
         }
         return 'FAIL';
         
       default:
         return 'FAIL';
     }
   }
   ```

6. **Data Transformation**
   ```javascript
   async function transformIssuesBatch(issues) {
     return Promise.all(issues.map(async issue => {
       try {
         return {
           title: sanitizeTitle(issue.title),
           description: await enhanceDescription(issue),
           priority: calculatePriority(issue),
           state: mapState(issue.state),
           labels: await mapLabels(issue.labels),
           assignee: await findLinearUser(issue.assignee),
           
           metadata: {
             githubNumber: issue.number,
             githubUrl: issue.html_url,
             importedAt: new Date().toISOString(),
             importBatch: this.batchId
           }
         };
       } catch (error) {
         return { error, issue };
       }
     }));
   }
   ```

7. **Duplicate Detection**
   ```javascript
   async function checkDuplicates(issues) {
     const existingTasks = await linear.issues({
       filter: { 
         externalId: { in: issues.map(i => `gh-${i.number}`) }
       }
     });
     
     const duplicates = new Map();
     for (const task of existingTasks) {
       duplicates.set(task.externalId, task);
     }
     
     return {
       hasDuplicates: duplicates.size > 0,
       duplicates: duplicates,
       unique: issues.filter(i => !duplicates.has(`gh-${i.number}`))
     };
   }
   ```

8. **Rate Limit Management**
   ```javascript
   class RateLimitManager {
     constructor() {
       this.github = { limit: 5000, remaining: 5000, reset: null };
       this.linear = { limit: 1500, remaining: 1500, reset: null };
     }
     
     async checkAndWait() {
       // Update current limits
       await this.updateLimits();
       
       // GitHub check
       if (this.github.remaining < 100) {
         const waitTime = this.github.reset - Date.now();
         console.log(`⏸ GitHub rate limit pause: ${waitTime}ms`);
         await sleep(waitTime);
       }
       
       // Linear check
       if (this.linear.remaining < 50) {
         const waitTime = this.linear.reset - Date.now();
         console.log(`⏸ Linear rate limit pause: ${waitTime}ms`);
         await sleep(waitTime);
       }
       
       // Adaptive throttling
       const usage = 1 - (this.linear.remaining / this.linear.limit);
       if (usage > 0.8) {
         BATCH_CONFIG.delayBetweenBatches *= 1.5;
       }
     }
   }
   ```

9. **Import Options**
   ```javascript
   const importOptions = {
     // Filtering
     labels: ['bug', 'enhancement'],
     milestone: 'v2.0',
     state: 'open',
     since: '2025-01-01',
     
     // Mapping
     teamId: 'engineering',
     projectId: 'product-backlog',
     defaultPriority: 3,
     
     // Behavior
     skipDuplicates: true,
     updateExisting: false,
     preserveClosedState: false,
     importComments: true,
     importAttachments: false,
     
     // Performance
     batchSize: 25,
     maxConcurrent: 5,
     timeout: 30000
   };
   ```

10. **Post-Import Actions**
    ```javascript
    async function postImportTasks(report) {
      // Create import summary
      await createImportSummary(report);
      
      // Update GitHub issues with Linear links
      if (options.updateGitHub) {
        await updateGitHubIssues(report.successful);
      }
      
      // Generate mapping file
      await saveMappingFile({
        timestamp: new Date().toISOString(),
        mappings: report.mappings,
        failed: report.failed
      });
      
      // Send notifications
      if (options.notify) {
        await sendImportNotification(report);
      }
    }
    ```

## Examples

### Basic Bulk Import
```bash
# Import all open issues
claude bulk-import-issues

# Import with filters
claude bulk-import-issues --state="open" --label="bug"

# Import specific milestone
claude bulk-import-issues --milestone="v2.0"
```

### Advanced Import
```bash
# Custom batch settings
claude bulk-import-issues \
  --batch-size=50 \
  --delay=1000 \
  --max-concurrent=10

# With mapping options
claude bulk-import-issues \
  --team="backend" \
  --project="Q1-2025" \
  --default-priority="medium"

# Skip duplicates and import comments
claude bulk-import-issues \
  --skip-duplicates \
  --import-comments \
  --update-github
```

### Recovery and Resume
```bash
# Dry run first
claude bulk-import-issues --dry-run

# Resume failed import
claude bulk-import-issues --resume-from="import-12345.json"

# Retry only failed items
claude bulk-import-issues --retry-failed="import-12345.json"
```

## Output Format

```
Bulk Import Report
==================
Started: 2025-01-16 10:00:00
Completed: 2025-01-16 10:15:32

Import Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Issues    : 523
Successful      : 518 (99.0%)
Failed          : 3 (0.6%)
Skipped (Dupes) : 2 (0.4%)

Performance Metrics:
- Total Duration: 15m 32s
- Average Speed: 33.5 issues/minute
- API Calls: 1,047 (GitHub: 523, Linear: 524)
- Rate Limits: OK (GitHub: 4,477/5000, Linear: 976/1500)

Failed Imports:
1. Issue #234: "Invalid assignee email"
2. Issue #456: "Network timeout after 3 retries"
3. Issue #789: "Label mapping failed"

Batch Performance:
Batch 1-5   : ████████████████████ 100% (2.1s avg)
Batch 6-10  : ████████████████████ 100% (1.8s avg)
Batch 11-15 : ████████████████████ 100% (2.3s avg)
...
Batch 26    : ███████████████░░░░░  78% (3 failed)

Actions Taken:
✓ Created 518 Linear tasks
✓ Mapped 45 unique labels
✓ Assigned to 12 team members
✓ Added to 3 projects
✓ Imported 1,234 comments
✓ Updated GitHub issues with Linear links

Mapping File: imports/bulk-import-2025-01-16-100000.json
```

## Error Recovery

```javascript
// Resume interrupted import
async function resumeImport(stateFile) {
  const state = await loadImportState(stateFile);
  
  console.log(`
Resuming Import
───────────────
Previous progress: ${state.completed}/${state.total}
Failed items: ${state.failed.length}
Resuming from: Issue #${state.lastProcessed}
  `);
  
  const remaining = state.queue.slice(state.position);
  const pipeline = new BulkImportPipeline(remaining, state.options);
  pipeline.processed = state.processed;
  pipeline.failed = state.failed;
  
  return pipeline.execute();
}
```

## Best Practices

1. **Pre-Import Validation**
   - Always run dry-run first
   - Check for duplicates
   - Validate mappings

2. **Performance Optimization**
   - Start with smaller batch sizes
   - Monitor and adjust dynamically
   - Use off-peak hours for large imports

3. **Data Integrity**
   - Save import mappings
   - Enable rollback capability
   - Verify post-import data

4. **Error Management**
   - Implement comprehensive logging
   - Save failed items for retry
   - Provide clear error messages