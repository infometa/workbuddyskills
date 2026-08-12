# kling-ai

Generate and monitor **Kling AI** images and videos right inside your chat, through Kling's official OAuth-protected MCP server.

## What it does

- Text-to-image & image-to-image
- Text-to-video & image-to-video (single and multi-shot)
- Check your remaining credits and task status
- Automatically checks task status until the generation completes or fails

## Install & authorize

1. Submit or import this Connector directory into WorkBuddy.
2. Open your host's **MCP / plugin connection** panel, find `kling-ai`, and click **Trust / Connect**, then sign in to your Kling account to authorize.
   Authorization uses OAuth — the skill never asks for an API key in chat.

## How to use

Just describe what you want in natural language. The skill shows the final settings and waits for your confirmation before any credit-consuming generation.

- *"Generate a 16:9 cinematic poster: a glass teapot in a white studio."*
- *"Turn this photo into a 5-second, 720p clip; keep the subject stable."*
- *"Check the status of generationId <id>."*

After submitting, the skill automatically checks the task until it completes or fails, then returns the result for display.

## Notes

- Output links (images/videos) **expire after 24 hours** — download in time.
- Each task is submitted **at most once** per confirmed intent; the skill never auto-retries.
- Never expose tokens, cookies, or signed output links.

## License

Released under the [MIT License](./LICENSE).
