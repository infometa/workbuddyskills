---
name: ae-generate-tracking-code
description: "Interactive generation of AE tracking code, LogBus2 configuration, and debug scripts from a tracking plan. Trigger words: 代码埋点、埋点代码、tracking code、埋点落地、logbus 配置、AE 上报代码、generate tracking code、insert tracking、トラッキングコード、트래킹 코드. Supports independent output mode selection per platform (insert/snippet). Server-side defaults to LoggerConsumer + LogBus2 architecture."
---

# ae-generate-tracking-code

> **Conversation language**: This skill document is in English, but **all output to the user MUST be in the user's input language**.
> English input → English reply; Chinese input → Chinese reply; Japanese input → Japanese reply.
> If uncertain, default to English.
> This applies to all output: section titles, phase names, template prompts, code comments, etc.
> **⚠️ CRITICAL: Many reference documents (wiki SDK docs, code examples) contain Chinese text. When reading Chinese source material to answer an English/Japanese user, you MUST translate headings, descriptions, and comments to the user's language. The source document's language is NOT the user's language. Use the Terminology Glossary above to map terms accurately.**
> Do NOT copy Chinese text verbatim from this document into English/Japanese replies.
>
> **Document link language**: When providing official documentation URLs, use `lan=zh-CN` for Chinese users, `lan=en-US` for all others.

## Terminology Glossary

| 中文 | English | Notes |
|------|---------|-------|
| 埋点方案 | Tracking Plan | AE project-level event/property definitions |
| 代码埋点 | Tracking Code Generation | Generating SDK/LogBus code from a plan |
| 埋点代码 | Tracking Code | The generated SDK init + track() calls + helpers |
| 输出方式 | Output Mode | insert (inject) or snippet (file delivery) |
| 插入 | Insert | Direct code injection into the user's project |
| 片段 / 代码片段 | Snippet | Code delivered as files under `.ae-cli/output/` |
| 采集端 | Collection Platform / Platform | Where events are sent from: client, server, or both |
| 客户端 | Client | Client-side SDK (Android/iOS/Web/etc.) |
| 服务端 | Server | Server-side SDK (Java/Python/Go/etc.) |
| 两端都采集 | Both | Events collected from both client and server |
| SDK 集成模式 | SDK Integration Mode | `client_only` / `server_only` / `both` |
| 用户体系 | User Identity System | distinct_id / account_id strategy |
| 校验脚本 | Validation / Debug Script | Test code to verify tracking works |
| LogBus2 配置 | LogBus2 Configuration | `daemon.json` for LogBus2 log sync tool |
| LoggerConsumer | LoggerConsumer | Server SDK consumer that writes events to local log files |
| BatchConsumer | BatchConsumer | Server SDK consumer that uploads events in batches |
| 公共属性 | Super Property | Properties attached to all events automatically. ⚠️ The correct Chinese AE term is "公共属性" or "公共事件属性". Never translate "Super Property" as "超级属性" — that is NOT a valid AE term. |
| 预置属性 | Preset Property | System properties prefixed with `#` (e.g. `#device_id`, `#time`) |
| 事件属性 | Event Property | Custom properties on specific events |
| 用户属性 | User Property | Properties set on the user profile |
| 上报地址 | SERVER_URL | Data ingestion endpoint (different from web URL!) |
| APP_ID | APP_ID | Application ID from AE Admin → "Integration Config" |
| project_id | Project ID | AE project identifier (≠ APP_ID) |
| 自动采集 | Auto-track | Auto-collected events (app install, start, view, click) |
| 埋点方案上传 | Plan Upload | Upload tracking plan xlsx to AE |

## When to Trigger

Trigger when user says: "generate tracking code / help me add web tracking / generate logbus config / server-side reporting code" etc. Supports multiple platforms with independent output mode selection per platform.

## Phase 0 — Anchor (one question per message)

### Pre-check: Read existing configuration from draft.json

First, check if `.ae-cli/draft.json` exists and read existing configuration:

| Config Item | draft.json Field | Handling |
|---|---|---|
| AE projectId | `meta.project_id` | Has value → confirm; missing → ask |
| AE web address | `meta.host` | Has value → confirm; missing → ask |
| **SERVER_URL** | `meta.server_url` | Has value → confirm; missing → try lookup from project config, then ask if unavailable |
| **APP_ID** | `meta.app_id` | Has value → confirm; missing → try lookup from accessible project list, then ask if unavailable |
| SDK integration mode | `meta.sdk_integration_mode` | Has value → use directly |
| Client SDK type | `meta.client_platforms` (preferred) or `meta.client_sdk_type` | Has value → use directly |
| Server language | `meta.server_language` | Has value → use directly |
| User identity system | `meta.user_identity` | Has value → use directly |

**Important**: `project_id` ≠ `APP_ID`, and `host` ≠ `SERVER_URL`. Even if project_id and host are already set, SERVER_URL and APP_ID must still be resolved and confirmed separately. Prefer lookup first; ask the user only when lookup is unavailable or ambiguous.

**Multi-platform support**:
- If `client_platforms` exists (array): multi-platform scenario — generate code for each platform
- If only `client_sdk_type` exists: single platform (backward compatible)
- Example: `client_platforms: ["android", "openharmony"]` → generate code for Android + OpenHarmony

**Language support**:
- Android SDK: supports Java / Kotlin (can generate both)
- iOS SDK: supports Objective-C / Swift (can generate both)
- Other SDKs: fixed language, no selection needed

**Language configuration source**:
- Prefer `meta.client_platform_languages` (e.g. `{"android": ["java", "kotlin"]}`)
- If not configured, ask user for Android/iOS platforms only

**Confirmation flow**:
- Has value → ask **"Confirm using draft.json config: <value>? yes / enter new value"**
- User says `yes` → use draft value
- User enters new value → update draft.json and use new value

### Required configuration (must resolve and confirm each item)

**⚠️ Key: SERVER_URL and APP_ID are independent config items. Even if draft.json has project_id and host, you MUST resolve and confirm them. `project_id` ≠ `APP_ID`, `host` ≠ `SERVER_URL`.**

1. **APP_ID** — Prefer automatic lookup before asking:
   - If `meta.project_id` is known, run `ae-cli project info list` once for the current host.
   - Find the project whose `projectId` matches `meta.project_id`.
   - If the matched project has `appId`, ask: **"I found APP_ID `<appId>` for project `<projectId>`. Use it? yes / enter new value"**
   - If the project is missing, ambiguous, or has no `appId`, ask the user to copy APP_ID from AE Admin → "Project Settings" → "Integration Config".
2. **SERVER_URL** — Data ingestion endpoint (**different from web URL**; go to AE Admin → "Project Settings" → "Integration Config" → fill in "Public URL")
   - If `meta.project_id` is known, you may try `ae-cli project info get --project-id <project_id>` once.
   - Use the returned value only if the response explicitly contains a receiver URL field such as `serverUrl`, `pushUrl`, `push_url`, `receiverUrl`, `publicUrl`, `publicReceiverAddress`, `privateReceiverAddress`, or equivalent ingestion endpoint field.
   - If both `publicReceiverAddress` and `privateReceiverAddress` are present, prefer `publicReceiverAddress` as `SERVER_URL` for generated snippets unless the user explicitly needs an internal/private-network receiver.
   - If a value is found, ask: **"I found SERVER_URL `<url>` for project `<projectId>`. Use it? yes / enter new value"**
   - ⚠️ "Public URL" only shows if previously filled in; if empty, this field won't display
   - Solution: ask ops for the URL, or **skip this step** (use `SERVER_URL` or `PUSH_URL` placeholder in code)

**host handling** (optional):
- If you need to fetch plan from AE (no local draft.json) → ask for host
- If local draft.json exists → host is not required for code generation
- Before Debug validation, run `ae-cli config current` and confirm the active host matches the target AE environment; if it does not, run `ae-cli config set-host <AE_HOST>`
- Complete Debug validation with `ae-cli tracking debug-device` and `ae-cli tracking debug-data` by default; only hint the user to open the AE Debug page when those CLI capabilities are unavailable

### If only xlsx file exists (no draft.json)

First, check if both `.ae-cli/draft.json` and `.ae-cli/draft.xlsx` exist:

**If both are missing** — the current environment hasn't generated a tracking plan yet. Remind user of two options:

1. **Do you need to generate a tracking plan first?**
   - Yes → suggest using `ae-generate-tracking-plan` skill
   - Reference: tracking plan document (Feishu: https://www.feishu.cn/docx/Jt0VdhNB6oSJ4TxISs1cq2Ebnmg)

2. **If you already have a tracking plan**
   - Provide the xlsx file path and use `ae-cli tracking code import-template --template` to import
   - Or place the xlsx file at `.ae-cli/draft.xlsx` and re-run

**If xlsx file exists** (provided via `ae-cli tracking code import-template --template` or placed at `.ae-cli/draft.xlsx`):

**Step 1: Parse the xlsx file**

```bash
ae-cli tracking code import-template --template <xlsx-path> --out .ae-cli/draft.json
```

This command:
1. Reads events, event properties, super properties, and user properties from xlsx
2. Infers `sdk_integration_mode` from the event `platform` field
3. Outputs draft.json (meta section has events and plan_name only)

**Step 2: What can be inferred from xlsx**

| Field | Can Infer? | Notes |
|---|---|---|
| Event list | ✅ | From `#event data` sheet |
| Event property pool | ✅ | From `#event data` sheet |
| Super properties | ✅ | From `#super property` sheet |
| User properties | ✅ | From `#user data` sheet |
| sdk_integration_mode | ⚠️ Limited | xlsx "Platform" column can infer (client/server/both); if missing, must ask |
| client_platforms | ❌ | Must ask user |
| client_platform_languages | ❌ | Must ask user (Android/iOS only) |
| server_language | ❌ | Must ask user (only if sdk_integration_mode includes server) |
| user_identity | ❌ | Must ask user |
| host / project_id | ❌ | Must ask or skip |

**"Platform" column parsing rules**:
- Empty / no column → cannot infer platform; default to client-side code generation (backward compatible)
- `客户端` / `client` → client-only collection, parsed as `platform: "client"`
- `服务端` / `server` → server-only collection, parsed as `platform: "server"`
- `客户端,服务端` / `client,server` / `服务端,客户端` / `server,client` → both platforms, parsed as `platform: "both"`

**Internal representation**: xlsx "Platform" column values are parsed by `ae-cli tracking code import-template --template` into internal `platform` field values:
- `client` → client-side collection
- `server` → server-side collection
- `both` → both platforms

**Platform filtering during code generation**:
- Client code: only generate events where `platform === "client"` or `platform === "both"`
- Server code: only generate events where `platform === "server"` or `platform === "both"`
- If xlsx has no platform column: generate all events for both client and server (backward compatible)

**Step 3: Ask for missing configuration**

Ask in order, one item per message:

1. **SDK integration mode**: ask **"Will tracking be reported via client-side or server-side? client / server / both"**

2. **Client platform(s)** (only if sdk_integration_mode includes client):
   ask **"What platform(s) is your app?"**
   - Android / Android SDK
   - iOS / iOS SDK
   - OpenHarmony / OpenHarmony SDK (Chinese users only)
   - Web / H5 (JavaScript SDK)
   - WeChat Mini-program (Mini-program SDK) (Chinese users only)
   - WeChat Mini-game (Mini-game SDK) (Chinese users only)
   - Unity Game (Unity SDK)
   - Cocos Game (CocosCreator / Cocos2d-x / Cocos2d-Lua / LayaAir — Cocos2d-Lua & LayaAir for Chinese users only)
   - React Native / Flutter / uni-app
   - Other

   → After user selects, **only if Android or iOS is selected**, follow up:
   - Android → ask **"Which programming language? Java / Kotlin / both"**
   - iOS → ask **"Which programming language? Objective-C / Swift / both"**

3. **Server language** (only if sdk_integration_mode includes server):
   ask **"What is your server-side language?"**
   - Java
   - Python
   - Go
   - Node.js
   - PHP
   - C# / .NET
   - Other

4. **User identity system**:
   - Account ID source: user_account / role_id / none
   - Visitor ID strategy: auto / device_id / custom

5. **APP_ID / SERVER_URL**: resolve them with the lookup-first flow above, confirm any found values with the user, and ask only for values that cannot be found or are rejected by the user.

**Step 4: Merge configuration and proceed to Phase 1**

Write gathered info to `.ae-cli/draft.json` meta section, then proceed to Phase 1.

---

### If no local plan file

Without `.ae-cli/draft.json` or `.ae-cli/remote-plan.json`:

1. **AE projectId** — get from AE Admin
2. **AE web address** — needed to fetch plan
3. Run `ae-cli tracking plan fetch` to retrieve the tracking plan

   **Follow-up rules** (determine which platforms need code based on integration mode):

   | Integration Mode | Platforms/Sides to Generate |
   |---|---|
   | `client_only` | 1 client platform (read from plan's `client_sdk_type` or ask) |
   | `server_only` | 1 server language (read from plan's `server_language` or ask) |
   | `both` | Client platform + server language (both needed) |

---

### Platform Definitions

**Client platforms** (corresponding to client SDKs):

| plan field | Platform | SDK |
|---|---|---|
| `android` | Android | Android SDK |
| `ios` | iOS | iOS SDK |
| `openharmony` | OpenHarmony | OpenHarmony SDK |
| `javascript` | Web / H5 | JavaScript SDK |
| `miniprogram` | Mini-program | Mini-program SDK |
| `unity` | Unity | Unity SDK |
| `game_engine` | Game Engine | Cocos / Laya / Unreal |

**Server languages** (corresponding to server SDKs):

| plan field | Language | SDK |
|---|---|---|
| `java` | Java | Java SDK |
| `python` | Python | Python SDK |
| `go` | Go | Go SDK |
| `nodejs` | Node.js | Node SDK |
| `php` | PHP | PHP SDK |
| `csharp` | C# | C# SDK |

**SDK document paths**:
- Do not use hard-coded wiki paths from this section.
- Always read `references/sdk-index.md` first and use the path listed there for the selected SDK.
- If the path from `references/sdk-index.md` does not exist in the local wiki mirror, search under `~/.ae-cli/wiki/raw/` with SDK-specific keywords and use the best matching latest main document.

---

### Output Mode Definitions

Each platform can choose between two output modes:

| Mode | Description | Parameters | Deliverables |
|---|---|---|---|
| **insert** | Direct Edit injection into user project | Requires project path (absolute) | Code written to target directory |
| **snippet** | Markdown print + generate code file | No path needed | `.ae-cli/output/<platform>-sdk.<ext>` |

**Server-side defaults** (always generated for server):
- LoggerConsumer code (insert or snippet, matching user's choice)
- LogBus2 config file (`.ae-cli/output/daemon.json`)
- Official docs link: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

**Standalone option**:
- `debug` — validation script (generates test upload code)

---

## Phase 1 — Load plan

```bash
ae-cli auth login --host <host>
ae-cli auth status
ae-cli tracking plan fetch --project <projectId> --host <host> > .ae-cli/remote-plan.json
```

Failure fallback:
- AE unreachable → ask user if they want to use `.ae-cli/draft.json` (local existing plan)
- Neither available → abort, suggest running `ae-generate-tracking-plan` first

**Read SDK integration config**:
From the plan file, read:
- `meta.sdk_integration_mode` — SDK integration mode
- `meta.client_sdk_type` — client SDK type (if `client_only` or `both`)
- `meta.server_language` — server language (if `server_only` or `both`)
- `meta.user_identity` — user identity config (used to generate `login()` / `identify()` calls)

**Determine list of platforms to generate code for**:
```
platforms = {
  client: [client_sdk_type]  // e.g. ['android'] or ['javascript']
  server: [server_language]  // e.g. ['java'] or ['python']
}
```

---

## Phase 2 — Route mode (select output mode)

### 2.1 Show platform list

Based on Phase 1 config, display the platforms that need code:

```
Platforms requiring code generation:

Client:
- android (Android SDK)

Server:
- java (Java SDK, default LoggerConsumer + LogBus2)
```

### 2.2 Quick options

Provide shortcuts to simplify interaction:

**Option 1: One-click generation (recommended)**
- All platforms use `snippet` mode
- Generate all code files to `.ae-cli/output/` at once
- **No project path needed** — delivers copy-ready code directly
- Best for quickly getting code reference to integrate manually

**Option 2: Insert into project**
- Each platform independently chooses `insert` or `snippet`
- **Project path required** — code is written directly to your project directory
- Best for existing projects where code should land in specific locations

### 2.3 Per-platform selection flow

If user chooses "per-platform selection", ask in platform order:

**Client platform prompt**:
```
Client android — choose output mode:
1. insert — requires project path
2. snippet — no path needed, generates code file

Your choice: insert / snippet
```

- `insert` → ask **"What is the project path? (absolute path)"**
- `snippet` → no additional parameters

**Server language prompt**:
```
Server java — choose output mode:
1. insert — requires project path
2. snippet — no path needed, generates code file

Your choice: insert / snippet

(Defaults included: LoggerConsumer + LogBus2 config + official docs link)
```

- `insert` → ask **"What is the project path? (absolute path)"**
- `snippet` → no additional parameters
- Server always gets `.ae-cli/output/daemon.json` regardless of mode
- **Always provide LogBus2 official docs link**: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

### 2.4 Standalone option

After platform selection is done, ask:

**"Generate a debug validation script? yes / no"**

- `yes` → generate `.ae-cli/output/te-debug.<ext>`
- `no` → skip

### 2.5 Summary of selections

Show final selection summary:

```
Output mode summary:

Client android: snippet
  Deliverables: .ae-cli/output/android-sdk.java

Server java: snippet
  Deliverables: .ae-cli/output/java-sdk.java
                .ae-cli/output/daemon.json

LogBus2 official docs: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

Standalone option: debug
  Deliverable: te-debug.java

Confirm? yes / no
```

---

## Phase 3 — Execute (per platform)

### 3.1 Pre-execution check

Before Phase 3 begins, check:
```bash
test -z "$(git status --porcelain)" || echo "uncommitted changes present"
```

**Handling rules**:
- `snippet` / `debug` → no check needed (doesn't touch user code)
- `insert` selection → check git status
  - git clean → proceed
  - git dirty → pause, wait for user choice:
    ```
    Uncommitted changes detected. Insert mode requires a clean git workspace.

    Choose:
    1. Commit / stash first, then tell me and I'll continue with insert
    2. Switch to snippet mode for code snippets (re-run skill later for insert)
    ```
    - User chooses 1 → after user completes commit/stash, **re-check Phase 3.1**, then proceed with insert
    - User chooses 2 → all `insert` modes switch to `snippet` for this run

### 3.2 Platform dispatch and execution

**Event platform filtering rules (important)**:
- xlsx "Platform" column values map to `platform` field:
  - `客户端` / `client` → `platform: "client"`
  - `服务端` / `server` → `platform: "server"`
  - `客户端,服务端` / `client,server` → `platform: "both"`
- Client code: only generate events where `platform === "client"` or `platform === "both"`
- Server code: only generate events where `platform === "server"` or `platform === "both"`
- If xlsx has no platform column (legacy plan): generate all events (backward compatible)
- `platform === undefined` (xlsx lacks column) → generate for both sides

**Client code generation**:

| Output Mode | Execution Flow |
|---|---|
| `insert` | Read `references/client-sdk-insert.md` → Explore project → Plan insertion → Edit to write |
| `snippet` | Read `references/snippet-delivery.md` → Print markdown + generate `.ae-cli/output/<platform>-sdk.<ext>` |

**Only generate events where `platform === "client"` or `platform === "both"`**

**⚠️ Hard rule: Never guess SDK imports**
- Before generating, MUST read `references/sdk-index.md`, resolve the corresponding SDK wiki main document, verify the path exists, and then read that main document
- **MUST copy import statements and package names from the wiki main document**, never guess
- Example: JavaScript SDK npm package is `thinkingdata-browser`, import variable is `ta`
- If generated code doesn't match wiki docs (e.g. `TDAnalytics`/`te`/`@thinkingdata/web-sdk`), re-read wiki and fix
- **Re-read docs before every code generation**, never rely on "remembered" code

---

**Server code generation**:

| Output Mode | Execution Flow |
|---|---|
| `insert` | Read `references/server-sdk-insert.md` → Explore project → Plan insertion → Edit to write |
| `snippet` | Read `references/snippet-delivery.md` → Print markdown + generate `.ae-cli/output/<language>-sdk.<ext>` |

**Only generate events where `platform === "server"` or `platform === "both"`**

**Server-side defaults** (always included):
- Generate LoggerConsumer mode code (writes to local log files)
- Generate `.ae-cli/output/daemon.json` (LogBus2 configuration)
- **Always provide LogBus2 official docs link**: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

**⚠️ Hard rule: Never guess SDK imports**
- Before generating, MUST read `references/sdk-index.md`, resolve the corresponding SDK wiki main document, verify the path exists, and then read that main document
- **MUST copy import statements and package names from the wiki main document**, never guess
- **Re-read docs before every code generation**, never rely on "remembered" code

---

**Standalone option execution**:

| Option | Execution Flow |
|---|---|
| `debug` | Read `references/debug-script.md` → Generate `.ae-cli/output/te-debug.<ext>` |

---

## Phase 4 — Deliver (output manifest)

Show deliverables based on selected output modes:

### Attachment upload

After all `.ae-cli/output/` files are generated, upload every generated output file to the Agent attachment library so the user can download them from the file/attachment management entry.

Use the existing attachment command:

```bash
ae-cli agent +add-attachment --files '<json-array-of-generated-output-files>'
```

Upload list rules:
- Include all generated snippet files under `.ae-cli/output/`.
- Include generated server config files such as `.ae-cli/output/daemon.json` and LogBus README files.
- Include `.ae-cli/output/README.md`.
- Include generated debug scripts if the user selected the debug option.
- Do not upload files inserted directly into the user's project; only upload generated output artifacts.

### Attachment upload compatibility

The Agent attachment backend accepts a limited document MIME set. Code/config artifacts such as `.java`, `.kt`, `.swift`, `.m`, `.ets`, `.cs`, `.py`, `.go`, `.ts`, `.js`, `.php`, and `.json` may be rejected if uploaded directly.

Before running `ae-cli agent +add-attachment`, prepare the upload list as follows:
- Keep every original generated file unchanged under `.ae-cli/output/`.
- For each generated text artifact whose extension may be unsupported by the attachment backend, create an upload-only sibling copy by appending `.txt` to the filename.
  - Example: `.ae-cli/output/java-sdk.java` → `.ae-cli/output/java-sdk.java.txt`
  - Example: `.ae-cli/output/daemon.json` → `.ae-cli/output/daemon.json.txt`
- The `.txt` copy must have identical content to the original file. Do not wrap it in markdown fences, do not add headers, and do not change line endings intentionally.
- Upload the `.txt` compatibility copies instead of the unsupported originals.
- Keep `.md`, `.txt`, and `.csv` artifacts in the upload list as-is.
- In the final response, list the original deliverable paths first, then mention any `.txt` compatibility copies used only for attachment upload.

If upload succeeds, include the attachment upload result in the final response and tell the user the files are available from the file/attachment management entry. If upload fails because Agent attachment credentials are unavailable, keep the local `.ae-cli/output/` files and tell the user the upload did not complete.

### All snippets

```
Deliverables:

Client:
- .ae-cli/output/android-sdk.java (Android SDK code snippet)

Server:
- .ae-cli/output/java-sdk.java (Java SDK LoggerConsumer code)
- .ae-cli/output/daemon.json (LogBus2 configuration)

LogBus2 official docs: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

Standalone:
- .ae-cli/output/te-debug.java (validation script)

README: .ae-cli/output/README.md (usage instructions)

Attachment upload: uploaded generated output files to the file/attachment management entry
```

### Mixed (some insert + some snippet)

```
Deliverables:

Client android (insert):
- <project-path>/src/main/java/.../TrackingHelper.java (SDK init + event calls)

Server java (snippet):
- .ae-cli/output/java-sdk.java (LoggerConsumer code snippet)
- .ae-cli/output/daemon.json (LogBus2 configuration)

LogBus2 official docs: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

Standalone:
- .ae-cli/output/te-debug.java (validation script)

Attachment upload: uploaded generated output files to the file/attachment management entry
```

### Markdown code snippet display

For all `snippet` selections, display code grouped by platform in the markdown response:

```
## Client Android

### SDK Initialization
```java
TDAnalytics.init(this, SERVER_URL, APPID);
```

### Super Properties
```java
Map<String, Object> superProperties = new HashMap<>();
superProperties.put("channel", "app_store");
TDAnalytics.setSuperProperties(superProperties);
```

### Event Group: auth
#### user_login
```java
TDAnalytics.track("user_login", new HashMap<String, Object>() {{
    put("login_method", "phone");
}});
```
...
```

---

## Phase 5 — Validate hint

Provide validation guidance based on selected platforms:

### Validation Steps

```
Validation steps:
1. Confirm the active AE environment:
   ae-cli config current

2. List existing Debug devices:
   ae-cli tracking debug-device list --project-id <project_id>

3. Create the script's stable device ID if it is missing, then select it:
   ae-cli tracking debug-device add --project-id <project_id> --device-id <device_id> --device-name <name>
   ae-cli tracking debug-device select --project-id <project_id> --device-id <device_id>

4. Run validation script:
   - Client: run .ae-cli/output/te-debug-client.<ext>
   - Server: run .ae-cli/output/te-debug-server.<ext>

5. Query the most recent hour of Debug data:
   ae-cli tracking debug-data list --project-id <project_id> --device-id <device_id>

6. Confirm has_data=true, then inspect event names, property structures, and error fields.
   If needed, add --event-name <event_name> or --start-time "YYYY-MM-DD HH:mm:ss".

7. Only if the CLI capability is unavailable, open the AE Debug page:
   https://<host>/#/data/debug

8. For LogBus2:
   - Copy daemon.json to LogBus2 conf/ directory
   - Start: ./logbus start
   - Official docs: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US
```

### After validation passes

- Remind user to commit changes (if any `insert` was used)
- Remind user to call `login()` / `identify()` in code to associate user IDs
- Remind user to copy daemon.json to LogBus2 conf/ directory

### Validation failure

- Ask user to paste error text for debugging
- Check SERVER_URL / appId correctness
- Check network connectivity
- Check LogBus2 config file format

---

## Prohibitions

- **Any `insert` without running `git status` check first (IMPORTANT: must check first; refuse execution if uncommitted changes exist)**
- Skipping reference docs in Phase 3 and inserting code arbitrarily
- Ignoring `// @tracking <event>` comment incremental detection
- Reusing web host as SERVER_URL (must be separate)
- **Using LogBus v1 (deprecated — only use LogBus2)**
- Generating LogBus2 config without providing official documentation link
- Including `platform === "server"` exclusive events in client code
- Including `platform === "client"` exclusive events in server code (unless `platform === "both"`)
- **Skipping SDK main doc read and guessing integration method** — each SDK has different integration approaches; must read wiki main doc's "Integrate SDK" section first, and choose the correct method based on project characteristics (with/without build tools)
- **Translating "Super Property" as "超级属性" in any user-facing output (code comments, interaction prompts, markdown) — the correct AE Chinese term is "公共事件属性" or "公共属性"**
- **Entering Phase 1 before Phase 0.5 is complete** — SDK integration must be confirmed before inserting code, otherwise generated track() calls won't work

---

## Internal Reference

All output mode rules are in `references/*.md`. This SKILL.md only handles phase orchestration.

**SDK document index**:
- `references/sdk-index.md` — All SDK wiki document path index (canonical source)

**Output mode references**:
- `references/client-sdk-insert.md` — Client code insertion workflow
- `references/snippet-delivery.md` — Code snippet generation workflow
- `references/server-sdk-insert.md` — Server code insertion workflow (LoggerConsumer + LogBus2)
- `references/logbus-config.md` — LogBus2 configuration generation (includes official docs link)
- `references/debug-script.md` — Validation script generation

**LogBus2 official documentation** (must provide when generating config):
- User guide: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US
- Download link is in the official doc's "二、Download LogBus2" section

**Wiki directory structure** (see `~/.ae-cli/wiki/schema.md`):
- `~/.ae-cli/wiki/raw/` — AE official documentation mirror (read-only, maintained by crawler)
- `~/.ae-cli/wiki/synthesis/` — LLM-synthesized overview documents

**Document reading order during code generation**:
1. Read `references/sdk-index.md` to find the selected SDK's main document and advanced guide paths.
2. Verify the main document path exists in the local wiki mirror before reading it.
3. If the indexed path is missing, search under `~/.ae-cli/wiki/raw/` with SDK-specific keywords such as SDK name, platform name, language name, and `main doc`; choose the latest main document, not historical/versioned documents.
4. Read the wiki main doc first (initialization, imports, package names, basic API).
5. Read the advanced guide only after the main doc (LoggerConsumer, user properties, auto-track, preset properties, etc.).
6. Check advanced guide sub-documents if needed.
