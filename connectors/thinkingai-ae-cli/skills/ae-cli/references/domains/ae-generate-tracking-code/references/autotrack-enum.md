# Auto-track Event Enum Reference

> **Terminology**: 自动采集事件 = auto-track event | 枚举值 = enum value | 上报事件名 = reported event name | bit = bit flag | SDK 初始化后开启 = enable after SDK init | 猜测 = guess (prohibited — always lookup from this table)

> Used by `snippet-delivery.md` / `client-sdk-insert.md` when generating auto-track event switch code.
> **Must copy from wiki docs directly** — do not guess enum values.

---

## Unity SDK（v3.x）— `TDAutoTrackEventType`

| 枚举值 | 上报事件名 | bit |
|---|---|---|
| `TDAutoTrackEventType.None` | (禁用) | `0` |
| `TDAutoTrackEventType.AppStart` | `ta_app_start` | `1 << 0` |
| `TDAutoTrackEventType.AppEnd` | `ta_app_end` | `1 << 1` |
| `TDAutoTrackEventType.AppCrash` | `ta_app_crash` | `1 << 4` |
| `TDAutoTrackEventType.AppInstall` | `ta_app_install` | `1 << 5` |
| `TDAutoTrackEventType.AppSceneLoad` | `ta_scene_loaded` | `1 << 6` |
| `TDAutoTrackEventType.AppSceneUnload` | `ta_scene_unloaded` | `1 << 7` |
| `TDAutoTrackEventType.All` | 全部 | OR 组合 |

**微信小游戏特殊映射**：

| 枚举值 | 上报事件名 |
|---|---|
| `TDAutoTrackEventType.AppStart` | `ta_mg_show` |
| `TDAutoTrackEventType.AppEnd` | `ta_mg_hide` |
| `TDAutoTrackEventType.AppInstall` | `ta_mg_launch` |

**代码示例**（从 wiki 直接复制）：

```csharp
// 开启全部自动采集事件
TDAnalytics.EnableAutoTrack(TDAutoTrackEventType.All);

// 开启启动和关闭事件的自动采集
TDAnalytics.EnableAutoTrack(TDAutoTrackEventType.AppStart | TDAutoTrackEventType.AppEnd);
```

---

## Android SDK — `TDAnalytics.TDAutoTrackEventType`

| 枚举值 | 上报事件名 |
|---|---|
| `TDAnalytics.TDAutoTrackEventType.APP_START` | `ta_app_start` |
| `TDAnalytics.TDAutoTrackEventType.APP_END` | `ta_app_end` |
| `TDAnalytics.TDAutoTrackEventType.APP_INSTALL` | `ta_app_install` |
| `TDAnalytics.TDAutoTrackEventType.APP_VIEW_SCREEN` | `ta_app_view` |
| `TDAnalytics.TDAutoTrackEventType.APP_CLICK` | `ta_app_click` |
| `TDAnalytics.TDAutoTrackEventType.APP_CRASH` | `ta_app_crash` |

**代码示例**（从 wiki 直接复制）：

```java
TDAnalytics.enableAutoTrack(TDAnalytics.TDAutoTrackEventType.APP_START | TDAnalytics.TDAutoTrackEventType.APP_END
    | TDAnalytics.TDAutoTrackEventType.APP_INSTALL | TDAnalytics.TDAutoTrackEventType.APP_VIEW_SCREEN
    | TDAnalytics.TDAutoTrackEventType.APP_CLICK | TDAnalytics.TDAutoTrackEventType.APP_CRASH);
```

---

## iOS SDK — `TDAutoTrackEventType`

**⚠️ iOS 枚举名与 Android/Unity 不同，必须使用 iOS SDK 实际的驼峰命名，不得照搬 Android 的 `APP_START` 下划线格式。**

| Objective-C 枚举值 | Swift 枚举值 | 上报事件名 |
|---|---|---|
| `TDAutoTrackEventTypeAppStart` | `.appStart` | `ta_app_start` |
| `TDAutoTrackEventTypeAppEnd` | `.appEnd` | `ta_app_end` |
| `TDAutoTrackEventTypeAppInstall` | `.appInstall` | `ta_app_install` |
| `TDAutoTrackEventTypeAppViewScreen` | `.appViewScreen` | `ta_app_view` |
| `TDAutoTrackEventTypeAppClick` | `.appClick` | `ta_app_click` |
| `TDAutoTrackEventTypeAppCrash` | `.appCrash` | `ta_app_crash` |

**快捷枚举（开启全部）**：

| Objective-C | Swift |
|---|---|
| `TDAutoTrackEventTypeAll` | `.all` |

**Objective-C 代码示例**（从 wiki 直接复制）：

```objc
// 开启全部自动采集事件（快捷方式）
[TDAnalytics enableAutoTrack:TDAutoTrackEventTypeAll];

// 或逐个开启
[TDAnalytics enableAutoTrack:TDAutoTrackEventTypeAppInstall
    | TDAutoTrackEventTypeAppStart
    | TDAutoTrackEventTypeAppEnd
    | TDAutoTrackEventTypeAppViewScreen
    | TDAutoTrackEventTypeAppClick
    | TDAutoTrackEventTypeAppCrash];
```

**Swift 代码示例**：

```swift
// 开启全部自动采集事件（快捷方式）
TDAnalytics.enableAutoTrack(.all)

// 或逐个开启
TDAnalytics.enableAutoTrack([.appStart, .appEnd, .appInstall, .appViewScreen, .appClick, .appCrash])
```

---

## JavaScript SDK（H5）— `autoTrack` 配置对象

| 配置项 | 说明 |
|---|---|
| `autoTrack.pageShow` | 页面显示（对应 `ta_page_show`） |
| `autoTrack.pageHide` | 页面隐藏（对应 `ta_page_hide`） |
| `autoTrack.appHide` | App 隐藏（微信小程序） |

**代码示例**（从 wiki 直接复制）：

```js
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

**单独开启**（调用 quick）：

```js
ta.quick("autoTrack");
```

---

## 微信小程序 SDK — `autoTrack` 配置对象

| 配置项 | 说明 |
|---|---|
| `autoTrack.mpLaunch` | 初始化（`ta_mp_launch`） |
| `autoTrack.mpShow` | 启动（`ta_mp_show`） |
| `autoTrack.mpHide` | 隐藏（`ta_mp_hide`） |
| `autoTrack.mpView` | 页面浏览（`ta_mp_view`） |
| `autoTrack.mpShare` | 转发（`ta_mp_share`） |
| `autoTrack.mpClick` | 点击（`ta_mp_click`） |
| `autoTrack.addFavorite` | 收藏（`ta_add_favorite`） |

---

## OpenHarmony SDK — `TDAutoTrackEventType`

| 枚举值 | 上报事件名 |
|---|---|
| `TDAutoTrackEventType.APP_START` | `ta_app_start` |
| `TDAutoTrackEventType.APP_END` | `ta_app_end` |
| `TDAutoTrackEventType.APP_INSTALL` | `ta_app_install` |
| `TDAutoTrackEventType.APP_VIEW_SCREEN` | `ta_app_view` |
| `TDAutoTrackEventType.APP_CLICK` | `ta_app_click` |
| `TDAutoTrackEventType.APP_CRASH` | `ta_app_crash` |

**代码示例**（从 wiki 直接复制）：

```typescript
TDAnalytics.enableAutoTrack(context,
  TDAutoTrackEventType.APP_START | TDAutoTrackEventType.APP_INSTALL
  | TDAutoTrackEventType.APP_END | TDAutoTrackEventType.APP_VIEW_SCREEN
  | TDAutoTrackEventType.APP_CLICK | TDAutoTrackEventType.APP_CRASH
);
```

---

## Cocos2d-x / CocosCreator / LayaAir / Unreal

游戏引擎 SDK 的自动采集枚举值请直接读取对应 wiki 文档：
- `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocos2d-x/cocos2d-x-advanced/automatic-event-tracking.md`
- `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/cocoscreator/cocoscreator-advance/automatic-event-tracking.md`
- `~/.ae-cli/wiki/raw/客户端-sdk/游戏引擎/layaair/进阶指南/自动采集.md`
- `~/.ae-cli/wiki/raw/data-ingestion-guide/client-sdk/game-engine/unreal/unreal-advanced/automatic-event-tracking.md`
