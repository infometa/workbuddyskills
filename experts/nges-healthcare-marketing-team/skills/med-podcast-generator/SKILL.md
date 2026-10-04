---
name: med-podcast-generator
description: 将医学文本草稿（论文摘要、临床指南、教学讲义、药品推广材料、专家访谈等）二创为播客音频，输出 .mp3 + 配套脚本文本。支持单人讲解与双人对话两种形式，edge-tts 神经网络真人级音色，内置 90+ 医学英文术语发音自动修正，无网络时回退 macOS 原生引擎。当用户提到"把医学内容做成播客""生成播客音频""双人对话播客""医学播客""medical podcast"等需求时使用本 skill。
agent_created: true
---

# med-podcast-generator — 医学内容播客二创与音频生成

## 适用场景

将医学文本草稿（论文摘要、临床指南、教学讲义、药品推广材料、专家访谈等）二创为**播客音频**，输出 `.mp3` 文件，适用于内部学习、医生碎片化收听、患教推送等场景。

支持两种形式：
- **单人讲解**：主播独白式解读，像「医学知识电台」
- **双人对话**：主持人 + 嘉宾访谈式，两人不同音色，更生动

## 技术基线（重要）

### 主引擎：edge-tts（v2，推荐）
- 语音合成：微软**神经网络真人级音色**，自然生动
- 输出格式：**mp3**（标准 MPEG Layer III）
- 需联网；安装必须用国内镜像：
  ```bash
  pip install edge-tts -i https://mirrors.cloud.tencent.com/pypi/simple/
  ```
- 脚本：`scripts/generate_podcast_v2.py`

### 兜底引擎：macOS say（v1）
- 仅在**无网络**时使用，音色机械、听感差，不适合正式播客
- 输出 `.m4a`（macOS 无 mp3 编码器）
- 脚本：`scripts/generate_podcast.py`

> **音质差是 v1 的固有缺陷**：macOS 中文音色全为 compact 低质量级别，系统内的 Siri premium 神经音色无法通过 API 调用。**默认一律用 v2。**

## 工作流程

### Step 1: 内容解析
从用户提供的医学文本中提取（复用 med-interactive-html 的解析逻辑）：
- 标题、关键标签、核心知识点（2-4 个维度）
- 专家信息（如有）
- 关键数据、对比信息、时间线
- 参考文献

### Step 2: 播客脚本二创（核心，决定成品质量）

将书面医学内容改写为**口语化、有对话感的播客脚本**。这一步做得好不好，比技术参数影响大得多。

#### 让播客「生动」的要点
- **开场用钩子**：别直接念标题。用提问、反常识、场景切入。
  - ✅「如果有一种肺癌，吃药就能控制好几年，你信吗？」
  - ❌「本期我们介绍 EGFR-TKI 联合治疗策略的进展。」
- **加口语连接词**：「对」「没错」「这个问题问得好」「坦率地说」「你想」
- **主持人要真提问、会追问**：不是报幕员，要替听众问出疑惑
  - 「变在哪儿呢？能不能打个比方？」「所以检测不是可选项，是必答题？」
- **用生活化类比讲机制**：
  - ✅「把肿瘤细胞想象成一间房子，里面有个开关一直开着，细胞就疯长——EGFR 就是这个开关，TKI 就是去关掉它」
- **长句拆短**：书面长句在音频里很难跟，一句话讲一件事
- **段落长短交错**：主持人短问（15-40 字）+ 嘉宾长答（90-130 字），有节奏感
- **结尾收三句干货**：便于听众记住

#### 必须守住的规范
- 所有医学数据原值保留（剂量、百分比、p 值、置信区间），不臆造、不改动
- 不添加原文没有的医学信息
- 术语首次出现给全称解释
- 结尾口播免责声明：「本节目内容仅供医学专业人士学习参考，不作为临床诊疗依据」
- 口播参考文献名称

#### 英文术语发音
脚本**无需手工处理**——合成脚本会自动把 `EGFR-TKI` 转成 `E G F R T K I` 确保逐字母清晰朗读。
详见 `references/pronunciation.md`。

> 但最自然的做法是**脚本层面就用中文**：说「客观缓解率」比念「O R R」好听得多。

### Step 3: 写脚本 JSON

**双人对话**（speaker 用 `host` / `guest`，脚本自动套用音色预设）：
```json
{
  "title": "EGFR-TKI 联合治疗策略解读",
  "mode": "dialogue",
  "segments": [
    {"speaker": "host",  "speaker_name": "主持人",   "text": "各位好，欢迎回到……"},
    {"speaker": "guest", "speaker_name": "邬麟教授", "text": "谢谢主持人，各位听众好……"}
  ]
}
```

**单人讲解**：
```json
{
  "title": "乐唯初核心信息速览",
  "mode": "solo",
  "segments": [
    {"speaker": "host", "text": "第一段内容……"},
    {"speaker": "host", "text": "第二段内容……"}
  ]
}
```

预设音色（自动应用，也可在 segment 里用 `voice`/`rate`/`pitch` 覆盖）：

| speaker | 音色 | rate | 说明 |
|---------|------|------|------|
| `host` | zh-CN-YunxiNeural | +6% | 男声活泼，主持人 |
| `guest` | zh-CN-YunyangNeural | -4% | 男声沉稳，专家 |
| solo | zh-CN-XiaoxiaoNeural | +2% | 女声温暖 |

> **差异化语速很关键**：主持人快、嘉宾慢，听感上立刻能区分两人。
> 完整音色列表见 `references/voices.md`。

### Step 4: 预检查发音（建议）
```bash
python3 <skill_dir>/scripts/generate_podcast_v2.py \
  --input script.json --output out.mp3 --dry-run
```
确认英文缩写转换正确、研究名（MELODY 等）保持原样。

### Step 5: 合成音频
```bash
python3 <skill_dir>/scripts/generate_podcast_v2.py \
  --input script.json \
  --output /path/to/output/podcast.mp3
```

脚本会：
1. 逐段调用 edge-tts 合成（自动应用发音修正 + 音色预设）
2. mp3 帧级字节流直接拼接（**不解码重编码**，零质量损失、保住真 mp3 格式）
3. 同时保存 `<output_name>_script.md`（脚本文本，便于对照与字幕）

> 技术细节：afconvert 只能解码 mp3、不能编码（Apple 未授权 LAME）。若走 WAV 中转会被迫降级 m4a，故采用字节流直接拼接。

### Step 6: 输出与预览
- 主产物：`.mp3` 音频
- 配套：`_script.md` 脚本文本
- 用 present_files 把 mp3 展示给用户试听

### Step 7: 质检（建议）
```bash
# 格式与时长
file out.mp3 && afinfo out.mp3 | grep -i duration
# 期望：MPEG ADTS, layer III
```

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| pip 安装 edge-tts 超时 | 直连 pypi.org 慢 | 加 `-i https://mirrors.cloud.tencent.com/pypi/simple/` |
| 音色机械难听 | 用了 v1（macOS say） | 改用 `generate_podcast_v2.py` |
| 英文缩写读错 | — | v2 自动处理；先 `--dry-run` 确认 |
| SSML 标签被念出来 | edge-tts 不支持 SSML | 别用标签，改用 `rate`/`pitch` 参数 |
| 输出 .mp3 但播放器不识别 | 曾用 mp4 容器封装 | v2 已修正为真 mp3 字节流拼接 |
| 无网络 | edge-tts 需联网 | 回退 v1 `generate_podcast.py`（输出 m4a） |

## 医学内容安全规范
- 不添加原文未提供的医学信息
- 药物名称、剂量、百分比等关键数据原样保留
- 音频口播末尾加免责声明
- 保留参考文献（口播念出文献名称）

## 与其他 skill 协作
- 与 `med-interactive-html` 互补：同一份内容既可出**互动页面**（看），也可出**播客音频**（听），形成「看 + 听」双形态学习物料。
- 专家（MedReCreator）会根据用户输入自动匹配本 skill。
