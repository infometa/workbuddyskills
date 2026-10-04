# Agent 入口与 Schema

## 什么时候读取

使用 `weaver-work-cli asset` 前、编写自动化调用、选择 operation 或确认字段结构时读取本文件。

## 准备命令

```text
weaver-work-cli --version
weaver-work-cli doctor --e10
weaver-work-cli --profile eteams asset schema
```

如未登录，按共享规则读取 `../../weaver-e10-shared-connector/references/e10-auth-and-session.md` 后处理。

## 固定入口

Agent 优先调用统一 operation 入口：

```text
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
```

简单 JSON 通过 `--input-json` 传入，复杂或多行 JSON 使用 UTF-8 文件和 `--input <path>`；只有确认当前 shell 能稳定传管道时才使用 `--input -`。按环境选择示例：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json asset run asset.list --input-json '{"page_size":10}'
```

`weaver-work-cli asset schema` 是可用 operation、输入字段、固定参数和风险等级的第一信息源。不要用未出现在 schema 中的 operation，也不要把原始 `weaver-e10-ziguanjia-connector` reference 当作可直接调用的 CLI 合约。

## 输出处理

成功结果在 stdout，失败结果在 stderr。判断规则读取共享 reference：`../../weaver-e10-shared-connector/references/json-output-contract.md`。

列表、详情或回查结果可能很长时，不要把 stdout 的完整 envelope 直接展示给用户。默认 `page_size=10` 小页读取；只渲染资产决策所需字段，例如资产 ID、名称、编号、类型、状态、地点、管理人/使用人。需要更多结果时按 `page_no` 分页继续；需要保留完整原始 JSON 时落本地文件并返回路径。

高风险写入读取共享 reference：`../../weaver-e10-shared-connector/references/high-risk-write.md`。

## 版本门禁

所有查询与写操作前，CLI 会先校验 `zgjasset_search_appver` 是否存在 `ver_name ≥ V14` 的记录。门禁结果也可直接查询：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json asset run asset.gate.check --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json asset run asset.gate.check --input-json '{}'
```

返回 `meta.status=VERSION_GATE_PASSED` 表示通过；`VERSION_GATE_FAILED` 表示未通过，此时应停止后续资产操作并提示用户升级到 V14 及以上。
