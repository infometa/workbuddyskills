---
description: Create a new epic following the Product as Code specification with guided workflow
category: project-task-management
argument-hint: "Specify epic details"
allowed-tools: Write
---

# Create PAC Epic

Create a new epic following the Product as Code specification with guided workflow

## Instructions

1. **Validate PAC Configuration**
   - Check if `.pac/` directory exists
   - Verify PAC configuration file exists at `.pac/pac.config.yaml`
   - If not configured, suggest running `/project:pac-configure` first
   - Parse arguments: `$ARGUMENTS`

2. **Epic Information Gathering**
   - If arguments provided, parse:
     - `--name <name>`: Epic name
     - `--description <desc>`: Epic description
     - `--owner <owner>`: Epic owner
     - `--scope <scope>`: Scope definition
   - For missing information, prompt user interactively:
     - Epic ID (suggest format: epic-[kebab-case-name])
     - Epic name (human-readable)
     - Epic owner (default from config if available)
     - Epic description (multi-line)
     - Scope definition (what's included/excluded)
     - Success criteria (at least 2-3 items)

3. **Generate Epic ID**
   - If not provided, generate from epic name:
     - Convert to lowercase
     - Replace spaces with hyphens
     - Remove special characters
     - Prefix with "epic-"
   - Validate uniqueness against existing epics

4. **Create Epic Structure**
   - Generate epic YAML following PAC v0.1.0 specification:
     ```yaml
     apiVersion: productascode.org/v0.1.0
     kind: Epic
     metadata:
       id: "[generated-epic-id]"
       name: "[Epic Name]"
       created: "[current-timestamp]"
       updated: "[current-timestamp]"
       owner: "[owner-email-or-name]"
       labels:
         status: "active"
         priority: "medium"
     spec:
       description: |
         [Multi-line description]
       
       scope: |
         [Scope definition]
       
       success_criteria:
         - [Criterion 1]
         - [Criterion 2]
         - [Criterion 3]
       
       constraints:
         - [Any constraints or limitations]
       
       dependencies:
         - [Dependencies on other epics/systems]
       
       tickets: []  # Will be populated as tickets are created
     ```

5. **Validate Epic Content**
   - Check all required fields are present
   - Validate apiVersion matches specification
   - Ensure metadata has required identifiers
   - Verify success criteria has at least one item
   - Check YAML syntax is valid

6. **Save Epic File**
   - Determine filename: `.pac/epics/[epic-id].yaml`
   - Check if file already exists
   - If exists, ask user to confirm overwrite
   - Write epic content to file
   - Set appropriate file permissions

7. **Create Epic Directory Structure**
   - Create `.pac/epics/[epic-id]/` directory for epic-specific docs
   - Add `.pac/epics/[epic-id]/README.md` with epic overview
   - Create `.pac/epics/[epic-id]/tickets/` for future ticket links

8. **Update PAC Index**
   - If `.pac/index.yaml` exists, add epic entry:
     ```yaml
     epics:
       - id: "[epic-id]"
         name: "[Epic Name]"
         status: "active"
         created: "[timestamp]"
         ticket_count: 0
     ```

9. **Git Integration**
   - If in git repository:
     - Add new epic file to git
     - Create branch `pac/[epic-id]` for epic work
     - Prepare commit message:
       ```
       feat(pac): add epic [epic-id]
       
       - Epic: [Epic Name]
       - Owner: [Owner]
       - Success Criteria: [count] items defined
       ```

10. **Generate Epic Summary**
    - Display created epic details:
      - Epic ID and location
      - Success criteria summary
      - Next steps for creating tickets
    - Show helpful commands:
      - Create ticket: `/project:pac-create-ticket --epic [epic-id]`
      - View epic: `cat .pac/epics/[epic-id].yaml`
      - Validate: `.pac/scripts/validate.sh .pac/epics/[epic-id].yaml`

## Arguments

- `--name <name>`: Epic name (required if not interactive)
- `--description <description>`: Epic description
- `--owner <owner>`: Epic owner email or name
- `--scope <scope>`: Scope definition
- `--success-criteria <criteria>`: Comma-separated success criteria
- `--priority <priority>`: Priority level (low/medium/high/critical)
- `--no-git`: Skip git integration

## Example Usage

```
/project:pac-create-epic
/project:pac-create-epic --name "User Authentication System"
/project:pac-create-epic --name "Payment Integration" --owner "john@example.com" --priority high
```