# 常见问题路由

本表用于识别用户真正想完成的工作。`workflow_id` 同时写入 `outputs/run-manifest.json`。先使用材料中已有信息，只追问会阻塞首个产物的最少未决输入。

| 用户意图 | `workflow_id` | 首个动作 | 最少未决输入 | 标准产物 | 验收条件 | 边界 |
|---|---|---|---|---|---|---|
| 材料很多，不知道从哪里下手 | `project_triage` | 读取已有消息和文件，判断阶段 | 会改变项目方向的角色或交易方向 | `outputs/project-triage.md` | 有阶段依据、关键缺口和下一步三件事 | 不要求用户重复填写已有信息 |
| 帮我整理一份报告 | `report_draft` | 确认受众与用途，选择模板 | 受众、用途、信息截止日 | `outputs/report-draft.md`、`outputs/report-qc.md` | 正文完整，来源与待确认项可定位 | 缺少事实用 `[待确认]`，不补造数字 |
| 检查报告里的数字和出处 | `report_qc` | 确定待检查文件，运行来源闸门 | 文件路径和检查范围 | `outputs/report-qc.md` | 写明脚本、退出码、问题位置与状态 | 退出码 2 代表未完成，不能写“通过” |
| 检查股权表 | `cap_table_check` | 优先读取 XLSX、CSV 或标准表格，运行股权闸门 | 股本分母、时点或文件路径 | `outputs/report-qc.md` | 比例合计、分母冲突和重复披露均有结论 | 未识别到表时不能写“通过” |
| 画交易结构图 | `structure_diagram` | 确认主体、比例、步骤和流向 | 影响拓扑的主体或流向 | `outputs/deal-structure-diagram.svg`、说明文件 | SVG 可编辑、机器校验通过、视觉预览无重叠 | 只按既定结构作图，不代替结构设计 |
| 帮我设计交易结构 | `structure_options` | 整理目标、约束、结构备选方案和决策点 | 交易目标与不可突破约束 | `outputs/structure-options.md` | 每个选项写清条件、利弊、风险和决策点 | 最终结构由用户决定，人工复核可选 |
| 帮我做估值 | `valuation_framework` | 整理时点、口径、数据和可用方法 | 估值时点、币种和对象 | `outputs/valuation-framework.md` | 方法适用性、关键假设和敏感项可追溯 | 不把框架包装成公允定价结论 |
| 判断项目有没有机会做成 | `deal_viability_review` | 按四个成交视角检查证据和阻力 | 买卖双方目标及已知约束 | `outputs/deal-viability-review.md` | 四个视角均有证据、未决问题和下一步动作 | 不保证成交，人工复核由用户决定 |
| 查询港股公告 | `hkex_query` | 告知外部查询参数，用户确认后运行一次披露易查询 | 股票代码、日期范围和用户确认 | `outputs/hkex-announcements.md` | 查询状态、日期、标题、URL 和 `external_queries` 记录齐全 | 零结果与查询失败必须区分 |
| 持续跟踪并提醒 | `tracking_plan` | 创建跟踪对象、信号和本次查询结果 | 对象、信号范围、复查频率 | `outputs/tracking-plan.md` | 有可重复执行的查询步骤和基线结果 | 当前公开包不后台持续运行或主动提醒 |
| 寻找买方或标的 | `buyer_target_framework` | 明确筛选条件并整理公开候选买方框架或标的框架 | 交易方向、行业、地域和规模 | `outputs/buyer-target-framework.md` | 筛选标准与候选证据可追溯 | 不代表已匹配或已有交易意愿，不访问 MAI 私有网络 |
| 联系交易对手 | `counterparty_preparation` | 整理授权、材料和内部准备事项 | 联系目标与授权状态 | `outputs/counterparty-preparation.md` | 权限、材料、审批与风险均有记录 | 不生成或发送对外联系内容 |
| PDF、扫描件或图片 | `file_intake` | 区分已阅读、已提取和已机器校验 | 文件路径和目标产物 | 分诊、报告草稿或质检记录 | 记录格式、读取状态和关键数字复核状态 | OCR 关键数字回到原件人工复核 |

## 回复顺序

1. 用一句话复述用户要完成的工作。
2. 直接执行当前材料足以支持的第一步。
3. 生成对应标准产物。
4. 按验收条件检查，并把结果写入本地运行清单。
5. 说明尚未完成的检查和最少必要输入。
6. 只有涉及高判断事项时，才询问用户是否需要 MAI 人工复核。
