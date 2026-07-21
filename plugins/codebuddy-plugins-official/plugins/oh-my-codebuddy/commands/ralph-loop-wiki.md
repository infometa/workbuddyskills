---
description: Generate comprehensive technical wiki from PRD, research findings, and codebase analysis following wiki_template.md format
argument-hint: "[--max-iterations=N] [--completion-promise=TEXT] [--prd-path=PATH]"
---

# /ralph-loop-wiki

You are starting a Wiki Generation Loop - a self-referential loop that generates comprehensive technical wiki documentation by combining PRD, research findings (`.research/`), and codebase analysis (`CODEBUDDY.md`), following the `wiki_template.md` format.

## Usage

```
/ralph-loop-wiki                              # Default: 3 iterations, auto-detect PRD
/ralph-loop-wiki --max-iterations=5           # Custom max iterations
/ralph-loop-wiki --prd-path=docs/PRD.md      # Specify PRD file path
/ralph-loop-wiki --completion-promise="WIKI_COMPLETE"  # Custom completion promise
```

---

## How Wiki Loop Works

1. **Collection Phase**: Gather PRD, research content, and CODEBUDDY.md files
2. **Analysis Phase**: Analyze content and identify gaps
3. **Generation Phase**: Generate wiki following wiki_template.md format
4. **Validation Phase**: Check for missing content or research needs
5. **Research Activation**: If gaps found, activate `/init-research` or continue research
6. **Loop**: Repeat until content is complete (default max 3 iterations)
7. **Finalization**: Generate optimization suggestions and summary

## Rules

- Follow `wiki_template.md` format EXACTLY
- Don't output completion promise until content is complete after 3 validation cycles
- Each iteration must improve content completeness
- Use todos to track generation progress
- Integrate content from all sources (PRD, research, codebase)
- Generate professional, technical content

## Exit Conditions

1. **Completion**: Output `<promise>WIKI_COMPLETE</promise>` after 3 successful validation cycles
2. **Max Iterations**: Loop stops at limit (default 3)
3. **Cancel**: User runs `/cancel-ralph` command

---

## Phase 1: Content Collection

**Mark "collection" as in_progress.**

### 1.1 Locate and Read PRD

**Auto-detect PRD files:**
```bash
# Common PRD file locations
find . -type f \( -name "*PRD*.md" -o -name "*prd*.md" -o -name "*requirements*.md" -o -name "*spec*.md" \) \
  -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.research/*' 2>/dev/null
```

**Or use specified path:**
- If `--prd-path` provided, read that file
- If not found, search common locations
- If still not found, note as missing (will use codebase analysis only)

**Extract from PRD:**
- Product overview and purpose
- Core features and requirements
- User stories or use cases
- Technical requirements
- Success criteria

### 1.2 Read Research Content

**Read all research notes:**
```bash
# Find all research notes
find .research -name "research-*.md" -type f 2>/dev/null
find .research/gh-repo -name "*.md" -type f 2>/dev/null
```

**For each research note:**
- Read content
- Extract key findings
- Note research topics
- Extract links and references
- Organize by topic/category

**Research content categories:**
- Architecture analysis
- Technology stack research
- API documentation
- Competitive analysis
- Best practices
- GitHub repository analysis

### 1.3 Read CODEBUDDY.md Files

**Find all CODEBUDDY.md files:**
```bash
# Find CODEBUDDY.md files (from init-deep)
find . -name "CODEBUDDY.md" -o -name "AGENTS.md" -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.gh-repo/*' 2>/dev/null
```

**For each CODEBUDDY.md:**
- Read content
- Extract codebase structure
- Extract conventions and patterns
- Extract key modules and components
- Extract file locations and references

### 1.4 Read deep-search.md Files (if available)

**Find all deep-search.md files:**
```bash
find . -name "deep-search.md" -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null
```

**Extract:**
- Research areas (should be researched by now)
- Technology decisions
- External dependencies
- Integration points

**Mark "collection" as completed.**

---

## Phase 2: Content Analysis and Gap Identification

**Mark "analysis" as in_progress.**

### 2.1 Analyze Collected Content

**Create content map:**
- PRD content: [list topics covered]
- Research content: [list topics covered]
- Codebase content: [list topics covered]
- Missing content: [identify gaps]

### 2.2 Identify Content Gaps

**Check against wiki_template.md structure:**

Required sections (from wiki_template.md):
1. **架构概览** (Architecture Overview)
   - Core architecture diagram
   - Data flow diagram
   - Architecture characteristics

2. **核心模块详解** (Core Modules)
   - Module overview
   - Detailed module descriptions
   - Module relationships

3. **高频 API 详解** (High-Frequency APIs)
   - API overview
   - Detailed API documentation
   - Usage examples

4. **上层应用使用 SDK** (SDK Usage)
   - SDK overview
   - Integration patterns
   - Code examples

5. **多 Agent 协作** (Multi-Agent Collaboration)
   - Collaboration patterns
   - Workflow examples

6. **IAM 权限配置** (IAM Configuration)
   - Permission requirements
   - Configuration examples

7. **技术架构总结** (Technical Architecture Summary)
   - Technology stack
   - Performance considerations
   - Scalability
   - Extension points

8. **参考资源** (Reference Resources)
   - Official documentation
   - Project implementation references
   - Related resources
   - Best practices

**Gap identification:**
- Missing sections: [list]
- Incomplete sections: [list]
- Need more research: [list topics]
- Need codebase analysis: [list areas]

**Mark "analysis" as completed.**

---

## Phase 3: Wiki Generation

**Mark "generation" as in_progress.**

### 3.1 Generate Wiki Following Template

**Follow wiki_template.md structure exactly:**

```markdown
# [Product/Project Name] 技术分析文档

## 目录

1. [架构概览](#1-架构概览)
2. [核心模块详解](#2-核心模块详解)
3. [高频 API 详解](#3-高频-api-详解)
4. [上层应用使用 SDK](#4-上层应用使用-sdk)
5. [多 Agent 协作](#5-多-agent-协作)
6. [IAM 权限配置](#6-iam-权限配置)
7. [技术架构总结](#7-技术架构总结)
8. [参考资源](#8-参考资源)

---

## 1. 架构概览

[Product/System] 是 [description from PRD/research].

### 1.1 核心架构图

```mermaid
[Generate architecture diagram based on codebase analysis and research]
```

### 1.2 数据流图

```mermaid
[Generate data flow diagram]
```

### 1.3 架构特点

[Extract from research and codebase analysis]
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

---

## 2. 核心模块详解

[For each core module identified from CODEBUDDY.md and research]

### 2.X [Module Name]

**功能概述**：
[From codebase analysis and research]

**核心功能**：
- [Function 1]
- [Function 2]

**关键特性**：
- [Feature 1]
- [Feature 2]

**相关 API**：
- `API1`: [description]
- `API2`: [description]

**使用场景**：
- [Scenario 1]
- [Scenario 2]

---

## 3. 高频 API 详解

[From codebase analysis and API research]

### 3.1 API 概览

[API overview from research and codebase]

### 3.2 核心 API

[For each major API]

#### API Name

**功能**：[description]

**参数**：
- `param1`: [type] - [description]
- `param2`: [type] - [description]

**返回值**：
[Return type and structure]

**使用示例**：
```[language]
[Code example from codebase or research]
```

---

## 4. 上层应用使用 SDK

[From codebase analysis and integration research]

### 4.1 SDK 概览

[SDK overview]

### 4.2 集成模式

[Integration patterns from research]

### 4.3 代码示例

[Examples from codebase]

---

## 5. 多 Agent 协作

[If applicable, from codebase analysis]

[Collaboration patterns and workflows]

---

## 6. IAM 权限配置

[From research and codebase analysis]

### 6.1 权限要求

[Permission requirements]

### 6.2 配置示例

[Configuration examples]

---

## 7. 技术架构总结

### 7.1 技术栈

[From codebase analysis and research]

**后端**：
- [Technology 1]
- [Technology 2]

**前端**：
- [Technology 1]
- [Technology 2]

**服务**：
- [Service 1]
- [Service 2]

### 7.2 性能考虑

[From research]

### 7.3 扩展性

[From research and codebase analysis]

---

## 8. 参考资源

### 8.1 官方文档

[From research notes]

### 8.2 当前项目实现

[From CODEBUDDY.md file references]

### 8.3 相关资源

[From research notes]

### 8.4 最佳实践

[From research notes]

---
```

### 3.2 Content Integration Rules

**Priority order:**
1. **PRD content**: Use for product overview, features, requirements
2. **Research content**: Use for external knowledge, best practices, comparisons
3. **Codebase content**: Use for implementation details, file references, code examples
4. **Inference**: Only when necessary, clearly marked

**Integration guidelines:**
- Combine information from multiple sources
- Reference sources in content
- Use codebase analysis for implementation details
- Use research for external knowledge
- Use PRD for product context

**Mark "generation" as completed.**

---

## Phase 4: Validation and Gap Checking

**Mark "validation" as in_progress.**

### 4.1 Content Completeness Check

**Check each required section:**

- [ ] 架构概览: Has diagram, data flow, characteristics
- [ ] 核心模块详解: Covers all major modules
- [ ] 高频 API 详解: Documents main APIs
- [ ] 上层应用使用 SDK: Has integration patterns
- [ ] 多 Agent 协作: Covered if applicable
- [ ] IAM 权限配置: Has requirements and examples
- [ ] 技术架构总结: Complete technology stack
- [ ] 参考资源: Has official docs, project refs, best practices

### 4.2 Quality Check

- [ ] Professional, technical language
- [ ] Proper markdown formatting
- [ ] Code examples included where relevant
- [ ] Diagrams included where helpful
- [ ] File references are accurate
- [ ] Links are valid
- [ ] Content is accurate (not assumptions)

### 4.3 Research Need Check

**Scan generated wiki for:**
- Missing information markers
- "TODO" or "TBD" markers
- Incomplete sections
- Areas needing more research

**If research needs found:**
- Activate `/init-research` if needed
- Or continue with `/ralph-loop-research` if TODOs exist
- Note research needs for next iteration

**Mark "validation" as completed.**

---

## Phase 5: Loop Control

### Loop Counter

- **Iteration 1**: Initial generation
- **Iteration 2**: Fill gaps, improve content
- **Iteration 3**: Final validation and polish

### After Each Iteration

1. **Check Content Completeness**
   - All sections present: ✅
   - All sections complete: ✅
   - No research needs: ✅

2. **Check Quality**
   - Professional language: ✅
   - Accurate content: ✅
   - Proper formatting: ✅

3. **Update Todo List**
   ```
   TodoWrite([
     { id: "iteration_1", content: "First wiki generation", status: "completed" },
     { id: "content_gaps", content: "Identified gaps: [list]", status: "in_progress" },
     // ... update statuses
   ])
   ```

### Loop Exit Conditions

**Exit with completion promise after 3 successful validation cycles:**
- Iteration 1: Generated initial wiki
- Iteration 2: Filled gaps, improved content
- Iteration 3: Final validation passed

**All three iterations must pass validation before completion.**

---

## Phase 6: Finalization

### 6.1 Generate Optimization Suggestions

**Analyze generated wiki and suggest improvements:**

```markdown
## 优化建议

### 内容完善
- [Suggestion 1: specific area to expand]
- [Suggestion 2: missing information to add]

### 结构优化
- [Suggestion 1: section reorganization]
- [Suggestion 2: diagram additions]

### 技术深度
- [Suggestion 1: deeper technical analysis]
- [Suggestion 2: more code examples]

### 可读性
- [Suggestion 1: clarity improvements]
- [Suggestion 2: formatting enhancements]
```

### 6.2 Generate Summary

```markdown
## 总结

### 文档生成情况
- PRD 内容整合: ✅/❌
- 研究内容整合: ✅ (X 个研究笔记)
- 代码库分析整合: ✅ (X 个 CODEBUDDY.md)
- Wiki 格式遵循: ✅

### 内容覆盖
- 架构概览: ✅
- 核心模块: ✅ (X 个模块)
- API 文档: ✅ (X 个 API)
- 技术栈: ✅
- 参考资源: ✅

### 迭代情况
- 迭代 1: [status]
- 迭代 2: [status]
- 迭代 3: [status]

### 后续建议
- [Follow-up suggestion 1]
- [Follow-up suggestion 2]
- [Follow-up suggestion 3]
```

### 6.3 Save Wiki

**Save to `wiki.md` in project root:**

```bash
# Save generated wiki
# File: wiki.md
```

**Also save optimization suggestions and summary to:**
- `wiki-optimization-suggestions.md`
- `wiki-summary.md`

---

## Content Integration Guidelines

### PRD Integration

- Use PRD for: Product purpose, features, requirements, user stories
- Don't use PRD for: Technical implementation details (use codebase)
- Combine with: Research findings for technical depth

### Research Integration

- Use research for: External knowledge, best practices, comparisons, API docs
- Reference sources: Always cite research notes
- Combine with: Codebase analysis for implementation context

### Codebase Integration

- Use codebase for: Implementation details, file references, code examples
- Reference files: Always include file paths
- Combine with: Research for external context

### Gap Filling

- If PRD missing: Use codebase analysis to infer product purpose
- If research missing: Note as limitation, suggest `/init-research`
- If codebase unclear: Note as limitation, suggest deeper analysis

---

## Anti-Patterns

- **Ignoring template**: MUST follow wiki_template.md format exactly
- **Generic content**: Generate specific, technical content
- **Missing sources**: Always reference where content comes from
- **Assumptions**: Don't assume, note limitations
- **Incomplete sections**: All sections must be complete
- **Poor formatting**: Follow markdown best practices
- **No validation**: Always validate after each iteration
- **Early exit**: Must complete 3 validation cycles

---

## Output Promise

After 3 successful validation cycles:

```
<promise>WIKI_COMPLETE</promise>
```

This signals that:
- Wiki is generated following wiki_template.md format
- All content is integrated from PRD, research, and codebase
- All sections are complete
- Content has been validated 3 times
- Optimization suggestions and summary are generated
