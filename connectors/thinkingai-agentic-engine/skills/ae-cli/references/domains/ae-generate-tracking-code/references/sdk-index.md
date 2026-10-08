# SDK Document Path Index

> **Terminology**: 文档路径索引 = document path index | 主文档 = main document (latest, authoritative) | 历史版本文档 = historical/versioned document (ignore) | 进阶指南 = advanced guide | 预置属性 = preset properties | 自动采集 = auto-track

> This index points to authoritative wiki documents for the skill to reference during code generation.
> The wiki directory is maintained by `ae-cli tracking wiki` and synced from AE official documentation.

---

## ⚠️ Important: Document Reading Priority

**When generating code, must prioritize reading the "main document". Do NOT read historical/versioned documents!**

| 优先级 | 文档类型 | 说明 |
|---|---|---|
| 🔴 **最高** | Main doc (e.g. `android.md`) | Latest SDK guide with correct API |
| 🟡 中等 | Advanced, Auto-track, Preset Props | Supplementary info |
| ⚫ **忽略** | Historical docs | Outdated, may use incompatible API |

**Directory naming**:
- `xxx.md` — latest main doc (read first)
- `xxx-advanced.md` — supplementary guide
- `advanced/` — supplementary sub-pages

---

## 客户端 SDK

### 原生移动端

| SDK | Main Doc | Advanced | Auto-track | Preset Props |
|---|---|---|---|---|
| Android | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/android.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/android/android-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/android/android-advanced/automatic-event-tracking.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/android/android-advanced/preset-properties.md` |
| iOS | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/ios.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/ios/ios-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/ios/ios-advanced/automatic-event-tracking.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/ios/ios-advanced/preset-properties.md` |

### Web / H5

| SDK | Main Doc | Advanced | Auto-track |
|---|---|---|---|
| JavaScript | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/javascript.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/javascript/javascript-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/javascript/javascript-advanced/automatic-event-tracking.md` |

### Mini Program & Mini Game (zh-CN only)

| SDK | Main Doc | Advanced | Auto-track |
|---|---|---|---|
| 小程序小游戏 | `~/.ae-cli/wiki/raw/客户端-sdk/小程序小游戏.md` | `~/.ae-cli/wiki/raw/客户端-sdk/小程序小游戏/进阶指南.md` | `~/.ae-cli/wiki/raw/客户端-sdk/小程序小游戏/进阶指南/自动采集.md` |

### Game Engines

| SDK | Version | Main Doc | Advanced | Auto-track |
|---|---|---|---|---|
| Unity | v3.x | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unity.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unity/unity-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unity/unity-advanced/automatic-event-tracking.md` |
| Unreal | v2.x | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unreal.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unreal/unreal-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unreal/unreal-advanced/automatic-event-tracking.md` |
| Cocos2d-x | v2.x | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocos2d-x.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocos2d-x/cocos2d-x-advanced.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocos2d-x/cocos2d-x-advanced/automatic-event-tracking.md` |
| CocosCreator | v2.x | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocoscreator.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocoscreator/cocoscreator-advance.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocoscreator/cocoscreator-advance/automatic-event-tracking.md` |
| Cocos2d-Lua (zh-CN) | v2.x | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/cocos2d-lua.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/cocos2d-lua/进阶指南.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/cocos2d-lua/进阶指南/自动采集.md` |
| LayaAir (zh-CN) | v2.x | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/layaair.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/layaair/进阶指南.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/layaair/进阶指南/自动采集.md` |
| Egret (zh-CN) | v2.x | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/egret.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/egret/进阶指南.md` | `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/egret/进阶指南/自动采集.md` |

**Note**: Unity SDK upgraded from v2.x to v3.x with significant API changes:
- v2.x API: `ThinkingAnalyticsAPI.Track()`
- v3.x API: `TDAnalytics.Track()`
- Main doc `unity.md` = v3.x; historical docs removed from v6.0

### Cross-Platform

| SDK | Main Doc | Advanced |
|---|---|---|
| React Native | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/react-native.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/react-native/reactnative-advanced.md` |
| Flutter | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/flutter.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/flutter/flutter-advanced.md` |
| uni-app | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/uni-app.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/cross-platform/uni-app/uniapp-advanced.md` |
| OpenHarmony (zh-CN) | `~/.ae-cli/wiki/raw/客户端-sdk/openharmony.md` | `~/.ae-cli/wiki/raw/客户端-sdk/openharmony/进阶指南.md` |

---

## Server SDK

| Language | Main Doc | Advanced |
|---|---|---|
| Java | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/java.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/java/java-advanced.md` |
| Python | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/python.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/python/python-advanced.md` |
| Golang | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/golang.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/golang/golang-advanced.md` |
| Node.js | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/nodejs.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/nodejs/nodejs-advanced.md` |
| PHP | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/php.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/php/php-advanced.md` |
| C# | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/c-V2W3wv.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/c/c-advanced-IauKwI.md` |
| C++ | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/c-Zf9Jwl.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/c/c-advanced-YAilwk.md` |
| Ruby | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/ruby.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/ruby/ruby-advanced.md` |
| Lua | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/lua.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/lua/lua-advanced.md` |
| Erlang | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/erlang.md` | `~/.ae-cli/wiki/raw/data-ingestion-guide/server-sdk/erlang/erlang-advanced.md` |

---

## Data Import Tools

| Tool | Doc Path | Description |
|---|---|---|
| **LogBus2** | `~/.ae-cli/wiki/raw/data-ingestion-guide/data-import-tools/logbus2-user-guide.md` | Recommended, paired with LoggerConsumer |
| DataX Writer | `~/.ae-cli/wiki/raw/data-ingestion-guide/data-import-tools/ta-datax-writer-plugin-user-guide.md` | Database batch import |
| RESTful API | `~/.ae-cli/wiki/raw/data-ingestion-guide/restful-api-user-guide.md` | Direct HTTP upload |

**Note: LogBus v1 is deprecated. Use LogBus2 for all scenarios.**

Official docs:
- Guide: https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US

---

## Preset Properties & System Fields

| Doc | Path |
|---|---|
| Preset Properties & System Fields | `~/.ae-cli/wiki/raw/preparations-before-data-ingestion/preset-properties-and-system-fields.md` |
| User Identification Rules | `~/.ae-cli/wiki/raw/preparations-before-data-ingestion/user-identification-rules.md` |
| Data Rules | `~/.ae-cli/wiki/raw/preparations-before-data-ingestion/data-rules.md` |

---

## Synthesized Docs (Overview)

LLM-synthesized overview docs from multiple raw sources:

| Synthesis Doc | Path | Description |
|---|---|---|
| Server SDK Overview | `~/.ae-cli/wiki/synthesis/server-sdk-overview.md` | Unified architecture of all server SDKs |
| SDK Selection Guide | `~/.ae-cli/wiki/synthesis/sdk-selection.md` | How to choose the right SDK |
| RESTful API Reference | `~/.ae-cli/wiki/synthesis/restful-api-reference.md` | RESTful API summary |
| JS SDK Cheatsheet | `~/.ae-cli/wiki/synthesis/js-sdk-cheatsheet.md` | JavaScript SDK quick reference |
| Batch Ingestion Comparison | `~/.ae-cli/wiki/synthesis/batch-ingest-comparison.md` | LogBus / DataX / Kafka comparison |
