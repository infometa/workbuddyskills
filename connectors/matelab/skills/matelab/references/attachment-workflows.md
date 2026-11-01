# Matelab MCP Attachment Workflows

## Upload a new local file

1. Select a notebook ref whose capabilities include `update_record`.
2. Determine the plain filename and exact byte size.
3. Call `prepare_upload(notebook_ref, filename, size)`.
4. Preserve the returned `attachment_ref` unchanged.
5. Outside MCP, send raw bytes to `upload.url` using `upload.method` and every returned header:

   ```bash
   curl --fail-with-body --request PUT \
     --header "Authorization: <upload.headers.Authorization>" \
     --header "Content-Type: application/octet-stream" \
     --data-binary @/path/to/file.ext \
     "<upload.url>"
   ```

6. Put the same ref into `create_records` template file values or `update_record` file inputs. Notebook-staged refs
   cannot be embedded in richtext; update existing richtext through `set_values` using Markdown without staged
   attachments. Raw HTML is treated as literal text.

The PUT URL is short-lived and single-use. Never send file bytes, base64, local paths, or upload headers through MCP.
The attachment ref is bound to the uploading user and the selected notebook. It can be finalized once into exactly
one file position and is consumed before that write begins. Prepare separate uploads for additional positions,
even when they contain the same file. Template-backed creation with staged attachments accepts one record per call.

If the host can read the selected local file and make the returned raw HTTP request—for example, Codex through its
command environment—perform the upload outside MCP without echoing capability URLs or headers. Otherwise, explain
that the host cannot complete the raw upload and stop before a record write. Never substitute Base64, file contents,
paths, or headers in MCP arguments.
If the PUT response is lost, use the reserved ref once in the intended record write; the write checks readiness.
Do not repeat the PUT. There is no `get_attachment` polling tool. When a PUT error identifies an expired or failed
upload and sets `retryable` to true, prepare a new upload. For other errors, follow the structured recovery message.
If a record write reports an unavailable or consumed attachment ref, inspect the current record state before
preparing a fresh upload for any remaining work; never replay a write that may have started.
Never construct Matelab's internal `elnurl://` form or pass a file hash; the MCP write adapter performs that conversion.
After `update_record`, follow its `persistence` result. If it is `pending_user_save`, the attachment and record change
remain pending in Matelab's browser draft; ask the user to save them in the Matelab web UI and do not repeat the write.

## Append a file to a record

1. Call `prepare_record_edit` for the writable record and choose a module from `edit.file_targets`.
2. Prepare and PUT the new file.
3. Call `update_record` with the current fingerprint:

```json
{
  "append_files": [
    {
      "module": "Attachments",
      "folder_path": ["Raw data", "Run 1"],
      "files": [{"file": "matelab:u:...", "text": "Raw data"}]
    }
  ]
}
```

`append_files` targets current `files` modules. Form file fields can be populated during template-backed creation;
`set_values` cannot attach new files to them. For table file columns, `set_cells` can fill a currently empty cell;
use `replace_files` for an occupied cell. Each row added through `append_rows` can contain at most one staged file.
Omit `folder_path` or use `[]` for the module root. Otherwise pass ordered subfolder names; existing folders with the
exact name are reused and missing folders are created. This is a path inside the files module, not a local path.

## Download an existing attachment

A full record fetch returns up to the first 50 attachment occurrences in `resource.attachments`. Each entry has
attachment metadata under `data`, a human-readable `location`, and a short-lived HTTP GET `download` object. Fetch
that URL outside MCP. Repeat the full fetch if the URL expires. If more occurrences exist, `resource.truncated` is
true and `resource.omitted` reports the remainder; there is no attachment continuation, so another fetch does not
retrieve the omitted files. Do not construct Provider download URLs or expose access tokens.

Check the HTTP status and `Content-Range` before treating the download as complete. A `206` response may contain
only part of the file, even for an open-ended request. For `Content-Range: bytes start-end/total`, continue with
`Range: bytes=<end+1>-` using the same download capability and assemble the returned ranges until all bytes are
present. Check that each returned range starts at the requested offset. If the server returns `200` with the full
file, replace any partial local copy rather than appending it. If the capability expires, full-fetch again and
verify that the new URL identifies the same attachment before continuing.

Richtext image and link occurrences have `data.location.kind: "richtext"`. The returned record Markdown uses matching
temporary download capabilities where available; occurrences beyond the cap have no download URL. These are
read-only attachment entries: change or remove them by replacing the richtext module with Markdown through
`set_values`, not through `remove_files` or `replace_files`.

## Remove or replace an existing attachment

`prepare_record_edit.attachments` contains editable occurrences with opaque `existing_attachment_ref` values and
explicit capabilities. It does not duplicate download instructions or record Markdown.

- Remove only when capabilities include `remove`, by copying the occurrence ref into `remove_files`.
- Replace only when capabilities include `replace`: prepare and PUT the new file, then pass
  `{existing_attachment_ref, new_attachment_ref, text?}` in `replace_files`.
- Omit replacement `text` to preserve a files-module caption. Table file cells do not accept captions.
- Never substitute a filename, download URL, hash, prepared-upload ref, or ref from another record.
- Prepare again before another mutation; old occurrence refs are fingerprint-bound and expire after 24 hours.

Current intentional limits follow returned capabilities: form file occurrences can be removed but not replaced; table
file cells can be replaced but not removed; files-module entries can normally be removed and replaced. A legacy
`images` module is read compatibility only, not a creatable target. Always trust the occurrence's returned capability
list over this summary.
