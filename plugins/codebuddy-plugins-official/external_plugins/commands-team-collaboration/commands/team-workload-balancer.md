---
description: Balance team workload distribution
category: team-collaboration
allowed-tools: Bash(git *), Bash(gh *)
---

# team-workload-balancer

Balance team workload distribution

## Purpose
This command analyzes team members' current workloads, skills, past performance, and availability to suggest optimal task assignments. It helps prevent burnout, ensures balanced distribution, and matches tasks to team members' strengths.

## Usage
```bash
# Show current team workload
claude "Show workload balance for the engineering team"

# Suggest optimal assignment for new tasks
claude "Who should work on the new payment integration task?"

# Rebalance current sprint
claude "Rebalance tasks in the current sprint for optimal distribution"

# Capacity planning for next sprint
claude "Plan task assignments for next sprint based on team capacity"
```

## Instructions

### 1. Gather Team Data
Collect information about team members:

```javascript
class TeamAnalyzer {
  async gatherTeamData() {
    const team = {};
    
    // Get team members from Linear
    const teamMembers = await linear.getTeamMembers();
    
    for (const member of teamMembers) {
      team[member.id] = {
        name: member.name,
        email: member.email,
        currentTasks: [],
        completedTasks: [],
        skills: new Set(),
        velocity: 0,
        availability: 100, // percentage
        preferences: {},
        strengths: [],
        timeZone: member.timeZone
      };
      
      // Get current assignments
      const activeTasks = await linear.getUserTasks(member.id, {
        filter: { state: ['in_progress', 'todo'] }
      });
      team[member.id].currentTasks = activeTasks;
      
      // Get historical data
      const completedTasks = await linear.getUserTasks(member.id, {
        filter: { state: 'done' },
        since: '3 months ago'
      });
      team[member.id].completedTasks = completedTasks;
      
      // Analyze git contributions
      const gitStats = await this.analyzeGitContributions(member.email);
      team[member.id].skills = gitStats.technologies;
      team[member.id].codeContributions = gitStats.contributions;
    }
    
    return team;
  }
  
  async analyzeGitContributions(email) {
    // Get commit history
    const commits = await exec(`git log --author="${email}" --since="6 months ago" --pretty=format:"%H"`);
    const commitHashes = commits.split('\n').filter(Boolean);
    
    const stats = {
      technologies: new Set(),
      contributions: {
        frontend: 0,
        backend: 0,
        database: 0,
        devops: 0,
        testing: 0,
        documentation: 0
      },
      filesChanged: new Map()
    };
    
    // Analyze each commit
    for (const hash of commitHashes.slice(0, 100)) { // Limit to recent 100 commits
      const files = await exec(`git show --name-only --pretty=format: ${hash}`);
      const fileList = files.split('\n').filter(Boolean);
      
      for (const file of fileList) {
        // Track technologies
        if (file.match(/\.(js|jsx|ts|tsx)$/)) stats.technologies.add('JavaScript');
        if (file.match(/\.(py)$/)) stats.technologies.add('Python');
        if (file.match(/\.(java)$/)) stats.technologies.add('Java');
        if (file.match(/\.(go)$/)) stats.technologies.add('Go');
        
        // Categorize contributions
        if (file.match(/\/(components|views|pages|frontend)\//)) stats.contributions.frontend++;
        if (file.match(/\/(api|server|backend|services)\//)) stats.contributions.backend++;
        if (file.match(/\/(migrations|schemas|models)\//)) stats.contributions.database++;
        if (file.match(/\/(deploy|docker|k8s|.github)\//)) stats.contributions.devops++;
        if (file.match(/\.(test|spec)\./)) stats.contributions.testing++;
        if (file.match(/\.(md|docs)\//)) stats.contributions.documentation++;
        
        // Track file expertise
        stats.filesChanged.set(file, (stats.filesChanged.get(file) || 0) + 1);
      }
    }
    
    return stats;
  }
}
```

### 2. Calculate Workload Metrics
Analyze current workload distribution:

```javascript
class WorkloadCalculator {
  calculateWorkload(teamMember) {
    const metrics = {
      currentPoints: 0,
      currentTasks: teamMember.currentTasks.length,
      inProgressPoints: 0,
      todoPoints: 0,
      blockedTasks: 0,
      overdueTasksk: 0,
      workloadScore: 0, // 0-100
      capacity: 0
    };
    
    // Sum story points
    for (const task of teamMember.currentTasks) {
      const points = task.estimate || 3; // Default to 3 if no estimate
      metrics.currentPoints += points;
      
      if (task.state === 'in_progress') {
        metrics.inProgressPoints += points;
      } else if (task.state === 'todo') {
        metrics.todoPoints += points;
      }
      
      if (task.blockedBy?.length > 0) {
        metrics.blockedTasks++;
      }
      
      if (task.dueDate && new Date(task.dueDate) < new Date()) {
        metrics.overdueTasksk++;
      }
    }
    
    // Calculate velocity from historical data
    const velocity = this.calculateVelocity(teamMember.completedTasks);
    
    // Calculate workload score (0-100)
    // Higher score = more overloaded
    metrics.workloadScore = Math.min(100, (metrics.currentPoints / velocity.average) * 100);
    
    // Calculate remaining capacity
    metrics.capacity = Math.max(0, velocity.average - metrics.currentPoints);
    
    // Adjust for blocked tasks
    if (metrics.blockedTasks > 0) {
      metrics.workloadScore *= 1.2; // Increase workload score for blocked work
    }
    
    return metrics;
  }
  
  calculateVelocity(completedTasks) {
    // Group by sprint/week
    const tasksByWeek = new Map();
    
    for (const task of completedTasks) {
      const weekKey = this.getWeekKey(task.completedAt);
      if (!tasksByWeek.has(weekKey)) {
        tasksByWeek.set(weekKey, []);
      }
      tasksByWeek.get(weekKey).push(task);
    }
    
    // Calculate points per week
    const weeklyPoints = [];
    for (const [week, tasks] of tasksByWeek) {
      const points = tasks.reduce((sum, t) => sum + (t.estimate || 0), 0);
      weeklyPoints.push(points);
    }
    
    return {
      average: weeklyPoints.reduce((a, b) => a + b, 0) / weeklyPoints.length || 10,
      min: Math.min(...weeklyPoints) || 5,
      max: Math.max(...weeklyPoints) || 15,
      trend: this.calculateTrend(weeklyPoints)
    };
  }
}
```

### 3. Skill Matching Algorithm
Match tasks to team members based on skills:

```javascript
class SkillMatcher {
  calculateSkillMatch(task, teamMember) {
    const taskRequirements = this.extractTaskRequirements(task);
    const memberSkills = this.consolidateSkills(teamMember);
    
    let matchScore = 0;
    let maxScore = 0;
    
    // Technology match
    for (const tech of taskRequirements.technologies) {
      maxScore += 10;
      if (memberSkills.technologies.has(tech)) {
        matchScore += 10;
      } else if (this.isRelatedTechnology(tech, memberSkills.technologies)) {
        matchScore += 5;
      }
    }
    
    // Domain expertise match
    if (taskRequirements.domain) {
      maxScore += 20;
      const domainExperience = this.getDomainExperience(teamMember, taskRequirements.domain);
      matchScore += Math.min(20, domainExperience * 2);
    }
    
    // Task type preference
    maxScore += 10;
    if (memberSkills.preferences[taskRequirements.type] > 0.7) {
      matchScore += 10;
    } else if (memberSkills.preferences[taskRequirements.type] > 0.4) {
      matchScore += 5;
    }
    
    // Recent similar work
    const similarTasks = this.findSimilarCompletedTasks(teamMember, task);
    if (similarTasks.length > 0) {
      maxScore += 15;
      matchScore += Math.min(15, similarTasks.length * 3);
    }
    
    return {
      score: maxScore > 0 ? (matchScore / maxScore) : 0,
      matches: {
        technologies: this.getTechMatches(taskRequirements, memberSkills),
        domain: taskRequirements.domain && memberSkills.domains.includes(taskRequirements.domain),
        experience: similarTasks.length
      }
    };
  }
  
  extractTaskRequirements(task) {
    const requirements = {
      technologies: new Set(),
      domain: null,
      type: 'feature',
      complexity: 'medium',
      skills: []
    };
    
    // Extract from title and description
    const text = `${task.title} ${task.description}`.toLowerCase();
    
    // Technology detection
    const techPatterns = {
      'react': /react|jsx|component/,
      'node': /node|express|npm/,
      'python': /python|django|flask/,
      'database': /sql|database|query|migration/,
      'api': /api|rest|graphql|endpoint/,
      'frontend': /ui|ux|css|style|layout/,
      'backend': /server|backend|service/,
      'devops': /deploy|docker|k8s|ci\/cd/
    };
    
    for (const [tech, pattern] of Object.entries(techPatterns)) {
      if (pattern.test(text)) {
        requirements.technologies.add(tech);
      }
    }
    
    // Domain detection
    if (text.includes('auth') || text.includes('login')) requirements.domain = 'authentication';
    if (text.includes('payment') || text.includes('billing')) requirements.domain = 'payments';
    if (text.includes('user') || text.includes('profile')) requirements.domain = 'users';
    
    // Type detection
    if (task.labels.some(l => l.name === 'bug')) requirements.type = 'bug';
    if (task.labels.some(l => l.name === 'refactor')) requirements.type = 'refactor';
    
    return requirements;
  }
}
```

### 4. Load Balancing Algorithm
Distribute tasks optimally:

```javascript
class LoadBalancer {
  balanceTasks(tasks, team, constraints = {}) {
    const assignments = new Map(); // task -> assignee
    const workloads = new Map(); // assignee -> current load
    
    // Initialize workloads
    for (const [memberId, member] of Object.entries(team)) {
      workloads.set(memberId, this.calculateWorkload(member));
    }
    
    // Sort tasks by priority and size
    const sortedTasks = tasks.sort((a, b) => {
      const priorityDiff = (a.priority || 3) - (b.priority || 3);
      if (priorityDiff !== 0) return priorityDiff;
      return (b.estimate || 3) - (a.estimate || 3); // Larger tasks first
    });
    
    // Assign tasks using modified bin packing algorithm
    for (const task of sortedTasks) {
      const candidates = this.findCandidates(task, team, workloads, constraints);
      
      if (candidates.length === 0) {
        console.warn(`No suitable assignee found for task: ${task.title}`);
        continue;
      }
      
      // Select best candidate
      const best = candidates.reduce((a, b) => 
        a.score > b.score ? a : b
      );
      
      assignments.set(task.id, best.memberId);
      
      // Update workload
      const currentLoad = workloads.get(best.memberId);
      currentLoad.currentPoints += task.estimate || 3;
      currentLoad.workloadScore = this.recalculateWorkloadScore(currentLoad);
    }
    
    return {
      assignments,
      balance: this.calculateBalance(workloads),
      warnings: this.generateWarnings(workloads, team)
    };
  }
  
  findCandidates(task, team, currentWorkloads, constraints) {
    const candidates = [];
    
    for (const [memberId, member] of Object.entries(team)) {
      const workload = currentWorkloads.get(memberId);
      
      // Check hard constraints
      if (constraints.maxLoad && workload.currentPoints >= constraints.maxLoad) {
        continue;
      }
      
      if (constraints.requireSkill && !member.skills.has(constraints.requireSkill)) {
        continue;
      }
      
      // Calculate assignment score
      const skillMatch = this.calculateSkillMatch(task, member);
      const loadScore = 1 - (workload.workloadScore / 100); // Prefer less loaded
      const velocityScore = member.velocity / 20; // Normalize velocity
      
      // Weighted score
      const score = (
        skillMatch.score * 0.4 +
        loadScore * 0.4 +
        velocityScore * 0.2
      );
      
      candidates.push({
        memberId,
        memberName: member.name,
        score,
        factors: {
          skill: skillMatch.score,
          load: loadScore,
          velocity: velocityScore
        }
      });
    }
    
    return candidates.sort((a, b) => b.score - a.score);
  }
  
  calculateBalance(workloads) {
    const loads = Array.from(workloads.values()).map(w => w.currentPoints);
    const avg = loads.reduce((a, b) => a + b, 0) / loads.length;
    const variance = loads.reduce((sum, load) => sum + Math.pow(load - avg, 2), 0) / loads.length;
    const stdDev = Math.sqrt(variance);
    
    return {
      average: avg,
      standardDeviation: stdDev,
      balanceScore: 100 - Math.min(100, (stdDev / avg) * 100), // 0-100, higher is better
      distribution: this.getDistribution(loads)
    };
  }
}
```

### 5. Visualization Functions
Create visual representations of workload:

```javascript
function visualizeWorkload(team, assignments) {
  const output = [];
  
  // Team workload bar chart
  output.push('## Team Workload Distribution\n');
  
  const maxPoints = Math.max(...Object.values(team).map(m => m.currentPoints));
  
  for (const [id, member] of Object.entries(team)) {
    const points = member.currentPoints;
    const capacity = member.velocity.average;
    const utilization = (points / capacity) * 100;
    
    // Create visual bar
    const barLength = Math.round((points / maxPoints) * 40);
    const bar = '█'.repeat(barLength) + '░'.repeat(40 - barLength);
    
    // Color coding
    let status = '🟢'; // Green
    if (utilization > 120) status = '🔴'; // Red - overloaded
    else if (utilization > 90) status = '🟡'; // Yellow - near capacity
    
    output.push(`${status} ${member.name.padEnd(15)} ${bar} ${points}/${capacity} pts (${Math.round(utilization)}%)`);
  }
  
  // Task distribution matrix
  output.push('\n## Recommended Task Assignments\n');
  output.push('| Task | Assignee | Skill Match | Load After | Reason |');
  output.push('|------|----------|-------------|------------|---------|');
  
  for (const [taskId, assignment] of assignments) {
    const task = findTask(taskId);
    const member = team[assignment.memberId];
    const newLoad = member.currentPoints + (task.estimate || 3);
    const loadPercent = Math.round((newLoad / member.velocity.average) * 100);
    
    output.push(
      `| ${task.title.substring(0, 30)}... | ${member.name} | ${Math.round(assignment.skillMatch * 100)}% | ${loadPercent}% | ${assignment.reason} |`
    );
  }
  
  return output.join('\n');
}

function generateGanttChart(team, timeframe = 14) {
  const chart = [];
  const today = new Date();
  
  chart.push('## Sprint Timeline (Next 2 Weeks)\n');
  chart.push('```');
  
  // Header
  const days = [];
  for (let i = 0; i < timeframe; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    days.push(date.toLocaleDateString('en', { weekday: 'short' })[0]);
  }
  chart.push('        ' + days.join(' '));
  
  // Team member rows
  for (const [id, member] of Object.entries(team)) {
    const tasks = member.currentTasks.sort((a, b) => 
      new Date(a.dueDate || '2099-01-01') - new Date(b.dueDate || '2099-01-01')
    );
    
    let timeline = '';
    let currentDay = 0;
    
    for (const task of tasks) {
      const duration = task.estimate || 3;
      const taskChar = task.priority === 1 ? '█' : '▓';
      timeline += ' '.repeat(Math.max(0, currentDay)) + taskChar.repeat(duration);
      currentDay += duration;
    }
    
    chart.push(`${member.name.padEnd(8)}${timeline.padEnd(timeframe, '·')}`);
  }
  
  chart.push('```');
  return chart.join('\n');
}
```

### 6. Optimization Suggestions
Generate actionable recommendations:

```javascript
class WorkloadOptimizer {
  generateSuggestions(team, currentAssignments, constraints) {
    const suggestions = [];
    const metrics = this.analyzeCurrentState(team);
    
    // Check for overloaded members
    for (const [id, member] of Object.entries(team)) {
      if (member.workloadScore > 90) {
        suggestions.push({
          type: 'overload',
          priority: 'high',
          member: member.name,
          action: `Redistribute ${member.currentPoints - member.velocity.average} points from ${member.name}`,
          tasks: this.findTasksToReassign(member)
        });
      }
    }
    
    // Check for underutilized members
    for (const [id, member] of Object.entries(team)) {
      if (member.workloadScore < 50 && member.availability > 80) {
        suggestions.push({
          type: 'underutilized',
          priority: 'medium',
          member: member.name,
          action: `${member.name} has ${member.capacity} points available capacity`,
          candidates: this.findTasksForMember(member, team)
        });
      }
    }
    
    // Check for skill mismatches
    const mismatches = this.findSkillMismatches(currentAssignments, team);
    for (const mismatch of mismatches) {
      suggestions.push({
        type: 'skill_mismatch',
        priority: 'medium',
        action: `Consider reassigning "${mismatch.task.title}" from ${mismatch.current} to ${mismatch.suggested}`,
        reason: mismatch.reason
      });
    }
    
    // Sprint risk analysis
    const risks = this.analyzeSprintRisks(team);
    for (const risk of risks) {
      suggestions.push({
        type: 'risk',
        priority: risk.severity,
        action: risk.mitigation,
        impact: risk.impact
      });
    }
    
    return suggestions;
  }
  
  findTasksToReassign(overloadedMember) {
    // Find lowest priority tasks that can be reassigned
    const tasks = overloadedMember.currentTasks
      .filter(t => t.state === 'todo' && !t.blockedBy?.length)
      .sort((a, b) => (b.priority || 3) - (a.priority || 3));
    
    const toReassign = [];
    let pointsToRemove = overloadedMember.currentPoints - overloadedMember.velocity.average;
    
    for (const task of tasks) {
      if (pointsToRemove <= 0) break;
      toReassign.push(task);
      pointsToRemove -= (task.estimate || 3);
    }
    
    return toReassign;
  }
}
```

### 7. Error Handling
```javascript
// Handle missing Linear access
if (!linear.available) {
  console.error("Linear MCP tool not available");
  // Fall back to manual input or cached data
}

// Handle team member availability
const availability = {
  async checkAvailability(member) {
    // Check calendar integration if available
    try {
      const calendar = await getCalendarEvents(member.email);
      const outOfOffice = calendar.filter(e => e.type === 'ooo');
      return this.calculateAvailability(outOfOffice);
    } catch (error) {
      console.warn(`Could not check calendar for ${member.name}`);
      return 100; // Assume full availability
    }
  }
};

// Handle incomplete data
if (!task.estimate) {
  console.warn(`Task "${task.title}" has no estimate, using default: 3 points`);
  task.estimate = 3;
}
```

## Example Output

```
Analyzing team workload and generating recommendations...

👥 Team Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Sprint: Sprint 23 (5 days remaining)
Team Size: 5 engineers
Total Capacity: 65 points
Current Load: 71 points (109% capacity)

📊 Individual Workload
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Alice Chen      ████████████████████████████████░░░░░░░░ 18/13 pts (138%)
   In Progress: 2 tasks (8 pts) | Todo: 3 tasks (10 pts)
   ⚠️ Overloaded by 5 points

🟡 Bob Smith       ████████████████████████████░░░░░░░░░░░░ 14/15 pts (93%)
   In Progress: 1 task (5 pts) | Todo: 3 tasks (9 pts)
   ✓ Near optimal capacity

🟢 Carol Davis     ████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 8/12 pts (67%)
   In Progress: 1 task (3 pts) | Todo: 2 tasks (5 pts)
   ✓ Has 4 points available capacity

🟢 David Kim       ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░ 7/10 pts (70%)
   In Progress: 1 task (4 pts) | Todo: 1 task (3 pts)
   ✓ Has 3 points available capacity

🔴 Eve Johnson     ██████████████████████████████████░░░░░░ 17/15 pts (113%)
   In Progress: 3 tasks (12 pts) | Todo: 2 tasks (5 pts)
   ⚠️ Slightly overloaded

🎯 Optimization Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 🔴 HIGH PRIORITY: Redistribute Alice's workload
   Action: Move 2 tasks (5 points) to other team members
   Suggested reassignments:
   • "API Rate Limiting" (3 pts) → Carol (has backend expertise)
   • "Update User Dashboard" (2 pts) → David (worked on similar feature)

2. 🟡 MEDIUM: Optimize skill matching
   • "Payment Webhook Integration" assigned to Eve
     Better match: Bob (85% skill match vs 60%)
     Bob has extensive webhook experience

3. 🟡 MEDIUM: Balance in-progress items
   Eve has 3 tasks in progress (risk of context switching)
   Recommendation: Complete 1 before starting new work

4. 🟢 LOW: Utilize available capacity
   Carol and David have 7 points combined capacity
   Suggested tasks from backlog:
   • "Add Email Notifications" (3 pts) → Carol
   • "Optimize Search Query" (2 pts) → David

📈 Proposed Rebalanced Distribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After rebalancing:
🟢 Alice Chen      ████████████████████████░░░░░░░░░░░░░░░░ 13/13 pts (100%)
🟢 Bob Smith       ████████████████████████████░░░░░░░░░░░░ 14/15 pts (93%)
🟢 Carol Davis     ████████████████████░░░░░░░░░░░░░░░░░░░░ 11/12 pts (92%)
🟢 David Kim       ████████████████████░░░░░░░░░░░░░░░░░░░░ 9/10 pts (90%)
🟢 Eve Johnson     ████████████████████████░░░░░░░░░░░░░░░░ 12/15 pts (80%)

Balance Score: 85/100 (Good) → 94/100 (Excellent)
Risk Level: High → Low

📅 Sprint Timeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        M T W T F M T W T F M T W T
Alice   ███▓▓▓░░░░░░░░
Bob     ████▓▓▓▓▓░░░░░
Carol   ██▓▓▓░░░░░░░░░
David   ███▓░░░░░░░░░░
Eve     ████████▓▓░░░░

Legend: █ High Priority | ▓ Normal | ░ Available

⚡ Quick Actions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Run: claude "Reassign task LIN-234 from Alice to Carol"
2. Run: claude "Update sprint capacity to account for Eve's half day Friday"
3. Run: claude "Create balanced task list for next sprint planning"
```

## Advanced Features

### Capacity Planning
```bash
# Plan next sprint with holidays and time off
claude "Plan sprint 24 capacity - Alice off Monday, Bob at conference Wed-Thu"
```

### Skill Development
```bash
# Identify learning opportunities
claude "Suggest tasks for Carol to learn React based on current workload"
```

### Team Performance
```bash
# Analyze team velocity trends
claude "Show team velocity trends and predict sprint 24 capacity"
```

## Tips
- Update availability regularly (vacations, meetings)
- Consider time zones for distributed teams
- Track actual vs estimated to improve predictions
- Use skill matching to grow team capabilities
- Monitor workload balance weekly, not just at sprint start
- Consider task dependencies in assignments
- Factor in code review time for junior developers