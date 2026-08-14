# Kling AI for WorkBuddy

Kling AI connects WorkBuddy to the official OAuth-protected Kling MCP service
for image and video creation.

## Capabilities

- Text-to-image and image-to-image generation
- Text-to-video and image-to-video generation
- Credit and task-status queries
- Generation progress tracking and result delivery

## Connect

Install the connector from WorkBuddy, choose **Connect**, and complete the Kling
OAuth flow in the browser. WorkBuddy manages authorization and refresh; no API
key is required.

To switch accounts, disconnect the current account before connecting the intended
account. Never paste credentials, tokens, or cookies into a conversation.

## Use

Describe the image or video you want in natural language. Kling AI submits one
generation task and checks it at service-allowed intervals until it succeeds or
fails. If the current turn ends first, it returns a **task number** that can be
used to query the same task later.

If credits are insufficient, recharge the Kling account and try again. Completed
results include the primary image, video, or result link supplied by Kling.
Temporary result links can be refreshed by querying the original task number;
the work also remains available in the authorized account's Kling generation
history.

See [README.zh-CN.md](./README.zh-CN.md) for Chinese documentation.

## License

[MIT](./LICENSE)
