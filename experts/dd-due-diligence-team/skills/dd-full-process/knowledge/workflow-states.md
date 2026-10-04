# 七步流程状态映射

本文档说明如何基于现有 Project 实体字段与 reports 表推断七步流程（S1-S7）状态。

进度条六种状态符号：

- ✓ 已完成 / ● 当前进行中 / ○ 未开始 — 基础状态，由后端持久化字段驱动（见下方「字段说明」）。
- ⚠ 有风险 / ✕ 被阻断 / ⟳ 待重新确认 — 扩展状态，**不落库**，由总控专家在运行时根据当前数据判断后叠加到基础状态之上（见下方「扩展状态」一节）。

## 字段说明

`get_project` 返回以下状态字段：

| 字段                      | 类型                                                     | 说明                        |
| ------------------------- | -------------------------------------------------------- | --------------------------- |
| `progressStage`           | `intaking` / `analyzing` / `report_ready`                | 总体进度阶段                |
| `stage1Status`            | `{ intake, financeVerify }`                              | 一阶段：进件 + 财务核验     |
| `stage2Status`            | `{ profile, finance, business, industry, riskOverview }` | 二阶段：四维分析 + 风险总览 |
| `stage3Status`            | `pending` / `doing` / `done`                             | 三阶段：报告（S7）          |
| `intakeSummary`           | `{ summary, stats, accessRisk }`                         | 进件总结和准入风险          |
| `riskScore` / `riskLevel` | 项目级风险评分                                           | 来自风险评估                |

S5 的状态依据来自 `reports` 表（通过专项报告 MCP 工具查询），不在 `get_project` 返回字段中：

| 报告类型           | reportType 取值      | 查询工具                                      |
| ------------------ | -------------------- | --------------------------------------------- |
| 企业画像专项报告   | `profile-analysis`   | `get_profile_reports`                         |
| 财务分析专项报告   | `financial-analysis` | `get_finance_run` / 财务报告查询              |
| 经营分析专项报告   | `business-analysis`  | `get_business_reports`                        |
| 行业分析专项报告   | `industry-analysis`  | `get_industry_reports`                        |
| 通用尽调报告（S7） | `general`            | `get_last_report_template` / reports 列表查询 |

reports.status 取值：`pending`（待生成）/ `generating`（生成中）/ `done`（已完成）/ `failed`（失败）。

## 七步推断规则

### S1 项目识别与创建

- **判断方式**：project 是否存在
- **完成标志**：`get_project` 能返回数据 → S1 已完成

### S2 进件材料准备

- **判断字段**：`stage1Status.intake`
- **状态映射**：
  - `pending` → S2 ○ 未开始
  - `doing` → S2 ● 进行中
  - `done` → S2 ✓ 已完成
- **补充信息**：`intakeSummary.stats` 可查看材料统计；`intakeSummary.summary` 可查看进件总览；`intakeSummary.accessRisk` 可查看准入风险评估

### S3 财务数据确认与校验

- **判断字段**：`stage1Status.financeVerify`
- **状态映射**：
  - `pending` → S3 ○ 未开始
  - `doing` → S3 ● 进行中
  - `done` → S3 ✓ 已完成
- **有限结论**：P1 以受限材料提交（run `status='limited'`）时 `financeVerify` 仍推进为 `done`，
  材料受限/勾稽差异等风险信号保留在 run.status 与 P1 stage.status 中，由下游分析与报告负责披露
- **补充信息**：通过 `get_finance_run` / `get_finance_workflow_context` 获取财务核验详细进度

### S4 分析任务编排与风险研判

- **判断字段**：`stage2Status`（4 个维度）
- **状态映射**：
  - 每个维度 `pending` / `doing` / `done`
  - `profile` → 企业画像分析
  - `finance` → 财务分析
  - `business` → 经营分析
  - `industry` → 行业分析
- **注意**：`riskOverview` 维度属于 S6 风险总览，不参与 S4 的四维分析判断
- **完成标志**：`done` 表示**用户已确认该维度结论**，不是"AI 已写完数据"。
  分析产出落库后须先展示并取得用户确认，确认后调用 `update_project_stage` 置 `done`（**禁止**重新调用 `save_*_data` 传内容，避免覆盖已落库 section）；
  用户选择「暂不纳入」时回退为 `pending`
- **补充信息**：通过 `get_profile_data` / `get_business_data` / `get_industry_data` / `get_finance_data` 拉取各专项分析结果

### S5 专项报告撰写

- **判断依据**：查询 `reports` 表，按 `reportType` + `status` 逐维度判断
- **状态映射**（每个维度独立）：

  | 状态     | 判定条件（对应 reportType 的最新一条记录）    |
  | -------- | --------------------------------------------- |
  | ○ 未开始 | 无对应 reportType 的记录                      |
  | ● 进行中 | 有记录且 `status` ∈ {`pending`, `generating`} |
  | ✓ 已完成 | 有记录且 `status = done`                      |

- **S5 整体完成标志**：四个专项报告（profile / finance / business / industry）均为 `done`
- **进入条件**：对应维度的 `stage2Status` 为 `done`（分析完成才能生成报告）
- **查询工具**：见上方"字段说明"表中各专项对应的 MCP 工具

> 注意：S5 状态不存入 Project 实体，每次判断都需实时查询 reports 表。`stage3Status` 不用于表达 S5。

### S6 风险总览与综合研判

- **判断字段**：`stage2Status.riskOverview`
- **状态映射**：
  - `pending` → S6 ○ 未开始
  - `doing` → S6 ● 汇总中
  - `done` → S6 ✓ 已确认
- **进入条件**：多数专项分析完成（`stage2Status` 四维分析维度多数为 `done`）或专项报告已生成
- **执行依据**：调用 `get_profile_data` / `get_business_data` / `get_industry_data` 拉取各专项分析结果中的 risks section，在对话中汇总、去重、分级，用 `ask_user_question` 让用户确认
- **完成标志**：用户确认风险总览后，调用 `update_project_stage` 将 `stage2Status.riskOverview` 置为 `done`

> **断点恢复**：`stage2Status.riskOverview` 已持久化。断点恢复时若为 `done` 则视为已确认，跳过重新聚合；否则重新引导用户确认。

### S7 最终报告撰写与定稿

- **判断字段**：`stage3Status` + `progressStage` + reports 表（`reportType=general` 记录）
- **状态映射**：
  - `stage3Status = pending` 且无 general 报告记录 → S7 ○ 未开始
  - `stage3Status = doing` 或有 general 报告记录（status ∈ {pending, generating}）→ S7 ● 进行中
  - `stage3Status = done` 或 `progressStage = report_ready` → S7 ✓ 已完成
- **补充信息**：通过 reports 列表查询 `reportType=general` 的记录状态

## 断点恢复规则

用户说"继续"时，按以下顺序定位断点：

1. 调用 `list_projects` 找到最近更新（`updatedAt` 倒序第一条）的项目
2. 调用 `get_project` 获取完整状态
3. 按优先级检查：
   - `stage1Status.intake ≠ done` → 断点在 S2
   - `stage1Status.financeVerify ≠ done` → 断点在 S3
   - `stage2Status` 四维分析维度（profile/finance/business/industry）任一 `≠ done` → 断点在 S4
   - S5 未全部完成（查询 reports 表，四个专项报告不全是 `done`）→ 断点在 S5
   - `stage3Status ≠ done` 且 S5 已全部完成 → 断点在 S6/S7
     - 若 `stage2Status.riskOverview ≠ done` → 断点在 S6，重新引导风险总览确认
     - 若已有 general 报告记录且 status ∈ {pending, generating} → 断点在 S7 生成中
     - 否则 → 断点在 S7 待生成
4. 给出推荐动作和快捷选项

## 阶段推进

状态推进分三类，**区别在于是否需要用户确认、是否需要显式调用 `update_project_stage`**：

| 完成的动作            | 推进方式                                                                                               | 说明                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| S2 进件材料准备完成   | 自动（`save_intake_summary`）                                                                          | summary + stats 齐备即置 `stage1Status.intake = 'done'`                                                                          |
| S3 财务核验完成       | 自动（`submit_finance_p1`）                                                                            | P1 提交成功（用户已确认）即置 `stage1Status.financeVerify = 'done'`；材料受限（`status='limited'`）仍推进 `done`，限制由下游披露 |
| S4 某维度分析开始     | 显式 `update_project_stage`                                                                            | `stage2Status: { <dimension>: 'doing' }`                                                                                         |
| S4 某维度**用户确认** | 显式 `update_project_stage`（确认只推进状态，**禁止**重新调用 `save_*_data` 传内容覆盖已落库 section） | 置 `<dimension>: 'done'`；未确认前禁止推进 `done`                                                                                |
| S4 某维度用户不采纳   | 显式 `update_project_stage`                                                                            | `stage2Status: { <dimension>: 'pending' }`，不纳入报告                                                                           |
| S5 进入报告阶段       | 显式 `update_project_stage`                                                                            | `stage3Status: 'doing'`                                                                                                          |
| S6 风险总览汇总中     | 显式 `update_project_stage`                                                                            | `stage2Status: { riskOverview: 'doing' }`                                                                                        |
| S6 风险总览确认完成   | 显式 `update_project_stage`                                                                            | `stage2Status: { riskOverview: 'done' }`                                                                                         |
| S7 最终报告定稿       | 自动（`submit_report`）                                                                                | general 报告提交成功即置 `stage3Status = 'done'`                                                                                 |

> - **`update_project_stage` 是增量合并语义**：只传需要变更的字段，未传字段自动保留数据库现值。
>   调用前**无需**为拼全量状态而先查 `get_project`；**禁止**凭对话记忆拼接全量状态（会误覆盖其他维度）。
>   返回值已包含合并后的完整状态，可直接用于展示进度。
>   （红线 2「每次都要读真实状态」依然有效：判断断点与展示进度必须调 `get_project`，
>   这里免掉的只是为拼参数而查原值的多余动作。）
> - **自动推进**的环节产出是确定性的（材料齐备/勾稽通过/报告落库），无需用户拍板；其中 `submit_finance_p1`、`submit_report` 的确认闸门在**调用工具之前**（工具描述已要求执行前向用户确认）。
> - **S4 四维分析**的结论属于语义判断，`complete: true` 即"用户已确认"信号，必须先展示结果并取得确认。
> - **`riskOverview` 没有对应业务工具**，任何时候都只能通过 `update_project_stage` 显式推进。
> - 所有**回退**操作（用户不采纳、结果失效）都必须显式调用 `update_project_stage`。
> - S5 各专项报告的状态由 reports 表记录（`create_report` / `save_*_report` / `submit_report` 写入），不通过 `update_project_stage` 推进。
> - `progressStage` 由后端自动推导，无需显式传入：`stage3Status=done` → `report_ready`；stage1 全 done 或二阶段任一维度非 `pending` → `analyzing`；否则 `intaking`。

## 扩展状态（不落库，由总控专家运行时控制）

⚠ 有风险 / ✕ 被阻断 / ⟳ 待重新确认 三种扩展状态不存入任何后端字段，由总控专家在生成进度条时根据当前数据判断后，叠加到基础状态之上。展示扩展状态时，必须在「当前环节」区说明具体原因。

### ⚠ 有风险

步骤已完成（基础状态为 ✓），但存在需要关注的风险，总控专家用 ⚠ 替代 ✓ 展示。

| 步骤 | 判断依据                                                                                 |
| ---- | ---------------------------------------------------------------------------------------- |
| S2   | `intakeSummary.accessRisk.conclusion` 为 `conditional` 或 `reject`；或材料统计有失败文件 |
| S3   | 财务核验完成但存在未解决勾稽差异（用户选择带风险继续）                                   |
| S4   | 某专项分析结果含高风险项（risks section 中存在 level=high）                              |
| S5   | 某专项报告生成完成但 provenance 标记数据来源不完整                                       |
| S7   | 最终报告已定稿但存在必须披露的缺失数据（如财务数据缺失）                                 |

### ✕ 被阻断

步骤无法继续推进，总控专家用 ✕ 替代 ● 或 ○ 展示，并在「当前环节」区给出阻断原因和可选动作。

| 步骤 | 判断依据                                                |
| ---- | ------------------------------------------------------- |
| S2   | 无任何进件材料，且用户未选择使用公开数据继续            |
| S3   | 财务数据缺失且无法跳过（如用户要求必须核验财务）        |
| S4   | 某维度分析多次失败，无替代数据源                        |
| S5   | 专项报告生成失败（reports.status = failed）且无可用结果 |
| S7   | 最终报告生成失败（general report status = failed）      |

### ⟳ 待重新确认

已完成的步骤因数据变化或用户否定需要重跑，总控专家用 ⟳ 替代 ✓ 展示，并提示需要重新确认的范围。

| 步骤 | 判断依据                                                                                 |
| ---- | ---------------------------------------------------------------------------------------- |
| S3   | 财务 P4 行业基准变更（`resolve_finance_p4_benchmark` 重新获取或 `confirm_finance_p4_industry` 人工覆盖触发），已发布财务报告被标记为 stale |
| S4   | 用户明确否定某专项分析结果（「这个分析结果不对」「重新分析」）                           |
| S5   | 对应专项分析被标记为 ⟳ 后，其专项报告也需重新生成                                        |
| S6   | 风险总览所依赖的专项分析结果发生变化，已确认的风险总览失效                               |

> - S4 用户否定某专项分析结果时，除展示 ⟳ 外，还应将 `stage2Status.<dimension>` 回退为 `'doing'`（要求修改/重新分析）或 `'pending'`（暂不纳入），确保断点恢复时能重新引导确认。
> - S6 风险总览失效时，除展示 ⟳ 外，还应将 `stage2Status.riskOverview` 回退为 `pending`（通过 `update_project_stage`），确保断点恢复时能重新引导确认。

### 断点恢复时的处理

扩展状态不持久化，断点恢复时会丢失。总控专家重新读取基础状态（stage 字段 + reports 表）后，按当前数据重新评估是否需要展示扩展状态：

- 若当前数据仍满足 ⚠ / ✕ / ⟳ 的判断条件 → 重新展示对应扩展状态
- 若条件已不满足（如失败报告已重试成功、被否定的结果已重新生成）→ 按基础状态展示

> 扩展状态丢失不影响数据完整性——风险点在各专项分析结果中、阻断原因在 reports.status 中、失效标记在财务报告 stale 状态中，均可重新读取判断。
