# config — 配置管理

读写 `.lovrabet.json` 中的用户意图配置。配置文件完整字段说明见 [lovrabet-config.md](lovrabet-config.md)。

> **边界**：平台应用目录不在 `.lovrabet.json`。应用目录缓存位于 `~/.lovrabet/cache/...`，平时由 `app list` 驱动更新；`app pull` 只是手动刷新入口。

## config init — 初始化连接配置

固定写入全局配置 `~/.lovrabet.json`，不需要额外的作用域参数。它只配置连接路由，不登录、不保存 AccessKey，也不建立当前目录的应用绑定。

交互模式用方向键选择 `Mainland China (cn)`、`Indonesia (id)` 或 `Global (global)`。非交互且未传 region/Domain 时默认 `cn`。自动化示例：

```bash
lovrabet config init --region id
lovrabet config init --domain-config ./lovrabet-domains.json
```

官方节点与独立部署 Domain 互斥：不能同时传 `--region` 和任一 Domain 输入。

### 官方节点模式

- `--region` 接受当前生成快照启用的 `cn` / `id` / `global`
- 选择 `cn` 时省略冗余的 `region` 字段，以默认值保持向前兼容；选择 `id` 时写入 `"region": "id"`
- 切回官方节点会删除全局配置里的显式 Domain，以及兼容读取的旧 Domain 字段

### 独立部署模式

推荐使用两个 CLI 共用的版本化企业路由清单：

```json
{
  "protocol": "lovrabet-routing/v1",
  "kind": "enterprise",
  "cdn": {
    "libraries": "https://cdnjs.cloudflare.com/ajax/libs",
    "lovrabet": "https://g.lovrabet.com"
  },
  "domains": {
    "userDomain": "https://user.customer.example.com",
    "apiDomain": "https://api.customer.example.com",
    "runtimeDomain": "https://runtime.customer.example.com",
    "skillDomain": "https://skills.customer.example.com",
    "kbServiceDomain": "https://kb.customer.example.com",
    "kbDomain": "https://kb-admin.customer.example.com",
    "appDomain": "https://app.customer.example.com"
  }
}
```

同一份清单可以包含其他消费者所需的 Domain、CDN 或数据库访问提示。Lovrabet CLI 校验并保存 `userDomain`、`apiDomain`、`runtimeDomain`、`skillDomain` 与可选的 `kbServiceDomain`；`kbDomain` 和其余消费者字段会被忽略。Personal KB 管理使用 `runtimeDomain`，搜索使用 `kbServiceDomain`。Domain 可写成共用 HTTPS 字符串；确有差异时写成带 `default` 或当前消费者键的对象。对象优先使用 `lovrabet-cli`，其次使用 `default`，两者都没有时命令报错。清单不能叠加单独的 Domain flags。旧扁平 JSON 继续兼容，并允许上述五个字段，且至少提供一个：

```json
{
  "userDomain": "https://user.customer.example.com",
  "apiDomain": "https://api.customer.example.com",
  "runtimeDomain": "https://runtime.customer.example.com",
  "skillDomain": "https://skills.customer.example.com"
}
```

也可以用 `--user-domain`、`--api-domain`、`--runtime-domain`、`--skill-domain`、`--kb-service-domain` 逐项传入；显式 flag 只覆盖旧扁平文件里的同名字段。所有值必须是无账号、路径、query 和 fragment 的 HTTPS origin。

新版企业清单会保存为带协议标识的 `routing` 对象，并整体优先于旧顶层 Domain；旧扁平配置继续保持既有回退行为。

进入旧扁平独立部署模式会删除全局 `region` 和旧 Domain 字段，再写入本次提供的 Domain。企业部署需要所有请求进入私有服务时，应提供所需 Domain；Personal KB 管理使用 `runtimeDomain`，知识搜索缺少 `kbServiceDomain` 时失败关闭。`--kb-service-url` 仅覆盖单次搜索且不写入配置。

两种模式都保留 AccessKey、env、format、locale、应用绑定等其他全局配置。当前目录 `.lovrabet.json` 的旧扁平同名字段仍会覆盖全局旧扁平配置；初始化后用 `lovrabet doctor` 核对最终生效的国家/地区和 Domain。

## config list — 查看完整配置

以 JSON 格式输出当前合并后的完整配置。

```bash
lovrabet config list
# 或
lovrabet config          # list 是默认子命令
```

无需参数。输出包含所有配置项的合并结果（当前目录 + 全局级）。

## config get — 读取配置项

读取单个配置项的值（读取合并后的结果）。

```bash
lovrabet config get <key>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `<key>` | string | **必填** — 配置键名（如 `appcode`、`format`、`riskLevel`） |

**示例**：

```bash
lovrabet config get appcode
# 输出: app-xxxxxxxx

lovrabet config get format
# 输出: compress
```

## config set — 写入配置项

写入配置项到 `.lovrabet.json`。

```bash
lovrabet config set <key> <value>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `<key>` | string | **必填** — 配置键名 |
| `<value>` | string | **必填** — 配置值 |

| Flag | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--global` | boolean | false | 写入全局配置 `~/.lovrabet.json` |

**风险等级**：`write`

> **作用域规则**：`config set` 是高级本地配置维护命令。默认写当前目录的 `.lovrabet.json`；如果当前目录没有本地配置文件且未传 `--global`，CLI **拒绝执行**，避免静默写入全局。常规使用优先通过 `auth login`、`app list`、显式 `--app` / `--appcode` 完成操作。

**示例**：

```bash
# 写入当前目录配置（默认；须在含 .lovrabet.json 的目录下执行）
lovrabet config set format compress

# 写入全局配置（任意目录可用，需用户明确意图）
lovrabet config set format compress --global

# 配置 User AK（client-ak）
lovrabet config set accessKey <ACCESS_KEY>
```

> **安全边界**：`riskLevel` 是 CLI 保护字段，`config set riskLevel ...` 与 `config delete riskLevel` 均会被拒绝，避免 Agent 或脚本静默提高风险权限。只有用户可以直接编辑配置文件修改该字段。

## config delete — 删除配置项

从 `.lovrabet.json` 中移除一个配置项。

```bash
lovrabet config delete <key>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `<key>` | string | **必填** — 要删除的配置键名 |

| Flag | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--global` | boolean | false | 操作全局配置 |
| `--app <name>` | string | — | 从指定应用 profile 内删除 |

**风险等级**：`write`

> **作用域规则**：与 `config set` 一致。无本地配置文件且未传 `--global` 时拒绝执行。

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-config.md](lovrabet-config.md) — 完整配置字段参考
