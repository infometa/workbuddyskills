---
description: Fix all linting and formatting issues across the codebase
category: code-analysis-testing
allowed-tools: Bash, Edit, Read, Glob
---

Fix all linting, formatting, and static analysis issues in the entire codebase.

## Process:

1. **Detect Project Language(s)**:
   - Check file extensions and configuration files
   - Common indicators:
     - Python: .py files, requirements.txt, pyproject.toml
     - JavaScript/TypeScript: .js/.ts files, package.json
     - Go: .go files, go.mod
     - Rust: .rs files, Cargo.toml
     - Java: .java files, pom.xml
     - Ruby: .rb files, Gemfile

2. **Run Language-Specific Linters**:

   **Python:**
   - Formatting: `black .` or `autopep8`
   - Import sorting: `isort .`
   - Linting: `flake8` or `pylint`
   - Type checking: `mypy`
   
   **JavaScript/TypeScript:**
   - Linting: `eslint . --fix`
   - Formatting: `prettier --write .`
   - Type checking: `tsc --noEmit`
   
   **Go:**
   - Formatting: `go fmt ./...`
   - Linting: `golangci-lint run --fix`
   
   **Rust:**
   - Formatting: `cargo fmt`
   - Linting: `cargo clippy --fix`
   
   **Java:**
   - Formatting: `google-java-format` or `spotless`
   - Linting: `checkstyle` or `spotbugs`
   
   **Ruby:**
   - Linting/Formatting: `rubocop -a`

3. **Check for Project Scripts**:
   - Look for lint/format scripts in package.json, Makefile, etc.
   - Common script names: `lint`, `format`, `fix`, `clean`

4. **Fix Issues**:
   - Apply auto-fixes where available
   - Manually fix issues that can't be auto-fixed
   - Re-run linters to verify all issues are resolved

5. **Verify Clean State**:
   - Run all linters again without fix flags
   - Ensure no errors or warnings remain

Fix all issues found until the codebase passes all linting and formatting checks.