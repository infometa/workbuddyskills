---
description: Create a new ticket within an epic following the Product as Code specification
category: project-task-management
argument-hint: "Specify ticket details"
allowed-tools: Write
---

# Create PAC Ticket

Create a new ticket within an epic following the Product as Code specification

## Instructions

1. **Validate PAC Environment**
   - Verify `.pac/` directory exists
   - Check PAC configuration at `.pac/pac.config.yaml`
   - If not configured, suggest running `/project:pac-configure`
   - Parse arguments from: `$ARGUMENTS`

2. **Epic Selection**
   - If `--epic <epic-id>` provided, validate epic exists
   - Otherwise, list available epics from `.pac/epics/`:
     - Show epic ID, name, and ticket count
     - Allow user to select epic interactively
   - Load selected epic to understand context

3. **Ticket Information Gathering**
   - Parse command arguments:
     - `--name <name>`: Ticket name
     - `--type <type>`: feature/bug/task/spike
     - `--description <desc>`: Ticket description
     - `--assignee <assignee>`: Assigned developer
     - `--priority <priority>`: low/medium/high/critical
   - For missing required fields, prompt interactively:
     - Ticket name (required)
     - Ticket type (default: feature)
     - Description (multi-line)
     - Assignee (default from config)
     - Priority (default: medium)
     - Initial status (default: backlog)

4. **Generate Ticket ID**
   - Create ID format: `ticket-[epic-short-name]-[sequence]`
   - Example: `ticket-auth-001`, `ticket-auth-002`
   - Check existing tickets in epic to determine sequence
   - Ensure uniqueness across all tickets

5. **Define Acceptance Criteria**
   - Prompt for acceptance criteria (at least 2 items)
   - Format as checkbox list:
     ```yaml
     acceptance_criteria:
       - [ ] User can successfully authenticate
       - [ ] Session persists across page refreshes
       - [ ] Invalid credentials show error message
     ```

6. **Define Implementation Tasks**
   - Prompt for implementation tasks
   - Break down work into actionable items:
     ```yaml
     tasks:
       - [ ] Create authentication service
       - [ ] Implement login form component
       - [ ] Add session management
       - [ ] Write unit tests
       - [ ] Update documentation
     ```

7. **Create Ticket Structure**
   - Generate ticket YAML following PAC v0.1.0:
     ```yaml
     apiVersion: productascode.org/v0.1.0
     kind: Ticket
     metadata:
       id: "[generated-ticket-id]"
       sequence: [number]
       name: "[Ticket Name]"
       epic: "[parent-epic-id]"
       created: "[timestamp]"
       updated: "[timestamp]"
       assignee: "[assignee]"
       labels:
         component: "[relevant-component]"
         effort: "[size-estimate]"
     spec:
       description: |
         [Detailed description]
         
       type: "[feature/bug/task/spike]"
       status: "[backlog/in-progress/review/done]"
       priority: "[low/medium/high/critical]"
       
       acceptance_criteria:
         - [ ] [Criterion 1]
         - [ ] [Criterion 2]
         
       tasks:
         - [ ] [Task 1]
         - [ ] [Task 2]
         
       technical_notes: |
         [Any technical considerations]
         
       dependencies:
         - [Other ticket IDs if any]
     ```

8. **Estimate Effort**
   - Prompt for effort estimation:
     - Story points (1, 2, 3, 5, 8, 13)
     - T-shirt size (XS, S, M, L, XL)
     - Time estimate (hours/days)
   - Add to metadata labels

9. **Link to Epic**
   - Update parent epic file to include ticket reference:
     ```yaml
     spec:
       tickets:
         - id: "[ticket-id]"
           name: "[ticket-name]"
           status: "backlog"
           assignee: "[assignee]"
     ```

10. **Save Ticket File**
    - Save to: `.pac/tickets/[ticket-id].yaml`
    - Create symbolic link in epic directory:
      `.pac/epics/[epic-id]/tickets/[ticket-id].yaml`
    - Validate file was created successfully

11. **Create Branch (Optional)**
    - If `--create-branch` flag or git integration enabled:
      - Create branch: `feature/[ticket-id]`
      - Include branch name in ticket metadata
      - Show git commands for switching to branch

12. **Generate Ticket Summary**
    - Display created ticket information:
      - Ticket ID and file location
      - Epic association
      - Assignee and priority
      - Task count and acceptance criteria count
    - Show next actions:
      - Start work: `git checkout -b feature/[ticket-id]`
      - Update status: `/project:pac-update-ticket --id [ticket-id] --status in-progress`
      - View ticket: `cat .pac/tickets/[ticket-id].yaml`

## Arguments

- `--epic <epic-id>`: Parent epic ID (required)
- `--name <name>`: Ticket name
- `--type <type>`: Ticket type (feature/bug/task/spike)
- `--description <description>`: Ticket description
- `--assignee <assignee>`: Assigned developer
- `--priority <priority>`: Priority level
- `--create-branch`: Automatically create git branch
- `--template <template>`: Use custom ticket template

## Example Usage

```
/project:pac-create-ticket --epic epic-authentication
/project:pac-create-ticket --epic epic-payment --name "Implement Stripe integration" --type feature
/project:pac-create-ticket --epic epic-ui --assignee jane@example.com --priority high --create-branch
```