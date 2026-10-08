# Agent Distribution and Generic Approval Command Risk Index

This index provides command-level risk metadata for Agent distribution and generic approval examples. These commands are Transitional; the references record their migration contracts. The command implementation remains the source of truth for runtime admission.

| CLI command                                  | Transport                     | Risk            | Reference            |
| -------------------------------------------- | ----------------------------- | --------------- | -------------------- |
| `ae-cli agent bundle preview` | CLI-token-only versioned REST | read | agent-distribution.md |
| `ae-cli agent share recipients` | CLI-token-only versioned REST | read | agent-distribution.md |
| `ae-cli agent share create` | CLI-token-only versioned REST | write | agent-distribution.md |
| `ae-cli agent share list` | CLI-token-only versioned REST | read | agent-distribution.md |
| `ae-cli agent share accept` | CLI-token-only versioned REST | write | agent-distribution.md |
| `ae-cli agent share reject` | CLI-token-only versioned REST | write | agent-distribution.md |
| `ae-cli agent submission preview` | CLI-token-only versioned REST | read | agent-distribution.md |
| `ae-cli agent approval-type list`            | CLI-token-only versioned REST | read            | approval-type.md     |
| `ae-cli agent approval-type get`             | CLI-token-only versioned REST | read            | approval-type.md     |
| `ae-cli agent approval-request list`         | CLI-token-only versioned REST | read            | approval-request.md  |
| `ae-cli agent approval-request get`          | CLI-token-only versioned REST | read            | approval-request.md  |
| `ae-cli agent approval-request submit`       | CLI-token-only versioned REST | write           | approval-request.md  |
| `ae-cli agent approval-request cancel`       | CLI-token-only versioned REST | write           | approval-request.md  |
| `ae-cli agent approval-task list`            | CLI-token-only versioned REST | read            | approval-task.md     |
| `ae-cli agent approval-task get`             | CLI-token-only versioned REST | read            | approval-task.md     |
| `ae-cli agent approval-task approve`         | CLI-token-only versioned REST | write           | approval-task.md     |
| `ae-cli agent approval-task reject`          | CLI-token-only versioned REST | write           | approval-task.md     |
| `ae-cli agent approval-effect list`          | CLI-token-only versioned REST | read            | approval-effect.md   |
| `ae-cli agent approval-effect get`           | CLI-token-only versioned REST | read            | approval-effect.md   |
| `ae-cli agent approval-effect retry`         | CLI-token-only versioned REST | high-risk-write | approval-effect.md   |
