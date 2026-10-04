# Changelog

## 1.0.3 - 2026-09-01

- 市场卡片 examples 更新为 5 句欢迎引导语（examples_zh / examples_en 同步），替换原业务查询示例。
- `versionCheck`（win32）新增自愈：二进制缺失时返回 `woscli version v0.0.0`，触发 `needsUpgrade` 自动执行 `init` 重装，规避 `isCliInstalled` 误判（`where "powershell"` 恒真）导致的「跳过安装、version-check 崩溃」死局。
- 内置 skill `woscli-usage` 升级至 1.1.0：新增第 0 节「能力路由」，优先复用已安装的微盟专家与 Skill，命中后禁止再用 woscli 重复探索同一能力。
- 新增本机资产检测命令（Bash / PowerShell 双版本）与 19 行「诉求 → 资产 → 兜底 category」路由表。
- 命令发现改为「语义精搜优先」：`search --response-format concise` 一次返回必填参数（REQUIRED INPUTS），把原「search → --help → 执行」三步压缩为两步。
- 标注 `<category> --help` 分页陷阱（默认 5 条/页，order 59 条、goods 125 条），禁止逐页翻完；新增探索预算上限 ≤3 次、批量探测合并为一次调用等成本约束。

## 1.0.1 - 2026-08-30

- 为 macOS、Linux 和 Windows 安装流程增加强制 SHA256 完整性校验。
- 将最低可用 woscli 版本设置为 1.0.0。
- 明确 Windows PowerShell 与 CMD 路径写法以及手动浏览器授权流程。
- 补充完整只读示例、JSON 响应结构、不可逆操作警示和升级/卸载说明。
