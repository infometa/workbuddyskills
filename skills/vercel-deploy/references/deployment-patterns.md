# Deployment Patterns

Common deployment workflows for web3 projects like BountyLock.

## Initial Sepolia Testnet Deployment

### Prerequisites
- Contracts deployed to Sepolia
- Contract addresses ready
- RPC URL configured

### Steps

**1. Set Environment Variables**
```bash
# Contract address
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0x..." \
  --env production

# RPC URL (Base Sepolia)
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_RPC_URL \
  --value "https://sepolia.base.org" \
  --env production

# Chain ID (Base Sepolia = 84532)
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CHAIN_ID \
  --value "84532" \
  --env production

# IPFS Gateway
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_IPFS_GATEWAY \
  --value "https://ipfs.io/ipfs/" \
  --env production
```

**2. Deploy**
```bash
cd ~/GIT/bountylock/frontend
scripts/vercel_deploy.sh --project bountylock --production
```

**3. Verify**
```bash
# Check deployment status
scripts/vercel_status.sh --project bountylock

# Test the site
# Visit the deployment URL and verify wallet connection + contract interaction
```

## Contract Redeployment Update

When contracts are redeployed (new addresses):

```bash
# Update contract address
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0xNEW_ADDRESS" \
  --env production

# Redeploy (picks up new env var)
cd ~/GIT/bountylock/frontend
scripts/vercel_deploy.sh --project bountylock --production
```

## Preview Deployment for Testing

```bash
# Deploy to preview URL
cd ~/GIT/bountylock/frontend
scripts/vercel_deploy.sh --project bountylock --preview

# Get preview URL
scripts/vercel_status.sh --project bountylock
```

## Mainnet Deployment

Same as testnet but with mainnet values:

```bash
# Base Mainnet
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_RPC_URL \
  --value "https://mainnet.base.org" \
  --env production

scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CHAIN_ID \
  --value "8453" \
  --env production

scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0xMAINNET_ADDRESS" \
  --env production
```

## Multi-Environment Setup

**Preview (Sepolia):**
```bash
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0xSEPOLIA_ADDRESS" \
  --env preview
```

**Production (Mainnet):**
```bash
scripts/vercel_env.sh --project bountylock --set \
  --key NEXT_PUBLIC_CONTRACT_ADDRESS \
  --value "0xMAINNET_ADDRESS" \
  --env production
```

## Troubleshooting Deployments

**Build fails with "Module not found":**
1. Check `package.json` dependencies
2. Verify `npm install` works locally
3. Check build logs: `scripts/vercel_logs.sh --deployment dpl_xxx`

**Site loads but wallet won't connect:**
1. Verify `NEXT_PUBLIC_RPC_URL` is set
2. Check `NEXT_PUBLIC_CHAIN_ID` matches network
3. Check browser console for errors

**Contract interactions fail:**
1. Verify `NEXT_PUBLIC_CONTRACT_ADDRESS` is correct
2. Check contract is deployed at that address
3. Verify wallet is on correct network
4. Check contract ABI matches deployment

**Environment variables not updating:**
1. Redeploy after changing env vars
2. Check env var is set for correct environment (production/preview)
3. Hard refresh browser (Ctrl+Shift+R) to clear cache
