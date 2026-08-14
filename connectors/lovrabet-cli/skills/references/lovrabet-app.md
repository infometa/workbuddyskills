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
lovrabet app list --env daily
lovrabet app list --include-unpublished
```

| Flag | 说明 |
|------|------|
| `--env <env>` | 指定环境，默认当前环境 |
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
- `data.items[].locale`：CLI 本地兼容配置字段，不代表应用支持语种，可能为 `null`
- `data.meta.env`：环境
- `data.meta.source`：来源
- `data.meta.fetchedAt`：最近同步时间
- `data.meta.cachePath`：cache 文件路径
- `data.meta.defaultApp` / `defaultAppSource`：当前默认候选应用决议结果
- `data.meta.remoteTotal`：远端或 cache 原始应用数量
- `data.meta.hiddenUnpublishedCount`：默认列表中因未发布被隐藏的应用数量
- `data.meta.includeUnpublished`：本次是否包含未发布应用

## 何时应该先跑 app list

应该先跑 `app list` 的场景：

- 用户只说了业务域，没有给 app 线索
- 当前没有显式 `--appcode` / `--app`，且需求包含业务域、对象名或数据集线索
- 你怀疑需求可能落在多个 app 中
- 你需要先确认当前 AK 在该环境下有哪些可运行态访问的应用
- 已经在 `defaultApp` 下按关键词验证过，但没有合理数据集命中

不需要先跑 `app list` 的场景：

- 用户已经给了 `--appcode`
- 用户已经给了 `--app <name>`
- 问题明显沿用上文已确认的同一 app 上下文
- 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是默认候选，不是强上下文。未显式指定 app 且存在 `defaultApp` 时，应先用 `dataset list --name <关键词>` 验证默认候选；命中不合理时，再通过 `app list` 扩大搜索。

## 如何选择使用哪个应用

推荐方法不是只看 app 名，而是：

1. 有 `defaultApp` 时，先在默认候选下执行 `dataset list --name <关键词>`
2. 默认候选命中合理时直接继续
3. 默认候选无命中、弱命中或语义不合理时，再用 `app list` 拿到候选 app
4. 按需求关键词挑 1-2 个候选，对每个候选执行 `dataset list --app <name> --name <关键词>`
5. 用数据集命中情况反向确认正确 app

这样比纯靠 app 名猜测更稳。

## app pull — 手动刷新本地 app cache

```bash
lovrabet app pull
lovrabet app pull --env daily
lovrabet app pull --local
lovrabet app pull --no-cache
```

| Flag | 说明 |
|------|------|
| `--env <env>` | 指定环境，默认当前环境 |
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
