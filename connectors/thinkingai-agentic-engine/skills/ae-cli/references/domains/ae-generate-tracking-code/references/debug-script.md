# Mode F — Debug / Validation Script

> **Terminology**: 校验脚本 = validation/debug script | 设备绑定 = device binding | Debug 模式 = debug mode | TDDebugConsumer = debug mode consumer (validates data format, does NOT persist to production) | 实时调试 = real-time debugging | 代表业务事件 = representative business events | SDK 日志打印 = SDK log printing

## Deliverable

`te-debug.<ext>` single file; used to quickly verify SDK configuration is correct.

---

## Debug Mode Verification

When using debug mode, register and select the debug device with `ae-cli` before sending events. The Agent can then query the received Debug data directly, without asking the user to return to the AE page.

### Verification Steps

| Step | Action                                                                                                                                             |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | List devices: `ae-cli tracking debug-device list --project-id <project_id>`                                                                        |
| 2    | Add the script's device ID when missing: `ae-cli tracking debug-device add --project-id <project_id> --device-id <device_id> --device-name <name>` |
| 3    | Select it: `ae-cli tracking debug-device select --project-id <project_id> --device-id <device_id>`                                                 |
| 4    | Run the debug script to send test events                                                                                                           |
| 5    | Query received data: `ae-cli tracking debug-data list --project-id <project_id> --device-id <device_id>`                                           |
| 6    | If needed, filter one event with `--event-name <event_name>` or inspect it in AE at `https://<host>/#/data/debug`                                  |

### Common Notes for Client and Server SDKs

- Both use **TDDebugConsumer** (or the platform's equivalent debug mode API)
- Both require registering the same device ID with `ae-cli tracking debug-device add`
- On validation failure, the SDK prints error logs or throws exceptions (behavior varies by language)
- `debug-data list` defaults to the most recent hour and returns `has_data`, `event_count`, `data_count`, and the raw Debug records
- Treat `has_data: true` as evidence that the receiver got Debug data; also inspect each record's error fields before declaring validation successful

---

## Debug Mode API by Platform

### Client SDK

| SDK              | Debug Mode API                                                                                                                                    | Reference Doc                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Unity SDK        | `TDConfig config = new TDConfig(appId, serverUrl); config.mode = TDMode.DEBUG; TDAnalytics.Init(config);`                                         | `data-ingestion-guide/client-sdk/game-engine/unity/unity-advanced/debugging-and-logging.md`                 |
| Android SDK      | `TDConfig config = new TDConfig(this, serverUrl, appId); config.setMode(TDConfig.Mode.DEBUG); TDAnalytics.init(this, config);`                    | `data-ingestion-guide/client-sdk/android/android-advanced/debugging-and-logging.md`                         |
| iOS SDK          | `TDConfig *config = [[TDConfig alloc] initWithAppId:appId serverUrl:serverUrl]; config.mode = TDModeDebug; [TDAnalytics startWithConfig:config];` | `data-ingestion-guide/client-sdk/ios/ios-advanced/debugging-and-logging.md`                                 |
| JavaScript SDK   | `ta.init({ appId: appId, server_url: serverUrl, debug: true });`                                                                                  | `data-ingestion-guide/client-sdk/javascript/javascript-advanced/debugging-and-logging.md`                   |
| Mini Program SDK | `ta.init({ appId: appId, server_url: serverUrl, debug: true });`                                                                                  | `客户端-sdk/小程序小游戏/进阶指南/实时调试.md`                                                              |
| CocosCreator     | See doc                                                                                                                                           | `data-ingestion-guide/client-sdk/game-engine/cocoscreator/cocoscreator-advance/debugging-and-logging.md`    |
| Cocos2d-x        | See doc                                                                                                                                           | `data-ingestion-guide/client-sdk/game-engine/cocos2d-x/cocos2d-x-advanced/debugging-and-logging.md`         |
| Unreal SDK       | See doc                                                                                                                                           | `data-ingestion-guide/client-sdk/game-engine/unreal/unreal-advanced/debugging-and-logging.md`               |
| Flutter SDK      | See doc                                                                                                                                           | `data-ingestion-guide/client-sdk/cross-platform/flutter/flutter-advanced/debugging-and-logging.md`          |
| React Native     | See doc                                                                                                                                           | `data-ingestion-guide/client-sdk/cross-platform/react-native/reactnative-advanced/debugging-and-logging.md` |

### Server SDK

| Language | DebugConsumer API                                                       | Reference Doc                                                                     |
| -------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Java     | `new TDDebugConsumer(serverUrl, appId, deviceId)`                       | `data-ingestion-guide/server-sdk/java/java-advanced/debugging-and-logging.md`     |
| Python   | `TDDebugConsumer(serverUrl, appId, device_id="...")`                    | `data-ingestion-guide/server-sdk/python/python-advanced/debugging-and-logging.md` |
| Go       | `NewDebugConsumerWithDeviceId(serverUrl, appId, false, deviceId)`       | `data-ingestion-guide/server-sdk/golang/golang-advanced/debugging-and-logging.md` |
| Node.js  | `ThinkingData.initWithDebugMode(appId, serverUrl, { deviceId: "..." })` | `data-ingestion-guide/server-sdk/nodejs/nodejs-advanced/debugging-and-logging.md` |
| PHP      | `new TDDebugConsumer(serverUrl, appId, deviceId)`                       | `data-ingestion-guide/server-sdk/php/php-advanced/debugging-and-logging.md`       |
| Ruby     | `TDDebugConsumer.new(serverUrl, appId, deviceId)`                       | `data-ingestion-guide/server-sdk/ruby/ruby-advanced/debugging-and-logging.md`     |
| Erlang   | `tddebug_consumer:new(ServerUrl, AppId, DeviceId)`                      | `data-ingestion-guide/server-sdk/erlang/erlang-advanced/debugging-and-logging.md` |
| Lua      | `TDDebugConsumer.new(serverUrl, appId, deviceId)`                       | `data-ingestion-guide/server-sdk/lua/lua-advanced/debugging-and-logging.md`       |
| C        | `td_debug_consumer_new(serverUrl, appId, deviceId)`                     | `data-ingestion-guide/server-sdk/c/c-advanced/debugging-and-logging.md`           |

---

## Skill Generation Checkpoints

When generating a debug script, the skill must:

1. **First read the corresponding SDK's "Real-time Debug" doc** (see reference doc paths below) to confirm the SDK's debug mode API and usage (the table above is an index reference only; actual usage may differ)
2. Use the corresponding platform's **TDDebugConsumer** or debug mode API
3. Set a stable `deviceId` (e.g. `agent-debug-<project_id>`) and register it with `ae-cli tracking debug-device add`
4. Read `SERVER_URL` and `appId` from plan (NOT web host)
5. Pick 3 representative business events from plan (if object array properties exist, construct them fully)
6. Recommend enabling SDK log printing (for easier troubleshooting)
7. File name must match class name (e.g. Unity: `TEDebugScript.cs`)

### Post-delivery Prompt

**Platform filtering notes**:

- xlsx "Platform" column values map to `platform` field:
  - `客户端` / `client` → `platform: "client"`
  - `服务端` / `server` → `platform: "server"`
  - `客户端,服务端` / `client,server` → `platform: "both"`
- Client debug script: only include events where `platform === "client"` or `platform === "both"`
- Server debug script: only include events where `platform === "server"` or `platform === "both"`
- If xlsx has no platform column: include all events (backward compatible)

```
Verification steps:
1. Run `ae-cli tracking debug-device list --project-id <project_id>`.
2. If needed, run `ae-cli tracking debug-device add --project-id <project_id> --device-id <device_id> --device-name <name>`.
3. Run `ae-cli tracking debug-device select --project-id <project_id> --device-id <device_id>`.
4. Run the debug script.
5. Run `ae-cli tracking debug-data list --project-id <project_id> --device-id <device_id>`.
6. Confirm `has_data` is true and inspect error fields and event property structures.
7. If no data appears, retry with an explicit `--start-time "YYYY-MM-DD HH:mm:ss"` and verify that the script reports the exact same device ID.
```

### Reference Doc Paths

All SDK debug/logging docs are located at:

- `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/<sdk>/<sdk>-advanced/debugging-and-logging.md`
- `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/<language>/<language>-advanced/debugging-and-logging.md`

For zh-CN only SDKs (Mini Program, LayaAir, etc.), refer to sdk-index.md for exact paths.
