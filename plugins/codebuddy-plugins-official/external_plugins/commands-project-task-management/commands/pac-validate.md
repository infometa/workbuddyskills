---
description: Validate Product as Code project structure and files for specification compliance
category: project-task-management
argument-hint: "Specify validation rules or targets"
---

# Validate PAC Structure

Validate Product as Code project structure and files for specification compliance

## Instructions

1. **Initial Environment Check**
   - Verify `.pac/` directory exists
   - Check for PAC configuration file at `.pac/pac.config.yaml`
   - Parse arguments: `$ARGUMENTS`
   - Determine validation scope (single file, directory, or entire project)

2. **Configuration Validation**
   - Load and validate `.pac/pac.config.yaml`:
     - Check `apiVersion` format (must be semantic version)
     - Verify `kind` is "Configuration"
     - Validate required metadata fields
     - Check defaults section has valid values
   - Report any missing or invalid configuration

3. **Directory Structure Validation**
   - Verify required directories exist:
     - `.pac/epics/` - Epic definitions
     - `.pac/tickets/` - Ticket definitions
     - `.pac/templates/` - Templates (optional but recommended)
   - Check file permissions are correct
   - Ensure no orphaned files outside expected structure

4. **Epic File Validation**
   - For each file in `.pac/epics/`:
     - Verify YAML syntax is valid
     - Check `apiVersion: productascode.org/v0.1.0`
     - Verify `kind: Epic`
     - Validate required metadata fields:
       - `id` (must be unique)
       - `name` (non-empty string)
       - `created` (valid timestamp)
       - `owner` (non-empty string)
     - Validate spec section:
       - `description` exists
       - `success_criteria` has at least one item
       - `tickets` array is properly formatted
   - Track all epic IDs for cross-reference validation

5. **Ticket File Validation**
   - For each file in `.pac/tickets/`:
     - Verify YAML syntax is valid
     - Check `apiVersion: productascode.org/v0.1.0`
     - Verify `kind: Ticket`
     - Validate required metadata:
       - `id` (unique across all tickets)
       - `name` (non-empty string)
       - `epic` (must reference valid epic ID)
       - `created` (valid timestamp)
       - `assignee` (if specified)
     - Validate spec fields:
       - `type` is one of: feature, bug, task, spike
       - `status` is one of: backlog, in-progress, review, done, cancelled
       - `priority` is one of: low, medium, high, critical
       - `acceptance_criteria` has at least one item
       - `tasks` array is properly formatted

6. **Cross-Reference Validation**
   - Verify all ticket epic references point to existing epics
   - Check that epic ticket lists match actual ticket files
   - Validate ticket dependencies reference existing tickets
   - Ensure no circular dependencies exist
   - Verify unique IDs across all entities

7. **Data Integrity Checks**
   - Validate timestamp formats (ISO 8601)
   - Check that updated timestamps are >= created timestamps
   - Verify status transitions make sense (no done tickets in backlog epics)
   - Validate priority and effort estimates are consistent

8. **Template Validation**
   - If templates exist in `.pac/templates/`:
     - Verify they follow PAC specification
     - Check they include all required fields
     - Ensure placeholder values are clearly marked

9. **Generate Validation Report**
   - Create detailed report with:
     ```
     PAC Validation Report
     ====================
     
     Configuration: [VALID/INVALID]
     - Issues found: [count]
     
     Structure: [VALID/INVALID]
     - Epics found: [count]
     - Tickets found: [count]
     - Orphaned files: [count]
     
     Epic Validation:
     - Valid epics: [count]
     - Invalid epics: [list with reasons]
     
     Ticket Validation:
     - Valid tickets: [count]
     - Invalid tickets: [list with reasons]
     
     Cross-Reference Issues:
     - Missing epic references: [list]
     - Orphaned tickets: [list]
     - Invalid dependencies: [list]
     
     Recommendations:
     - [Specific fixes needed]
     ```

10. **Auto-Fix Options**
    - If `--fix` flag provided:
      - Add missing required fields with placeholder values
      - Fix formatting issues (indentation, quotes)
      - Update epic ticket lists to match actual tickets
      - Create backup before making changes
    - Show what would be fixed without `--fix` flag

11. **Git Integration**
    - If `--pre-commit` flag:
      - Only validate files staged for commit
      - Exit with appropriate code for git hook
      - Provide concise output suitable for CLI

12. **Summary and Exit Codes**
    - Exit code 0: All validations passed
    - Exit code 1: Validation errors found
    - Exit code 2: Configuration errors
    - Display summary:
      - Total files validated
      - Issues found and fixed (if applicable)
      - Next steps for remaining issues

## Arguments

- `--file <path>`: Validate specific file only
- `--epic <epic-id>`: Validate specific epic and its tickets
- `--fix`: Automatically fix common issues
- `--pre-commit`: Run in pre-commit mode (concise output)
- `--verbose`: Show detailed validation information
- `--quiet`: Only show errors, no success messages

## Example Usage

```
/project:pac-validate
/project:pac-validate --fix
/project:pac-validate --file .pac/epics/epic-auth.yaml
/project:pac-validate --epic epic-payment --verbose
/project:pac-validate --pre-commit
```