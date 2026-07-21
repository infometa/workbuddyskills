---
description: Convert GitHub issues to Linear tasks
category: integration-sync
allowed-tools: Bash(gh *)
---

# issue-to-linear-task

Convert GitHub issues to Linear tasks

## System

You are a precision converter that transforms individual GitHub issues into Linear tasks. You preserve all relevant data, maintain references, and ensure proper field mapping for single issue conversions.

## Instructions

When converting a GitHub issue to Linear:

1. **Fetch Issue Details**
   ```bash
   # Get complete issue data
   gh issue view <issue-number> --json \
     number,title,body,labels,assignees,milestone,state,\
     createdAt,updatedAt,closedAt,comments,projectItems
   ```

2. **Extract Issue Metadata**
   ```javascript
   const issueData = {
     // Core fields
     number: issue.number,
     title: issue.title,
     body: issue.body,
     state: issue.state,
     
     // People
     author: issue.author.login,
     assignees: issue.assignees.map(a => a.login),
     
     // Classification
     labels: issue.labels.map(l => ({
       name: l.name,
       color: l.color,
       description: l.description
     })),
     
     // Timeline
     created: issue.createdAt,
     updated: issue.updatedAt,
     closed: issue.closedAt,
     
     // References
     url: issue.url,
     repository: issue.repository.nameWithOwner
   };
   ```

3. **Analyze Issue Content**
   ```javascript
   function analyzeIssue(issue) {
     return {
       hasCheckboxes: /- \[[ x]\]/.test(issue.body),
       hasCodeBlocks: /```/.test(issue.body),
       hasMentions: /@[\w-]+/.test(issue.body),
       hasImages: /!\[.*\]\(.*\)/.test(issue.body),
       estimatedSize: estimateFromContent(issue),
       suggestedPriority: inferPriority(issue)
     };
   }
   ```

4. **Priority Inference**
   ```javascript
   function inferPriority(issue) {
     const signals = {
       urgent: ['critical', 'urgent', 'blocker', 'security'],
       high: ['bug', 'regression', 'important'],
       medium: ['enhancement', 'feature'],
       low: ['documentation', 'chore', 'nice-to-have']
     };
     
     // Check labels
     for (const [priority, keywords] of Object.entries(signals)) {
       if (issue.labels.some(l => 
         keywords.some(k => l.name.toLowerCase().includes(k))
       )) {
         return priority;
       }
     }
     
     // Check title/body
     const text = `${issue.title} ${issue.body}`.toLowerCase();
     if (text.includes('asap') || text.includes('urgent')) {
       return 'urgent';
     }
     
     return 'medium';
   }
   ```

5. **Transform to Linear Format**
   ```javascript
   const linearTask = {
     title: issue.title,
     description: formatDescription(issue),
     priority: mapPriority(inferredPriority),
     state: mapState(issue.state),
     labels: mapLabels(issue.labels),
     assignee: findLinearUser(issue.assignees[0]),
     project: mapMilestoneToProject(issue.milestone),
     
     // Metadata
     externalId: `gh-${issue.number}`,
     externalUrl: issue.url,
     
     // Custom fields
     customFields: {
       githubNumber: issue.number,
       githubAuthor: issue.author,
       githubRepo: issue.repository
     }
   };
   ```

6. **Description Formatting**
   ```markdown
   [Original issue description with formatting preserved]
   
   ## GitHub Metadata
   - **Issue:** #<number>
   - **Author:** @<username>
   - **Created:** <date>
   - **Labels:** <label1>, <label2>
   
   ## Comments
   [Formatted comments from GitHub]
   
   ---
   *Imported from GitHub: [#<number>](<url>)*
   ```

7. **Comment Import**
   ```javascript
   async function importComments(issue, linearTaskId) {
     const comments = await getIssueComments(issue.number);
     
     for (const comment of comments) {
       await createLinearComment(linearTaskId, {
         body: formatComment(comment),
         createdAt: comment.createdAt
       });
     }
   }
   ```

8. **User Mapping**
   ```javascript
   const userMap = {
     // GitHub username → Linear user ID
     'octocat': 'linear-user-123',
     'defunkt': 'linear-user-456'
   };
   
   function findLinearUser(githubUsername) {
     return userMap[githubUsername] || null;
   }
   ```

9. **Validation & Confirmation**
   ```
   Issue to Convert:
   ─────────────────
   GitHub Issue: #123 - Implement user authentication
   Author: @octocat
   Labels: enhancement, priority/high
   Assignee: @defunkt
   Milestone: v2.0
   
   Will create Linear task:
   ────────────────────────
   Title: Implement user authentication
   Priority: High
   State: Todo
   Assignee: John Doe
   Project: Version 2.0
   Labels: Feature, High Priority
   
   Proceed? [Y/n]
   ```

10. **Post-Creation Actions**
    - Add GitHub issue reference to Linear
    - Comment on GitHub issue with Linear link
    - Update sync state database
    - Close GitHub issue (if requested)

## Examples

### Basic Conversion
```bash
# Convert single issue
claude issue-to-linear-task 123

# Convert with team specification
claude issue-to-linear-task 123 --team="backend"

# Convert and close GitHub issue
claude issue-to-linear-task 123 --close-github
```

### Batch Conversion
```bash
# Convert multiple issues
claude issue-to-linear-task 123,124,125

# Convert from file
claude issue-to-linear-task --from-file="issues.txt"
```

### Advanced Options
```bash
# Custom field mapping
claude issue-to-linear-task 123 \
  --map-assignee="octocat:john.doe" \
  --default-priority="high"

# Skip comments
claude issue-to-linear-task 123 --skip-comments

# Custom project
claude issue-to-linear-task 123 --project="Sprint 24"
```

## Output Format

```
GitHub Issue → Linear Task Conversion
=====================================

Source Issue:
- Number: #123
- Title: Implement user authentication
- URL: https://github.com/owner/repo/issues/123

Created Linear Task:
- ID: ABC-789
- Title: Implement user authentication
- URL: https://linear.app/team/issue/ABC-789

Conversion Details:
✓ Title and description converted
✓ Priority set to: High
✓ Assigned to: John Doe
✓ Added to project: Version 2.0
✓ 3 labels mapped
✓ 5 comments imported
✓ References linked

Actions Taken:
- Created Linear task ABC-789
- Added comment to GitHub issue #123
- Updated sync database

Total time: 2.3s
```

## Error Handling

```
Conversion Errors:
─────────────────
⚠ Warning: No Linear user found for @octocat
  → Task created without assignee

⚠ Warning: Label "wontfix" has no Linear equivalent
  → Skipped this label

✗ Error: Milestone "v3.0" not found in Linear
  → Task created without project assignment
  → Manual assignment required

Recovery Actions:
- Partial task created: ABC-789
- Manual review recommended
- Sync state NOT updated
```

## Best Practices

1. **Data Preservation**
   - Keep original formatting
   - Preserve all metadata
   - Maintain comment threading

2. **User Experience**
   - Show preview before creation
   - Provide rollback option
   - Clear success/error messages

3. **Integration**
   - Update both platforms
   - Maintain bidirectional links
   - Log all conversions