---
description: Load project context by reading README.md and exploring relevant project files
category: context-loading-priming
allowed-tools: Read, Bash(git *)
---

Read README.md, THEN run `git ls-files | grep -v -f (sed 's|^|^|; s|$|/|' .cursorignore | psub)` to understand the context of the project