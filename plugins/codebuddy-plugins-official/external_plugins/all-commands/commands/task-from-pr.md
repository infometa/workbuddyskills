---
description: Create Linear tasks from pull requests
category: integration-sync
allowed-tools: Bash(gh *)
---

# task-from-pr

Create Linear tasks from pull requests

## Purpose
This command analyzes GitHub pull requests and creates corresponding Linear tasks, automatically extracting key information like title, description, labels, and assignees. It helps maintain synchronization between GitHub development workflow and Linear project management.

## Usage
```bash
# Convert a specific PR to a Linear task
claude "Convert PR #123 to a Linear task"

# Convert multiple PRs from a repository
claude "Convert all open PRs to Linear tasks for repo owner/repo"

# Convert PR with custom mapping
claude "Create Linear task from PR #456 and assign to team 'Engineering'"
```

## Instructions

### 1. Gather PR Information
First, use GitHub CLI to fetch PR details:

```bash
# Get PR information
gh pr view <PR_NUMBER> --json title,body,labels,assignees,state,url,createdAt,updatedAt,milestone

# List all open PRs
gh pr list --json number,title,labels,assignees --limit 100
```

### 2. Parse PR Description
Extract structured information from the PR body:

- Look for sections like "## Description", "## Changes", "## Testing"
- Identify checklist items (- [ ] or - [x])
- Extract any mentioned issue numbers (#123)
- Find @mentions for stakeholders
- Identify code blocks for technical details

### 3. Map GitHub Labels to Linear
Common label mappings:
- `bug` → Linear label: "Bug" + Priority: High
- `feature` → Linear label: "Feature"
- `enhancement` → Linear label: "Improvement"
- `documentation` → Linear label: "Documentation"
- `performance` → Linear label: "Performance"
- `security` → Linear label: "Security" + Priority: Urgent

### 4. Extract Task Details
Generate Linear task structure:

```javascript
{
  title: `[PR #${prNumber}] ${prTitle}`,
  description: `
    **GitHub PR:** ${prUrl}
    
    ## Summary
    ${extractedSummary}
    
    ## Changes
    ${bulletPoints}
    
    ## Acceptance Criteria
    ${checklistItems}
    
    ## Technical Details
    ${codeSnippets}
  `,
  priority: mapPriorityFromLabels(labels),
  labels: mapLabelsToLinear(labels),
  estimate: estimateFromPRSize(additions, deletions),
  assignee: mapGitHubUserToLinear(assignees[0])
}
```

### 5. Estimate Task Size
Calculate estimates based on PR metrics:

```
- Tiny (1 point): < 10 lines changed
- Small (2 points): 10-50 lines changed
- Medium (3 points): 50-250 lines changed
- Large (5 points): 250-500 lines changed
- X-Large (8 points): > 500 lines changed

Adjust based on:
- Number of files changed (multiply by 1.2 if > 10 files)
- Presence of tests (multiply by 0.8 if tests included)
- Documentation changes (multiply by 0.7 if only docs)
```

### 6. Create Linear Task
Use Linear MCP to create the task:

```javascript
// Example Linear task creation
const task = await linear.createTask({
  title: taskTitle,
  description: taskDescription,
  teamId: getTeamId(),
  priority: priority,
  estimate: estimate,
  labels: labelIds,
  assigneeId: assigneeId
});

// Link back to GitHub PR
await linear.createComment({
  issueId: task.id,
  body: `Linked to GitHub PR: ${prUrl}`
});
```

### 7. Error Handling
Handle common scenarios:

```javascript
// Check for Linear MCP availability
if (!linear.available) {
  console.error("Linear MCP tool not available. Please ensure it's configured.");
  return;
}

// Check for GitHub CLI
try {
  await exec('gh --version');
} catch (error) {
  console.error("GitHub CLI not installed. Please install: https://cli.github.com/");
  return;
}

// Handle duplicate tasks
const existingTask = await linear.searchTasks(`PR #${prNumber}`);
if (existingTask) {
  console.log(`Task already exists for PR #${prNumber}: ${existingTask.url}`);
  return;
}
```

## Example Output

```
Converting PR #123 to Linear task...

Fetched PR details:
- Title: Add user authentication middleware
- Author: @johndoe
- Labels: feature, backend, security
- Size: 234 lines changed across 8 files

Parsed description:
- Summary: Implements JWT-based authentication
- Has 5 checklist items (3 completed)
- References issues: #98, #102

Creating Linear task...
✓ Task created: LIN-456
  Title: [PR #123] Add user authentication middleware
  Team: Backend
  Priority: High (due to security label)
  Estimate: 3 points
  Labels: Feature, Backend, Security
  Assignee: John Doe

Task URL: https://linear.app/yourteam/issue/LIN-456
```

## Advanced Features

### Batch Processing
Convert multiple PRs:
```bash
# Convert all PRs with specific label
gh pr list --label "needs-task" --json number | \
  jq -r '.[].number' | \
  xargs -I {} claude "Convert PR #{} to Linear task"
```

### Custom Field Mapping
Map PR metadata to Linear custom fields:
- PR review status → Linear custom field "Review Status"
- PR branch name → Linear custom field "Feature Branch"
- CI/CD status → Linear custom field "Build Status"

### Automated Sync
Set up webhook to automatically create tasks when PRs are opened:
```javascript
// Webhook handler
on('pull_request.opened', async (event) => {
  await createLinearTaskFromPR(event.pull_request);
});
```

## Tips
- Include PR number in task title for easy reference
- Use Linear's GitHub integration to auto-link commits
- Set up bidirectional sync to update PR when task status changes
- Create subtasks for PR checklist items if needed
- Add PR author as a subscriber if they're not the assignee