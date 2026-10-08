---
title: "Unity SDK FAQ"
code: "unity_sdk_faq"
source: "Feishu MCP"
doc_id: "wikcnZ5YKmQd4b26mJQ2uiF6fvd"
fetched_at: "2026-04-20T17:29:38Z"
---

> 本文主要针对 Unity 打包除 Android / iOS 之外平台的问题。Android / iOS 平台默认使用原生 SDK。

# SDK 初始化
## 推荐初始化 SDK 初始化位置
- 建议在用户同意隐私协议后再进行 SDK 初始化

## 初始化方式
### 手动初始化
```csharp
using ThinkingData.Analytics;
TDAnalytics.Init("APPID","SERVER");
// 或通过 TDConfig 初始化
TDConfig config = new TDConfig("APPID","SERVER");
TDAnalytics.Init(config);
```

### 自动初始化
- 添加 TDAnalytics 预置体，并设置 SDK 配置

# 数据缓存机制
## 存储位置
- 通过 PlayerPrefs 存储，Mac OS X 上存储在 ~/Library/Preferences

## 缓存限制
- 没有限制缓存数据量上限，缓存数据没有过期删除策略

# 数据上报策略
## 触发数据上报场景
- APP 切换到后台
- 产生自动采集事件
- 调用 flush() 接口
- 缓存数据量达到阈值（默认 30 条）
- 上报时间间隔超过阈值（默认 30 秒）
- DEBUG / DEBUG_ONLY 模式下直接上报

# 访客 ID（#distinct_id）
## 设置访客 ID
```csharp
TDAnalytics.SetDistinctId("Thinker");
```

## 访客 ID 改变场景
- 用户清除应用数据
- 用户卸载重装或更换设备
- 调用 SetDistinctId() 接口

# 账号 ID（#account_id）
## 设置账号 ID
```csharp
TDAnalytics.Login("TA");
```

# 设备 ID（#device_id）
## 生成规则
- UNITY_WEBGL：取 System.Guid.NewGuid().ToString("N")
- 其它平台：取 SystemInfo.deviceUniqueIdentifier

# Debug 模式
## Normal，Debug，DebugOnly 模式区别

| 模式 | 上报模式 | 数据入库 | 数据严格检查 | 数据加密 |
|------|----------|----------|--------------|----------|
| Normal | 批量上报 | 是 | 否 | 支持 |
| Debug | 逐条上报 | 是 | 是 | 不支持 |
| DebugOnly | 逐条上报 | 否 | 是 | 不支持 |

# 自动采集事件
## ta_app_install
- 应用安装或卸载后重装时触发

## ta_app_start
- 应用程序获得焦点

## ta_app_end
- 应用程序失去焦点或退出

## ta_app_crash
- 监听到 UnhandledException 或 LogType.Error 等
- 2.2.0 以上版本会默认采集 C# 异常

## ta_scene_loaded / ta_scene_unloaded
- 监听 SceneManager 的回调

# 公共事件属性
## 静态公共事件属性
- setSuperProperties 方法，存在本地

## 动态公共事件属性
- 每次 track() 时调用回调函数获取当前值

## 属性优先级
- 用户自定义事件属性 > 动态公共事件属性 > 静态公共事件属性

# 预置属性
## #ip
- TE 服务器获取 http 请求 header 中的 ip

## #os
- Unity WebGL 转的微信小游戏 #os 为 "other"

# 异常问题
详见文档完整内容。

# 已知问题
- 打包 iOS & Android 后 #zone_offset 缺失问题
- 多个版本已知 bug 及修复版本
详见文档完整内容。