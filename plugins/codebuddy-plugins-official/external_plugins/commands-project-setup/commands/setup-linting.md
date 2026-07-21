---
description: Setup code linting and quality tools
category: project-setup
argument-hint: 1. **Project Analysis**
allowed-tools: Bash(npm *)
---

# Setup Linting Command

Setup code linting and quality tools

## Instructions

Follow this systematic approach to setup linting: **$ARGUMENTS**

1. **Project Analysis**
   - Identify programming languages and frameworks
   - Check existing linting configuration
   - Review current code style and patterns
   - Assess team preferences and requirements

2. **Tool Selection by Language**

   **JavaScript/TypeScript:**
   ```bash
   npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
   npm install -D prettier eslint-config-prettier eslint-plugin-prettier
   ```

   **Python:**
   ```bash
   pip install flake8 black isort mypy pylint
   ```

   **Java:**
   ```bash
   # Add to pom.xml or build.gradle
   # Checkstyle, SpotBugs, PMD
   ```

3. **Configuration Setup**

   **ESLint (.eslintrc.json):**
   ```json
   {
     "extends": [
       "eslint:recommended",
       "@typescript-eslint/recommended",
       "prettier"
     ],
     "parser": "@typescript-eslint/parser",
     "plugins": ["@typescript-eslint"],
     "rules": {
       "no-console": "warn",
       "no-unused-vars": "error",
       "@typescript-eslint/no-explicit-any": "warn"
     }
   }
   ```

4. **IDE Integration**
   - Configure VS Code settings
   - Setup auto-fix on save
   - Install relevant extensions

5. **CI/CD Integration**
   ```yaml
   - name: Lint code
     run: npm run lint
   ```

6. **Package.json Scripts**
   ```json
   {
     "scripts": {
       "lint": "eslint src --ext .ts,.tsx",
       "lint:fix": "eslint src --ext .ts,.tsx --fix",
       "format": "prettier --write src"
     }
   }
   ```

Remember to customize rules based on team preferences and gradually enforce stricter standards.