# 字幕与时间戳最佳实践

时间戳只有一个可信来源：**TTS 返回的词级时间戳**。不要按字数估算，不要按"每秒 4 个字"折算，不要在时间轴里写死秒数——换音色或改一个字，估算就全错。

## 怎么拿到

CLI（推荐，字幕场景显式指定 `lookahead`）：

```sh
breeze tts --text "……" --voice voc_reys5un5t4ed --with-timestamps \
  --timestamp-mode lookahead --format mp3 --file out.mp3 --output json --agent
```

返回里带 `word_timestamps`，同时写一个旁文件 `out.mp3.timestamps.json`（内容相同）。异步任务用 `jobs wait --file` 落盘后再取。

HTTP 直连（没有 CLI 时）：

```sh
curl -X POST "https://api.breeze.blue/v1/text-to-speech/$VOICE_ID/with-timestamps?output_format=mp3" \
  -H "xi-api-key: $BREEZE_API_KEY" -H 'content-type: application/json' \
  --data '{"text":"……","language_code":"zh"}'
```

返回 `{"audio_base64":"…","content_type":"audio/mpeg","word_timestamps":[…]}`，`audio_base64` 解码后就是音频。

## 切分粒度：两条通道不一样

这是最容易踩的坑，实测结论：

| 通道 | 粒度 | 一条 `word` 长什么样 |
| --- | --- | --- |
| CLI `--timestamp-mode chunk`（默认） | 短句级 | `"第一句验证模式"`、`"。` |
| CLI `--timestamp-mode lookahead` | 短句级，边界更准 | 同上，但 `end` 更贴近真实发音结束 |
| HTTP `/with-timestamps` | **字/词级** | `"第一"`、`"句"`、`"验证"`、`"无"`、`"CLI"` |

同一句话的实测差异：

```
chunk      第一句验证模式 0.00 → 1.81   。1.81 → 2.17
lookahead  第一句验证模式 0.00 → 1.47   。1.47 → 2.09
HTTP       第一 0.00-0.32  句 0.32-0.49  验证 0.49-1.01  无 1.01-1.41 …
```

chunk 把停顿并进了短语，句子 `end` 偏晚约 0.3 秒；lookahead 的 `end` 更接近真正说完的时刻。**做字幕用 `lookahead`**，字幕消失不会拖沓。

HTTP 的字级结果信息更细，但必须自己合并——**一字一条会闪成跑马灯**。

不管哪种粒度，都遵循同一条规律：**标点单独成条，且带时长**（`"。"` 占 0.4–0.6 秒），这个时长就是停顿。

时间是浮点秒，别取整，取整会累积漂移。

## 组装句级字幕

规则：

- 遇到句末标点（`。` `！` `？` `；` `…`）收一条字幕
- **终点** = 句末标点的 `start`（停顿开始即消失），不要用标点的 `end`
- 遇到 `，` `、` `,` 且已累积 ≥ 8 字时，可作软断点收一条，读起来更自然
- 没有标点的长片段按 14 字硬切，切点必须落在完整 `word` 边界
- 单片最短 0.8 秒、最长 6 秒；不足 0.8 秒的短句并入下一条
- 字级输入（HTTP）务必先合并到句，再套上述规则

可直接跑的组装脚本（兼容两种粒度）：

```python
import json, sys

HARD = set("。！？；…")
SOFT = set("，、,;")
PUNCT = HARD | SOFT

def build(ts, max_chars=14, soft_at=8, min_dur=0.8, max_dur=6.0):
    cues, buf = [], []

    def flush(end):
        if buf:
            cues.append((buf[0]["start"], end, "".join(x["word"] for x in buf)))
            buf.clear()

    for w in ts:
        tok = w["word"]
        if tok in PUNCT:
            if buf and (tok in HARD or sum(len(x["word"]) for x in buf) >= soft_at):
                flush(w["start"])
            continue
        buf.append(w)
        if sum(len(x["word"]) for x in buf) >= max_chars:
            flush(buf[-1]["end"])
    flush(buf[-1]["end"] if buf else 0)

    out = []
    for s, e, t in cues:
        e = max(e, s + min_dur)
        if e - s > max_dur:
            e = s + max_dur
        if out and s < out[-1][1]:
            s = out[-1][1]
        out.append((s, e, t))

    # 合并被硬切后剩下的孤立短碎片（如"2026 年"的"年"）
    merged = []
    for s, e, t in out:
        if merged and len(t) <= 2 and len(merged[-1][2]) + len(t) <= 16:
            ps, pe, pt = merged[-1]
            merged[-1] = (ps, e, pt + t)
        else:
            merged.append((s, e, t))
    return merged

def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

ts = json.load(open(sys.argv[1]))["word_timestamps"]
for i, (s, e, t) in enumerate(build(ts), 1):
    print(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{t}\n")
```

用法：`python3 to_srt.py out.mp3.timestamps.json > out.srt`。

## 排版规则

- **中文每行 ≤ 14 个全角字符，最多 2 行**；英文每行 ≤ 42 字符
- 断行优先在标点或语义停顿处，不要把一个词拆到两行
- 句末句号可以不显示，但问号、感叹号保留（影响语气）
- 数字、公式、字母缩写保持原样，不要转写

## 视频里的字幕

Video Lab 没有独立的字幕命令，字幕在 motion 层随拍点出现：

- **不要写死秒数。** 用 `$start` / `$end` 或 `{#cue}` 锚点，让字幕跟着音频走。
- `output/audio/beats.md` 的每行时间就是短语被说出的时刻，直接用作字幕切换点最稳。
- 一行字幕对应一个 cue，超过 14 字就拆成两个 cue，不要靠缩小字号硬塞。
- 字幕轨放在安全区：竖屏底部留 15% 安全距离，避免被平台 UI 遮挡。

## 常见错误

| 错误 | 后果 |
| --- | --- |
| 按字数估算时长 | 与实际语音对不上，越到后面漂移越大 |
| 把标点条目做成字幕 | 闪出一帧"。"，很脏 |
| 用标点的 `end` 做字幕结束 | 字幕在静音里多停半秒，观感迟钝 |
| HTTP 字级结果直接逐条输出 | 一字一闪，像跑马灯 |
| 把 chunk 的 `end` 当句末 | 平均晚 0.3 秒，整片字幕偏拖 |
| 时间戳取整数秒 | 精度损失，长片累计偏移 |
| 时间轴里写 `duration: 3.2` | 换音色即错位，必须走音频时间轴 |
| 先做字幕再配音 | 顺序反了，字幕必然要重排；先配音再出字幕 |
