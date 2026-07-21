---
description: Run CI checks and fix any errors until all tests pass
category: ci-deployment
allowed-tools: Bash, Edit, Read, Glob
---

Run CI checks for the project and fix any errors until all tests pass.

## Process:

1. **Detect CI System**:
   - Check for CI configuration files:
     - `.github/workflows/*.yml` (GitHub Actions)
     - `.gitlab-ci.yml` (GitLab CI)
     - `.circleci/config.yml` (CircleCI)
     - `Jenkinsfile` (Jenkins)
     - `.travis.yml` (Travis CI)
     - `bitbucket-pipelines.yml` (Bitbucket)

2. **Detect Build System**:
   - JavaScript/TypeScript: package.json scripts
   - Python: Makefile, tox.ini, setup.py, pyproject.toml
   - Go: Makefile, go.mod
   - Rust: Cargo.toml
   - Java: pom.xml, build.gradle
   - Other: Look for common CI scripts

3. **Run CI Commands**:
   - Check for CI scripts: `ci`, `test`, `check`, `validate`, `verify`
   - Common script locations:
     - `./scripts/ci.sh`, `./ci.sh`, `./run-tests.sh`
     - Package manager scripts (npm/yarn/pnpm run test)
     - Make targets (make test, make ci)
   - Activate virtual environments if needed (Python, Ruby, etc.)

4. **Fix Errors**:
   - Analyze error output
   - Fix code issues, test failures, or configuration problems
   - Re-run CI checks after each fix

5. **Common CI Tasks**:
   - Linting/formatting
   - Type checking
   - Unit tests
   - Integration tests
   - Build verification
   - Documentation generation

## Examples:
- JavaScript: `npm test` or `npm run ci`
- Python: `make test` or `pytest` or `tox`
- Go: `go test ./...` or `make test`
- Rust: `cargo test`
- Generic: `./ci.sh` or `make ci`

Continue fixing issues and re-running until all CI checks pass.