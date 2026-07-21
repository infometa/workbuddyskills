---
name: setup-pre-commit
description: Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.
description_zh: "为 JS/TS 项目配置 Husky pre-commit hooks（lint-staged + Prettier + 类型检查 + 测试）"
description_en: "Set up Husky pre-commit hooks with lint-staged, Prettier, type checking, and tests"
version: 1.0.0
homepage: https://github.com/mattpocock/skills
allowed-tools: Read,Write,Bash
---

# Setup Pre-Commit Hooks

**Applies to**: JavaScript / TypeScript projects with `package.json`. Not applicable to other languages.

**Prerequisites**: The project must already have `package.json` (run `npm init -y` first if missing) and be inside a git repository (`git init` if not).

## What This Sets Up

- **Husky** pre-commit hook
- **lint-staged** running Prettier on all staged files
- **Prettier** config (if missing)
- **typecheck** and **test** scripts in the pre-commit hook

## Steps

### 1. Detect package manager

Read the project root for lockfiles in this priority order:

| Lockfile | Package manager | Install cmd prefix | Script runner | dlx runner |
|----------|----------------|-------------------|---------------|------------|
| `pnpm-lock.yaml` | pnpm | `pnpm add -D` | `pnpm run` | `pnpm dlx` |
| `yarn.lock` | yarn | `yarn add --dev` | `yarn` | `yarn dlx` |
| `bun.lockb` | bun | `bun add -d` | `bun run` | `bunx` |
| `package-lock.json` | npm | `npm install --save-dev` | `npm run` | `npx` |

If multiple lockfiles exist, use the first match in the order above. If none found, default to npm and inform the user.

### 2. Install dependencies

Run with the detected package manager's install command:

```
<install-cmd-prefix> husky lint-staged prettier
```

Example for pnpm: `pnpm add -D husky lint-staged prettier`

### 3. Initialize Husky

```bash
npx husky init
```

This creates `.husky/` and adds `"prepare": "husky"` to `package.json`. It also auto-generates `.husky/pre-commit` with a default content — **Step 4 will overwrite it**.

### 4. Create `.husky/pre-commit`

Overwrite `.husky/pre-commit` with:

```
<dlx-runner> lint-staged
<script-runner> typecheck
<script-runner> test
```

Where `<dlx-runner>` and `<script-runner>` come from the table in Step 1. Example for pnpm:

```
pnpm dlx lint-staged
pnpm run typecheck
pnpm run test
```

**Adapt**: Check `package.json` scripts. If no `typecheck` script exists, omit that line. If no `test` script exists, omit that line. Tell the user which lines were omitted.

Then make the file executable:

```bash
chmod +x .husky/pre-commit
```

### 5. Create `.lintstagedrc`

If `.lintstagedrc` (or `.lintstagedrc.json`, `.lintstagedrc.js`) does not already exist, create `.lintstagedrc`:

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

If it already exists, leave it unchanged and tell the user.

### 6. Create `.prettierrc` (if missing)

Check for any existing Prettier config: `.prettierrc`, `.prettierrc.json`, `.prettierrc.js`, `.prettierrc.cjs`, `prettier.config.js`, `prettier.config.cjs`, or a `"prettier"` key in `package.json`. If any exists, skip this step.

If none exists, create `.prettierrc`:

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

### 7. Verify

- [ ] `.husky/pre-commit` exists and is executable (`ls -la .husky/pre-commit`)
- [ ] `.lintstagedrc` exists
- [ ] `"prepare": "husky"` is in `package.json` scripts
- [ ] Prettier config exists (any of the forms listed in Step 6)
- [ ] Run `<dlx-runner> lint-staged` to confirm it executes without errors

If the lint-staged run fails, check: (a) is Prettier installed? (b) does `.lintstagedrc` point to the right formatter?

### 8. Commit

Stage the created/modified files and commit:

```bash
git add .husky/pre-commit .lintstagedrc package.json
```

Add `.prettierrc` only if it was created in Step 6:

```bash
git add .prettierrc   # only if Step 6 created it
```

Then commit:

```bash
git commit -m "Add pre-commit hooks (husky + lint-staged + prettier)"
```

This commit will run through the new pre-commit hooks — a good smoke test that everything works.

## Notes

- Husky v9+ doesn't need shebangs in hook files — the file created in Step 4 has no `#!/bin/sh`
- `prettier --ignore-unknown` skips files Prettier can't parse (images, binaries, etc.)
- The pre-commit runs lint-staged first (fast, staged-only), then full typecheck and tests
- If the project already has Husky v4–v8 installed, remove it first (`npm uninstall husky` and delete the old `.husky/` config) before running this skill

## Tools

- **Read**: Detect package manager by reading lockfiles; check `package.json` scripts; check for existing Prettier/lint-staged config
- **Write**: Create `.husky/pre-commit`, `.lintstagedrc`, `.prettierrc` (if missing), update `package.json`
- **Bash**: Run install commands, `npx husky init`, `chmod +x`, lint-staged verification, `git add`, and the final commit
