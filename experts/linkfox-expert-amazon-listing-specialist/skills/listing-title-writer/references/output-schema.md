# Portable Title Output

Single-row outputs contain `row_id`, `title`, `item_highlights`, `used_keywords`, `status`, `warnings`
and optional `change_reason`. Batch outputs contain a `rows` array and aggregate counts.

The schema is platform-neutral JSON. It has no UI component metadata, upload identifier, product-library
identifier or XLSX artifact path.
