---
description: Test-driven development workflow with Red-Green-Refactor process and branch management
category: code-analysis-testing
allowed-tools: Read, Write, Edit, Bash(git *)
---

This outlines the development practices and principles we require you to follow. Don't start
working on features until asked, this document is intended to get you into the right state
of mind.

1. Make sure you are on the main branch before you start (unless instructed to start on a specific branch)
2. Understand the code that is there before you begin to change it.
3. Create a branch for the feature, bugfix, or requested refactor you've been asked to work on.
4. Employ test-driven development. Red-Green-Refactor process (outlined below)
5. When committing to git, omit the Claude footer from comments.
6. Wrap up each feature, bug, or requested refactor by pushing the branch to github and submitting a pull request.
7. If you've been asked to work on multiple features, bugs, and/or refactors you can then move on to the next one.

# High-level flow

## One vs many
Sometimes you will be given one task. Sometimes you will be given a task list.
The list might be provided as a git repo issue list, for example.

If you are given many at once, start with the first, and complete them one by one, creating a branch for each and a pull-request when finished.

## Keep notes
Create a markdown file under the notes/features/ folder for the feature. If you are creating a feature branch, use the same name.

Use this notes file to record answers to clarifying questions, and other important things as you work on the feature. This can be your long-term memory in case the session is interrupted and you need to come back to it later.

These are your notes, so feel free to add, modify, re-arrange, and delete content in the notes file.

You may, if you wish, add other notes that might be helpful to you or future developers, but more isn't always better. Be breif and helpful.

## Understand the feature
1. First read the README.md and any relevant docs it points to.
1. Ask additional clarifying questions (if there are any important ambiguities) to test your understanding first. For example,
if you were asked to write a tic-tac-toe app,