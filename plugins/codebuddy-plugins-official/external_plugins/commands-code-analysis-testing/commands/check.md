---
description: Run project checks and fix any errors without committing
category: code-analysis-testing
allowed-tools: Bash, Edit, Read
---

Run project validation checks and resolve any errors found.

## Process:

1. **Detect Package Manager** (for JavaScript/TypeScript projects):
   - npm: Look for package-lock.json
   - pnpm: Look for pnpm-lock.yaml
   - yarn: Look for yarn.lock
   - bun: Look for bun.lockb

2. **Check Available Scripts**:
   - Read package.json to find check/validation scripts
   - Common script names: `check`, `validate`, `verify`, `test`, `lint`

3. **Run Appropriate Check Command**:
   - JavaScript/TypeScript:
     - npm: `npm run check` or `npm test`
     - pnpm: `pnpm check` or `pnpm test`
     - yarn: `yarn check` or `yarn test`
     - bun: `bun check` or `bun test`
   
   - Other languages:
     - Python: `pytest`, `flake8`, `mypy`, or `make check`
     - Go: `go test ./...` or `golangci-lint run`
     - Rust: `cargo check` or `cargo test`
     - Ruby: `rubocop` or `rake test`

4. **Fix Any Errors**:
   - Analyze error output
   - Fix code issues, syntax errors, or test failures
   - Re-run checks after fixing

5. **Important Constraints**:
   - DO NOT commit any code
   - DO NOT change version numbers
   - Only fix errors to make checks pass

If no check script exists, run the most appropriate validation for the project type.