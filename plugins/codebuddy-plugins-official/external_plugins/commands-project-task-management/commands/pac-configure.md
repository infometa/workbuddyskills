---
description: Configure and initialize a project following the Product as Code specification for structured, version-controlled product management
category: project-task-management
argument-hint: "Specify configuration settings"
---

# Configure PAC (Product as Code) Project

Configure and initialize a project following the Product as Code specification for structured, version-controlled product management

## Instructions

1. **Analyze Project Context**
   - Check if the current directory is a git repository
   - Verify if a PAC configuration already exists (look for epic-*.yaml or ticket-*.yaml files)
   - Parse any arguments provided: `$ARGUMENTS`
   - If PAC files exist, analyze them to understand current structure

2. **Interactive Setup (if no existing PAC config)**
   - Ask user for project details:
     - Project name
     - Project description
     - Primary product owner
     - Default ticket assignee
     - Initial epic name
   - Validate inputs and confirm with user before proceeding

3. **Create PAC Directory Structure**
   - Create `.pac/` directory if it doesn't exist
   - Create subdirectories:
     - `.pac/epics/` - for epic definitions
     - `.pac/tickets/` - for ticket definitions
     - `.pac/templates/` - for reusable templates
   - Add `.pac/README.md` explaining the structure and PAC specification

4. **Generate PAC Configuration Files**
   - Create `.pac/pac.config.yaml` with:
     ```yaml
     apiVersion: productascode.org/v0.1.0
     kind: Configuration
     metadata:
       project: "[project-name]"
       owner: "[owner-name]"
       created: "[timestamp]"
     spec:
       defaults:
         assignee: "[default-assignee]"
         epic_prefix: "epic-"
         ticket_prefix: "ticket-"
       validation:
         enforce_unique_ids: true
         require_acceptance_criteria: true
     ```

5. **Create Initial Epic Template**
   - Generate `.pac/templates/epic-template.yaml`:
     ```yaml
     apiVersion: productascode.org/v0.1.0
     kind: Epic
     metadata:
       id: "epic-[name]"
       name: "[Epic Name]"
       created: "[timestamp]"
       owner: "[owner]"
     spec:
       description: |
         [Epic description]
       scope: |
         [Scope definition]
       success_criteria:
         - [Criterion 1]
         - [Criterion 2]
       tickets: []
     ```

6. **Create Initial Ticket Template**
   - Generate `.pac/templates/ticket-template.yaml`:
     ```yaml
     apiVersion: productascode.org/v0.1.0
     kind: Ticket
     metadata:
       id: "ticket-[name]"
       name: "[Ticket Name]"
       epic: "[parent-epic-id]"
       created: "[timestamp]"
       assignee: "[assignee]"
     spec:
       description: |
         [Ticket description]
       type: "feature"
       status: "backlog"
       priority: "medium"
       acceptance_criteria:
         - [ ] [Criterion 1]
         - [ ] [Criterion 2]
       tasks:
         - [ ] [Task 1]
         - [ ] [Task 2]
     ```

7. **Create First Epic and Ticket**
   - Based on user input, create first epic in `.pac/epics/`
   - Create an initial ticket linked to the epic
   - Use proper naming convention and unique IDs
   - Set appropriate timestamps

8. **Set Up Validation Scripts**
   - Create `.pac/scripts/validate.sh` to check PAC compliance:
     - Verify YAML syntax
     - Check required fields
     - Validate unique IDs
     - Ensure epic-ticket relationships are valid
   - Make script executable

9. **Configure Git Integration**
   - Add PAC-specific entries to `.gitignore` if needed:
     ```
     .pac/tmp/
     .pac/cache/
     *.pac.lock
     ```
   - Create git hook for pre-commit PAC validation (optional)

10. **Generate PAC Documentation**
    - Create `.pac/GUIDE.md` with:
      - Quick start guide for team members
      - Common PAC workflows
      - How to create new epics and tickets
      - How to update ticket status
      - Link to full PAC specification

11. **Create Helper Commands**
    - Generate `.pac/scripts/new-epic.sh` for creating new epics
    - Generate `.pac/scripts/new-ticket.sh` for creating new tickets
    - Include prompts for required fields and validation

12. **Final Validation and Summary**
    - Run validation script on created files
    - Display summary of created structure
    - Show next steps:
      - How to create new epics: `cp .pac/templates/epic-template.yaml .pac/epics/epic-[name].yaml`
      - How to create new tickets: `cp .pac/templates/ticket-template.yaml .pac/tickets/ticket-[name].yaml`
      - How to validate PAC files: `.pac/scripts/validate.sh`
    - Suggest integrating with CI/CD for automatic validation

## Arguments

- `--minimal`: Create minimal PAC structure without templates and scripts
- `--epic-name <name>`: Specify initial epic name
- `--owner <name>`: Specify product owner name
- `--no-git`: Skip git integration setup

## Example Usage

```
/project:pac-configure
/project:pac-configure --epic-name "user-authentication" --owner "john.doe"
/project:pac-configure --minimal
```