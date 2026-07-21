#!/bin/bash
# Vercel deployment script

set -euo pipefail

# Check for required env vars
if [ -z "${VERCEL_TOKEN:-}" ]; then
    echo "Error: VERCEL_TOKEN not set"
    exit 1
fi

# Parse arguments
PROJECT=""
ENV="preview"
YES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --production)
            ENV="production"
            shift
            ;;
        --preview)
            ENV="preview"
            shift
            ;;
        --yes|-y)
            YES=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -z "$PROJECT" ]; then
    echo "Error: --project required"
    exit 1
fi

# Confirm production deployment
if [ "$ENV" = "production" ] && [ "$YES" = false ]; then
    read -p "Deploy to PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 0
    fi
fi

echo "🚀 Deploying $PROJECT to $ENV..."

# Build deployment command
CMD="npx vercel --token $VERCEL_TOKEN --yes"

if [ "$ENV" = "production" ]; then
    CMD="$CMD --prod"
fi

# Execute deployment
$CMD

echo "✅ Deployment complete!"
echo "Check status: scripts/vercel_status.sh --project $PROJECT"
