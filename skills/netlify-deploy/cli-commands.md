# Netlify CLI Commands

## Authentication

```bash
npx netlify login
npx netlify status
npx netlify logout
```

## Site Linking

```bash
npx netlify link
npx netlify link --git-remote-url <url>
npx netlify init
npx netlify unlink
```

## Deployments

```bash
npx netlify deploy
npx netlify deploy --prod
npx netlify deploy --dir=dist
npx netlify deploy --message="release note"
npx netlify deploy:list
```

## Environment Variables

```bash
npx netlify env:list
npx netlify env:set KEY value
npx netlify env:get KEY
npx netlify env:import .env
```

## Build and Validation

```bash
npx netlify build
npx netlify build --dry
```

## Debugging

```bash
npx netlify --version
npx netlify status --verbose
npx netlify help deploy
```

## Dashboard Shortcuts

```bash
npx netlify open
npx netlify open:admin
npx netlify open:site
```
