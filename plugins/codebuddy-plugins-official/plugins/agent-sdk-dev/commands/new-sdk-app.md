---
description: Create and setup a new CodeBuddy Agent SDK application
argument-hint: [project-name]
---

You are tasked with helping the user create a new CodeBuddy Agent SDK application. Follow these steps carefully:

## About CodeBuddy Agent SDK

CodeBuddy Agent SDK is the AI agent development toolkit provided by Tencent, allowing you to programmatically build AI agents with CodeBuddy capabilities.

**SDK Information:**
- TypeScript package: `@tencent-ai/agent-sdk`
- Python package: `codebuddy-agent-sdk`
- Node.js requirement: >= 18.20
- Python requirement: >= 3.10

## Reference Documentation

Before starting, review the official documentation to ensure you provide accurate and up-to-date guidance. Use WebFetch to read these pages:

1. **Start with the SDK overview**: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk.md
2. **Based on the user's language choice, read the appropriate SDK reference**:
   - TypeScript: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-typescript.md
   - Python: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-python.md
3. **Read relevant guides**:
   - Session management: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-sessions.md
   - Hook system: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-hooks.md
   - Permission control: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-permissions.md
   - MCP integration: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-mcp.md
   - Custom tools: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-custom-tools.md
   - Example projects: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-demos.md

**IMPORTANT**: Always check for and use the latest versions of packages. Use WebSearch or WebFetch to verify current versions before installation.

## Gather Requirements

IMPORTANT: Ask these questions one at a time. Wait for the user's response before asking the next question.

Ask the questions in this order (skip any that the user has already provided via arguments):

1. **Language** (ask first): "Would you like to use TypeScript or Python?"

   - Wait for response before continuing

2. **Project name** (ask second): "What would you like to name your project?"

   - If $ARGUMENTS is provided, use that as the project name and skip this question
   - Wait for response before continuing

3. **Agent type** (ask third, skip if #2 was sufficiently detailed): "What kind of agent are you building? Some examples:

   - Coding agent (code review, automated testing, documentation generation)
   - Business agent (customer support, data analysis, content creation)
   - Automation workflow (CI/CD integration, deployment automation)
   - Custom agent (describe your use case)"
   - Wait for response before continuing

4. **Starting point** (ask fourth): "Would you like:

   - A minimal 'Hello World' example to start
   - A basic agent with common features (multi-turn conversation, permission control)
   - A specific example based on your use case"
   - Wait for response before continuing

5. **Tooling choice** (ask fifth): Let the user know what tools you'll use, and confirm with them:
   - TypeScript: npm/yarn/pnpm
   - Python: pip/uv/poetry

After all questions are answered, proceed to create the setup plan.

## Setup Plan

Based on the user's answers, create a plan that includes:

1. **Project initialization**:

   - Create project directory (if it doesn't exist)
   - Initialize package manager:
     - TypeScript: `npm init -y` and setup `package.json` with `"type": "module"` and scripts (include a "typecheck" script)
     - Python: Create `requirements.txt` or use `uv init` / `poetry init`
   - Add necessary configuration files:
     - TypeScript: Create `tsconfig.json` with proper settings for the SDK
     - Python: Create pyproject.toml if needed

2. **Check for Latest Versions**:

   - BEFORE installing, use WebSearch or check npm/PyPI to find the latest version
   - For TypeScript: Check https://www.npmjs.com/package/@tencent-ai/agent-sdk
   - For Python: Check https://pypi.org/project/codebuddy-agent-sdk/
   - Inform the user which version you're installing

3. **SDK Installation**:

   - TypeScript: `npm install @tencent-ai/agent-sdk`
   - Python: `pip install codebuddy-agent-sdk` or `uv add codebuddy-agent-sdk`
   - After installation, verify the installed version:
     - TypeScript: Check package.json or run `npm list @tencent-ai/agent-sdk`
     - Python: Run `pip show codebuddy-agent-sdk`

4. **Create starter files**:

   TypeScript example (`index.ts`):
   ```typescript
   import { query } from '@tencent-ai/agent-sdk';

   async function main() {
     const q = query({
       prompt: 'Hello, please introduce yourself',
       options: { permissionMode: 'bypassPermissions' }
     });
     
     for await (const message of q) {
       if (message.type === 'assistant') {
         for (const block of message.message.content) {
           if (block.type === 'text') {
             console.log(block.text);
           }
         }
       }
     }
   }

   main().catch(console.error);
   ```

   Python example (`main.py`):
   ```python
   import asyncio
   from codebuddy_agent_sdk import query, CodeBuddyAgentOptions, AssistantMessage, TextBlock

   async def main():
       options = CodeBuddyAgentOptions(permission_mode="bypassPermissions")
       async for message in query(prompt="Hello, please introduce yourself", options=options):
           if isinstance(message, AssistantMessage):
               for block in message.content:
                   if isinstance(block, TextBlock):
                       print(block.text)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

5. **Environment setup**:

   - Create `.gitignore` file (include .env, node_modules, __pycache__, etc.)
   - Explain authentication methods:
     - Method 1: Use CodeBuddy CLI login (`codebuddy login`)
     - Method 2: Set environment variable `CODEBUDDY_API_KEY`

6. **Optional: Create .codebuddy directory structure**:
   - Offer to create `.codebuddy/` directory for agents, commands, and settings
   - Ask if they want any example configurations

## Implementation

After gathering requirements and getting user confirmation on the plan:

1. Check for latest package versions using WebSearch or WebFetch
2. Execute the setup steps
3. Create all necessary files
4. Install dependencies (always use latest stable versions)
5. Verify installed versions and inform the user
6. Create a working example based on their agent type
7. Add helpful comments in the code explaining what each part does
8. **VERIFY THE CODE WORKS BEFORE FINISHING**:
   - For TypeScript:
     - Run `npx tsc --noEmit` to check for type errors
     - Fix ALL type errors until types pass completely
     - Ensure imports and types are correct
     - Only proceed when type checking passes with no errors
   - For Python:
     - Verify imports are correct
     - Check for basic syntax errors
   - **DO NOT consider the setup complete until the code verifies successfully**

## Verification

After all files are created and dependencies are installed, use the appropriate verifier agent to validate that the Agent SDK application is properly configured and ready for use:

1. **For TypeScript projects**: Launch the **agent-sdk-verifier-ts** agent to validate the setup
2. **For Python projects**: Launch the **agent-sdk-verifier-py** agent to validate the setup
3. The agent will check SDK usage, configuration, functionality, and adherence to official documentation
4. Review the verification report and address any issues

## Getting Started Guide

Once setup is complete and verified, provide the user with:

1. **Next steps**:

   - How to set up authentication:
     - Using CLI: `codebuddy login`
     - Or set environment variable: `export CODEBUDDY_API_KEY="your-api-key"`
   - How to run their agent:
     - TypeScript: `npm start` or `npx tsx index.ts`
     - Python: `python main.py`

2. **Useful resources**:

   - SDK Overview: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk.md
   - TypeScript SDK Reference: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-typescript.md
   - Python SDK Reference: https://cnb.cool/codebuddy/codebuddy-code/-/git/raw/main/docs/sdk-python.md
   - Explain key concepts: permission modes, hook system, MCP servers

3. **Common next steps**:
   - How to implement multi-turn conversations (session management)
   - How to add custom tools via MCP
   - How to configure permission control (canUseTool callback)
   - How to create custom Agents

## Important Notes

- **ALWAYS USE LATEST VERSIONS**: Before installing any packages, check for the latest versions
- **VERIFY CODE RUNS CORRECTLY**:
  - For TypeScript: Run `npx tsc --noEmit` and fix ALL type errors before finishing
  - For Python: Verify syntax and imports are correct
  - Do NOT consider the task complete until the code passes verification
- Verify the installed version after installation and inform the user
- Check the official documentation for any version-specific requirements
- Always check if directories/files already exist before creating them
- Use the user's preferred package manager
- Ensure all code examples are functional and include proper error handling
- Use modern syntax and patterns that are compatible with the latest SDK version
- Make the experience interactive and educational
- **ASK QUESTIONS ONE AT A TIME** - Do not ask multiple questions in a single response

Begin by asking the FIRST requirement question only. Wait for the user's answer before proceeding to the next question.
