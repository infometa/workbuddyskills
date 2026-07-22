# Web 端日志模式详解

本文档包含 TRTC Web SDK 的完整日志特征，用于精准识别和分析日志含义。

## 适用范围

| 环境 | 是否适用 | 备注 |
|-----|---------|-----|
| Chrome/Firefox/Safari 浏览器 | ✅ | 直接使用本文档 |
| Electron 渲染进程 | ✅ | 直接使用本文档 |
| App 内嵌 WebView | ✅ | 直接使用本文档 |
| H5 页面 | ✅ | 直接使用本文档 |
| UniApp (H5 模式) | ✅ | 直接使用本文档 |

> ⚠️ **判断依据**：代码是否运行在浏览器或 WebView 中？是 → 使用本文档

---

## 日志格式说明

Web 端日志通常格式为：
```
[时间戳][IP地址] <日志级别> [↑/↓标识|用户ID] 日志内容
```

- `↑` 表示上行/本地
- `↓` 表示下行/远端
- `t1/r1` 等是实例 ID
- `at` 表示音频轨道，`vt` 表示视频轨道

---

## 一、环境与初始化

### SDK 版本
**关键词**: `TRTC Web SDK Version`
```
[2025-08-04 13:51:39.125][68.116.169.30] <INFO> TRTC Web SDK Version: 5.6.3
```
**解读**: SDK 版本号，排障时需确认版本

### 浏览器信息
**关键词**: `UA:`
```
[2025-10-27 19:18:48.756][191.209.174.30] <INFO> UA: Mozilla/5.0 (Phone; OpenHarmony 5.0) AppleWebKit/537.36...
```
**解读**: 浏览器 UserAgent，用于判断浏览器兼容性

### 能力检测
**关键词**: `TrtcStats`
```
TrtcStats-{"browser":"Chrome/138.0.0.0","os":"MacOS","trtc":{"webRTC":true,"webSocket":true,"screenShare":true,"webAudio":false,"h264Encode":false,"h264Decode":true,"vp8Encode":true,"vp8Decode":true},"devices":{"microphone":7,"camera":1}}
```
**解读**: 
- `webRTC/webSocket/screenShare/webAudio` - 基础能力支持
- `h264Encode/h264Decode` - H264 编解码支持（false 可能导致兼容性问题）
- `vp8Encode/vp8Decode` - VP8 编解码支持
- `microphone/camera` - 设备数量

### CPU 负载
**关键词**: `cpu:`
```
<INFO> cpu: critical
```
**状态值**:
- `nominal` - 负载低
- `fair` - 负载正常
- `critical` - **负载过载**，可能导致编码质量下降

---

## 二、进房/退房

### 请求进房
**关键词**: `enterRoom()`
```
[↑t1|614302_630334946] enterRoom() [{"strRoomId":"Rom_2_4_614302","sdkAppId":1600090419,"userId":"614302_630334946","userSig":"hided","autoReceiveAudio":false,"autoReceiveVideo":false}]
```
**参数说明**:
- `strRoomId` - 字符串房间号
- `roomId` - 数字房间号
- `autoReceiveAudio/Video` - 是否自动接收音视频

### 加入房间
**关键词**: `Join() => joining room`
```
[↑r1|101286] Join() => joining room: T_R_101286 useStringRoomId: true scene: rtc role: anchor
```
**参数说明**:
- `scene: rtc` - 实时通话场景
- `scene: live` - 互动直播场景
- `role: anchor` - 主播
- `role: audience` - 观众

### 进房成功
**关键词**: `Join room success`
```
[↑r1|603397c7d76367b6ab431599f8d5c9d2e78dbb] Join room success, start heartbeat
```
**解读**: 进房成功，开始与服务端保持心跳

### 退房
**关键词**: `exitRoom()`, `leave()`
```
[↑t1|4_a_22392] exitRoom() success
[↑c2|102248_1129696_122691991_PC] leave() => leaving room
```

---

## 三、音频采集与推流

### 开启麦克风
**关键词**: `startLocalAudio()`
```
[↑t1] startLocalAudio() [{"mute":true,"option":{"microphoneId":"f4ac2659..."}}]
[↑t1|4_c_358742721] startLocalAudio() success
```
**参数说明**:
- `publish` - 是否发布到房间
- `mute` - 是否临时关闭麦克风
- `microphoneId` - 指定麦克风设备

### 停止麦克风
**关键词**: `stopLocalAudio()`
```
[↑t1] stopLocalAudio() success
```

### 采集失败
**关键词**: `startLocalAudio() failed`
```
[↑t1|4_c_238550912] startLocalAudio() failed DEVICE_ERROR: NotAllowedError, you have disabled microphone access...
```
**常见错误**:
- `NotAllowedError` - 用户拒绝权限
- `DEVICE_ERROR` - 设备错误

---

## 四、视频采集与推流

### 开启摄像头
**关键词**: `startLocalVideo()`
```
[↑t1] startLocalVideo() [{"camera":"8f6622ce...","view":"id: trtcplayer","resolution":"720p","objectFit":"contain"}]
[↑t1|4_c_358565795] startLocalVideo() success
```
**参数说明**:
- `camera` - 摄像头设备 ID
- `resolution` - 分辨率
- `small` - 是否有小流
- `mirror` - 是否镜像

### 停止摄像头
**关键词**: `stopLocalVideo()`
```
[↑t1] stopLocalVideo() success
```

### 推流失败
**关键词**: `startLocalVideo() failed`, `publish failed`
```
[↑r1|614302_630334946] publish failed: your device does not support H.264 encoding.
```
**常见原因**:
- 设备不支持 H264 编码
- 权限被拒绝

---

## 五、媒体采集（getUserMedia）

### 开始采集
**关键词**: `getUserMedia with constraints`
```
getUserMedia with constraints: {"audio":{"echoCancellation":true,"noiseSuppression":true,"autoGainControl":true,"sampleRate":48000,"channelCount":1},"video":{"facingMode":"environment","width":{"ideal":640},"height":{"ideal":480},"frameRate":15}}
```
**参数说明**:
- `echoCancellation` - 回声消除
- `noiseSuppression` - 噪声抑制
- `autoGainControl` - 自动增益
- `facingMode` - 摄像头朝向（environment=后置）

### 采集重试
**关键词**: `getUserMedia retrying`
```
<WARN> getUserMedia retrying [1/3]
```

### 采集失败
**关键词**: `getUserMedia error`
```
<WARN> getUserMedia error: OverconstrainedError: constraint: deviceId <INITIALIZE_FAILED 0x1004>
<ERROR> [↑vt] getUserMedia error observed Permission denied
```
**常见错误**:
- `OverconstrainedError` - 设备约束不满足
- `Permission denied` - 权限被拒绝
- `NotAllowedError` - 用户拒绝授权

### 重新采集
**关键词**: `recapture`
```
[↑vt|4_c_62938431] recapture trying    // 尝试重新采集
[↑at|4_c_334791189] recapture success  // 重新采集成功
[↑at|4_c_334791189] recapture failed   // 重新采集失败
```

### 采集停止
**关键词**: `track ended`
```
[↑t1-r1-at|4_c_369877696] audio track ended
```
**解读**: 麦克风/摄像头采集停止，SDK 会尝试自动恢复

---

## 六、订阅远端

### 订阅视频
**关键词**: `startRemoteVideo()`
```
[↑t1|101286] startRemoteVideo() [{"userId":"100822","streamType":"main","view":"id: type:htmldivelement"}]
```
**参数说明**:
- `streamType: main` - 主流
- `streamType: auxiliary` - 辅流（屏幕分享）

### 停止订阅
**关键词**: `stopRemoteVideo()`
```
[↑t1|101286] stopRemoteVideo() [{"userId":"100822","streamType":"main"}]
```

### 订阅失败
**关键词**: `startRemoteVideo() failed`
```
[↑t1|4_c_328370922] startRemoteVideo() failed user_2987065299_main OPERATION_FAILED: 'startRemoteVideo' failed, reason: subscribe_change failed: not support h264!.
```
**常见原因**: 设备不支持 H264 解码

### 远端音频控制
**关键词**: `muteRemoteAudio()`
```
[↑t1|101286] muteRemoteAudio() ["100822",false]  // false=恢复播放, true=暂停
```

---

## 七、远端用户状态

### 远端推流
**关键词**: `remote publish`
```
remote publish. state: {"userId":"user_386961067","hasAudio":true,"hasVideo":false,"hasAuxiliary":false,"hasSmall":false,"audioMuted":false,"videoMuted":false,"audioAvailable":true,"videoAvailable":false}
```
**字段说明**:
- `hasAudio/Video` - 是否有音视频流
- `audioMuted/videoMuted` - 是否 muted
- `audioAvailable/videoAvailable` - 音视频是否可用

### 远端流状态更新
**关键词**: `remote publish updated`
```
[↑r1|4_a_22392] remote publish updated: {"userId":"4_c_345664378",...}
```

---

## 八、编解码

### 编码失败
**关键词**: `encode failed`
```
[↑t1-r1-at|3d0cb7e596ee4c5198ba863945e2442eINTERVIEW] encode failed
stat-encode-failed-audio-ios/unknown/unknown
stat-encode-failed-video
```

### 解码失败
**关键词**: `decode failed`
```
[↓vt|2YyaSXCgaIOKPYa5A3xsgNedX5m] decode failed: isPlaying: false framesDecoded: false
stat-decode-failed-video
stat-decode-failed-audio
```

### H264 不支持
**关键词**: `h264 encoder not supported`, `not support h264`
```
<WARN> [↑t1-r1-n|4_c_146611769] h264 encoder not supported
```

### 编码切换
**关键词**: `switch to vp8`, `OpenH264`
```
[↑t1-r1-n|xxx] h264 encoder not working, switch to vp8  // H264 失败，切换 VP8
encoderImplementation change to OpenH264(h264) HWEncoder: false  // 使用软编
```

### 编码质量受限
**关键词**: `qualityLimitationReason`
```
[↑r1|4_a_22392] qualityLimitationReason change to bandwidth
```
**状态值**:
- `bandwidth` - 带宽不足导致质量受限
- `cpu` - CPU 负载高导致质量受限
- `none` - 正常

---

## 九、连接状态

### WebRTC 连接
**关键词**: `connectionState`, `ICE`, `DTLS`
```
[↑t1-r1-spc1|xxx] connectionState: connecting ICE: checking DTLS: new
```
**connectionState 状态**:
- `connecting` - 连接中
- `connected` - 已连接
- `disconnected` - 断开
- `failed` - **连接失败**

### 网络质量
**关键词**: `uplink`, `downlink`
```
[↑q|4_a_22392] uplink 0 -> 1, rtt: 12, loss: 0 ws-rtt: 71
[↑q|4_a_22392] downlink 0 -> 1, rtt: 14, loss: 0 ws-rtt: 67
```
**解读**:
- `rtt` - 延迟（毫秒）
- `loss` - 丢包率（%）
- `ws-rtt` - WebSocket 延迟

---

## 十、播放

### 播放本地流
**关键词**: `play with options`（↑标识）
```
[↑at] play with options: {"muted":true}
```
**注意**: 非耳返场景一般以静音方式播放本地音频流

### 播放远端流
**关键词**: `play with options`（↓标识）
```
[↓at|100822] play with options: {"volume":100}
```

### 数据不足
**关键词**: `unable to provide media output`
```
[↓vt|4_c_345664378] video track is unable to provide media output
[↓at|4_c_345664378] audio track is unable to provide media output
```
**解读**: 远端数据不足以播放，当收到足够数据会变成 unmuted

### 自动播放失败
**关键词**: `handleAutoPlayFailed`
```
[↓t1-r1-at|4_a_55700] handleAutoPlayFailed audio play failed, browser exception: NotAllowedError...
```
**原因**: 浏览器自动播放策略限制

### 渲染首帧
**关键词**: `Render first frame`
```
Video: Render first frame. width:540, height:960, reason:StartRendering
```

---

## 十一、设备管理

### 麦克风列表
**关键词**: `microphones:`
```
<INFO> microphones: [{"deviceId":"4f0494e61a74308e...","groupId":"2fa37884","label":"MacBook Pro麦克风 (Built-in)"},...]
```

### 摄像头列表
**关键词**: `cameras:`
```
<INFO> cameras: [{"deviceId":"d0b64e0b9044ce89...","groupId":"c3f41dc1c718947c...","label":"罗技高清网络摄像机 C930c (046d:0891)"},...]
```

### 扬声器列表
**关键词**: `speakers:`
```
<INFO> speakers: default: Default - 扬声器 (Realtek Audio), ...
```

### 切换视频输入
**关键词**: `change video input`
```
[↑vm] change video input HD User Facing (0408:a061)
```

### 设置扬声器
**关键词**: `_setCurrentSpeaker()`
```
[↑t1] _setCurrentSpeaker() ["a9e2ff4e221397a04bf621bb638f0431f7a3927f154eac6671246dbcc0390c87"]
```

### 设置采集设备
**关键词**: `setOutputMediaStreamTrack`
```
[↑at] setOutputMediaStreamTrack 4f0494e61a74308e... "田中豪的iPhone (2)"的麦克风
```

### 设备增删
**关键词**: `audioOutputAdded`, `DeviceRemoved`, `DeviceAdded`
```
<WARN> audioOutputAdded: {"kind":"audiooutput","deviceId":"603c4c8db8fb247404255abde283ce78a3ac0c70460b6318ae057d04f205fd82","groupId":"d4b505bc971d76e197c5c6240758acd653084fb68e3ef0b50f2e4fea68ad287c","label":"耳机"}
```

### 采集配置更新
**关键词**: `updateMediaSettings`
```
updateMediaSettings: {"videoCodec":"h264","videoWidth":640,"videoHeight":480,"videoBps":500000,"videoFps":15,"audioCodec":"opus","audioFs":48000,...}
```

---

## 十二、角色与权限

### 切换角色
**关键词**: `switchRole()`
```
[↑t1|101286] switchRole() ["anchor"]
```
- `anchor` - 主播
- `audience` - 观众

### 更新推流配置
**关键词**: `updateLocalAudio()`, `updateLocalVideo()`
```
[↑t1|101286] updateLocalVideo() [{"publish":true}]
[↑t1|101286] updateLocalAudio() [{"publish":true}]
```

---

## 十三、RoomEngine（TUIRoomKit）

### 登录
**关键词**: `TUIRoomEngine.login`
```
<INFO> TUIRoomEngine.login with options: {"sdkAppId":1600065180,"userId":"10","userSig":"..."}
<INFO> TUIRoomEngine.login success.
```

### 创建房间
**关键词**: `roomEngine.createRoom`
```
roomEngine.createRoom with options: {"roomId":"live_c123456","roomName":"room方式创建的直播间","roomType":2,"isSeatEnabled":false,...}
```
**roomType**:
- `1` - 会议场景
- `2` - 直播场景

### 创建房间失败
**关键词**: `roomEngine.createRoom fail`
```
roomEngine.createRoom fail. 100003 error_code:100003, error_message:room existed
```

### 获取麦位
**关键词**: `roomEngine.takeSeat`
```
roomEngine.takeSeat with options: {"seatIndex":-1,"timeout":0}
roomEngine.takeSeat response data: {"requestCallbackType":4,"requestId":"","userId":"","code":-1001,"message":"please enter room first"}
```
**注意**: `code` 非 0 表示失败

### 麦位错误
**关键词**: `TakeSeat|`
```
<ERROR> [↑roomEngine3|10] [seat_manager.cc: 68] |TakeSeat|not enter room, room_id:
```

---

## 十四、插件

### 插件操作
**关键词**: `startPlugin()`, `updatePlugin()`, `stopPlugin()`
```
[↑t1|101286] startPlugin() ["CDNStreaming",{"target":{"publishMode":"publish-main-stream-to-cdn","streamId":"T_S_101286"}}]
```
**常见插件**: CDNStreaming（CDN 推流）

---

## 十五、信令

### 发布信令
**关键词**: `publish() => main`
```
[↑t1-r1|xxx] publish() => main audio
[↑t1-r1|xxx] publish() => main video
```

### 信令回包
**关键词**: `spc-publish-result`
```
[↑t1-r1-ws|xxx] Received event: [ spc-publish-result ]
```

---

## 常见错误码速查

| 错误 | 含义 | 常见原因 |
|-----|------|---------|
| `NotAllowedError` | 权限被拒 | 用户拒绝授权或浏览器策略限制 |
| `OverconstrainedError` | 约束不满足 | 设备不存在或不支持指定参数 |
| `DEVICE_ERROR` | 设备错误 | 设备被占用、无权限 |
| `OPERATION_FAILED` | 操作失败 | 通用错误，需看具体原因 |
| `not support h264` | 不支持 H264 | 需切换 VP8 或升级浏览器 |
| `100003` | 房间已存在 | RoomEngine 创建房间时房间已存在 |
| `-1001` | 未进房 | 操作前需先进房 |

---

## 十六、日志含义速查表（重要）

以下是 TRTC Web SDK 关键日志的详细解读，用于快速定位问题。

### 播放相关

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `play() error: NotAllowedError` | 自动播放受限导致播放失败。远端流需用户交互后播放；本地流此报错通常出现在 Android 微信设备，无需处理 | 🔴 高 |
| `main stream start to play with options: {"muted":true}` | 以静音方式播放远端流。需确认 `stream.play` 接口传参是否正确 | 🟡 中 |
| `main stream - audio player is starting playing` | 远端流音频播放成功 | ✅ 正常 |
| `main stream - video player is starting playing` | 远端流视频播放成功 | ✅ 正常 |
| `stream - video player is starting playing` | 本地视频播放成功 | ✅ 正常 |
| `stream - audio player is starting playing` | 本地音频播放成功 | ✅ 正常 |
| `video player is playing` | 本地视频播放成功 | ✅ 正常 |
| `audio player is playing` | 本地音频播放成功 | ✅ 正常 |
| `main stream - audio player is paused` | 远端流音频播放暂停。可能原因：1) 播放容器 div 被移除 2) Chrome 70 及以下移动 div 导致暂停 | 🟡 中 |
| `main stream - video player is paused` | 远端流视频播放暂停。同上 | 🟡 中 |
| `main setAudioVolume to 0` | 业务侧调用 `remoteStream.setAudioVolume(0)`，将播放音量设为 0，导致无声 | 🟡 中 |

### 流/轨道状态

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `main stream - video track is muted` | 远端视频数据不足以播放，通常网络原因，恢复后会变 unmuted | 🟡 中 |
| `main stream - audio track is muted` | 远端音频数据不足以播放，通常网络原因 | 🟡 中 |
| `auxiliary stream - video track is muted` | 远端屏幕分享数据不足以播放 | 🟡 中 |
| `video track is unable to provide media output` (含↓) | 远端 track 暂时无法解码数据，可能网络波动 | 🟡 中 |
| `video track is unable to provide media output` (含↑) | 本地摄像头采集暂停，设备被占用或权限回收。SDK 会自动恢复 | 🟡 中 |
| `audio track is unable to provide media output` (含↓) | 远端 track 暂时无法解码数据 | 🟡 中 |
| `audio track is unable to provide media output` (含↑) | 本地麦克风采集暂停。SDK 会自动恢复 | 🟡 中 |
| `main stream - video track is unmuted` | 收到足够播放的视频数据 | ✅ 正常 |
| `main stream - audio track is unmuted` | 收到足够播放的音频数据 | ✅ 正常 |
| `video track is ended` | 摄像头采集停止。设备拔出时 SDK 会自动恢复；设备被占用时 v4.11.4+ 会自动恢复 | 🟡 中 |
| `audio track is ended` | 麦克风采集停止。同上 | 🟡 中 |
| `main audio track is ended` | 远端音频轨道停止 | 🟡 中 |
| `main video track is ended` | 远端视频轨道停止 | 🟡 中 |
| `auxiliary video track is ended` | 远端屏幕分享轨道停止 | 🟡 中 |

### 采集与推流

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `gotStream` | 本地流采集成功 | ✅ 正常 |
| `local stream is published successfully` | 推流成功 | ✅ 正常 |
| `getUserMedia with constraints` | 开始媒体采集（摄像头/麦克风） | ℹ️ 信息 |
| `getDisplayMedia with constraints` | 开始屏幕分享采集 | ℹ️ 信息 |
| `switch camera success` | 切换摄像头成功 | ✅ 正常 |
| `switch microphone success` | 切换麦克风成功 | ✅ 正常 |
| `updateStream() try to recover local stream` | 设备采集异常，正在尝试自动恢复 | 🟡 中 |
| `updateStream() recover local stream successfully` | 设备采集异常，自动恢复成功 | ✅ 正常 |
| `updateStream() failed to recover local stream` | 设备采集异常，自动恢复失败 | 🔴 高 |
| `updateStream() video flag is true, but no camera detected, set video to false` | 尝试恢复摄像头采集时检测到无摄像头，不恢复 | 🟡 中 |

### 编码器

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `encoderImplementation change to OpenH264` | 使用软编 | ℹ️ 信息 |
| `encoderImplementation change to ExternalEncoder` | 使用硬编 | ℹ️ 信息 |
| `qualityLimitationReason change to bandwidth` | 带宽不足导致编码质量受限，可能降低码率/帧率/分辨率 | 🟡 中 |
| `qualityLimitationReason change to cpu` | CPU 负荷高导致编码质量受限 | 🟡 中 |

### 网络质量

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `downlink network quality change` | 下行网络质量变更 (1:极佳 2:较好 3:一般 4:较差 5:极差) | ℹ️ 信息 |
| `uplink network quality change` | 上行网络质量变更 (1:极佳 2:较好 3:一般 4:较差 5:极差) | ℹ️ 信息 |
| `black detected` | 检测到黑屏 (fps=0)，通常网络问题，网络恢复后会正常 | 🟡 中 |
| `schedule failed` | 信令调度请求失败，不影响进房，SDK 会连接默认信令域名 | ℹ️ 信息 |

### 流操作

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `localStream mute video` | mute 上行视频流 | 🟡 中 |
| `localStream unmute video` | unmute 上行视频流 | 🟡 中 |
| `localStream mute audio` | mute 上行音频流 | 🟡 中 |
| `localStream unmute audio` | unmute 上行音频流 | 🟡 中 |
| `is adding audio track to current published local stream` | 添加音频轨道 | 🟡 中 |
| `is removing audio track from current published local stream` | 移除音频轨道 | 🟡 中 |
| `is adding video track to current published local stream` | 添加视频轨道 | 🟡 中 |
| `is removing video track from current published local stream` | 移除视频轨道 | 🟡 中 |
| `is replacing audio track to current published local main stream` | 替换音频轨道 | 🟡 中 |
| `is replacing video track to current published local main stream` | 替换视频轨道 | 🟡 中 |

### 房间与用户

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `client-banned` | 被踢出房间 | 🔴 高 |
| `user_timeout` | 后台长时间没收到 SDK 心跳导致被踢，通常是用户 JS 线程长时间阻塞 | 🔴 高 |
| `visibility change: hidden` | 页面切后台，移动端会导致设备采集暂停 | 🟡 中 |
| `visibility change: visible` | 页面切回前台 | ℹ️ 信息 |

### 屏幕分享

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `"displaySurface":"window"` | 屏幕分享采集了应用窗口 | ℹ️ 信息 |
| `"displaySurface":"monitor"` | 屏幕分享采集了整个屏幕 | ℹ️ 信息 |
| `"displaySurface":"browser"` | 屏幕分享采集了某个标签页 | ℹ️ 信息 |
| `screen sharing was stopped because the video track is ended` | 屏幕分享停止，用户点击停止按钮或分享窗口被关闭 | 🟡 中 |

### API 调用日志

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `Join() => joining room` | 调用 `client.join` 接口 | ℹ️ 信息 |
| `publish() => publishing local stream` | 调用 `client.publish` 接口 | ℹ️ 信息 |
| `subscribe() => subscribe to` | 调用 `client.subscribe` 接口 | ℹ️ 信息 |
| `switchRole() => switch role` | 调用 `client.switchRole` 接口 | ℹ️ 信息 |
| `main stream start to play with` | 调用 `remoteStream.play` 接口 | ℹ️ 信息 |
| `stream start to play with` | 调用 `localStream.play` 接口 | ℹ️ 信息 |
| `updateMediaSettings` | 实际采集的分辨率及帧率信息 | ℹ️ 信息 |

### TRTC 5.x API 成功日志

以下 API 成功调用会输出 `xxx() success` 格式日志：
- `enterRoom`, `exitRoom`, `switchRole`, `destroy`
- `startLocalAudio`, `updateLocalAudio`, `stopLocalAudio`
- `startLocalVideo`, `updateLocalVideo`, `stopLocalVideo`
- `startScreenShare`, `updateScreenShare`, `stopScreenShare`
- `startRemoteVideo`, `updateRemoteVideo`, `stopRemoteVideo`
- `muteRemoteAudio`, `startPlugin`, `updatePlugin`, `stopPlugin`, `setRemoteAudioVolume`

### 特殊场景

| 日志特征 | 含义 | 严重程度 |
|---------|------|---------|
| `gen canvas track` | 如果没有调用 `localStream.play`，可能导致 iOS 15.1 编码黑屏；若调用了则是规避 iOS 15.1 crash 的二次渲染 | 🟡 中 |

---

## 十七、排障日志搜索优先级

根据问题类型，推荐按以下优先级搜索：

### 无声问题
1. `startLocalAudio` - 是否开启了音频采集
2. `mute audio` / `muteLocalAudio` - 是否有 mute 操作
3. `audio track is ended` / `audio track is unable` - 采集是否中断
4. `setAudioVolume to 0` - 是否设置了音量为 0
5. `audio player is starting playing` - 播放是否成功
6. `NotAllowedError` - 权限是否被拒

### 无画面问题
1. `startLocalVideo` / `startRemoteVideo` - 是否开启了视频
2. `video track is ended` / `video track is unable` - 采集是否中断
3. `video player is starting playing` - 播放是否成功
4. `black detected` - 是否检测到黑屏
5. `qualityLimitationReason` - 编码是否受限

### 卡顿问题
1. `qualityLimitationReason` - 编码是否受限 (bandwidth/cpu)
2. `uplink/downlink network quality change` - 网络质量
3. `muted` / `unmuted` 状态变化 - 数据是否不足
4. `cpu: critical` - CPU 是否过载

### 被踢房间
1. `client-banned` - 确认被踢
2. `user_timeout` - 心跳超时被踢（JS 线程阻塞）

### 自动播放失败
1. `play() error: NotAllowedError` - 确认自动播放失败
2. `handleAutoPlayFailed` - SDK 检测到自动播放失败
