# Output Mode Architecture

> **Terminology**: 输出方式 = output mode | 插入 = insert (inject into project) | 片段 = snippet (code file delivery) | 产物 = deliverable/output | 端/平台 = platform | 项目路径 = project path (absolute) | LoggerConsumer = writes events to local log files | LogBus2 = log sync tool | 校验脚本 = validation/debug script

## Core Choice (per platform)

| Output Mode | Description | Parameters | Deliverables |
|---|---|---|---|
| **insert** | Direct Edit injection into user project | Requires project path (absolute) | Code written to target directory |
| **snippet** | Markdown print + generate code file | No path needed | `.ae-cli/output/<platform>-sdk.<ext>` |

---

## Server-side Defaults

Server-side always gets the following regardless of `insert` or `snippet`:

| Deliverable | Description |
|---|---|
| LoggerConsumer code | Server SDK writes to local log files |
| `.ae-cli/output/daemon.json` | LogBus2 config (reads logs and uploads to TE) |

**Note: LogBus v1 is deprecated. Use LogBus2 for all scenarios.**

Official docs:
- User guide: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US
- Download link is in the official doc's "二、Download LogBus2" section

**Architecture**:
```
Server code → LoggerConsumer → Local log files
                                    ↓
                              LogBus2 process → AE platform
```

Advantages:
- Data reliability (local log persistence)
- Async upload (doesn't block business logic)
- Batch upload (high network efficiency)

---

## Standalone Options (reserved)

| Option | Description | Deliverable |
|---|---|---|
| `datax` | Database batch import | `.ae-cli/output/datax-job.json` + README |
| `restful` | RESTful API direct upload (HTTP POST) | `.ae-cli/output/restful-client.<ext>` |
| `debug` | Validation script | `.ae-cli/output/te-debug.<ext>` |

---

## SDK Integration Mode → Platform List

| SDK Integration Mode | Platform List |
|---|---|
| `client_only` | Client: [client_sdk_type] (e.g. `['android']`) |
| `server_only` | Server: [server_language] (e.g. `['java']`) |
| `both` | Client: [client_sdk_type], Server: [server_language] |

---

## Quick Selection

| Quick Option | Description |
|---|---|
| **Generate all as snippets** | All platforms use `snippet`, output all code files at once |

When to use:
- Not inside the project directory
- Just want to reference code structure
- Multi-platform one-shot output

---

## Constraints

- Any `insert` must check `git status` first; refuse if uncommitted changes exist
- Client code: only generate events where `platform === "client"` or `platform === "both"`
- Server code: only generate events where `platform === "server"` or `platform === "both"`
- Server defaults to LoggerConsumer + LogBus2, does NOT default to RESTful
- **Use LogBus2 only; do not use LogBus v1** (deprecated)
- When generating LogBus2 config, must always provide official documentation link (user guide + download address)
