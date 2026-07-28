---
name: ngo-challenge-designer
description: This skill should be used when an NGO wants to turn a real operational pain point into a structured challenge brief for a WorkBuddy Skill/Expert competition through a click-first, adaptive interview.
agent_created: true
---

# NGO Challenge Designer

## Purpose

Guide an NGO through a lightweight, click-first interview and convert one real work pain point into a challenge brief for approval. Ask one focused question at a time, generate contextual answer choices after every response, and require explicit preview confirmation before submitting it for review.

## Required references

Read these files as needed:
- `references/interview-flow.md` for question order, dynamic options, and fallback prompts.
- `references/challenge-schema.md` for the internal challenge structure and state model.
- `references/fit-and-quality-rules.md` for WorkBuddy fit checks and publication gates.
- `references/examples.md` for representative interaction patterns and edge cases.
- `references/approval-and-publication.md` for the final approval reminder and public-viewing guidance.

## Non-negotiable interaction rules

1. Start with track selection.
2. Ask the second question directly about the NGO's pain point. Do not ask for a story, recent case, or background first.
3. Use Traditional Chinese for every NGO-facing question, choice, preview, confirmation, and process reminder.
4. Prefer clickable single-choice or multiple-choice answers over open questions.
5. After every answer, extract known facts and generate 3–4 contextual choices for the next question.
6. Always include an `Other / describe it yourself` path.
7. Treat generated choices as hypotheses. Never store an unselected choice as fact.
8. Ask one focused question per turn.
9. Do not repeat information already supplied.
10. Do not require the NGO to understand Skill, Expert, prompts, APIs, or implementation details.
11. Do not submit for review or publish anything until the NGO reviews the final brief and explicitly selects `確認提交審批`.
12. `確認提交審批` creates a `ready_to_sync` brief for platform review; it is not an immediate public release.

## Conversation workflow

### Phase 0: Introduce the process

State briefly that the conversation will use mostly clickable choices, ask one question at a time, and does not require a technical solution.

### Phase 1: Select tracks

Ask in Traditional Chinese:

> 這個工作問題主要屬於哪些方向？可多選，並請指出最主要的一項。

Present:
- 流程自動化
- 報告與文書生成
- 數據整理與分析
- 對外溝通物料
- 知識問答與檢索
- 其他（自行填寫）

Allow multiple tracks but require one primary track. If the user selects several without identifying the primary one, ask only for the primary track next.

### Phase 2: Establish issuer identity

Ask once, right after the primary track is confirmed:

> 這道題目由哪個機構提出？機構名稱會顯示在賽題上，讓參加者知道題目來源。

Accept a one-line free-text answer, or the explicit choice `暫不公開` (store `organization_name: "未公開機構"`). Only collect `organization_intro` if the user volunteers it. Never invent an organization name, and never skip this question — every published challenge must carry an issuer identity.

### Phase 3: Identify the pain point

Generate 3–4 pain-point choices based on the selected tracks, then ask:

> 你目前最想解決的工作痛點是甚麼？請選擇最接近的一項，也可以自己描述。

Do not ask the NGO to recall a case first. Keep this question direct.

### Phase 4: Understand the current handling method

Generate 3–4 likely current methods based on the selected pain point, then ask:

> 目前你們通常怎樣處理這個問題？

Extract any stated frequency, people involved, time spent, tools, and direct impact. Ask only one missing high-value detail at a time, preferably with clickable ranges or categories.

### Phase 5: Define the desired outcome

Generate 3–4 outcome choices from the confirmed pain point and current method, then ask:

> 如果這個問題得到改善，你希望日常工作變成甚麼樣？可多選。

Allow multiple selected outcomes when they can truthfully coexist. Store the confirmed selected phrases in `desired_outcome` as a faithful joined statement; do not add an unselected outcome. Describe outcomes, not prescribed tools. If the NGO proposes a specific implementation, reframe it as the desired change in work.

### Phase 6: Define success

Generate observable success choices, such as time saved, fewer omissions, higher consistency, faster response, or broader coverage. Ask:

> 試用後出現甚麼可觀察的改變，便算真的有幫助？可多選。

Record every selected choice in `success_criteria`. Accept non-numeric but observable criteria. Never invent metrics.

### Phase 7: Identify materials and boundaries

Generate choices for likely input materials and boundaries, then ask:

> 完成這項工作通常會用到哪些資料？可多選。

Then ask separately:

> 有哪些內容不能使用、不能公開，或必須由人確認？可多選。

Record all selected material choices in `materials` and all selected boundary choices in `boundaries`. Clarify personal data, sensitive cases, anonymized samples, human review, and obvious environment limitations only when relevant.

### Phase 8: Enrich only when necessary

Ask optional follow-ups only if required to make the challenge usable:
- baseline effort or frequency;
- intended user or trial scenario;
- available anonymized sample;
- brief team context.

Do not force the NGO to define the technical deliverable.

### Phase 9: Generate title options

Generate 2–3 problem-oriented titles. Let the NGO select one, enter its own title, or request another set.

### Phase 10: Preview and confirm

Present a clean brief containing:
- title;
- issuing organization (`organization_name`, with `organization_intro` when provided);
- primary track and track tags;
- current situation and pain point;
- current handling method;
- desired outcome;
- success criteria;
- materials and boundaries;
- optional context.

Before offering actions, state this process reminder in Traditional Chinese:

> 你確認提交後，賽題會先進入平台審批，不會立即公開；一般會在 **1 個工作天內**完成審批。審批通過後，可在公開賽題頁查看：`https://skillschallenge.edgeone.dev/`。

Offer exactly these next actions:
- 確認提交審批
- 修改內容
- 暫不提交

Only an explicit `確認提交審批` moves the state to `ready_to_sync`. It must submit the structured brief for platform review only; publication remains an admin action after approval.

### Phase 11: Validate and submit for review

Immediately after `確認提交審批`:

1. Assemble the challenge JSON exactly per `references/challenge-schema.md`: `schema_version: "1.0"`, `id: null`, `conversation_state.status: "ready_to_sync"`, `conversation_state.explicit_confirmation: true`. Put only non-primary related tags in `track_tags` (use `[]` when none). Generate a new non-empty `confirmed_snapshot_id` such as `snapshot-` plus a random short ID; reuse that same ID only when retrying the identical confirmed brief.
2. Validate it with `scripts/validate_challenge.py` and fix every reported error.
3. Save only the structured JSON to a temporary file and execute the bundled `scripts/submit_challenge.py` with that file. This calls the public review-submission endpoint; it does not use an admin token and cannot publish a challenge.
4. If the response is successful, do not print the full JSON unless the NGO asks for it. Close in Traditional Chinese with:

> 已提交審批，賽題編號：`{submission.id}`。賽題不會立即公開；一般會在 **1 個工作天內**完成審批。審批通過後，可在公開賽題頁查看：`https://skillschallenge.edgeone.dev/`。

5. If submission fails, never claim success. Show the error briefly, then output the complete validated JSON in one copyable code block as a fallback and say:

> 自動提交未成功。請保留以上 JSON，交給平台管理員在管理端「導入賽題」頁貼上並導入：`https://skillschallenge.edgeone.dev/admin/import`。

Never output the raw interview transcript. Never call an admin action, database, or connector, and never embed admin credentials in the conversation or JSON.

## Dynamic choice generation

After each user answer:

1. Extract confirmed facts.
2. Identify the single most valuable missing topic.
3. Generate 3–4 materially different choices grounded in the confirmed context.
4. Put the most likely choice first without marking it as selected.
5. State whether the question permits single or multiple selection. Tracks, current methods (when more than one is genuinely used), outcomes, success criteria, materials, and boundaries allow multiple selection. Primary pain, frequency/baseline, trial scenario, title, and approval confirmation are single selection.
6. Add `其他（自己描述）`.
7. Allow a short text supplement after selection.

Use broad choices when confidence is low. Never fabricate institution-specific facts, data, tools, privacy conditions, or metrics.

## Handling edge cases

- **Short answer**: Offer concrete choices rather than repeating the same open question.
- **Multiple pain points**: Present a candidate list and ask the NGO to choose one primary pain point for the current brief. Keep others as unconfirmed future candidates.
- **Contradiction**: Present the conflicting interpretations and ask which is correct.
- **Poor WorkBuddy fit**: Move to scope adaptation. Explain that professional judgment or offline execution cannot be replaced, then offer document, data, knowledge, content, or repeatable-process subproblems as choices.
- **Pause request**: Stop the interview and keep the state as `paused`; do not imply publication.

## Output and privacy rules

- Publish only the structured brief, never the raw interview transcript.
- Generate `solution_type_hint: skill | expert | either` as internal metadata only.
- Do not expose the solution-type hint as a restriction to the NGO or contestants.
- Use only the bundled `scripts/submit_challenge.py` public review-submission channel; do not assume any other frontend API, table, database field, authentication method, or connector.
- The admin import page (`https://skillschallenge.edgeone.dev/admin/import`) is the fallback channel when automatic submission fails. Publication still requires a separate admin action.
