# Portable Listing Core Execution Contract

## Inputs

The host supplies product facts, optional current/reference listing copy, optional keyword evidence,
buyer questions, marketplace and language. An ASIN is an identifier only; Core never fetches it.

Facts must identify whether they describe the target product or a reference product. Reference facts
may guide structure and terminology but may not be asserted as target-product facts.

## Pipeline

```bash
python3 scripts/run_pipeline.py plan --run-dir /abs/run --mode create
python3 scripts/run_pipeline.py ingest --run-dir /abs/run --product-detail /abs/provided-evidence.json
python3 scripts/run_pipeline.py prepare-write --run-dir /abs/run --insight-bundle /abs/insight.json
python3 scripts/run_pipeline.py finish --run-dir /abs/run
```

`benchmark` and `rewrite` use the same local pipeline. The host must place any source or reference
listing in the provided evidence before `ingest`.

## Outputs

- `03-write/listing-final.json`: canonical Listing and score data
- `03-write/listing-final.md`: human-readable copy
- `03-write/ai-readiness.json`: answerability checks
- `03-write/check-report.json`: deterministic validation
- `run-manifest.json`: stage status and artifact paths

No step authorizes a store, publishes a listing, accesses a product library, uploads files, or renders
platform-specific HTML/XLSX. The host owns any later integration.

## Failure behavior

Missing facts are reported as gaps. Validation failures stop finalization. Network access, API keys,
platform session directories and product-center identifiers are never required.
