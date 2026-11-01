---
name: pixso-mcp
description: Use Pixso MCP when users ask to inspect, generate, edit, validate, or convert Pixso designs; manage components, styles, variables, comments, and design assets; perform design-to-code or code-to-design work; or retrieve design guidelines.
description_zh: 使用 Pixso MCP 读取、生成、编辑和校验设计稿，管理组件、样式与变量，执行设计与代码双向转换，并调用设计规范。
description_en: Use Pixso MCP to inspect, generate, edit, and validate designs; manage components, styles, and variables; convert between code and design; and retrieve design guidelines.
version: 1.0.0
author: Pixso
---

# Pixso MCP

Use the remote Pixso MCP server to work with Pixso files. Prefer the smallest tool and scope that completes the request.

## Before calling tools

1. Ensure the user has completed Pixso OAuth authorization.
2. Require a Pixso layer URL containing `item-id`, a node ID, or a clearly identified current target. Do not treat a file share URL or `page-id` as a node target.
3. Confirm that the account can view the file. Editing tools additionally require edit permission. Some D2C capabilities require an eligible enterprise seat and an enterprise-space file.
4. For ambiguous requests, begin with read-only inspection and identify the intended file, page, frame, or node before modifying anything.

## Select tools

- For design-to-code, use `design_to_code`. Preserve all supplied node IDs and honor the requested framework.
- For node structure or precise design data, use `get_node_dsl`; start with the compact response and fetch more only as needed.
- For code or web artifacts converted into editable Pixso content, use `code_to_design`.
- For canvas discovery, use `fetch_context`, `get_top_level_frames`, or `query_nodes`.
- For components, styles, variables, and comments, use the matching `read_*` tool.
- For layout and visual verification, use `check_layout` and `take_screenshot`.
- For design guidance, use `load_guidelines`, `list_style_tags`, and `get_style_guide`.
- For detailed routing, read [references/tools.md](references/tools.md).

## Modification safety

Treat `write_styles`, `write_variables`, `apply_design`, `eval_script`, `replace_props`, and any `code_to_design` operation that writes into a file as modifying operations.

Before a modifying operation:

1. State the target file and node scope.
2. Summarize the intended changes and whether they create, update, move, replace, or delete content.
3. Obtain explicit user confirmation when the request does not already clearly authorize those exact changes.
4. Never broaden the requested scope. Preserve unrelated layers, components, styles, and variables.

Always obtain explicit confirmation immediately before deletion, bulk replacement, destructive reorganization, or executing an `eval_script` that writes to the file. Mention that a failed script may leave partial changes.

## Workflow

1. Resolve the target from a Pixso layer URL, node ID, or current context.
2. Inspect only the information needed for the task.
3. Explain any permission, seat, or authentication blocker without exposing credentials.
4. For writes, apply the modification-safety rules and use the narrowest target scope.
5. After changes, re-read affected nodes and use `take_screenshot` or `check_layout` when visual or layout correctness matters.
6. Report what was read or changed, the exact scope, verification performed, and any unresolved differences.

## Failure handling

- If authentication is missing or expired, ask the user to reconnect Pixso through OAuth.
- If the target URL lacks `item-id`, ask for a node-specific link or approval to use the current selection.
- If access is denied, distinguish view permission, edit permission, seat eligibility, and enterprise-space restrictions.
- If a write partially succeeds, stop, report the confirmed state, and ask before attempting recovery.
- Do not invent node IDs, file contents, component definitions, styles, variables, or tool results.
