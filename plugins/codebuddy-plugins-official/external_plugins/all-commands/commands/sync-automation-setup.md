---
description: Setup automated synchronization workflows
category: integration-sync
allowed-tools: Bash(npm *)
---

# sync-automation-setup

Setup automated synchronization workflows

## System

You are an automation setup specialist that configures robust, automated synchronization between GitHub and Linear. You handle webhook configuration, CI/CD integration, scheduling, monitoring, and ensure reliable continuous synchronization.

## Instructions

When setting up sync automation:

1. **Prerequisites Check**
   ```javascript
   async function checkPrerequisites() {
     const checks = {
       github: {
         cli: await checkCommand('gh --version'),
         auth: await checkGitHubAuth(),
         permissions: await checkGitHubPermissions(),
         webhookAccess: await checkWebhookPermissions()
       },
       linear: {
         mcp: await checkLinearMCP(),
         apiKey: await checkLinearAPIKey(),
         webhookUrl: await checkLinearWebhookEndpoint()
       },
       infrastructure: {
         serverEndpoint: process.env.SYNC_SERVER_URL,
         database: await checkDatabaseConnection(),
         queue: await checkQueueService(),
         storage: await checkStateStorage()
       }
     };
     
     return validateAllChecks(checks);
   }
   ```

2. **GitHub Webhook Setup**
   ```bash
   # Create webhook for issue events
   gh api repos/:owner/:repo/hooks \
     --method POST \
     --field name='web' \
     --field active=true \
     --field events[]='issues' \
     --field events[]='issue_comment' \
     --field events[]='pull_request' \
     --field events[]='pull_request_review' \
     --field config[url]="${WEBHOOK_URL}/github" \
     --field config[content_type]='json' \
     --field config[secret]="${WEBHOOK_SECRET}"
   ```

3. **Linear Webhook Configuration**
   ```javascript
   async function setupLinearWebhooks() {
     const webhook = await linear.createWebhook({
       url: `${WEBHOOK_URL}/linear`,
       resourceTypes: ['Issue', 'Comment', 'Project', 'Cycle'],
       label: 'GitHub Sync',
       enabled: true,
       secret: process.env.LINEAR_WEBHOOK_SECRET
     });
     
     // Verify webhook
     await linear.testWebhook(webhook.id);
     
     return webhook;
   }
   ```

4. **GitHub Actions Workflow**
   ```yaml
   # .github/workflows/linear-sync.yml
   name: Linear Sync
   
   on:
     issues:
       types: [opened, edited, closed, reopened, labeled, unlabeled]
     issue_comment:
       types: [created, edited, deleted]
     pull_request:
       types: [opened, edited, closed, merged]
     schedule:
       - cron: '*/15 * * * *'  # Every 15 minutes
     workflow_dispatch:
       inputs:
         sync_type:
           description: 'Type of sync to perform'
           required: true
           default: 'incremental'
           type: choice
           options:
             - incremental
             - full
             - repair
   
   jobs:
     sync:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         
         - name: Setup sync environment
           run: |
             npm install -g @linear/sync-cli
             echo "${{ secrets.SYNC_CONFIG }}" > sync.config.json
         
         - name: Run sync
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
             LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
             SYNC_STATE_BUCKET: ${{ secrets.SYNC_STATE_BUCKET }}
           run: |
             case "${{ github.event_name }}" in
               "schedule")
                 linear-sync run --type=incremental
                 ;;
               "workflow_dispatch")
                 linear-sync run --type=${{ inputs.sync_type }}
                 ;;
               *)
                 linear-sync handle-event \
                   --event=${{ github.event_name }} \
                   --payload='${{ toJSON(github.event) }}'
                 ;;
             esac
         
         - name: Upload sync report
           if: always()
           uses: actions/upload-artifact@v3
           with:
             name: sync-report-${{ github.run_id }}
             path: sync-report.json
   ```

5. **Sync Server Configuration**
   ```javascript
   // sync-server.js
   const express = require('express');
   const { Queue } = require('bull');
   const { SyncEngine } = require('./sync-engine');
   
   const app = express();
   const syncQueue = new Queue('sync-tasks', REDIS_URL);
   const syncEngine = new SyncEngine();
   
   // GitHub webhook endpoint
   app.post('/webhooks/github', verifyGitHubWebhook, async (req, res) => {
     const event = req.headers['x-github-event'];
     const payload = req.body;
     
     // Queue sync task
     await syncQueue.add('github-event', {
       event,
       payload,
       timestamp: new Date().toISOString()
     }, {
       attempts: 3,
       backoff: { type: 'exponential', delay: 2000 }
     });
     
     res.status(200).send('OK');
   });
   
   // Linear webhook endpoint
   app.post('/webhooks/linear', verifyLinearWebhook, async (req, res) => {
     const { action, data, type } = req.body;
     
     await syncQueue.add('linear-event', {
       action,
       data,
       type,
       timestamp: new Date().toISOString()
     });
     
     res.status(200).send('OK');
   });
   
   // Health check endpoint
   app.get('/health', async (req, res) => {
     const health = await syncEngine.getHealth();
     res.json(health);
   });
   
   // Process sync queue
   syncQueue.process('github-event', async (job) => {
     return await syncEngine.processGitHubEvent(job.data);
   });
   
   syncQueue.process('linear-event', async (job) => {
     return await syncEngine.processLinearEvent(job.data);
   });
   ```

6. **Sync Configuration File**
   ```yaml
   # sync-config.yml
   version: 1.0
   
   sync:
     enabled: true
     direction: bidirectional
     mode: real-time  # real-time, scheduled, or hybrid
     
   scheduling:
     incremental:
       interval: '*/5 * * * *'  # Every 5 minutes
       enabled: true
     full:
       interval: '0 2 * * *'    # Daily at 2 AM
       enabled: true
     health_check:
       interval: '*/30 * * * *' # Every 30 minutes
       enabled: true
   
   mapping:
     states:
       github_to_linear:
         open: Todo
         closed: Done
       linear_to_github:
         Backlog: open
         Todo: open
         'In Progress': open
         Done: closed
         Canceled: closed
     
     priorities:
       label_to_priority:
         'priority/urgent': 1
         'priority/high': 2
         'priority/medium': 3
         'priority/low': 4
       priority_to_label:
         1: 'priority/urgent'
         2: 'priority/high'
         3: 'priority/medium'
         4: 'priority/low'
     
     teams:
       default: 'engineering'
       mapping:
         'frontend/*': 'frontend-team'
         'backend/*': 'backend-team'
         'docs/*': 'docs-team'
   
   conflict_resolution:
     strategy: newer_wins  # newer_wins, github_wins, linear_wins, manual
     preserve_fields:
       - comments
       - attachments
     merge_fields:
       - labels
       - assignees
   
   filters:
     github:
       include_labels:
         - 'linear-sync'
       exclude_labels:
         - 'no-sync'
         - 'draft'
     linear:
       include_teams:
         - 'engineering'
         - 'product'
       exclude_states:
         - 'Duplicate'
   
   notifications:
     slack:
       enabled: true
       webhook_url: ${SLACK_WEBHOOK_URL}
       channels:
         errors: '#sync-errors'
         summary: '#dev-updates'
     email:
       enabled: false
       recipients:
         - 'ops@company.com'
   
   monitoring:
     metrics:
       enabled: true
       provider: datadog
       api_key: ${DATADOG_API_KEY}
     logging:
       level: info
       destination: 'cloudwatch'
     alerts:
       - metric: sync_failure_rate
         threshold: 0.05
         action: notify
       - metric: sync_lag
         threshold: 300  # seconds
         action: alert
   ```

7. **Database Schema**
   ```sql
   -- Sync state management
   CREATE TABLE sync_state (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     github_id VARCHAR(255),
     linear_id VARCHAR(255),
     github_updated_at TIMESTAMP,
     linear_updated_at TIMESTAMP,
     last_sync_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     sync_hash VARCHAR(64),
     sync_version INTEGER DEFAULT 1,
     metadata JSONB,
     UNIQUE(github_id, linear_id)
   );
   
   -- Sync history
   CREATE TABLE sync_history (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     sync_id UUID REFERENCES sync_state(id),
     direction VARCHAR(50),
     status VARCHAR(50),
     started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     completed_at TIMESTAMP,
     changes JSONB,
     errors JSONB
   );
   
   -- Conflict log
   CREATE TABLE sync_conflicts (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     sync_id UUID REFERENCES sync_state(id),
     detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
     conflict_type VARCHAR(100),
     github_data JSONB,
     linear_data JSONB,
     resolution VARCHAR(100),
     resolved_at TIMESTAMP,
     resolved_by VARCHAR(255)
   );
   
   -- Indexes for performance
   CREATE INDEX idx_sync_state_github_id ON sync_state(github_id);
   CREATE INDEX idx_sync_state_linear_id ON sync_state(linear_id);
   CREATE INDEX idx_sync_history_sync_id ON sync_history(sync_id);
   CREATE INDEX idx_sync_history_started_at ON sync_history(started_at);
   ```

8. **Monitoring Dashboard**
   ```javascript
   // monitoring/dashboard.js
   const metrics = {
     // Real-time metrics
     syncRate: new Rate('sync.operations'),
     syncDuration: new Histogram('sync.duration'),
     syncErrors: new Counter('sync.errors'),
     
     // Business metrics
     issuesSynced: new Counter('issues.synced'),
     conflictsResolved: new Counter('conflicts.resolved'),
     
     // System health
     apiLatency: new Histogram('api.latency'),
     queueDepth: new Gauge('queue.depth'),
     rateLimitRemaining: new Gauge('ratelimit.remaining')
   };
   
   // Dashboard configuration
   const dashboard = {
     title: 'GitHub-Linear Sync Monitor',
     widgets: [
       {
         type: 'timeseries',
         title: 'Sync Operations',
         metrics: ['sync.operations', 'sync.errors'],
         period: '1h'
       },
       {
         type: 'gauge',
         title: 'Queue Depth',
         metric: 'queue.depth',
         thresholds: [0, 50, 100, 200]
       },
       {
         type: 'heatmap',
         title: 'Sync Duration',
         metric: 'sync.duration',
         buckets: [100, 500, 1000, 5000, 10000]
       },
       {
         type: 'counter',
         title: 'Today\'s Syncs',
         metric: 'issues.synced',
         period: '1d'
       }
     ],
     alerts: [
       {
         name: 'High Error Rate',
         condition: 'rate(sync.errors) > 0.1',
         severity: 'critical'
       },
       {
         name: 'Sync Lag',
         condition: 'queue.depth > 100',
         severity: 'warning'
       }
     ]
   };
   ```

9. **Deployment Script**
   ```bash
   #!/bin/bash
   # deploy-sync-automation.sh
   
   set -e
   
   echo "🚀 Deploying GitHub-Linear Sync Automation"
   
   # Check prerequisites
   echo "📋 Checking prerequisites..."
   command -v gh >/dev/null 2>&1 || { echo "❌ GitHub CLI required"; exit 1; }
   command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
   
   # Load configuration
   source .env
   
   # Build sync server
   echo "🔨 Building sync server..."
   docker build -t linear-sync-server .
   
   # Deploy database
   echo "🗄️ Setting up database..."
   docker-compose up -d postgres redis
   sleep 5
   docker-compose run --rm migrate
   
   # Configure webhooks
   echo "🔗 Configuring webhooks..."
   ./scripts/setup-webhooks.sh
   
   # Deploy sync server
   echo "🌐 Deploying sync server..."
   docker-compose up -d sync-server
   
   # Setup monitoring
   echo "📊 Configuring monitoring..."
   ./scripts/setup-monitoring.sh
   
   # Verify deployment
   echo "✅ Verifying deployment..."
   sleep 10
   curl -f http://localhost:3000/health || { echo "❌ Health check failed"; exit 1; }
   
   # Run initial sync
   echo "🔄 Running initial sync..."
   docker-compose run --rm sync-cli full-sync
   
   echo "✨ Deployment complete!"
   echo "📊 Dashboard: http://localhost:3000/dashboard"
   echo "📝 Logs: docker-compose logs -f sync-server"
   ```

10. **Maintenance Commands**
    ```bash
    # Sync management CLI
    linear-sync status          # Check sync status
    linear-sync pause          # Pause all syncing
    linear-sync resume         # Resume syncing
    linear-sync repair         # Repair sync state
    linear-sync reset          # Reset sync (caution!)
    
    # Troubleshooting
    linear-sync diagnose       # Run diagnostics
    linear-sync test-webhooks  # Test webhook connectivity
    linear-sync validate       # Validate configuration
    
    # Maintenance
    linear-sync cleanup        # Clean old sync records
    linear-sync export         # Export sync state
    linear-sync import         # Import sync state
    ```

## Examples

### Basic Setup
```bash
# Interactive setup
claude sync-automation-setup

# Setup with config file
claude sync-automation-setup --config="sync-config.yml"

# Minimal setup (webhooks only)
claude sync-automation-setup --mode="webhooks-only"
```

### Advanced Configuration
```bash
# Full automation with monitoring
claude sync-automation-setup \
  --mode="full" \
  --monitoring="datadog" \
  --alerts="slack,email"

# Custom deployment
claude sync-automation-setup \
  --deploy-target="kubernetes" \
  --namespace="sync-system"
```

### Maintenance
```bash
# Update webhook configuration
claude sync-automation-setup --update-webhooks

# Rotate secrets
claude sync-automation-setup --rotate-secrets

# Upgrade sync version
claude sync-automation-setup --upgrade
```

## Output Format

```
GitHub-Linear Sync Automation Setup
===================================

✅ Prerequisites Check
  ✓ GitHub CLI authenticated
  ✓ Linear MCP connected
  ✓ Database accessible
  ✓ Redis running

📋 Configuration Summary
  Mode: Bidirectional real-time sync
  Webhook URL: https://sync.company.com/webhooks
  Sync Interval: 5 minutes (incremental)
  Conflict Strategy: newer_wins

🔗 Webhook Configuration
  GitHub Webhooks:
    ✓ Issues webhook created (ID: 12345)
    ✓ Pull requests webhook created (ID: 12346)
    ✓ Webhook test successful
  
  Linear Webhooks:
    ✓ Issue webhook registered
    ✓ Comment webhook registered
    ✓ Webhook verified

🚀 Deployment Status
  ✓ Sync server deployed (3 replicas)
  ✓ Database migrations complete
  ✓ Redis queue initialized
  ✓ Monitoring configured

📊 Monitoring Setup
  Dashboard: https://monitoring.company.com/linear-sync
  Alerts configured:
    - Slack: #sync-alerts
    - Email: ops@company.com
  
  Metrics collecting:
    - Sync rate
    - Error rate
    - API latency
    - Queue depth

🔒 Security Configuration
  ✓ Webhook secrets configured
  ✓ API keys encrypted
  ✓ TLS enabled
  ✓ Rate limiting active

📝 Next Steps
  1. Monitor initial sync: docker-compose logs -f
  2. Check dashboard for metrics
  3. Review sync-config.yml for customization
  4. Set up team notifications

Automation Status: ✅ ACTIVE
First sync scheduled: 2 minutes
```

## Best Practices

1. **Security**
   - Use webhook secrets
   - Encrypt API keys
   - Implement rate limiting
   - Regular secret rotation

2. **Reliability**
   - Implement retry logic
   - Use message queues
   - Monitor system health
   - Plan for failures

3. **Performance**
   - Optimize batch sizes
   - Implement caching
   - Use connection pooling
   - Monitor API limits

4. **Maintenance**
   - Regular health checks
   - Automated backups
   - Log retention policies
   - Update procedures