# Snippet Output Mode

> **Terminology**: 片段/代码片段 = snippet/code snippet | 产物 = deliverable/output | markdown 响应 = markdown response | 初始化 = initialization | 公共属性 = super property (公共事件属性; never "超级属性") | 用户属性 = user property | 事件组 = event group | 触发时机 = trigger timing | 验证步骤 = verification steps | 设备绑定 = device binding | 自动采集事件 = auto-track event | 占位值 = placeholder value | 属性类型 = property type

## Deliverables

Three outputs:
1. **Markdown response**: code snippets grouped by platform (for reading)
2. **Code files**: `.ae-cli/output/<platform>-sdk.<ext>` (for copy-paste use)
3. **Attachment library upload**: generated files uploaded with `ae-cli agent +add-attachment` so the user can download them from the file/attachment management entry

---

## Markdown Response Structure

### 0. Pre-checklist

Show configuration info:
```
Configuration:
- SDK type: <platform> (e.g. android / java / javascript)
- SERVER_URL: <user-provided ingestion URL>
- appId: <user-provided APP_ID>
- User identity: account_id=<field>, distinct_id=<strategy>
```

### 1. SDK Initialization Snippet

```
## <Platform> SDK Initialization

```<lang>
// Copy to your entry file
<init code with SERVER_URL / appId>
```

### 1.1 Auto-track Event Enablement (if needed)

**Important**: Auto-track events (e.g. page view, button click) are disabled by default after SDK init.
You must call the corresponding API to **enable** them after or during initialization.

⚠️ **Must read `references/autotrack-enum.md` first** to look up the correct enum values and names for the target SDK.
**Do not write auto-track code without checking the enum table** — wrong enum names will cause runtime errors.

```
## Auto-track Event Switches

```<lang>
// Add auto-track switches based on selected SDK type
<autoTrackEnable code>
```
```

### 2. Super Properties Snippet

```
## Super Properties

```<lang>
// Call after SDK init
<setSuperProperties code>
```
```

### 3. User Properties Snippet

```
## User Properties

```<lang>
// Call after user login
<user_set / user_setOnce code>
```
```

### 4. By Event Group

```
## Event Group: <tag>

### <event_name>
Trigger: <event_desc>

```<lang>
// Place at <trigger location>
ta.track('<event_name>', {
    <prop_name>: <sample value>,
    ...
});
```
```

Show each event individually, each as its own block for easy copying.

### 5. Verification Steps (snippet mode only)

```
## Verification Steps

1. **Integrate SDK** (follow steps based on integration method)
   - **npm / package manager**: Run `npm install` or equivalent to install SDK
   - **Build tool integration**: Add SDK dependency via Package Manager or Epic Games Launcher
   - **Dependency management**: Add SDK dependency in `build.gradle` / `Podfile`
   - **Manual download**: Download SDK files and place in project directory

   Reference the official docs in `references/sdk-index.md` for each SDK

2. **Debug mode device binding** (AE Debug requires device ID to be added first)
   - Get device ID: DeviceId printed in console after SDK init, or call SDK's getDeviceId method
   - Add device: AE Admin → Tracking Management → Debug Mode → Add Device → paste device ID

3. **Trigger events by interacting with the app** and view data in AE Debug page
```

---

## Code File Generation

### File Path Rules

| Platform | File Path |
|---|---|
| Client android (java) | `.ae-cli/output/android-sdk-java.java` |
| Client android (kotlin) | `.ae-cli/output/android-sdk-kotlin.kt` |
| Client ios (objc) | `.ae-cli/output/ios-sdk-objectivec.m` |
| Client ios (swift) | `.ae-cli/output/ios-sdk-swift.swift` |
| Client openharmony | `.ae-cli/output/openharmony-sdk.ets` |
| Client javascript | `.ae-cli/output/javascript-sdk.js` |
| Client miniprogram | `.ae-cli/output/miniprogram-sdk.js` |
| Client unity | `.ae-cli/output/unity-sdk.cs` |
| Server java | `.ae-cli/output/java-sdk.java` |
| Server python | `.ae-cli/output/python-sdk.py` |
| Server go | `.ae-cli/output/go-sdk.go` |
| Server nodejs | `.ae-cli/output/nodejs-sdk.ts` |
| Server php | `.ae-cli/output/php-sdk.php` |

**Multi-language platform output rules**:
- Android SDK: if Java + Kotlin selected, generate two files (android-sdk-java.java and android-sdk-kotlin.kt)
- iOS SDK: if Objective-C + Swift selected, generate two files (ios-sdk-objectivec.m and ios-sdk-swift.swift)

### File Content Structure

```<ext>
/**
 * AE Tracking Code Snippet - <Platform>
 *
 * Usage:
 * 1. Copy SDK initialization code to entry file
 * 2. Copy super properties code after init
 * 3. Copy event code to corresponding trigger locations
 *
 * Configuration:
 * - SERVER_URL: <data ingestion URL>
 * - APPID: <APP_ID>
 */

// ==================== SDK Initialization ====================
<init code>

// ==================== Super Properties ====================
<setSuperProperties code>

// ==================== User Properties ====================
<user_set code>

// ==================== Event Group: <tag> ====================
// <event_name> - <event_desc>
<track code>

// ... other events
```

### README File

Generate `.ae-cli/output/README.md`:

```
# AE Tracking Code Snippets

## File List

| File | Description |
|---|---|
| <platform>-sdk.<ext> | SDK initialization + event call code |
| daemon.json | LogBus2 configuration (server-side only) |

## Usage Steps

### Client

1. Copy SDK initialization code to entry file
2. Configure SERVER_URL and appId
3. Copy event code to corresponding trigger locations

### Server

1. Copy LoggerConsumer code to project
2. Configure log file path
3. **Download LogBus2**: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US (download link in "二、Download LogBus2" section)
4. Copy daemon.json to LogBus2 conf/ directory
5. Start LogBus2: `./logbus start`

## LogBus2 Official Documentation

| Document | Link |
|---|---|
| User Guide | https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US |

Note: LogBus v1 is deprecated. Please use LogBus2.

## Verification

Run `te-debug.<ext>` and open AE Debug page to verify data upload.

### Debug Mode Device Binding (snippet mode only)

AE Debug mode requires the device ID to be added in AE Admin before data can be viewed:

1. **Get device ID** (choose one):
   - Client logs: DeviceId printed after SDK initialization
   - Code: `ta.getDeviceId()` to get current device ID

2. **Add device in AE Admin**:
   - Path: AE Admin → Tracking Management → Debug Mode → Add Device
   - Paste device ID and confirm

3. **Verify data**:
   - Trigger events by interacting with the app
   - View data uploads on AE Debug page
```

---

## Attachment Library Upload

After all snippet output files are written, upload generated output artifacts to the Agent attachment library:

```bash
ae-cli agent +add-attachment --files '<json-array-of-generated-output-files>'
```

Upload list must include:
- Every generated platform snippet file under `.ae-cli/output/`
- `.ae-cli/output/README.md`
- Server-side config files, including `.ae-cli/output/daemon.json` and related README files
- Generated debug scripts, if any

Only upload generated output artifacts. Do not upload files inserted directly into the user's project.

### Upload Compatibility for Code and Config Files

The attachment upload endpoint accepts a limited document MIME set. Many generated tracking artifacts are valid text files but have extensions that may be rejected by the backend when uploaded directly, including `.java`, `.kt`, `.swift`, `.m`, `.ets`, `.cs`, `.py`, `.go`, `.ts`, `.js`, `.php`, and `.json`.

Before calling `ae-cli agent +add-attachment`, build an upload-safe file list:

1. Keep the original generated files unchanged in `.ae-cli/output/`.
2. For each unsupported text artifact, create a sibling upload-only copy with `.txt` appended to the original filename.
   - `.ae-cli/output/android-sdk-java.java` → `.ae-cli/output/android-sdk-java.java.txt`
   - `.ae-cli/output/daemon.json` → `.ae-cli/output/daemon.json.txt`
3. Copy the content exactly. Do not add markdown fences, comments, titles, or any extra bytes beyond the original text content.
4. Upload the `.txt` compatibility copies instead of the unsupported originals.
5. Upload already-supported text artifacts such as `.md`, `.txt`, and `.csv` directly.

The final deliverable list should still point users to the original generated files. Mention the `.txt` files only as attachment-upload compatibility copies.

If upload succeeds, report that the files are available from the file/attachment management entry. If upload fails because Agent attachment credentials are unavailable, preserve the local output files and report the upload failure separately.

---

## Generation Workflow

### ⚠️ Mandatory Pre-checks (do not skip)

**Before generating code, execute in the following order. Each step must be completed before proceeding to the next:**

#### Step 0: Read SDK Main Document

1. **Read `references/sdk-index.md`** to find the SDK's main document path
2. **Read the SDK main document**, must include these sections:
   - **Integrate SDK** section (npm package name / CDN URL / integration methods)
   - **Initialization** section (init API signature and example code)
   - **Track** section (event upload API and examples)
   - **User Properties** section (user_set / user_setOnce / user_add API)

3. **⚠️ Do not skip Step 0** — even if you've generated code for the same platform before, must re-read latest docs every time

#### Step 1: Read Config from Plan

1. Read `meta.user_identity` from plan (user identity config)
2. **Read event list from plan, filter by platform**:
   - Client snippet: only read events where `platform === "client"` or `platform === "both"`
     - xlsx "Platform" column: `客户端` or `client` → `platform: "client"`
     - xlsx "Platform" column: `客户端,服务端` or `client,server` → `platform: "both"`
   - Server snippet: only read events where `platform === "server"` or `platform === "both"`
     - xlsx "Platform" column: `服务端` or `server` → `platform: "server"`
     - xlsx "Platform" column: `客户端,服务端` or `client,server` → `platform: "both"`
   - If event has no platform field (legacy xlsx without this column): read all events (backward compatible)
3. Read user property list from plan (user properties have no platform field; generate for both sides)

#### Step 2: Copy Wiki Code Examples

**Must directly copy code examples from the wiki main document read in Step 0**, do not manually write:

- **Initialization code**: directly copy the complete code block from wiki doc (including import statements, package names, init parameters)
- **⚠️ Strict language matching**:
  - User chose **Java** → only copy code from `::: el-tab-pane label=Java` or ` ```java` blocks
  - User chose **Kotlin** → only copy code from `::: el-tab-pane label=Kotlin` or ` ```kotlin` blocks
  - User chose **Objective-C** → only copy code from `::: el-tab-pane label=Objective-C` or ` ```objc` blocks
  - User chose **Swift** → only copy code from `::: el-tab-pane label=Swift` or ` ```swift` blocks
  - **Prohibited**: copying from Java block into Kotlin file, or vice versa
  - **Prohibited**: copying from Objective-C block into Swift file, or vice versa
  - If wiki doc uses el-tabs format, first confirm the current language tab, then switch to correct tab to copy
- **Auto-track code**: ⚠️ **Must read `references/autotrack-enum.md` first** to look up the correct enum names and values for the target SDK, then copy the `EnableAutoTrack` call example from wiki. **Do not guess enum names or omit enum values**
- **Event track code**: property names and event names from plan, structure directly reused from wiki examples
- **User property code**: directly copy API call style from wiki doc
- **Super property code**: directly copy setSuperProperties call style from wiki doc

#### Step 3: Generate Code Snippets

Generate code snippets (markdown + files)

#### Step 3.5: ⚠️ Language Style Check (do not skip)

After generation, perform language style checks on each output file:

| Language | Check Rules |
|---|---|
| **Kotlin** | File must not contain `;` (trailing semicolons); fix immediately and inform user if found |
| **Java** | Every statement must end with `;`; fix immediately if missing |
| **Swift** | Do not use `var` for optional types — use `let` + `?`; do not use `@objc` unless necessary |
| **Objective-C** | Method calls must use `[self method]` syntax — no `.` calls; must use `nil`, not `null` |

**If language style errors are found**:
1. Immediately replace with correct syntax
2. Note in the response: `⚠️ Auto-corrected: <error description> → <correct syntax>`

#### Step 4: Server-side Additional Processing

1. Additionally generate `daemon.json` for server-side
2. **Must always provide LogBus2 official documentation link**

#### Step 5: Upload Generated Artifacts

Prepare upload compatibility copies for unsupported code/config extensions, then upload the safe file list to the Agent attachment library using `ae-cli agent +add-attachment --files '<json-array>'`.

---

## Code Style

- Event names / property names strictly from plan, do not modify
- Add comment above each code block describing trigger timing
- Do NOT add try/catch
- User identity calls: `login()` / `identify()` generated based on `meta.user_identity`

### Property Placeholder Value Rules (based on plan `type` field)

When generating property value placeholders, **must select the correct type placeholder based on the property's `type` field in the plan**. Do not use string placeholders uniformly for all types:

| plan `type` | Placeholder | Notes |
|---|---|---|
| `string` | `"\"<actual value>\""` | String placeholder |
| `number` | `0` | Numeric placeholder (**`userAdd` must use numeric**; string causes runtime error) |
| `bool` | `true` / `false` | Boolean placeholder (**do NOT use string `"\"<actual value>\""`**, type mismatch) |
| `datetime` | `new Date()` / platform-specific syntax | Datetime placeholder |
| `array_string` | `["example"]` | Array placeholder |
| `array_row` | `[{"key":"example"}]` | Object array placeholder |

**Platform-specific datetime placeholder syntax**:

| Platform | Syntax |
|---|---|
| Android Java | `new Date()` |
| Android Kotlin | `Date()` |
| iOS Objective-C | `[NSDate date]` |
| iOS Swift | `Date()` |
| JavaScript | `new Date()` |
| Java Server | `new Date()` |
| Python | `datetime.datetime.now()` |
| Go | `time.Now()` |
| Node.js | `new Date()` |

### ⚠️ Server SDK track() Parameter Order (varies by SDK; do not assume uniform ordering)

For server-side SDK `track()` calls, **accountId and distinctId parameter positions differ across SDKs**. Generate code using each SDK's actual parameter order:

| SDK | Positional Parameter Order | Recommended Approach |
|---|---|---|
| Java | `track(accountId, distinctId, eventName, properties)` | Positional ✅ |
| Go | `Track(accountId, distinctId, eventName, properties)` | Positional ✅ |
| **Python** | **`track(distinct_id, account_id, eventName, properties)`** — **distinct_id first** | **Prefer keyword args** ✅ |
| Node.js | Single object param `{accountId, distinctId, event, ...}` | Object arg ✅ |

**Python SDK strongly recommends keyword args** to avoid positional order confusion:
```python
te.track(account_id="<Account ID>", distinct_id="<Visitor ID>", event_name="order_create", properties={...})
```

Similarly, Python `user_set` / `user_setOnce` / `user_add` should use keyword args:
```python
te.user_set(account_id="<Account ID>", distinct_id="<Visitor ID>", properties={...})
```

### ⚠️ JavaScript SDK Examples (correct vs incorrect comparison)

**Init code directly copied from wiki** (includes correct import and package name):

```js
// ✅ Correct: directly copied from wiki javascript.md
import ta from "thinkingdata-browser";
ta.init({
  appId: "YOUR_APP_ID",
  serverUrl: "https://YOUR_SERVER_URL/sync_js",
  autoTrack: {
    pageShow: true,
    pageHide: true,
  }
});
```

**❌ Incorrect examples (absolutely prohibited)**:

```js
// ❌ Wrong: guessed package name and import syntax
import TDAnalytics from "@thinkingdata/web-sdk";  // package name is wrong
TDAnalytics.init({...});  // class name is wrong

// ❌ Wrong: using generic variable names like te or analytics
import te from "thinkingdata-browser";  // wiki has never used te
te.init({...});
```

**Key points**:
- npm package name: `thinkingdata-browser` (NOT `@thinkingdata/web-sdk`, NOT `thinkingdata`)
- import variable name: `ta` (NOT `TDAnalytics`, NOT `te`)
- init method: `ta.init({...})` (NOT `TDAnalytics.init()`)
