# `hithink-finance market adjustment-factors`

## 前置条件

- 读取[本域入口](../SKILL.md)和本命令说明；需要认证、共用输出或维护指引时，再读取[共享规则](../../hithink-finance-shared/SKILL.md)。
- 首次执行或版本变化时用 `hithink-finance schema market.adjustment-factors --format json` 确认参数，未说明的组合规则再看命令 `--help`。
- 查询本地日级复权因子；需要本地库。

## 命令

```bash
hithink-finance schema market.adjustment-factors --format json
hithink-finance market adjustment-factors --thscode <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --format json
```

## 参数选择策略

- 必填 `--thscode <code>`；可选 `--start` / `--end`。

## 窗口与分页

- 本地命令按目标库执行；查询大结果使用 `db export` 或 `market panel --output`。

## 常见错误

- 日期必须是 `YYYY-MM-DD`；没有本地库先走 `data init|sync`。

## 批量操作说明

- 批量或全量请求必须落盘，最终只报告路径、行数和窗口。
- 如果需要多标的循环，逐批执行并记录每批参数；不要把完整结果塞进上下文。
