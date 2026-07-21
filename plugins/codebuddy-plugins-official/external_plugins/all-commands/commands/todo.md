---
description: Manage project todos in a todos.md file with add, complete, remove, and list operations
category: project-task-management
argument-hint: <action> [args...]
allowed-tools: Read, Write, Edit
---

# Project Todo Manager

Manage todos in a `todos.md` file at the root of your current project directory.

## Usage Examples:
- `/user:todo add "Fix navigation bug"`
- `/user:todo add "Fix navigation bug" [date/time/"tomorrow"/"next week"]` an optional 2nd parameter to set a due date
- `/user:todo complete 1`
- `/user:todo remove 2`
- `/user:todo list`
- `/user:todo undo 1`

## Instructions:
Parse the command arguments: $ARGUMENTS

Manage todos in a `todos.md` file at the root of the current project directory. When this command is invoked:

1. **Determine the project root** by looking for common indicators (.git, package.json, etc.)
2. **Locate or create** `todos.md` in the project root
3. **Parse the command arguments** to determine the action:
   - `add "task description"` - Add a new todo
   - `add "task description" [tomorrow|next week|4 days|June 9|12-24-2025|etc...]` - Add a new todo with the provided due date
   - `due N [tomorrow|next week|4 days|June 9|12-24-2025|etc...]` - Mark todo N with the due date provided
   - `complete N` - Mark todo N as completed and move from the ##Active list to the ##Completed list
   - `remove N` - Remove todo N entirely
   - `undo N` - Mark completed todo N as incomplete
   - `list [N]` or no args - Show all (or N number of) todos in a user-friendly format, with each todo numbered for reference
   - `past due` - Show all of the tasks which are past due and still active
   - `next` - Shows the next active task in the list, this should respect Due dates, if there are any. If not, just show the first todo in the Active list

## Todo Format:
Use this markdown format in todos.md:
```
# Project Todos

## Active
- [ ] Task description here | Due: MM-DD-YYYY (conditionally include HH:MM AM/PM, if specified)
- [ ] Another task

## Completed
- [x] Completed task description | Due: MM-DD-YYYY | Completed: MM-DD-YYYY
```

## Implementation Notes:
- Always show friendly numbered lists when displaying todos
- Handle date parsing for common formats (natural language, ISO dates, etc.)
- Maintain the markdown checkbox format for compatibility
- Keep completed tasks in the file for reference but in a separate section
- Support undo operations by moving tasks back to Active section