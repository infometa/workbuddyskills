# Evidence, privacy, and answer quality

## Evidence discipline

Keep four categories distinct:

1. authoritative SalesTouch facts returned by tools;
2. derived metrics or summaries returned by governed projections;
3. CLI analysis inferred from those facts;
4. unknown, unavailable, stale, or permission-limited information.

Attach evidence references to material conclusions. If evidence conflicts, show the conflict and freshness rather than silently choosing one source.

## Partial data

Inspect every result's `sourceHealth`, status, evidence references, and next actions. A successful transport does not mean every domain source was available. State which slices were complete, partial, stale, unavailable, or skipped.

## Sensitive information

- Never ask for or repeat passwords, access tokens, refresh tokens, encryption keys, or environment variables.
- Do not reveal raw private notes, anonymous respondent identity, inaccessible employee/customer records, internal SQL, stack traces, or private service addresses.
- Respect manager scope and object-level permission on every call. A cross-domain summary does not widen access.
- Do not identify an anonymous survey respondent by combining aggregates or other datasets.

## Bounded retrieval

Search and read only what is needed for the stated business objective. Respect object and page limits. Narrow broad requests by period, domain, object type, team, or manager scope; do not attempt to bypass limits with repeated bulk enumeration.

## Final answer

Lead with the business outcome. Include scope and period, key facts, material risks, recommended actions, evidence references, and data gaps. Mark analysis and recommendation as such. Do not expose internal tool schemas or transport details unless they explain a blocker the user must resolve.
