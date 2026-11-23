# 全局规则

## 前置条件

- 宿主依据内置 Skill 的 description 直接选择业务域。选定命令后按需读取目标 reference 与 schema；需要发现未知命令时再运行 `capabilities`。同版本已读取的规则和目标 schema 可复用。
- 远端取数逐命令透明复用本地worker，空闲约120秒退出；认证、维护和数据库命令在前台。状态/停止/普通路径及不确定结果处理见 [本地查询worker](query-worker.md)。
- 默认 auto 在终端显示按宽度排版的表格，管道输出紧凑 JSON 信封；机器读取显式使用 `--format json`（两空格缩进）或 `--format ndjson`（每次命令一个单行信封，数组保留在 data 内）。
- `--format table` 使用业务默认列、数值右对齐和宽屏/窄屏布局；数据列表默认预览20条，`--max-rows N` 控制预览（0为本次全部），`--columns a,b` 按原始字段选列（`*`为全部）。这些选项仅影响终端表格；JSON/NDJSON和导出保持完整。
- `--output <path>` 只用于声明该参数的命令。远端默认保存完整紧凑JSON信封；`--file-format ndjson|csv` 将本次结果逐行导出，stdout报告路径/格式/数量。一次命令不自动翻页。CSV空值为空单元格、嵌套值为JSON字符串；NDJSON保留类型和嵌套结构。db export/market panel仍按各自文件格式契约执行。

## 输出契约

- `auth status` 用退出码表达连接状态：已连接退出 0，未连接退出 3；两者均在 stdout 返回 `ok=true`，读取 `data.connected`。读取或存储失败时，从 stderr 的 `ok=false` 信封读取 `error`。
- 命令执行成功以进程退出码 0 和 `ok: true` 为准；业务验收还应检查命令结果，例如质量检查的 `data.ok`、目标窗口、样本和行数。
- 错误以非 0 退出码和 `ok: false` 为准；读取 `error.code`、`error.category`、`error.hint`。
- 需要诊断时使用 `--debug`；已脱敏的 request ID 与堆栈位于 `meta.diagnostics`，非预期内部错误的预填问题链接位于 `error.report_url`。
- HTTP 429/502/503/504 优先于响应体中的业务错误信封进行有界重试；耗尽后返回 `UPSTREAM_HTTP_<status>`。
- 不要按上游旧格式 `code == 0` 判断成功。

## 大结果纪律

- 全市场、分页、长区间、多 ticker 数据不得回显完整内容。
- 远端大结果用该命令自己的 `--output <path>`，stdout 只保留路径/count 摘要。
- 本地大结果用 `db export --output <path>` 或 `market panel --output <path>`。
- 最终回答只报告输出路径、行数、时间窗口、命令摘要和必要字段名。
- 下游需要数据时让 pandas/notebook/脚本读取落盘文件。
