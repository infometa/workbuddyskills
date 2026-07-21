# TeachAny Video & Audio（精简版）

## TTS 基线要求

所有课件必须包含：
- `[data-tts]` 段落；
- `teachany-tts-narrator.js` 标准模块；
- 如有音频列表，使用标准 audio player。

## TTS 生成流程

1. 写旁白 JSON：`scripts/narration_zh.json` 或课件目录内 `narration.json`。
2. 生成音频：
   ```bash
   python3 scripts/tts-engine.py --text "讲解文本" --voice zh-CN-XiaoxiaoNeural --output tts/s01.mp3
   ```
3. 检查文件大小和可播放性。
4. HTML 中用标准 audio/TTS 模块引用。

## 视频/动画

适用：过程性概念、实验变化、历史演变、函数变换。

要求：
- 画面信息与旁白同步；
- 有至少 3 个动态 beat；
- 不是单张图铺满全程；
- 嵌入对应 section，而不是集中放在页尾。

## 验证

```bash
ffprobe -hide_banner assets/video/*.mp4
ls -lh tts/*.mp3
node "$TEACHANY_SKILL/scripts/validate-courseware.cjs" "$COURSE_DIR"
```

## 降级说明

- Remotion 视频和批量 mp3 按课型需要补齐，非所有课件强制。
- 增强项失败必须修复、换方案或取得用户明确豁免；不允许以"后续升级"为由跳过。
