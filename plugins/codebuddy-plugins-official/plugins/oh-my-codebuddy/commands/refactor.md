---
description: Intelligent refactoring command with LSP, AST-grep, architecture analysis, codemap, and TDD verification
argument-hint: "<refactoring-target> [--scope=<file|module|project>] [--strategy=<safe|aggressive>]"
---

# Intelligent Refactor Command

## Usage
```
/refactor <refactoring-target> [--scope=<file|module|project>] [--strategy=<safe|aggressive>]

Arguments:
  refactoring-target: What to refactor. Can be:
    - File path: src/auth/handler.ts
    - Symbol name: "AuthService class"
    - Pattern: "all functions using deprecated API"
    - Description: "extract validation logic into separate module"

Options:
  --scope: Refactoring scope (default: module)
    - file: Single file only
    - module: Module/directory scope
    - project: Entire codebase

  --strategy: Risk tolerance (default: safe)
    - safe: Conservative, maximum test coverage required
    - aggressive: Allow broader changes with adequate coverage
```

## What This Command Does

Performs intelligent, deterministic refactoring with full codebase awareness. Unlike blind search-and-replace, this command:

1. **Understands your intent** - Analyzes what you actually want to achieve
2. **Maps the codebase** - Builds a definitive codemap before touching anything
3. **Assesses risk** - Evaluates test coverage and determines verification strategy
4. **Plans meticulously** - Creates a detailed plan with Plan agent
5. **Executes precisely** - Step-by-step refactoring with LSP and AST-grep
6. **Verifies constantly** - Runs tests after each change to ensure zero regression

---

# EXECUTION PHASES

## Phase 0: Intent Validation

**BEFORE ANY ACTION, classify and validate the request.**

| Signal | Classification | Action |
|--------|----------------|--------|
| Specific file/symbol | Explicit | Proceed to codebase analysis |
| "Refactor X to Y" | Clear transformation | Proceed to codebase analysis |
| "Improve", "Clean up" | Open-ended | **MUST ask**: "What specific improvement?" |
| Ambiguous scope | Uncertain | **MUST ask**: "Which modules/files?" |
| Missing context | Incomplete | **MUST ask**: "What's the desired outcome?" |

If unclear, ask for clarification before proceeding.

---

## Phase 1: Codebase Analysis

Launch parallel explore agents to understand the target:

```
background_task(agent="explore", prompt="Find all occurrences and definitions of [TARGET]")
background_task(agent="explore", prompt="Find all code that imports, uses, or depends on [TARGET]")
background_task(agent="explore", prompt="Find similar code patterns to [TARGET]")
background_task(agent="explore", prompt="Find all test files related to [TARGET]")
background_task(agent="explore", prompt="Find architectural patterns around [TARGET]")
```

While agents run, use LSP tools:
- `lsp_hover` - Type information
- `lsp_goto_definition` - Find definitions
- `lsp_find_references` - Map all usages
- `lsp_document_symbols` - File structure
- `lsp_workspace_symbols` - Search symbols
- `lsp_diagnostics` - Baseline errors

---

## Phase 2: Build Codemap

Create dependency map showing:
- Core files (direct impact)
- Dependency graph (what imports/exports)
- Impact zones (risk levels)
- Established patterns
- Refactoring constraints

---

## Phase 3: Test Assessment

1. Detect test infrastructure
2. Analyze test coverage for target code
3. Determine verification strategy:
   - HIGH coverage (>80%): Proceed with existing tests
   - MEDIUM (50-80%): Add safety assertions
   - LOW (<50%): **Propose adding tests first**
   - NONE: **Block aggressive refactoring**

---

## Phase 4: Plan Generation

Invoke Plan agent with:
- Refactoring goal
- Codemap from Phase 2
- Test coverage from Phase 3
- Constraints

Plan agent will create:
- Atomic refactoring steps
- Verification points
- Rollback strategies
- Commit checkpoints

---

## Phase 5: Execute Refactoring

For EACH step in the plan:

### Pre-Step
1. Mark step todo as `in_progress`
2. Read current file state
3. Verify baseline diagnostics

### Execute
Use appropriate tool:
- **Symbol renames**: `lsp_prepare_rename` → `lsp_rename`
- **Pattern transformations**: `ast_grep_replace` (preview with dryRun=true first)
- **Structural changes**: `edit` tool

### Post-Step Verification
1. `lsp_diagnostics` - Must be clean
2. Run tests - Must pass
3. Type check - Must pass

If verification fails: **STOP, REVERT, FIX**

---

## Phase 6: Final Verification

1. Full test suite run
2. Complete type check
3. Lint check
4. Build verification (if applicable)
5. Final diagnostics on all changed files

Generate summary of what changed and verification results.

---

## CRITICAL RULES

### NEVER DO
- Skip diagnostics check after changes
- Proceed with failing tests
- Use `as any`, `@ts-ignore`, `@ts-expect-error`
- Delete tests to make them pass
- Commit broken code

### ALWAYS DO
- Understand before changing
- Preview before applying (ast_grep dryRun=true)
- Verify after every change
- Follow existing codebase patterns
- Keep todos updated in real-time
- Report issues immediately

### ABORT CONDITIONS
- Test coverage is zero for target code
- Changes would break public API
- 3 consecutive verification failures
- User-defined constraints violated

**Remember: Refactoring without tests is reckless. Refactoring without understanding is destructive. This command ensures you do neither.**


