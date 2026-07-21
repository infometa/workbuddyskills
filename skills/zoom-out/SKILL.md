---
name: zoom-out
description: Tell the agent to zoom out and give broader context or a higher-level perspective on unfamiliar code. Use when you're unfamiliar with a section of code, need to understand how it fits into the bigger picture, or want a map of relevant modules and callers.
description_zh: "提升抽象层次，快速获取陌生代码模块的全局地图与调用关系"
description_en: "Zoom out for a higher-level map of modules, callers, and how unfamiliar code fits the big picture"
version: 1.0.0
homepage: https://github.com/mattpocock/skills
allowed-tools: Read,Grep
---

# Zoom Out

## What to do

I don't know this area of code well. Go up a layer of abstraction and give me a map of all the relevant modules and callers.

**Starting point**: begin from the file or symbol currently in context (the one being discussed or most recently mentioned). If no specific entry point is given, start from the project root and identify the top-level modules.

**Output format** — present the map as:
1. A brief description of what this area of the codebase does (1–3 sentences)
2. A module list: each module with its responsibility and key public interface (file path, exported functions/classes)
3. A caller/dependency map: who calls what — show the direction of dependencies

Use the project's domain glossary vocabulary if a `CONTEXT.md` or `glossary.md` exists (check with Read). If no glossary exists, use the names found in the code itself.

**Depth**: go up 1–2 abstraction levels from the starting point. Don't descend into implementation details — the goal is orientation, not exhaustive documentation.

## When to use

Invoke this skill when:
- You're dropped into an unfamiliar part of the codebase and need orientation
- You want to understand how a specific function or file fits into the broader system
- You need a high-level view before diving deeper (e.g. before running `diagnose` or `tdd`)

## Tools

- **Read**: Read source files to understand module structure, exports, and interfaces
- **Grep**: Search for references, callers, and usages across the codebase to trace dependencies
