# Scene Routing

Choose the route from the user's current artifact and requested change, not from keywords alone.

| Route | Strong signals | First action | Minimum visible result |
| --- | --- | --- | --- |
| `material_activation` | Outlines, interview notes, transcripts, fragments, research notes, or a new long-document goal | Infer the best-fit document form and mark narrow assumptions | Manuscript judgment, structure, chapter tasks, and a substantive opening |
| `continuation_or_revision` | “Continue,” “rewrite,” “polish this section,” an explicit chapter, a quoted paragraph, or an existing draft with a local goal | Bind the request to an anchor and scope | Continued or revised prose, preserved context, and a short change explanation |
| `finished_draft_closure` | A complete or nearly complete draft, delivery request, consistency review, final polish, or export preparation | Diagnose the highest-impact delivery risk | Overall judgment, at least one concrete repair, remaining risks, and a delivery checklist |

## Routing procedure

1. Identify the current artifact: fragments, outline, partial draft, selected passage, or finished draft.
2. Identify the requested delta: create, continue, revise, diagnose, or finish.
3. Identify the target reader and intended use when supplied. Do not block if they can be stated as a provisional assumption.
4. Select one primary route. Treat another route as secondary only when it is necessary to complete the same user-visible artifact.
5. State the route in user language only when it helps orient the response; do not expose route IDs unless structured output is requested.

## Mixed requests

- If fragments and an old draft arrive together, use `material_activation` to rebuild the structure, then revise only one representative passage.
- If the user asks to continue and polish the same chapter, use `continuation_or_revision`; continue first, then perform a bounded polish on the new passage.
- If a finished draft has a single selected defect, use `continuation_or_revision` for the selected scope instead of reopening the entire manuscript.
- If the user requests a final review but supplies only part of the draft, review the supplied scope and label whole-document conclusions unavailable.

## Sparse or ambiguous input

Do not wait for perfect requirements. Choose the smallest useful route, list the assumption that affects the result most, and produce a reversible sample. Ask one question only when different answers would produce materially incompatible documents.

Never route based on the presence of connectors, network access, a host label, or a claimed external status. Those signals do not change the manuscript scene.
