#!/bin/bash
# Vercel environment variable management

set -euo pipefail

if [ -z "${VERCEL_TOKEN:-}" ]; then
    echo "Error: VERCEL_TOKEN not set"
    exit 1
fi

PROJECT=""
ACTION=""
KEY=""
VALUE=""
ENV="production"

while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --list)
            ACTION="list"
            shift
            ;;
        --set)
            ACTION="set"
            shift
            ;;
        --delete)
            ACTION="delete"
            shift
            ;;
        --key)
            KEY="$2"
            shift 2
            ;;
        --value)
            VALUE="$2"
            shift 2
            ;;
        --env)
            ENV="$2"
            shift 2
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

case $ACTION in
    list)
        echo "📋 Environment variables for $PROJECT:"
        npx vercel env ls --token "$VERCEL_TOKEN" "$PROJECT"
        ;;
    set)
        if [ -z "$KEY" ] || [ -z "$VALUE" ]; then
            echo "Error: --key and --value required for --set"
            exit 1
        fi
        echo "✏️  Setting $KEY=$VALUE (env: $ENV)"
        echo "$VALUE" | npx vercel env add "$KEY" "$ENV" --token "$VERCEL_TOKEN" "$PROJECT"
        echo "✅ Environment variable set!"
        ;;
    delete)
        if [ -z "$KEY" ]; then
            echo "Error: --key required for --delete"
            exit 1
        fi
        echo "🗑️  Deleting $KEY (env: $ENV)"
        npx vercel env rm "$KEY" "$ENV" --token "$VERCEL_TOKEN" "$PROJECT" --yes
        echo "✅ Environment variable deleted!"
        ;;
    *)
        echo "Error: Action required (--list, --set, or --delete)"
        exit 1
        ;;
esac
