---
description: Deep research loop that processes all TODO: RESEARCH HERE markers, performs external research, and generates professional wiki-format content
argument-hint: "[--max-iterations=N] [--completion-promise=TEXT]"
---

# /ralph-loop-research

You are starting a Research Loop - a self-referential research loop that processes all `TODO: RESEARCH HERE` markers in `deep-search.md` files, performs deep external research, and generates professional wiki-format content.

## Usage

```
/ralph-loop-research                      # Default: 3 iterations, completion promise "ALL_RESEARCHED"
/ralph-loop-research --max-iterations=5   # Custom max iterations
/ralph-loop-research --completion-promise="RESEARCH_COMPLETE"  # Custom completion promise
```

---

## How Research Loop Works

1. **Scan Phase**: Find all `TODO: RESEARCH HERE` markers in `deep-search.md` files
2. **Research Phase**: For each TODO marker, perform deep external research
3. **Generation Phase**: Generate professional wiki-format content
4. **Replacement Phase**: Replace TODO markers with researched content
5. **Link Discovery**: If links are found, continue deep research
6. **Loop**: Repeat until all TODOs are replaced (default max 3 iterations)
7. **Completion**: Output completion promise when all research is done

## Rules

- Focus on completing ALL research, not partially
- Don't output the completion promise until ALL `TODO: RESEARCH HERE` markers are replaced
- Each iteration should make meaningful progress
- Use todos to track research progress
- Save all research notes to `.research/` directory
- Generate professional, technical content (not generic summaries)

## Exit Conditions

1. **Completion**: Output `<promise>ALL_RESEARCHED</promise>` when ALL TODOs are replaced
2. **Max Iterations**: Loop stops automatically at limit (default 3)
3. **Cancel**: User runs `/cancel-ralph` command

---

## Phase 1: Initial Scan and Setup

**Mark "scan" as in_progress.**

### Find All deep-search.md Files

```bash
# Find all deep-search.md files
find . -name "deep-search.md" -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.gh-repo/*' 2>/dev/null
```

### Extract All TODO: RESEARCH HERE Markers

For each `deep-search.md` file:
1. Read the file
2. Find all `## TODO: RESEARCH HERE` sections
3. Extract:
   - File locations
   - Research points (1-5 points)
   - Context from surrounding content
4. Create TODO list with unique IDs

**TodoWrite initial research tasks:**
```
TodoWrite([
  { id: "scan", content: "Scan all deep-search.md files for TODO markers", status: "in_progress" },
  { id: "research_001", content: "Research: [topic from TODO 1]", status: "pending" },
  { id: "research_002", content: "Research: [topic from TODO 2]", status: "pending" },
  // ... for each TODO found
])
```

**Mark "scan" as completed.**

---

## Phase 2: Research Execution Loop

**Loop counter**: Start at 1, increment each iteration (max: default 3)

### For Each TODO Marker

#### Step 1: Prepare Research Context

- Read the original `deep-search.md` file
- Understand the context around the TODO marker
- Identify related files mentioned
- Understand what information is needed

#### Step 2: Perform Deep Research

**Use librarian agent for external research:**

```
Task: librarian
Input:
## Research Request
[Research point 1 from TODO]

## Context
- File locations: [file locations from TODO]
- Related context: [context from deep-search.md]
- Purpose: [why this research is needed]

## Research Requirements
1. Find official documentation and best practices
2. Find real-world usage examples
3. Find comparison/analysis if applicable
4. Find performance/security considerations
5. Find any other relevant information

## Output Format
Generate professional wiki-format content suitable for technical documentation.
```

**For each research point (up to 5 per TODO):**
- Perform separate research if points are distinct
- Or combine research if points are related
- Use web search if available for current information
- Use context7 for official documentation
- Use grep_app for GitHub examples

#### Step 3: Generate Wiki-Format Content

**Content Structure:**

```markdown
# [Research Topic]

## 概述
[Brief overview of what was researched]

## 详细内容
[Professional, technical content in wiki format]
[Include sections as appropriate]
[Use proper markdown formatting]
[Include code examples if relevant]
[Include diagrams if helpful]

## 关键发现
[Key findings and insights]

## 参考资源
- [Official Documentation](url)
- [GitHub Examples](url)
- [Related Articles](url)

## 实际应用
[How this applies to the codebase]
[File locations: path/to/file1, path/to/file2]
```

**Quality Requirements:**
- **Professional**: Use technical, professional language
- **Accurate**: Based on actual research, not assumptions
- **Structured**: Follow clear section organization
- **Complete**: Cover all research points from TODO
- **Referenced**: Include links to sources
- **Actionable**: Include how to apply findings

#### Step 4: Save Research Note

Save to `.research/research-XXX.md` where XXX is a unique identifier:

```bash
mkdir -p .research
# Save research note
```

**File naming**: `research-001.md`, `research-002.md`, etc.

**Include in research note:**
- Research topic
- Source TODO location
- File locations from TODO
- Research content
- Links found during research
- Any follow-up research needed

#### Step 5: Replace TODO Marker

In the original `deep-search.md` file:
1. Find the `## TODO: RESEARCH HERE` section
2. Replace it with the generated wiki-format content
3. Add a reference to the research note: `*[Research Note: research-XXX.md]*`

**Replacement format:**
```markdown
## [Research Topic]

[Generated wiki-format content]

*[Research Note: .research/research-XXX.md]*
```

---

## Phase 3: Link Discovery and Deep Research

### Detect Links in Research Content

After generating research content, scan for links:

```bash
# Extract all links from research content
grep -oP '\[.*?\]\(https?://[^\)]+\)' research-content.md
```

### Process Links

For each link found:

#### Type 1: GitHub Repository Links

**Pattern**: `https://github.com/owner/repo` or `github.com/owner/repo`

**Action**: Activate `gh-repo-research` agent

```
Task: gh-repo-research
Input:
## Repository URL
https://github.com/owner/repo

## Context
Found during research for [research topic]
Original TODO location: [deep-search.md location]

## Output Location
.research/gh-repo/repo-name/
```

**After gh-repo-research completes:**
- Reference the generated documentation in research note
- Add link to research note: `*[GitHub Analysis: .research/gh-repo/repo-name/]*`

#### Type 2: Regular Links

**Action**: Perform additional research on the link content

- Use web search to understand the linked content
- Extract key information
- Add to research note
- If the link leads to another research need, create a new TODO or note it for follow-up

---

## Phase 4: Loop Control and Validation

### After Each Iteration

1. **Rescan for Remaining TODOs**
   ```bash
   # Find remaining TODO: RESEARCH HERE markers
   grep -r "## TODO: RESEARCH HERE" . --include="deep-search.md" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.gh-repo
   ```

2. **Count Remaining TODOs**
   - If count > 0: Continue to next iteration
   - If count = 0: Check completion criteria

3. **Check Completion Criteria**
   - ✅ All `TODO: RESEARCH HERE` markers replaced
   - ✅ All links in research content processed
   - ✅ Research notes saved to `.research/` directory
   - ✅ Generated content includes:
     - Product function modules
     - Product architecture
     - Product value proposition
     - Competitive analysis (if applicable)

4. **Update Todo List**
   ```
   TodoWrite([
     { id: "iteration_1", content: "First research iteration", status: "completed" },
     { id: "remaining_todos", content: "Remaining TODO count: X", status: "in_progress" },
     // ... update research task statuses
   ])
   ```

### Loop Exit Conditions

**Exit with completion promise when:**
- All `TODO: RESEARCH HERE` markers are replaced
- All links are processed
- Required content sections are complete (function modules, architecture, value, competitive analysis)

**Exit with warning when:**
- Max iterations reached but TODOs remain
- Generate report of remaining TODOs
- Suggest manual intervention

---

## Phase 5: Final Validation

Before outputting completion promise:

### Validation Checklist

- [ ] Scanned all `deep-search.md` files
- [ ] Found all `TODO: RESEARCH HERE` markers
- [ ] Researched all TODO markers
- [ ] Generated wiki-format content for each
- [ ] Replaced all TODO markers in original files
- [ ] Processed all links found in research
- [ ] Activated `gh-repo-research` for GitHub links
- [ ] Saved all research notes to `.research/` directory
- [ ] Generated required content sections:
  - [ ] Product function modules
  - [ ] Product architecture
  - [ ] Product value proposition
  - [ ] Competitive analysis (if applicable)
- [ ] No remaining `TODO: RESEARCH HERE` markers exist

### Generate Final Report

```
## Research Loop Completion Report

### Statistics
- Total TODO markers found: X
- Total TODO markers researched: X
- Total research notes created: X
- GitHub repositories analyzed: X
- Links processed: X
- Iterations completed: X

### Research Notes Location
.research/
├── research-001.md
├── research-002.md
└── gh-repo/
    └── [repo-name]/

### Content Generated
- Product function modules: ✅
- Product architecture: ✅
- Product value: ✅
- Competitive analysis: ✅

### Files Updated
- [list of deep-search.md files updated]
```

---

## Research Quality Guidelines

### Content Quality

**Good research content:**
- Professional, technical language
- Based on actual research (not assumptions)
- Includes references and sources
- Provides actionable insights
- Connects research to codebase context

**Bad research content:**
- Generic summaries
- Assumptions without evidence
- Missing references
- Not connected to codebase
- Too brief or too verbose

### Wiki Format Requirements

- Use proper markdown structure
- Include clear section headings
- Use code blocks for examples
- Include diagrams (Mermaid) when helpful
- Reference actual code files
- Link to external resources
- Maintain professional tone

---

## Anti-Patterns

- **Skipping research**: Don't skip TODO markers, research all of them
- **Generic content**: Generate specific, technical content
- **Missing links**: Process all links found in research
- **Incomplete replacement**: Ensure TODO markers are fully replaced
- **No validation**: Always validate completion before exiting
- **Ignoring GitHub links**: Always activate gh-repo-research for GitHub repos
- **Not saving notes**: Always save research notes to .research directory

---

## Output Promise

When ALL research is complete:

```
<promise>ALL_RESEARCHED</promise>
```

This signals that:
- All `TODO: RESEARCH HERE` markers have been replaced
- All links have been processed
- All research notes are saved
- Required content sections are complete
