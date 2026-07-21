---
description: Systematic workflow for fixing bugs including issue creation, branch management, and PR submission
category: version-control-git
argument-hint: <bug_description>
allowed-tools: Bash(git *), Bash(gh *)
---

Understand the bug: $ARGUMENTS

Before Starting:
- GITHUB: create an issue with a short descriptive title.
- GIT: checkout a branch and switch to it.

Fix the Bug

On Completion:
- GIT: commit with a descriptive message.
- GIT: push the branch to the remote repository.
- GITHUB: create a PR and link the issue.