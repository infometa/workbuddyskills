# Vercel API Reference

Quick reference for Vercel CLI operations used by this skill.

## Authentication

All commands use `--token` flag with `$VERCEL_TOKEN` environment variable.

## Project Operations

### List Projects
```bash
vercel ls --token $VERCEL_TOKEN
```

### Get Project Info
```bash
vercel inspect <deployment-id> --token $VERCEL_TOKEN
```

## Deployment

### Deploy (Preview)
```bash
vercel --token $VERCEL_TOKEN
```

### Deploy (Production)
```bash
vercel --prod --token $VERCEL_TOKEN
```

### Deploy from CI/CD
```bash
vercel --token $VERCEL_TOKEN --yes
```

## Environment Variables

### List
```bash
vercel env ls <project-name> --token $VERCEL_TOKEN
```

### Add
```bash
echo "value" | vercel env add KEY_NAME production --token $VERCEL_TOKEN <project-name>
```

Available environments: `production`, `preview`, `development`

### Remove
```bash
vercel env rm KEY_NAME production --token $VERCEL_TOKEN <project-name> --yes
```

## Logs

### Deployment Logs
```bash
vercel logs <deployment-url> --token $VERCEL_TOKEN
```

### Function Logs
```bash
vercel logs <deployment-url> --token $VERCEL_TOKEN --follow
```

## Domains

### List Domains
```bash
vercel domains ls --token $VERCEL_TOKEN
```

### Add Domain
```bash
vercel domains add example.com --token $VERCEL_TOKEN
```

## Common Patterns

### Complete Deployment Workflow
```bash
# 1. Set environment variables
echo "$VALUE" | vercel env add KEY production --token $VERCEL_TOKEN project-name

# 2. Deploy
vercel --prod --token $VERCEL_TOKEN

# 3. Check status
vercel ls project-name --token $VERCEL_TOKEN

# 4. Get logs if needed
vercel logs <deployment-url> --token $VERCEL_TOKEN
```

### Update Env Vars and Redeploy
```bash
# Update var
echo "new-value" | vercel env add KEY production --token $VERCEL_TOKEN project-name

# Trigger redeploy (Vercel auto-redeploys on env change)
# Or manually: vercel --prod --token $VERCEL_TOKEN
```

## Error Handling

**Authentication Error:**
- Check `VERCEL_TOKEN` is set
- Verify token hasn't expired
- Regenerate token if needed

**Project Not Found:**
- Verify project name spelling
- Check account access
- Use `vercel ls` to list available projects

**Build Failed:**
- Check `vercel logs <deployment-url>`
- Verify environment variables
- Check build configuration in `vercel.json`
