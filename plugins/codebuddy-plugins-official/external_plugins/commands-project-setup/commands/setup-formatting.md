---
description: Configure code formatting tools
category: project-setup
argument-hint: 1. **Language-Specific Tools**
allowed-tools: Bash(npm *)
---

# Setup Formatting Command

Configure code formatting tools

## Instructions

Setup code formatting following these steps: **$ARGUMENTS**

1. **Language-Specific Tools**

   **JavaScript/TypeScript:**
   ```bash
   npm install -D prettier
   echo '{"semi": true, "singleQuote": true, "tabWidth": 2}' > .prettierrc
   ```

   **Python:**
   ```bash
   pip install black isort
   echo '[tool.black]\nline-length = 88\ntarget-version = ["py38"]' > pyproject.toml
   ```

   **Java:**
   ```bash
   # Google Java Format or Spotless plugin
   ```

2. **Configuration Files**

   **.prettierrc:**
   ```json
   {
     "semi": true,
     "singleQuote": true,
     "tabWidth": 2,
     "trailingComma": "es5",
     "printWidth": 80
   }
   ```

3. **IDE Setup**
   - Install formatter extensions
   - Enable format on save
   - Configure keyboard shortcuts

4. **Scripts and Automation**
   ```json
   {
     "scripts": {
       "format": "prettier --write .",
       "format:check": "prettier --check ."
     }
   }
   ```

5. **Pre-commit Hooks**
   ```bash
   npm install -D husky lint-staged
   echo '{"*.{js,ts,tsx}": ["prettier --write", "eslint --fix"]}' > .lintstagedrc
   ```

Remember to run formatting on entire codebase initially and configure team IDE settings consistently.