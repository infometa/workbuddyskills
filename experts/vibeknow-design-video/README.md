# 设计感图文视频师 · WorkBuddy 专家

把主题或文档变成有设计感的图文短视频：按版式模板填文案，ImageGen 出背景图，配旁白，本地渲染成片。风格随选。

## 能力边界
- **全本地（WorkBuddy 内）**：内容拆分/填 slot（WB LLM）、出图（WB `ImageGen`）、旁白（默认微软 edge-tts，免费/免登录）、渲染成片（包内自带 remotion 渲染工程，WB 自带的 node 即可跑）。**本 skill 自身无 MCP、无连接器**，全走脚本 + Bash 调用；解锁完整主题库时会用到 WorkBuddy 已内置的「连接 VibeKnow」MCP 能力（不是本 skill 自带，见「解锁完整主题库」）。
- **「选模板填空」而非自由绘图**：出片靠 `render-bundle/manifest.json` 里定义好的一批版式（layout）+ 主题（theme）组合，agent 按 slot schema 填文案、出对应背景图，不做自定义画面结构。
- 免费/完整门禁（单 bundle，双 manifest）：
  - **版式（layout）全部免费**：全部 **53 个**版式，无需登录即可任选。
  - **主题（theme）按 manifest 门禁**：免费默认仅 `serious-dark`（严肃深色）1 个；连接 VibeKnow（免费注册）后可解锁**完整 50 个主题**（含商务、科技、文艺、活泼等多种风格，每个主题都带 `desc`/`tags` 说明，方便按氛围挑选）。
  - 画幅：v1 固定 **1920×1080 横版**。
  - 字体：系统回退（暂无定制设计字体嵌入，见「已知后续项」）。
  - 用户想要免费主题外的风格 → 主动展示完整 50 主题的多样性（名称/描述/标签），引导其点 WorkBuddy「连接 VibeKnow」卡片解锁，登录过程免费、不影响免费流程继续可用。

## 目录结构
```
design-expert/                       = ${CODEBUDDY_PLUGIN_ROOT}
  .codebuddy-plugin/plugin.json       专家配置（agent 型；无 mcpServers）
  agents/design-artist.md             主理人 SOP
  avatars/design-artist.png
  render-bundle/
    manifest.json                     免费 manifest（版式/主题/slot schema 唯一真源；主题仅 serious-dark）
    manifest.full.json                完整 manifest（版式与 manifest.json 逐字节一致，主题全 50 个）——
                                       随插件一起分发，和 bundle 永远同版本，不靠登录下载
    bundle/                           预打包的 remotion webpack bundle（渲染直接吃这个，不现场编译；
                                       免费/完整共用同一份）
  predefine/                          bundle 的**源码**（.tsx + build-bundle.mjs）——仅用于重新生成 bundle，
                                       不随插件分发（打包/安装都会排除，体积/合规原因）
  skills/design/
    SKILL.md                          slot 填法 + 出片 SOP（agent 实际读的操作手册）
    scripts/
      run.mjs                         统一 CLI 入口：init / unlock / render / preview / tts / build-manifest
      check-slots.mjs                 掏钱前 slot 校验 CLI（本任务新增，见下）
      scene-schema.mjs                validateScenes 纯逻辑（check-slots 与 render-reel 共用同一套规则）
      build-manifest.mjs              JOBDIR 下 NN.* 配对成 scenes.json（图/音转 data:URI）
      render-reel.mjs                 导出成片 mp4 / 自包含预览 html
      tts-microsoft.mjs               默认旁白引擎（edge-tts）
      setup-env.mjs                   首次使用装运行依赖（渲染引擎 + chrome + edge-tts）
      test/                           node:test 单测（不随插件分发）
```

## 出图前的闸：`check-slots.mjs`
一次生成 = 一个 JOBDIR，内含 `NN.scene.json`（场景定义：layout/slots/themeId，`durationInFrames` 可选，由 `build-manifest` 后填）。出图（ImageGen）是较重的一步，出图前先本地校验一遍文案，避免无效重出：
```bash
node skills/design/scripts/check-slots.mjs <JOBDIR>
```
- 读 JOBDIR 下所有 `NN.scene.json`（按 NN 升序），读 `render-bundle/manifest.json`，逐屏校验 layout 是否存在、必填 slot 是否齐、文本是否超 `maxLength`、`textArray` 是否超 `maxItems`。
- **此时 `durationInFrames` 通常还没填**（它由后续 `build-manifest` 从显式值/音频时长/默认值里推导），也还没有 `NN.mp3`——`check-slots` 校验前会给每屏注入占位时长（`durationInFrames ?? 120`）再调 `validateScenes`，只管 slot 合规，不因「还没定时长」误拒。
- 合格 → 打印 `{"ok":true,"count":N}`，退出码 **0**。
- 不合格 → 打印 `{"ok":false,"problems":[...]}`（每条含屏号 `n` 和原因 `reason`），退出码 **4**。按提示改文案重跑，或换一个有对应 slot 的 layout；**不要跳过这一步直接出图**。

## 首次使用：装依赖
本专家以「纯源码」分发，运行依赖（`@remotion/renderer` 渲染引擎、chrome-headless-shell、edge-tts）在**首次使用时自动装进包内**：
```bash
node skills/design/scripts/run.mjs init
```
已装则秒过；chrome 下载失败不致命，首次渲染会自动补下。装进 `skills/design/scripts/node_modules`（不提交 git）。

## 解锁完整主题库

版式全部免费；主题默认只有 `serious-dark`。完整主题库（`manifest.full.json`，50 个主题）**早已随插件分发在本地**，和渲染包永远同版本——解锁不是下载，只是本地翻一个标记文件。走 WorkBuddy 原生 MCP 连接（不是设备码登录）：

```bash
# 0. 先查解锁状态（端上确定性检测，只看本地标记）——已 unlocked 就别再劝连接
node skills/design/scripts/run.mjs status
# → { "unlocked": false, "tier": "free", "themes": 1, "layouts": 53, "markerPath": "…" }

# 1. 用户点 WorkBuddy「连接 VibeKnow」卡片完成连接（免费注册，MCP OAuth，全程在 WorkBuddy 内完成）

# 2. 连接后调用 MCP 工具 verify_connection（门禁在连接本身，成功=已登录）

# 3. verify_connection 成功后【立即】本地翻标记解锁（不联网、不下载、幂等）
node skills/design/scripts/run.mjs unlock
# 成功输出：{ "status": "unlocked", "themes": 50 }
```

**要点**：
- **连接与解锁是一步内两个动作**：`verify_connection` 成功后必须立即 `unlock`，别漏——否则会"连了却没翻标记、还继续弹连接提示"（端上检测错位）。判断是否已解锁一律以 `status`（本地标记）为准，不凭对话记忆猜。
- 单 bundle + 双 manifest：`render-bundle/bundle` 免费/完整共用同一份；`manifest.json`（免费）与 `manifest.full.json`（完整）都随插件一起分发，版式逐字节一致，只 `themes` 字段不同——永远和 bundle 同版本，消除"下载版 vs 装机版对不上"的漂移风险。
- 连接仅为解锁完整主题库（拉新），免费版式（全部 53 个）全程**无需连接**、完全可用。
- 旁白默认走 edge-tts（免费），不受影响。
- 若用户指定了免费主题外的主题，`check-slots`/`render` 会拦下，报错文案会友好提示"该主题属完整主题库，连接 VibeKnow（免费）即可解锁 50 个主题"。
- **主动展示主题多样性**：免费流程中，agent 应主动把完整 50 主题的名称/氛围描述简要展示给用户（而非等用户问），用真实的风格多样性吸引其连接解锁，而不是干巴巴一句"可以解锁更多"。

## SOP 一句话
逐屏填 `NN.scene.json` → `check-slots.mjs` 本地校验（出图前的闸）→ ImageGen 出 `NN.bg.jpg` / `run.mjs tts` 配 `NN.mp3` → `run.mjs build-manifest` 生成 `scenes.json` → `run.mjs render` 出片。完整版见 `skills/design/SKILL.md`。

## 打包
```bash
bash pack.sh design-expert
```
- 打包前跑一致性自检（plugin.json / agent MD / avatar / skills 齐全性等），自检不过则跳过、不出包。
- 产物：`dist/vibeknow-design-video-v0.1.0.zip`（版本号取自 `.codebuddy-plugin/plugin.json`）。
- zip 内含：`render-bundle/bundle`（预打包渲染产物）+ `skills/design`（`scripts/*.mjs` + `SKILL.md`）+ `agents/` + `.codebuddy-plugin/` + `avatars/`。
- zip **不含**：`predefine/`（bundle 源码，仅用于重新构建 bundle）、`node_modules/`、`test/`、`*.tsx`（这些要么是生成 bundle 用的开发态源码，要么是依赖/测试，不随插件分发）。

## 已知后续项（留计划 3）
- **字体**：现走系统字体回退（非设计定制字体嵌入）；后续计划做 OSS 托管字体 + 按主题取用 + 按视频内容做字符子集裁剪，减小体积。
- **主题解锁**：v1 已切至「连接 VibeKnow 解锁完整主题库」（版式全免费 + 主题门禁 serious-dark→50，单 bundle + 双 manifest 随插件一起分发，解锁本地翻标记、不下载）。
- **渲染优化**：目前改一屏要整片重渲；后续考虑「只重渲改动的那一屏 + 拼接」。

## 测试
```bash
cd design-expert/skills/design/scripts
node --test test/*.test.mjs
```

## 致谢与许可

本专家为 VibeKnow 发布的第三方专家，agent prompt 与 `design` 技能为 VibeKnow 自有版权，视频渲染通过 VibeKnow 托管的 MCP 服务完成。渲染产物中打包了以下第三方开源组件：

- **Remotion**（视频渲染引擎，https://www.remotion.dev）：受 Remotion 官方许可条款约束（非标准宽松开源许可，商业使用请遵守其 License）。
- **React / React-DOM**（Meta Platforms, Inc.）：遵循 MIT License。
- **Mediabunny**（https://github.com/Vanilagy/mediabunny）：遵循 Mozilla Public License 2.0（MPL-2.0）。

各许可全文见 `license/` 目录（VibeKnow 版权声明见 `license/vibeknow-PROPRIETARY.LICENSE`）。字体当前走系统回退，暂无嵌入字体。
