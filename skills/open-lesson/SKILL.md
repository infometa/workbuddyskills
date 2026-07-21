---
name: open-lesson
description: "Interact with openLesson tutoring API for Socratic learning: generate learning plans as directed graphs, start audio-based tutoring sessions, analyze reasoning gaps, and manage tutoring workflows. Use when users want personalized tutoring, learning plan generation, or Socratic dialogue-based education."
description_zh: "苏格拉底式 AI 辅导：生成学习计划、音频对话式教学、诊断推理差距"
description_en: "Socratic AI tutoring: generate learning plans, audio sessions, reasoning gap analysis"
version: 1.0.2
homepage: https://clawhub.ai/dncolomer/open-lesson
allowed-tools: Read,Write,Bash
---

# OPENLESSON AGENT API SKILL

You are an AI agent that can interact with the openLesson tutoring platform via API.

## OVERVIEW

openLesson is a tutoring system that uses audio-based dialogue to help users learn by asking questions rather than giving answers. The platform generates personalized learning plans as directed graphs, where each node is a session. Agents can programmatically generate learning plans, start sessions, and analyze audio chunks for reasoning gaps.

## IMPORTANT: NO BROWSER TOOL REQUIRED

You do not need a browser tool. You only need shell tools (e.g., curl) to make API calls to openLesson.

## IMPORTANT: AUDIO-ONLY SYSTEM

CRITICAL: The openLesson platform is audio-only. The analyze endpoint accepts ONLY audio input, NOT text.

- Always convert speech to base64-encoded audio before calling the analyze endpoint
- Supported formats: webm, mp4, ogg
- Do not send text to the analyze endpoint — it will be rejected

## AUTHENTICATION

Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

Important: Always use `https://www.openlesson.academy` for API calls. The domain `openlesson.academy` has a redirect that loses the Authorization header.

## CREDENTIALS

This skill requires an API key for the openLesson API:

- Environment variable: `OPENLESSON_API_KEY`
- How to obtain: Generate from the user's dashboard at `/dashboard`

## ENDPOINTS

### 1. GENERATE LEARNING PLAN

Creates a directed graph of learning sessions for a given topic.

**Endpoint**: `POST /api/agent/plan`

```json
{
  "topic": "Machine Learning Fundamentals",
  "days": 30
}
```

Days to Sessions mapping:
- 7 days: 3-5 sessions
- 14 days: 4-7 sessions
- 30 days (default): 5-10 sessions
- 60 days: 8-14 sessions
- 90 days: 10-18 sessions
- 180 days: 15-25 sessions

### 2. START SESSION

Starts a new Socratic session.

**Endpoint**: `POST /api/agent/session/start`

```json
{
  "problem": "Explain how gradient descent works in neural networks",
  "plan_node_id": "uuid-from-plan"
}
```

### 3. ANALYZE AUDIO CHUNK

Submits an audio chunk for Socratic analysis. Returns reasoning gap score and follow-up questions.

**Endpoint**: `POST /api/agent/session/analyze`

```json
{
  "session_id": "uuid-from-start",
  "audio_base64": "base64-encoded-audio-data",
  "audio_format": "webm"
}
```

Response includes: `gapScore`, `signals`, `transcript`, `followUpQuestion`, `requiresFollowUp`

### 4. END SESSION

Ends an agent session and generates a summary report.

**Endpoint**: `POST /api/agent/session/end`

### 5. GET SESSION SUMMARY

Retrieves the summary report of a completed session.

**Endpoint**: `GET /api/agent/session/summary?session_id=xxx`

## COMPLETE AGENT WORKFLOW

1. Generate a learning plan → get plan with nodes
2. Start a session for the first node → get session ID
3. Record and analyze audio → get gap scores and follow-up questions
4. Continue until concept mastery
5. End session → get summary report
6. Move to next node in the plan

## TIPS FOR AGENTS

1. Always use audio: The analyze endpoint ONLY accepts audio
2. Record in webm format (Opus codec preferred)
3. Chunk audio: Send 30-60 second chunks for analysis
4. Follow up: If `requiresFollowUp` is true, ask the follow-up question
5. Track gap scores: Use gap score to determine mastery
6. Schedule all sessions: Create reminders for each planned session

## ERROR HANDLING

- 401: Invalid or inactive API key
- 403: Session doesn't belong to this key
- 404: Session not found
- 500: Internal server error
