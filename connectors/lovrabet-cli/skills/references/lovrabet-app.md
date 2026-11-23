# app — 应用管理

`app` 子命令负责应用目录发现和本地缓存刷新：

- **应用目录发现**：通过远端接口和本地 cache 获取当前 AK 可运行态访问的应用列表
- **缓存刷新**：在需要显式更新本地应用目录时使用 `app pull`

> **核心边界**：平台应用列表不再写入 `.lovrabet.json`。`.lovrabet.json` 只保存用户配置；应用目录缓存位于 `~/.lovrabet/cache/...`。
>
> 给当前工作目录绑定默认应用时，使用 `lovrabet workspace init/use`；命令选择取决于当前目录是否已经存在应用绑定。

## app list — 列出当前 AK 可运行态访问应用

```bash
lovrabet app list
lovrabet app list --local
lovrabet app list --no-cache
lovrabet app list --include-unpublished
```

| Flag | 说明 |
|------|------|
| `--local` | 只读本地 cache，不打远端 |
| `--no-cache` | 强制打远端并刷新 cache |
| `--include-unpublished` | 排查用：包含未发布应用 |

**行为**：
- 默认：远端优先，成功后刷新 cache，只展示已发布应用
- 远端失败且本地有 cache：回退到 cache
- `--local`：只读 cache
- `--include-unpublished`：仅用于确认未发布应用是否在远端目录或 cache 中；不要把未发布应用作为 `dataset` / `data` / `sql` / `bff` 目标
- 输出中的 `meta.source` 为 `remote` / `cache` / `mock`

**缓存路径**：

```text
~/.lovrabet/cache/<env>/<ak-fingerprint>/my-apps.json
```

**输出**：
- `data.items`：应用列表；默认只包含已发布、可运行态访问的应用
- `data.items[].enableI18n`：应用是否开启国际化；旧缓存或远端缺失该字段时为 `null`
- `data.items[].languages`：应用支持的语种列表，来自平台真实 `i18nInfo.langs`
- `data.items[].i18nInfo`：平台返回的应用国际化配置
- `data.items[].locale`：本地应用本地化设置覆盖，可能为 `null`；不是 CLI 语言，也不代表平台支持语种
- `data.meta.env`：实际环境标识，用于排障；最终服务地址以 `doctor` 为准
- `data.meta.source`：来源
- `data.meta.fetchedAt`：最近同步时间
- `data.meta.cachePath`：cache 文件路径
- `data.meta.defaultApp` / `defaultAppSource`：当前默认候选应用决议结果
- `data.meta.remoteTotal`：远端或 cache 原始应用数量
- `data.meta.hiddenUnpublishedCount`：默认列表中因未发布被隐藏的应用数量
- `data.meta.includeUnpublished`：本次是否包含未发布应用

## 何时使用 app list

应用选择统一遵循[默认应用与应用发现](../guides/app-resolution.md)：未指定目标时先查默认 AppCode（顶层 `appcode` 或 `defaultApp` 解析结果）；仅在成功查询无合理匹配、核对筛选条件且用户未限定范围后，才扩大只读发现。认证、权限或连接错误不触发跨应用重试。

没有默认应用、用户明确要求跨应用查找或查看可访问应用目录时，可直接 `app list`。已有明确目标或尚未查询默认应用时，不因用户只说业务需求就要求先选应用。

目录返回的名称与描述只用于筛选候选，仍需在目标应用内验证数据集或可信业务能力。数据集名称用 `--name`，物理表名用 `--table-name`，详见[数据集发现](dataset-discovery-workflow.md)。

`--app` / `--appcode` 只对本次命令生效。临时选择其他应用后，后续每条 `detail`、`data` 或执行命令都必须显式携带该目标；资源标识必须与发现它的 AppCode 配对，不能依靠上一条命令改变默认值。

## app pull — 手动刷新本地 app cache

```bash
lovrabet app pull
lovrabet app pull --local
lovrabet app pull --no-cache
```

| Flag | 说明 |
|------|------|
| `--local` | 只读 cache，不请求远端 |
| `--no-cache` | 强制打远端并刷新 cache |

**注意**：
- 平时优先用 `lovrabet app list`；只有你明确想单独刷新缓存时才用 `app pull`
- `app pull` **不再**把远端应用列表写入 `.lovrabet.json`
- 它的职责只是“刷新本地 cache”

详见 [lovrabet-workspace.md](lovrabet-workspace.md)。

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-config.md](lovrabet-config.md)
