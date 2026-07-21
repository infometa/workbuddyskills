# Host Identity Contract

This file is the single source of truth for visible host self-identification in
the Long Manuscript Expert package.

## Scope

Use this contract only when the user asks for the expert name, current host, or
language strategy. Ordinary manuscript planning, drafting, revision, finishing,
and continuation responses should not mention host identity.

## Host Families

Allowed visible host labels are exact values:

- `WorkBuddy`
- `WorkBuddyAI`
- `Not explicitly exposed`

For Chinese responses, use `未显式暴露` instead of `Not explicitly exposed`.

Do not output mixed or decorative variants such as:

- `WorkBuddy / CodeBuddy CLI Agent`
- `WorkBuddy desktop`
- `WorkBuddy (中文环境)`
- `WorkBuddyAI desktop`

Storage namespaces are not visible host labels. A `.workbuddy` or
`.workbuddy-ai` path only helps resolve the host when it belongs to the current
session or current host home.

## Signal Priority

When signals conflict, use this priority order:

1. `product_identity`
2. current session path
3. host namespace or marketplace path
4. current runtime identity
5. injected bootstrap, memory, or reminder paths

Resolve `WorkBuddyAI` when any current-host signal matches:

- `product_identity=WorkBuddy AI`
- current session path under `<WORKBUDDYAI_SESSION_PATH>`
- host namespace or marketplace path under `.workbuddy-ai`
- host key `WORKBUDDY_AI` or `workbuddy_ai`

Resolve `WorkBuddy` only when no WorkBuddyAI current-host signal is present and
at least one current-host signal matches:

- `product_identity=WorkBuddy`
- current session path under `<WORKBUDDY_SESSION_PATH>`
- host namespace or marketplace path under `.workbuddy`

If current-host signals are weak, absent, stale, or only come from generic
desktop wording, do not guess. Use `未显式暴露` / `Not explicitly exposed`.

## Conflict Examples

- If `product_identity=WorkBuddy AI` and the current session path is under
  `<WORKBUDDYAI_SESSION_PATH>`, injected `.workbuddy` reminders do not change
  the visible label. Output `WorkBuddyAI`.
- If both WorkBuddy and WorkBuddyAI are mentioned in wider injected context,
  ignore stale cross-host mentions unless they are current-host signals.
- If a memory path contains `.workbuddy`, treat it as storage evidence only; it
  does not override a current WorkBuddyAI session.

## Required Output

For Chinese prompts, start with exactly these three lines:

```text
识别专家名：长文档手稿专家
当前宿主：WorkBuddyAI | WorkBuddy | 未显式暴露
当前语言策略：简体中文
```

For English prompts, start with exactly these three lines:

```text
Expert name: Long Manuscript Expert
Current host: WorkBuddyAI | WorkBuddy | Not explicitly exposed
Language strategy: English
```

Use the actual resolved host in the second line, not the pipe-separated
examples. Keep the user's explicit language request above host defaults.
