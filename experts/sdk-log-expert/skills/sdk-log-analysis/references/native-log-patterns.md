# Native 端日志模式详解

本文档包含 TRTC Native SDK 的日志特征，适用于所有非 Web 环境。

## 适用范围

| 平台 | 是否适用 | 备注 |
|-----|---------|-----|
| iOS App | ✅ | 直接使用本文档 |
| Android App | ✅ | 直接使用本文档 |
| Electron 主进程 | ✅ | 直接使用本文档 |
| Flutter | ✅ | 直接使用本文档 |
| React Native | ✅ | 直接使用本文档 |
| UniApp (App 端) | ✅ | 直接使用本文档 |
| **微信/支付宝小程序** | ✅ | 如涉及组件/协议问题，另需 `miniprogram-log-patterns.md` |
| UniApp (小程序端) | ✅ | 如涉及组件/协议问题，另需 `miniprogram-log-patterns.md` |

> ⚠️ **小程序说明**：小程序底层使用 Native SDK，本文档的进房、编解码、信令知识同样适用。若需分析 `live-pusher`/`live-player` 组件或 `room://` 协议问题，另加载 miniprogram-log-patterns.md。

---

## 日志格式说明

Native 端日志通常格式为：
```
[日志级别][月-日/时:分:秒.毫秒+时区][进程ID,线程ID][源文件:行号]@会话ID 模块: 日志内容
```

示例：
```
[I][09-02/13:13:38.984+8.0][29742,30418][signal_manager.cc:397]@2c0 Network: Signal: Seq: 883234782, Command: QueryACCIPandSignResponse
```

- `[I]` - INFO 级别
- `[W]` - WARN 级别
- `[E]` - ERROR 级别
- `@2c0` - 会话 ID

---

## 一、信令与网络

### 信令消息
**关键词**: `Signal:`, `Command:`
```
[I][09-02/13:13:38.984+8.0][29742,30418][signal_manager.cc:397]@2c0 Network: Signal: Seq: 883234782, Command: QueryACCIPandSignResponse, Tinyid: 0, ErrorCode: -100018, Reason: usersig expired
```

**关键字段**:
- `Command:` - 信令命令类型
- `ErrorCode:` - 错误码（负数通常表示错误）
- `Reason:` - 错误原因

### 常见信令错误

| ErrorCode | Reason | 含义 |
|-----------|--------|------|
| `-100018` | `usersig expired` | UserSig 过期，需重新生成 |

---

## 二、播放器

### 首帧渲染
**关键词**: `Render first frame`
```
[I][01-13/20:43:32.009+8.0][647,882][player_video_module.cc:438][6:be00] Video: Render first frame. width:540, height:960, reason:StartRendering
```

**解读**:
- `width/height` - 视频分辨率
- `reason:StartRendering` - 开始渲染
- 出现此日志说明视频首帧已渲染成功

---

## 三、音频相关

### 音频采集
**搜索关键词**: `startLocalAudio`, `EnableLocalAudio`, `AudioCapture`

### 音频播放
**搜索关键词**: `AudioPlayout`, `Speaker`, `AudioRoute`

### 音频设备
**搜索关键词**: `Microphone`, `AudioDevice`, `AudioSession`

---

## 四、视频排障（重要）

本节包含完整的视频问题排障流程，涵盖采集、渲染、编码、解码各环节。

### 视频问题分类

| 问题类型 | 描述 | 排障方向 |
|---------|------|---------|
| **本地渲染黑屏** | 本地预览画面黑屏 | 采集 → 本地渲染 → 前后台状态 |
| **本地渲染花屏** | 本地预览画面花屏 | glContext 线程问题，需反馈研发 |
| **本地无上行** | 本地有画面但远端收不到 | 采集 → 编码 → 网络 |
| **远端播放黑屏** | 远端画面黑屏 | 本地上行 → 网络下行 → 解码 → 远端渲染 |
| **远端播放花屏** | 远端画面花屏 | glContext 线程问题，需反馈研发 |

---

### 上行排障：摄像头采集（iOS/Mac/Android）

**模块关键词**: `camera_safe_wrapper`, `TXCCameraCapture`

#### 采集状态检查

| 阶段 | 日志关键词 | 说明 |
|-----|----------|------|
| **开启采集** | `start [front\|back] camera successfully` | 前置/后置摄像头启动成功 |
| **停止采集** | `stop camera` | 摄像头停止 |
| **启动错误** | `TXCCameraCapture.mm` + `[E]` | 采集启动报错，检查该文件的 ERROR 日志 |

#### 采集是否正常

| 检查项 | 日志关键词 | 说明 |
|-------|----------|------|
| **前后台状态** | `AppState:` | `Foreground`, `Active` = 前台，只有前台才会正常出帧 |
| **摄像头被打断** | `TXCCameraCapture session interrupted` | 采集被系统打断（如来电） |
| **打断恢复** | `TXCCameraCapture session interruption ended` | 打断结束，恢复出帧 |

#### 采集出帧打点（重要）

**日志关键词**: `[VideoCapture] camera capture frameIndex:`

- 摄像头启动时打点，之后在第 1、5、10、30 秒打点，此后每 30 秒打一次
- `frameIndex` 每帧 +1，fps=15 时每秒应增加 15
- 用于排查摄像头出帧是否有卡顿

```
搜索关键词: "[VideoCapture] camera capture frameIndex"
```

---

### 上行排障：屏幕采集（iOS/Mac）

**模块关键词**: `screen_safe_wrapper`

| 阶段 | 日志关键词 | 说明 |
|-----|----------|------|
| **开启采集** | `VideoCapture[%Address%]: start [screen\|window]` | 屏幕/窗口采集启动 |
| **停止采集** | `VideoCapture[%Address%]: stop [screen\|window]` | 屏幕/窗口采集停止 |
| **状态变更回调** | `onScreenShare[Start\|Stop\|Pause\|Resume]` | 采集状态变更事件 |

#### 屏幕采集出帧打点

**日志关键词**: `[VideoCapture] screen capture`

- 屏幕采集启动时打点，之后在第 1、5、10、30 秒打点，此后每 30 秒打一次
- 有此日志 = 系统正常出帧

---

### 上行排障：自定义采集

| 日志关键词 | 说明 |
|-----------|------|
| `EnableCustomVideoCapture [stream_type:BigStream\|enable:True]` | 开启自定义采集 |
| `EnableCustomVideoCapture [stream_type:BigStream\|enable:False]` | 关闭自定义采集 |
| `input video pixel format error` | ⚠️ 像素格式错误 |
| `input video frame error` | ⚠️ 视频帧数据错误 |
| `[VideoCapture] custom capture` | 自定义采集送帧打点 |

**自定义采集送帧打点**：
- 首次发送时打点，之后在第 1、10、30 秒打点，此后每 30 秒打一次
- 检查日志中 `width` 和 `height` 是否正常（不应为 0）

---

### 上行排障：本地渲染

#### 渲染状态检查

| 检查项 | 日志关键词 | 说明 |
|-------|----------|------|
| **渲染控件创建** | `TXCRenderView init` | 渲染画面控件成功创建 |
| **渲染控件布局** | `TXCRenderView %Address% layoutSubviews` | 检查 frame 大小不为 0 |
| **前后台状态** | `AppState:` | 只有前台时才会正常渲染 |

#### 渲染打点日志（重要）

**日志关键词**: `[VideoRender] userID:`

- 首次渲染时打点，之后在第 1、5、10、30 秒打点，此后每 30 秒打一次
- 有此日志 = 渲染正常运行
- ⚠️ 无此日志 = 本地渲染打点异常

```
搜索关键词: "[VideoRender] userID:"
```

---

### 上行排障：编码

#### 编码器状态

| 阶段 | 日志关键词 | 说明 |
|-----|----------|------|
| **创建硬编** | `[TXCHWVideoEncoder] init` | 创建硬件编码器 |
| **创建软编** | `[TXCSWVideoEncoder] init` | 创建软件编码器 |
| **启动编码** | `VideoEncoder[%Address%]: Start ...` | 编码器启动，检查参数 |
| **启动成功** | `VideoEncoder[%Address%]: Start successfully` | 编码器启动成功 |
| **销毁硬编** | `[TXCHWVideoEncoder] dealloc` | 销毁硬件编码器 |
| **销毁软编** | `[TXCSWVideoEncoder] dealloc` | 销毁软件编码器 |

#### 编码错误检查

| 编码器类型 | 检查文件 | 说明 |
|-----------|---------|------|
| 硬编 | `TXCHWVideoEncoder.mm` | 搜索该文件的 ERROR 日志 |
| 软编 | `TXCSWVideoEncoder.mm`, `TXCSoftwareVideoCodec.cpp` | 搜索该文件的 ERROR 日志 |

- 硬编出错时，会尝试重启硬编或切换到软编
- 软编出错时，会尝试重启软编

#### 编码打点日志（重要）

| 日志关键词 | 说明 |
|-----------|------|
| `[VideoCapture] [sw\|hw] encode pts` | 有帧送到编码器 |
| `[VideoCapture] send pts` | 编码器正常出帧 |

- 首帧时打点，之后在第 1、10、30 秒打点，此后每 30 秒打一次
- ⚠️ 无 `encode pts` = 没有帧送到编码器
- ⚠️ 无 `send pts` = 编码器没有出帧

---

### 下行排障：解码

#### 解码器状态

| 阶段 | 日志关键词 | 说明 |
|-----|----------|------|
| **创建硬解** | `[TXCHWVideoDecoder] init` | 创建硬件解码器 |
| **创建软解** | `[TXCSWVideoDecoder] init` | 创建软件解码器 |
| **启动解码** | `Remote-VideoDecoder[%Address%]: Start` | 解码启动，检查 type/tinyID/streamType |
| **停止解码** | `Remote-VideoDecoder[%Address%]: Stop` | 解码停止，检查 tinyID/streamType |
| **销毁硬解** | `[TXCHWVideoDecoder] dealloc` | 销毁硬件解码器 |
| **销毁软解** | `[TXCSWVideoDecoder] dealloc` | 销毁软件解码器 |

#### 解码送帧打点（重要）

**日志关键词**: `[VideoRender] decode receive frame userID`

- 首次解码时打点，之后在第 1、5、10、30 秒打点，此后每 30 秒打一次
- 有此日志 = 有帧送到解码器
- ⚠️ 无此日志 = 解码器没有收到数据

---

### 下行排障：远端渲染

#### 渲染状态检查

| 检查项 | 日志关键词 | 说明 |
|-------|----------|------|
| **渲染控件创建** | `TXCRenderView init` | 渲染画面控件成功创建 |
| **渲染控件布局** | `TXCRenderView %Address% layoutSubviews` | 检查 frame 正常 |
| **前后台状态** | `AppState:` | 只有前台时才会正常渲染 |
| **卡顿丢帧** | `receive new frame while busy` | ⚠️ 渲染繁忙导致丢帧 |

#### 远端渲染打点

**日志关键词**: `[VideoRender] userID:`

- 同本地渲染，首次渲染时打点，之后在第 1、5、10、30 秒打点，此后每 30 秒打一次
- 检查对应用户 ID 的渲染状态

---

### 画面朝向问题

#### 主播端设置

| 接口 | 说明 |
|-----|------|
| `setVideoEncoderRotation` | 设置编码旋转角度 |
| `setGSensorMode` | 重力感应模式 |

**GSensorMode 说明**：
- 默认 `TRTCGSensorMode_UIAutoLayout`：适用于推流页面不做自动旋转
- 如果页面支持自动旋转，需设置为 `TRTCGSensorMode_Disable`

#### 观众端设置

| 接口 | 说明 |
|-----|------|
| `setRemoteRenderParams` | 设置远端渲染参数，检查 `params.rotation` |

---

### 视频排障流程图

#### 本地渲染黑屏排障

```
1. 检查采集
   ├─ 搜索 "start [front|back] camera successfully" → 确认摄像头启动
   ├─ 搜索 "[VideoCapture] camera capture frameIndex" → 确认出帧
   └─ 搜索 "TXCCameraCapture session interrupted" → 检查是否被打断

2. 检查本地渲染
   ├─ 搜索 "TXCRenderView init" → 确认渲染控件创建
   ├─ 搜索 "TXCRenderView layoutSubviews" → 确认 frame 不为 0
   └─ 搜索 "[VideoRender] userID:" → 确认渲染打点正常

3. 检查前后台状态
   └─ 搜索 "AppState:" → 确认在前台（Foreground/Active）
```

#### 本地无上行排障

```
1. 确认本地渲染正常（同上）

2. 检查编码
   ├─ 搜索 "VideoEncoder: Start successfully" → 确认编码器启动
   ├─ 搜索 "[VideoCapture] [sw|hw] encode pts" → 确认送帧到编码器
   ├─ 搜索 "[VideoCapture] send pts" → 确认编码器出帧
   └─ 搜索 "TXCHWVideoEncoder" + "[E]" → 检查编码错误

3. 检查网络 → 参见网络排障
```

#### 远端播放黑屏排障

```
1. 确认本地上行正常（同上）

2. 检查网络下行 → 参见网络排障

3. 检查解码
   ├─ 搜索 "Remote-VideoDecoder: Start" → 确认解码器启动
   └─ 搜索 "[VideoRender] decode receive frame userID" → 确认送帧到解码器

4. 检查远端渲染
   ├─ 搜索 "TXCRenderView init" → 确认渲染控件创建
   └─ 搜索 "[VideoRender] userID:" → 确认渲染打点正常

5. 检查前后台状态
   └─ 搜索 "AppState:" → 确认在前台

6. 自定义渲染注意
   └─ 使用自定义渲染需先调用 startRemoteView(nil) 获取视频流
```

---

### 视频打点日志汇总

| 打点类型 | 日志关键词 | 打点时机 |
|---------|----------|---------|
| 摄像头采集 | `[VideoCapture] camera capture frameIndex` | 启动时 + 第 1/5/10/30 秒 + 每 30 秒 |
| 屏幕采集 | `[VideoCapture] screen capture` | 启动时 + 第 1/5/10/30 秒 + 每 30 秒 |
| 自定义采集 | `[VideoCapture] custom capture` | 首帧 + 第 1/10/30 秒 + 每 30 秒 |
| 本地/远端渲染 | `[VideoRender] userID:` | 首帧 + 第 1/5/10/30 秒 + 每 30 秒 |
| 编码送帧 | `[VideoCapture] [sw\|hw] encode pts` | 首帧 + 第 1/10/30 秒 + 每 30 秒 |
| 编码出帧 | `[VideoCapture] send pts` | 首帧 + 第 1/10/30 秒 + 每 30 秒 |
| 解码送帧 | `[VideoRender] decode receive frame userID` | 首帧 + 第 1/5/10/30 秒 + 每 30 秒 |

---

## 五、进房/退房（重要）

### 进房流程概述

Native 进房是一个多步骤的信令交互过程：

```
JoinRoom
   ↓
查询接口机请求 (0x1) ──超时──→ 重走进房流程（没超20s）
   ↓                           ↓
收到接口机应答              超过20s → 结束流程通知外部
   ↓
云控配置请求
   ↓
收到云控应答
   ↓
发起进房请求 (0x109) ──超时──→ 轮询下一接口机
   ↓                           ↓
收到正常回包               所有接口机都发送了 → 重走流程
   ↓
进房成功
```

### 进房日志关键词对照表（重要）

绿色填充的是 Kibana 在线日志关键词：

| 阶段 | 线上日志关键词 | Kibana 搜索关键词 |
|-----|--------------|-----------------|
| **调用进房接口** | `TRTCNetwork: EnterRoom` | `Enter room with` |
| **请求信令服务器 0x1** | `Signal: requestACCIPandSign` | `QueryAccessServerInfo` |
| **收到 0x1 应答** | `Signal: handleResponseACCIPandSign` | `Connected to SignalServer` |
| **请求云控拉取配置** | `Signal: requestQueryConfig` | `RequestQueryConfig` |
| **收到云控应答** | `Signal: handleResponseQueryConfig` | `QueryConfigResponse` |
| **请求接口机 0x109** | `Signal: requestEnterRoom` | `EnterRoomRequest` |
| **进房成功** | `Signal: handleACC_C2S_Rsp_EnterRoom` | `Enter room success with duration` |
| **进房失败** | iOS/Mac: `trtccloud onerror`<br>Android: `onError callback`<br>Windows: `onEnterRoom err` | `Enter room failed with error code` |

### 进房排障搜索顺序

按以下顺序搜索定位进房问题：

1. **`Enter room with`** - 查看进房参数（appid/roomid 等信息）
2. **`QueryAccessServerInfo`** - 查看发起请求的 IP 及使用的协议
3. **`Connected to SignalServer`** - 查看收到了哪个接口机的应答
4. **`RequestQueryConfig`** - 查看发起请求的 IP 及使用的协议
5. **`QueryConfigResponse`** - 查看云控正常应答信息
6. **`EnterRoomRequest`** - 查看发起进房请求的 IP 及使用的协议
7. **`Enter room success`** - 查看进房成功应答信息
8. **`Enter room failed`** - 查看进房失败信息

### 超时重试场景

| 场景 | 搜索关键词 | 说明 |
|-----|----------|-----|
| **0x1 超时后重走流程** | `QueryAccessRequest Timeout observed` | 查看 0x1 超时后重走进房流程信息 |
| **0x109 超时后重走流程** | `EnterRoomRequest Timeout observed` | 查看 0x109 超时后重走进房流程信息 |

### 进房成功日志示例

```
[I][01-15/10:30:45.123+8.0][12345,67890][signal_manager.cc:xxx]@abc Enter room success with duration: 1234ms
```

**关键信息**:
- `duration` - 进房耗时（毫秒）
- 正常进房耗时应在 1-3 秒内

### 进房失败日志示例

```
[E][01-15/10:30:45.123+8.0][12345,67890][xxx.cc:xxx] Enter room failed with error code: -3301
```

**常见错误码**:

| 错误码 | 含义 | 处理建议 |
|-------|-----|---------|
| `-3301` | 进房失败 | 检查 sdkAppId 和 roomId |
| `-100018` | UserSig 过期 | 重新生成 UserSig |
| `-3308` | 房间不存在 | 确认房间号正确 |

### 退房
**搜索关键词**: `exitRoom`, `ExitRoom`, `LeaveRoom`, `Exit room`

### 房间事件
**搜索关键词**: `onRemoteUserEnterRoom`, `onRemoteUserLeaveRoom`, `RoomEvent`

---

## 六、常见错误场景

### UserSig 过期
**特征日志**:
```
ErrorCode: -100018, Reason: usersig expired
```
**解决方案**: 重新生成 UserSig

### 进房失败
**搜索关键词**: `enterRoom`, `failed`, `ErrorCode`

检查点:
1. sdkAppId 是否正确
2. UserSig 是否有效且未过期
3. 网络是否通畅

---

## 七、排障搜索策略

| 问题类型 | 优先搜索关键词 |
|---------|--------------|
| **进房问题** | `Enter room with` → `QueryAccessServerInfo` → `EnterRoomRequest` → `Enter room success` / `Enter room failed` |
| **进房超时** | `QueryAccessRequest Timeout observed`, `EnterRoomRequest Timeout observed` |
| **UserSig 问题** | `usersig`, `expired`, `-100018` |
| **音频问题** | `Audio`, `Microphone`, `Mute` |
| **本地渲染黑屏** | `start camera successfully` → `[VideoCapture] camera capture frameIndex` → `TXCRenderView init` → `[VideoRender] userID:` → `AppState:` |
| **本地无上行** | `VideoEncoder: Start successfully` → `[VideoCapture] encode pts` → `[VideoCapture] send pts` |
| **远端播放黑屏** | `Remote-VideoDecoder: Start` → `[VideoRender] decode receive frame` → `TXCRenderView init` → `[VideoRender] userID:` |
| **摄像头采集** | `start camera successfully` → `[VideoCapture] camera capture frameIndex` → `session interrupted` |
| **屏幕采集** | `start screen` → `onScreenShareStart` → `[VideoCapture] screen capture` |
| **自定义采集** | `EnableCustomVideoCapture` → `[VideoCapture] custom capture` → `input video frame error` |
| **编码问题** | `VideoEncoder: Start` → `[VideoCapture] encode pts` → `[VideoCapture] send pts` → `TXCHWVideoEncoder` + `[E]` |
| **解码问题** | `Remote-VideoDecoder: Start` → `[VideoRender] decode receive frame` → `TXCHWVideoDecoder` / `TXCSWVideoDecoder` |
| **渲染打点** | `[VideoRender] userID:`, `TXCRenderView layoutSubviews` |
| **前后台状态** | `AppState:` |
| **首帧问题** | `first frame`, `FirstFrame`, `Render first frame`, `OnVideoCaptureFirstFrame`, `Screen capture first frame` |
| **网络问题** | `Network`, `Signal`, `timeout`, `Connected to SignalServer` |
| **云控问题** | `RequestQueryConfig`, `QueryConfigResponse` |

> **小程序问题排障**：请参考 [miniprogram-log-patterns.md](./miniprogram-log-patterns.md)

---

## 八、日志级别含义

| 级别 | 标识 | 含义 |
|-----|------|------|
| INFO | `[I]` | 正常信息 |
| WARN | `[W]` | 警告，需关注 |
| ERROR | `[E]` | 错误，需处理 |

**排障优先级**: 先搜索 ERROR 级别日志，再搜索 WARN 级别

---

## 九、与 Web 端的对比

| 功能 | Web 端关键词 | Native 端关键词 |
|-----|-------------|----------------|
| 进房请求 | `enterRoom()`, `Join() => joining room` | `Enter room with`, `EnterRoomRequest` |
| 进房成功 | `Join room success` | `Enter room success with duration` |
| 进房失败 | `failed`, `error` | `Enter room failed with error code` |
| SDK 版本 | `TRTC Web SDK Version` | SDK 版本在日志头部 |
| 信令请求 | `Received event:` | `Signal:`, `Command:`, `Request` |
| 接口机连接 | N/A | `Connected to SignalServer`, `QueryAccessServerInfo` |
| 云控配置 | N/A | `RequestQueryConfig`, `QueryConfigResponse` |
| 首帧 | `Render first frame` | `Render first frame` |
| 错误 | `<ERROR>`, `failed` | `[E]`, `ErrorCode:`, `error code` |

---

## 十、Native 特有场景

### iOS 音频会话
**搜索关键词**: `AVAudioSession`, `AudioSession`, `interrupt`

iOS 特有的音频会话管理，常见问题：
- 来电打断
- 其他 App 抢占音频
- 音频路由切换

### Android 权限
**搜索关键词**: `Permission`, `RECORD_AUDIO`, `CAMERA`

Android 特有的权限问题：
- 麦克风权限未授权
- 摄像头权限未授权
