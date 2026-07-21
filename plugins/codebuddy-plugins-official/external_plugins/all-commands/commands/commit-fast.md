---
description: Automatically create and execute a git commit using the first suggested commit message
category: version-control-git
allowed-tools: Bash(git *)
---

# Create new fast commit task

This task uses the same logic as the commit task (.claude/commands/commit.md) but automatically selects the first suggested commit message without asking for confirmation.

- Generate 3 commit message suggestions following the same format as the commit task
- Automatically use the first suggestion without asking the user
- Immediately run `git commit -m` with the first message
- All other behaviors remain the same as the commit task (format, package names, staged files only)
- Do NOT add Claude co-authorship footer to commits