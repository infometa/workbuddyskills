# Viewing Client SDK Logs

> **Terminology**: 客户端 SDK = client SDK | 日志 = log | 数据采集 = data collection | 数据上报 = data upload / ingestion | 本地缓存 = local cache / local database | 批量上报 = batch upload | 触发上报 = trigger upload | 上报时间间隔 = upload interval | 日志级别 = log level | 调试 = debugging | 排查问题 = troubleshooting

# 一、背景

在客户端 SDK 集成调试以及排查问题时，可以借助日志分析数据的采集和上报是否符合预期。本文介绍如何开启SDK日志，以及日志中的关键词和对应含义。

### 原生客户端 SDK 上报机制

首先我们简要介绍原生客户端 SDK 的上报机制，Android 和 iOS SDK 都会在本地数据库缓存数据并批量上报。本地缓存数据为了避免网络异常情况下丢失数据，批量上报为了避免频繁上报产生的系统和网络开销。当符合以下任一条件时，均会触发数据上报：

- APP 切换到后台
- 距上次数据上报时间间隔达到上报时间间隔（默认时间间隔为30秒，可以在 TE 修改）
- 本地缓存数量达到上报的数量（默认上报的数量达到30条触发上报，可以在 TE 修改）

因此，在调试过程中，如果没有满足触发数据上报的条件，数据仍然缓存在本地。

### 数据日志打印

对于一条数据，数据在本地存储时会打印一条日志，数据上报时又会打印一条日志，因此需要根据日志中的关键词区分日志的含义，不要误以为产生了重复数据。

# 二、开启日志打印

### iOS 3.0之前版本

日志筛选字段"[THINKING]"

**开启日志打印**

```objectivec
[ThinkingAnalyticsSDK setLogLevel:TDLoggingLevelDebug];
```

**初始化SDK**

mode：表示SDK使用的模式

```
2024-02-01 11:36:47.862929+0800 TATest_iOS[32287:14658471] [THINKING] Thinking Analytics iOS SDK 2.8.4 instance initialized successfully with mode: NORMAL, APP ID: af6861d085e14b5c948662e1fcdce6ef, server url: https://receiver-ta-demo.thinkingdata.cn, device ID: 15F96974-CE32-44F5-9AD0-F259349FDAF2
```

**数据存储本地**（关键词：`[THINKING] queueing data`）

```objectivec
2022-10-25 17:30:29.270504+0800 TATest_iOS[85710:698131] [THINKING] queueing data:{
  "properties" : {
    "#os" : "iOS",
    "#device_model" : "arm64",
    ...
  },
  "#type" : "track",
  "#uuid" : "DB2B97A5-183A-439E-B8B2-FE9AF77D7421",
  "#distinct_id" : "E5ABB02F-EA10-47AC-AB6C-A8E47E55B4E9",
  "#event_name" : "testA",
  "#time" : "2022-10-25 14:30:29.256"
}
```

**数据上报TA**（关键词：`[THINKING] flush success sendContent`）

```objectivec
2022-10-25 17:30:32.551796+0800 TATest_iOS[85710:698131] [THINKING] flush success sendContent---->:{
  "#app_id" : "af6861d085e14b5c948662e1fcdce6ef",
  "data" : [...],
  "#flush_time" : 1666690232351
}
```

**上报TA结果**（关键词：`flush success responseData`）

code为0代表上传成功

```objectivec
2022-10-25 17:30:32.552237+0800 TATest_iOS[85710:698131] [THINKING] flush success responseData---->{
  "code" : 0
}
```

### iOS 3.0及之后版本

日志筛选字段"[ThinkingData]"

**开启日志打印**

```objectivec
[TDAnalytics enableLog:YES];
```

**初始化SDK**

```
2024-02-01 12:07:05.077926+0800 TATest_iOS[32411:14665745] [ThinkingData] [ThinkingData][Info] initialized successfully!
 AppID: af6861d085e14b5c948662e1fcdce6ef 
 ServerUrl: https://receiver-ta-demo.thinkingdata.cn 
 Mode: Debug 
 TimeZone: Local Time Zone (Asia/Shanghai (GMT+8) offset 28800) 
 DeviceID: 15F96974-CE32-44F5-9AD0-F259349FDAF2 
 Lib: iOS 
 LibVersion: 3.0.0
```

**数据存储本地**（关键词：`[ThinkingData] [Info] Enqueue data`）

```
2023-09-05 14:27:44.721461+0800 TestTAiOS[41411:3781875] [ThinkingData] [Info] Enqueue data: {
  "properties" : {...},
  "#type" : "track",
  "#uuid" : "0ECCD33B-8076-42A5-BA2B-89DE0773B84B",
  "#distinct_id" : "51C6265F-8F03-461E-91D3-D0FFB11DFCFD_2",
  "#event_name" : "iOS_001",
  "#time" : "2023-09-05 14:27:44.719"
}
```

**数据上报TA**（关键词：`[ThinkingData] [Debug] flush success sendContent`）

```
2023-09-05 14:28:14.834448+0800 TestTAiOS[41411:3782015] [ThinkingData] [Debug] flush success sendContent---->:{...}
```

**上报TA结果**

- code为0代表上传成功
- 打印了flush success responseData，就可以认为上报成功。只看response的状态码为200，不看返回内容中的code

```
2023-09-05 14:28:14.835774+0800 TestTAiOS[41411:3782015] [ThinkingData] [Debug] flush success responseData---->{
  "code" : 0
}
```

### Android 3.0之前版本

日志筛选字段"ThinkingAnalytics"

**开启日志打印**

```java
ThinkingAnalyticsSDK.enableTrackLog(true);
```

**初始化SDK**

mode：表示SDK使用的模式

```
2024-04-09 13:39:23.458 12219-12219 ThinkingAnalyticsSDK cn.thinkingdata.android.demo I Thinking Analytics SDK 2.8.3 instance initialized successfully with mode: NORMAL, APP ID ends with: 3356, server url: https://receiver.ta.thinkingdata.cn/sync, device ID: d4d6419233102942
```

**数据存储本地**（关键词：`Data enqueued`）

```
2022-10-26 10:56:54.416 6445-6528/cn.thinkingdata.android.demo I/ThinkingAnalytics.DataHandle: Data enqueued(e6ef):
    {
        "#type": "track",
        "#time": "2022-10-26 10:56:54.285",
        "#distinct_id": "04af1a3d-56b2-4c8f-a54a-2b6f655b8286",
        "#event_name": "testA",
        ...
    }
```

**数据上报TA及结果**（关键词：`upload message`）

code为0代表上传成功

```
2022-10-26 10:56:54.637 6445-6526/cn.thinkingdata.android.demo I/ThinkingAnalytics.DataHandle: ret code: 0, upload message: {...}
```

### Android 3.0之后版本

日志筛选字段"[ThinkingData]"

**开启日志打印**

```java
TDAnalytics.enableLog(true);
```

**初始化SDK**

```
2024-04-09 13:48:02.088 13974-13974 ThinkingAnalyticsSDK cn.thinkingdata.android.demo I [ThinkingData] Info: ThinkingData SDK 3.0.2 initialize success with mode: NORMAL, APP ID ends with: 3df0, server url: https://receiver-ta-preview.thinkingdata.cn/sync
```

**数据存储本地**（关键词：`[ThinkingData] Info: Enqueue data`）

```
2023-09-14 10:09:52.461 15126-15163/com.example.tatest_android I/ThinkingAnalytics.DataHandle: [ThinkingData] Info: Enqueue data(e6ef):
    {
        "#type": "track",
        "#time": "2023-09-14 10:09:52.445",
        "#distinct_id": "b86de4eb-12b8-4ce4-924a-54cd12b5fa25",
        "#event_name": "android_001",
        ...
    }
```

**数据上报TA**（关键词：`[ThinkingData] Debug: Send event, Request =`）

```
2023-09-14 10:09:52.688 15126-15162/com.example.tatest_android D/ThinkingAnalytics.DataHandle: [ThinkingData] Debug: Send event, Request = {...}
```

**上报TA结果**（关键词：`[ThinkingData] Debug: Send event, Response =`）

code为0代表上传成功

```
2023-09-14 10:09:52.688 15126-15162/com.example.tatest_android D/ThinkingAnalytics.DataHandle: [ThinkingData] Debug: Send event, Response ={
        "code": 0
    }
```

### Unity 3.0之前版本

**开启日志打印**

注意：EnableLog 需要放在 StartThinkingAnalytics 之后调用

```csharp
ThinkingAnalyticsAPI.EnableLog(true);
```

**数据存储本地**（关键词：`Save event`）

```
[ThinkingEngine] (Unity_V2.6.0-beta.1) Save event: {...}
```

**数据上报TA**（关键词：`Post event`）

```
[ThinkingEngine] (Unity_V2.6.0-beta.1) Post event: {...}
```

**上报TA结果**

code为0代表上传成功

```
[ThinkingEngine] (Unity_V2.6.0-beta.1) Response: {"code":0}
```

### Unity 3.0之后版本

**开启日志打印**

注意：EnableLog 需要放在 Init 之后调用。Unity的日志默认是开启的。

```csharp
TDAnalytics.EnableLog(true);
```

**数据存储本地**（关键词：`Enqueue data`）

```
[ThinkingData] Info: Enqueue data: {...}
```

**数据上报TA**（关键词：`Send event Request`）

```
[ThinkingData] Info: Send event Request: {...}
```

**上报TA结果**（关键词：`Send event Response`）

- Normal模式，code为0代表上传成功
- Debug模式，如果没有加白名单，"errorLevel":-1，提示加白名单
- Debug模式，如果加了白名单，"errorLevel":0，表示上报成功

### OpenHarmony

日志筛选字段"[ThinkingData]"，但是由于打印字段有限制，所以一般不加筛选条件

**开启日志打印**

```
TDAnalytics.enableLog(true);
```

**初始化SDK**

```
[ThinkingData] Info: ThinkingData SDK 1.3.3 initialize success with mode: NORMAL, APP ID ends with: e6ef, server url: https://receiver-ta-demo.thinkingdata.cn, device ID: ad6a69cf-3f2c-47ed-a6e9-4808e36cc61f
```

**数据存储本地**（关键词：`[ThinkingData] Info: Enqueue data`）

```
[ThinkingData] Info: Enqueue data : {...}
```

**数据上报TA**（关键词：`[ThinkingData] Info: Send event`）

```
[ThinkingData] Info: Send event, Request = {...}
```

**上报TA结果**（关键词：`[ThinkingData] Info: Response`）

打印了Response，就可以认为上报成功。只看response的状态码为200，不看返回内容中的code

```
[ThinkingData] Info: Response :{"responseCode":200,...}
```

# 三、TE系统查询数据

使用sql通过#device_id查询数据，这里数据最及时，实时数据也没这里及时

1. 分析中选择SQL查询
2. 解析事件表，where中添加#device_id