# 可恢复 Excel 导入

用户明确授权导入后，先完成应用决议与 `dataset detail`，确认目标为当前 User AK 可访问的已发布应用及唯一数据集。Excel 导入按实际 `source` 选路：

- `METADATA`：`lovrabet data import-excel`，使用服务端可恢复契约。
- `DB_TABLE`：按 [Excel 转换与分批新增指引](lovrabet-db-table-excel-import.md) 校验整份文件、唯一键和目标限制，生成 JSON 批次后使用 `lovrabet data batchCreate`。此命令不解析 Excel、不自动拆批，没有导入检查点或 `--resume`；结果不明时暂停并只读对账。
- 来源缺失、未知、元数据目标不匹配、权限不足或契约失败：停止并说明缺失事实，不猜测、不自动改用另一 API。

## METADATA 操作

映射文件是“Excel 表头 → 字段 code”的 JSON 对象，例如 `{"Name":"name","Amount":"amount"}`。仅映射已确认可写的业务字段，不输入主键、系统生成字段或不支持的字段类型。

```bash
lovrabet data import-excel --appcode <appCode> --code <datasetCode> --file ./records.xlsx --mapping ./mapping.json --dry-run
lovrabet data import-excel --appcode <appCode> --code <datasetCode> --file ./records.xlsx --mapping ./mapping.json
lovrabet data import-excel --appcode <appCode> --code <datasetCode> --file ./records.xlsx --mapping ./mapping.json --resume
```

`--dry-run` 读取元数据和导入契约，完成本地文件、映射与单元格校验，输出有效/无效行、空行、错误、警告及预计批次数；不写业务记录、检查点或报告。修正无效单元格后才能执行。成功返回也会逐行核对各字段，不能只以 HTTP 成功认定入库完成。

参数：`--sheet` 为工作表名或从 1 开始的序号（默认首表）；`--header-row` 默认 1；`--batch-size` 为 1–500（默认 500），同时服从服务端每请求字节限制；`--checkpoint` 和 `--report` 指定私有输出路径（默认 XLSX 路径加 `.import-checkpoint.json` 与 `.import-report.json`）。源文件、映射和两个输出文件必须不同，输出不得使用符号链接。

限制：仅 XLSX，文件不超过 20 MB，展开不超过 100 MB，最多 100,000 行、256 列、单元格 64 KB；公式必须有缓存结果。日期、数字、布尔值按已确认的字段类型校验，未支持的复杂类型停止。

## 中断与恢复

保留原文件、映射、工作表、批次参数、目标应用/数据集、连接地址、AK 身份和检查点。使用原命令加 `--resume`，先回查原检查点中的标识和数据，再继续未完成部分；不要删除检查点、换 taskId/标记、改目标或盲目重发来绕过未知结果。

报告包含 `sourceRows`、`succeeded`、`unknown`、`conflicts`、`notAttempted`、批次耗时和输出路径。unknown 表示需恢复核对；内容冲突、已导入行不可见或契约/身份漂移时停止，不自动修复或换标记。重复恢复已完成导入会重新核对字段且不新增记录。

检查点与报告包含业务数据及恢复标识，保留私有权限，不外发真实 AK 或敏感业务值。该能力不放宽应用可访问性、创建权限或读取权限；非 Excel `batchCreate` 保持原有调用方式。


# Native Excel image import into UPLOAD fields

For `METADATA` datasets, `lovrabet data import-excel` reads embedded PNG, JPEG and GIF pictures from floating DrawingML anchors, Microsoft Excel in-cell rich data, and standalone WPS `DISPIMG` formulas (including `_xlfn.` / `@` forms). The import stores the original embedded image bytes. Excel crop, rotation and filter effects are not rendered into the result. EXIF is not mapped to business fields; metadata already present in the original bytes is retained. Map the picture column header to the confirmed `UPLOAD` field code. Its business value is an ordered `{fileName,filePath}` array; for example, `{"UPLOAD_1":[{"fileName":"photo.png","filePath":"dataset-import/<scope>/<digest>.png"}]}`. Use the durable file path returned by upload. Digest, MIME type and byte size remain upload verification/checkpoint metadata. Pictures in one cell preserve their order; repeated identical bytes upload once per import. Picture-only rows are included. Hidden rows are included with a warning.

Existing `IMAGE` fields keep their legacy `{name,type,key,size}` value format and checkpoint compatibility. Do not change a dataset's field type or translate existing persisted rows automatically. The field protocol is bound to the source/schema/checkpoint; switching an original import from IMAGE to UPLOAD is not a resume operation.

Start with the existing import command and `--dry-run`. Dry-run validates the local workbook, mapping, image bytes, server capability and request size, then reports image occurrences, unique images and unique bytes. It does not upload images, create records, or write checkpoints/reports. A missing server image capability blocks an import containing pictures; scalar-only imports continue to use the existing import contract.

Inspect all validation errors before running the confirmed write. Each image must be no larger than 10 MiB and no larger than 40 million pixels. GIF cumulative frame canvas pixels must also fit that pixel limit. Unique images total at most 50 MiB per import, with at most 10,000 occurrences. Only the selected sheet and mapped UPLOAD or legacy IMAGE columns contribute uploads. Mixed scalar content and pictures in one mapped image cell, missing images, unsupported formulas, external images, ambiguous relationships, pictures spanning multiple business rows, and unmappable absolute anchors stop validation. UPLOAD support here is for embedded images, not arbitrary embedded documents or JSON/URL text in cells.

Image imports use a v3 main checkpoint at `--checkpoint` and a row checkpoint at `<checkpoint>.rows.json`. Keep both files together, plus the source workbook and mapping. The main checkpoint binds the actor, application, dataset, runtime domain, source, mapping, schema, image descriptors, batch settings and row strategy. Do not edit or replace checkpoint files. Keep the result report for reconciliation.

After an interruption, run the exact command with `--resume`. Resume queries the original image identity before deciding whether a pending upload may continue, then resumes the original row IDs/task markers. A completed image that becomes missing, corrupt or changed stops recovery; it is not automatically re-uploaded. Completed resumes re-read images and records without uploading or creating duplicates. If a row phase was already started but its row checkpoint is missing, stop and reconcile the original outcome before proceeding.

UPLOAD values are compared strictly: a changed fileName, filePath, array order or unexpected property stops recovery. Legacy IMAGE comparison ignores known empty server defaults for creator fields and geolocation, while preserving meaningful or unknown metadata differences. For an auto-ID image import previously marked as conflicted, `--resume` may recover only when the original generated row IDs are recorded and fresh readback confirms every original image, row ID and mapped field. All batches are checked before any remaining rows are written. Missing rows, different content, marker collisions, or conflicts without recorded IDs still stop recovery. Keep the original checkpoints; never clear a conflict by editing them or starting the same import with new markers. Scalar-only and fixed-ID conflict handling is unchanged.

WebP (including static and animated), SVG/EMF, remote URLs, arbitrary image formulas, shared image formulas, ATTACHMENT fields, and native DB_TABLE image import are unsupported. Animated PNG is also rejected. `DB_TABLE` continues to use its separately documented `batchCreate` workflow, without import checkpoints; do not automatically switch an image import to that route. Business fields never receive base64 data, formulas or temporary signed URLs.
