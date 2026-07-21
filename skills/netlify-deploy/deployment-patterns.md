# Netlify Deployment Patterns

## Decision Flow

```text
Authenticated?
|- No -> npx netlify login
`- Yes -> Linked?
   |- No -> Try link by git remote
   |  |- Success -> preview deploy
   |  `- Fail -> npx netlify init
   `- Yes -> deploy mode?
      |- Preview -> npx netlify deploy
      `- Production -> npx netlify deploy --prod
```

## First-Time Deploy

1. `npx netlify status`
2. `npx netlify login` if needed
3. `npx netlify init`
4. Build locally (`npm run build` or project equivalent)
5. `npx netlify deploy` then optionally `--prod`

## Existing Site + Existing Repo

1. `git remote get-url origin`
2. `npx netlify link --git-remote-url <url>`
3. Run preview deploy and verify URL

## Monorepo Pattern

- Deploy from target package directory, or
- Set in `netlify.toml`:

```toml
[build]
  base = "packages/web"
  command = "npm run build"
  publish = "dist"
```

## Production Promotion Pattern

1. Preview deploy
2. Validate URL and smoke checks
3. Promote with `npx netlify deploy --prod`
4. Share production URL with commit context

## Error Recovery

- Auth error -> `npx netlify login`
- Site not linked -> link or init flow
- Publish directory missing -> rebuild and verify output folder
- Build failure -> run local build first, fix, redeploy
