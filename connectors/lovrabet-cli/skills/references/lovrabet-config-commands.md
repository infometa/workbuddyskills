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

官方 Region 与企业 Domain 是互斥的初始化入口，不能同时传入。企业服务地址示例：

```bash
lovrabet config init --runtime-domain https://runtime.customer.example.com
```

- `--region` 接受当前启用的 `cn` / `id` / `global`；默认 `cn` 不保存冗余字段。
- 提供企业 Domain 或企业清单会清除全局 `region` 和旧 Domain/routing，再保存本次企业配置；无需先选择地区。
- 选择 `--region` 会清除全局旧 Domain/routing，并使用地区默认地址。
- AccessKey、env、format、locale 和应用绑定保持不变。

### 可选 Domain 覆盖值

支持 `userDomain`、`apiDomain`、`runtimeDomain`、`skillDomain`、`kbServiceDomain` 和 `harnessDomain`，均可省略。没有配置的字段使用当前地区及环境的内置地址，独立部署也遵循同一规则。Personal KB 管理和搜索使用 `kbServiceDomain`，定时接口使用 `harnessDomain`。

版本化企业路由清单可只包含需要覆盖的字段，`domains` 也可以为空：

```json
{
  "protocol": "lovrabet-routing/v1",
  "kind": "enterprise",
  "domains": {
    "runtimeDomain": "https://runtime.customer.example.com"
  }
}
```

其他工具可能要求完整清单中的其他字段；Lovrabet CLI 仅校验并保存自己使用的六个 Domain，忽略其他消费者的 Domain、CDN 或数据库字段。各值可写为 HTTPS 字符串，或带 `lovrabet-cli` / `default` 的对象；当前消费者专属值优先；该值未提供或为 null 时使用 `default`。字段省略时使用内置默认值；字段已提供但最终没有可用的消费者地址，或地址为空、格式错误时会报错。

支持扁平 JSON 配置。也可使用 `--user-domain`、`--api-domain`、`--runtime-domain`、`--skill-domain`、`--kb-service-domain`、`--harness-domain`。显式 flag 覆盖扁平文件的同名字段；版本化企业清单不能叠加单独的 Domain flags，也不能搭配 `--region`。

企业清单保存为 `routing` 对象。初始化只修改全局配置，项目配置仍参与运行时解析，具体顺序见 [配置解析优先级](lovrabet-config.md#解析优先级)。初始化后可用 `lovrabet doctor` 核对实际生效的 Domain。

通过 `config init` 或企业清单提供的地址必须是不含凭据、路径、查询参数或片段的 HTTPS origin。只有所选地区没有该服务内置地址且未配置覆盖值时，对应操作才要求提供地址；请求失败不会切换服务地址。`--kb-service-url` 仅覆盖单次搜索，不写入配置。

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
