# Local analysis

Dimension / dictionary data (a stable-entity lookup with a join key) is not local-analysis material — it routes to ae-metadata as a dimension table. See [ue-routing.md](ue-routing.md) and [dimension-routing.md](dimension-routing.md).

Keep the source on the local machine. Generated scripts and reports belong under `.ae-cli/data-integration/runs/<run-id>/` with restrictive permissions.
Set the directory to `0700` and generated scripts/reports to `0600`.

## Default report when no question is supplied

Include only analyses supported by the fields:

- Schema, row count, missingness, parse failures, and duplicate rows/keys.
- Numeric and categorical distributions without dumping raw values.
- Time coverage, frequency, gaps, and trends when a reliable time field exists.
- Outliers with a declared method and threshold.
- Correlations or segment comparisons only when sample size and field semantics support them.

## Targeted report

Restate the user's question, identify the relevant population/time/metrics, run reproducible calculations, then report:

1. Observed facts.
2. Inferences and alternative explanations.
3. Confidence.
4. Data limitations and excluded rows.

Do not claim causality from correlation. Do not hide missingness or filtering. Charts must have titles, units, time ranges, and definitions for derived measures.

`analyze.mjs` must accept the source path and selected data-set as parameters or documented constants, avoid network calls, and write `analysis-report.md`. It must never embed APPID, receiver, or tokens.
