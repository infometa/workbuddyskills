---
name: dcs-data-manager
description: 通过本机 dcs CLI 管理 DCS Cloud Files：浏览、下载、上传。
version: 1.1.0
---

# 数据管理（dcs CLI）

> 执行前确认已完成总览 [SKILL.md](../SKILL.md) 中的 **auth login + project switch**。

用 **本机 `dcs` CLI** 操作项目 Files 与集群数据。**参数名是 `--path` / `--target`，不是 `--source_path` / `--target_path`。**

## 浏览与导航

| 意图 | 命令 |
|------|------|
| 列目录 | `dcs data ls [path] --output json` |
| 搜索 | `dcs data find --output json` |
| 文件/目录详情 | `dcs data info --path <path> --output json` |
| 切换当前目录 | `dcs data cd <path>` |
| 当前目录 | `dcs data pwd` |
| 删除 | `dcs data rm <path>` |

路径以 **`/Files/...`** 为项目数据根（也支持相对当前 `data cd` 路径）。

## 下载到本机

```bash
dcs data download --type web --path /Files/ResultData/report.html --target D:\download\
```

| 参数 | 说明 |
|------|------|
| `--type` / `-T` | **必填**：`web`（≤200MB 小文件）、`raysync`、`ossutil` 等 |
| `--path` / `-p` | **必填**：云端路径，逗号分隔可批量 |
| `--target` / `-t` | 本机目标目录；web 模式默认可为当前目录 |
| `--download-mode` / `-m` | 仅 raysync：`client` 或 `command` |

- 小文件 / 图片：**`--type web`** 最简单
- 大文件：需本机安装 `ossutil` 等，用 `--type ossutil`

## 上传到 Files

```bash
dcs data upload --cluster-mode other --path /dell2/test/result.txt --target /Files/RawData
```

| 参数 | 说明 |
|------|------|
| `--cluster-mode` / `-c` | **必填**：`other`（集群文件）或 `batch_import`（表格导入） |
| `--path` / `-p` | 源：集群路径或表格路径 |
| `--target` / `-t` | 目标：须 **`/Files` 开头** |

这是**集群侧**上传到项目 Files，不是本机拖拽上传。

## 其它

| 命令 | 用途 |
|------|------|
| `dcs data copy` | 项目内/跨项目/跨片区复制 |
| `dcs data move` | 项目内移动 |

## Agent 约定

- 优先 `--output json`
- 查参数：`dcs data download --describe`
- Windows：路径含空格时用引号；**不要**在 CMD 里输入 `<>` 占位符

## 明确不做

- 不用 `terminal read` 代替 `data download` 取二进制文件
- 不假设 `--source_path` / `--target_path` 存在（CLI 未提供这两个 flag 名）
