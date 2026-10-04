---
name: mibao-safety-qa
description: 对原件保护、输出路径、失败恢复、隐私外发、manifest、校验和与最终交付状态执行失败关闭验收。
---

# 安全、交付与验收

原件默认只读；禁止覆盖、删除、移动、符号链接逃逸、任意 shell 和隐式上传。派生物写入新的输出目录，长任务使用检查点，失败或中断不能留下疑似成功的交付物。

标准交付包含：输入 manifest、输出 manifest、处理日志、失败清单、校验结果、人工复核列表、隐私/外发清单和最终摘要。完成状态只能来自可回读产物与验收回执；`partial`、`failed`、`blocked`、`not-run` 必须分别保留。

模型或宿主未暴露能力时给出 `ready-with-limitations` 诊断和可恢复下一步。路径上的第三方工具不证明包自包含；本地/候选/宿主/可提审/已上架必须分层报告。

对 `execution_core_v1`，执行前必须展示并确认精确源目录与项目目录，且两者互不包含。用户数据只写入闭合 JSON 请求，不进入 Shell argv；请求必须绑定宿主给出的绝对根与固定作用域，并在源/项目访问前消费。只允许包内一次性 `inventory_build` / `inventory_search`，不安装 MCP、连接器或依赖。完成后必须回读结果 schema、报告 manifest、HTML、`privacyMode=local-private` 和检索 evidence refs；失败时保留 `requestDisposition` 与恢复动作，任一缺失均失败关闭。
