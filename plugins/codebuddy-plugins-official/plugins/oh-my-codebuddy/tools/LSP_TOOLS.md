# LSP Tools

oh-my-codebuddy provides 11 Language Server Protocol (LSP) tools that give AI agents full IDE capabilities.

## Tool List

### 1. lsp_hover
Get type information, documentation, and signatures at a specific position.

**Usage**: `lsp_hover(filePath, line, character)`

**Returns**: Type info, documentation strings, function signatures

**Use when**: Need to understand what a symbol is or what type it has

---

### 2. lsp_goto_definition
Jump to where a symbol is defined.

**Usage**: `lsp_goto_definition(filePath, line, character)`

**Returns**: File path and position of definition

**Use when**: Need to find where a function/class/variable is defined

---

### 3. lsp_find_references
Find all usages of a symbol across the workspace.

**Usage**: `lsp_find_references(filePath, line, character, includeDeclaration)`

**Returns**: List of all files and positions where symbol is referenced

**Use when**: Need to understand impact of changing a symbol, or find all usages

---

### 4. lsp_document_symbols
Get hierarchical outline of symbols in a file.

**Usage**: `lsp_document_symbols(filePath)`

**Returns**: Nested structure of classes, functions, variables in file

**Use when**: Need to understand file structure or find specific symbols in a file

---

### 5. lsp_workspace_symbols
Search for symbols by name across entire project.

**Usage**: `lsp_workspace_symbols(filePath, query)`

**Returns**: List of symbols matching query with their locations

**Use when**: Looking for a symbol but don't know which file it's in

---

### 6. lsp_diagnostics
Get errors, warnings, and hints for a file.

**Usage**: `lsp_diagnostics(filePath)`

**Returns**: List of diagnostic messages (errors, warnings, info)

**Use when**: Need to check for errors before/after making changes

---

### 7. lsp_servers
List available LSP servers and their status.

**Usage**: `lsp_servers()`

**Returns**: List of configured LSP servers and their state

**Use when**: Debugging LSP issues or checking what languages are supported

---

### 8. lsp_prepare_rename
Validate that a rename operation is possible.

**Usage**: `lsp_prepare_rename(filePath, line, character)`

**Returns**: Whether rename is possible and suggested range

**Use when**: Before performing a rename to ensure it's safe

---

### 9. lsp_rename
Rename a symbol across the entire workspace.

**Usage**: `lsp_rename(filePath, line, character, newName)`

**Returns**: List of all file changes needed for the rename

**Use when**: Need to safely rename a function/class/variable everywhere

---

### 10. lsp_code_actions
Get available quick fixes and refactorings at a position.

**Usage**: `lsp_code_actions(filePath, line, character)`

**Returns**: List of code actions (quick fixes, refactorings)

**Use when**: Looking for automated fixes or refactoring options

---

### 11. lsp_code_action_resolve
Apply a specific code action.

**Usage**: `lsp_code_action_resolve(filePath, action)`

**Returns**: The edit to apply

**Use when**: Executing a code action from lsp_code_actions

---

## Supported Languages

The LSP tools work with any language that has an LSP server configured:

- **TypeScript/JavaScript**: typescript-language-server
- **Python**: pylsp, pyright
- **Go**: gopls
- **Rust**: rust-analyzer
- **And many more**: Any LSP-compliant language server

## Configuration

LSP servers are configured in OpenCode's config file. Example:

```json
{
  "lsp": {
    "typescript-language-server": {
      "command": ["typescript-language-server", "--stdio"],
      "extensions": [".ts", ".tsx"],
      "priority": 10
    }
  }
}
```

## Usage Patterns

### Safe Refactoring Workflow

```typescript
// 1. Understand the symbol
lsp_hover(filePath, line, character)

// 2. Find all usages
lsp_find_references(filePath, line, character, true)

// 3. Validate rename is possible
lsp_prepare_rename(filePath, line, character)

// 4. Execute rename
lsp_rename(filePath, line, character, "newName")

// 5. Verify no new errors
lsp_diagnostics(filePath)
```

### Code Navigation Workflow

```typescript
// 1. Search for symbol by name
lsp_workspace_symbols(".", "functionName")

// 2. Go to definition
lsp_goto_definition(filePath, line, character)

// 3. Find all references
lsp_find_references(filePath, line, character)
```

### Error Detection Workflow

```typescript
// 1. Get file structure
lsp_document_symbols(filePath)

// 2. Check for errors
lsp_diagnostics(filePath)

// 3. Get available fixes
lsp_code_actions(filePath, errorLine, errorCharacter)

// 4. Apply fix
lsp_code_action_resolve(filePath, action)
```

## Benefits

1. **Precision**: Semantic understanding, not just text matching
2. **Safety**: Symbol-aware refactoring across entire codebase
3. **Speed**: Instant symbol lookup without grep
4. **Correctness**: Type-aware navigation and validation

## Limitations

- Requires LSP server installation for each language
- Performance depends on project size (indexing time)
- Some language servers have incomplete implementations
- Cannot replace all manual code review

## For CodeBuddy Users

These LSP tools are not directly available in CodeBuddy. Alternatives:

1. **Use oh-my-codebuddy with OpenCode** (recommended)
2. **Custom implementation**: Create CodeBuddy plugin that wraps LSP
3. **Manual equivalents**: Use grep, read, and manual code inspection
4. **IDE integration**: Leverage your IDE's LSP features and communicate findings to CodeBuddy

## See Also

- [AST_GREP.md](AST_GREP.md) - Structural code search and replacement
- [SESSION_MANAGER.md](SESSION_MANAGER.md) - Session history navigation


