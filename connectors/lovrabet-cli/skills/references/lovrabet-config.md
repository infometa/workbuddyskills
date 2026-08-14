# `.lovrabet.json` 配置参考

`.lovrabet.json` 现在只承载**用户意图配置**，不再承载平台应用目录。

这意味着：
- `accessKey` / `env` / `format` / `riskLevel` / `defaultApp` 等仍然放在 `.lovrabet.json`
- 当前 AK 在平台上可见的应用列表，放在 `~/.lovrabet/cache/.../my-apps.json`
- 常规使用不需要先创建本地配置文件；登录后可以直接 `app list` 并通过 `--app` / `--appcode` 操作

兼容旧名：`.lovrabetrc`（优先级 `.lovrabet.json` > `.lovrabetrc`）。

## 单应用模式

```json
{
  "appcode": "app-xxxxxxxx",
  "env": "daily",
  "accessKey": "<ACCESS_KEY>"
}
```

## 默认应用模式

```json
{
  "accessKey": "<ACCESS_KEY>",
  "env": "daily",
  "defaultApp": "crm"
}
```

`defaultApp` 现在只表示“没有更明确 app 线索时的默认候选远端应用名”。真正的应用目录来自 cache / remote，不再在本地维护 `apps.*` overrides。

## app cache

平台应用列表缓存路径：

```text
~/.lovrabet/cache/<env>/<ak-fingerprint>/my-apps.json
```

这个 cache 由以下命令维护：
- `lovrabet app list`
- `lovrabet app list --no-cache`
- `lovrabet app pull`

## 顶层字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `appcode` | string | — | 兼容单应用模式，直接指定 appcode |
| `env` | string | `production` | 环境：`production` / `development` / `daily` |
| `accessKey` | string | — | User Access Key（client-ak） |
| `format` | string | — | 默认输出格式：`json` / `pretty` / `compress` |
| `pageSize` | number | — | 默认分页大小 |
| `riskLevel` | string | `write` | 允许执行的最高风险等级 |
| `defaultApp` | string | — | 默认候选应用名称 |
| `inherit` | boolean | true | 当前目录配置是否继承全局配置 |

## 解析优先级

```
CLI flag (--appcode, --env, --format, --app ...)
  ↓
环境变量 (LOVRABET_APPCODE, LOVRABET_ENV ...)
  ↓
当前目录 .lovrabet.json（兼容本地配置）
  ↓
全局级 ~/.lovrabet.json
  ↓
内置默认值
```

## 关于 `defaultApp`

`defaultApp` 仍然是本地配置字段，但它现在只表示默认候选的远端应用名称。

所以：
- 通过 `workspace init/use --app <name>` 建立或修改命名绑定时会写入 `defaultApp`
- 运行时通过 cache 解析对应 `appcode`
- Agent 场景中，`defaultApp` 是第一个验证候选；用户未指定 app 时先查默认候选的数据集，验证不成立再扩大到应用列表

## 环境变量

| 环境变量 | 对应字段 |
|----------|----------|
| `LOVRABET_APPCODE` | `appcode` |
| `LOVRABET_ENV` | `env` |
| `LOVRABET_ACCESS_KEY` | `accessKey` |
| `LOVRABET_FORMAT` | `format` |
| `LOVRABET_PAGE_SIZE` | `pageSize` |
| `LOVRABET_VERBOSE` | verbose |
| `LOVRABET_APP` | 当前应用名 |

## 查找与合并

| 作用域 | 查找目录 | 文件名优先级 |
|--------|---------|------------|
| 当前目录 | `process.cwd()` | `.lovrabet.json` > `.lovrabetrc` |
| 全局级 | `~` | 同上 |

合并策略：
- 标量字段：当前目录配置覆盖全局级
- `defaultApp`：当前目录显式声明 > 全局 `defaultApp`

## 示例

### 全局 AK + 默认应用

```json
{
  "accessKey": "<ACCESS_KEY>",
  "env": "daily",
  "defaultApp": "crm"
}
```

### 当前目录默认候选（兼容场景）

```json
{
  "defaultApp": "crm"
}
```
