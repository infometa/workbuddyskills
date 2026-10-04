# 文书定档案 CLI 入口

## 什么时候读取

首次进入文书定档案场景、需要确认 operation 清单、需要确认调用方式或输出约定时读取本文件。

## 统一入口

所有能力都通过 `weaver-work-cli --profile eteams archive run <operation>` 调用；`weaver-work-cli archive schema` 输出 operation、字段、风险等级和是否必须确认的合约。

| 想做什么 | Operation |
| --- | --- |
| 查看全宗 | `archive.fonds.list` |
| 查看预归档电子文件库节点 | `archive.prelib.tree` |
| 全文检索可借档案 | `archive.search.run` |
| 查看档案基本信息 | `archive.info.get` |
| 查看借阅车 | `archive.borrow-car.list` |
| 加入借阅车（免确认） | `archive.borrow-car.add` |
| 查看借阅单 | `archive.borrow-list.list` |
| 查看借阅单详情 | `archive.borrow-list.detail` |
| 下载借阅单原文 | `archive.borrow-list.download.prepare` / `.apply` |
| 从借阅车发起借阅 | `archive.flow.borrow-car.prepare` / `.apply` |
| 从检索结果发起借阅 | `archive.flow.search.prepare` / `.apply` |
| 借阅单续借 | `archive.flow.renew.prepare` / `.apply` |
| 上传到预归档电子文件库 | `archive.upload.prelib.prepare` / `.apply` |

便捷子命令（`archive borrow-car list`、`archive borrow-list download-prepare` 等）与 `archive run <operation>` 等价，字段一致。

## 输入方式

- 简单 JSON：优先 `--input-json '<json>'`。
- 复杂或多行 JSON：先写 UTF-8 文件，再 `--input <path>`；只有确认当前 shell 能稳定传管道时才用 `--input -`。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams archive schema
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams archive schema
weaver-work-cli --profile eteams --json archive run archive.fonds.list --input-json '{"menuSign":"collectLib"}'
weaver-work-cli --profile eteams --json archive run archive.search.run --input-json '{"key":"会计凭证","pageNo":0,"pageSize":10}'
weaver-work-cli --profile eteams --json archive run archive.borrow-car.list --input-json '{"pageNo":1,"pageSize":10}'
```

## 输出约定

成功写 stdout，形如 `{"schemaVersion":1,"ok":true,"operation":"...","data":{...},"meta":{...},"warnings":[]}`；失败写 stderr，形如 `{"schemaVersion":1,"ok":false,"error":{"type":"...","subtype":"...","message":"...","retryable":false}}` 并设置非 0 退出码。

列表类操作默认小页读取（`pageNo`/`pageSize`），先展示最相关的前 10 条；不要把完整 JSON 原样贴给用户，超长内容落本地文件后给路径。

## 注意

- 认证和登录态只能通过 `weaver-work-cli auth ...` 判断；禁止直接读取、列出、打印或解析用户主目录下的旧 `.e10-cli`、auth、config 或 Keychain 数据。
- 错误为 `authentication` 或 `session_expired` 时立即停止，不要用示例占位域名或自行猜域名登录。
- 写操作（`*.apply`）必须先执行同名 `.prepare` 拿到 `continuation`，再带 `confirm=true` 执行；不要手工构造 continuation。
- 例外：`archive.borrow-car.add` 加入借阅车是免确认写操作，直接执行，不需要 `.prepare` / `.apply` 两段确认链。
