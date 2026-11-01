# 阶段表：本轮允许做什么


仅在固定循环需要判断阶段或发布时读取。以本轮 CLI 字段和 nextActions 为准；问答 payload 只查 interactions.md，等待只查 state-and-recovery.md。

正常顺序：**需求问卷 → 风格预览与选择 → CLI 静默生成并确认研发规划 → 展示功能清单并由用户选择 → 研发 → 本轮成果 → 按授权代码审查 / 自动测试 / 安全扫描 / 继续创作 / 上线运营**。发布成功且站点已公开后，再按 [扩展能力](extend.md) 提供接入引导。

已有项目的运营请求从 [运营方法](operations.md) 进入：原样转交、对话、等待，由 superun 访问数据库执行，不重走新建流程。运营轮完成时展示本轮结果，不因返回中保留历史 development 字段而套用研发完成菜单；实际未决交互仍按固定循环处理。

## 从上到下匹配当前阶段

| 当前事实 | 展示/动作 | 下一步 |
|---|---|---|
| autoTest / codeReview | 优先按 [质量检查](quality-checks.md) 展示当前报告及遗留问题，不套用普通研发完成菜单 | 条件满足才展示/执行 nextActions.when 对应动作；检查完成不等于通过 |
| securityReview | 按 [扩展能力](extend.md) 展示本次扫描与报告摘要，不套用普通研发完成菜单 | 按实际报告给“继续创作 / 自动测试 / 上线运营”；报告失败只在用户要求后重试 |
| agentFriendly | 同一文档：`READY` 只问一次接入方式，`INSTRUCTIONS` 在一个文本代码块里原样展示所选原文 | 不自动选、不安装；展示原文后再给三项接入引导 |
| PRD_CLARIFICATION | 完整问卷，用已有答案补已知项；缺失项交用户 | 答齐提交，CLI 自动生成风格，不再问是否生成 |
| 风格仍生成 | 每个新就绪 previewUrl 立即打开；保留本批 choiceId 与 A/B/C/D | 按固定循环等待剩余候选；不代选、不重试生成、不拿历史批次补位 |
| NEEDS_SELECTION | 展示本批可用页面和失败项，让用户选择 | 提交真实 choiceId；CLI 静默整理功能清单 |
| stylePlanning | 只提示“已采用方案 B，正在整理开发功能清单”，用实际方案名称；真实问题和错误仍须处理 | 继续 chat wait，由 CLI 核验并自动确认本次规划；不展示过渡 demo/规划或查看演示/开始研发/确认规划入口，不在宿主手工 APPROVE |
| 独立 PLAN_REVIEW（非 stylePlanning） | 按 messages 顺序展示当前规划原文，不额外重复附件 README；给确认/调整入口 | 明确确认才 APPROVE；调整原文走 send，等新方案再确认，不批准旧方案 |
| FEATURE_SELECTION，且没有 development.previewUrl 或兼容旧结果 | 功能清单按 CLI 顺序展示全部“编号＋完整功能名称”，详细说明按需展开，保留编号到真实 ID；只收用户选项或具体需求，不追加上线引导 | 选项走 SELECT；具体需求原文走 send。确认规划不等于全选 |
| EXECUTION_REVIEW / START_EXECUTION | 仅在 CLI 实际返回时展示当前执行计划 | 用户明确决定后按 schema EXECUTE，不强加额外确认 |
| development.previewUrl 或研发完成引导（无检查上下文） | 展示本轮原始结果；按 [全部端入口](project-links.md) 交付 development.routing 的完整端列表，单端直接“查看预览”、多端逐项展示并引导进入；旧结果用 previewUrl，缺失时说明缺口 | 给“代码审查 / 自动测试 / 安全扫描 / 继续创作 / 上线运营”入口；即使仍有 SELECT_FEATURES，也不退回首次强制选功能 |

stylePlanning 遇到唯一 APPROVE_ARCHITECTURE_PLAN 且允许 APPROVE 时是 CLI 内部续等点，即使 state=NEEDS_INPUT 也继续 chat wait，不弹规划审批；其他实际业务交互仍交用户。功能清单必须展示并等待用户选择。独立规划调整仍按原确认流程。

用户直接提出开发或修改要求时保留原文，不强迫先选推荐功能。完成阶段的功能清单只供参考；只有用户明确选择才提交 SELECT。所有提交后都回到固定循环读取新结果。

## 仅处理实际出现的旧演示流程

这些分支不适用于 stylePlanning：

| 当前事实 | 动作 |
|---|---|
| 实际返回 ENTER_IDEATION | 按当前交互处理；新建不要自己加这一步 |
| COMPLETED + demo.viewed=false | 展示当前 messages 中完整使用场景及说明，询问是否查看演示；缺失内容不编造 |
| demo.viewed=true 或 development.stage=READY | 打开本轮 demo.url，展示“修改演示 / 进入研发”；没有 URL 就说明暂缺，不使用旧地址 |
| 用户修改演示 | 原文提交，等本轮结果，不自动进入研发 |
| 用户要求进入研发 | 执行当前 develop 入口；实际前置条件由 CLI 检查，不改写阶段标记 |

自动记录 viewed 不证明用户已阅读。研发主线使用 CLI 返回的稳定 previewUrl，不查找或等待快照；规划轮不要求预览。旧结果中的 development.snapshot 仅供兼容解释，不能让新版重新走快照等待。预览不证明已部署。

## 用户明确要求上线时

1. `chat publish status <sessionId> --for-launch` 取得最新待发布版本，保存 encryptedId 和提交前 updatedAt。
2. 原样展示该版本 changeLog。未部署则按 nextActions start 并沿用 --for-launch；已在部署则只跟踪该版本。没有可发布版本就说明并停止本次发布。
3. 读取同一版本部署记录。成功后尚未公开时，沿用上线授权执行 visibility public，不重复问是否发布。
4. 按 [交付核对](delivery.md) 验证正式入口，原样展示 changeLog，按 [全部端入口](project-links.md) 展示 publish.routing 的所有正式入口及单端/多端继续创作引导；旧结果兼容 publish.publishUrl。已部署且已公开时，按 [扩展能力](extend.md) 与继续创作并列提供接入入口。

普通 status 查询不产生发布授权；没有上线要求不进入本节。--for-launch 只表达已有授权，额外费用仍须匹配用户授权。

发布成功结果另有 `ADVANCED_DESIGNER_POLISH` 时，保留上述全部交付与原有选项，再追加「高级设计师」入口，按 [发布后高级设计师](extend.md#发布后高级设计师调整页面或重新设计) 收集要求并执行 chat design。该入口与风格选择阶段的高级设计师不同，调整或重新设计都不回到风格选择流程。
