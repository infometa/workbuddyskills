# Vercel Deploy Skill

**Practical Vercel operations for existing projects. No "AI will build your app" magic - just deployments, environment variables, and logs.**

## What This Skill Does

✅ Deploy existing projects to Vercel (production/preview)  
✅ Manage environment variables  
✅ Check deployment status and logs  
✅ Troubleshoot deployment issues  

❌ No code generation  
❌ No "describe your app" builders  
❌ No magic deployments of non-existent projects  

## Quick Start

### 1. Get Your Vercel Token
- Go to: https://vercel.com/account/tokens
- Click "Create"
- Name it "OpenClaw"
- Copy the token

### 2. Set the Token
```bash
export VERCEL_TOKEN="vtk_xxx..."
```

To persist across sessions:
```bash
echo 'export VERCEL_TOKEN="vtk_xxx..."' >> ~/.bashrc
source ~/.bashrc
```

### 3. Deploy
Just tell your OpenClaw agent:
- **"Deploy my-project to Vercel production"**
- **"Deploy to preview"**
- **"Set NEXT_PUBLIC_API_URL to https://api.example.com on Vercel"**
- **"Check latest deployment status"**
- **"List environment variables for my-project"**

## Use Cases

### Web3 Projects
Deploy Next.js frontends for smart contract projects:
```
"Set these on Vercel:
- NEXT_PUBLIC_CONTRACT_ADDRESS: 0x...
- NEXT_PUBLIC_RPC_URL: https://sepolia.base.org
- NEXT_PUBLIC_CHAIN_ID: 84532

Then deploy to production"
```

### Environment Management
```
"List all environment variables"
"Update the API URL to staging environment"
"Delete the old DATABASE_URL variable"
```

### Status Checks
```
"Check deployment status"
"Show me the latest deployment logs"
"What's the current production URL?"
```

## How It Works

The skill provides three bash scripts:
- **vercel_deploy.sh** - Deploy to production/preview
- **vercel_env.sh** - Manage environment variables
- **vercel_status.sh** - Check deployment status/logs

Your agent reads the skill documentation and runs the appropriate script based on your request.

## Example Workflow

**1. Deploy contracts to testnet** (using Hardhat/Foundry)

**2. Set contract addresses in Vercel:**
```
"Set NEXT_PUBLIC_CONTRACT_ADDRESS to 0xABC... on Vercel for my-dapp"
```

**3. Deploy frontend:**
```
"Deploy my-dapp to Vercel production"
```

**4. Check it worked:**
```
"Show me the deployment URL"
```

## Requirements

- **Vercel account** (free tier works)
- **Vercel token** (from account settings)
- **Existing project** to deploy (in a git repository or local directory)

## Security

- Tokens are passed via environment variables (not stored)
- Production deployments ask for confirmation
- Destructive operations require approval
- Preview deployments run automatically

## Troubleshooting

**"VERCEL_TOKEN not set"**
```bash
echo $VERCEL_TOKEN  # Check if set
export VERCEL_TOKEN="vtk_xxx..."  # Set it
```

**"Authentication failed"**
- Token might be expired - regenerate it
- Check for extra spaces when copying

**"Project not found"**
- Verify project exists on Vercel dashboard
- Check spelling of project name

**"Build failed"**
- Check build logs for errors
- Verify dependencies in package.json
- Test build locally first: `npm run build`

## Philosophy

This skill treats you like a developer who knows what they're doing. It doesn't try to "understand your vision" or "generate your app" - it just handles the boring Vercel CLI operations so you can focus on building.

Perfect for:
- Web3 frontend deployments
- Next.js/React projects
- Environment variable management
- Quick preview deployments
- CI/CD automation via OpenClaw

Not for:
- "Build me an app" requests
- Learning to code from scratch
- Projects that don't exist yet

## Author

Created for practical infrastructure management. Tested with BountyLock (USDC escrow platform on Base L2).

## License

MIT - Use however you want.
