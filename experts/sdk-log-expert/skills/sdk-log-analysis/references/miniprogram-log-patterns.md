# 微信小程序 TRTC 日志模式详解

微信小程序使用 `live-pusher` 和 `live-player` 原生组件，底层调用 TRTC Native SDK。

## 适用范围

| 平台 | 是否适用 | 备注 |
|-----|---------|-----|
| 微信小程序 | ✅ | 使用本文档 |
| 支付宝小程序 | ✅ | 使用本文档 |
| UniApp (小程序端) | ✅ | 使用本文档 |

> ⚠️ **重要**：小程序底层使用 Native SDK，分析时**必须同时加载 native-log-patterns.md**！
> - 本文档：小程序特有的组件、协议、JS 适配层知识
> - native-log-patterns.md：进房信令、编解码、底层 SDK 日志

## 依赖说明

分析小程序日志时，需要同时具备以下知识（如尚未加载，请加载）：
- 本文档：小程序特有的组件和协议
- `native-log-patterns.md`：底层 SDK 日志模式

---

## 一、小程序组件概述

### live-pusher（推流组件）

用于采集本地音视频并推送到 TRTC 房间。

```html
<live-pusher
  url="room://cloud.tencent.com/rtc?sdkappid=xxx&roomid=xxx&userid=xxx&usersig=xxx"
  autopush="{{true}}"
  mode="RTC"
/>
```

### live-player（拉流组件）

用于播放远端用户的音视频流。

```html
<live-player
  src="room://cloud.tencent.com/rtc?sdkappid=xxx&roomid=xxx&userid=remoteUser&usersig=xxx&streamtype=main"
  autoplay="{{true}}"
  mode="RTC"
/>
```

---

## 二、推流/拉流模式（重要）

### 自动模式 vs 手动模式

| 模式 | 推流（live-pusher） | 拉流（live-player） |
|-----|-------------------|-------------------|
| **自动模式** | `autopush="true"`，设置 URL 后自动推流 | `autoplay="true"`，设置 URL 后自动拉流 |
| **手动模式** | `autopush="false"`，需调用 `LivePusherContext.start()` | `autoplay="false"`，需调用 `LivePlayerContext.play()` |

#### 自动模式

```javascript
// 推流：只需更新 URL，自动开始推流
this.setData({
  pusherUrl: 'room://cloud.tencent.com/rtc?sdkappid=xxx&...'
});

// 拉流：只需更新 URL，自动开始拉流
this.setData({
  playerUrl: 'room://cloud.tencent.com/rtc?sdkappid=xxx&...'
});
```

#### 手动模式

```javascript
// 推流：需要手动调用 start
const pusherContext = wx.createLivePusherContext();
this.setData({ pusherUrl: '...' });
pusherContext.start();

// 拉流：需要手动调用 play
const playerContext = wx.createLivePlayerContext('playerId');
this.setData({ playerUrl: '...' });
playerContext.play();
```

### 排障关注点

| 问题 | 检查点 |
|-----|-------|
| 推流不启动 | 检查 `autopush` 属性，手动模式需调用 `start()` |
| 拉流不启动 | 检查 `autoplay` 属性，手动模式需调用 `play()` |
| 自动播放失败 | 小程序对自动播放有限制，检查用户交互触发 |

---

## 三、自动订阅模式（recvmode）

### recvmode 参数详解

在 `live-pusher` 的 URL 中通过 `recvmode` 控制自动订阅行为：

| 值 | 含义 | 适用场景 |
|---|-----|---------|
| `1` | 自动接收房间里音视频（默认） | 视频通话，进房秒开 |
| `2` | 仅自动接收音频 | 语音聊天，节省视频流量 |
| `3` | 仅自动接收视频 | 特殊场景 |
| `4` | 音视频都不自动接收 | 需要手动订阅 |

### 费用提示

> ⚠️ SDK 默认进房后自动接收音视频（recvmode=1）。若您主要用于语音聊天等没有自动接收视频数据需求的场景，建议设置 `recvmode=2`，以免产生预期之外的视频时长费用。

### 手动订阅控制

当 `recvmode=4` 时，需要手动控制订阅：

| 属性/方法 | 含义 |
|----------|-----|
| `autoRecvAudio=true` | 自动接收音频（默认 true） |
| `autoRecvAudio=false` | 需调用 `muteRemoteAudio` 控制 |
| `autoRecvVideo=true` | 自动接收视频（默认 true） |
| `autoRecvVideo=false` | 需调用 `startRemoteView`/`stopRemoteView` 控制 |

### 排障搜索

```
# 检查订阅模式
recvmode=

# 检查是否有手动订阅调用
muteRemoteAudio
startRemoteView
stopRemoteView
```

---

## 四、TRTC-ROOM 协议详解

### 推流 URL 格式（live-pusher）

```
room://cloud.tencent.com/rtc?sdkappid=1400182283&roomid=586999&userid=user123&usersig=xxx&appscene=videocall&encsmall=0&cloudenv=PRO&enableBlackStream=0&streamid=&userdefinerecordid=&privatemapkey=&pureaudiomode=1&recvmode=1
```

**历史版本域名**: `room://rtc.tencent.com?...`

### 拉流 URL 格式（live-player）

```
room://cloud.tencent.com/rtc?sdkappid=1400182283&roomid=586999&userid=remoteUser&usersig=xxx&appscene=videocall&streamtype=main
```

---

## 五、推流参数详解

| 参数 | 含义 | 是否必填 | 默认值 | 排障关注点 |
|-----|------|---------|-------|-----------|
| `room://` | ROOM 协议前缀 | 必填 | - | 检查协议前缀是否正确 |
| `cloud.tencent.com` | 域名 | 必填 | - | 历史版本用 `rtc.tencent.com` |
| `sdkappid` | 腾讯云音视频应用 ID | 必填 | - | ⚠️ 检查是否正确 |
| `roomid` | 房间 ID（数字类型） | 二选一 | - | 与 `strroomid` 二选一 |
| `strroomid` | 房间 ID（字符串类型） | 二选一 | - | 与 `roomid` 二选一 |
| `userid` | 用户 ID | 必填 | - | ⚠️ 检查用户标识 |
| `usersig` | 用户签名 | 必填 | - | ⚠️ 检查是否过期 |
| `appscene` | 场景模式 | 可选 | `live` | 见下表 |
| `cloudenv` | 环境 | 可选 | `PRO` | `0`=pro, `1`=dev, `2`=uat, `3`=ccc |
| `pureaudiomode` | 纯音频模式 | 可选 | 不填 | `1`=纯音频可旁路, `2`=纯音频+录制MP3 |
| `encsmall` | 是否开启小流 | 可选 | `false/0` | `1`=开启双路编码 |
| `enableBlackStream` | 是否开启黑帧 | 可选 | `false/0` | 无视频时推黑帧 |
| `streamid` | 指定旁路直播流 ID | 可选 | 空 | CDN 直播相关 |
| `userdefinerecordid` | 自定义录制 ID | 可选 | 空 | 云端录制相关 |
| `privatemapkey` | 进房权限密钥 | 可选 | 空 | 权限控制相关 |
| `recvmode` | 自动订阅模式 | 可选 | `1` | 见第三节 |

### appscene 场景模式

| 值 | 场景 | 说明 |
|---|-----|------|
| `videocall` | 视频通话 | 只推音频时不能旁路 |
| `live` | 在线直播 | 只推音频时不能旁路 |
| `audiocall` | 语音通话 | 只推音频时可旁路 |
| `voicechatroom` | 语音聊天室 | 只推音频时可旁路 |

---

## 六、拉流参数详解

| 参数 | 含义 | 是否必填 | 默认值 |
|-----|------|---------|-------|
| `sdkappid` | 应用 ID | 必填 | - |
| `roomid` / `strroomid` | 房间 ID | 必填 | - |
| `userid` | 远端用户 ID | 必填 | - |
| `usersig` | 用户签名 | 必填 | - |
| `streamtype` | 流类型 | 必填 | `main` |
| `appscene` | 场景模式 | 可选 | `live` |
| `cloudenv` | 环境 | 可选 | `PRO` |
| `privatemapkey` | 权限密钥 | 可选 | 空 |

### streamtype 流类型

| 值 | 含义 |
|---|-----|
| `main` | 大流（高清） |
| `small` | 小流（低清） |
| `aux` | 辅流（屏幕分享） |

---

## 七、日志分层与关键词（重要）

小程序日志分为多层，排障时需要根据问题定位到具体层级。

### 日志层级结构

```
┌─────────────────────────────────────────────────────────┐
│  小程序业务层（live-pusher / live-player 组件）          │
├─────────────────────────────────────────────────────────┤
│  JS 适配层（V2TXLivePusherJSAdapter / V2TXLivePlayerJSAdapter）│
├─────────────────────────────────────────────────────────┤
│  播放层（V2_Pusher / V2_Player）                         │
├─────────────────────────────────────────────────────────┤
│  底层 SDK（TXTRTCPlayerImpl 等）                         │
└─────────────────────────────────────────────────────────┘
```

### 各层级关键词

| 层级 | 推流关键词 | 拉流关键词 | 说明 |
|-----|----------|----------|------|
| **JS 适配层** | `V2TXLivePusherJSAdapter` | `V2TXLivePlayerJSAdapter` | 小程序调用 SDK 的适配层 |
| **播放层** | `V2_Pusher` | `V2_Player` | 音视频推拉流处理层 |
| **底层 SDK** | `TXTRTCPusherImpl` | `TXTRTCPlayerImpl` | TRTC 底层实现 |

---

### JS 适配层日志（V2TXLivePlayerJSAdapter）

**搜索关键词**：`V2TXLivePlayerJSAdapter`, `V2TXLivePusherJSAdapter`

#### 拉流日志示例

| 关键日志 | 含义 |
|---------|------|
| `operateLivePlayerWithType: play` | 开始播放 |
| `operateLivePlayerWithType: stop` | 停止播放 |
| `onPlayEvent: event[2001]` | 连接服务器成功 |
| `onPlayEvent: event[2004]` | 视频播放开始 |
| `onPlayEvent: event[2008]` | 启用 H264 硬件解码器 |
| `onPlayEvent: event[2009]` | 分辨率变化 |
| `onPlayEvent: event[2003]` | 渲染首帧视频 |
| `onPlayEvent: event[2026]` | 视频播放开始 |
| `onAudioPlayStatusUpdate` | 音频播放状态更新 |
| `onVideoPlayStatusUpdate` | 视频播放状态更新 |
| `enterBackground: isPlaying[1] blsBackgroundInterrupted[0] blsManualPause[0]` | 进入后台状态 |
| `msg[connect server success, serverIP: xxx.xxx.xxx.xxx]` | 连接服务器成功，显示 IP |
| `msg[Enable default H264 hardware decoder.]` | 启用 H264 硬件解码器 |
| `msg[Video playback started]` | 视频播放已开始 |
| `msg[Render the first video packet(IDR)]` | 渲染首个视频关键帧 |
| `msg[Resolution changed]` | 分辨率发生变化 |

#### 推流日志示例

| 关键日志 | 含义 |
|---------|------|
| `startPusher` | 开始推流 |
| `stopPushInner` | 停止推流 |
| `pause push` | 暂停推流 |
| `enableMicrophone:true/false` | 麦克风开关状态 |
| `enableCamera:true/false` | 摄像头开关状态 |

---

### 播放层日志（V2_Player / V2_Pusher）

**搜索关键词**：`V2_Player`, `V2_Pusher`

#### V2_Player 日志示例

| 关键日志 | 含义 |
|---------|------|
| `setObserver:` | 设置观察者 |
| `setRenderView:` | 设置渲染视图 |
| `pauseVideo` | 暂停视频 |
| `resumeVideo` | 恢复视频 |
| `pauseAudio` | 暂停音频 |
| `resumeAudio` | 恢复音频 |
| `setRenderRotation: 0(0:0 1:90: 2:180 3:270)` | 设置渲染旋转角度 |
| `setRenderFillMode: 0` | 设置渲染填充模式 |
| `setCacheParams:maxTime:` | 设置缓存参数 |
| `enableVolumeEvaluation:` | 启用音量评估 |
| `setProperty:value:` | 设置属性 |
| `startPlay` | 开始播放，URL 为 `room://cloud.tencent.com/rtc?...` |
| `stopPlay` | 停止播放 |
| `create [TXTRTCPlayerImpl:0x...]` | 创建 TRTC 播放器实例 |
| `setPlayURLType, value:-1` | 设置播放 URL 类型 |
| `key:enableRecvSEIMessage` | 启用接收 SEI 消息 |
| `key:setPlayURLType` | 设置播放 URL 类型 |

---

### 事件码速查

| 事件码 | 含义 | 层级 |
|-------|------|-----|
| `2001` | 连接服务器成功 | JS 适配层 |
| `2003` | 渲染首帧视频 | JS 适配层 |
| `2004` | 视频播放开始 | JS 适配层 |
| `2008` | 启用 H264 硬件解码器 | JS 适配层 |
| `2009` | 分辨率变化 | JS 适配层 |
| `2026` | 视频播放开始 | JS 适配层 |
| `2105` | 视频卡顿（jitterbuffer 不足） | JS 适配层 |

---

### URL 参数搜索

| 搜索关键词 | 用途 |
|-----------|-----|
| `room://cloud.tencent.com/rtc` | 定位 TRTC-ROOM 协议推拉流 |
| `room://rtc.tencent.com` | 定位历史版本 URL |
| `sdkappid=` | 提取应用 ID |
| `roomid=` | 提取房间号 |
| `userid=` | 提取用户 ID |
| `usersig=` | 检查签名参数 |
| `appscene=` | 检查场景配置 |
| `streamtype=` | 检查拉流类型 |
| `pureaudiomode=` | 检查纯音频模式 |
| `encsmall=1` | 检查是否开启小流 |
| `recvmode=` | 检查订阅模式 |
| `autopush` | 检查推流模式 |
| `autoplay` | 检查拉流模式 |

### 组件相关搜索

| 搜索关键词 | 用途 |
|-----------|-----|
| `live-pusher` | 定位推流组件相关日志 |
| `live-player` | 定位拉流组件相关日志 |
| `LivePusherContext` | 定位推流 API 调用 |
| `LivePlayerContext` | 定位拉流 API 调用 |
| `pusher.start` | 手动启动推流 |
| `player.play` | 手动启动拉流 |

---

## 八、常见问题排障

| 问题 | 搜索关键词 | 检查点 |
|-----|----------|-------|
| **进房失败** | `room://`, `sdkappid`, `usersig` | 检查 URL 参数完整性和正确性 |
| **推流不启动** | `autopush`, `LivePusherContext`, `start` | 手动模式需调用 start() |
| **拉流不启动** | `autoplay`, `LivePlayerContext`, `play` | 手动模式需调用 play() |
| **拉流黑屏** | `streamtype=`, `userid=` | 检查远端用户 ID 和流类型是否正确 |
| **无声音** | `pureaudiomode=`, `appscene=`, `recvmode=` | 检查音频模式和订阅配置 |
| **旁路失败** | `appscene=`, `streamid=` | `videocall`/`live` 只推音频时不能旁路 |
| **录制问题** | `userdefinerecordid=`, `pureaudiomode=` | 检查录制 ID 和模式 |
| **小流问题** | `encsmall=`, `streamtype=small` | 检查是否开启小流编码 |
| **订阅问题** | `recvmode=`, `autoRecvAudio`, `autoRecvVideo` | 检查订阅模式配置 |
| **意外计费** | `recvmode=1` | 语音场景建议用 recvmode=2 避免视频计费 |

---

## 九、小程序与其他端的区别

| 特性 | 小程序 | iOS/Android Native | Web |
|-----|-------|-------------------|-----|
| 进房方式 | URL 参数传递 | API 调用 | API 调用 |
| 组件 | `live-pusher`/`live-player` | SDK 内部渲染 | HTML video 标签 |
| 日志特征 | URL 中包含完整参数 | 分散在多条日志中 | API 调用日志 |
| 调试方式 | 解析 URL 参数 | 搜索 API 调用日志 | 搜索 API 调用日志 |
| 推流控制 | `autopush` / `LivePusherContext.start()` | `startLocalPreview()` | `publish()` |
| 拉流控制 | `autoplay` / `LivePlayerContext.play()` | `startRemoteView()` | `subscribe()` |
| 订阅模式 | `recvmode` URL 参数 | `setDefaultStreamRecvMode()` | 自动订阅 |

---

## 十、其他小程序协议（参考）

### TRTC 协议（私有，桌面端不支持）

```
推流: trtc://cloud.tencent.com/push/streamId?sdkappid=xxx&userid=xxx&usersig=xxx
拉流: trtc://cloud.tencent.com/play/streamId?sdkappid=xxx&userid=xxx&usersig=xxx
```

| 参数 | 含义 |
|-----|------|
| `push` / `play` | 推流/拉流标识 |
| `streamId` | 流 ID |
| `sdkappid` | 应用 ID |
| `userid` | 用户 ID |
| `usersig` | 用户签名 |

### RTMP-ROOM 协议（私有，Mac 不支持）

```
推流: room://cloud.tencent.com?sdkappid=xxx&roomid=xxx&userid=xxx&roomsig=xxx&bizbuf=xxx
拉流: room://cloud.tencent.com/webrtc/sdkappid_roomid_userid_main
```

| 参数 | 含义 |
|-----|------|
| `roomsig` | 房间签名（与 usersig 不同） |
| `bizbuf` | 业务自定义信息 |
| `stream_type` | 流类型（main/aux） |

---

## 十一、常见问题排障指南（重要）

> ⚠️ **转人工条件**：当根据 Kibana 日志无法定位问题时，需引导用户上传更详细的微信日志后转人工处理：
> - 微信 → 我的 → 设置 → 帮助与反馈 → 右上角扳手图标 → 上传日志
> - 记录用户**微信号**和**上传时间点**

---

### 1. 上行问题（推流端）

#### 1.1 上行无声音

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| iOS/Mac | `enableMicrophone:false` | 客户没有开麦克风 | 开启麦克风 |
| Android | `enableMicrophone:false` | 客户没有开麦克风 | 开启麦克风 |
| iOS/Mac | `-1317` 错误码 | 没有麦克风权限 | 引导用户开启麦克风权限 |
| Android | `micphone not authorized` 或 `microphone start error` | 没有麦克风权限 | 引导用户开启麦克风权限 |
| iOS/Mac | `operateLivePlayerWithType: stop` | 业务主动调用 stop | 确认是用户触发还是微信客户端导致 |
| Android | `pause push` 或 `stopPushInner` | 业务主动调用 stop | 确认是用户触发还是微信客户端导致 |

**搜索关键词**：`enableMicrophone`, `-1317`, `micphone not authorized`, `microphone start error`, `pause push`, `stopPushInner`

#### 1.2 上行无画面

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| iOS/Mac | `enableCamera:false` | 客户没有开摄像头 | 开启摄像头 |
| Android | `enableCamera:false` | 客户没有开摄像头 | 开启摄像头 |
| iOS/Mac | `-1314` 错误码 | 没有摄像头权限 | 引导用户开启摄像头权限 |
| Android | `camera not authorized` | 没有摄像头权限 | 引导用户开启摄像头权限 |

**搜索关键词**：`enableCamera`, `-1314`, `camera not authorized`

#### 1.3 推流不生效

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| Android | 没有 `startPusher` | 没有调用 start | 引导用户调用 start |
| iOS/Android | `onEnterRoom failed, error` | 进房失败 | 查看错误码确定原因 |

**搜索关键词**：`startPusher`, `onEnterRoom failed`

---

### 2. 下行问题（拉流端）

#### 2.1 下行无声音

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| iOS/Mac | `muteAudio:1` | mute 了音频 | 引导用户取消 mute |
| Android | `operate live player.[name:mute` | mute 了音频 | 引导用户取消 mute |

**搜索关键词**：`muteAudio`, `operate live player.[name:mute`

> 💡 如果日志正常，检查仪表盘是否有下发数据，可能是上行端问题。

#### 2.2 下行无画面

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| Android | `operate live player.[name:pause` | 暂停了视频 | 引导用户取消 pause |

**搜索关键词**：`operate live player.[name:pause`

> 💡 如果日志正常，检查仪表盘是否有下发数据，可能是上行端问题。

#### 2.3 下行卡顿

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| iOS/Mac | `onPlayEvent: event[2105]` | 视频卡顿，jitterbuffer 数据不足 | 检查网络情况 |
| Android | `onPlayEvent event: 2105` 或 `onWarning code: 2105` | 视频卡顿，jitterbuffer 数据不足 | 检查网络情况 |

**搜索关键词**：`2105`, `OnWarning: code->2105`, `onPlayEvent`

#### 2.4 进房失败

| 平台 | 关键日志 | 说明 | 解决方案 |
|-----|---------|------|---------|
| iOS/Mac | `onEnterRoom` 失败或 `onError` | 进房失败 | 查看错误码确定原因 |
| Android | `onEnterRoom` 失败或 `onError` | 进房失败 | 查看错误码确定原因 |

**搜索关键词**：`onEnterRoom`, `onError`

---

### 3. 自动/手动模式问题（高频问题）

#### 3.1 手动模式未调用 start

**问题表现**：设置 `autopush=false`，更新 URL 后无法推流

**原因**：手动模式必须调用 `LivePusherContext.start()` 或 `LivePlayerContext.play()`

**搜索关键词**：`autopush`, `autoplay`, `startPusher`, `start`

**解决方案**：
```javascript
// 手动模式必须调用 start
const pusherContext = wx.createLivePusherContext();
pusherContext.start();
```

#### 3.2 自动模式先 start 再设置 URL

**问题表现**：先调用 `start()`，再设置 URL，无法播放

**原因**：先 start 会提示 `start failed`，后设置 URL 更新时无法起播

**搜索关键词**：`start failed`

**解决方案**：自动模式下先设置 URL，再依赖自动播放；或使用手动模式先设置 URL 再 start

---

### 4. 时序问题

#### 4.1 先推流再开摄像头导致黑屏

**问题表现**：`enableCamera=false` 时先 `startPush`，再 `startCamera` 预览，然后 `enableCamera=true`，出现黑屏

**搜索关键词**：`enableCamera`, `startPush`, `startCamera`

#### 4.2 频繁 start/stop 导致异常

**问题表现**：高频率调用 `start` → `stop` → `start`，推流显示画面异常

**原因**：小程序使用 surface 同层渲染，stop 时 surface 没有释放干净

**搜索关键词**：`start`, `stop`

---

### 5. 退后台问题

#### 5.1 退后台没有声音

**问题表现**：点击小圈圈或按 Home 键退后台，没有声音

**原因**：小程序退后台不会触发退房，但会影响音视频

**推流端行为**：
- 设置了 `wait-image-url`：触发垫片推流（推静态图片）
- 未设置 `wait-image-url`：暂停音视频上行

**拉流端行为**：停止播放

**搜索关键词**：`wait-image-url`, `pausePusher`, `visibility`

#### 5.2 没有上行却出现垫片推流

**问题表现**：没有开启麦克风/摄像头，退后台却出现垫片推流

**原因**：退后台时设置了 `waiting-image-url`，但没有判断是否开启过麦克风/摄像头就触发了 `pausePusher`

**搜索关键词**：`waiting-image-url`, `pausePusher`

---

### 6. 其他问题

#### 6.1 截图一直失败

**问题表现**：`snapShot` 一直提示错误

**原因**：本地存储权限没有打开，无法保存图片

**解决方案**：引导用户开启本地存储权限

**搜索关键词**：`snapShot`, `snapshot`

---

## 十二、错误码速查

### 常见错误码

| 错误码 | 含义 | 解决方案 |
|-------|-----|---------|
| `-1314` | 摄像头权限未授权（iOS/Mac） | 引导用户开启摄像头权限 |
| `-1317` | 麦克风权限未授权（iOS/Mac） | 引导用户开启麦克风权限 |
| `2105` | 视频卡顿，jitterbuffer 数据不足 | 检查网络情况 |

### 权限相关日志

| 平台 | 问题 | 关键日志 |
|-----|-----|---------|
| iOS/Mac | 摄像头权限 | `-1314` |
| iOS/Mac | 麦克风权限 | `-1317` |
| Android | 摄像头权限 | `camera not authorized` |
| Android | 麦克风权限 | `micphone not authorized`, `microphone start error` |

---

## 十三、排障搜索策略

| 问题类型 | 优先搜索关键词 |
|---------|--------------|
| **进房问题** | `room://cloud.tencent.com/rtc` → `sdkappid=` → `usersig=` → `onEnterRoom` → `onError` |
| **上行无声** | `enableMicrophone` → `-1317` → `micphone not authorized` → `pause push` |
| **上行无画面** | `enableCamera` → `-1314` → `camera not authorized` |
| **下行无声** | `muteAudio` → `operate live player.[name:mute` |
| **下行无画面** | `operate live player.[name:pause` → `streamtype=` |
| **下行卡顿** | `2105` → `onPlayEvent` → `OnWarning` |
| **推流不生效** | `startPusher` → `autopush` → `start failed` |
| **拉流不生效** | `autoplay` → `LivePlayerContext` → `start failed` |
| **退后台问题** | `wait-image-url` → `pausePusher` → `visibility` |
| **权限问题** | `-1314`, `-1317`, `not authorized` |
