# Scene packs

The package contains one general fallback and twenty reviewed vertical scene packs under `../scenes/`. Select a domain scene independently from the operation mode.

- An explicit valid scene has priority. An unknown explicit scene is rejected rather than silently becoming general.
- Without an explicit scene, the package-local router uses reviewed NFKC-normalized trigger phrases and deterministic weights. A unique score of at least 0.8 routes to that vertical scene; a tie asks for clarification; no qualifying signal uses general.
- Connector state never influences the score or selected scene.
- Scene packs are implemented. Thirty-two package-local machine evaluators are active, while the human gate accepts only a trusted, externally signed receipt chain. A draft is not delivery-ready until the applicable gates run for that request.
- Optional adapters are registered, but a scene request still produces an intent with `executionAllowed=false`; the separate adapter dispatcher performs any authorized execution. Missing connectors preserve the route and local workflow.
- Artifact planning creates descriptors only. It does not claim that final files or delivery artifacts exist.
- General does not lower a high or restricted scene risk floor. Restricted investigation requires a scene-, gate-, owner-, scope-, evidence-, and time-bound trusted legal-review bundle before finished-draft closure.

Use `resources/scene-registry.json` as the index and verify each pack against its recorded SHA-256 before loading.
