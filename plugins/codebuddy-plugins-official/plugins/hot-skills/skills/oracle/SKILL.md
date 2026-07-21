---
name: oracle
description: Use the @steipete/oracle CLI to bundle a prompt plus the right files and get a second-model review (API or browser) for debugging, refactors, design checks, or cross-validation.
---

# Oracle (CLI)

Oracle bundles your prompt + selected files into one "one-shot" request so another model can answer with real repo context (API or browser automation). Treat outputs as advisory: verify against the codebase + tests.

## Main use case (browser)

Default workflow: `--engine browser` with GPT in ChatGPT.

## Golden path

1. Pick a tight file set (fewest files that still contain the truth).
2. Preview what you're about to send (`--dry-run` + `--files-report`).
3. Run in browser mode for the usual ChatGPT workflow; use API only when you explicitly want it.
4. If the run detaches/timeouts: reattach to the stored session (don't re-run).

## Commands (preferred)

- Show help: `npx -y @steipete/oracle --help`
- Preview (no tokens): `npx -y @steipete/oracle --dry-run summary -p "<task>" --file "src/**" --file "!**/*.test.*"`
- Token/cost sanity: `npx -y @steipete/oracle --dry-run summary --files-report -p "<task>" --file "src/**"`
- Browser run: `npx -y @steipete/oracle --engine browser -p "<task>" --file "src/**"`
- Manual paste fallback: `npx -y @steipete/oracle --render --copy -p "<task>" --file "src/**"`

## Attaching files (`--file`)

- Include: `--file "src/**"`, `--file src/index.ts`
- Exclude: `--file "!src/**/*.test.ts"`
- Default-ignored dirs: `node_modules`, `dist`, `coverage`, `.git`, etc.
- Hard cap: files > 1 MB are rejected.

## Budget + observability

- Target: keep total input under ~196k tokens.
- Use `--files-report` to spot token hogs before spending.

## Sessions

- Stored under `~/.oracle/sessions`.
- List: `oracle status --hours 72`
- Attach: `oracle session <id> --render`
- Use `--slug "<3-5 words>"` for readable session IDs.

## Safety

- Don't attach secrets by default.
- Prefer "just enough context": fewer files + better prompt beats whole-repo dumps.
