---
name: netlify-deploy
description: "Deploy and manage Netlify sites with npx netlify. Use for first deploys, preview deploys, production releases, site linking, authentication checks, and netlify.toml fixes."
description_zh: "使用 Netlify CLI 部署和管理静态网站"
description_en: "Deploy and manage Netlify sites with preview and production releases"
version: 1.0.0
homepage: https://api.skillhub.cn/ivangdavila/netlify-deploy
allowed-tools: Bash,Read
metadata:
  clawdbot:
    emoji: NET
    requires:
      bins:
        - npx
        - git
      config:
        - ~/netlify-deploy/
    os:
      - linux
      - darwin
      - win32
---
## Setup

On first use, read `setup.md` for integration and environment checks.

## When to Use

User needs to deploy, host, publish, or relink a web project on Netlify from the terminal. Use this skill for first deploys, preview deploys, production pushes, monorepo paths, and netlify.toml fixes.

## Architecture

Memory lives in `~/netlify-deploy/`.
Use this local memory only for operational defaults so future deploy requests can start with the right safety assumptions.

```text
~/netlify-deploy/
`- memory.md    # Preferred deploy mode, default project path, and common build settings
```

See `memory-template.md` for setup.

## Quick Reference

Load only the file needed for the current task to keep command decisions fast and avoid irrelevant context.

| Topic | File |
|-------|------|
| Setup and integration flow | `setup.md` |
| Memory template | `memory-template.md` |
| CLI command map | `cli-commands.md` |
| Deployment scenarios | `deployment-patterns.md` |
| Configuration examples | `netlify-toml.md` |

## Core Rules

### 1. Verify Auth and Site Link Before Any Deploy
```bash
npx netlify status
```
If not authenticated, run `npx netlify login` and re-check status. If authenticated but not linked, resolve linking before deploy.

### 2. Use Link-First, Init-Second
```bash
git remote get-url origin
npx netlify link --git-remote-url <remote-url>
```
If the repository is not linked or no matching site exists, fall back to `npx netlify init`.

### 3. Default to Preview Deploys Unless User Asks for Production
```bash
npx netlify deploy
```
Use `npx netlify deploy --prod` only when the user explicitly requests production or confirms readiness.
Never force production deploys as a shortcut when validation is still pending.

### 4. Confirm Build and Publish Paths Before First Production Deploy
```bash
npm run build
npx netlify deploy --dir=dist
```
Use framework defaults only as a starting point. Validate the actual output folder in the current project.

### 5. Make Monorepo Context Explicit
For monorepos, deploy from the correct subdirectory or set `build.base` in `netlify.toml` before linking/deploying.

### 6. Report Actionable Results
After each deploy, return deploy URL, environment (preview or production), and one concrete next step.

## Common Traps

These traps are prioritized by how often they cause failed or risky deploys in terminal-first workflows.

| Trap | Consequence | Fix |
|------|-------------|-----|
| Running deploy before login check | Command fails with auth errors | Always run `npx netlify status` first |
| Running `--prod` by default | Unreviewed changes go live | Start with preview deploy unless user confirms production |
| Wrong publish directory | Site deploys blank or outdated build | Run local build and verify output folder |
| Linking from wrong monorepo folder | Deploys wrong app | Confirm current path and base directory before link/deploy |
| Treating `netlify.toml` as optional on complex projects | Inconsistent builds between environments | Commit a minimal, explicit `netlify.toml` |

## External Endpoints

Only Netlify service endpoints and Netlify documentation endpoints are expected in normal usage of this skill.

| Endpoint | Data Sent | Purpose |
|----------|-----------|---------|
| https://api.netlify.com | Deploy metadata, site/project identifiers, build outputs via CLI | Authentication, linking, and deployments |
| https://app.netlify.com | Browser session data when login opens OAuth flow | Interactive authentication and dashboard access |
| https://docs.netlify.com | Documentation requests only | Reference for command and config behavior |

No other data is sent externally.

## Security & Privacy

**Data that leaves your machine:**
- Project deploy artifacts and metadata are sent to Netlify when running deploy commands.
- Auth/session data is exchanged with Netlify during `npx netlify login`.

**Data that stays local:**
- Local source files and build scripts remain in your project unless you deploy.
- Skill preferences stay in `~/netlify-deploy/memory.md`.

**This skill does NOT:**
- Store secrets inside skill files.
- Run undeclared external services beyond Netlify endpoints.
- Modify unrelated repositories or directories.

## Trust

By using this skill, deployment data is sent to Netlify services.
Only install if you trust Netlify with your project artifacts and deployment metadata.

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `ci-cd` - delivery pipeline design and release automation practices
- `git` - branch hygiene and release-safe commit workflow
- `deploy` - generic deployment planning across environments
- `devops` - infrastructure and operational guardrails

## Feedback

- If useful: `clawhub star netlify-deploy`
- Stay updated: `clawhub sync`
