# Long Manuscript Expert Embedded References

This package carries a functional subset of BookWriter capability references
plus debug contracts so the expert can remain useful even when a full local
BookWriter runtime is not installed in WorkBuddy.

Included reference layers:

- `core/`: intake, continuation, and runtime boundary notes
- `core/host-identity-contract.md`: the single source of truth for WorkBuddy /
  WorkBuddyAI visible host self-identification
- `core/network-evolution-boundary.md`: when network help is optional,
  required only for claim upgrades, or not needed at all
- `lifecycle/`: resume and progress-card behavior
- `workflows/`: material activation and post-draft finishing chains
- `workflows/intelligent-ops-habit-loop.md`: healthy continuation loop,
  service-readable value events, deidentified personalization, taskboards, and
  lebao unlock boundaries
- `quality/`: lightweight manuscript quality gate
- `playbooks/`: task-first scene playbooks for high-frequency longform flows
- `../templates/`: granular scenario dimensions, reusable modules, scene
  blueprints, representative scenarios, network-evolution policy, and
  intelligent-ops habit components
- `../contracts/`: operating contract, no-connector action contract, and
  service-side closure schema
- `../examples/`: resume progress-card, content-operations payload, and
  intelligent-ops habit loop examples
- `../fixtures/post-draft/`: before/after/layout samples for finishing-lane tests

These files are product-facing and debug-facing absorbed capability assets. They
are not local runtime cache, dependency trees, or generated service evidence.
