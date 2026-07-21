---
name: handdraw
description: 手绘动画生成本地能力——按风格目录用 ImageGen 出图，调 vibeknow 手绘绘制，再本地渲染成「绘制→落定」手绘视频。
---

# 手绘动画 Skill

## ⚠️ 脚本路径（先做这一步，否则命令全找不到）
本 skill 的脚本在**本 SKILL.md 所在目录**下的 `scripts/`。而你的 shell 工作目录是**用户工作目录**（沙箱），不是插件目录 —— 所以**不能用相对路径**。

**每次会话先设一次**（把路径换成加载本技能时告知你的 SKILL.md 绝对路径的所在目录）：
```bash
SKILL_DIR="/Users/<你>/.workbuddy/plugins/marketplaces/my-experts/plugins/vibeknow-handdraw/skills/handdraw"
```
下文所有命令都用 `"$SKILL_DIR/scripts/xxx.mjs"`。
（产物目录 `JOBDIR` 仍然要落在**当前工作目录**下 —— 沙箱只允许写这里。）

## 风格目录
可用风格见 @references/styles.md（id / 名称 / 分类 / style_prompt）。出图时把所选风格的 `style_prompt` 拼在画面描述前。

## 环境准备（首次使用，幂等）
本专家以「纯源码」分发，运行依赖（remotion 渲染引擎、chrome-headless-shell）在**首次使用时自动装进包内**：
`node "$SKILL_DIR/scripts/run.mjs" init`（已装则秒过；chrome 走国内镜像 npmmirror，失败回退官方源）。
- 装进：`render/node_modules`、`render/node_modules/.remotion`（chrome 缓存）。
- **无 MCP、无连接器**：手绘绘制/旁白/登录全走脚本（`run.mjs`/`handdraw-page.mjs`）+ Bash 调用；`mcp/` 目录只是零依赖的客户端函数库。

## 落盘约定（输入输出位置 + 命名，务必遵守）
一次生成 = 一个 **job 目录 JOBDIR**：开工先 `node "$SKILL_DIR/scripts/workspace.mjs" new --topic "<主题>"` 拿到它的绝对路径。目录内用**两位页号 NN 同号绑定**：
```
<JOBDIR>/  01.png 01.vec.json 01.mp3   02.png 02.vec.json 02.mp3  …  scenes.json  成片.mp4
```
- ⚠️ **同号配对硬约束**：第 N 页的图 `NN.png` / 绘制数据 `NN.vec.json` / 音频 `NN.mp3` 必须同一个 NN；scenes.json 第 N 项也同号。**这是防止图与绘制数据错位、渲染出错的关键。**
- 多次会话：换主题/整体重生 → 新建 JOBDIR；改某页 → 复用原 JOBDIR、覆盖该页 `NN.*` 后重跑渲染。

## 本地生成流程（第 N 页）
1. 写 `visual` 画面描述：**严格按 @references/visual-rules.md**（禁抽象总结句、不提文字、屏幕/UI/照片做画风适配转译、人物锁进画风、跨页角色一致且禁指代）。出图 prompt **用脚本生成**（自动拼画风+锁画风尾巴，勿手拼）：
   `node "$SKILL_DIR/scripts/build-gen-prompt.mjs" --style "<style_prompt>" --visual "<visual>"` → 输出整串喂 ImageGen，**存 `<JOBDIR>/NN.png`**。
   - 📐 **出图尺寸 = 成片尺寸**（同比例、同大小）。由 `--aspect` × `--resolution` 唯一确定：

     | `--aspect` | 比例 | **720p（默认）** | 1080p | 540p |
     |---|---|---|---|---|
     | `horizontal`（默认） | 16:9 | **1280×720** | 1920×1080 | 960×540 |
     | `vertical` | 9:16 | **720×1280** | 1080×1920 | 540×960 |
     | `square` | 1:1 | **720×720** | 1080×1080 | 540×540 |
     | `classic` | 4:3 | **960×720** | 1440×1080 | 720×540 |
     | `portrait43` | 3:4 | **720×960** | 1080×1440 | 540×720 |

   - 🚦 **这是硬约束，不是建议**：所有页出完后、**掏钱绘制之前**，先跑一次 `check-images.mjs <JOBDIR>`（见下）统一校验每张 `NN.png`，不合格**先重新出图**再画（退 4，此步不花积分），它会告诉你该出多大、哪几页不合格。拦截的四种情况：**比例不对**（→黑边/裁切）、**短边小于成片档位**（→定格画面糊）、**长边 >1920**（→服务端拒）、**各页尺寸不一致**（→成片画面忽大忽小）。
   - 💰 出图**花 WorkBuddy 积分**（渲染只花本地时间），分辨率越高越贵 —— **默认就用 720p 那一档，别主动往上加**；用户要更高档时**顺带告知会多花生图积分**。
   - 生图模型出不了该尺寸时，**必须保持同宽高比**（比例变了必被拦）。
   - ⚠️ **长边 ≤ 1920px**（出图与任何图片素材都是）：1920 **恰好合规**；超过会被 `handdraw` 服务端拒（提示 long edge must not exceed 1920px），需先等比缩到 ≤1920。
2. **绘制不在本步做**——所有页的图出完、尺寸预检通过后，再**逐页**手绘绘制（见「逐页手绘绘制」）。每页用 `handdraw-page.mjs <JOBDIR>/NN.png [--title <主题>]`（从图路径派生同名 `.vec.json` 与页码，结构上杜绝错位，别手写 json）。
3. 若该页有旁白：`node "$SKILL_DIR/scripts/run.mjs" synthesize "<narration>" --out <JOBDIR>/NN.mp3`（同号落盘）。可选把旁白文本写 `<JOBDIR>/NN.txt`。
   - **默认引擎 `microsoft`（edge-tts，免费、免登录、不扣积分）**——旁白默认走这个，正常无需登录/积分。`--voice <id>` 可选，缺省 `zh-CN-XiaoxiaoNeural`。
   - `--engine vibeknow` 为**可选高级音色/声音克隆**（需登录 + 扣积分）；仅在用户明确要 vibeknow 音色时用。
   - ⚠️ **绝不因"想省事/想换个音色"擅自切引擎**；引擎由默认或用户明示决定。

## 鉴权（in-chat 登录，免终端）
`node "$SKILL_DIR/scripts/run.mjs" login` → JSON `{status:"pending",verification_uri,user_code}`，把链接+验证码展示给用户在浏览器确认；再 `run.mjs login-status` → `{status:"success"}` 即登录成功（`pending` 稍等再查，`error` 重新 login）。登录态存本机固定路径，后续免登。

## 逐页手绘绘制（所有页出图+旁白完成后做）
**先预检、再逐页绘制。**

1. **出图尺寸预检（掏钱前，一次过）**：
   `node "$SKILL_DIR/scripts/check-images.mjs" <JOBDIR> [--aspect <画幅>] [--resolution <档位>]`
   ⚠️ `--aspect` / `--resolution` **要和出图、渲染时用的完全一致**。合格 → `{"ok":true,...}` 退 0；不合格 → `{"ok":false,"problems":[...]}` **退 4**（此步不花积分），按提示把不合格的页**重新出图**后再画。

2. **逐页绘制**：对每一张 `NN.png`
   `node "$SKILL_DIR/scripts/handdraw-page.mjs" <JOBDIR>/NN.png --title "<视频主题>"`
   → 调服务端画好该页，**按图名派生**写出 `<JOBDIR>/NN.vec.json`（同名同目录，结构上杜绝图/数据错位，别手写 json）。打印生成的路径。

**计费口径**：**逐页各扣各的** —— 每页一次冻结→结算，积分明细**一页一条**「手绘绘制 · 《主题》· 第 n 页」，带 `workbuddy` 标签。

- 未登录 → 先按「鉴权」`login`（`handdraw-page` 会报未登录）。
- **可安全补跑**：某页已有有效 `NN.vec.json` 就不必再画（重跑会再扣一次费）；只对**缺 `NN.vec.json`** 的页跑 `handdraw-page`。
- **单页失败**：`handdraw-page` 非 0 退出、stderr 是错误原因 → 重跑该页重试，或按 SOP 降级（放 `NN.static`）。脚本**绝不写出空的 `NN.vec.json`**（返回空绘制数据即报错退出，不落盘）。
- **余额不足**：`handdraw-page` 输出 `{"error":"insufficient_credits","service":"handdraw"}` **退 2** → 走下方 SOP（**优先充值**）。逐页扣费，遇到不足即停在当前页，已画好的页不受影响。

## 积分不足与降级（重要 SOP，禁止自由发挥）
`handdraw-page` / `synthesize` 遇积分不足时，**stdout 输出 `{"error":"insufficient_credits","service":"handdraw"|"tts"}` 且非 0 退出**。收到此信号：
- **立即停止该步骤**：不重试、不静默改用别的能力、不手写/编造绘制数据或音频冒充产出。
- **service=`handdraw`（绘制不足）**——绘制只有 vibeknow 一条路：
  1. **第一动作：引导用户充值**（说明积分不足、去哪充），继续正常"逐笔绘制"。这是默认建议。
  2. 用户**不充值**时，**才**提供降级选项：**该页用原图直接定格、跳过绘制**（不扣积分）。**必须先向用户二次确认**，同意后才：给该页放同号空文件 `NN.static`（`: > <JOBDIR>/NN.static`），跳过 `handdraw-page`，其余流程照常。**不主动替用户选降级。**
- **service=`tts`（vibeknow 音色不足）**——因默认就是免费微软，正常遇不到；只有用户主动选了 `--engine vibeknow` 才会。提示用户：**改回默认免费微软音色继续**（去掉 `--engine vibeknow` 重跑）**或充值**。

## 串成成片（带转场+旁白）
1. **别手写 scenes.json**——用脚本按文件名 `NN` 自动配对（LLM 不参与配对，配不错）：
   `node "$SKILL_DIR/scripts/build-manifest.mjs" <JOBDIR>` → 生成 `<JOBDIR>/scenes.json`（`NN.png`＋`NN.vec.json`＋`NN.mp3`同号配对；`NN.txt` 作 narration；缺 `NN.vec.json` 的页报错，按提示补跑 handdraw-page）。
   - **降级页**：某页放同号空文件 `NN.static` → 该页用原图直接定格（不逐笔绘制），此时**不要求** `NN.vec.json`。仅在积分不足降级时用（见「积分不足与降级」）。
   - 有 `audio` 的页：时长按旁白音频自动校准（音频时长 + 尾留 `--tail-seconds`，默认 1.0s）；无 `audio` 页用 `--scene-seconds`（默认 4s）。
2. 渲染成片：
   `node "$SKILL_DIR/scripts/render-reel.mjs" --manifest <JOBDIR>/scenes.json --out <JOBDIR>/成片.mp4 --aspect <horizontal|vertical> --transition <fade|slide|wipe> [--scene-seconds 4] [--transition-seconds 0.5] [--tail-seconds 1.0]`
   - **画幅 `--aspect`**：`horizontal`(16:9，默认) / `vertical`(9:16) / `square`(1:1) / `classic`(4:3) / `portrait43`(3:4)。**按用户要求选**；不认识的值会直接报错，不会静默当横版。
   - **分辨率 `--resolution`**：按「短边」表示，**默认 `720p`**（540p 实测偏糊，720p 是发布的合理下限）；可选 `1080p`（上限）/ `540p`。
     - **默认就用 720p，不要主动上 1080p**——出图分辨率要跟着升，而**出图是花积分的**。
     - **按用户要求给**：用户说要 1080p 就传（并提醒会多花生图积分）。
     - **超过 1080p（2K/4K）→ 脚本自动压到 1080p，返回值里带 `clamped` 说明**，不报错、不卡流程。**把这个说明如实转告用户**（合成短边就 1080，再放大只会糊）。
   - ⚠️ **`--aspect` / `--resolution` 必须和出图时用的完全一致**（`check-images.mjs` 预检也要传同样的值，它会据此校验出图尺寸）。

### 🖥 渲染吃机器资源(默认已限流)
渲染并发默认限到 **2**(而非 remotion 缺省的 ≈核数/2)——本专家跑在用户个人电脑上、同时还在跑 WorkBuddy,并发拉满会把机器占死。**默认就好,别动。** 机器很闲、想快点可设环境变量 `HANDDRAW_RENDER_CONCURRENCY=4` 重跑;想更省资源设 `=1`。

### ⚠️ 渲染很慢，别把没渲完的文件当成品（重要）
渲染一条几分钟的片子**可能要好几分钟甚至更久**（分辨率越高越久）。请这样处理：
- **调 Bash 时把超时设到最大**，耐心等它跑完。
- **成片只有渲完才会出现**：脚本先渲到临时文件，ffprobe 校验通过后才**原子改名**成 `成片.mp4`。所以 `成片.mp4` **一旦存在就一定是完整可播的**；渲染期间它**根本不存在**。
- **命令超时了怎么办**：**不要重跑渲染**（只会更久）。渲染进程还在后台跑 —— 改为**每隔 30–60 秒轮询一次** `ls -la <JOBDIR>/成片.mp4`，等它出现即可。
- **不要自己 ls/stat 去判断大小是否正常**。渲染成功时脚本会直接输出 JSON：
  `{"status":"done","out":"…/成片.mp4","width":1280,"height":720,"durationSec":46.55,"bytes":2104538}`
  **交付时直接用这里的 width/height/durationSec/bytes 汇报**（这是校验过的真实值）。

## 数据格式铁律
handdraw 返回 `{coarse, full}`，**整个原样写入 json**。⚠️ 切勿只取 `.full` 拍平——渲染层取 `j.full`，拍平数据会判空走兜底，结果只剩原图淡入、没有逐笔手绘过程。

## 踩坑经验
（以下由 AI 在实际使用中自动积累，请勿手动删除。遇到反复出错的点，简短记一条，供后续参考。）
- 图与绘制数据错位 → 已用 `handdraw-page.mjs`（派生同名 vec.json）+ `build-manifest.mjs`（按 NN 自动配对）根治，别再手写 scenes.json。
- 出图:**必须串行逐页落 `NN.png`**(每出一张立即移到 `NN.png`,确认落好再出下一张)。🚫 **不要并行出图**,更不能「并行写同一目录 + 事后按关键词重命名」—— 猜错一页就会让第 3 页配上第 5 页的画面,**视频照渲、内容全错、无从发现**。
- 文件只往「当前工作目录」下的 JOBDIR 写，别往家目录/外部绝对路径（沙箱拒写）。
