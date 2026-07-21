---
description: Analyze team retrospectives for insights
category: team-collaboration
---

# Retrospective Analyzer

Analyze team retrospectives for insights

## Instructions

1. **Retrospective Setup**
   - Identify sprint to analyze (default: most recent)
   - Check Linear MCP connection for sprint data
   - Define retrospective format preference
   - Set analysis time range

2. **Sprint Data Collection**

#### Quantitative Metrics
```
From Linear/Project Management:
- Planned vs completed story points
- Sprint velocity and capacity
- Cycle time and lead time
- Escaped defects count
- Unplanned work percentage

From Git/GitHub:
- Commit frequency and distribution
- PR merge time statistics  
- Code review turnaround
- Build success rate
- Deployment frequency
```

#### Qualitative Data Sources
```
1. PR review comments sentiment
2. Commit message patterns
3. Slack conversations (if available)
4. Previous retrospective action items
5. Support ticket trends
```

3. **Automated Analysis**

#### Sprint Performance Analysis
```markdown
# Sprint [Name] Retrospective Analysis

## Sprint Overview
- Duration: [Start] to [End]
- Team Size: [Number] members
- Sprint Goal: [Description]
- Goal Achievement: [Yes/Partial/No]

## Key Metrics Summary

### Delivery Metrics
| Metric | Target | Actual | Variance |
|--------|--------|--------|----------|
| Velocity | [X] pts | [Y] pts | [+/-Z]% |
| Completion Rate | 90% | [X]% | [+/-Y]% |
| Defect Rate | <5% | [X]% | [+/-Y]% |
| Unplanned Work | <20% | [X]% | [+/-Y]% |

### Process Metrics
| Metric | This Sprint | Previous | Trend |
|--------|-------------|----------|-------|
| Avg PR Review Time | [X] hrs | [Y] hrs | [↑/↓] |
| Avg Cycle Time | [X] days | [Y] days | [↑/↓] |
| CI/CD Success Rate | [X]% | [Y]% | [↑/↓] |
| Team Happiness | [X]/5 | [Y]/5 | [↑/↓] |
```

#### Pattern Recognition
```markdown
## Identified Patterns

### Positive Patterns 🟢
1. **Improved Code Review Speed**
   - Average review time decreased by 30%
   - Correlation with new review guidelines
   - Recommendation: Document and maintain process

2. **Consistent Daily Progress**
   - Even commit distribution throughout sprint
   - No last-minute rush
   - Indicates good sprint planning

### Concerning Patterns 🔴
1. **Monday Deploy Failures**
   - 60% of failed deployments on Mondays
   - Possible cause: Weekend changes not tested
   - Action: Implement Monday morning checks

2. **Increasing Scope Creep**
   - 35% unplanned work (up from 20%)
   - Source: Urgent customer requests
   - Action: Review sprint commitment process
```

4. **Interactive Retrospective Facilitation**

#### Pre-Retrospective Report
```markdown
# Pre-Retrospective Insights

## Data-Driven Discussion Topics

### 1. What Went Well 
Based on the data, these areas showed improvement:
- ✅ Code review efficiency (+30%)
- ✅ Test coverage increase (+5%)
- ✅ Zero critical bugs in production
- ✅ All team members contributed evenly

**Suggested Discussion Questions:**
- What specific changes led to faster reviews?
- How can we maintain zero critical bugs?
- What made work distribution successful?

### 2. What Didn't Go Well
Data indicates challenges in these areas:
- ❌ Sprint velocity miss (-15%)
- ❌ High unplanned work (35%)
- ❌ 3 rollbacks required
- ❌ Team overtime increased

**Suggested Discussion Questions:**
- What caused the velocity miss?
- How can we better handle unplanned work?
- What led to the rollbacks?

### 3. Action Items from Data
Recommended improvements based on patterns:
1. Implement feature flags for safer deployments
2. Create unplanned work budget in sprint planning
3. Add integration tests for [problem area]
4. Schedule mid-sprint check-ins
```

#### Live Retrospective Support
```
During the retrospective, I can help with:

1. **Fact Checking**: 
   "Actually, our velocity was 45 points, not 50"

2. **Pattern Context**:
   "This is the 3rd sprint with Monday deploy issues"

3. **Historical Comparison**:
   "Last time we had similar issues, we tried X"

4. **Action Item Tracking**:
   "From last retro, we completed 4/6 action items"
```

5. **Retrospective Output Formats**

#### Standard Retrospective Summary
```markdown
# Sprint [X] Retrospective Summary

## Participants
[List of attendees]

## What Went Well
- [Categorized list with vote counts]
- Supporting data: [Metrics]

## What Didn't Go Well  
- [Categorized list with vote counts]
- Root cause analysis: [Details]

## Action Items
| Action | Owner | Due Date | Success Criteria |
|--------|-------|----------|------------------|
| [Action 1] | [Name] | [Date] | [Measurable outcome] |
| [Action 2] | [Name] | [Date] | [Measurable outcome] |

## Experiments for Next Sprint
1. [Experiment description]
   - Hypothesis: [What we expect]
   - Measurement: [How we'll know]
   - Review date: [When to assess]

## Team Health Pulse
- Energy Level: [Rating]/5
- Clarity: [Rating]/5
- Confidence: [Rating]/5
- Key Quote: "[Notable team sentiment]"
```

#### Trend Analysis Report
```markdown
# Retrospective Trends Analysis

## Recurring Themes (Last 5 Sprints)

### Persistent Challenges
1. **Deployment Issues** (4/5 sprints)
   - Root cause still unresolved
   - Recommended escalation

2. **Estimation Accuracy** (5/5 sprints)
   - Consistent 20% overrun
   - Needs systematic approach

### Improving Areas
1. **Communication** (Improving for 3 sprints)
2. **Code Quality** (Steady improvement)

### Success Patterns
1. **Pair Programming** (Mentioned positively 5/5)
2. **Daily Standups** (Effective format found)
```

6. **Action Item Generation**

#### Smart Action Items
```
Based on retrospective discussion, here are SMART action items:

1. **Reduce Deploy Failures**
   - Specific: Implement smoke tests for Monday deploys
   - Measurable: <5% failure rate
   - Assignable: DevOps team
   - Relevant: Addresses 60% of failures
   - Time-bound: By next sprint

2. **Improve Estimation**
   - Specific: Use planning poker for all stories
   - Measurable: <20% variance from estimates
   - Assignable: Scrum Master facilitates
   - Relevant: Addresses velocity misses
   - Time-bound: Start next sprint planning
```

## Error Handling

### No Linear Data
```
"Linear MCP not connected. Using git data only.

Missing insights:
- Story point analysis
- Task-level metrics
- Team capacity data

Would you like to:
1. Proceed with git data only
2. Manually input sprint metrics
3. Connect Linear and retry"
```

### Incomplete Sprint
```
"Sprint appears to be in progress. 

Current analysis based on:
- [X] days of [Y] total
- [Z]% work completed

Recommendation: Run full analysis after sprint ends
Proceed with partial analysis? [Y/N]"
```

## Advanced Features

### Sentiment Analysis
```python
# Analyze PR comments and commit messages
sentiment_indicators = {
    'positive': ['fixed', 'improved', 'resolved', 'great'],
    'negative': ['bug', 'issue', 'broken', 'failed', 'frustrated'],
    'neutral': ['updated', 'changed', 'modified']
}

# Generate sentiment report
"Team Sentiment Analysis:
- Positive indicators: 65%
- Negative indicators: 25%  
- Neutral: 10%

Trend: Improving from last sprint (was 55% positive)"
```

### Predictive Insights
```
"Based on current patterns:

⚠️ Risk Predictions:
- 70% chance of velocity miss if unplanned work continues
- Deploy failures likely to increase without intervention

💡 Opportunity Predictions:
- 15% velocity gain possible with proposed process changes
- Team happiness likely to improve with workload balancing"
```

### Experiment Tracking
```
"Previous Experiments Results:

1. 'No Meeting Fridays' (Sprint 12-14)
   - Result: 20% productivity increase
   - Recommendation: Make permanent

2. 'Pair Programming for Complex Tasks' (Sprint 15)
   - Result: 50% fewer defects
   - Recommendation: Continue with guidelines"
```

## Integration Options

1. **Linear**: Create action items as tasks
2. **Slack**: Post summary to team channel
3. **Confluence**: Export formatted retrospective page
4. **GitHub**: Create issues for technical debt items
5. **Calendar**: Schedule action item check-ins

## Best Practices

1. **Data Before Discussion**: Review metrics first
2. **Focus on Patterns**: Look for recurring themes
3. **Action-Oriented**: Every insight needs action
4. **Time-boxed**: Keep retrospective focused
5. **Follow-up**: Track action item completion
6. **Celebrate Wins**: Acknowledge improvements
7. **Safe Space**: Encourage honest feedback