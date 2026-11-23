---
name: breezetts
description: 使用 Breeze 完成文字转语音、按场景选音色、念法指令、字幕时间戳、声音试听/设计/克隆/管理、任务与历史查询、音频下载播放、余额与用量查询。优先调用 Breeze CLI，没有 CLI 时用 HTTP 直连兜底。不包含视频制作、播客编排或 Studio 项目工作流。
display_name: BreezeTTS
display_name_en: BreezeTTS
description_zh: 用自然语言生成语音、搜索和管理声音、下载音频并查询余额。
description_en: Generate speech, find and manage voices, download audio, and check balance.
version: 1.0.2
author: BreezeBlue
examples_zh:
- 用温柔的中文女声读：欢迎来到 Breeze。
- 把这段文字生成 MP3 并保存到当前项目。
- 给这段旁白配一版字幕。
examples_en:
- Read "Welcome to Breeze" with a gentle female voice.
- Turn this text into an MP3 and save it in my project.
- Generate subtitles for this narration.
metadata:
  ai.workbuddy.icon: assets/icon.svg
---

# BreezeTTS

优先使用已安装的 Breeze CLI：功能最全，安装、登录与连接状态由连接器生命周期负责。**CLI 不可用时不要直接失败**——见「没有 CLI 时」一节，用 HTTP 直连完成同样的合成。

## 环境与登录

定位 CLI：优先 `BREEZE_CLI_BIN`，其次 PATH 中的 `breeze`，最后检查 `$HOME/.local/bin/breeze`（连接器已把该目录放进 PATH）。路径含空格时正确引用。以下示例中的 `breeze` 替换为解析后的可执行文件。

首次调用先运行 `breeze version --output json` 和 `breeze whoami --agent`（最低版本 0.23.1）。

### 未登录时：直接给链接，不要让用户自己找入口

`whoami --agent` 返回 `error.code = "auth"` 或退出码 3 时，按下面做：

1. **后台**启动登录（它会阻塞轮询，不要放在前台等它结束）：

   ```sh
   breeze login --no-browser --agent > login.log 2> login.json &
   ```

2. 等 1–3 秒，从 **`login.json`（stderr）** 读这一行 JSON：

   ```json
   {"auth_url":"https://breezeblue.ai/cli/login?flow_id=...","expires_at":"...","poll_interval_seconds":2,"status":"pending"}
   ```

   取 `auth_url`。注意它写在 **stderr 而不是 stdout**——`--agent` 让 stdout 保持干净。取不到时，退回不带 `--agent` 的 `breeze login --no-browser`，从 stdout 里 `Open this URL to authenticate:` 之后那一行取链接。

3. 把 `auth_url` **原样**发给用户，单独一行、可直接点击，并说明：点开完成登录后会自行回到会话，不需要复制任何东西。不要截断、不要改写 query 参数、不要包进代码块。

4. 用户点开后，登录进程轮询到结果会自行退出。随后重新跑 `breeze whoami --agent`，`present` 为 `true` 即完成，**接着做用户原来的请求**，不要让用户重说一遍。

5. 链接有效期见 `expires_at`（约 10 分钟）。过期就重新生成一条，新链接覆盖旧的。

6. 用户暂时不想登录：保留原请求与已准备的内容，说明随时可以继续，不要反复催促。

不要在对话里索要 API Key，不要读取或打印凭据文件，不要替用户执行安装命令（安装归连接器）。

### 已登录

凭据存在时忽略登录流程。业务查询与生成一律加 `--agent`（JSON、非交互）。根据返回 JSON 的 `error` 判断成败，不依赖退出码。

凭据存在但网络失败时排查网络，不要要求重新授权。

## 没有 CLI 时：HTTP 直连

`breeze` 不存在、安装失败、或用户明确不装 CLI 时，只要有 API Key 就能完成合成与字幕。按顺序取凭据：`BREEZE_API_KEY` 环境变量 → 用户当场提供 → 都没有时请用户到 Breeze 控制台的 Developer API 页面创建，**不要索取账号密码**。

合成：

```sh
curl -X POST "https://api.breeze.blue/v1/text-to-speech/$VOICE_ID/stream?output_format=mp3" \
  -H "xi-api-key: $BREEZE_API_KEY" \
  -H 'content-type: application/json' \
  --data '{"text":"要朗读的正文","language_code":"zh"}' \
  --output out.mp3
```

带词级时间戳（字幕用）：

```sh
curl -X POST "https://api.breeze.blue/v1/text-to-speech/$VOICE_ID/with-timestamps?output_format=mp3" \
  -H "xi-api-key: $BREEZE_API_KEY" -H 'content-type: application/json' \
  --data '{"text":"……","language_code":"zh"}'
```

返回 `{"audio_base64":"…","content_type":"audio/mpeg","word_timestamps":[…]}`：把 `audio_base64` 解码写成音频文件，`word_timestamps` 的用法与 CLI 完全一致。

可选字段：`instructions`（念法指令）、`voice_settings`（如 `{"guidance_scale":2}`）。要确认某组参数的准确写法，用 `breeze curl tts <同样的参数>` 生成一份对照命令（该命令只做拼装、不发送请求）。

HTTP 路径的限制，如实告诉用户：没有 `voice list` 的本地缓存、没有断点续传、没有异步任务管理。批量长文本仍建议装 CLI。

## 选音色：先查表，不随机

**不要用 `--random-voice`。** 默认音色池与场景映射见 [默认音色池](references/voices.md)：20 个官方公共音色（男 10 女 10），按场景查表即可。

顺序：用户指定 → 场景表 → 没线索时用「知识讲解」那一对 → 都不合适才 `voice list --voice-type default --language zh` 现找。

用户描述模糊（"好听的女声"）时，从表里挑 2 个候选说明差异让用户选一次，不要一口气列 20 个 id。

## "用温柔女声读这段话"

1. 用户未提供文本且无明确可引用的上下文时，先询问要读的内容。
2. 按上一节确定音色，拿到真实 `voc_` id；"第二个""刚才那个声音"沿用真实结果，不编造 ID。
3. 查询 `breeze balance --agent`。用户已要求生成时直接执行；余额不足则停止。把原文写入当前项目 `.local/breezetts/` 下的 UTF-8 文本文件，用 `--input` 传入，避免把原文拼进 shell 命令。文件名唯一，保留已有产物。
4. `breeze tts --input TEXT_PATH --voice VOICE_ID --format mp3 --file AUDIO_PATH --stream --play --agent`。用户要求语速或语气时用 `--speed`（0.5–2.0）或 `--instructions`，不要把指令写进朗读正文。不要自动改写用户文本。念法指令的写法见 [念法指令最佳实践](references/instruction.md)。
5. 检查返回 JSON、输出路径、文件存在且非空，再交付可点击的音频文件并展示声音名称。已流式播放过的文件不要重复播放。检查播放相关返回与 stderr，不能只凭文件存在就声称已播放。声音从本机音频设备输出，是否内嵌播放由 WorkBuddy UI 决定。

## 默认播放行为

用户要求生成语音时，默认流式播放并保存文件，不必再问是否播放。用户说"不要播放""静音""只保存文件"时优先遵守，使用 `--no-play --agent`，且不要随后补播。

- **普通 TTS**：明确传 `--stream --play --agent`，不用 `--async`、不用 `--no-stream`。以短等待返回后台会话并保持进程运行；不要因暂时没有 stdout 就重启生成。
- **声音设计、克隆、remix/localize**：无统一流式试听保证。生成用 `--agent`，取到真实预览 ID 后 `voice preview download PREVIEW_ID --file PREVIEW_PATH --agent`，再 `breeze play PREVIEW_PATH` 自动试听一次。设计时 `--preview-count 1`，不擅自增加付费候选。
- **历史/任务下载**：仅查询、仅下载不自动播放；用户要求试听或此前已请求生成并试听时，下载完成后播放一次。
- **不支持流式播放的环境或格式**：保留已生成结果，说明实际限制，完成后播放保存的文件；不得为播放失败重新调用付费合成。无音频设备或远程执行环境下返回文件，并如实说明未在用户电脑出声。
- **用户要求停止**：终止当前播放/生成会话，保留已有产物，不自动重启。多个音频顺序播放，不重叠。

## 字幕与时间戳

用户要字幕、要"每句话什么时候说"、要把旁白和画面/板书对齐时，走时间戳，不要按字数估算。要点：

- 加 `--with-timestamps`，取返回里的 `word_timestamps` 或旁文件 `<audio>.timestamps.json`
- 中文的 `word` 是**短句级片段**，标点单独成条且带时长（= 停顿），天然就是句级字幕
- 字幕止于标点的 `start`，不要用它的 `end`，否则字幕会在静音里滞留

完整规则、SRT 组装脚本与常见错误见 [字幕与时间戳最佳实践](references/subtitles.md)。

## 功能路由

详细参数与示例见 [CLI 操作参考](references/commands.md)。不熟悉的子命令先查 `--help`；支持范围用 `breeze capabilities --output json` 查询。

| 用户需求 | CLI 命令族 |
| --- | --- |
| 找声音、声音信息、试听 | `voice search/list/get/play` |
| 文本转语音、流式/异步语音 | `tts`、`tts realtime`、`jobs` |
| 字幕、词级时间戳 | `tts --with-timestamps` |
| 优化念法描述 | `tts enhance` |
| 设计、克隆、变声、语言转换 | `voice design/clone/remix/localize` |
| 预览下载、保存、声音修改/删除 | `voice preview`、`voice edit/delete` |
| 查询任务、历史及下载 | `jobs get/wait/download`、`history list/get/download` |
| 播放已有音频 | `play`、`history play`、`voice preview play` |
| 账户、余额、用量、模型 | `whoami`、`balance`、`usage list`、`models list` |

付费生成遵循用户请求，不擅自生成多个候选。保存、修改、删除云端声音或历史仅在用户明确要求时执行。声音 ID 与预览 ID 不能混用；保存 preview 需要 `--language`。克隆使用用户指定的参考音频。

用户要求后台生成、批处理或遇到服务限制时才用 `tts --async`，记录 job ID，再用 `jobs get` 或有界 `jobs wait` 查询下载。异步任务不能边生成边播放，完成后用 `breeze play AUDIO_PATH` 播放一次。常规"读这段话"保持流式，不因耗时长改为异步。排队不等于完成。超时或断线时先查已知任务与历史，不自动重复提交收费生成。

## 错误恢复

读取 `error.code/message/suggestion`：`auth` 走上文的自动登录流程；`quota` 报告余额不足并停止；`usage` 查帮助修正参数；`not_found` 重新查询资源；`policy_blocked` 展示原因并停止。`timeout/network` 对只读查询最多重试一次；生成先核实历史与任务状态，结果未知时告知用户，不能无限重试。

"换男声""慢一点"等后续请求沿用已知文本与真实资源 ID，只调整用户要求的参数，产生新文件。最终交付结果与简短说明，不要把命令教程当作执行结果。
