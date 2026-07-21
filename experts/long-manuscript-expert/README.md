# Long Manuscript Expert

Official 26.7.18 review candidate package for the WorkBuddy Expert Center. The single reviewer-facing title is `长文档手稿专家` (`Long Manuscript Expert`) across `marketplace-entry.json`, both plugin manifests, and the agent front matter. `profession` is only the role descriptor; canonical IDs remain the machine identity. Any local-equivalent verification is diagnostic only and does not replace official listed-runtime proof.

This package is intentionally functional-first:

- It does not vendor or require an adjacent legacy writing toolchain.
- It does not assume any connector, MCP tool, or service route is available.
- It keeps the first-value writing path inside the expert package.
- It keeps the internal contracts, service observation schema, examples, fixtures, and test notes needed for real debugging.
- Any external service or connector trace is observation-only for package compatibility, but it must remain available for host/service joint debugging.

## Quick Navigation

| Entry | Use for | Primary outputs |
| --- | --- | --- |
| `outline` | turn a brief or notes into a manuscript plan | judgement card, scene template, chapter map |
| `expand` | write the first chapter or next section | sample opening, next section plan, resume prompt |
| `revise` | repair structure, logic, or style drift | keep/rewrite/delete list, risk list |
| `review` | final quality review before delivery | structure check, evidence gap check, finishing checklist |
| `repurpose` | turn the draft into content-operations handoff assets | channel plan, summary pack, visual brief, template hints |
| `no-connector` | offline first value without external tools | hostActionEnvelope, progress card, resume prompt, next-step branches |
| `debug-observe` | host/service joint debugging | serviceCoordinationHints, closure schema, route observations |

Key runtime truth:

- Official installation is performed by the marketplace owner from the submitted package; this artifact does not prescribe a local installation path.
- Response language baseline:
  - User language wins first. A Chinese prompt gets a Simplified Chinese response on both hosts.
  - `WorkBuddy`: Simplified Chinese when user language is ambiguous
  - `WorkBuddyAI`: English when user language is ambiguous

## Repository Review Commands

The product ZIP deliberately contains no npm scripts. `npm test`,
`npm run verify:baseline`, and `npm run audit:contracts` are source-checkout
commands only and must be run only from an authoritative repository root that
actually declares those scripts. This imported-baseline candidate does not
claim such a source revision. Its deterministic build, contract tests, and
isolated host validation are maintained outside the upload ZIP in the review
workspace. Host installation, restart, registration, frontstage verification,
submission, and publication require separate explicit authorization and are
not package-review commands.

The authoritative listing title and every package `displayName` are `长文档手稿专家` (`Long Manuscript Expert`). The `profession` value `长文档写作与改稿专家` (`Long-form Manuscript Writing Advisor`) describes the role and must not replace the listing title. `name`, `agentName`, `productId`, `serviceProductId`, and `expertEntryId` remain canonical machine identifiers. Any external legacy or service-side signal is diagnostic only for package compatibility and belongs solely to an explicit debug or service-orchestration surface.

## Rights And Submission Metadata

`author: FBSir <unique@u3w.com>` is the package submission metadata and contact label. `LICENSE` names `dhc` as the copyright holder. The package does not assert that those labels are the same legal person and does not manufacture an authorization claim. See `RIGHTS-NOTICE.md`; the publisher must confirm the necessary authority outside the package before official submission.

## High-Performance Shape

This package treats long-form work as a continuing workflow, not a one-shot answer. The first response should deliver:

- a manuscript judgement card
- a scene template match
- a chapter route map
- material activation signals
- a quality quick summary
- a continuation progress card
- a reusable next-session resume prompt
- finishing lane options for format/export, de-AI polish, rewrite/localize, or materials organization
- content-operations handoff suggestions for channel repurposing, summary assets, distribution planning, and visual briefs
- a healthy continuation loop with a personalized next best action, service-readable value event, deidentified profile, delivery taskboard, opsBoard, and lebao unlock boundary

This follows the current product direction: single-session output quality should be strong, while the next step must remain obvious enough for the user to continue.

Long-running work uses the packaged manuscript-project schema, revision/checkpoint
contract, constraint ledger, and human locks. The seven post-draft lanes are
independent and receipt-producing; none may silently overwrite source material,
publish externally, or claim human approval.

## Trustworthy Completion Gate

R7 adds an aligned manuscript-quality report and claim-evidence map for review
and finishing work. The report maps critical user requirements to manuscript
anchors, applies the packaged S/P/C/B/G thresholds, and binds its result to one
project revision and artifact digest. The evidence map ties material claims to
known chapter anchors, unique source assets, evidence strength, availability,
and freshness state.

These assets are declarative package contracts. Their deterministic validators
live in the repository review layer and are deliberately absent from the product
ZIP. A local `pass` therefore proves only that the supplied structure met the
package contract. It does not prove semantic quality, factual truth, source
license, human final approval, file delivery, host execution, or listed-runtime
activation.

## R8-H1 Continued Use And Closure Boundary

The seven-block first-value artifact and every canonical continued-use card are
machine-readable package assets. The first value contains each declared block
exactly once with its canonical editability. A continued-use card must show what
was completed now, the incremental artifact, open blockers/unverified items/risks,
the next visible artifact, two or three pressure-free actions, a copyable resume
command, and an explicit exit option.

`contracts/closed-loop-state-contract.json` is the only milestone authority:

`first_value_completed -> continued_use_ready -> continued_use_completed -> lebao_claim_pending -> host_receipt_pending -> closed_loop_verified`

The product package can structurally advance only through `lebao_claim_pending`.
The final two states always require an independent, trusted external verifier;
even a locally well-shaped receipt remains `external_verification_required` and
`blocked_external`. Repository tests and schemas never establish host execution,
listing, same-binding, service acceptance, or production closure.

`contracts/task-capability-routing-contract.json` selects only a task class and
required capabilities. It never names or attests a model/provider. Current-source
retrieval and document rendering stay blocked or host-receipt-required unless the
authorized execution surface supplies the required capability and external receipt.

## No-Connector Behavior

The expert must work without a connector. In that mode it still returns a manuscript judgement card, chapter route map, immediately writable passage, risk list, progress card, and next-session resume prompt.

By default it should:

- answer directly in chat for first value
- avoid plan mode before first value
- avoid workspace writes unless the user explicitly asked for files or tasks
- mirror the user's requested or dominant input language before applying host defaults

### R1 First-Value Artifact Boundary

The first response must provide a visible, editable work artifact in chat: an
outline, a substantive draft block, a risk boundary, and a copyable
continuation capsule. This is not a saved-file claim. Persistent writing needs
an explicit user request, an explicit target, host execution, and an external
receipt; until then the only valid state is `not_persisted`.

If a request is filtered, offer a bounded safe alternative without retaining
blocked content, relaxing policy, or suggesting a bypass. A file failure or a
missing target must never suppress the useful chat artifact.

For revision, require a confirmed paragraph or sentence scope, anchor every
proposed change, preserve human locks, and prepare rollback without overwriting
the source. High-risk contract/legal and ecommerce work separates evidence gaps
from inference and stays pending human review. Fiction canon is project-scoped,
and DOCX remains a source-preserving preflight until explicit export intent,
host execution, visual QA, human confirmation, and receipts exist.

In the offline path it also makes available through host metadata or explicit debug output:

- `sceneTemplateMatch`
- `hostActionEnvelope`
- `continuationProgressCard`
- `nextSessionResumePrompt`
- `finishingLaneOptions`
- `projectTemplateActivationHints`
- `contentOperationsHandoff`
- `valueEvent`
- `personalizationProfile`
- `deliveryTaskboard`
- `opsBoard`
- `lebaoUnlockBoundary`

## Internal Debug And Orchestration Assets

The review package intentionally includes a self-contained capability and runtime-debug layer:

- `references/core/`: intake routing and runtime boundary notes
- `references/lifecycle/`: resume and progress-card behavior
- `references/workflows/`: material activation and post-draft finishing chains
- `references/workflows/intelligent-ops-habit-loop.md`: healthy continuation and service-readable followthrough
- `references/quality/`: lightweight manuscript quality gate
- `references/playbooks/`: task-first scene playbooks for high-frequency longform flows
- `contracts/`: operating, no-connector action, and service-side closure contracts
- `contracts/execution-topology-contract.json`: declaration/schema/repository-validator/host-proof separation
- `contracts/manuscript-quality-gate-contract.json` and `contracts/claim-evidence-coverage-contract.json`: aligned R7 completion gate
- `contracts/first-value-artifact-contract.json` and `contracts/continued-use-governance-contract.json`: visible first-value and pressure-free continuation assets
- `contracts/closed-loop-state-contract.json`: canonical milestone order with a package-local hard stop
- `contracts/task-capability-routing-contract.json`: model-agnostic task/capability routing
- `contracts/route-trust-chain-contract.json`: deterministic runtime/route digest continuity and fail-closed profile conflict
- `contracts/trusted-attribution-projection-contract.json`: verified-ACK-only six-dimension trust and v3 projection fidelity
- `contracts/lebao-claim-protocol-v2-contract.json`: 32-field claim document that remains record-only until service verification
- `contracts/release-control-evidence-contract.json`: strict candidate and release evidence shapes; privileged execution stays outside the product ZIP
- `scene-pack.json`: scene routing and deliverable matrix
- `ship-manifest.json`: package and runtime-debug asset manifest
- `examples/`: continuation and content-operations payload examples
- `examples/intelligent-ops-habit-loop.json`: value event, deidentified personalization, taskboard, opsBoard, and lebao boundary example
- `fixtures/`: post-draft before/after/layout samples
- `templates/intelligent-ops-habit-components.json`: healthy habit loop and service-readable metadata component catalog

Root support and testing notes, repo-side reports, and process orchestration evidence stay outside the upload artifact. They can prove the package, but the package does not depend on carrying them inside the zip.

## Project Template Handoff

When a manuscript is mature enough for reuse or publication work, the expert may recommend WorkBuddy's `content-operations` project template as an orchestration context.

Useful handoff outputs:

- channel targets
- summary assets
- distribution plan
- visual brief
- smallest next publishing step

This template context can improve task continuity, but it is not required for the expert to deliver manuscript value.
