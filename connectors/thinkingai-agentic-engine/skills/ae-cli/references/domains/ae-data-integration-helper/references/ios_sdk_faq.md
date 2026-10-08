---
title: "iOS SDK FAQ"
code: "ios_sdk_faq"
source: "Feishu MCP"
doc_id: "wikcn4nM313WpHDriYEdxvUmzqe"
fetched_at: "2026-04-20T17:29:37Z"
---

# 集成 SDK
## SDK 集成方式说明
- 目前支持手动集成和自动集成（CocoaPods）两种方式，不支持 Carthage 方式集成

# 初始化 SDK
## 推荐初始化 SDK 初始化位置
- 建议在用户同意隐私协议后再进行 SDK 初始化
```objectivec
if (授权隐私政策) {
    NSString *appid = @"APPID";
    NSString *url = @"SERVER_URL";
    [TDAnalytics startAnalyticsWithAppId:appid serverUrl:url];
}
```

# SDK 缓存机制 & 限制
## SDK 哪些数据会在本地存储？
- 基础数据：访客 ID、设备 ID、静态通用事件属性等，存储在 Library 目录
- 事件数据：缓存到本地数据库 Library/TDData-data.plist

## 事件数据缓存数量限制
- SDK 默认缓存限制为 10000 条数据
- 可自定义缓存数量，最小值为 5000 条

## 缓存过期时间
- SDK 默认过期时间为 10 天
- 可在 info.plist 中配置

# SDK 数据上报策略
## 立即上报
- APP 切换到后台会立即上报缓存数据
- debug / debug_only 模式会立即上报
- 自动采集事件会立刻上报
- 手动调用 flush() 接口会立即上报
- 每个请求上限为 50 条数据

## 批量上报
- 时间间隔超过配置时长上报（默认 30 秒）
- 缓存事件数量达到阈值（默认 30 条）

# 访客 ID（#distinct_id）
## 访客 ID 如何设置
```objectivec
[TDAnalytics setDistinctId:@"Thinker"];
```

## 访客 ID 何时会变
- 用户清除了应用数据
- 用户更换了设备或卸载重装
- 调用 identify 接口手动设置

# 账号 ID（#account_id）
## 账号 ID 如何设置
```objectivec
[TDAnalytics login:@"TD"];
```

# Debug 模式
## Normal，Debug，DebugOnly 模式区别

| 模式 | 上报模式 | 本地缓存 | 数据入库 | 数据严格检查 | 数据加密 |
|------|----------|----------|----------|--------------|----------|
| Normal | 批量上报 | 是 | 是 | 否 | 支持 |
| Debug | 逐条上报 | 否 | 是 | 是 | 不支持 |
| DebugOnly | 逐条上报 | 否 | 否 | 是 | 不支持 |

> 请勿在生产环境使用 Debug 和 DebugOnly 模式

# 自动采集事件
## ta_app_install
- 新安装 APP 或卸载重装 APP 时触发
- #install_time 和 #time 不相等是正常的

## ta_app_start
- 第一次开启自动采集时
- app 后台切换到前台后触发

## ta_app_end
- app 从前台切换到后台、杀掉 app 进程后

## ta_app_crash
- 监听 NSSetUncaughtExceptionHandler 捕获的异常
- 在 Debug 模式下 ta_app_crash 可能丢失

# 公共事件属性
## 静态公共事件属性
- `[TDAnalytics setSuperProperties:@{@"vip_level": @(2)}];`
- 存在本地，每次 track 都会带上

## 动态公共事件属性
```objectivec
[TDAnalytics setDynamicSuperProperties:^NSDictionary * _Nonnull{
    return @{@"now": [NSDate date]};
}];
```

## 属性优先级
- 用户自定义事件属性 > 动态公共事件属性 > 静态公共事件属性

# 预置属性
## #device_id
- 获取的是 idfv，获取不到就获取 UUID
- Keychain 持久化存储，卸载重装后不会改变

## #ip
- TE 服务器获取 http 请求 header 中的 ip 信息
- 使用第三方 IP 库解析地理位置

# 已知问题
详见文档完整内容。