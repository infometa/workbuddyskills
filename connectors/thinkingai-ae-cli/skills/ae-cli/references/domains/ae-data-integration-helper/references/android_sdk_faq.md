---
title: "Android SDK FAQ"
code: "android_sdk_faq"
source: "Feishu MCP"
doc_id: "wikcnVrL8nNo5bwytvIVde3MT8e"
fetched_at: "2026-04-20T17:29:37Z"
---

# 集成 SDK
## 集成方式
- Android SDK 支持自动集成 gradle 和 手动集成 aar 两种接入方式。
### gradle 方式导入
- 在 `Project` 级别的 `build.gradle` 文件中添加如下配置依赖
```json
buildscript {
    repositories {
        jcenter()
        mavenCentral()
    }
}
```

- 在 `Module` 工程目录下的 `build.gradle`文件中添加依赖项：
```java
dependencies {
    implementation 'cn.thinkingdata.android:ThinkingAnalyticsSDK:2.8.3'
}
```

### 本地 aar 导入
参见官方文档。

## 兼容性说明
- Android SDK 兼容最低版本 Android 4.0
  - `minSdkVersion 14`

# 初始化
## 推荐初始化位置
- 建议在用户同意隐私协议后再进行 SDK 初始化，详见 ThinkingData 官方文档中的《合规指南》部分。
```json
// 根据隐私协议判断是否开启数据采集
if (授权隐私政策) {
    TDAnalytics.init(this, APPID, SERVER_URL);
}
```

## 初始化方式一：其它配置默认，只需要传入 APPID 和 SERVER_URL 就可以
```java
// 在主线程中初始化 SDK
TDAnalytics.init(this, APPID, SERVER_URL);
```

## 初始化方式二：根据 config 自定义一些参数配置
- 模式设置
  - config.setMode(TDConfig.TDMode.NORMAL);
  - config.setMode(TDConfig.TDMode.DEBUG);
  - config.setMode(TDConfig.TDMode.DEBUG_ONLY);
- 模式时区设置
  - config.setDefaultTimeZone(TimeZone.getDefault());
- 是否开启多进程
  - config.setMutiprocess(true);
- 是否开启加密
  - config.enableEncrypt(true)
```java
TDConfig config = TDConfig.getInstance(this, APPID, TE_SERVER_URL);
TDAnalytics.init(config);
```

# 上报模式
## NORMAL
- 在 Normal 模式下，数据会首先进入缓存，之后根据配置的上报规则进行批量上报，上报成功后数据会入库。

## DEBUG
- 在 Debug 模式下，数据会立即逐条上报。上报成功后数据会入库。
- 如果上报失败，SDK 会采取降级处理，将 Debug 模式降级为 Normal 模式并且将失败数据缓存到本地。
- 需要在应用程序中配置设备白名单。

## DEBUG_ONLY
- 在 DebugOnly 模式下，数据会立即逐条上报并且数据不会入库，如果上报失败，数据就会丢失。
- 没有配置白名单不会自动切换到 NORMAL 模式。

> 注意：
> - 在正式上线时，建议避免使用 debug 或 debug_only 模式
> - debug 模式下如果没有 TE 后台配置白名单会切换成 NORMAL 模式
> - debug_only 不会自动切换成 NORMAL 模式

# 上报策略
- normal 模式默认 30 秒或者 30 条满足上报一次，TE 项目管理可以设置修改
- debug / debug_only 模式事件会立即上报
- 手动调用 flush() 接口，会立即上报缓存数据
- 自动采集事件会立刻上报
- 每个请求上限为 50 条数据

# 缓存机制
- 非 debug、debug_only 模式，数据会先缓存本地数据库，然后按策略发送
- 默认本地缓存条数 1 万条，超过就会开始丢弃前面的数据
- SDK 2.8.2 版本之前默认缓存 15 天，2.8.2 开始默认缓存 10 天
- 可通过 ta_public_config.xml 配置缓存天数和条数

# 自动采集
## ta_app_install
### 触发条件以及时机
- 开启了 install 事件自动采集
- 初始化 SDK 时判断 firstInstallTime

## ta_app_start
### 触发条件以及时机
- 开启了 ta_app_start 事件自动采集
- App 启动或者 App 从后台回到前台

## ta_app_end
### 触发条件以及时机
- 开启了 end 事件自动采集
- App 退出或者切换到后台，或者闪退

## ta_app_crash
### 触发条件以及时机
- 开启了 crash 事件的自动采集
- App 闪退的时候触发

## ta_app_view
### 触发条件以及时机
- 开启了 view 事件的自动采集
- Activity 或者 fragment 的页面显示的时候

## ta_app_click
### 触发条件以及时机
- 开启了 click 事件的自动采集
- 点击页面的控件
- 需要接入全埋点插件

# 预置属性
## 设备 ID #device_id
- 获取 AndroidID 或者随机生成的
- 什么情况下会变：应用多开、拿不到 androidId 并卸载重装、刷机或更换包名

## 模拟器 #simulator
- 根据 Android 的 SystemProperties 来判断

## 内存 #ram
- 获取的是可用内存和总内存大小

## 运营商 #carrier
- 部分应用市场反馈安全检测存在未申请权限获取运营商的情况，可屏蔽该字段

## 网络类型 #network_type
- 事件发生时无网络则为 NULL

## 访客 ID #distinct_id
- 默认系统 UUID 方式生成，存本地
- 卸载重装会变

# 公共属性
## 静态公共属性
- 方法名 setSuperProperties
- 把设置的属性存在本地 SharedPreferences

## 动态公共属性
- 方法名 setDynamicSuperPropertiesTracker
- 每次 track 的时候会带上这个回调回来的属性

# 数据加密
- 默认是先 gzip 然后 base64 处理
- 2.8.0 开始也可以选择开启非对称加密
- 加密只对 normal 模式生效

# 通用问题
## 数据上报失败
- 检查上报地址和 appid 是否正确
  - {上报地址}/check_appid?appid={appid} 返回 0 表示正常
- 服务异常
  - {上报地址}/health_check 返回 ok 表示正常

## 部分用户没有事件上报
- 查看上报地址是否使用 https 协议，安卓 9.0 以上默认不支持 http
- 初始化 SDK 是否有逻辑判断，有情况没有初始化

# 已知问题
详见文档完整内容。