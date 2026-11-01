---
name: atypica
display_name: Atypica 用户研究
display_name_en: Atypica User Research
description: User research with atypica.AI. Use when the user wants to understand consumers, test a product or concept, analyze a market, get answers from real people through interviews or surveys, or find out what is already known about a topic. Triggers include 用户研究, 消费者研究, 用户访谈, 问卷, 市场分析, 产品测试, 桌面研究, 调研报告, user research, consumer research, interview, survey, concept test, market analysis, desk research.
description_zh: 用 AI 做用户研究：让 AI 模拟的消费者讨论、接受访谈，用 AI 访谈真人，快速做桌面研究，最后给出可追溯来源的研究报告。
description_en: "User research with AI: run discussions and interviews with AI-simulated consumers, interview real people with an AI interviewer, and do quick desk research, then get reports you can trace back to sources."
examples_zh:
  - "研究年轻人为什么买无糖咖啡"
  - "给我们的新产品做一轮 20 人的用户访谈"
  - "继续我上次的研究，看看进度和报告"
examples_en:
  - "Research why young people buy sugar-free coffee"
  - "Run a 20-person interview about our new product"
  - "Resume my last study and show me its progress and report"
version: 1.0.0
author: atypica.AI
---

# Atypica User Research

atypica.AI answers business questions by researching people. One MCP server, three modes. First pick the mode, then read only that mode's file.

## Pick the mode

| The user wants                                                             | Who answers                                           | Takes                                          | You get                                      | Mode                | Read                           |
| -------------------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- | -------------------------------------------- | ------------------- | ------------------------------ |
| To understand consumers, test a product or concept, analyze a market       | AI-simulated consumers, interviewed and in discussion | Minutes; you poll                              | A report with traceable sources              | **User research**   | @references/user-research.md   |
| Answers from real people: an interview or questionnaire sent by link       | Real people, asked by an AI interviewer               | Hours or days; people answer on their own time | Per-person answers and aggregated statistics | **Human interview** | @references/human-interview.md |
| What is already known about a topic: facts, trends, what people say online | The web and X (Twitter)                               | One call                                       | A written summary                            | **Desk research**   | @references/desk-research.md   |

Signs:

- "Research", "test", "analyze", "how would consumers react" → user research. Research results are AI simulations; say so when you present them.
- "Ask our users", "send a survey", "interview 20 people", "real customers" → human interview.
- "Look up", "what does the internet say", "latest trends", a factual question → desk research.
- Unsure → user research. Its agent clarifies the question with the user before planning anything.

Every tool description also starts with its mode name.

## Connection

The MCP server is `https://atypica.ai/mcp`. If tools named `atypica_*` are available, it is connected; do nothing.

Otherwise the user connects it once in their client:

- **OAuth** (ChatGPT, WorkBuddy, any client with MCP OAuth): add the server URL with no headers. The client opens atypica.AI's sign-in and authorization page; the user approves; the client refreshes access by itself.
- **API key** (clients without OAuth, scripts): create a key at https://atypica.ai/account/api-keys and send `Authorization: Bearer atypica_xxx`.

Both act as the account the user signed in as, personal or team member, and use that account's credits. Never ask the user to paste a key into the conversation when the client can do OAuth.

## Rules for every mode

- **Files**: to attach an image or document, call `atypica_get_upload_credentials({ fileName, mimeType })`, HTTP PUT the file to `putUrl` with the same `Content-Type` within 5 minutes, then pass `objectUrl` where the mode's file says. Images: jpeg, png, gif, webp, bmp, svg. Documents: pdf, json, csv.
- **HTTP 401**: not connected, or the authorization expired or was revoked. OAuth clients reconnect by themselves; with an API key, the user checks it at https://atypica.ai/account/api-keys.
- **Not found**: the token or id belongs to another account or does not exist. Never guess ids; take them from earlier results.
- **Fields**: every tool describes its own input; the mode files only add what the descriptions cannot say (states to look for, answer shapes, limits).
