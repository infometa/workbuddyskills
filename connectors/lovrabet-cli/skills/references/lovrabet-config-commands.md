# config — 配置管理

读写 `.lovrabet.json` 中的用户意图配置。配置文件完整字段说明见 [lovrabet-config.md](lovrabet-config.md)。

> **边界**：平台应用目录不在 `.lovrabet.json`。应用目录缓存位于 `~/.lovrabet/cache/...`，平时由 `app list` 驱动更新；`app pull` 只是手动刷新入口。

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
| `<key>` | string | **必填** — 配置键名（如 `appcode`、`env`、`riskLevel`） |

**示例**：

```bash
lovrabet config get appcode
# 输出: app-xxxxxxxx

lovrabet config get env
# 输出: daily
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
| `--app <name>` | string | — | 写入指定应用 profile 内 |

**风险等级**：`write`

> **作用域规则**：`config set` 是高级本地配置维护命令。默认写当前目录的 `.lovrabet.json`；如果当前目录没有本地配置文件且未传 `--global`，CLI **拒绝执行**，避免静默写入全局。常规使用优先通过 `auth login`、`app list`、显式 `--app` / `--appcode` 完成操作。

**示例**：

```bash
# 写入当前目录配置（默认；须在含 .lovrabet.json 的目录下执行）
lovrabet config set env daily
lovrabet config set riskLevel write

# 写入全局配置（任意目录可用，需用户明确意图）
lovrabet config set env daily --global

# 写入指定应用配置
lovrabet config set riskLevel write --app order

# 配置 User AK（client-ak）
lovrabet config set accessKey <ACCESS_KEY>
```

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
