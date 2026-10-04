# global（认证与全局参数）

## 认证

### 首次登录

```bash
# 浏览器登录（默认，自动打开浏览器扫码）
yzj-cli auth login

# 设备码登录（无浏览器 / CI / SSH 环境使用）
yzj-cli auth login --device
```

**选择登录方式：**
- 本地桌面环境（macOS / Windows / Linux 桌面）→ `auth login`（默认，自动打开浏览器）
- SSH / CI / 远程服务器 / 容器 / 无浏览器环境 → `auth login --device`
- 不确定时 → 优先 `auth login`，若失败或用户反馈无法打开浏览器，再改用 `--device`

### 多 Profile 支持

```bash
yzj-cli --profile work auth login
yzj-cli --profile work calendar event list --start 2026-05-06 --end 2026-05-06
```

- `--profile <name>` 指定独立配置空间，默认使用 `default` profile
- 每个 profile 有独立的凭证和配置，互不干扰

### 凭据存储

- **app_secret** 存储在 OS keychain（macOS Keychain / Windows Credential Manager / Linux encrypted storage）
- **config.json** 只保存非敏感引用，不含明文密钥
- 配置文件位置：`~/.yzj-cli/config.json`

## 全局参数

| 参数 | 说明 |
|------|------|
| `--debug` | 启用调试输出（tracing DEBUG 级别，stderr） |
| `--verbose` | 启用详细输出（tracing INFO 级别，stderr） |
| `--profile <name>` | 切换配置与凭证隔离空间，默认 `default` |
| `--endpoint <url>` | 覆盖 API 端点（HTTPS only） |

## 输出格式

成功时 stdout 输出 JSON 信封，exit 0：

```json
{
  "success": true,
  "identity": "user",
  "data": { "list": [ ... ], "count": 10, "more": true }
}
```

- `data`：业务数据本体——get 类为对象；list 类为 `{list, ...伴随字段}`（`list` 是记录数组，每项结构见各产品文档；伴随字段与 `list` 平级）；空回执命令整体省略
- 伴随字段（list 类，与 `list` 平级放 `data` 内）：`count`（本次返回条数）、`more`（是否还有下一页）、`total`（关键词总命中数）、`pageToken`（token 翻页游标）、`lastUpdateTime`（增量变更游标）等，具体见各产品文档
- `identity`：当前使用的身份（`user` / `app`）
- 失败时 stdout 为空，stderr 输出**单行**错误 JSON：`{"success": false, "error": {"type", "subtype", "message", "hint", "code"}}`，退出码按 `error.type` 派生（见下方「进程退出码」）

## 输出过滤（--jq / -q）

**非全局参数**，仅在返回 JSON 的读命令上可用：doc（workspace list/get、doc list/get/recent/search、block list）、sheet（get、table get、record list）、calendar（event list/get/participants、room find）、contact（user search/get）、im（message list、group recent）。写命令（create/update/delete/send 等）传 `--jq` 会报 unknown argument。

`--jq` 以整个成功信封为根：get 类业务数据在 `.data` 下，list 类在 `.data.list` 下，伴随字段在 `.data` 下与 `list` 平级。

```bash
# 提取列表中每个对象的 id（每行一个）
yzj-cli doc workspace list --jq '.data.list[].id'

# 提取单个字段（字符串原样输出，不带引号）
yzj-cli doc get --id <DOC_ID> --jq '.data.title'

# 统计本次返回条数
yzj-cli im group recent --jq '.data.list | length'

# 取伴随字段
yzj-cli doc search --keyword "..." --jq '.data.total'
```

行为约定：

- 结果为字符串时输出裸文本（无引号），非字符串为合法 JSON；多个结果每行一个
- 表达式语法错误 → exit 2，在发起任何 API 请求前拦截（fail-fast）
- 求值失败 → exit 5，stdout 不输出部分结果
- 不确定 JSON 结构时先去掉 `--jq` 查看原始输出

## 常见错误码

| errorCode | 含义 | 解决方案 |
|-----------|------|---------|
| `10000400` | accessToken 无效或过期 | 重新运行 `yzj-cli auth login` |
| `43001` | 无权限访问该资源 | 检查应用是否有对应 API 权限 |
| `93001` | 凭据无效 | 确认 appId/appSecret 正确后重新登录 |

## 进程退出码

| exit code | 含义 | agent 下一步 |
|-----------|------|-------------|
| `0` | 成功 | 读 stdout 信封的 `data` |
| `1` | API 业务错误（`error.type=api`） | 读 stderr 信封的 `message` / `hint` 判断是否可修，不盲目重试 |
| `2` | 参数校验或 `--jq` 表达式解析错误（fail-fast，未发起请求） | 修正命令行后重试 |
| `3` | 认证 / 授权 / 配置错误（`authentication` / `authorization` / `config`） | 按提示重新登录或修配置 |
| `4` | 网络错误（连接失败、超时、HTTP 4xx/5xx） | 检查网络后可重试 |
| `5` | 内部错误（含 `--jq` 求值失败） | 上报，不要重试 |
| `10` | 需 `--yes` 确认（仅非交互模式；stderr 带 `confirmation_required` 标识，未发起任何请求。交互终端会改为提问，拒绝同样 exit 10） | 确认用户意图后追加 `--yes` 重试；用户已明确要求且目标无歧义时可直接追加，无需二次询问 |

## 安全规则

- **禁止输出密钥**（appSecret、accessToken）到终端明文
- **写入/删除操作前必须确认用户意图**
- **HTTPS-only** — 所有请求必须使用 HTTPS，HTTP 会被拒绝
- **可信主机** — 凭据只发送到 `*.yunzhijia.com` 和配置的端点域名
