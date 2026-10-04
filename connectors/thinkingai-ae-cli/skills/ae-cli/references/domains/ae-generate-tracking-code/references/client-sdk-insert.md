# Mode A — Client SDK Code Insertion

> **Terminology**: 客户端 SDK = client SDK | 代码插入 = code insertion/injection | 前置检查 = pre-check | 集成方式 = integration method | 埋点 = tracking/event tracking | 业务触发点 = business trigger point | 公共属性 = super property (公共事件属性; never "超级属性") | 用户属性 = user property | 自动采集事件 = auto-track event | 插入位置预览 = insertion site preview | 语言风格校验 = language style check

## ⚠️ Mandatory Pre-checks (do not skip)

**Before inserting code, execute in the following order. Each step must be completed before proceeding to the next:**

### Stage 0: Read SDK Main Document (must complete, never skip)

1. **Read `references/sdk-index.md`** to find the SDK's main document path
2. **Read the SDK main document's "Integrate SDK" section** to understand:
   - **npm package name** (e.g. `thinkingdata-browser`, `@thinkingdata/react-native-sdk`)
   - **import/require statement** syntax
   - **All integration methods** (e.g. JS SDK has npm / CDN sync / CDN async)
3. Choose integration method based on project characteristics:
   - Has `package.json` + build tool → npm integration
   - Plain HTML / no build tool → CDN method
4. Read `~/.ae-cli/wiki/synthesis/sdk-selection.md` to confirm appType's npm package name and init signature
5. Read the corresponding cheatsheet (e.g. `js-sdk-cheatsheet.md`) for additional details

**⚠️ Prohibited**: Skipping Stage 0 and writing code directly, guessing integration methods, using unverified CDN URLs

### Stage 0 Mid-point Language Identification (do not skip)

When reading the SDK main document, if it uses multi-language tab format (e.g. `::: el-tab-pane label=Java` / `label=Kotlin` or ` ```java` / ` ```kotlin`), **must confirm the language for the current task**:

- Android docs: identify `label=Java` vs `label=Kotlin` code blocks
- iOS docs: identify `label=Objective-C` vs `label=Swift` code blocks
- Other multi-language docs: same principle

**⚠️ Prohibited**: Copying code examples without confirming language, mixing code snippets from different languages.

### Stage 0.5: SDK Integration Confirmation (must execute after Stage 0)

Based on the integration method chosen in Step 3, confirm with user whether SDK is already integrated:

**Integration methods that require code changes (npm / Gradle / CocoaPods / Maven / pip / go get, etc.)**:

```
Project detected using <integration-method>. Configuration file changes needed to add dependencies.

Should I modify the config file directly to add SDK dependencies?
- yes → Edit the config file (e.g. package.json / build.gradle / Podfile), then proceed to Stage 1
- no → Reference the docs below to complete SDK integration, then reply yes to continue

Documentation: <wiki doc path>
```

- User `yes` → Execute Edit on config file, then proceed to Stage 1
- User `no` → Display doc path, pause and wait for user completion

**Integration methods that don't require code changes (CDN script tag / UnityPackage / manual file placement, etc.)**:

```
Project uses <integration-method>. No config file changes needed.

Please reference the docs below to complete SDK integration, then reply yes to continue.

Documentation: <wiki doc path>
```

Wait for user confirmation, then proceed to Stage 1.

---

## Stage 1: Explore
1. Grep entry points: `src/main.*`, `src/App.*`, `pages/_app.*`, `index.html`
2. Grep existing tracking: `ta\.track|thinkingdata|TA\.init|// @tracking`
3. Grep routing: `react-router|vue-router|next/router`
4. Grep user state: `(handleLogin|onLogin|signIn|doLogin)` / `(handleLogout|signOut)`
5. **Grep business trigger points** (finding where to insert track() calls — the correct insertion sites):
   - Button/click: `(onClick|handleClick|onTap|@click|\.click\()`
   - Form submit: `(onSubmit|handleSubmit|onFormSubmit)`
   - Page entry: `(onMounted|onShow|onLoad|componentDidMount|useEffect.*\[.*\])`
   - Purchase/payment: `(onPurchase|handlePurchase|doPurchase|payOrder)`
   - Search: `(onSearch|handleSearch|doSearch)`
   - Custom events: `(emit|trigger|dispatch|sendEvent)`
- Astro-specific:
  - Entry: `src/middleware.ts` (SSR middleware, suitable for page_view), `src/layouts/*.astro` (global layout for init), `astro.config.mjs` (integrations)
  - Client components: `<script>` blocks in `*.astro` files, React/Vue island components with `client:*` directives
- **For each business trigger found, record its file:line and business meaning** for Stage 2 mapping

## Stage 2: Insertion Plan (markdown table)

**Platform filtering**:
- xlsx "Platform" value `客户端` / `client` → `platform: "client"` (client-only collection)
- xlsx "Platform" value `客户端,服务端` / `client,server` → `platform: "both"` (both platforms)
- xlsx "Platform" value `服务端` / `server` → `platform: "server"` (server-only, do NOT generate in client)
- Only insert events where `platform === "client"` or `platform === "both"`

**⚠️ Auto-track event handling**:
- Auto-track events (e.g. `ta_page_view`, `ta_app_crash`, etc.) are automatically collected by the SDK, **do NOT manually insert track() code for them**
- However, you MUST **enable the corresponding auto-track switch** after SDK initialization for them to take effect
- ⚠️ **MUST read `references/autotrack-enum.md`** first to look up correct enum values before writing code; never guess (e.g. Unity's `AppStart` ≠ `APP_START`)
- Mark which auto-track events need to be enabled in the insertion plan for user confirmation in Stage 3

```
## SDK Initialization
- File: <path>:<line>
- Code: init(...) with appId/SERVER_URL

## Auto-track Event Switches (if needed)
- Enum values: check `references/autotrack-enum.md`, do not guess
- File: <path>:<line>
- enableAutoTrack({...}) or quick("autoTrack")

## Super Properties
- File: <path>:<line>
- setSuperProperties({...})

## User Properties
- File: <path>:<line>
- user_set / user_setOnce / user_add

## Event Group: <tag>
- <event_name>: <file>:<line> [Business action: <business meaning>]
  Insertion rationale: <why insert here, e.g. "called after user clicks pay button">
- ...
```

**⚠️ Business action mapping is the core of the insertion plan**:
- Every event must be mapped to a concrete business action (e.g. "user clicks login button", "order submit success callback")
- Business actions must come from Stage 1 exploration results, never guess
- If no business trigger point is found for an event, mark it in the plan as `⚠️ No trigger point found; manual confirmation needed`

**⚠️ After Stage 2, MUST show the "Insertion Site Preview"** for user to confirm each event's insertion point matches business expectations:

```
## Insertion Site Preview

| Event | File Location | Business Action | Confirm |
|---|---|---|---|
| payment_success | src/pages/Pay.jsx:42 | User clicks "Confirm Payment" button | ok / change |
| user_login | src/pages/Login.jsx:28 | User clicks "Login" button | ok / change |
```

- User `ok` → proceed to Stage 3
- User says "change" → remap specific events to correct business trigger points
- **Do not skip this preview and go directly to Stage 3**

After showing, ask user `ok` to enter Stage 3, or "go back to event X to remap".

## Stage 3: Batched Edit
- Batch 1: SDK init + super properties
- Batch 2: User properties
- Batch 3..N: Grouped by `event_tag`
- Each batch: use Edit tool; print file list + added line count after completion, ask `ok / undo`
- `undo` → reverse Edit to rollback the batch

## Stage 3.5: ⚠️ Language Style Check (do not skip)

After each batch Edit, perform language style checks on modified files:

| Language | Check Rules |
|---|---|
| **Kotlin** | File must not contain `;` (trailing semicolons); fix immediately if found |
| **Java** | Every statement must end with `;`; fix immediately if missing |
| **Swift** | Do not use `var` for optional types — use `let` + `?`; do not use `@objc` unless necessary |
| **Objective-C** | Method calls must use `[self method]` syntax — no `.` calls; must use `nil`, not `null` |

**If language style errors are found**:
1. Immediately replace with correct syntax
2. Note in the batch confirmation: `⚠️ Auto-corrected: <error description> → <correct syntax>`

## Stage 4: Summary
- Print all modified files + newly added events per file
- Suggest user consider running Mode F (debug)

## Code Style
- Singleton: create `src/lib/tracking.ts` (if not exists), export `ta` singleton
- Prefix each track call with `// @tracking <event_name>` comment
- Do NOT add try/catch
- Event names / property names strictly from plan, do not modify
- Astro: SDK init goes in `<script>` block of `src/layouts/BaseLayout.astro`; page_view uses middleware or `Astro.url.pathname` listener

## Pre-check
- `git status --porcelain` not empty → refuse, prompt user to commit/stash first

## Stage 5: Verification Steps (insert mode only)

**⚠️ Insert mode: debug is off by default. Do not guide user to the Debug page to view data.**

### Verification Steps
1. **Integrate SDK** (follow steps based on integration method)
   - **npm / package manager** (JavaScript/React Native/Flutter/uni-app): Run `npm install` or equivalent to install SDK
   - **Build tool integration** (Unity/Unreal): Add SDK dependency via Package Manager or Epic Games Launcher
   - **Dependency management** (Android/iOS): Add SDK dependency in `build.gradle` / `Podfile`
   - **Manual download** (Web H5/Mini-program/Game engine, etc.): Download SDK files and place in project directory

   Reference the official docs in `references/sdk-index.md` for each SDK

2. **Open AE Real-time Data page** (NOT the Debug page)
   - `https://<host>/#/data/realtime`
   - Since debug mode is off, data goes through the normal upload pipeline — only the real-time data page can show it

3. **Trigger events by interacting with the app** and check if data appears

### Pre-launch Checklist
- [ ] Confirm `debug: false` or no debug field in config
- [ ] SDK correctly integrated (dependencies added / files placed)
- [ ] Real-time data page shows event uploads
