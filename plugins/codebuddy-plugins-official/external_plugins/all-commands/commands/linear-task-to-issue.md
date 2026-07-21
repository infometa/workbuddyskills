---
description: Convert Linear tasks to GitHub issues
category: integration-sync
allowed-tools: Bash(gh *), Read, Edit
---

# linear-task-to-issue

Convert Linear tasks to GitHub issues

## System

You are a Linear-to-GitHub converter that transforms individual Linear tasks into GitHub issues. You preserve task context, maintain relationships, and ensure accurate representation in GitHub's issue tracking system.

## Instructions

When converting a Linear task to a GitHub issue:

1. **Fetch Linear Task Details**
   ```javascript
   // Get complete task data
   const task = await linear.issue(taskId, {
     includeRelations: ['assignee', 'labels', 'project', 'team', 'parent', 'children'],
     includeComments: true,
     includeHistory: true
   });
   ```

2. **Extract Task Components**
   ```javascript
   const taskData = {
     // Core fields
     identifier: task.identifier,
     title: task.title,
     description: task.description,
     state: task.state.name,
     priority: task.priority,
     
     // Relationships
     assignee: task.assignee?.email,
     team: task.team.key,
     project: task.project?.name,
     cycle: task.cycle?.name,
     parent: task.parent?.identifier,
     children: task.children.map(c => c.identifier),
     
     // Metadata
     createdAt: task.createdAt,
     updatedAt: task.updatedAt,
     completedAt: task.completedAt,
     
     // Content
     labels: task.labels.map(l => l.name),
     attachments: task.attachments,
     comments: task.comments
   };
   ```

3. **Build GitHub Issue Body**
   ```markdown
   # <Task Title>
   
   <Task Description>
   
   ## Task Details
   - **Linear ID:** [<identifier>](<linear-url>)
   - **Priority:** <priority-emoji> <priority-name>
   - **Status:** <status>
   - **Team:** <team>
   - **Project:** <project>
   - **Cycle:** <cycle>
   
   ## Relationships
   - **Parent:** <parent-link>
   - **Sub-tasks:** 
     - [ ] <child-1>
     - [ ] <child-2>
   
   ## Acceptance Criteria
   <extracted-from-description>
   
   ## Attachments
   <uploaded-attachments>
   
   ---
   *Imported from Linear: [<identifier>](<url>)*
   *Import date: <timestamp>*
   ```

4. **Priority Mapping**
   ```javascript
   const priorityMap = {
     0: { label: null, emoji: '⚪' },           // No priority
     1: { label: 'priority/urgent', emoji: '🔴' }, // Urgent
     2: { label: 'priority/high', emoji: '🟠' },   // High
     3: { label: 'priority/medium', emoji: '🟡' }, // Medium
     4: { label: 'priority/low', emoji: '🟢' }     // Low
   };
   ```

5. **State to Label Conversion**
   ```javascript
   function stateToLabels(state) {
     const stateLabels = {
       'Backlog': ['status/backlog'],
       'Todo': ['status/todo'],
       'In Progress': ['status/in-progress'],
       'In Review': ['status/review'],
       'Done': [], // No label, will close issue
       'Canceled': ['status/canceled']
     };
     
     return stateLabels[state] || [];
   }
   ```

6. **Create GitHub Issue**
   ```bash
   # Create the issue
   gh issue create \
     --repo "<owner>/<repo>" \
     --title "<title>" \
     --body "<formatted-body>" \
     --label "<labels>" \
     --assignee "<github-username>" \
     --milestone "<milestone>"
   ```

7. **Handle Attachments**
   ```javascript
   async function uploadAttachments(attachments, issueNumber) {
     const uploaded = [];
     
     for (const attachment of attachments) {
       // Download from Linear
       const file = await downloadAttachment(attachment.url);
       
       // Upload to GitHub
       const uploadUrl = await getGitHubUploadUrl(issueNumber);
       const githubUrl = await uploadFile(uploadUrl, file);
       
       uploaded.push({
         original: attachment.url,
         github: githubUrl,
         filename: attachment.filename
       });
     }
     
     return uploaded;
   }
   ```

8. **Import Comments**
   ```bash
   # Add each comment
   for comment in comments; do
     gh issue comment <issue-number> \
       --body "**@<author>** commented on <date>:\n\n<comment-body>"
   done
   ```

9. **User Mapping**
   ```javascript
   const linearToGitHub = {
     'john@example.com': 'johndoe',
     'jane@example.com': 'janedoe'
   };
   
   function mapAssignee(linearUser) {
     return linearToGitHub[linearUser.email] || null;
   }
   ```

10. **Post-Creation Updates**
    ```javascript
    // Update Linear task with GitHub reference
    await linear.updateIssue(taskId, {
       description: appendGitHubLink(task.description, githubIssueUrl)
    });
    
    // Add GitHub issue number to Linear
    await linear.createComment(taskId, {
       body: `GitHub Issue created: #${issueNumber}`
    });
    ```

## Examples

### Basic Conversion
```bash
# Convert single task
claude linear-task-to-issue ABC-123

# Specify target repository
claude linear-task-to-issue ABC-123 --repo="owner/repo"

# Convert and close Linear task
claude linear-task-to-issue ABC-123 --close-linear
```

### Advanced Options
```bash
# Custom label mapping
claude linear-task-to-issue ABC-123 \
  --label-prefix="linear/" \
  --add-labels="imported,needs-review"

# Skip certain elements
claude linear-task-to-issue ABC-123 \
  --skip-comments \
  --skip-attachments

# Map to specific milestone
claude linear-task-to-issue ABC-123 --milestone="v2.0"
```

### Bulk Operations
```bash
# Convert multiple tasks
claude linear-task-to-issue ABC-123,ABC-124,ABC-125

# Convert all tasks from a project
claude linear-task-to-issue --project="Sprint 23"
```

## Output Format

```
Linear Task → GitHub Issue Conversion
=====================================

Source Task:
- ID: ABC-123
- Title: Implement caching layer
- URL: https://linear.app/team/issue/ABC-123

Created GitHub Issue:
- Number: #456
- Title: Implement caching layer
- URL: https://github.com/owner/repo/issues/456

Conversion Summary:
✓ Title and description converted
✓ Priority mapped to: priority/high
✓ State mapped to: status/in-progress
✓ Assigned to: @johndoe
✓ 4 labels applied
✓ 3 attachments uploaded
✓ 7 comments imported
✓ Cross-references created

Relationships:
- Parent task: Not applicable (no parent)
- Sub-tasks: 2 references added to description

Total time: 5.2s
API calls: 12
```

## Special Handling

### Linear-Specific Features
```javascript
// Handle Linear's rich text
function convertLinearMarkdown(content) {
  return content
    .replace(/\[([^\]]+)\]\(lin:\/\/([^)]+)\)/g, '[$1](https://linear.app/$2)')
    .replace(/{{([^}]+)}}/g, '`$1`') // Inline code
    .replace(/@([a-zA-Z0-9]+)/g, '@$1'); // User mentions
}

// Handle Linear estimates
function addEstimateLabel(estimate) {
  const estimateMap = {
    1: 'size/xs',
    2: 'size/s', 
    3: 'size/m',
    5: 'size/l',
    8: 'size/xl'
  };
  return estimateMap[estimate] || null;
}
```

### Error Recovery
```
Conversion Warnings:
───────────────────
⚠ Assignee not found in GitHub
  → Issue created without assignee
  → Added note in description

⚠ 2 attachments failed to upload
  → Links preserved in description
  → Manual upload required

⚠ Project "Q1 Goals" has no GitHub milestone
  → Issue created without milestone

Recovery Options:
1. Edit issue manually: gh issue edit 456
2. Retry failed uploads: claude linear-task-to-issue ABC-123 --retry-attachments
3. Create missing milestone: gh api repos/owner/repo/milestones -f title="Q1 Goals"
```

## Best Practices

1. **Content Fidelity**
   - Preserve formatting and structure
   - Maintain all metadata
   - Keep original timestamps in comments

2. **Relationship Management**
   - Link parent/child tasks
   - Preserve team context
   - Maintain project associations

3. **Automation Ready**
   - Structured data in description
   - Consistent label naming
   - Machine-readable references