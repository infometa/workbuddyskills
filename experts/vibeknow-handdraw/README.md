# 手绘动画师 · WorkBuddy 专家

把主题/文档变成「像手一样逐步画出、最后定格成清晰画面」的手绘动画短片。Agent 型专家，内置 51 种手绘风格。

## 能力边界
- **本地(WorkBuddy)**：内容(讲稿/分镜，WB LLM)、出图(WB `ImageGen` + 包内 51 风格 prompt)、**手绘渲染 + 导出**(包内自带 remotion 渲染工程，WB 自带的 node 即可跑)。
- **远端(经 go-vibeknow 托管，需登录)**：`handdraw`(rmbg + 矢量化 + 主体优先重排) 与 `tts`(**可选**高级音色 —— 旁白默认走本地免费 edge-tts,不经服务端)。由**脚本经 Bash 调用**接入——**无 MCP、无连接器**。

## 自洽包结构
```
vibeknow-handdraw/                 = ${CODEBUDDY_PLUGIN_ROOT}
  .codebuddy-plugin/plugin.json     专家配置(agent 型;无 mcpServers)
  agents/handdraw-artist.md         主理人 SOP
  avatars/handdraw-artist.png
  mcp/                              vibeknow 客户端函数库(零外部依赖,Node 内置 fetch)
    server.mjs                      callHanddraw / callSynthesize / loadStyles / token
    auth-login.mjs                  设备码登录(device code, RFC 8628)
    token-path.mjs
  render/                           自带 remotion 渲染工程
    HandDrawReel.tsx  layout/       多幕成片 + 绘制/落定/运镜
    package.json  ensure-chrome-cn.mjs   依赖 + chromium 装时拉取(国内镜像优先)
    public/hdprev/sample.*
  skills/handdraw/
    SKILL.md  references/styles.json      51 风格目录 + visual-rules
    scripts/
      run.mjs            统一 CLI(init / login / login-status / synthesize / list-styles)
      handdraw-page.mjs  对一张图矢量化,派生同名 NN.vec.json
      check-images.mjs   掏钱绘制前的出图尺寸预检(CLI + 纯逻辑校验)
      tts-microsoft.mjs  默认旁白引擎(edge-tts,免费/免登录)
      build-gen-prompt.mjs  出图 prompt(锁画风尾巴)
      workspace.mjs      建 job 目录     build-manifest.mjs  按 NN 配对 scenes.json
      render-reel.mjs    多幕成片        setup-env.mjs       装依赖(render + chrome)
```

## 关键设计
- **无 MCP，脚本 + Bash**：手绘/旁白/登录全走 `run.mjs`、`handdraw-page.mjs`，agent 在对话里用 Bash 调。彻底避开 WB 对自定义 MCP 连接器的不稳(参考美团生活助手同款范式)。
- **`mcp/` 零依赖**：客户端函数只用 Node 内置 `fetch`/`FormData`/`fs`，无需 `npm install`。
- **装时拉取**：只有 `render/node_modules` 与 remotion 的 headless chromium(~150MB)由 `run.mjs init` 拉到包内(chrome 走国内镜像 npmmirror + 官方兜底)。git 只存源码。
- **零外部/个人路径**：脚本用 `import.meta.url` 推包内路径；地址由环境变量注入，包内不写死地址/密钥。
- **渲染写工作区**：`render-reel.mjs` 用 `--public-dir` 把数据写在输出同级，remotion 只读包内工程，不写工作区外，无需沙箱授权。
- **落盘约定**：一次生成 = 一个 job 目录，页内 `NN.png`/`NN.vec.json`/`NN.mp3` 同号绑定，`build-manifest` 按号配对，杜绝图/数据错位。

## 本地安装
```bash
# 1) 完全退出 WorkBuddy(Cmd+Q)
# 2) 先在 WorkBuddy 里创建过任意一个专家(生成 my-experts 市场脚手架)
# 3) 在本仓根目录:
bash install-local.sh          # 复制源码 + 装 render/chrome 依赖 + 注册 + 启用
# 4) 打开 WorkBuddy →「我的专家」→『手绘动画师』
```
> 打包提交用 `bash pack.sh`(纯源码 zip，自检 + 排除依赖/生成物)。首次使用时专家自己 `run.mjs init` 拉齐依赖。

## 环境配置（远端地址 / 登录）
远端能力经 go-vibeknow 网关（按首段路由 /vibeknow、/account）。**源码里默认写死生产网关域名**。

### 在 WorkBuddy 里做本地联调 → 用 `install-local.sh --local`
⚠️ **WorkBuddy 无法给 agent 注入环境变量**，所以下表的 env 覆盖在 WB 内**不生效**。要让 WB 里的专家打到本地后端，用安装脚本把地址**烧进「已安装副本」**（仓库源码不动，`pack.sh` 发布不受影响）：

```bash
bash install-local.sh --local        # → vibeknow 127.0.0.1:28080 / account 127.0.0.1:20001
                                     #   token 也切到 token.local.json，不会覆盖你的生产登录态
bash install-local.sh                # 重装即恢复生产（https://vibeknow.com）
bash install-local.sh --vibeknow-base <URL> [--account-base <URL>]   # 自定义（如测试环境）
```
装完脚本会打印**当前已安装副本实际指向的后端**，避免「以为在测本地、其实打到生产扣了积分」。

### 在终端里直接跑脚本 → env 覆盖仍可用
| env | 默认（生产网关） | 本地覆盖（无反代，直连端口） |
|---|---|---|
| `VIBEKNOW_BASE` | `https://vibeknow.com/vibeknow/v1` | `http://127.0.0.1:28080/vibeknow/v1` |
| `ACCOUNT_BASE` | `https://vibeknow.com/account/v1` | `http://127.0.0.1:20001/account/v1` |
| `WB_TOKEN` | —（缺省读 token 文件） | 直接塞 token，跳过登录 |
| `VOICE_ID` | 微软默认音色 `zh-CN-XiaoxiaoNeural` | 同 |
| `WB_TOKEN_FILE` | token 存储路径（缺省 `~/.workbuddy/vibeknow-handdraw/token.json`） | 同 |


首次使用登录(设备码，浏览器输验证码，agent 在对话里代跑)：
```bash
node skills/handdraw/scripts/run.mjs login          # → 授权链接 + 验证码
node skills/handdraw/scripts/run.mjs login-status   # → success/pending/error
```

## 试一条
> 用水墨写意画一个「溪山访茶」的手绘动画。

预期：拆单页 → `ImageGen` 出图 → `check-images.mjs` 尺寸预检 → 逐页 `handdraw-page.mjs` 矢量化 → `run.mjs synthesize` 旁白 → `render-reel.mjs` 包内 remotion 渲染 → 给出成片 mp4 + job 目录路径。

## 测试
```bash
cd handdraw-expert
node --test mcp/test/*.test.mjs skills/handdraw/scripts/test/*.test.mjs   # 客户端函数 + run/脚本单测
```
