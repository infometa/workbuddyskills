---
description: Generate daily standup reports
category: team-collaboration
allowed-tools: Bash(git *), Bash(npm *)
---

# Standup Report

Generate daily standup reports

## Instructions

1. **Initial Setup**
   - Check Linear MCP server connection
   - Determine time range (default: last 24 hours)
   - Identify team members (from git config or user input)
   - Set report format preferences

2. **Data Collection**

#### Git Activity Analysis
```bash
# Collect commits from last 24 hours
git log --since="24 hours ago" --all --format="%h|%an|%ad|%s" --date=short

# Check branch activity
git for-each-ref --format='%(refname:short)|%(committerdate:short)|%(authoremail)' --sort=-committerdate refs/heads/

# Analyze file changes
git diff --stat @{1.day.ago}
```

#### Linear Integration (if available)
```
1. Fetch tasks updated in last 24 hours
2. Get task status changes
3. Check new comments and blockers
4. Review completed tasks
```

#### GitHub PR Status
```
1. Check PR updates and reviews
2. Identify merged PRs
3. Find new PRs created
4. Review CI/CD status
```

3. **Report Generation**

Generate structured standup report:

```markdown
# Daily Standup Report - [Date]

## Team Member: [Name]

### Yesterday's Accomplishments
- ✅ Completed [Task ID]: [Description]
  - Commits: [List with links]
  - PR: [Link if applicable]
- 🔄 Progressed on [Task ID]: [Description]
  - Current status: [X]% complete
  - Latest commit: [Message]

### Today's Plan
- 🎯 [Task ID]: [Description]
  - Estimated completion: [Time]
  - Dependencies: [List]
- 🔍 Code review for PR #[Number]
- 📝 Update documentation for [Feature]

### Blockers & Concerns
- 🚫 Blocked on [Task ID]: [Reason]
  - Need input from: [Person/Team]
  - Expected resolution: [Time]
- ⚠️ Potential risk: [Description]

### Metrics Summary
- Commits: [Count]
- PRs Updated: [Count]
- Tasks Completed: [Count]
- Cycle Time: [Average]
```

4. **Multi-Format Output**

Provide output in various formats:

#### Slack Format
```
*Daily Standup - @username*

*Yesterday:*
• Merged PR #123: Add user authentication
• Fixed bug in payment processing (ENG-456)
• Reviewed 3 PRs

*Today:*
• Starting ENG-457: Implement rate limiting
• Pairing with @teammate on database migration
• Sprint planning meeting at 2 PM

*Blockers:*
• Waiting on API credentials from DevOps
• ENG-458 needs design clarification
```

#### Email Format
```
Subject: Daily Standup - [Name] - [Date]

Hi team,

Here's my update for today's standup:

COMPLETED YESTERDAY:
- [Detailed list with context]

PLANNED FOR TODAY:
- [Prioritized task list]

BLOCKERS/HELP NEEDED:
- [Clear description of impediments]

Let me know if you have any questions.

Best,
[Name]
```

5. **Team Rollup View**

For team leads, generate consolidated view:

```markdown
# Team Standup Summary - [Date]

## Velocity Metrics
- Total Commits: [Count]
- PRs Merged: [Count]
- Tasks Completed: [Count]
- Active Blockers: [Count]

## Individual Updates
[Summary for each team member]

## Critical Items
- Blockers requiring immediate attention
- At-risk deliverables
- Resource conflicts

## Team Health Indicators
- On-track tasks: [%]
- Blocked tasks: [%]
- Overdue items: [Count]
```

## Error Handling

### No Linear Connection
```
"Linear MCP server not connected. Generating report from git and GitHub data only.

To enable full functionality:
1. Install Linear MCP: npm install -g @modelcontextprotocol/server-linear
2. Configure with your API key
3. Restart with Linear connected

Proceeding with available data..."
```

### No Recent Activity
```
"No git activity found in the last 24 hours. 

Possible reasons:
1. No commits made (check your time range)
2. Working on untracked branches
3. Local changes not committed

Would you like to:
- Extend the time range?
- Check specific branches?
- Manually input your updates?"
```

## Interactive Features

1. **Update Customization**
```
"I've generated your standup report. Would you like to:
1. Add additional context to any item?
2. Reorder priorities for today?
3. Add missing blockers or concerns?
4. Include work done outside of git?"
```

2. **Blocker Resolution**
```
"I notice you have blockers. Would you like help with:
1. Drafting messages to unblock items?
2. Finding alternative approaches?
3. Identifying who can help?"
```

## Best Practices

1. **Run before standup**: Generate 15-30 minutes before meeting
2. **Be specific**: Include task IDs and measurable progress
3. **Highlight blockers early**: Don't wait until standup
4. **Keep it concise**: Focus on key updates
5. **Link to evidence**: Include commit/PR links

## Advanced Features

### Trend Analysis
```
"Looking at your past week:
- Average daily commits: [Number]
- Task completion rate: [%]
- Common blocker patterns: [List]

Suggestions for improvement:
[Personalized recommendations]"
```

### Smart Scheduling
```
"Based on your calendar and task estimates:
- You have 5 hours of focused time today
- Recommended task order: [Prioritized list]
- Potential conflicts: [Meeting overlaps]"
```

## Command Examples

### Basic Usage
```
User: "Generate my standup report"
Assistant: [Generates standard report for last 24 hours]
```

### Custom Time Range
```
User: "Generate standup for last 2 days"
Assistant: [Generates report covering 48 hours]
```

### Team Report
```
User: "Generate team standup summary"
Assistant: [Generates consolidated team view]
```

### Specific Format
```
User: "Generate standup in Slack format"
Assistant: [Generates Slack-formatted message ready to paste]
```