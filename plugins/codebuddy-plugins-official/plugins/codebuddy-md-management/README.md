# CODEBUDDY.md Management Plugin

Tools to maintain and improve CODEBUDDY.md files - audit quality, capture session learnings, and keep project memory current.

## What It Does

Two complementary tools for different purposes:

| | codebuddy-md-improver (skill) | /revise-codebuddy-md (command) |
|---|---|---|
| **Purpose** | Keep CODEBUDDY.md aligned with codebase | Capture session learnings |
| **Triggered by** | Codebase changes | End of session |
| **Use when** | Periodic maintenance | Session revealed missing context |

## Usage

### Skill: codebuddy-md-improver

Audits CODEBUDDY.md files against current codebase state:

```
"audit my CODEBUDDY.md files"
"check if my CODEBUDDY.md is up to date"
```

<img src="codebuddy-md-improver-example.png" alt="CODEBUDDY.md improver showing quality scores and recommended updates" width="600">

### Command: /revise-codebuddy-md

Captures learnings from the current session:

```
/revise-codebuddy-md
```

<img src="revise-codebuddy-md-example.png" alt="Revise command capturing session learnings into CODEBUDDY.md" width="600">

## Author

Isabella He (isabella@anthropic.com)
