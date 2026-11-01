# 更新日志 (CHANGELOG)

> 本文件随 AI-HIVE Connector 包版本更新。Connector 包当前版本：**1.2.1**。
> 日期：2026-09-14

## 1.2.1 — 2026-09-14

- 修复 2026-09-09 平台审核驳回：`cli.json` 补齐 `init` 三平台安装命令，解决干净 Windows 环境安装步骤读取 `cliConfig.init` 崩溃（`Cannot read properties of undefined (reading 'win32')`）；技能内容不变。

## 1.2.0 — 2026-09-09

- 新增 wan3-video-expert 技能：覆盖 Wan 3.0 标准版与 Pro 的 T2V / I2V / R2V prompt 工程、badcase 诊断与付费生成流程，对齐 `@infimind-next/ai-hive-mcp@0.3.0` 的 `get_model` 模型契约、`dryRun` 只读预检、`clientRequestId` 幂等键与 `pricingSnapshot` 原样回传。
