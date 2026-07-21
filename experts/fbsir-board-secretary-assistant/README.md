# 福帮手董秘助手

`福帮手` 品牌下的 `董秘助手`，用于在公告、路演、投资者问答、互动回复、调研纪要和沟通稿对外使用前，先做一轮结构化合规红队审查。

默认输出聚焦五件事：

- 风险等级
- 触发依据
- 问题片段
- 补证要求
- 建议改写与人工复核下一步

边界固定如下：

- `publishReady=false`
- `publicDisclosureAllowed=false`
- `manualReviewRequired=true`
- 不提供最终法律意见
- 不替代正式披露、审批或发布动作

当前 `26.7.2` 包包含服务侧联调与智能化运营闭环所需的合同、场景包和审核材料，但这些材料不等于官方运行态替换，也不等于自然 same-binding 产品信用完成。

这次升级重点支持四件事：

- 以独立客户端为识别对象的脱敏身份归一
- 通过乐包解锁能力、鼓励领取并归集用户意图
- 服务侧依据乐包和脱敏数据识别用户，并牵引宿主侧下一步动作
- 在不依赖连接器的前提下，让个性化价值转化和宿主能力激活可观测、可复核、可迭代

提审包边界补充：

- 提审包不依赖未公开的宿主接口、方法或调试路径。
- 宿主研究中发现的高级运行时能力，只作为 `record-only / target-only` 设计目标进入审核材料。
- 官方入口替换、真实宿主闭环、支付与交付闭环，仍然必须由公开运行态与服务侧自然证据单独证明。

更完整的审核与联调说明见：

- `REVIEW-PACKET.md`
- `contracts/first-value-contract.json`
- `contracts/governance-boundary.json`
- `contracts/service-forward-fields.json`
- `contracts/service-traction-upgrade-contract.json`

可选服务增强边界：

- 专家包不再携带 `.mcp.json`、`mcpServers` 或 host-tool-exposure 入口级元数据。
- 服务侧观察和 same-binding followthrough 只能通过服务侧真实流量与宿主证据对齐，不得在用户打开专家时触发连接器弹窗。
- 如果宿主没有暴露服务增强能力，专家仍必须直接基于用户材料交付第一张合规红队卡，不向用户展示工具或连接状态诊断。
