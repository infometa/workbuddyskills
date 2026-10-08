# analysis dashboard-definition import

Use when the user wants to validate or import dashboard definition JSON. Use `--validate-only true` for pre-checks such as name conflict, reference relation, and importable state.

Do not use a separate pre-check command; validation is part of this import command.

Command:

```bash
ae-cli analysis dashboard-definition import --project-id <project_id> --definition '{...}' [--validate-only true] [--dashboard-name-conflict-policy <policy>] [--space-dashboard-policy <policy>] [--payload '{...}']
```

Input sends `project_id`, `definition`, and optional validation/import policies and `payload`.

Output is the gateway envelope. `data` contains validation findings or import result.
