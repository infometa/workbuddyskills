# Scientific analysis of Matelab attachments

The Matelab server can expose public scientific MCPs through the same Identity-authorized connection. Matelab tools
retain their names. Analysis tools use a configured service prefix; inspect live discovery and schemas before use.
Typical prefixes are `arpes`, `matrouter`, `hsp`, `magscan`, `microscopy_analysis`, `crack_seg`, and `pxrdgen`.
These prefixes belong to tool names, in addition to any client-added server namespace.

If a domain's tools are missing, report that the service is unconfigured or unavailable. Other Matelab tools can
still be used. Do not invent a result or bypass Matelab authorization. No separate analysis OAuth resource is needed
for these public services. Never pass MCP Authorization, Cookie, credentials or user identity into their arguments
or transfer requests.

## Record to ARPES

1. Discover the notebook and use `search_records` to select the intended record. Call `fetch(ref, view="full")`.
2. Select an occurrence from `resource.attachments`. Its metadata is in `data`; the temporary GET capability is in
   `download`. Download the entire input using the [attachment workflow](attachment-workflows.md), including all
   `Content-Range` continuations. A partial response is not a complete input file.
3. Call `arpes_prepare_upload` with the plain filename, for example `{"filename":"sample.txt"}`. Follow the ARPES
   Skill and current service requirements for supported file formats.
4. Outside MCP, HTTP PUT the raw file to the returned `upload.url` using the returned method and headers. Do not
   substitute the Matelab MCP token for this upload capability. Do not send bytes, base64 or local paths in tool
   arguments. If the host cannot perform the raw transfer, explain the missing host capability before submitting.
5. Copy the returned ARPES `attachment_ref` into `arpes_denoise`, for example `{"attachment_refs":["<returned ref>"]}`.
   For scanning-mesh artifacts, use `arpes_demesh` and its live parameters instead. Matelab refs and ARPES refs are not
   interchangeable. Analysis writes are authorized by the user's analysis request; writing results back into a
   record is a separate requested action.
6. Copy the returned `task_id` into `arpes_get_task_status`. Follow the reported pending/running/succeeded/failed
   lifecycle. Do not submit another task merely because processing is still running or a response was lost;
   consult the domain's recovery and idempotency rules.
7. Only after success, call `arpes_get_task_outputs` with the same ID. HTTP GET available `url` values in the returned
   result and preview manifests. Preserve null or missing artifacts as unavailable, rather than constructing URLs.
8. Report the source record, selected attachment, task state and available results. Use the domain Skill to explain
   scientific meaning and limitations. Link to downloaded outputs when the host supports it.

When ARPES can directly access the returned attachment URL, `arpes_ingest_url(url, filename)` can replace the local
download/PUT steps. Domain services own their URL allowlists and network behavior; use the raw upload path if URL
ingestion is rejected. An expiring Matelab download capability is not a permanent input reference.

## Other domains and saving results

Use current discovery and the matching domain Skill: `microscopy_analysis_detect_blobs`, `crack_seg_segment_cracks`,
`magscan_analyze_signal` / `magscan_analyze_field`, and `pxrdgen_predict` consume their own prepared inputs. HSP uses
`hsp_prepare_structure_upload` and `hsp_identify_structure_symmetry`; MatRouter has its own evidence acquisition and
scientific method tools. Read their actual input schemas rather than assuming every service accepts ARPES refs or
has the same status/result tools. Algorithms, task storage and large-file processing remain in those services.

When the user asks to save results back to Matelab, download the chosen artifacts, use the original unprefixed
`prepare_upload` for the target notebook, PUT each file, then `prepare_record_edit` and `update_record` with fresh
edit metadata. Follow `pending_user_save` and uncertain-write recovery exactly as in the attachment workflow.
Do not replay a record write or place an analysis attachment ref directly into a Matelab file field.
