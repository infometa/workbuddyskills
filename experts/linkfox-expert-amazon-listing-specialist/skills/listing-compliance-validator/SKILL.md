---
name: listing-compliance-validator
description: 对当前 Amazon Listing 版本执行平台无关的本地合规终检，复用随包受限词、绝对化宣称、品牌冲突和用户禁用词规则。
---

# Listing Compliance Validator

把当前标题、五点、描述和搜索词交给 `listing-compliance-scan` 的本地脚本，生成字段级结果。

- 任一受限内容或明确禁用词命中时为 `fail`。
- 绝对化、无证据数字、竞品品牌或不确定品类声明为 `review` 或 `fail`，按规则严重度处理。
- 输出必须包含命中原文、字段、规则来源和最小修改建议。
- 不调用外部商标、版权、专利、店铺或平台服务。
- 通过只表示随包本地规则未发现阻断项，不代表法律或平台审核保证。
