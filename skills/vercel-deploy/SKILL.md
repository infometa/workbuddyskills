---
name: vercel-deploy
description: "Deploy and manage Vercel projects from the terminal. Use for Vercel deployments, preview or production releases, environment variables, deployment status, logs, and project operations."
description_zh: "部署和管理 Vercel 项目、环境变量与日志"
description_en: "Deploy and manage Vercel projects, environments, status and logs"
version: 1.0.0
homepage: https://api.skillhub.cn/nightfullstar/vercel-deploy
allowed-tools: Bash,Read
---
# Vercel Deployment & Management

Deploy and manage Vercel projects. No "AI will build your app" nonsense - just practical Vercel operations.

## Configuration

### Vercel Setup

**Get your token:**
1. Go to https://vercel.com/account/tokens
2. Create token (name it "OpenClaw")
3. Set in environment:

```bash
export VERCEL_TOKEN="your-token-here"
```

Or store in `.env`:
```
VERCEL_TOKEN=your-token-here
```

## Vercel Operations

### Deploy Project

```bash
# Deploy to preview
scripts/vercel_deploy.sh --project bountylock --preview

# Deploy to production
scripts/vercel_deploy.sh --project bountylock --production
```

### Manage Environment Variables

```bash
# List env vars
scripts/vercel_env.sh --project bountylock --list

# Set env var
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_RPC_URL \
  --value "https://sepolia.base.org" \
  --env production

# Delete env var
scripts/vercel_env.sh --project bountylock --delete \
  --key OLD_VAR \
  --env production
```

### Check Deployment Status

```bash
# Get latest deployment
scripts/vercel_status.sh --project bountylock

# Get specific deployment
scripts/vercel_status.sh --deployment dpl_abc123
```

### View Logs

```bash
# Get deployment logs
scripts/vercel_logs.sh --deployment dpl_abc123

# Get runtime logs
scripts/vercel_logs.sh --project bountylock --function api/bounties
```

## Common Workflows

### Initial Testnet Deployment

1. **Set environment variables:**
```bash
# Contract addresses (after deploying to Sepolia)
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0x..." \
  --env production

# RPC URL
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_RPC_URL \
  --value "https://sepolia.base.org" \
  --env production

# Chain ID
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CHAIN_ID \
  --value "84532" \
  --env production
```

2. **Deploy:**
```bash
scripts/vercel_deploy.sh --project bountylock --production
```

3. **Check status:**
```bash
scripts/vercel_status.sh --project bountylock
```

### Update Environment Variables

```bash
# Update contract address after redeployment
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0xNEW_ADDRESS" \
  --env production

# Trigger new deployment to use updated vars
scripts/vercel_deploy.sh --project bountylock --production
```

### Debug Deployment Issues

```bash
# Get latest deployment info
scripts/vercel_status.sh --project bountylock

# Get build logs
scripts/vercel_logs.sh --deployment dpl_abc123

# Check environment variables
scripts/vercel_env.sh --project bountylock --list
```

## Security Best Practices

1. **Token Scope:** Use project-scoped tokens when possible
2. **Rotation:** Rotate tokens periodically
3. **Audit:** Review deployment logs regularly
4. **Secrets:** Never commit tokens to git

## Troubleshooting

**"Authentication failed"**
- Check token is set correctly
- Verify token hasn't expired

**"Project not found"**
- Verify project name matches Vercel project
- Check account has access to project

**"Deployment failed"**
- Check build logs: `scripts/vercel_logs.sh --deployment dpl_xxx`
- Verify environment variables are set correctly
- Check for build errors in code

## Reference Files

- **Vercel API Reference:** See [vercel-api.md](references/vercel-api.md) for complete API documentation
- **Deployment Patterns:** See [deployment-patterns.md](references/deployment-patterns.md) for common deployment workflows
