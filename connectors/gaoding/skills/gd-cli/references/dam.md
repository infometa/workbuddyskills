# DAM 素材管理

## 先发现，再操作

先读 `gd-cli dam --help` 选择当前支持的操作，使用前读对应子命令的 `--help`；以下是常见路径，不是完整命令或参数清单。

任何资源库范围内的查询或写入都先运行：

```bash
gd-cli org current
gd-cli dam repository list --json
```

只使用返回的 `repositories[].repository_id`。团队资源库的 `type` 为 `team`，企业资源库的 `type` 为 `enterprise`；不要使用名称、前端 URL、团队实体 ID 或历史值猜 ID。资源库不做 switch，`org switch` 只切换组织。

需要文件夹或标签 ID 时继续发现：

```bash
gd-cli dam folder list --repository-id <id> --json
gd-cli dam tag list --repository-id <id> --json
```

文件夹、标签的筛选和分页参数从对应 `--help` 获取。根文件夹 ID 为 `0`，涉及目标位置时必须显式传 `--target-folder-id 0`，不要把缺省值理解为根目录。

## 查询与下载

```bash
gd-cli dam list --repository-id <id> --json
gd-cli dam search <query> --repository-id <id> --json
gd-cli dam get <asset-id> --json
gd-cli dam download <asset-id> --repository-id <id> --output-dir ./downloads --json
```

跨资源库查询只在用户明确要求时使用 `--all-repositories`。筛选、下载范围和本地文件处理规则从所选命令的 `--help` 获取，不擅自扩大用户指定的资源范围。

## 写入与授权

```bash
gd-cli dam upload ./asset.png --repository-id <id> --folder-id <folder-id> --tag-ids <tag-id> --json
gd-cli dam rename <entry-id> --kind asset --title <new-title> --repository-id <id> --json
gd-cli dam copy <entry-id> --kind asset --repository-id <source-id> --target-repository-id <target-id> --target-folder-id <folder-id> --json
gd-cli dam move <entry-id> --kind asset --repository-id <source-id> --target-repository-id <target-id> --target-folder-id <folder-id> --json
gd-cli dam delete <asset-id> --repository-id <id>
```

- 条目类型和单次操作范围以命令 `--help` 为准，不把示例当作完整能力清单，也不擅自扩大写入范围。
- 上传受保护路径时，只有用户明确允许才加 `--allow-sensitive-path`；需要等待分析完成时加 `--wait-analysis`。
- 复制结果可能没有 `copied_entry_id`，这不表示失败；查询目标文件夹或目标资源库发现新副本，不要猜测新 ID，也不要再次提交 copy。
- 移动、复制或重命名若返回“已提交但未确认”，先查询目标位置并报告诊断 ID，不要立即重复提交。
- 删除默认移入回收站；只有用户明确要求永久删除时才加 `--permanent`。
- 回收站等未在示例中展示的操作先查 `gd-cli dam --help`；未发现所需能力时说明限制，不猜测命令。

写操作前确认资源库、条目 ID、类型和目标位置。优先从本轮 JSON 输出取得 ID，不从本地登录状态或旧输出替用户猜测。
