---
description: Verify repository is in working state by running CI checks and fixing issues
category: version-control-git
allowed-tools: Bash, Read, Edit
---

## Summary

Verify the repository is in a working state by running appropriate CI checks and fixing any issues found.

## Process

1. **Detect Package Manager**:
   - Check for package manager files: package-lock.json (npm), pnpm-lock.yaml (pnpm), yarn.lock (yarn), bun.lockb (bun)
   - Check for other build systems: Makefile, Cargo.toml, go.mod, requirements.txt, etc.

2. **Update Dependencies**:
   - npm: `npm install`
   - pnpm: `pnpm install`
   - yarn: `yarn install`
   - bun: `bun install`
   - Other: Run appropriate dependency installation

3. **Run Linting**:
   - Check package.json scripts for lint command
   - Common patterns: `lint`, `eslint`, `check`, `format`
   - Fix any linting issues found

4. **Run Type Checking** (if applicable):
   - TypeScript: `tsc` or check for `typecheck` script
   - Other typed languages: run appropriate type checker

5. **Run Build**:
   - Check for build scripts in package.json or build configuration
   - Common patterns: `build`, `compile`, `dist`
   - Fix any build errors

6. **Run Tests**:
   - Check for test scripts: `test`, `test:unit`, `test:coverage`
   - Source .env file if it exists before running tests
   - Fix any failing tests

7. **Additional Checks**:
   - Check if package.json needs sorting (if sort-package-json is available)
   - Run any other project-specific checks found in CI configuration

8. **Stage Changes**:
   - Review changes with `git status`
   - Add fixed files with `git add`
   - Exclude any git submodules or vendor directories

## Important Notes:

- Do NOT continue to the next step until the current command succeeds
- Fix any issues found before proceeding
- If a command doesn't exist, check for alternatives or skip if not applicable
- Print a summary with checkmarks (✅) for passed steps at the end

## Protocol when something breaks

Take the following steps if CI breaks

### 1. Explain why it's broke

- Whenever a test is broken first give think very hard and a complete explanation of what broke. Cite source code and logs that support your thesis.
- If you don't have source code or logs to support your thesis, think hard and look in codebase for proof. 
- Add console logs if it will help you confirm your thesis or find out why it's broke
- If you don