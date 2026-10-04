# 中文语音音色参考

本 skill 有两套引擎，**优先用 v2（edge-tts 真人级音色）**。

| 引擎 | 音色质量 | 输出格式 | 联网 | 脚本 |
|------|---------|---------|------|------|
| **v2（推荐）** | 神经网络真人级，自然生动 | **mp3** | 需要 | `generate_podcast_v2.py` |
| v1（离线兜底） | 系统合成音，机械感强 | m4a | 不需要 | `generate_podcast.py` |

---

## v2 引擎：edge-tts 神经网络音色（推荐）

### 安装
```bash
# 必须用国内镜像，直连 pypi.org 会超时
pip install edge-tts -i https://mirrors.cloud.tencent.com/pypi/simple/
```

### 可用中文音色（zh-CN）

| Voice | 性别 | 风格标签 | 适合角色 |
|-------|------|---------|---------|
| `zh-CN-YunxiNeural` | 男 | Lively, Sunshine | **主持人首选**——活泼、有亲和力 |
| `zh-CN-YunyangNeural` | 男 | Professional, Reliable | **专家/教授首选**——沉稳可信 |
| `zh-CN-XiaoxiaoNeural` | 女 | Warm（News/Novel） | 主持人 / 旁白 / 单人讲解 |
| `zh-CN-XiaoyiNeural` | 女 | Lively（Cartoon/Novel） | 活泼女声、第二嘉宾 |
| `zh-CN-YunjianNeural` | 男 | Passion（Sports） | 激情解说、强调段落 |
| `zh-CN-YunxiaNeural` | 男 | Cute | 年轻男声 |
| `zh-CN-liaoning-XiaobeiNeural` | 女 | 东北方言, Humorous | 特色内容 |
| `zh-CN-shaanxi-XiaoniNeural` | 女 | 陕西方言, Bright | 特色内容 |

查看完整列表：
```bash
python -m edge_tts --list-voices | grep zh-CN
```

### 内置预设（脚本自动应用）

| speaker | 音色 | rate | pitch | 说明 |
|---------|------|------|-------|------|
| `host` | YunxiNeural | +6% | +2Hz | 主持人稍快、略上扬，显精神 |
| `guest` | YunyangNeural | -4% | +0Hz | 专家稍慢、沉稳，显权威 |
| solo 模式 | XiaoxiaoNeural | +2% | +0Hz | 温暖自然 |

**差异化语速是关键**：主持人快、嘉宾慢，听感上立刻能区分两个人，比单纯换音色更有效。

### 表现力调节
在 segment 里可覆盖：
```json
{"speaker": "guest", "rate": "-10%", "pitch": "-2Hz", "volume": "+10%", "text": "..."}
```
- `rate`：`-50%` ~ `+100%`，强调段落可放慢
- `pitch`：`-10Hz` ~ `+10Hz`，上扬显活泼、下沉显沉稳
- `volume`：`-50%` ~ `+50%`

### 角色组合建议
- **双人对话（最佳）**：`host`=YunxiNeural（男，活泼）+ `guest`=YunyangNeural（男，沉稳）
  - 想要男女搭配：`host`=XiaoxiaoNeural（女）+ `guest`=YunyangNeural（男）
- **单人讲解**：XiaoxiaoNeural（温暖）或 YunyangNeural（专业）
- **三人圆桌**：YunxiNeural + YunyangNeural + XiaoxiaoNeural

---

## v1 引擎：macOS `say`（离线兜底）

仅在**无网络**时使用。音色为系统合成，机械感明显，不适合正式播客。

| Voice | 说明 |
|-------|------|
| `Tingting` | 女声，zh_CN 里唯一较正常的播音音色 |
| `Eddy` / `Flo` / `Grandma` / `Grandpa` / `Reed` / `Rocko` / `Sandy` / `Shelley` | **卡通化趣味音色**，听感差，慎用 |

> 实测结论：macOS 中文音色全部为 compact（低质量）级别；系统内虽有 Siri premium 神经音色资源（`zh_CN.linfei.neural.premium`），但 `say` 和 `AVSpeechSynthesizer` API 均无法调用。这是 v1 音质差的根本原因，也是必须优先用 v2 的理由。

v2 脚本已内置 v1 音色名自动映射（`Eddy`→`YunxiNeural`、`Ting-Ting`→`XiaoxiaoNeural` 等），旧脚本 JSON 可直接复用。
