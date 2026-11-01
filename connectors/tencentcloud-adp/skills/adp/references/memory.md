# 记忆库

记忆库按空间可见：传 `--space-id`，或在有 `adp.jsonc` 的项目里运行。
它和 `adp.jsonc` 的 `memory`（应用自带的长期记忆开关）是两回事；用户说“记忆库”“记忆条目”“绑定记忆库”时用 `adp memory`。

ID 前缀决定类型，CLI 自动推断，不用传类型：

- `rms_…` 结构化记忆库（rich）：条目有名称、类型、front matter、版本，每个终端用户可有一份 L2 摘要。
- `fms_…` 扁平记忆库（flat）：只有类型和正文，可设保留天数（`ttl_days`，0 为永久）。类型创建后不能改。

## 查看

```bash
adp memory list --space-id <id> --fields storeId,name,typeName,referencedApps --format json
adp memory users --space-id <id> --store-id <store> --format json
adp memory entry list --space-id <id> --store-id <store> --user-id <user> --format json
adp memory summary get --space-id <id> --store-id <rms_id> --user-id <user> --format json
adp memory binding get --space-id <id> --app-id <app> --format json
```

`referencedApps` 不总是准确，判断某个应用用哪个库要看 `memory binding get`。

## 写入

先 `--dry-run` 预览，再执行。

```bash
adp memory create --space-id <id> --name 客服长期记忆 --format json            # 默认 rich、开摘要
adp memory create --space-id <id> --name 会话缓存 --type flat --ttl-days 30 --format json
adp memory entry add --space-id <id> --store-id <store> --user-id <user> --text "<≤4000 字>" --format json
adp memory entry update --space-id <id> --store-id <store> --user-id <user> --entry-key <key> --content "<新内容>" --format json
adp memory bind --space-id <id> --app-id <app> --store-id <store> --format json
adp memory binding update --space-id <id> --app-id <app> --disable --format json
```

- rich 库 `entry add` 会用模型从文本生成条目名称（就是 entry key）和 front matter；写完用 `entry list` 取真实 key，不要自己猜。
- `entry update`/`entry delete` 会自动读取当前版本；flat 条目只能改 `--content`/`--type`。
- 一个应用每种类型最多一个绑定。`bind` 已有绑定时会切换到新库；不传 `--store-id` 时平台自动建默认库。没有解绑接口，停用用 `binding update --disable`。
- `memory summary set --user-id <user> --text "<完整摘要>"` 是整份覆盖，不是追加；`--text` 必填，先 `memory summary get` 取现有内容再改。

## 删除

`memory delete`、`entry delete`、`summary delete` 都需要用户明确同意后才加 `--yes`。
删除库会连同所有条目一起删除，不可恢复；应用仍启用绑定时报 `MemoryStoreInUse`，要先切换或停用绑定，不要擅自去改用户应用的绑定。

## 导入导出

```bash
adp memory export --space-id <id> --store-id <store> --output ./memory.csv --format json
adp memory import --space-id <id> --store-id <store> --file ./memory.csv --format json
```

CSV 列与导出一致：rich 为 `UserId,Name,Type,Frontmatter,Content`，`Type` 写标签（如 `user`），不是数字；flat 为 `VisitorId,Type,Content`。
导入失败报 `MemoryImportFailed`，平台不给逐行原因，先对照一份导出的 CSV 检查列名和类型。导入的 rich 条目名称可能被模型改写。
