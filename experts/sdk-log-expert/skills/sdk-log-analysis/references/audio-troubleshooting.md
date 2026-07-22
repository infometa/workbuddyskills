# 音频日志排障指南

## ⚠️ 排障前必读

**在排查音频问题时，Agent 必须先阅读本指南，按照对应的排障思路进行分析。**

## 第一步：判断问题类型

首先确定是**上行无声**还是**下行无声**：

| 类型 | 表现 | 影响 |
|-----|------|-----|
| 上行无声 | 本地用户说话，远端听不到 | 本地采集/发送问题 |
| 下行无声 | 远端用户说话，本地听不到 | 远端接收/播放问题 |

---

## 上行无声排障流程

按以下顺序逐一排查：

### 1. 检查音频采集是否开启

**搜索关键词**: `["startLocalAudio", "enableLocalAudio", "muteLocalAudio"]`

- 查找 `startLocalAudio` 或 `enableLocalAudio` 调用记录
- 确认返回值是否成功（code = 0）

### 2. 检查是否有禁音操作

**搜索关键词**: `["muteLocalAudio", "mute", "setAudioMute"]`

- 查找 `muteLocalAudio(true)` 调用
- 检查是否有意外的 mute 操作

### 3. 检查音量设置

**搜索关键词**: `["setAudioCaptureVolume", "setCaptureVolume", "volume"]`

- 确认采集音量是否设置过低（< 10）
- 检查是否有 `setAudioCaptureVolume(0)` 调用

### 4. 检查采集设备状态

**搜索关键词**: `["microphone", "device", "capture", "error"]`

- 查找设备枚举和选择记录
- 检查是否有设备错误日志

### 5. 检查麦克风抢占

**搜索关键词**: `["device", "occupied", "busy", "exclusive"]`

- 查找设备被占用的错误
- 检查是否有其他应用抢占麦克风

### 6. 检查音频打断

**搜索关键词**: `["interrupt", "interruption", "AVAudioSession"]`

- 查找 `interrupt` 相关日志
- 检查是否被其他应用（如来电）打断

### 7. 检查自定义采集

**搜索关键词**: `["enableCustomAudioCapture", "customAudio", "sendCustomAudioData"]`

- 确认是否启用了自定义采集模式
- 如果启用，检查是否正常发送自定义音频数据

---

## 下行无声排障流程

### 阶段一：检查是否收到远端音频数据

#### 1. 检查首帧音频回调

**搜索关键词**: `["onFirstAudioFrame", "firstAudioFrame", "onUserAudioAvailable"]`

| 情况 | 含义 | 下一步 |
|-----|------|-------|
| ✅ 有首帧回调 | 正常收到远端数据 | 进入**阶段二** |
| ❌ 无首帧回调 | 未收到远端数据 | 进入**阶段三** |

#### 2. 检查远端音频可用回调

**搜索关键词**: `["onUserAudioAvailable", "AudioAvailable", "remoteAudio"]`

- 查找 `onUserAudioAvailable(userId, true)` 回调
- 确认远端用户是否发布了音频流

#### 3. 检查远端用户进房

**搜索关键词**: `["onRemoteUserEnterRoom", "onUserEnter", "remoteUser"]`

- 确认远端用户是否成功进入房间
- 检查 userId 是否匹配

---

### 阶段二：有首帧回调但无声（播放问题）

#### 1. 检查播放音量

**搜索关键词**: `["setAudioPlayoutVolume", "setPlayoutVolume", "playVolume"]`

- 确认播放音量是否设置过低
- 检查是否有 `setAudioPlayoutVolume(0)` 调用

#### 2. 检查是否 mute 远端用户

**搜索关键词**: `["muteRemoteAudio", "muteAllRemoteAudio", "mute"]`

- 查找 `muteRemoteAudio(userId, true)` 调用
- 检查是否调用了 `muteAllRemoteAudio(true)`

#### 3. 检查播放设备状态

**搜索关键词**: `["speaker", "playout", "playback", "device"]`

- 查找播放设备选择记录
- 检查是否有播放设备错误

#### 4. 检查音频打断

**搜索关键词**: `["interrupt", "interruption", "AVAudioSession"]`

- 查找播放被打断的日志
- 检查是否被其他应用打断

#### 5. 检查播放警告/错误

**搜索关键词**: `["warning", "error", "playout", "audio"]`

- 查找音频播放相关的警告或错误日志
- 注意 warning code 和 error code

#### 6. 检查音频路由切换

**搜索关键词**: `["audioRoute", "setAudioRoute", "speaker", "earpiece", "headphone"]`

- 查找音频路由切换记录
- 常见场景：
  - 用户插拔耳机
  - 从扬声器切换到听筒
  - 蓝牙设备连接/断开
- **注意**：用户可能不知道路由已切换（如耳机声音小）

#### 7. 检查自定义播放

**搜索关键词**: `["enableCustomAudioRendering", "customAudioRendering", "getCustomAudioRenderingFrame"]`

- 确认是否启用了自定义渲染/播放模式
- 如果启用，SDK 不会自动播放音频，需要应用自行处理
- 检查是否正常调用 `getCustomAudioRenderingFrame` 获取音频数据

---

### 阶段三：无首帧回调（未收到数据）

#### 1. 检查是否 mute 远端用户

**搜索关键词**: `["muteRemoteAudio", "muteAllRemoteAudio"]`

- 查找是否在收到数据前就 mute 了远端用户
- mute 会导致不拉取远端音频流

#### 2. 检查自动拉流模式

**搜索关键词**: `["setDefaultStreamRecvMode", "autoRecvAudio", "streamRecvMode"]`

- 确认是否开启了自动拉取音频模式
- 默认应该是自动拉取，如果设置为手动需要主动订阅

#### 3. 检查订阅状态

**搜索关键词**: `["subscribeRemoteAudio", "subscribe", "startRemoteView"]`

- 如果是手动订阅模式，检查是否调用了订阅接口
- 确认订阅的 userId 是否正确

---

## 排障搜索关键词汇总

| 场景 | 推荐关键词 |
|-----|-----------|
| 上行采集 | `["startLocalAudio", "enableLocalAudio", "muteLocalAudio"]` |
| 音量设置 | `["setAudioCaptureVolume", "setAudioPlayoutVolume", "volume"]` |
| 设备问题 | `["microphone", "speaker", "device", "error"]` |
| 音频打断 | `["interrupt", "interruption", "AVAudioSession"]` |
| 下行首帧 | `["onFirstAudioFrame", "onUserAudioAvailable"]` |
| 远端 mute | `["muteRemoteAudio", "muteAllRemoteAudio"]` |
| 音频路由 | `["audioRoute", "setAudioRoute", "speaker", "headphone"]` |
| 自动拉流 | `["setDefaultStreamRecvMode", "autoRecvAudio"]` |
| 自定义采集 | `["enableCustomAudioCapture", "sendCustomAudioData"]` |
| 自定义播放 | `["enableCustomAudioRendering", "getCustomAudioRenderingFrame"]` |

---

## 常见问题速查

| 现象 | 最可能原因 | 快速检查 |
|-----|-----------|---------|
| 上行完全无声 | 未开启采集 / mute | 搜索 `startLocalAudio` |
| 上行断断续续 | 设备抢占 / 打断 | 搜索 `interrupt` |
| 下行完全无声 | mute 远端 / 未订阅 | 搜索 `muteRemoteAudio` |
| 下行声音小 | 音频路由切换 | 搜索 `audioRoute` |
| 偶发无声 | 音频打断 | 搜索 `interrupt` |
