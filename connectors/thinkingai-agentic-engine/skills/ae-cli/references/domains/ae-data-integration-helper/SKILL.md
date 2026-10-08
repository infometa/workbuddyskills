---
name: ae-data-integration-helper
description: "Answers questions about ThinkingData SDK integration and usage, including the LogBus2 data import tool. Trigger words: 怎么接入 / 如何集成 / SDK / 埋点 / 报错 / 使用方式 / API / LogBus / tracking / integration / how to integrate / data import / データ連携 / インテグレーション / 트래킹 / 연동."
---

# ae-data-integration-helper

> **Conversation language**: This skill document is in English, but **all output to the user MUST be in the user's input language**.
> Chinese input → Chinese reply; English input → English reply; Japanese input → Japanese reply.
> If uncertain, default to English.
> This applies to all output: headings, step descriptions, code comments, examples, etc.
> **⚠️ CRITICAL: Many reference documents (FAQ, wiki) are in Chinese. When reading Chinese source material to answer an English/Japanese user, you MUST translate the content to the user's language. The source document's language is NOT the user's language. Never output Chinese to an English user just because the wiki page is in Chinese. Use the Terminology Glossary above to map terms accurately.**
> Do NOT copy Chinese text verbatim from this document into English/Japanese replies.

## Terminology Glossary

| 中文 | English | Notes |
|------|---------|-------|
| 埋点 / 数据上报 | Tracking / Data Ingestion | Sending event data to TE |
| 用户识别规则 | User Identification Rule | distinct_id / account_id mapping |
| 访客 ID | Visitor ID / Guest ID | Anonymous user before login |
| 登录 ID | Login ID / Account ID | Identified user after login |
| 预置属性 | Preset Property | `#device_id`, `#time`, `#ip`, etc. |
| 系统字段 | System Field | TE built-in fields prefixed with `#` |
| 事件格式 | Event Format | Event name + properties structure |
| 属性类型 | Property Type | String / Number / Boolean / Date / Array |
| 数据校验 | Data Validation | Verify event format & property types |
| 公共事件属性 | Super Property | Properties attached to all events. ⚠️ The correct Chinese AE term is "公共事件属性" or "公共属性". Never translate "Super Property" as "超级属性" — that is NOT a valid AE term. |
| 可更新事件 | Updatable Event | Event whose properties can be updated after creation |
| 首次事件校验 | First Event Check | Validate an event's first occurrence |
| 自动采集 | Auto-track | Auto-collected events (app install, start, page view, etc.) |
| 实时调试 | Real-time Debug / Debug Mode | Device binding + live data validation |
| 合规 / 隐私 | Compliance / Privacy | GDPR, privacy policy, SDK data collection rules |
| 数据导入 | Data Import | LogBus2 / RESTful API / DataX |
| 缓存上报 | Batch Upload / Buffered Upload | Cache events locally, then upload in batches |
| 重试策略 | Retry Strategy | Re-upload failed data automatically |
| 数据加密 | Data Encryption | Encrypt event data before upload |
| 时间校准 | Time Calibration | Sync device time with server time |
| 多端上报 | Multi-platform Tracking | Report events from multiple clients/services |
| 用户割裂 | User Fragmentation | Same user split into multiple TE user profiles |
| 上报模式 | Upload Mode | Normal / Debug / Debug_Only |
| LoggerConsumer | LoggerConsumer | Server SDK consumer that writes events to local log files |
| BatchConsumer | BatchConsumer | Server SDK consumer that uploads events in batches |
| DebugConsumer | DebugConsumer | Server SDK consumer for debug mode (not for production) |

## When to Trigger

Trigger when a user asks about:

- **Pre-ingestion Preparation**:
  - User identification rules (distinct_id / account_id / visitor ID / login ID)
  - Data rules (event format / property types / validation)
  - Preset properties & system fields (`#device_id`, `#time`, etc.)
- **Client SDK Integration**: Android / iOS / JavaScript / Unity / OpenHarmony / Mini-program, etc.
- **Server SDK Integration**: Java / Python / Go / Node.js / PHP / C#, etc.
- **Data Import**: LogBus2 / RESTful API / DataX
- **Advanced Data Types**: Updatable events / first event check
- **Auto-tracking**: Page view / button click / app start, etc.
- **Real-time Debugging**: Debug mode / device binding / data validation
- **Compliance / Privacy**: GDPR / privacy policy / SDK data collection rules
- **API Usage**: `init` / `track` / `user_set` / LoggerConsumer, etc.
- **Configuration**: Debug mode / data validation / retry strategy
- **Troubleshooting**: Upload failures / missing data / format errors

**Do NOT trigger**: Inline Q&A within `ae-generate-tracking-plan` or `ae-generate-tracking-code` sessions (those skills have their own workflows). Offline local-file import (CSV / Excel / JSONL → AE) is owned by the `ae-data-integration` skill — route those requests there instead of answering with LogBus / RESTful guidance.

## Workflow

### Step 1: Parse the Question

Extract from the user's query:

- **Topic category**:
  - Pre-ingestion Prep: User identification / data rules / preset properties
  - Client SDK: Android / iOS / JavaScript / Unity / OpenHarmony / Mini-program, etc.
  - Server SDK: Java / Python / Go / Node.js / PHP / C#, etc.
  - Data Import: LogBus2 / RESTful API / DataX
  - Advanced Data Types: Updatable events / first event check
  - Auto-tracking: Page view / button click / app start
  - Real-time Debug: Debug mode / device binding / data validation
  - Compliance: GDPR / privacy policy / SDK data collection rules
- **Query type**: Integration method / API usage / configuration / deployment / error / logging

### Step 1.5: Information Gathering

**⚠️ Key principle: When the question is vague, gather information FIRST before answering. Do NOT guess or ramble.**

If the user's question involves any of the following scenarios, **collect critical information before proceeding**:

| Scenario | Must Collect |
|----------|-------------|
| "Data not showing up" / "Can't see data" / "Upload successful but nothing in the dashboard" | Upload method (SDK / LogBus / HTTP), data type (event / user property), specific symptom (no data at all / partial data) |
| "Error" / "Failure" type questions | Full error message, reproduction steps |
| "Can't connect" / "Unable to upload" | Platform/language used, error symptoms |
| "How to implement X" | Platform/language used, what X specifically means |

**Ask first, then answer**. Examples:
- "Data logs show success but the dashboard shows nothing — are you using SDK, LogBus, or HTTP upload?"
- "Can't connect — which language/platform are you using? Can you share the error message?"

### Step 2: Find Relevant Documentation

**Prefer FAQ documents first** (for quick lookup of specific issues):
1. Read `skills/ae-data-integration-helper/references/` corresponding FAQ (e.g., `android_sdk_faq.md`, `logbus2_guide.md`, etc.)
2. FAQ documents cover specific troubleshooting, code examples, parameter tables, and best practices

**Check wiki when FAQ has no answer** (for framework-level and authoritative content):
1. Read `~/.ae-cli/wiki/te-docs/index.md` to locate document paths
2. Prefer overview documents under `~/.ae-cli/wiki/te-docs/synthesis/`
3. For detailed API references, check the corresponding main document under `~/.ae-cli/wiki/te-docs/raw/`

**Commonly used FAQ documents**:
- `references/android_sdk_faq.md` — Android SDK integration & FAQ
- `references/ios_sdk_faq.md` — iOS SDK integration & FAQ
- `references/java_sdk_faq.md` — Java SDK integration & FAQ
- `references/logbus2_guide.md` — LogBus2 complete configuration guide
- `references/sdk_usage_notes.md` — Client/server SDK usage notes
- `references/restful_api_notes.md` — RESTful API usage notes
- Full list: see `references/index.md`

### Step 3: Read & Summarize

After reading relevant documentation, output in the following format:

```
## <Topic> (<Platform>)

### Summary
<1-2 sentence description>

### Integration / Usage Steps
1. <Step 1>
2. <Step 2>
...

### Code Example
```<language>
<code>
```

### Notes / Caveats
- <Note 1>
- <Note 2>

### Source Document
<Prefer wiki document sourceUrl. Language rules:
  - User interacts in Chinese → provide Chinese doc (lan=zh-CN)
  - User interacts in other languages → provide English doc (lan=en-US)
  - Chinese-only SDKs (Mini-program / OpenHarmony / Cocos2d-Lua / LayaAir / Egret) → Chinese only
  Example: https://docs-v2.thinkingdata.cn/?version=v6.0&lan=en-US&code=xxx>
(If no sourceUrl, provide local .md file path)
```

**⚠️ Terminology Rules**:
- **Only output what is in the documentation**. Do NOT speculate, imagine, or fill in defaults.
- **Never translate "Super Property" as "超级属性"** — the correct AE Chinese term is "公共事件属性" or "公共属性". This applies to all user-facing output: headings, step descriptions, code comments, examples, etc.
- For uncertain information (e.g., data delay times, specific limit values), **do NOT fabricate**.
- If the document has no direct answer but allows inference: mark under "Source Document" as "Synthesized inference; recommend verification".
- If the documentation truly does not cover the question, fall back to Step 4. Do NOT force an answer.

### Step 4: Fallback

If neither FAQ nor wiki has relevant content:
- Provide the official online documentation link: https://docs-v2.thinkingdata.cn
- Optionally suggest running the `te-wiki-synthesize` skill to generate a new synthesis document.

## Example Conversations

**User**: What is distinct_id and how do I use it?

**Agent**:
1. Read `references/index.md` to find user identification rule document paths
2. If `sdk_usage_notes.md` or wiki has relevant sections, read those first
3. Output in the Step 3 format

**User**: How do I configure LogBus2?

**Agent**:
1. Read `references/logbus2_guide.md`
2. Output in the Step 3 format

**User**: Java SDK is losing data — what should I do?

**Agent**:
1. Read `references/java_sdk_faq.md`, section on "LoggerConsumer data loss risks"
2. Output in the Step 3 format

**User**: How do I integrate the Android SDK?

**Agent**:
1. Read `references/android_sdk_faq.md` or `~/.ae-cli/wiki/te-docs/index.md` to find Android SDK path
2. Read the relevant sections
3. Output in the Step 3 format

```
## Android SDK Integration

### Summary
Android SDK supports both Gradle and manual AAR integration. Gradle is recommended.

### Integration Steps (Gradle)
1. Add mavenCentral to project-level `build.gradle`:
   ```groovy
   repositories { mavenCentral() }
   ```
2. Add dependency to module-level `build.gradle`:
   ```groovy
   dependencies {
       implementation 'cn.thinkingdata.android:ThinkingAnalyticsSDK:3.3.6'
   }
   ```
3. Initialize SDK:
   ```java
   TDAnalytics.init(this, SERVER_URL, APPID);
   ```

### Source Document
~/.ae-cli/wiki/te-docs/raw/data-ingestion-guide/client-sdk/android.md
```

**User**: How do I enable real-time debugging for Android SDK?

**Agent**:
1. Read `~/.ae-cli/wiki/te-docs/raw/data-ingestion-guide/client-sdk/android/android-advanced/debugging-and-logging.md`
2. Output in the Step 3 format

## Internal Reference

**FAQ Documents** (check first):
- `references/index.md` — All FAQ document index
- `references/android_sdk_faq.md` — Android SDK FAQ
- `references/logbus2_guide.md` — LogBus2 complete guide
- `references/sdk_usage_notes.md` — SDK usage notes

**Wiki Documents** (check when FAQ has no answer):
- `~/.ae-cli/wiki/te-docs/index.md` — All wiki document index
- `~/.ae-cli/wiki/te-docs/schema.md` — Wiki layout description
- `~/.ae-cli/wiki/te-docs/raw/preparations-before-data-ingestion/user-identification-rules.md` — User Identification Rules
- `~/.ae-cli/wiki/te-docs/raw/preparations-before-data-ingestion/data-rules.md` — Data Rules
- `~/.ae-cli/wiki/te-docs/raw/preparations-before-data-ingestion/preset-properties-and-system-fields.md` — Preset Properties
- `~/.ae-cli/wiki/te-docs/raw/advanced-data-type/updated-event.md` — Updatable Event
- `~/.ae-cli/wiki/te-docs/raw/advanced-data-type/first-event-check.md` — First Event Check
- `~/.ae-cli/wiki/te-docs/raw/data-ingestion-guide/data-import-tools/logbus2-user-guide.md` — LogBus2
