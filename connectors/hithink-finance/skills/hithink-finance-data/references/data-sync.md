# `hithink-finance data sync`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema data.sync --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 需要当前可用凭据，先按 shared 查看只读 auth status，或提供本次显式 Key。
- 命令会持有数据锁，避免并发写库。

## 命令

```bash
hithink-finance schema data.sync --format json
hithink-finance data sync --format json
```

## 参数选择策略

- 使用全局 `--db` 指定库路径；默认路径来自平台数据目录。

## 窗口与分页

- 本地命令按目标库执行；查询大结果使用 `db export` 或 `market panel --output`。

## 常见错误

- 认证失败时先回到 shared skill 的 auth 流程。

## 批量操作说明

- 维护操作按目标库逐项执行，并检查每个结果。
- 确认目标路径与影响；不要从只读查询意图推断清理、迁移或修复授权。
