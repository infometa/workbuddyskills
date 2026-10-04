# Portable Batch Execution

Each product receives an isolated run directory and manifest. The host supplies evidence per row;
failed rows retain a reason and do not block completed rows.

After all rows settle, merge completed manifests with:

```bash
python3 scripts/finalize_batch.py --items /abs/batch-items.json --out-dir /abs/final
```

The result is `listing-batch-final.json`. Batch execution does not publish listings, modify a product
library, upload source files, or generate platform-specific HTML/XLSX.
