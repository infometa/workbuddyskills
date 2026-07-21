# netlify.toml Quick Reference

## Minimal Config

```toml
[build]
  command = "npm run build"
  publish = "dist"
```

## SPA Fallback

```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## Context Overrides

```toml
[context.production]
  command = "npm run build"

[context.deploy-preview]
  command = "npm run build:preview"
```

## Environment Variables

```toml
[build.environment]
  NODE_VERSION = "20"

[context.production.environment]
  NODE_ENV = "production"
```

## Monorepo Base Directory

```toml
[build]
  base = "apps/web"
  command = "npm run build"
  publish = "dist"
```

## Common Framework Publish Directories

- Vite / React: `dist`
- Vue: `dist`
- Astro: `dist`
- SvelteKit static adapter: `build`
- Static HTML: project root or configured directory

## Validation Command

```bash
npx netlify build --dry
```

Use this before first production deploy to catch config issues early.
