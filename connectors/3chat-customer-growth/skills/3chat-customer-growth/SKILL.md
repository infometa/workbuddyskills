---
name: 3Chat私域客户运营
description: Use 3Chat to search customers, read customer communication context, analyze customer conversations, draft follow-up messages, send confirmed customer messages, and check batch send status.
---

# 3Chat Customer Growth

Use this skill when the user wants to search 3Chat customers, understand customer communication context, analyze customer conversations, draft customer follow-up messages, send confirmed messages to customers, or check the status of a batch send task.

3Chat helps businesses manage customer conversations across connected channels and maintain long-term customer communication context. This skill lets the assistant use 3Chat customer search, conversation context, and messaging capabilities during daily work.

## Supported Capabilities

This skill supports:

- Search one or more 3Chat customers by name, email, phone, account, channel-related fields, or supported custom-field conditions.
- Read communication context for one or more customers, including the customer's unique session, session memory summary, recent conversations, conversation custom fields, and conversation messages.
- Analyze customer communication history and summarize customer needs, objections, interests, recent progress, and suggested follow-up direction.
- Draft follow-up messages based on the user's intent and the customer's 3Chat communication context.
- Send one message to one confirmed customer after the user explicitly confirms the recipient, message content, and attachments if any.
- Send confirmed messages to multiple selected customers after the user explicitly confirms the recipients, message content, attachments if any, and send scope.
- Check the execution status of a batch send task.

This skill does not support:

- Sending messages without explicit user confirmation.
- Creating marketing campaigns or automated workflows.
- Editing customer profile data.
- Creating, editing, publishing, or rolling back 3Chat Agents.

## Available Tools

This skill requires the bound 3Chat MCP Connector with source `3chat-customer-growth` and MCP server name `3chat-customer-growth`.

Expected MCP server name:

- `3chat-customer-growth`

If this connector or its tools are unavailable, tell the user that the `3chat-customer-growth` MCP Connector is not connected, authorized, or configured correctly, and ask them to connect or reauthorize it before continuing.

Use these tools from the bound connector:

- `search_3chat_customers`
- `search_3chat_customers_context`
- `send_3chat_customer_message`
- `send_3chat_customer_messages`
- `get_3chat_batch_send_status`

## Tool Usage

### `search_3chat_customers`

Use this tool to search 3Chat customers.

Use it when the user asks to:

- find a customer
- query customer information
- filter customers by name, email, phone, account, channel, or supported custom fields
- find customers that match multiple conditions

The tool can return zero, one, or many customers.

Rules:

- If the user only asks to list, count, filter, summarize, or analyze multiple customers, do not force the user to choose one customer.
- If the next step requires exactly one customer, and the tool returns multiple customers, ask the user to choose one.
- If no customer is found, ask the user for more clues such as full name, company, phone number, email, channel, or account.
- Multiple filter fields are matched with AND semantics. Multiple alternative values within the same filter field are matched with OR semantics.

### `search_3chat_customers_context`

Use this tool to read communication context for one or more confirmed customers.

The tool returns:

- the customer's unique 3Chat session
- the session memory summary maintained by 3Chat
- recent conversations under the session
- conversation entity fields and conversation custom fields, when requested
- messages under each returned conversation, when requested
- Agent logs only for Agent messages, when requested

Rules:

- Use this tool after customer IDs are available from `search_3chat_customers`, or when the user provides confirmed 3Chat customer IDs.
- Use it when the user asks what a customer discussed, what the customer cares about, what happened recently, why the customer is high intent, or how to follow up.
- Do not treat this tool as a full customer profile or persona API.
- The session memory summary is the long-term summary across the customer's communication lifecycle.
- A conversation summary is only the summary of one conversation.
- Conversation custom fields belong to conversation entities. Do not assume session or message custom fields are available.

### `send_3chat_customer_message`

Use this tool to send one message to one confirmed customer. The message may contain text, attachments, or both.

Rules:

- This is a high-impact action.
- Before calling this tool, identify exactly one customer.
- If multiple customers match, ask the user to choose one.
- Before sending, show the recipient, the exact message content, and attachments if any.
- When sending attachments, use the final downloadable file URL for each attachment.
- Ask the user for explicit confirmation.
- After the user explicitly confirms, generate or pass a confirmation token for the tool call.
- Call this tool only after the user confirms.
- Never send messages based on inferred consent.
- Never claim a message was sent unless this tool returns success.

### `send_3chat_customer_messages`

Use this tool to send messages to multiple selected customers. Each message may contain text, attachments, or both.

Rules:

- This is a high-impact batch action.
- Before calling this tool, identify the customer set and the exact message content and attachments for each recipient or recipient group.
- Show the send scope, recipient count, representative recipients, exact message content, and attachments if any before sending.
- When sending attachments, use the final downloadable file URL for each attachment.
- Ask the user for explicit confirmation.
- After the user explicitly confirms, generate or pass confirmation tokens for the tool call.
- Call this tool only after the user confirms.
- Prefer 1 to 3 send items per batch when possible; larger batches may be limited by connected channels.
- Do not send to more than 100 customers in one batch task.
- Never use this tool when the user only asks to analyze, draft, preview, or estimate an outreach plan.
- Never claim a batch send task was completed unless this tool or `get_3chat_batch_send_status` returns that status.

### `get_3chat_batch_send_status`

Use this tool to check the execution status of a batch send task created by `send_3chat_customer_messages`.

Rules:

- Use this tool when the user asks whether a batch send task has started, completed, failed, or partially failed.
- Use the batch task id returned by `send_3chat_customer_messages`.
- Report status, counts, failures, and recoverable next steps based only on the tool result.

## Common Workflows

### Search Customers

When the user asks to find or filter customers:

1. Call `search_3chat_customers`.
2. Present the matched customers or result summary.
3. If the user wants more context, call `search_3chat_customers_context` with the returned customer IDs.

### Analyze One Customer

When the user asks about a specific customer:

1. Call `search_3chat_customers`.
2. If multiple customers are returned, ask the user to choose one.
3. Call `search_3chat_customers_context` for the selected customer.
4. Use the returned session memory summary, conversations, custom fields, and messages to answer.

### Analyze Multiple Customers

When the user asks about a group of customers:

1. Call `search_3chat_customers` with the user's filtering conditions.
2. Call `search_3chat_customers_context` with the returned customer IDs if conversation context is needed.
3. Summarize patterns, needs, objections, interests, and possible follow-up directions.
4. Do not send messages unless the user asks and confirms the exact recipient or recipient set, message content, attachments if any, and send scope.

### Send A Message

When the user asks to send a message:

1. Call `search_3chat_customers` to identify the recipient.
2. If multiple customers are returned, ask the user to choose one.
3. Optionally call `search_3chat_customers_context` to understand recent communication before drafting.
4. Draft the message.
5. Show the recipient, exact message content, and attachments if any.
6. If attachments are included, make sure each attachment URL is a final downloadable file URL.
7. Ask for explicit confirmation.
8. After confirmation, call `send_3chat_customer_message`.
9. Report the send result.

### Send Messages To Multiple Customers

When the user asks to send messages to a group of customers:

1. Call `search_3chat_customers` to identify the target customer set.
2. Optionally call `search_3chat_customers_context` if message drafting needs recent communication context.
3. Draft the message or per-customer message variants.
4. Show the send scope, recipient count, representative recipients, exact message content, and attachments if any.
5. If attachments are included, make sure each attachment URL is a final downloadable file URL.
6. Ask for explicit confirmation.
7. If the target set contains more than 100 customers, ask the user to narrow the target set or split it into smaller batches.
8. After confirmation, call `send_3chat_customer_messages`.
9. Report the returned batch task id and initial status. Do not say the batch has completed unless a tool result explicitly says it has completed.
10. Use `get_3chat_batch_send_status` when the user asks for progress or final results.

## Attachment URL Rules

When sending an attachment through `send_3chat_customer_message` or `send_3chat_customer_messages`, the attachment `url` must be a plain HTTP or HTTPS URL string that points to the final downloadable file resource.

Do not pass Markdown link syntax such as `[https://example.com/file.png](https://example.com/file.png)`.

Do not pass short links, redirect links, preview page links, browser-only links, or links that require a browser to open before reaching the file.

When the user uploads an image in the Work Agent, use the static CDN URL or the final redirected image URL as `attachments[].url`, not the short upload link shown in the chat interface.

For images, prefer URLs that directly return an image resource, such as PNG, JPG, JPEG, GIF, or WebP, or URLs whose HTTP response has an image Content-Type.

## Safety Rules

- Do not invent customer data, conversation content, message content, or send results.
- Do not guess which customer the user means when multiple customers match.
- Do not send messages without explicit confirmation.
- Do not expose raw access tokens, API keys, app secrets, or connector credentials.
- If a tool returns an error, explain the issue clearly and suggest the next recoverable step.
- If available data is partial, state what is missing and continue only with the available context.
