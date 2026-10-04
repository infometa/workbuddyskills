---
name: ae-kb-discovery
description: >
  Discover which AE/TE/ThinkingEngine knowledge bases accessible to the current user are worth searching, and decide whether to search at all, through read-only operations. Use when the user explicitly asks to search knowledge bases, internal documentation, or company materials. Also use when a task requires internal facts or business context, including product design and rules, events, campaign or operations calendars, release and iteration records, workflows, policies, and terminology; use it as well when this context is needed to explain data analysis results, anomalies, or trends and form evidence-backed conclusions. Do not use if the user explicitly asks not to access knowledge bases. This skill covers discovery and candidate selection; run the actual `+index` / `+grep` / `+read` / `+ask` retrieval with the `ae-kb` skill.
---

# Knowledge Base Discovery

Treat knowledge bases as an optional source of internal facts and business context. Keep the user's original goal unchanged; knowledge base retrieval is a supporting workflow, not the task itself.

This skill decides **whether** to use a knowledge base and **which** knowledge base is worth searching. The retrieval procedure itself — inspecting the index, grep, reading sections, and optional LLM synthesis — lives in the `ae-kb` skill (`references/query-workflow.md`). Discover here, then hand off to `ae-kb` to execute.

## Decide Whether to Use This Skill

Use this skill when:

- The user explicitly asks to search a knowledge base, internal documentation, or company materials.
- The task requires organization-specific facts or context, such as product design and rules, events, campaign or operations calendars, release and iteration records, workflows, policies, or terminology.
- Internal context is needed to explain data analysis results, anomalies, or trends and form evidence-backed conclusions.
- The knowledge base context currently available does not cover the question, and discovering other accessible sources has clear value.

Do not use this skill when:

- The user explicitly asks not to use knowledge bases.
- The task only requires querying real-time state or performing an operation and does not need document context.
- General knowledge is sufficient for a reliable answer and internal evidence would not materially improve it.

## Discovery Workflow

### 1. Get the List of Accessible Knowledge Bases

First, get the lightweight list of knowledge bases accessible to the current user:

```bash
ae-cli kb +list
```

Use the exact `scope` and knowledge base name returned by the command, together with available metadata such as description, tags, language, and `bindings`. A binding identifies an associated context through `targetType`, `targetId`, and optional `targetName`. Do not guess a name, scope, or binding. Treat metadata returned by `+list` only as input for candidate selection, not as evidence from knowledge base content.

If `+list` is unavailable or fails, do not guess which knowledge bases exist. If the user explicitly requested a knowledge base search, explain that discovery cannot currently be completed. Otherwise, return to the original task and reassess the capabilities currently available.

### 2. Rank Candidate Knowledge Bases

Rank candidates in this order:

1. Prefer a knowledge base explicitly named by the user. Use the exact name and scope returned by `+list`, regardless of whether it has a matching binding.
2. Prefer candidates whose bindings exactly match the current session context. Match `targetType: project` against the current analysis project ID, `targetType: space` against the current community space ID, and `targetType: dwSpace` against the current digital workspace code.
3. For the remaining candidates, compare the user's request with the knowledge base name, description, and tags. Use language only as a preference between candidates with similar relevance; language alone does not establish relevance.

Compare `targetId` with the corresponding current ID or code first. Use `targetName` only as a secondary signal when an ID or code is unavailable; do not replace a conflicting ID match with a name match. A candidate with no bindings or no current-context match remains eligible for semantic ranking. A binding to another project or space lowers implicit priority but does not exclude the candidate, and an explicit user choice still takes precedence.

Select one preferred knowledge base by default. When several candidates are highly relevant, retain no more than three and try them one at a time in priority order. Do not read the indexes of all candidates in advance. A binding, name, description, tag, or language match only indicates that a knowledge base is worth searching; it does not prove a content match, grant access, or count as knowledge base evidence.

### 3. Hand Off to Retrieval

Once a preferred knowledge base is selected, hand off to the `ae-kb` skill and follow its `references/query-workflow.md` for the entire retrieval procedure — including when `+ask` is appropriate.

## Assess Coverage

- Full coverage: The page content read supports the key conclusions required for the information request or analysis.
- Partial coverage: The page content read provides only background, definitions, or partially relevant facts and cannot independently support the required conclusions.
- No coverage: No suitable candidate knowledge base exists, or `+grep` and `+read` return no content that can support the conclusions.

A candidate returned by `+list`, navigation returned by `+index`, a successful command, a tool call, or a metadata match does not count as a knowledge base hit. Only relevant page content that has actually been read can serve as knowledge base evidence.

## Use Knowledge Base Evidence in Analysis

When using internal context to explain data analysis results, anomalies, or trends:

1. First state what the analysis itself demonstrates, including the metric change, time range, affected entity, and magnitude.
2. Search using the affected entity, metric, time range, campaign or event name, product area, and release or version name.
3. Verify that the retrieved evidence:
   - Applies to the same entity, product area, or business scope.
   - Overlaps with the time range covered by the analysis.
   - Records an event, rule, release, or change that actually took effect.
   - Uses a version and effective date that remained valid during the analysis period.
4. Distinguish planned activities from completed events. A calendar or roadmap does not prove that an activity or release occurred unless the retrieved content confirms execution.
5. Combine analytical facts with retrieved internal evidence and state directly what the evidence supports. Do not list possible causes that lack evidence.
6. Use causal language such as "caused" or "led to" only when the available evidence establishes causality. Otherwise, say that the evidence supports a factor as a key explanation or that the factor is consistent with the observed change.
7. If the evidence is insufficient, state clearly that the cause cannot be determined from the available evidence. Do not fill evidence gaps with speculation.
8. When appropriate, organize the final answer in this order:
   - Conclusion.
   - Analytical evidence.
   - Knowledge base evidence and relevant page paths.
   - Necessary limitations of the evidence.

## Handle Partial or No Coverage

When knowledge base evidence provides only partial coverage, is entirely absent, or retrieval fails:

1. Stop repeating searches against the same candidate knowledge base.
2. If ranked candidates remain, switch to the next candidate. Search no more than three knowledge bases in one task.
3. When all candidates provide no coverage, return to the user's original request instead of remaining in the knowledge base retrieval subtask.
4. Reassess the capabilities currently available and choose the next path that best serves the original task. Do not hard-code a fixed fallback.
5. Retain verified background evidence when useful, but never attribute conclusions drawn from other sources to a knowledge base.
6. Do not report an unsuccessful knowledge base search unless the retrieval failure itself affects the user's decision.

Knowledge base information must not replace required business operations. If the original task also requires real-time data or an action, complete that part through the appropriate available capability.

## Safety Boundaries

- Limit knowledge base access to the read-only retrieval primitives (`+list`, `+index`, `+grep`, `+read`, and `+ask` when the question requires multi-page synthesis or multi-hop reasoning). Do not create, upload, compile, or delete knowledge bases.
- Respect existing scope, tenant, and membership permissions. Do not attempt to bypass an inaccessible knowledge base.
- Do not expose internal root paths, access tokens, or raw permission metadata.
- For protected knowledge bases, provide only summaries and synthesized conclusions allowed by the current permissions. Do not export complete source text or extensive verbatim excerpts.
