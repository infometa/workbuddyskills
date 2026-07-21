# AST-Grep Tools

AST-Grep provides AST-aware (Abstract Syntax Tree) code search and replacement across 25+ programming languages. Unlike text-based search, AST-Grep understands code structure.

## Tools

### 1. ast_grep_search
Search for code patterns using AST awareness.

**Usage**: `ast_grep_search(pattern, lang, paths)`

**Parameters**:
- `pattern`: AST pattern to match (e.g., `function $NAME($$$) { $$$ }`)
- `lang`: Language (typescript, python, go, rust, java, etc.)
- `paths`: Optional file paths to search

**Returns**: List of matches with file, line, column information

---

### 2. ast_grep_replace
Replace code patterns while preserving structure.

**Usage**: `ast_grep_replace(pattern, rewrite, lang, paths, dryRun)`

**Parameters**:
- `pattern`: AST pattern to match
- `rewrite`: Replacement pattern
- `lang`: Language
- `paths`: Optional file paths
- `dryRun`: Preview changes without applying (default: false)

**Returns**: Preview or actual changes made

---

## Supported Languages (25+)

- C, C++, C#
- Go, Rust, Java, Kotlin
- JavaScript, TypeScript, JSX, TSX
- Python, Ruby, Lua
- PHP, HTML, CSS, Swift
- Bash, Elixir, Dart, Thrift
- And more...

## Pattern Syntax

### Meta-variables

- `$VAR` - Match single node (variable, expression, etc.)
- `$$$` - Match multiple nodes (function arguments, array elements)

### Examples

#### Find all function declarations
```
Pattern: function $NAME($$$) { $$$ }
Language: typescript
```

#### Find all class methods
```
Pattern: class $CLASS { $$$ $METHOD($$$) { $$$ } $$$ }
Language: typescript
```

#### Find specific API calls
```
Pattern: fetch($URL, $$$)
Language: javascript
```

## Usage Patterns

### Search for Structural Patterns

```typescript
// Find all async functions
ast_grep_search(
  pattern: "async function $NAME($$$) { $$$ }",
  lang: "typescript",
  paths: ["src/"]
)

// Find all class constructors
ast_grep_search(
  pattern: "constructor($$$) { $$$ }",
  lang: "typescript"
)

// Find all try-catch blocks
ast_grep_search(
  pattern: "try { $$$ } catch ($ERR) { $$$ }",
  lang: "javascript"
)
```

### Safe Refactoring Workflow

```typescript
// 1. Search for pattern to understand scope
ast_grep_search(
  pattern: "oldFunction($$$)",
  lang: "typescript"
)

// 2. Preview replacement (DRY RUN)
ast_grep_replace(
  pattern: "oldFunction($$$)",
  rewrite: "newFunction($$$)",
  lang: "typescript",
  dryRun: true  // ALWAYS preview first
)

// 3. Review preview output carefully

// 4. Execute replacement
ast_grep_replace(
  pattern: "oldFunction($$$)",
  rewrite: "newFunction($$$)",
  lang: "typescript",
  dryRun: false
)

// 5. Verify with lsp_diagnostics
```

### Pattern Transformation Examples

#### Rename function calls
```typescript
Pattern: oldName($ARGS)
Rewrite: newName($ARGS)
```

#### Update API usage
```typescript
Pattern: api.old($DATA)
Rewrite: api.new({ data: $DATA })
```

#### Modernize syntax
```typescript
Pattern: var $VAR = $VALUE
Rewrite: const $VAR = $VALUE
```

## Advantages Over Text-Based Search

| Feature | Text Search | AST-Grep |
|---------|-------------|----------|
| Structure awareness | No | Yes |
| Ignores comments | No | Yes |
| Handles formatting | No | Yes |
| Type safety | No | Partial |
| Cross-language | Limited | Yes (25+ langs) |

## Best Practices

1. **Always preview first**: Use `dryRun=true` before actual replacement
2. **Start broad, refine narrow**: Search broadly, then narrow pattern
3. **Verify after changes**: Run tests and diagnostics
4. **Understand the pattern**: AST patterns must be valid AST nodes, not fragments
5. **Test on subset first**: Try on a few files before full codebase

## Limitations

- Requires pattern to be valid AST node (not arbitrary text)
- Some language features may not be fully supported
- Performance scales with project size
- Not all syntactic variations captured by one pattern

## For CodeBuddy Users

AST-Grep is available as a standalone CLI tool:

```bash
# Install
npm install -g @ast-grep/cli

# or
cargo install ast-grep --locked

# or
brew install ast-grep
```

You can use it through bash commands in CodeBuddy:

```bash
# Search
sg run -p 'pattern' --lang typescript

# Replace (dry run)
sg run -p 'old' -r 'new' --lang typescript

# Apply changes
sg run -p 'old' -r 'new' --lang typescript --update-all
```

However, the oh-my-codebuddy integration provides:
- Automatic timeout handling
- Better error messages
- Seamless integration with other tools
- Parallel execution support

## See Also

- [LSP_TOOLS.md](LSP_TOOLS.md) - Language Server Protocol tools
- [SESSION_MANAGER.md](SESSION_MANAGER.md) - Session management tools
- [Official AST-Grep Documentation](https://ast-grep.github.io/)


