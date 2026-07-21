#!/bin/bash
# Check Vercel deployment status

set -euo pipefail

if [ -z "${VERCEL_TOKEN:-}" ]; then
    echo "Error: VERCEL_TOKEN not set"
    exit 1
fi

PROJECT=""
DEPLOYMENT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --deployment)
            DEPLOYMENT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ -n "$DEPLOYMENT" ]; then
    echo "📊 Deployment status for $DEPLOYMENT:"
    npx vercel inspect "$DEPLOYMENT" --token "$VERCEL_TOKEN"
elif [ -n "$PROJECT" ]; then
    echo "📊 Latest deployments for $PROJECT:"
    npx vercel ls "$PROJECT" --token "$VERCEL_TOKEN"
else
    echo "Error: --project or --deployment required"
    exit 1
fi
