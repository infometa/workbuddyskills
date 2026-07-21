# Wiki / 知识库 (wiki) 命令参考

> 知识库（Wiki）是钉钉的文档空间管理能力。知识库内可以存放文档、表格、脑图等多种类型的页面，按空间和目录树组织。

## 命令总览

| 子命令 | 用途 |
|-------|------|
| `space list` | 列出知识库空间 |
| `space get` | 获取知识库空间详情 |
| `space create` | 创建知识库空间 |
| `space search` | 搜索知识库空间 |
| `member` | 知识库成员管理 |

> 注意：知识库内文档的搜索、读取、编辑等操作使用 `doc` 命令并传入 `--workspace` 参数。`wiki` 域主要负责空间管理。

---

## space list — 列出知识库空间

```
Usage:
  dws wiki space list [flags]
Example:
  dws wiki space list
  dws wiki space list --type myWikiSpace
  dws wiki space list --type orgWikiSpace --limit 50
Flags:
      --type string         空间类型: myWikiSpace / orgWikiSpace (默认 orgWikiSpace)
      --limit string        每页数量 1-50 (默认 20)
      --page-token string   分页游标 (从上次结果获取)
```

注意:
- `--type myWikiSpace` 列出个人知识库，`--type orgWikiSpace` 列出组织知识库
- 翻页：响应中有 `nextPageToken` 时，传入下次请求的 `--page-token`

---

## space get — 获取知识库空间详情

```
Usage:
  dws wiki space get --id <workspaceId> [flags]
Example:
  dws wiki space get --id <WORKSPACE_ID>
Flags:
      --id string   知识库空间 ID (必填)
```

---

## space create — 创建知识库空间

```
Usage:
  dws wiki space create [flags]
Example:
  dws wiki space create --name "项目文档库"
  dws wiki space create --name "团队知识库" --description "团队共享的技术文档和最佳实践"
Flags:
      --name string          空间名称，不超过 100 字符 (必填)
      --description string   空间描述，不超过 500 字符 (可选)
      --icon string          空间图标标识 (可选)
```

---

## space search — 搜索知识库空间

```
Usage:
  dws wiki space search --keyword <关键词> [flags]
Example:
  dws wiki space search --keyword "项目"
```

> 注意：`dws wiki search` 已重定向到 `dws wiki space search`，请直接使用后者。

---

## member — 知识库成员管理

知识库成员管理子命令。具体子命令和参数请先执行 `dws wiki member --help` 查看。

---

## 意图判断

- 用户说"知识库 / Wiki / 空间管理" → `wiki space list` / `wiki space create`
- 用户说"知识库里的文档 / Wiki 文档" → 使用 `doc list --workspace` / `doc search --workspace-ids`
- 用户说"创建知识库" → `wiki space create`
- 用户说"搜索知识库" → `wiki space search`

关键区分: wiki(空间/目录管理) vs doc(文档内容读写)

## 核心工作流

```bash
# 1. 列出我参与的知识库
dws wiki space list --format json

# 2. 创建新知识库
dws wiki space create --name "项目文档库" --format json

# 3. 查看知识库详情
dws wiki space get --id <WORKSPACE_ID> --format json

# 4. 在知识库中创建文档（使用 doc 命令 + --workspace）
dws doc create --name "技术方案" --workspace <WORKSPACE_ID> --format json

# 5. 浏览知识库目录（使用 doc 命令 + --workspace）
dws doc list --workspace <WORKSPACE_ID> --format json
```

## 上下文传递表

| 操作 | 从返回中提取 | 用于 |
|------|-------------|------|
| `wiki space list` / `wiki space search` | `workspaceId` | `doc list --workspace`、`doc create --workspace`、`wiki space get --id` |
| `wiki space create` | `workspaceId` | 同上 |
| `doc list` | 文档 `nodeId` | `doc read --node`、`doc info --node` |

## 注意事项

- 知识库内的文档操作（创建、读取、搜索等）通过 `doc` 命令配合 `--workspace` 参数完成
- `wiki` 域当前主要提供空间级别管理能力，文档级别操作走 `doc` 域
- 具体可用子命令和参数以 `dws wiki --help` 和 `dws wiki space --help` 为准

## 相关产品

- [doc](./doc.md) — 文档创建、读写、块级编辑，配合 `--workspace` 用于知识库文档操作
- [sheet](./sheet.md) — 普通电子表格
- [aitable](./aitable.md) — AI 表格/多维表
