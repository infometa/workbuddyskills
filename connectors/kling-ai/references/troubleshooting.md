# Troubleshooting

## MCP tools are missing after installation

Reload the host's plugins/extensions and confirm that the `kling-ai` MCP
server is enabled. If the tools still do not appear, restart the host and
check its MCP diagnostics. Do not ask for an API key as a workaround.

## Not authorized or not linked

Open the host's MCP/plugin connection panel, select `kling-ai`, and complete
the browser OAuth flow. If OAuth
returns `invalid_target`, do not add an explicit `oauth_resource` override;
Kling publishes protected-resource metadata and the host should discover it.

## Upload or image-to-video fails

- Confirm `file_upload` returned a Kling URL.
- Reuse the same UUID v7 `taskTraceId` for upload and generation.
- Use the input name declared by the selected live model, commonly
  `first_image` for one first frame.
- Keep every `arguments[].value` a string.

## Status or result URL is unavailable

Use the host's OAuth-connected MCP session and call `query_tasks` once with the
preserved `generationId` (and `taskTraceId` when available). Signed output URLs
expire after 24 hours; query the task again to fetch current URLs.

## Generation fails

Return the provider's failure message and preserve the IDs for support. Do
not automatically create a replacement task because that may consume credits
again.

## Submission timed out and billing is unknown

Do not retry the generation call. First query existing tasks using the
available `taskTraceId`, `generationId`, or provider task-list filters. If the
provider cannot prove whether a task was created, tell the user the billing
state is unknown and request a deliberate decision before any new submission.

## Result link expired

Signed output URLs may be temporary. Query the preserved `generationId` again
to obtain current outputs. Do not log or treat a signed URL as a permanent
asset identifier.
