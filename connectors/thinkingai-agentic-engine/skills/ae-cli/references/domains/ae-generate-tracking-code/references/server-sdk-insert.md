# Server-side Code Insertion (LoggerConsumer + LogBus2)

> **Terminology**: 服务端 SDK = server-side SDK | 代码插入 = code insertion/injection | LoggerConsumer = writes events to local log files (recommended for production) | LogBus2 = log sync tool that reads local logs and uploads to TE | 架构 = architecture | 异步上报 = async upload | 批量上传 = batch upload | 重试策略 = retry strategy | 公共属性 = super property (公共事件属性; never "超级属性") | 用户属性 = user property | 依赖管理 = dependency management

## Architecture

Server-side SDK uses the recommended LoggerConsumer + LogBus2 architecture:

```
Server code → LoggerConsumer → Local log files (/data/ta_log/)
                                    ↓
                              LogBus2 process → AE platform
```

**Note: LogBus v1 is deprecated. Use LogBus2 exclusively.**

Official docs:
- User guide: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US
- Download link is in the official doc's "二、Download LogBus2" section

Advantages:
- Data reliability (local log persistence, resilient to network fluctuations)
- Async upload (doesn't block business logic)
- Batch upload (high network efficiency)
- Controllable retry (LogBus2 configures retry strategy)

---

## Stage 0: Wiki

1. Read `references/sdk-index.md` to find the server SDK's wiki path
2. Read wiki main doc (initialization, LoggerConsumer configuration)
3. Read wiki advanced guide (user properties, batch upload, etc.)

### Stage 0.5: SDK Integration Confirmation (must execute after Stage 0)

Based on the selected SDK, identify the dependency management method (Maven / pip / go get / npm / composer, etc.), then confirm with user:

**Integration methods that require code changes (Maven / pip / go get / npm / composer, etc.)**:

```
Server-side <language> SDK detected. Dependency config changes needed.

Should I modify the config file directly to add SDK dependencies?
- yes → Edit the config file (e.g. pom.xml / requirements.txt / go.mod / package.json / composer.json), then proceed to Stage 1
- no → Reference the docs below to complete SDK integration, then reply yes to continue

Documentation: <wiki doc path>
```

- User `yes` → Execute Edit on config file, then proceed to Stage 1
- User `no` → Display doc path, pause and wait for user completion

**Integration methods that don't require code changes (manual JAR download / file placement, etc.)**:

```
Please reference the docs below to complete SDK integration, then reply yes to continue.

Documentation: <wiki doc path>
```

Wait for user confirmation, then proceed to Stage 1.

---

## Stage 1: Explore

1. Grep entry points: `src/main.*`, `App.*`, `Application.*` (Java), `main.go` (Go)
2. Grep existing tracking: `TaAnalytics|TDAnalytics|thinkingdata|// @tracking`
3. Grep business logic locations: `(createOrder|handlePayment|userRegister)` etc. (based on plan events)
4. Confirm log directory: recommends `/data/ta_log/` or `/var/log/ae-tracking/`

---

## Stage 2: Insertion Plan (markdown table)

**Platform filtering**:
- xlsx "Platform" value `服务端` / `server` → `platform: "server"` (server-only collection)
- xlsx "Platform" value `客户端,服务端` / `client,server` → `platform: "both"` (both platforms)
- xlsx "Platform" value `客户端` / `client` → `platform: "client"` (client-only, do NOT generate in server)
- Only insert events where `platform === "server"` or `platform === "both"`

```
## SDK Initialization (LoggerConsumer)
- File: <path>:<line>
- Code: TaAnalytics.init(new LoggerConsumer("/data/ta_log/"))

## Super Properties
- File: <path>:<line>
- setSuperProperties({...})

## User Properties
- File: <path>:<line>
- user_set / user_setOnce / user_add

## Event Group: <tag>
- <event_name>: <file>:<symbol> or SKIP (already present)
- ...

## LogBus2 Configuration
- File: (outside project) `.ae-cli/output/daemon.json`
```

After showing, ask user `ok` to enter Stage 3, or "go back to event X to remap".

---

## Stage 3: Batched Edit

### Batch 1: SDK init (LoggerConsumer)

```java
// Java example
TaAnalytics.init(new LoggerConsumer("/data/ta_log/")
    .setRotateMode(LoggerConsumer.RotateMode.DAILY)
    .setRotateSize(1024 * 1024 * 100)); // 100MB
```

Insertion point: entry file static block / start of main function

### Batch 2: Super Properties + User Properties

Generate based on `meta.user_identity`:
- `user_set` / `user_setOnce`: user property upload
- `login()` call: on user login

### Batch 3..N: Events grouped by event_tag

Insert track calls at corresponding business logic locations for each event.

Each batch: use Edit tool; print file list + added line count after completion, ask `ok / undo`.

---

## Stage 4: LogBus2 Configuration Generation

Additionally generate `.ae-cli/output/daemon.json` (NOT written to user project):

```json
{
  "datasource": [
    {
      "type": "file",
      "file_patterns": [
        "/data/ta_log/*.log"
      ],
      "app_id": "<appId>",
      "unit_remove": "day",
      "offset_remove": 7
    }
  ],
  "push_url": "<SERVER_URL>"
}
```

**Always provide official docs** (for customer download and deployment):

```
LogBus2 official documentation:
- User guide: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US
- Download link is in the official doc's "二、Download LogBus2" section

Note: LogBus v1 is deprecated. Please use LogBus2.
```

---

## Stage 5: Summary

- Print all modified files + newly added events per file
- Print LogBus2 config file path (daemon.json)
- **Always provide LogBus2 official documentation link**
- Guide user to start LogBus2:
  1. Copy `daemon.json` to LogBus2 `conf/` directory
  2. Run `./logbus start`
- Suggest user consider running debug mode for verification

---

## Code Style

- LoggerConsumer singleton: create `src/lib/TeTracking.java` (if not exists)
- Prefix each track call with `// @tracking <event_name>` comment
- Log path: `/data/ta_log/` (Linux) or `C:\ta_log\` (Windows)
- Do NOT add try/catch (LoggerConsumer is fault-tolerant on its own)
- Event names / property names strictly from plan, do not modify

---

## Pre-check

- `git status --porcelain` not empty → refuse, prompt user to commit/stash first

---

## LoggerConsumer Configuration by Language

| Language | LoggerConsumer Class | Log Format |
|---|---|---|
| Java | `LoggerConsumer` | JSON line |
| Python | `TaLoggerConsumer` | JSON line |
| Go | `LoggerConsumer` | JSON line |
| Node.js | `LoggerConsumer` | JSON line |
| PHP | `TE_LoggerConsumer` | JSON line |

See wiki SDK docs for details.
