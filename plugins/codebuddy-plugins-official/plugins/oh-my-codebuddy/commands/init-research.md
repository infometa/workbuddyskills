---
description: Initialize research documentation with TODO markers for external research needs
argument-hint: "[--create-new] [--max-depth=N]"
---

# /init-research

Generate hierarchical `deep-search.md` files. Root + complexity-scored subdirectories. Identifies areas requiring external research and marks them with `TODO: RESEARCH HERE`.

## Usage

```
/init-research                      # Update mode: modify existing + create new where warranted
/init-research --create-new         # Read existing → remove all → regenerate from scratch
/init-research --max-depth=2        # Limit directory depth (default: 3)
```

---

## Workflow (High-Level)

1. **Discovery + Analysis** (concurrent)
   - Fire background explore agents immediately
   - Main session: bash structure + LSP codemap + read existing CODEBUDDY.md/deep-search.md
   - Identify external dependencies, APIs, frameworks, libraries
2. **Research Need Identification** - Identify areas requiring external research
3. **Generate** - Root first, then subdirs in parallel, with TODO markers
4. **Review** - Validate TODO markers, ensure research points are specific

<critical>
**TodoWrite ALL phases. Mark in_progress → completed in real-time.**
```
TodoWrite([
  { id: "discovery", content: "Fire explore agents + LSP codemap + identify external dependencies", status: "pending", priority: "high" },
  { id: "research_identification", content: "Identify areas requiring external research", status: "pending", priority: "high" },
  { id: "generate", content: "Generate deep-search.md files (root + subdirs) with TODO markers", status: "pending", priority: "high" },
  { id: "review", content: "Validate TODO markers and research points", status: "pending", priority: "medium" }
])
```
</critical>

---

## Phase 1: Discovery + Analysis (Concurrent)

**Mark "discovery" as in_progress.**

### Fire Background Explore Agents IMMEDIATELY

Don't wait—these run async while main session works.

```
// Fire all at once, collect results later
background_task(agent="explore", prompt="External dependencies: FIND package.json, requirements.txt, go.mod, Cargo.toml → LIST all external libraries and frameworks")
background_task(agent="explore", prompt="API integrations: FIND API calls, HTTP clients, SDK usage → LIST external APIs and services")
background_task(agent="explore", prompt="Technology stack: IDENTIFY frameworks, libraries, tools → LIST technologies that need documentation research")
background_task(agent="explore", prompt="Architecture patterns: FIND design patterns, architectural decisions → IDENTIFY patterns that need comparison/analysis")
background_task(agent="explore", prompt="Competitive analysis: FIND references to competitors, alternatives → LIST areas needing competitive research")
background_task(agent="explore", prompt="Industry standards: FIND compliance requirements, standards → LIST standards needing research")
```

<dynamic-agents>
**DYNAMIC AGENT SPAWNING**: After bash analysis, spawn ADDITIONAL explore agents based on project scale:

| Factor | Threshold | Additional Agents |
|--------|-----------|-------------------|
| **Total files** | >100 | +1 per 100 files |
| **Total lines** | >10k | +1 per 10k lines |
| **Directory depth** | ≥4 | +2 for deep exploration |
| **Large files (>500 lines)** | >10 files | +1 for complexity hotspots |
| **Monorepo** | detected | +1 per package/workspace |
| **Multiple languages** | >1 | +1 per language |
| **External dependencies** | >20 | +1 per 20 dependencies |

```bash
# Measure project scale first
total_files=$(find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l)
total_lines=$(find . -type f \( -name "*.ts" -o -name "*.py" -o -name "*.go" \) -not -path '*/node_modules/*' -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
large_files=$(find . -type f \( -name "*.ts" -o -name "*.py" \) -not -path '*/node_modules/*' -exec wc -l {} + 2>/dev/null | awk '$1 > 500 {count++} END {print count+0}')
max_depth=$(find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' | awk -F/ '{print NF}' | sort -rn | head -1)
# Count external dependencies
if [ -f "package.json" ]; then
  deps=$(grep -E '"(dependencies|devDependencies)"' package.json | wc -l)
elif [ -f "requirements.txt" ]; then
  deps=$(grep -v '^#' requirements.txt | grep -v '^$' | wc -l)
fi
```
</dynamic-agents>

### Main Session: Concurrent Analysis

**While background agents run**, main session does:

#### 1. Bash Structural Analysis
```bash
# Directory depth + file counts
find . -type d -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/venv/*' -not -path '*/dist/*' -not -path '*/build/*' | awk -F/ '{print NF-1}' | sort -n | uniq -c

# Files per directory (top 30)
find . -type f -not -path '*/\.*' -not -path '*/node_modules/*' | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -30

# Code concentration by extension
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.go" -o -name "*.rs" \) -not -path '*/node_modules/*' | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -20

# Existing CODEBUDDY.md / deep-search.md
find . -type f \( -name "CODEBUDDY.md" -o -name "AGENTS.md" -o -name "deep-search.md" \) -not -path '*/node_modules/*' 2>/dev/null

# External dependencies
find . -type f \( -name "package.json" -o -name "requirements.txt" -o -name "go.mod" -o -name "Cargo.toml" -o -name "pom.xml" \) -not -path '*/node_modules/*' 2>/dev/null
```

#### 2. Read Existing Documentation
```
For each existing file found:
  Read(filePath=file)
  Extract: key insights, research needs, existing TODO markers
  Store in EXISTING_DOCS map
```

If `--create-new`: Read all existing first (preserve context) → then delete all → regenerate.

#### 3. LSP Codemap (if available)
```
lsp_servers()  # Check availability

# Entry points (parallel)
lsp_document_symbols(filePath="src/index.ts")
lsp_document_symbols(filePath="main.py")

# External imports (parallel)
lsp_workspace_symbols(filePath=".", query="import")
lsp_workspace_symbols(filePath=".", query="require")
lsp_workspace_symbols(filePath=".", query="from")

# API calls and external services
lsp_workspace_symbols(filePath=".", query="fetch")
lsp_workspace_symbols(filePath=".", query="axios")
lsp_workspace_symbols(filePath=".", query="http")
```

**LSP Fallback**: If unavailable, rely on explore agents + AST-grep.

### Collect Background Results

```
// After main session analysis done, collect all task results
for each task_id: background_output(task_id="...")
```

**Merge: bash + LSP + existing + explore findings. Mark "discovery" as completed.**

---

## Phase 2: Research Need Identification

**Mark "research_identification" as in_progress.**

### Identify Research Needs

For each directory/module, identify areas requiring external research:

#### Research Categories

1. **External Libraries/Frameworks**
   - Official documentation and best practices
   - Version compatibility and migration guides
   - Performance characteristics and benchmarks
   - Security considerations

2. **API Integrations**
   - API documentation and usage examples
   - Authentication and authorization patterns
   - Rate limiting and error handling
   - Integration best practices

3. **Technology Stack**
   - Technology comparison and selection rationale
   - Industry standards and compliance
   - Alternative solutions and trade-offs
   - Migration paths and upgrade strategies

4. **Architecture Patterns**
   - Design pattern comparisons
   - Architectural decision records (ADRs)
   - Industry best practices
   - Performance and scalability considerations

5. **Competitive Analysis**
   - Competitor feature analysis
   - Market positioning
   - Differentiation points
   - Industry trends

6. **Open Source Projects**
   - Project architecture and design
   - Implementation details
   - Community practices
   - Contribution guidelines

### Research Need Scoring

| Factor | Weight | High Threshold | Research Need |
|--------|--------|----------------|---------------|
| External dependencies | 3x | >5 deps | High |
| API integrations | 3x | >3 APIs | High |
| Complex patterns | 2x | Uncommon patterns | Medium |
| Technology choices | 2x | Multiple alternatives | Medium |
| Industry standards | 1x | Compliance required | Low |

### Decision Rules

| Score | Action |
|-------|--------|
| **Root (.)** | ALWAYS create deep-search.md |
| **>15** | Create deep-search.md with TODO markers |
| **8-15** | Create if distinct domain with research needs |
| **<8** | Skip (parent covers) |

**Mark "research_identification" as completed.**

---

## Phase 3: Generate deep-search.md

**Mark "generate" as in_progress.**

### Root deep-search.md (Full Treatment)

Generate comprehensive root deep-search.md with:

1. **Project Overview**
   - Project purpose and scope
   - Technology stack summary
   - Key external dependencies

2. **Architecture Analysis**
   - System architecture
   - Core modules and their relationships
   - Integration points

3. **External Dependencies**
   - List of external libraries/frameworks
   - TODO markers for each major dependency

4. **API Integrations**
   - List of external APIs
   - TODO markers for API documentation research

5. **Technology Decisions**
   - Key technology choices
   - TODO markers for comparison/analysis

6. **Research Areas**
   - Areas requiring competitive analysis
   - Industry standards research needs
   - Open source project analysis needs

### TODO Marker Format

For each research need, create a TODO marker:

```markdown
## TODO: RESEARCH HERE
**文件位置**: `path/to/file1.ts`, `path/to/file2.py`
**调研内容**:
1. [Specific research point 1 - be concrete and actionable]
2. [Specific research point 2 - focus on what needs to be learned]
3. [Specific research point 3 - include context and purpose]
4. [Specific research point 4 - maximum 5 points]
5. [Specific research point 5 - if needed]
```

**Rules for TODO markers**:
- Maximum 5 research points per TODO
- Each point should be specific and actionable
- Include file locations where the research is needed
- Focus on what information is needed, not how to find it
- Group related research needs together

### Subdirectory deep-search.md (Parallel)

Launch document-writer agents for each location:

```
for loc in DEEP_SEARCH_LOCATIONS (except root):
  background_task(agent="document-writer", prompt=`
    Generate deep-search.md for: ${loc.path}
    - Reason: ${loc.reason}
    - 30-80 lines max
    - NEVER repeat parent content
    - Sections: OVERVIEW (1 line), KEY DEPENDENCIES, API INTEGRATIONS, RESEARCH NEEDS
    - Include TODO: RESEARCH HERE markers for external research needs
    - Format: Follow the TODO marker format exactly
  `)
```

**Wait for all. Mark "generate" as completed.**

---

## Phase 4: Review & Validate

**Mark "review" as in_progress.**

For each generated file:
- Validate TODO marker format
- Ensure research points are specific (not generic)
- Verify file locations are accurate
- Check that research points don't exceed 5 per TODO
- Remove duplicate research needs
- Ensure research needs are actually external (not internal code analysis)

**Mark "review" as completed.**

---

## Research Need Identification Guidelines

### When to Mark for Research

**Mark for research when**:
- External library/framework needs official documentation
- API integration requires detailed usage examples
- Technology choice needs comparison with alternatives
- Architecture pattern needs industry best practices
- Competitive analysis is needed
- Industry standards or compliance requirements
- Open source project architecture analysis

**Do NOT mark for research when**:
- Internal code analysis (use explore agents)
- Code structure understanding (use LSP/explore)
- Local configuration (use codebase analysis)
- Internal patterns (use codebase analysis)

### Research Point Quality

**Good research points**:
- "AWS Bedrock Agent Core 的完整 API 文档和最佳实践"
- "与其他 AI Agent 平台的对比分析（功能、性能、成本）"
- "实际生产环境中的使用案例和性能指标"
- "安全性和权限管理的最佳实践"
- "成本优化策略和计费模式"

**Bad research points**:
- "了解这个库" (too vague)
- "研究 API" (not specific)
- "看看文档" (not actionable)
- "对比一下" (no context)

---

## Anti-Patterns

- **Generic research points**: MUST be specific and actionable
- **Too many research points**: Maximum 5 per TODO marker
- **Internal analysis marked as research**: Use explore agents for internal code
- **Missing file locations**: Always include file locations
- **Duplicate research needs**: Group related needs together
- **Over-documenting**: Not every dir needs deep-search.md
- **Redundancy**: Child never repeats parent research needs

---

## Output Structure

```
项目根目录/
├── deep-search.md                    # 根目录研究文档
├── subdir1/
│   └── deep-search.md               # 子目录研究文档（如果评分足够）
└── subdir2/
    └── deep-search.md               # 子目录研究文档（如果评分足够）
```

Each `deep-search.md` contains:
- Project/module overview
- Key dependencies and integrations
- TODO: RESEARCH HERE markers with specific research points
- File locations for each research need
