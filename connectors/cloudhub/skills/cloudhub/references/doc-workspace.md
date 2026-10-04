# doc workspace（知识库容器）

> **前置条件：** 先阅读 [`./doc.md`](./doc.md) 了解 doc scope 整体。

知识库（Workspace）是文档的顶层容器，通过 `doc workspace list` 获取 `KB_ID`。

## 命令

| 命令 | 必填参数 | 说明 |
|------|---------|------|
| `doc workspace list` | — | 列出当前 profile 可访问的所有知识库（个人 + 企业） |
| `doc workspace list --type personal` | `--type personal` | 仅列出个人知识库 |
| `doc workspace list --type enterprise` | `--type enterprise` | 仅列出企业知识库 |
| `doc workspace get --id <KB_ID>` | `--id` | 获取单个知识库详情 |
| `doc workspace create --name <NAME>` | `--name` | 创建个人知识库，`--description` 可选 |

`--type` 取值（clap ValueEnum，**不支持短前缀**，必须写完整）：

| 值 | 含义 |
|----|------|
| `all`（默认） | 个人 + 企业 |
| `personal` | 仅个人知识库 |
| `enterprise` | 仅企业知识库 |

> 完整意图映射见 [`./doc.md`](./doc.md) 的"意图映射"段。

## 返回字段

`doc workspace list`（无论 `--type` 取何值）返回 `data.list` 数组，每项字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 知识库 ID（即 `KB_ID`，传给 `--workspace` / `doc workspace get --id`） |
| `name` | string | 知识库名称 |
| `description` | string | 描述 |
| `visibility` | int | **1=企业知识库，2=个人知识库** |
| `bizType` | string? | 业务类型；非空表示按场景自动建的知识库（如 `meeting` 是会议 Agent），普通用户建不出来 |
| `permissionLevel` | int | 当前用户在该 KB 的权限：**1=可管理（owner），2=可编辑，3=可查看** |
| `docCount` | int | 文档数量 |
| `memberCount` | int | 成员数量 |
| `ownerName` | string | 拥有者姓名 |
| `ownerOid` | string | 拥有者 openId |
| `ownerPhotoUrl` | string | 拥有者头像 URL |
| `createTime` / `updateTime` | string | ISO 时间戳 |
| `topped` | bool? | 是否置顶 |
| `favorited` | bool? | 是否收藏 |
| `deletable` | bool | 当前用户能否删除 |

## 创建知识库

```bash
yzj-cli doc workspace create --name "我的笔记" --description "可选描述"
```

CLI 当前固定创建个人知识库（`visibility=2`）；企业知识库需要额外的成员权限参数，CLI 暂未暴露。

## 常见问题

- **`doc workspace list` 返回的 KB 比 `--type personal` 多** —— 正常。`all` 含个人 + 企业；`personal` 只个人。
- **企业知识库列表有"会议Agent知识库"等不是我建的** —— `bizType` 非空的 KB 是后端按业务自动建的，列出来说明你有权限。
- **`--type p` 报 invalid value** —— clap 不支持短前缀，必须写完整 `personal` / `enterprise` / `all`。
