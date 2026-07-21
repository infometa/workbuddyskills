---
name: chatcut-plugin-basics
description: Base operating guide for any video editing or creation task handled through the ChatCut MCP in WorkBuddy, including project targeting, editable timeline work, editor handoff, generation confirmation, and verification.
---

# ChatCut Plugin Basics for WorkBuddy

## Runtime contract

ChatCut tools come from the OAuth-connected `chatcut` MCP server declared by this expert package. WorkBuddy may namespace the tools, so resolve them by their visible ChatCut tool name (`read_project`, `edit_item`, `submit_export`, and so on). Treat the current schema as authoritative and never guess a hidden parameter.

WorkBuddy owns OAuth. If the connection is missing, ask the user to complete the WorkBuddy connector card; never request or handle an OAuth token yourself.

## Project model

A ChatCut project contains a shared asset library and one or more editable timelines. Each timeline has canvas settings, tracks, timeline items, captions, effects, and generation/export state.

- Use `list_projects` for discovery only.
- Use `create_project` when the user wants a new project.
- Use `target_project` when the user chose an existing project.
- Use `read_project` before nontrivial work and after edits. Read IDs, tracks, fps, dimensions, assets, and ranges instead of inferring them.
- If the user may have edited manually, refresh project state before the next write.

## Editing contract

Keep the result editable in ChatCut. Use transcript/Script tools for speech-led edits and timeline tools for visual/audio composition. Do not replace a ChatCut workflow with a locally flattened render.

Align only on load-bearing creative choices. Mechanical, fully specified edits can run immediately. For any `submit_*` generation that may spend credits, describe the concrete generation and wait for explicit confirmation before submitting.

## Editor handoff

When a project tool returns `editorUrl`, `liveProject`, `browserHandoff`, or a preview resource:

1. Use the exact returned URL or preview result.
2. If WorkBuddy exposes an in-app browser or MCP preview, open it there.
3. Otherwise show the clean editor link to the user.
4. Never claim the visible editor matches the requested change until project readback or visual proof confirms it.

## Default delivery

An editing request normally ends with an editable timeline ready for review. Export only when the user asks to export, download, render, or finalize. Report ongoing upload, transcription, generation, and render states honestly.
