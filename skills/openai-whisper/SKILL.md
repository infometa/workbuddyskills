---
name: openai-whisper
description: "Local speech-to-text with the Whisper CLI (no API key)."
description_zh: "本地语音转文字（无需 API 密钥）"
description_en: "Local speech-to-text (no API key needed)"
version: 1.0.0
---

# Whisper (CLI)

Use `whisper` to transcribe audio locally.

Quick start
- `whisper /path/audio.mp3 --model medium --output_format txt --output_dir .`
- `whisper /path/audio.m4a --task translate --output_format srt`

Notes
- Models download to `~/.cache/whisper` on first run.
- `--model` defaults to `turbo` on this install.
- Use smaller models for speed, larger for accuracy.
