# Troubleshooting

## MCP tools are missing after installation

Reload WorkBuddy and confirm that the `kling-ai` MCP
server is enabled. If the tools still do not appear, restart the host and
check its MCP diagnostics. Do not ask for an API key as a workaround.

## Not authorized or not linked

Open WorkBuddy's connector connection entry, select `kling-ai`, and complete
the browser OAuth flow. WorkBuddy may show the connection under the connector
details page or MCP settings. If OAuth returns `invalid_target`, do not invent
an `oauth_resource` override; report the host diagnostic and verify the current
Kling protected-resource metadata.

## Upload or image-to-video fails

- Refresh the live schema and identify its current upload tool and output field.
- Reuse the upload reference exactly as returned.
- If the schema returns or requires a `taskTraceId`, preserve the same value
  across upload and generation.
- Use only the input names, value types, and reference roles declared by the
  selected live tool; do not assume `file_upload`, `first_image`, or string-only
  argument values.

## Task is still running

During the original generation turn, continue polling with the live status tool
at intervals allowed by Kling until the task succeeds or fails. If the user
cancels or the turn times out, return the task number; the task keeps running on
Kling's side. A later explicit status request queries it once.

## Generation fails

Return the provider's failure message and preserve the IDs for support. Do
not automatically create a replacement task because that may consume credits
again.

## Insufficient credits

Tell the user the balance is insufficient and ask them to recharge before
trying again. Do not retry automatically.

## Submission timed out and task creation is unknown

Do not retry the generation call. First query existing tasks using the
available `taskTraceId`, `generationId`, or provider task-list filters. If the
provider cannot prove whether a task was created, tell the user the submission
status is unknown and ask whether they want to create a new task.

## Result link expired

Signed output URLs may be temporary. Query the preserved `generationId` again
to obtain a current output URL, or view the generation history on the Kling
website while signed in to the authorized account. An expired URL does not mean
the generated work was lost. Do not log or treat a signed URL as a permanent
asset identifier.
