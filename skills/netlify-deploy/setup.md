# Setup - Netlify Deploy

Read this when the user first asks to deploy with Netlify and project context is still unknown.

## Integration First

In the first exchange, confirm activation behavior:
- Should this skill activate whenever they mention Netlify deploys?
- Should production deploys always require explicit confirmation?
- Is there a default repository or folder to assume?

Store integration preferences in main memory.

## Environment Discovery

Before proposing commands, establish:
- Package manager in use (npm, pnpm, yarn)
- Build command and publish directory
- Whether the project is a monorepo or single app
- Whether the site is already linked in Netlify

## Safe First Execution

For initial command flow:
1. `npx netlify status`
2. `git remote get-url origin` (if repo exists)
3. `npx netlify link --git-remote-url <remote>` or `npx netlify init`
4. `npx netlify deploy` (preview first)

Use production deploy only after explicit user confirmation.

## What to Persist

In `~/netlify-deploy/memory.md`, keep:
- Preferred default deploy mode (preview first or prod-first by request)
- Frequent project paths and common publish directories
- Team-specific release constraints (for example: required preview review)

## Completion Signal

Setup is effectively complete once auth works, site linking is reliable, and one preview deploy succeeds with a valid URL.
