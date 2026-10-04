# Portable Output Schema

## Single Listing

`listing-final.json` is the canonical artifact. It contains product context, Listing fields, research
summary, deterministic checks and an optional canonical `scorePanel`. `listing-final.md` is a readable
projection of the same copy. `ai-readiness.json` records buyer-question coverage.

Paths in `run-manifest.json` are ordinary local paths selected by the host. No filename, transport
prefix, cloud URL or UI component is required by this package.

## Batch

`listing-batch-final.json` contains `kind=listingBatchFinal`, batch statistics and the canonical bundles
from completed rows. Failed rows include a stable row identifier and reason.

## Interoperability

External harnesses may transform these JSON/Markdown artifacts after Core completes. Those adapters
are outside this expert: it does not generate HTML/XLSX, upload artifacts, publish to Amazon, or write
to a platform product library.
