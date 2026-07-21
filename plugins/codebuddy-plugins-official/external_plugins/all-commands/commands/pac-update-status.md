---
description: Update ticket status and track progress in Product as Code workflow
category: project-task-management
argument-hint: "Specify status update details"
allowed-tools: Read, Write
---

# Update PAC Ticket Status

Update ticket status and track progress in Product as Code workflow

## Instructions

1. **Parse Command Arguments**
   - Extract arguments from: `$ARGUMENTS`
   - Required: `--ticket <ticket-id>` or select interactively
   - Optional: `--status <status>`, `--assignee <assignee>`, `--comment <comment>`
   - Validate `.pac/` directory exists

2. **Ticket Selection**
   - If ticket ID provided, validate it exists
   - Otherwise, show interactive ticket selector:
     - List tickets grouped by status
     - Show: ID, Name, Current Status, Assignee
     - Filter by epic if `--epic` flag provided
     - Allow search by ticket name

3. **Load Current Ticket State**
   - Read ticket file from `.pac/tickets/[ticket-id].yaml`
   - Display current ticket information:
     - Name and description
     - Current status and assignee
     - Epic association
     - Acceptance criteria progress
     - Task completion status

4. **Status Transition Validation**
   - Current status determines valid transitions:
     - `backlog` → `in-progress`, `cancelled`
     - `in-progress` → `review`, `blocked`, `backlog`
     - `review` → `done`, `in-progress`
     - `blocked` → `in-progress`, `cancelled`
     - `done` → (no transitions, warn if attempting)
     - `cancelled` → `backlog` (for resurrection)
   - Prevent invalid status transitions
   - Show available transitions if invalid status provided

5. **Update Ticket Status**
   - If new status provided and valid:
     - Update `spec.status` field
     - Update `metadata.updated` timestamp
     - Add status change to history (if tracking)
   - Special handling for status transitions:
     - `backlog → in-progress`: 
       - Prompt for assignee if not set
       - Suggest creating feature branch
     - `in-progress → review`:
       - Check if all tasks are marked complete
       - Warn if acceptance criteria not met
     - `review → done`:
       - Verify all acceptance criteria checked
       - Update completion timestamp

6. **Update Additional Fields**
   - If `--assignee` provided:
     - Update `metadata.assignee`
     - Add assignment history entry
   - If `--comment` provided:
     - Add to ticket comments/notes section
     - Include timestamp and current user

7. **Task and Criteria Progress**
   - If moving to `in-progress`, prompt to review tasks
   - Allow marking tasks as complete:
     ```yaml
     tasks:
       - [x] Create authentication service
       - [x] Implement login form component
       - [ ] Add session management
       - [ ] Write unit tests
     ```
   - Calculate and display completion percentage

8. **Update Parent Epic**
   - Load parent epic from `.pac/epics/[epic-id].yaml`
   - Update ticket entry in epic's ticket list:
     ```yaml
     tickets:
       - id: "[ticket-id]"
         name: "[ticket-name]"
         status: "[new-status]"  # Update this
         assignee: "[assignee]"
         updated: "[timestamp]"
     ```
   - If ticket is done, increment epic completion metrics

9. **Git Integration**
   - If status changes to `in-progress` and no branch exists:
     - Suggest: `git checkout -b feature/[ticket-id]`
   - If status changes to `review`:
     - Suggest creating pull request
     - Generate PR description from ticket details
   - If status changes to `done`:
     - Suggest merging and branch cleanup

10. **Generate Status Report**
    - Show status update summary:
      ```
      Ticket Status Updated
      ====================
      
      Ticket: [ticket-id] - [ticket-name]
      Epic: [epic-name]
      
      Status: [old-status] → [new-status]
      Assignee: [assignee]
      Updated: [timestamp]
      
      Progress:
      - Tasks: [completed]/[total] ([percentage]%)
      - Criteria: [met]/[total]
      
      Next Actions:
      - [Suggested next steps based on new status]
      ```

11. **Notification Hooks**
    - If `.pac/hooks/` directory exists:
      - Execute `status-change.sh` if present
      - Pass ticket ID, old status, new status as arguments
    - Could integrate with Slack, email, or project management tools

12. **Validation and Save**
    - Validate updated YAML structure
    - Create backup of original ticket file
    - Save updated ticket file
    - Run PAC validation on updated file
    - If validation fails, restore from backup

## Arguments

- `--ticket <ticket-id>`: Ticket ID to update (or select interactively)
- `--status <status>`: New status (backlog/in-progress/review/blocked/done/cancelled)
- `--assignee <assignee>`: Update assignee
- `--comment <comment>`: Add comment to ticket
- `--epic <epic-id>`: Filter tickets by epic (for interactive selection)
- `--force`: Force status change even if validation warnings exist

## Example Usage

```
/project:pac-update-status --ticket ticket-auth-001 --status in-progress
/project:pac-update-status --ticket ticket-ui-003 --status review --comment "Ready for code review"
/project:pac-update-status  # Interactive mode
/project:pac-update-status --epic epic-payment --status done
```