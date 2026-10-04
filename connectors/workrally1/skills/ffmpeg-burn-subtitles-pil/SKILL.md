---
name: ffmpeg-burn-subtitles-pil
description: 在**缺少字幕滤镜的 ffmpeg 构建**上把字幕烧进视频像素（硬字幕），并完成「标题板 + 正片 + 片尾板」的成片合板。当用户要求烧字幕/硬字幕/把 SRT 压进画面，或本机 ffmpeg 报 `No such filter ass` / `subtitles` / `drawtext`，或需要把多段对白按时间轴排布成双语字幕时使用。核心方案：PIL 渲染透明 PNG 图层 → ffmpeg concat + 单次 overlay（不依赖 libass/freetype）。同时覆盖静音/无声视频的四轨混音与侧链闪避不可用时的电平差替代方案。注意：若只是外挂 SRT 或环境有 libass，请直接用 `subtitles` 滤镜，不要走本流程。
description_zh: 无字幕滤镜环境的字幕烧入
description_en: Burn subtitles via PIL layers
disable: false
agent_created: true
---

# ffmpeg-burn-subtitles-pil

用 **PIL 渲染透明 PNG 图层 + ffmpeg overlay** 的方式烧硬字幕，适用于 ffmpeg 构建**不含 libass/freetype/fontconfig** 的环境。

## When to use

- 用户要求「烧字幕 / 硬字幕 / 把字幕压进视频 / 加字幕的成片」
- `ffmpeg -filters` 查不到 `ass` / `subtitles` / `drawtext`，或报 `No such filter: 'ass'`
- 需要**双语字幕**（如中上英下、各一行、底部居中、白字细黑描边）按语音时间轴逐句同步
- 需要把「片头板标题 + 正片 + 片尾板」拼成完整交付版
- **不适用**：只需外挂 SRT 文件；或环境有 libass（那就直接 `subtitles=xxx.srt` 一行搞定）

## 第 0 步（必做）：先探明本机 ffmpeg 的真实能力

```bash
ffmpeg -hide_banner -filters > /tmp/ff_filters.txt
ffmpeg -hide_banner -version | head -3   # 看 configuration 里有没有 --enable-libass / --enable-freetype / --enable-fontconfig
```
**用 Grep 工具检索 /tmp/ff_filters.txt**（注意：部分沙箱里 shell 的 `grep` 管道被禁用，会静默返回空 —— 不要据此判断「滤镜不存在」）。
确认这几个是否在：`fade` / `afade` / `anullsrc` / `concat` / `overlay` / `scale` / `format`。
**同时确认双输入音频滤镜**（见 Pitfalls 第 4 条）。

## Steps

### 1. 排时间轴 → 生成字幕母版（SRT + 一份机器可读 JSON）

写一个 Python 脚本，输入「每句台词 + 所属单元/镜头 + 起始秒」，输出：
- `*_中文.srt` / `*_英文.srt` / `*_双语.srt`（供外挂）
- `*.ass`（文字母版存档）
- **`subs.json`**：`[{key, file, unit, start, end, dur, cn, en}, ...]` —— 后续两步都读它，**不要回头去解析 SRT/ASS**

**排布规则（关键）**：
- 若成片实际单元时长 ≠ 设计网格（例如设计 30s、实测 30.0417s），必须做绝对时码换算吸收累计漂移：
  `to_abs(unit, t) = (unit-1)*UNIT_LEN + (t - (unit-1)*GRID)`
- 必须 **全局串行** 排布，不能按单元分组后再串行 —— 否则跨单元的长句（L-cut）会让溢出字幕与下一单元首句重叠
- 典型参数：`LEAD_IN=0.25` `GAP=0.15` `MIN_DUR=0.60`
- 排完**打印校验**：重叠数、越界数必须为 0；并列出所有跨单元台词

### 2. PIL 渲染透明 PNG 图层（每句一张）

用 `scripts/gen_sub_overlay.py` 为每条 cue 渲染一张**全画布尺寸的 RGBA 透明 PNG**。

- 字体（macOS）：中文 `/System/Library/Fonts/STHeiti Medium.ttc`(**index=1**)；英文 `/System/Library/Fonts/HelveticaNeue.ttc`(**index=0**)。其他系统用 `font.get_fonts()` 或 `fc-list` 找。
- 双语版式（中上英下）：中文较大、英文约中文的 0.55–0.6 倍；各自一行；底部居中。
- 描边靠 `draw.text(..., stroke_width=N, stroke_fill=(0,0,0,alpha))`。
- 居中要**用 textbbox 修正偏移**，不要直接用 `(W-w)/2`：
  ```python
  bbox = dr.textbbox((0,0), text, font=font, stroke_width=stroke)
  w = bbox[2]-bbox[0]; h = bbox[3]-bbox[1]
  x = (W-w)//2 - bbox[0]; y = bottom_y - h - bbox[1]
  ```
- 另存一张**全透明垫片** `transparent.png`（间隙用）。

### 3. 组成「字幕图层视频」再单次 overlay

用 `scripts/gen_sub_layer.py`：把 cue PNG 与透明垫片按时间轴交替排列 → `-loop 1 -framerate FPS -t <dur> -i <png>` → `concat` 成一条图层流 → 对正片做**一次** `overlay`。

```bash
ffmpeg -y -v error -i <正片> \
  -loop 1 -framerate 24 -t <dur0> -i <seg0.png>  ... (N 段) \
  -filter_complex "[1:v]format=rgba,setpts=PTS-STARTPTS[s0]; ... ; [s0][s1]...concat=n=N:v=1:a=0[layer]; [0:v][layer]overlay=0:0:format=auto,format=yuv420p[vout]" \
  -map "[vout]" -map 0:a:0 -c:v libx264 -preset fast -crf 18 -c:a copy -movflags +faststart -t <总时长> <输出>
```

**⚠️ 输入索引从 1 开始**（`-i 正片` 占输入 0）——见 Pitfalls 第 1 条，这是最容易踩的坑。

### 4.（可选）标题板 + 正片 + 片尾板 合板

用 `scripts/assemble_final.py`：把标题板/片尾板（静态图）先编码成与正片**完全同参数**的片段（分辨率/帧率/pix_fmt/音频采样率声道一致），再用 concat demuxer **无损**拼接：
```bash
ffmpeg -f concat -safe 0 -i list.txt -c copy -movflags +faststart out.mp4
```
静态图转片段的 `-vf`：`scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2:color=black,fade=t=in:st=0:d=1,fade=t=out:st=<dur-0.8>:d=0.8,format=yuv420p`，并配 `-f lavfi -i anullsrc=r=48000:cl=stereo` 补静音轨。

## Pitfalls

1. **⚠️ 静默失败：`rc=0` 但字幕一帧都没烧进去 —— 输入索引 off-by-one。**
   `-i 正片` 是输入 **0**，图层段是输入 **1..N**。若循环里写 `[{k}:v]`（k 从 0 起），就会**把正片本身当成第 0 段图层** → concat 出的「图层」前段是原画，真字幕段被挤到片尾之外被 `-t` 裁掉。
   **必须写 `[{k+1}:v]`。**
   → **通用教训：ffmpeg 滤镜图不报错 ≠ 结果正确。`rc=0` 只证明语法通过。**

2. **合板必须做小样验证，不要直接跑全长。**
   给脚本加 `--tlimit=<秒>` 参数（只编码前 90–120 秒），几十秒出结果；抽全分辨率帧看底部区域确认字幕出现；通过后再跑全长。全长 600s/1080p 档约 4–5 分钟。

3. **不要用 shell 的 `grep` 判断 ffmpeg 能力。** 部分沙箱会静默拦截 `cmd | grep`，返回空 stdout 且退出码 0 —— 会被误读成「没有这个滤镜」。改成 `> /tmp/x.txt` 后用 Grep 工具检索。

4. **侧链闪避不可用（部分构建）**：`sidechaincompress` / `sidechaingate` 在 `filter_complex` 里可能**无法解析第二个输入 label**，报 `Error binding filtergraph inputs/outputs: Invalid argument`（rc=234）。最小复现可确认。
   → 替代方案：**静态混音 + 电平差**。例：对白 gain 1.9、终混 `amix=inputs=2:normalize=0,alimiter=limit=0.94:level=disabled`，对白 mean −16dB / 底噪 −30dB → SNR 14dB，对白清晰度够用。代价是底噪不自动下压。

5. **PIL 居中不要用 `(W-w)/2`**：`textlength`/`textbbox` 不含描边与 bearing，直接算会偏。用 `textbbox` 把偏移减掉。

6. **字体 index 要试**：`.ttc` 是字体集合，`STHeiti Medium.ttc` 的 index=1 才是 Medium；`index=0` 可能报错或给出另一种字重。

7. **跨单元长句（L-cut）**：若一句台词跨越单元边界，混音时两段必须各自只播自己那一段（`atrim=start=<负偏移>` 接续），**不能整句重复播放**，否则接缝处会出现叠字。

## Verification

1. **字幕层**：抽 2–3 帧全分辨率图，裁出底部 20% 条带拼版目检 —— 必须**肉眼看到字**。只看 `rc=0` 或文件体积不算验收。
2. **时间轴**：脚本里断言「重叠=0、越界=0」；末句结束时间 ≤ 片长。
3. **L-cut 接续（信号级，硬证据）**：对每条跨单元台词，取**目标单元首段音频**与其源音频「应播区段」做**归一化互相关**，峰值应落在 lag≈0、NCC 显著（实测可达 0.99）。短窗（<0.4s）把搜索范围收到 ±50ms 并放宽最小窗口，否则相关函数会因样本不足返回哨兵值（如 −2.0）被误判为失败。
4. **成片规格**：`ffprobe` 核对 duration / 分辨率 / 帧率 / 音频采样率声道数，与源一致。
5. **合板段**：抽头板、正片首帧、片尾板各 1 帧拼版，确认淡入淡出与三段衔接无黑帧、无错位。

## 参考脚本

> 以下四个脚本是从一次真实项目（21:9 / 600s / 双语字幕）跑通后归档的，**里面的绝对路径与项目常量是示例**，复用时改开头的 `PROJ / WD / FIN / SR / UNIT_LEN` 等常量即可。它们同时是「排布 → 渲染 → 合板 → 验收」四个阶段的参考实现。

- `scripts/gen_sub_overlay.py` — subs.json → 逐条透明 PNG 图层
- `scripts/gen_sub_layer.py` — PNG 序列 → 图层视频 → 单次 overlay（含 `--tlimit` 小样通道）
- `scripts/verify_lcut.py` — 跨单元对白接续的信号级互相关验收
- `scripts/assemble_final.py` — 标题板 + 正片 + 片尾板 同参编码 + 无损 concat
