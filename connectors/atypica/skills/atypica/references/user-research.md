# User research

A study: AI-simulated consumers are interviewed and discuss the user's question, and a report comes out with traceable sources. Use it to understand consumers, test a product or concept, or analyze a market. Results are AI simulations; say so when you present them.

Tools: `atypica_study_*`, `atypica_panel_*`, `atypica_persona_*`. Every field is described on the tool itself.

## The loop

One question is one study. `atypica_study_create({ content })` returns the study's `userChatToken`; the research agent is already running. Then poll and do what `next` says:

```
atypica_study_get_messages({ userChatToken, tail: 5 })  → next
```

| `next.kind`      | Meaning                                           | Do                                                                                                                                            |
| ---------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `running`        | The agent is working                              | Tell the user it is working; poll again (every 30 s until the plan is confirmed, every 2–5 min after)                                         |
| `tool_result`    | The agent asked the user something as a tool call | Show `next.input` to the user in plain words, then `atypica_study_submit_tool_result({ userChatToken, toolCallId: next.toolCallId, output })` |
| `artifact_ready` | A report or podcast is finished                   | `atypica_study_get_report({ token: next.token })` or `atypica_study_get_podcast({ token: next.token })` by `next.artifactType`                |
| `text_message`   | The agent spoke and stopped                       | Relay what it said; send the user's reply with `atypica_study_send_text_message({ userChatToken, text })`                                     |
| `stalled`        | Nothing running, nothing to answer                | `atypica_study_send_text_message({ userChatToken, text: "Please continue the research" })`; `next.error` says why the last run failed         |

- `tail` only limits how many parts come back; `next` is decided on the whole study.
- Writes while the agent runs are rejected (`isError`); wait for `next` to leave `running`.
- `status` in a write result: `running` (agent started), `saved_no_ai` (the account is out of credits; tell the user), `ai_failed` (write again to retry).

## Two ways to write

What the user says goes in as text; what the agent asked as a tool call goes back as that tool's result. The shape of the data decides, not who started the exchange.

| Write          | Tool                                                                      | When                                                                       |
| -------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| A text message | `atypica_study_send_text_message({ userChatToken, text })`                | `next.kind` is `text_message` or `stalled`, or the user says something new |
| A tool result  | `atypica_study_submit_tool_result({ userChatToken, toolCallId, output })` | `next.kind` is `tool_result`                                               |

The `output` each tool call takes, by `next.toolType`:

| `next.toolType`           | `next.input`                                                              | `output`                                                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tool-requestInteraction` | Questions with options: `question` + `options`, or several in `questions` | `{ "answer": ["<option label>"] }`; several questions `{ "answers": [{ "label": "<question label>", "answer": [...] }] }`; skip `{ "skipped": true }` |
| `tool-makeStudyPlan`      | The research plan                                                         | `{ "confirmed": true }` or `{ "confirmed": false }` (the agent re-plans)                                                                              |

Option labels must match exactly; `answer` is always an array, even for one choice. The server keeps the tool call's input; you send only the output. The output is the user's decision: show the question, wait for the user, submit what the user chose. Never confirm a plan or pick an option for the user.

## Delivering

- Report: `atypica_study_get_report` with `next.token`. Give the user `title`, a short summary and `shareUrl`.
- Podcast, when the study made one: `atypica_study_get_podcast` with `next.token`.
- Resume earlier work: `atypica_study_list`; each entry's `token` is that study's `userChatToken`.

## Choosing who is simulated

By default the agent builds the consumer group from the question. To use a group the user already has, `atypica_panel_search` and pass `panelId` to `atypica_study_create`. `atypica_persona_search` / `atypica_persona_get` show individual simulated consumers when the user asks who took part.

## Files

Upload with `atypica_get_upload_credentials` (see SKILL.md), then pass `attachments` to `atypica_study_create` or `atypica_study_send_text_message`. Up to 5 images and 3 documents per message, 3 MB each.
