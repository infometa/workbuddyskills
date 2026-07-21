#!/bin/bash

# CodeBuddy Chat Web - Template Copy Script
# This script copies the complete project template to a new directory

set -e

# Check if project name is provided
if [ -z "$1" ]; then
    echo "Error: Project name is required"
    echo "Usage: $0 <project-name>"
    exit 1
fi

PROJECT_NAME="$1"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"

# Check if template directory exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Error: Template directory not found at $TEMPLATE_DIR"
    exit 1
fi

# Check if target directory already exists
if [ -d "$PROJECT_NAME" ]; then
    echo "Error: Directory '$PROJECT_NAME' already exists"
    exit 1
fi

# Create project directory and copy template contents
echo "Creating project '$PROJECT_NAME' from template..."
mkdir -p "$PROJECT_NAME"
cp -r "$TEMPLATE_DIR/"* "$PROJECT_NAME/"

# Update package.json with project name
if [ -f "$PROJECT_NAME/package.json" ]; then
    # Use sed to replace the name field in package.json
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/\"name\": \".*\"/\"name\": \"$PROJECT_NAME\"/" "$PROJECT_NAME/package.json"
    else
        # Linux
        sed -i "s/\"name\": \".*\"/\"name\": \"$PROJECT_NAME\"/" "$PROJECT_NAME/package.json"
    fi
fi

echo "✓ Project created successfully!"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. npm install"
echo "  3. cp .env.example .env"
echo "  4. Edit .env and add your CODEBUDDY_API_KEY"
echo "  5. npm run dev"
echo ""
echo "The app will be available at http://localhost:5173"
