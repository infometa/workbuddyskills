# `hithink-finance data init`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema data.init --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 远端初始化先通过 `auth status` 复用当前启用的 OAuth 或 API Key；首次登录默认推荐 OAuth。本地文件导入无需远端认证。
- 本地文件导入必须同时提供 `--kline` 和 `--events`。
- 远端全量初始化包含下载、导入和复权重建；使用可等待全部子进程的前台执行器，超时不少于 15 分钟。下载完成不表示命令已结束或数据库已解锁。
- 仅在退出码 0 且 JSON 信封 `ok=true` 后，才对同一 `--db` 继续状态、行情或 SQL 查询。

## 命令

```bash
hithink-finance schema data.init --format json
hithink-finance data init --kline <kline.parquet> --events <events.parquet> --format json
```

## 参数选择策略

- `--kline <path>` 与 `--events <path>` 成对出现；可选 `--symbols <path>`。
- 省略本地文件时从远端 Market Dump 初始化，使用当前全局凭据或本次显式 `--api-key-stdin`。

## 窗口与分页

- 本地命令按目标库执行；查询大结果使用 `db export` 或 `market panel --output`。

## 常见错误

- 只给 `--kline` 或只给 `--events` 会失败；两者必须成对。
- 执行器超时或非零退出时，检查锁文件或错误中的存活 PID；PID 仍存活则继续等待，不得在该 DB 上继续执行或删除活锁。用户明确取消时才终止对应进程。

## 批量操作说明

- 维护操作按目标库逐项执行，并检查每个结果。
- 确认目标路径与影响；不要从只读查询意图推断清理、迁移或修复授权。
