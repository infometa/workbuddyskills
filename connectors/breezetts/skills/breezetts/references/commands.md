# Breeze CLI 0.23.1 操作参考

以下资源 ID 都是占位符，应使用前序查询的实际返回值；路径按当前项目解析。优先 `--agent`，需要额外参数时先查子命令帮助。

## 声音与合成

普通 TTS 默认显式 `--stream --play --agent`，边接收边播放并保存；用户要求静音才用 `--no-play`。异步命令是后台生成备选，不用于实时试听。

```sh
breeze voice list --voice-type default --language zh --gender female --page-size 100 --agent
breeze voice get VOICE_ID --agent
breeze models list --agent
breeze tts --input TEXT_PATH --voice VOICE_ID --format mp3 --file AUDIO_PATH --stream --play --agent
breeze tts --input TEXT_PATH --voice VOICE_ID --instructions "请以冷静、温和且沉稳的语气进行讲解。保持语速稍慢，字句清晰。" --agent
breeze tts --input TEXT_PATH --voice VOICE_ID --with-timestamps --format mp3 --file AUDIO_PATH --no-play --agent
breeze tts enhance --instruction "冷静温和的讲解，语速稍慢" --language zh --json
breeze tts --async --input TEXT_PATH --voice VOICE_ID --agent
breeze jobs get JOB_ID --agent
breeze jobs wait JOB_ID --timeout 2m --file AUDIO_PATH --agent
breeze jobs download JOB_ID --file AUDIO_PATH --agent
breeze curl tts --text "TEXT" --voice VOICE_ID --instructions "…" --output json
```

`--speed` 范围 0.5–2.0；`--volume` 为 0.01–2.0。语言用模型支持的 ISO 语言码。

`--with-timestamps` 返回 `word_timestamps`（`index` / `word` / `start` / `end`，浮点秒），并额外写 `<file>.timestamps.json`。中文的 `word` 是短句级片段，标点单独成条且带时长（即停顿）——用法见 [字幕与时间戳](subtitles.md)。

`--instructions` 只影响表演，不进入正文；`--guidance-scale` 默认 1，连续旁白先试 1–2；`--use-speaker-boost` 与指令互斥。写法见 [念法指令](instruction.md)。

`tts enhance` 只扩写指令文本，不合成音频、不计配音费；`--language` 要与朗读语言一致。

`breeze curl tts` **只拼装一条等价 curl 命令并打印，不发送请求**，用于核对 HTTP 字段名，也是无 CLI 时走 REST 的参照：

```sh
curl -X POST "https://api.breeze.blue/v1/text-to-speech/VOICE_ID/stream?output_format=mp3" \
  -H "xi-api-key: $BREEZE_API_KEY" -H 'content-type: application/json' \
  --data '{"text":"…","language_code":"zh","instructions":"…","voice_settings":{"guidance_scale":2}}'
```

字幕走 `/with-timestamps` 而不是 `/stream`，返回 `{"audio_base64","content_type","word_timestamps"}`。

异步下载时间戳时查 `jobs download --help`。保留 JSON 中的任务 ID、历史 ID、文件路径。

实时语音先查 `tts realtime --help`，按其要求提供文本或 JSONL 输入；不要把 streaming 参数与 realtime 参数混用。实时任务中断后不能自动重放整段收费请求。

## 声音管理

```sh
breeze voice design --description "温柔自然的中文女声，使用标准普通话" --text "欢迎来到 Breeze。" --preview-count 1 --no-play --agent
breeze voice clone --file SAMPLE_PATH --name "我的声音" --agent
breeze voice preview download PREVIEW_ID --file AUDIO_PATH --agent
breeze play AUDIO_PATH
breeze voice preview save PREVIEW_ID --name "我的声音" --language zh --agent
breeze voice metadata-options --agent
breeze voice edit --help
breeze voice remix --help
breeze voice localize --help
breeze voice delete VOICE_ID --yes --agent
```

设计描述表达音色、年龄感、节奏及用户要求的口音；用户未指定时中文采用标准普通话。设计返回预览，不等于保存到声音库。默认生成一个预览，下载后自动播放一次；这属于完成后试听，不是流式播放。用户要求静音时跳过播放。修改元数据之前查询 metadata-options，不猜代码。删除必须有明确用户指令。

## 历史、播放及账户

```sh
breeze history list --agent
breeze history get HISTORY_ID --agent
breeze history download HISTORY_ID --file AUDIO_PATH --agent
breeze play AUDIO_PATH
breeze balance --agent
breeze whoami --days 7 --agent
breeze usage list --days 7 --agent
```

历史 ID 可能以 `job_` 开头，直接使用返回值，不自行改成其他前缀。下载后检查真实文件；请求成功不代表听感已经验收。
