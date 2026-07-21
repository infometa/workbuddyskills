#!/bin/bash
# Example SessionStart hook for loading project context
# This script detects project type and sets environment variables

set -euo pipefail

# Navigate to project directory
cd "$CODEBUDDY_PROJECT_DIR" || exit 1

echo "Loading project context..."

# Detect project type and set environment
if [ -f "package.json" ]; then
  echo "📦 Node.js project detected"
  echo "export PROJECT_TYPE=nodejs" >> "$CODEBUDDY_ENV_FILE"

  # Check if TypeScript
  if [ -f "tsconfig.json" ]; then
    echo "export USES_TYPESCRIPT=true" >> "$CODEBUDDY_ENV_FILE"
  fi

elif [ -f "Cargo.toml" ]; then
  echo "🦀 Rust project detected"
  echo "export PROJECT_TYPE=rust" >> "$CODEBUDDY_ENV_FILE"

elif [ -f "go.mod" ]; then
  echo "🐹 Go project detected"
  echo "export PROJECT_TYPE=go" >> "$CODEBUDDY_ENV_FILE"

elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  echo "🐍 Python project detected"
  echo "export PROJECT_TYPE=python" >> "$CODEBUDDY_ENV_FILE"

elif [ -f "pom.xml" ]; then
  echo "☕ Java (Maven) project detected"
  echo "export PROJECT_TYPE=java" >> "$CODEBUDDY_ENV_FILE"
  echo "export BUILD_SYSTEM=maven" >> "$CODEBUDDY_ENV_FILE"

elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
  echo "☕ Java/Kotlin (Gradle) project detected"
  echo "export PROJECT_TYPE=java" >> "$CODEBUDDY_ENV_FILE"
  echo "export BUILD_SYSTEM=gradle" >> "$CODEBUDDY_ENV_FILE"

else
  echo "❓ Unknown project type"
  echo "export PROJECT_TYPE=unknown" >> "$CODEBUDDY_ENV_FILE"
fi

# Check for CI configuration
if [ -f ".github/workflows" ] || [ -f ".gitlab-ci.yml" ] || [ -f ".circleci/config.yml" ]; then
  echo "export HAS_CI=true" >> "$CODEBUDDY_ENV_FILE"
fi

echo "Project context loaded successfully"
exit 0
