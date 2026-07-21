---
description: Sync project structure to Linear workspace
category: project-task-management
argument-hint: "Examine the current codebase structure and existing functionality"
---

# Project to Linear

Sync project structure to Linear workspace

## Instructions

1. **Analyze Project Requirements**
   - Review the provided task description or project requirements: **$ARGUMENTS**
   - Examine the current codebase structure and existing functionality
   - Identify all major components and features needed
   - Determine technical dependencies and constraints
   - Assess the scope and complexity of the work

2. **Understand User's Intent**
   - Ask clarifying questions about:
     - Project goals and objectives
     - Priority levels for different features
     - Timeline expectations
     - Technical preferences or constraints
     - Team structure (if relevant)
     - Definition of done for tasks
   - Confirm understanding of the requirements before proceeding

3. **Check Linear Configuration**
   - Verify if Linear MCP server is available and configured
   - If not available, ask the user to:
     - Install the Linear MCP server if not already installed
     - Configure the Linear API key in their MCP settings
     - Provide the default team ID or workspace information
   - Test the connection by listing available projects

4. **Project Setup in Linear**
   - Ask the user if they want to:
     - Use an existing Linear project (request project ID)
     - Create a new project (ask for project name and description)
   - For new projects, determine:
     - Project type (Feature, Bug, Task, etc.)
     - Project status (Planning, In Progress, etc.)
     - Project lead or owner
     - Any custom fields or labels to use

5. **Generate Comprehensive Task List**
   - Break down the project into logical phases:
     - Planning and Design
     - Core Implementation
     - Testing and Quality Assurance
     - Documentation
     - Deployment and Release
   - For each phase, create detailed tasks including:
     - Clear, actionable task titles
     - Detailed descriptions with acceptance criteria
     - Technical specifications where relevant
     - Estimated effort (if requested)
     - Dependencies between tasks
     - Priority levels (Critical, High, Medium, Low)

6. **Create Task Hierarchy**
   - Organize tasks into a proper hierarchy:
     - Epic/Project level (if creating new project)
     - Parent tasks for major features or components
     - Subtasks for implementation details
     - Related tasks for cross-cutting concerns
   - Ensure logical grouping and dependencies

7. **Add Task Details**
   - For each task, include:
     - **Title**: Clear, concise description
     - **Description**: Detailed requirements and context
     - **Acceptance Criteria**: Definition of done
     - **Labels**: Appropriate tags (frontend, backend, testing, etc.)
     - **Priority**: Based on user input and analysis
     - **Estimates**: If sizing is requested
     - **Assignee**: If team members are specified
     - **Due Dates**: Based on timeline requirements

8. **Create Tasks in Linear**
   - Use the Linear MCP server to:
     - Create the project (if new)
     - Create all parent tasks first
     - Create subtasks under appropriate parents
     - Set up dependencies between tasks
     - Apply labels and priorities
     - Add any custom fields
   - Provide feedback on each task created

9. **Review and Refinement**
   - Present a summary of all created tasks
   - Show the task hierarchy and relationships
   - Ask if any adjustments are needed:
     - Task grouping or organization
     - Priority changes
     - Additional tasks or details
     - Timeline adjustments
   - Make any requested modifications

10. **Provide Project Overview**
    - Generate a summary including:
      - Total number of tasks created
      - Task breakdown by type/phase
      - Critical path items
      - Estimated timeline (if applicable)
      - Link to the Linear project
      - Next recommended actions

## Example Task Structure

```
Project: User Dashboard Feature
├── Planning & Design
│   ├── Create UI/UX mockups
│   ├── Define API requirements
│   └── Technical design document
├── Backend Development
│   ├── User API endpoints
│   │   ├── GET /api/users endpoint
│   │   ├── PUT /api/users/:id endpoint
│   │   └── User data validation
│   └── Dashboard data aggregation
├── Frontend Development
│   ├── Dashboard layout component
│   ├── User profile widget
│   ├── Activity feed component
│   └── Data visualization charts
├── Testing
│   ├── Unit tests for API
│   ├── Frontend component tests
│   ├── E2E dashboard tests
│   └── Performance testing
└── Documentation & Deployment
    ├── API documentation
    ├── User guide
    └── Production deployment
```

## Integration Notes

- This command requires the Linear MCP server to be configured
- If MCP is not available, provide the task list in a format that can be manually imported
- Support batch operations to avoid rate limiting
- Handle errors gracefully and provide clear feedback
- Maintain task relationships and dependencies properly