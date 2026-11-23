# Beluga MCP（生产）连接器包

连接 Beluga 生产环境 MCP 网关:`https://beluga-server-cn.heytapmobi.com/beluga-mcp/gateway`

## 包结构

```
beluga-mcp-prod/
├── connector-meta.json     # 连接器元数据(名称/描述/示例指令)
├── mcp.json                # MCP Server 配置(streamableHttp)
├── icon.svg                # 连接器图标
├── connect.py              # 备用接入脚本(仅调试/排障用，非推荐路径)
├── README.md               # 本说明
└── skills/beluga/SKILL.md  # Agent 使用说明(接入方式 + 工具清单 + 调用约定)
```

> 说明：`token_<name>.json` / `client_<name>.json` **不在包内**，它们是用户在
> 本机运行 `connect.py` 后自动生成的令牌缓存（含 refresh_token），属于账号凭据，
> 严禁随包分发。

## 用户接入（推荐：平台托管授权）

本连接器已声明 `auth_mode: server-side`，凭据由 WorkBuddy 平台托管：

```text
WorkBuddy「插件 → MCP 服务器」→ 添加/搜索「心力球」→ 点击「信任/连接」
→ 自动拉起原生 OAuth 授权页 → 登录 Beluga 账号并授权 → 完成
```

令牌由平台自动携带并静默刷新，手机端与桌面端行为一致，无需本机配置文件。

> 兼容性：使用新字段需 WorkBuddy ≥ 4.22.12（见 `minWorkbuddyVersion`）。

## 备用方案 connect.py（仅调试用）

早期因 Beluga OAuth 服务端仅接受 http/https 回调，曾推荐使用 connect.py
把 Bearer Token 写入本机 `~/.workbuddy/mcp.json`。该方案**仅在本地桌面端有效、
无法在手机端复现授权**，现已降级为调试/排障备用，不再作为常规接入方式。

```bash
python connect.py --check    # 验证现有令牌并列出可用工具
python connect.py --refresh  # access_token 过期后静默续期（依赖 client_*.json）
python connect.py            # 手动完整授权（标准 MCP OAuth 2.1，PKCE + loopback）
```

> ⚠️ 注意：运行 connect.py 会在本机 `~/.workbuddy/mcp.json` 写入
> `headers.Authorization`，可能与平台托管授权并存。如已在桌面端用「信任」
> 完成托管授权，则无需再运行 connect.py。

## 关于 connect.py（2026-10-09 更新）

**服务端限制已解除**：经实测，Beluga OAuth 的动态客户端注册（RFC 7591）
现已接受 WorkBuddy 原生自定义协议回调
`workbuddy://workbuddy/mcp/connector%3A<source>/oauth/callback`
（HTTP 201 注册成功并回显 redirect_uris），授权端点同样接受，
且对未注册回调仍严格校验（400 拦截）。

**因此用户现在可直接在 WorkBuddy「插件 → MCP 服务器」添加本连接器，
走原生授权（点「信任」）即可完成接入，无需运行 connect.py。**

connect.py 对其他有同类限制的 MCP 网关仍可复用（通过 `--url` / `--name` 参数）。

## 变更记录

### 1.0.6

- 与 1.0.5 内容一致，仅版本号递增（用于平台要求“版本号必须大于当前最新版本”时）。

### 1.0.5

- **修复打包方式导致的审核 A1「压缩包安全解压」不通过**：改用规范化打包器重新发布，
  包内目录条目同时带上 `/` 结尾、Unix 目录权限位（`0o40755`）与 MS-DOS 目录属性位。
  此前用系统压缩工具产出的包目录条目权限位为 `0`，审核端严格解压时会把
  `skills/beluga` 落成普通文件，导致 `[Errno 20] Not a directory`。
- 包内顶层目录由 `beluga-prod/` 统一为 `beluga-mcp-prod/`，与 `connector-meta.json`
  的 `source` 字段对齐。
- 补充「随口记」类与「连通性检查」类中英文示例指令，使详情页能力覆盖更完整。
- README 的包结构说明更正：`token_*.json` / `client_*.json` 为本机生成、不入包。

### 1.0.4

- 新增 `auth_mode: "server-side"`：凭据声明为平台托管，授权链路可被
  WorkBuddy 各端（含手机端）复现，修复连接器未在手机端连接器市场出现的问题。
- 新增 `minWorkbuddyVersion: "4.22.12"`（使用新字段时必填）。
- README 接入方式调整：平台托管授权为推荐路径，connect.py 降级为调试备用。

### 1.0.3

- 修正描述文案，补充中英文示例指令。

## 安全说明

- `token_*.json` 含 access_token 与 refresh_token,等同账号凭据,
  请勿提交到版本库或随包分发。
- 打包发布前请删除本机生成的 `token_*.json` 与 `client_*.json`。
