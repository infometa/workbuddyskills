---
description: Create a new command following existing patterns and organizational structure
category: project-task-management
allowed-tools: Read, Write, Edit, LS, Glob
---

Create a new command that follows the existing patterns and organizational structure in this project.

## ANALYZE EXISTING COMMANDS

1. First, study the existing commands in the `.claude/commands/` directory to understand:
   - Common patterns and structures
   - Naming conventions
   - Documentation styles
   - Command organization

2. Use MCP tools to explore the codebase and understand:
   - Project structure
   - Existing functionality
   - Code patterns
   - Dependencies

## UNDERSTAND THE REQUEST

3. Analyze the user's request to determine:
   - The command's purpose and functionality
   - Which category it belongs to
   - Similar existing commands to reference
   - Required inputs and outputs

## SELECT APPROPRIATE PATTERNS

4. Based on your analysis, choose the most appropriate pattern:
   - Simple execution commands
   - File generation commands
   - Analysis and reporting commands
   - Multi-step workflow commands

## DETERMINE COMMAND LOCATION

5. Place the command in the appropriate category directory:
   - `code-analysis-testing/` - For code analysis, testing, and quality assurance
   - `ci-deployment/` - For CI/CD and deployment related commands
   - `context-loading-priming/` - For loading context and priming commands
   - `documentation-changelogs/` - For documentation and changelog commands
   - `project-task-management/` - For project and task management commands
   - `version-control-git/` - For version control and Git operations
   - `miscellaneous/` - For commands that don't fit other categories

## PLAN SUPPORTING RESOURCES

6. Consider what supporting resources might be needed:
   - Templates or example files
   - Configuration files
   - Documentation updates
   - Related commands that might work together

## CREATE THE COMMAND

7. Write the command following these guidelines:
   - Use clear, descriptive names
   - Include comprehensive instructions
   - Follow existing formatting patterns
   - Add appropriate examples
   - Include error handling considerations

## HUMAN REVIEW

8. Present your analysis and proposed command to the human for review before implementation, including:
   - Command purpose and location
   - Key patterns you're following
   - Any assumptions you're making
   - Questions about specific requirements