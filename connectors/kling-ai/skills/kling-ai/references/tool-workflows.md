# Remote tool workflow

1. Discover the live tools and schemas from remote `kling-ai` at `https://klingai.com/mcp`.
2. For attached media, call the remote upload tool and pass its returned reference to the generation request.
3. Once materially missing inputs are resolved, call the selected remote generation tool once and preserve its `generationId`. Do not add a credit warning or separate confirmation step.
4. If submission is not terminal, poll with the status tool declared by the live schema at provider-allowed intervals until success or failure. On user cancellation or current-turn timeout, return the state and task number.
5. Present the returned image, video, text, or one primary output link when complete.

Never retry a generation automatically.
