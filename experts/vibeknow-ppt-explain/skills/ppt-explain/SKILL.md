---
name: ppt-explain
description: 把 PPT / PDF / Word 文档逐页转成图，逐页写旁白配音，本地 remotion 加运镜/转场/字幕渲成讲解视频。含文档解析、TTS、分镜、渲染全套脚本。
---

# ppt-explain —— 文档 / PPT 逐页讲解成片

把一份**已有文档**（PPT / PDF / Word）变成「逐页展示 + 讲解旁白 + 运镜」的视频。**不生成插画、不做手绘绘制**——画面就是文档原页。与手绘专家共用一套渲染/TTS/登录骨架，独有的只是**文档解析**与**运镜 Layout**。

## 脚本目录（都在本 skill 的 scripts/ 下）

| 脚本 | 来源 | 作用 |
|---|---|---|
| `run.mjs init` | 复用手绘 | 幂等装 remotion 渲染依赖 + chrome（国内镜像优先） |
| `workspace.mjs new --topic` | 复用手绘 | 在当前工作目录建 JOBDIR，回绝对路径 |
| `doc-to-pages.mjs <file> --out <JOBDIR>` | **本专家新增** | 文档逐页转 `NN.png` + 导出 `source.txt`（逐页文字，供整体解析） |
| `run.mjs synthesize "<text>" --out NN.mp3` | 复用手绘 | edge-tts（默认免费）/ vibeknow（付费高级音色）合成旁白 |
| `build-manifest.mjs <JOBDIR>` | 本专家版（去掉 vec 依赖） | 按 `NN` 同号配对 `png+mp3+txt` → `scenes.json` |
| `run.mjs login` / `login-status` | 复用手绘 | 设备码登录（成片闸门用；带 workbuddy channel 归因） |
| `render-reel.mjs --manifest ... --out ...` | 本专家版（新 Layout + 登录闸门） | 未登录拒渲，登录后 remotion 出片，输出校验过的 `width/height/durationSec/bytes` JSON |

> **同号配对铁律**：`NN.png`/`NN.txt`/`NN.mp3` 必须同一个两位序号，`build-manifest.mjs` 只按文件名配对，配不错。
> **写稿铁律**：先整体解析 `source.txt` + 页面图 → Stage1 导演定调性+每页字数预算 → Stage2 逐页写 `NN.txt`（不是一页一句地攒，页页要承接）→ `check-script.mjs` 机器核字数达标。**全自动一次性出片，中途不停下审稿**（用户诉求）。详见两份 references + agent SOP。

## doc-to-pages.mjs（新脚本，逐页转图）

- **PDF**：`pymupdf`（fitz）逐页 `get_pixmap(dpi=144)` → `NN.png`。144DPI 是密度/体积平衡点。
- **PPTX**：走**纯 JS 渲染**（专家自带 Chrome + `@aiden0z/pptx-renderer`，见 `pptx-to-images.mjs`）逐页出图，**不依赖 Office/LibreOffice、不装任何东西**，谁的机器都能跑。
- **.ppt / .docx / .doc / .odp / .key**：只用机器上**已装**的引擎转 PDF（已装的 `soffice`/LibreOffice，或 macOS 已装的 Keynote），**绝不主动安装**（700MB LibreOffice 会劝退用户）；都没有 → 报 `NEED_PDF`，提示用户自己「导出为 PDF」再上传（几秒、零安装）。
- 输出：`NN.png`（页号从 01 起）+ 打印 `{pages, width, height}`，各页尺寸一致（同一文档天然一致）。
- 页数即视频镜头数；文档几页视频就几幕，不额外拆页。

## 渲染 Layout（render/layout/PptExplainLayout.tsx，新增）

- **底图 = 整页 `NN.png`**（`objectFit: contain`，按画幅居中，letterbox 用近黑 `#111318` 给「屏幕」质感）。
- **刻意不做运镜**（用户明确要求）：整页静态展示，不推近/不平移。动感只靠幕间转场。
- **转场**：幕间 `fade`（复用 `@remotion/transitions`），简单克制。
- **字幕**：底部安全区半透明底 + 白字，显示当前幕 `narration`（字号按画面高度 4%，可 `--no-subtitle` 关）。CJK 字体走系统栈（PingFang/YaHei/Noto），渲染机需有中文字体。
- 每幕时长 = 该页 `NN.mp3` 时长 + 尾部留白（默认 1.0s，别靠调大它凑时长）。

## 画幅 / 分辨率（与出图、渲染保持一致）

- `--aspect`：`horizontal`(16:9,默认) / `vertical`(9:16) / `square`(1:1) / `classic`(4:3)。**按文档原比例选**（PPT 多为 16:9 或 4:3），错配会黑边或裁切。
- `--resolution`：默认 `720p`；文档字多时 `1080p` 更清晰但更慢。
- PDF/PPT 转图 DPI 够高即可（144DPI 对 720p/1080p 都够），不像手绘要严格 check-images 尺寸档位。

## 登录 / 引流抓手（已定：成片就要登录）

本能力**全本地可跑**（转图 + edge-tts + remotion 都不需远端），没有手绘 vtracer 那种天然登录关卡。**引流 gate 落在「成片」这一步**：
- `render-reel.mjs` 自带闸门：**未登录直接拒渲**，返回 `{status:"login_required"}` 退出码 3 → 专家引导用户 `run.mjs login`（设备码，复用 vibeknow 账号 + `channel=workbuddy-ppt-explain` 归因）。
- 登录态 token 独立存 `~/.workbuddy/vibeknow-ppt-explain/token.json`（与手绘分开，各自归因）。
- 更远端的抓手（发布到 vibeknow / 分享链接 / 去水印高清 / 高级音色）用同一登录态。
