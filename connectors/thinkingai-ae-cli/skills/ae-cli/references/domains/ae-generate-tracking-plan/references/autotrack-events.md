# SDK Auto-track Event Definitions (internal reference)

> **Terminology**: 自动采集事件 = auto-track event | 预置属性 = preset property (`#` prefix) | recommended = auto-injected events | optional = user opt-in events | 事件注入规则 = event injection rules | 触发条件 = trigger condition | 去重 = deduplication

> This file defines auto-track events for each platform SDK, used by the `ae-generate-tracking-plan` skill in Phase 2
> for auto-injection into the draft.

---

## Event Injection Rules

1. Select auto-track events based on `meta.sdk_type` for the corresponding platform
2. **By default, only inject `recommended` events**; `optional` events are not auto-injected; prompt user for optional enablement during Refine phase
3. Injected events marked `source: "autotrack"` to distinguish from `template/prd/chat`
4. Auto-track event properties only include preset properties (`#` prefix), no custom properties
5. Preset properties do not need to be defined in the `event_properties` pool; they are auto-collected by the SDK

### recommended vs optional 定义依据

依据各 SDK 主文档「最佳实践」章节的默认推荐事件集：
- Android/iOS/OpenHarmony 最佳实践：`APP_START` + `APP_END` + `APP_INSTALL`（3 个）
- Unity 最佳实践：`AppInstall` + `AppStart` + `AppEnd`（3 个）
- JavaScript 最佳实践：`pageShow` + `pageHide`（2 个）
- 微信小程序最佳实践：`appLaunch` + `appShow` + `appHide` + `pageShow` + `appShare`（5 个）
- OpenHarmony 最佳实践：全 6 个（wiki 示例为全量，但推荐分级与 Android 统一：3 个 recommended + 3 个 optional）

---

## Android SDK

### 事件列表

| 事件名 | 显示名 | 事件说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_app_install` | APP 安装 | APP 首次安装时上报，升级不触发，删除重装会触发 | — | ✅ recommended |
| `ta_app_start` | APP 启动 | 用户开启 APP 或从后台唤醒时触发 | `#resume_from_background`, `#start_reason`, `#background_duration` | ✅ recommended |
| `ta_app_end` | APP 关闭 | 用户关闭 APP 或将 APP 调至后台时触发 | `#duration` | ✅ recommended |
| `ta_app_view` | APP 页面浏览 | 用户浏览 Activity 时触发 | `#screen_name`, `#title`, `#url`, `#referrer` | ⚠️ optional |
| `ta_app_click` | APP 控件点击 | 用户点击控件时触发（量级大，Android 需额外 Gradle 插件） | `#screen_name`, `#title`, `#element_id`, `#element_type`, `#element_content`, `#element_position`, `#element_selector` | ⚠️ optional |
| `ta_app_crash` | APP 崩溃 | APP 出现未捕获异常时上报 | `#app_crashed_reason` | ⚠️ optional |

### Draft JSON 示例

```json
{
  "event_name": "ta_app_install",
  "display_name": "APP 安装",
  "event_desc": "APP 首次安装时上报，升级不触发，删除重装会触发",
  "event_tag": "系统事件",
  "prop_names": [],
  "source": "autotrack"
}
```

---

## iOS SDK

### 事件列表

与 Android SDK 一致，事件名相同：

| 事件名 | 显示名 | 事件说明 | 推荐 |
|---|---|---|---|
| `ta_app_install` | APP 安装 | APP 首次安装时上报 | ✅ recommended |
| `ta_app_start` | APP 启动 | 用户开启 APP 或从后台唤醒 | ✅ recommended |
| `ta_app_end` | APP 关闭 | 用户关闭 APP 或进入后台 | ✅ recommended |
| `ta_app_view` | APP 页面浏览 | 用户切换 ViewController | ⚠️ optional |
| `ta_app_click` | APP 控件点击 | 用户点击控件（量级大） | ⚠️ optional |
| `ta_app_crash` | APP 崩溃 | APP 出现未捕获异常 | ⚠️ optional |

### iOS 特有事件

| 事件名 | 显示名 | 说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_app_bg_start` | APP 后台启动 | APP 在后台启动时触发（需开启配置） | — | ⚠️ optional |

---

## OpenHarmony SDK

### 事件列表

与 Android SDK 事件名相同，推荐分级也与 Android SDK 一致：

| 事件名 | 显示名 | 事件说明 | 推荐 |
|---|---|---|---|
| `ta_app_install` | APP 安装 | APP 首次安装时上报 | ✅ recommended |
| `ta_app_start` | APP 启动 | 用户开启 APP 或从后台唤醒 | ✅ recommended |
| `ta_app_end` | APP 关闭 | 用户关闭 APP 或进入后台 | ✅ recommended |
| `ta_app_view` | APP 页面浏览 | 用户浏览页面时触发 | ⚠️ optional |
| `ta_app_click` | APP 控件点击 | 用户点击控件时触发 | ⚠️ optional |
| `ta_app_crash` | APP 崩溃 | APP 出现未捕获异常时上报 | ⚠️ optional |

---

## JavaScript SDK（Web / H5）

### 事件列表

| 事件名 | 显示名 | 事件说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_pageview` | 页面浏览 | 调用 `ta.quick("autoTrack")` 时上报 | `#url`, `#referrer`, `#title` | ⚠️ optional（需单独调用 `ta.quick("autoTrack")`，不通过 autoTrack 配置开启） |
| `ta_page_show` | 页面显示 | 页面显示时触发（需开启配置） | — | ✅ recommended |
| `ta_page_hide` | 页面隐藏 | 页面隐藏时触发（需开启配置） | `#duration` | ✅ recommended |

---

## 小程序 SDK

### 事件列表

| 事件名 | 显示名 | 事件说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_mp_launch` | 小程序初始化 | 小程序被首次打开时触发，进程生命周期内只触发一次 | `#scene`, `#start_reason` | ✅ recommended |
| `ta_mp_show` | 小程序启动 | 小程序被启动或从后台调回前台时触发 | `#scene`, `#url_path`, `#start_reason` | ✅ recommended |
| `ta_mp_hide` | 小程序隐藏 | 小程序被调入后台时触发 | `#scene`, `#duration` | ✅ recommended |
| `ta_mp_view` | 小程序页面浏览 | 页面被打开或从后台调回前台时触发 | `#scene`, `#url_path`, `#referrer` | ✅ recommended |
| `ta_mp_share` | 小程序转发分享 | 转发按钮被点击时触发 | `#scene`, `#url_path` | ✅ recommended |
| `ta_page_leave` | 小程序页面卸载 | 页面卸载时触发 | `#duration`, `#url_path` | ⚠️ optional |
| `ta_add_favorite` | 小程序页面收藏 | 页面被收藏时触发 | `#url_path` | ⚠️ optional |
| `ta_mp_click` | 小程序元素点击 | 页面元素被点击时触发（量级大） | `#element_id`, `#element_type`, `#element_content`, `#element_name` | ⚠️ optional |

### 平台支持矩阵

| 事件 | 微信小程序 | 微信小游戏 | 抖音小程序 | 支付宝小程序 | 其他小程序 |
|---|---|---|---|---|---|
| `ta_mp_launch` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ta_mp_show` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ta_mp_hide` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `ta_mp_view` | ✅ | ❌ | ✅ | ✅ | ✅ |
| `ta_mp_share` | ✅ | ❌ | ✅ | ✅ | 视平台 |
| `ta_page_leave` | ✅ | ❌ | ✅ | ✅ | 视平台 |
| `ta_add_favorite` | ✅ | ❌ | ❌ | ❌ | 视平台 |
| `ta_mp_click` | ✅ | ❌ | ✅ | ✅ | 视平台 |

---

## Unity SDK

### 事件列表

| 事件名 | 显示名 | 事件说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_app_install` | APP 安装 | 首次安装后打开时触发 | — | ✅ recommended |
| `ta_app_start` | APP 启动 | 游戏进入前台时触发 | `#resume_from_background` | ✅ recommended |
| `ta_app_end` | APP 关闭 | 游戏进入后台时触发 | `#duration` | ✅ recommended |
| `ta_scene_loaded` | 场景加载 | 游戏场景（Scene）加载时触发 | — | ⚠️ optional |
| `ta_scene_unloaded` | 场景卸载 | 游戏场景（Scene）卸载时触发 | — | ⚠️ optional |

### 微信小游戏特殊事件

| 事件名 | 显示名 | 说明 | 预置属性 | 推荐 |
|---|---|---|---|---|
| `ta_mg_launch` | 小游戏初始化 | 替代 `ta_app_install` | `#start_reason` | ✅ recommended |
| `ta_mg_show` | 小游戏启动 | 替代 `ta_app_start` | `#start_reason` | ✅ recommended |
| `ta_mg_hide` | 小游戏隐藏 | 替代 `ta_app_end` | `#duration` | ✅ recommended |

---

## 其他游戏引擎 SDK

### Cocos2d-x / CocosCreator / LayaAir

与 Unity SDK 一致，支持：
- `ta_app_install` / `ta_app_start` / `ta_app_end`

### Unreal SDK

| 事件名 | 显示名 | 说明 | 推荐 |
|---|---|---|---|
| `ta_app_install` | APP 安装 | 首次安装时触发 | ✅ recommended |
| `ta_app_start` | APP 启动 | 游戏进入前台 | ✅ recommended |
| `ta_app_end` | APP 关闭 | 游戏进入后台 | ✅ recommended |

---

## 跨平台框架

### React Native SDK

继承原生 SDK（iOS/Android）的自动采集事件。

### Flutter SDK

继承原生 SDK（iOS/Android）的自动采集事件。

### uni-app SDK

| 平台 | 自动采集事件 |
|---|---|
| 微信小程序 | 继承小程序 SDK 自动采集事件 |
| APP（iOS/Android） | 继承原生 SDK 自动采集事件 |
| H5 | 继承 JavaScript SDK 自动采集事件 |

---

## 预置属性定义

所有预置属性以 `#` 开头，由 SDK 自动采集。**预置属性不需要在埋点方案中定义**，
但需要了解其含义以便分析使用。

| 属性名 | 中文名 | 类型 | 适用事件 | 说明 |
|---|---|---|---|---|
| `#duration` | 事件时长 | number | `ta_app_end`, `ta_mp_hide`, `ta_page_hide` | 单位：秒 |
| `#resume_from_background` | 是否从后台唤醒 | bool | `ta_app_start` | true=后台唤醒，false=直接启动 |
| `#screen_name` | 页面名称 | string | `ta_app_view`, `ta_app_click` | Activity 类名 / ViewController 类名 |
| `#title` | 页面标题 | string | `ta_app_view`, `ta_app_click` | 页面标题 |
| `#url` | 页面地址 | string | `ta_app_view`, `ta_pageview` | 当前页面地址 |
| `#referrer` | 前向地址 | string | `ta_app_view`, `ta_mp_view`, `ta_pageview` | 跳转前页面地址 |
| `#url_path` | 页面路径 | string | 小程序事件 | 小程序页面路径 |
| `#element_id` | 元素 ID | string | `ta_app_click`, `ta_mp_click` | 控件 ID |
| `#element_type` | 元素类型 | string | `ta_app_click`, `ta_mp_click` | 控件类型 |
| `#element_content` | 元素内容 | string | `ta_app_click`, `ta_mp_click` | 控件上的内容 |
| `#element_position` | 元素位置 | string | `ta_app_click`, `ta_mp_click` | 控件位置信息 |
| `#element_selector` | 元素选择器 | string | `ta_app_click` | viewPath 拼接 |
| `#element_name` | 元素名称 | string | `ta_mp_click` | 小程序元素名称 |
| `#app_crashed_reason` | 异常信息 | string | `ta_app_crash` | 崩溃堆栈信息 |
| `#scene` | 场景值 | number | 小程序事件 | 小程序启动场景值 |
| `#start_reason` | 启动原因 | string | `ta_app_start`, `ta_mp_launch`, `ta_mp_show` | JSON 字符串，启动来源信息 |
| `#background_duration` | 后台停留时长 | number | `ta_app_start` | 单位：秒 |

---

## SDK 类型 → 自动采集事件映射

```typescript
type SDKType =
  | 'android'
  | 'ios'
  | 'openharmony'
  | 'javascript'
  | 'wechat_mp'      // 微信小程序
  | 'wechat_mg'      // 微信小游戏
  | 'douyin_mp'      // 抖音小程序
  | 'alipay_mp'      // 支付宝小程序
  | 'unity'
  | 'unity_wxmg'     // Unity 微信小游戏
  | 'cocos2dx'
  | 'cocoscreator'
  | 'layaair'
  | 'unreal'
  | 'react_native'
  | 'flutter'
  | 'uniapp_mp'      // uni-app 小程序端
  | 'uniapp_app'     // uni-app APP端
  | 'uniapp_h5'      // uni-app H5端
  ;

function getAutotrackEvents(sdkType: SDKType): Event[] {
  // 根据 sdkType 返回对应的自动采集事件数组
}
```

### 映射规则

**默认注入 recommended 事件，optional 事件在 Refine 阶段提示用户可选开启。**

| SDK 类型 | recommended（默认注入） | optional（不自动注入） |
|---|---|---|
| `android` | install, start, end | view, click, crash |
| `ios` | install, start, end | view, click, crash, bg_start |
| `openharmony` | install, start, end | view, click, crash |
| `javascript` | page_show, page_hide | pageview（需单独 quick 调用） |
| `wechat_mp` | launch, show, hide, view, share | page_leave, favorite, click |
| `wechat_mg` | launch, show, hide | — |
| `unity` | install, start, end | scene_loaded, scene_unloaded |
| `unity_wxmg` | mg_launch, mg_show, mg_hide | scene_loaded, scene_unloaded |
| `cocos2dx` / `cocoscreator` / `layaair` / `unreal` | install, start, end | — |
| `react_native` / `flutter` | 继承原生 recommended | 继承原生 optional |
| `uniapp_mp` | 继承小程序 recommended | 继承小程序 optional |
| `uniapp_app` | 继承原生 recommended | 继承原生 optional |
| `uniapp_h5` | 继承 JavaScript recommended | 继承 JavaScript optional |