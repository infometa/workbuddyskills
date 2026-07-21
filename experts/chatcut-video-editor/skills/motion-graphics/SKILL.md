---
name: motion-graphics
description: Add editable Motion Graphics to a ChatCut timeline in WorkBuddy by reusing library templates or generating a new motion graphic through ChatCut.
user-invocable: true
---

# Motion Graphics

## Prefer reusable templates

Use `browse_library` with the `motion-graphics` category first when a suitable reusable title, lower third, quote card, label, or data graphic may already exist. Inspect the chosen item, then place its returned library asset ID with `edit_item`.

## Generate a new Motion Graphic

When no library item fits:

1. Read the timeline dimensions, fps, target placement, nearby visual language, captions, and subject-safe area.
2. Write a concrete brief covering purpose, text, hierarchy, animation, duration, aspect ratio, palette, and avoidances.
3. Tell the user what will be generated and that it may consume ChatCut credits; wait for explicit confirmation.
4. Call `submit_motion_graphic` using the current tool schema.
5. Track the generation with `track_progress`, then place the completed asset with `edit_item`.
6. Verify the item range and inspect a composed frame/preview when available.

Keep text readable, motion purposeful, and overlays clear of faces and captions. Match the project rather than showing off an unrelated style. Do not use local HTML/JSX files or invent a direct-authoring tool that is not present on the WorkBuddy MCP surface.
