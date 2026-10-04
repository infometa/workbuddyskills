---
version: 1.0.13
name: ai-due-diligence-workflow-map
display_name: AI尽调·技能地图
display_name_en: AI Due Diligence · Workflow Map
description: Use when the user asks for an overview/index of the AI尽调 skill suite, wants to know which AI due-diligence skill to use for a given step (建档/材料/画像/报告/售前), or asks 有哪些AI尽调技能/怎么归类/用什么技能做XX. Provides the full lifecycle map and skill classification.
description_zh: AI尽调技能总览索引：按生命周期（建档/材料/画像/报告/售前）展示技能地图，引导使用对应技能。
description_en: AI DD Workflow Map — lifecycle overview and skill classification index to route users to the right skill.
category: finance
author: 腾讯金融云
permissions: [sandbox, file-read-write]
skill_type: index
priority: P1
requires_sandbox: false
agent_created: true
---

## 打开 embed 页面（重要）

需要通过 `present_files` 打开业务页面时，**不要自己拼 URL**，按下面两步调用：

```
调用工具：create_embed_code
参数 path：/embed/workspace/{projectId}/finance

调用工具：present_files
参数 url：<上一步 create_embed_code 返回的 url>
```

- `path` 只写**站内相对路径**（以 `/embed/` 开头），`{projectId}` 替换为真实项目 ID；**站点域名由服务端决定，禁止自行拼接**。
- `create_embed_code` 返回 `{ url, code, expiresIn }`，**只用返回的 `url`**，不要拿 `code` 自己拼。
- 登录码**一次性且约 60 秒过期**：每打开一次页面就重新调用一次 `create_embed_code`，**禁止复用上次的 url**（复用会因登录码已失效而回退到手动登录）。

- **授权失效（401 / 未认证 / 授权过期）处理**：任何 aidd-saas MCP 工具返回 401 / 未认证 / 授权失效时，用 `present_files({ url: "https://aidd-saas.txfc.cloud/guide/mcp-guide.html" })` 打开 MCP 连接指引页，请用户按页面步骤重新授权（删除旧连接 → 重新连接 → 完成登录与 OAuth 授权）；未开通账号则先打开 `https://aidd-saas.txfc.cloud/guide/auth-guide.html` 引导注册。禁止在回复里输出裸相对路径。

# AI 尽调技能地图（总览索引）

## 概述

AI 尽调工作流的技能总览索引。当用户询问"AI 尽调有哪些技能""这个步骤用什么技能""技能怎么归类"时，按本索引定位并引导到对应技能；当用户发起具体任务时，直接加载对应技能执行。

## 主流程（按项目生命周期）

```
建档 → 材料 → 画像 → 报告 → 售前/交付
```

| 步骤              | 技能                                                                                                                            | 职责                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 0. 打开工作台     | `dd-full-process`                                                                                                               | 右侧预览面板打开 AI 尽调助手工作区（总控第 0 轮承接）                                                   |
| 1. 企业档案建档   | `ai-due-diligence-enterprise-record`                                                                                            | 录入/修正/更换尽调对象企业档案（AskUserQuestion 引导 + 覆盖写回）                                       |
| 2. 材料与财务数据 | `ai-due-diligence-material-organizer`                                                                                           | 进件材料整理、备份、批量重命名                                                                          |
| 2b. 财务分析      | `dd-financial-analysis`                                                                                                         | 基于进件材料 + 公开披露生成可追溯财务分析                                                               |
| 2c. 行业分析      | `dd-industry-analysis`                                                                                                          | E0 行业定位 + E1-E8 行业分析 + 行业专项报告（MD/DOCX），基于进件材料 + 联网搜索，脚本计算 CAGR/CR5/分位 |
| 3. 企业画像分析   | `dd-profile-analysis`                                                                                                           | 12 分段画像即时推送 + risks 风险要点（表格形态）+ 企业画像专项报告（MD/DOCX 版本化保存）                |
| 4. 尽调报告       | `bank-credit-due-diligence-report-expert`                                                                                       | 本地进件材料 → 银行送审尽调报告                                                                         |
| 5. 售前交付物     | `ai-due-diligence-business-interpretation-ppt`<br>`ai-due-diligence-ppt-from-matrix`<br>`ai-due-diligence-cost-estimation-xlsx` | 业务解读售前 PPT / 信息矩阵转 PPT / 工作量造价评估                                                      |

## 本项目 dd-* 技能对照（aidd-saas 内置技能库）

以下为本项目 `skills/` 实际内置的 dd-* 技能及对应流程步骤，供在本项目内定位技能使用：

| 步骤          | 技能                                                                                                                                                                           | 职责                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| S1 项目管理   | `dd-project-manager`                                                                                                                                                           | 项目查询/搜索/创建/信息维护                                                  |
| S2 进件管理   | `dd-intake-manager`<br>`dd-intake-recognition`<br>`dd-intake-preprocess`                                                                                                       | 进件材料管理 / 文档扫描识别 / 材料预处理                                     |
| S3 财务核验   | `dd-finance-verify`                                                                                                                                                            | P0 三表标准化 + P1 三表勾稽核验                                              |
| S4 专项分析   | `dd-profile-analysis`<br>`dd-financial-analysis`<br>`dd-business-analysis`<br>`dd-industry-analysis`<br>`dd-access-analysis`<br>`dd-cashflow-analysis`<br>`dd-credit-analysis` | 企业画像 / 财务分析 / 经营分析 / 行业分析 / 准入分析 / 现金流分析 / 征信分析 |
| S5 全流程总控 | `dd-full-process`                                                                                                                                                              | 全流程编排（新手引导 + 人机审阅 + 风险总览委托）                             |
| S6 风险       | `dd-risk-overview`<br>`dd-risk-analysis`                                                                                                                                       | 跨维度风险总览 / 风险审查                                                    |
| S7 报告       | `dd-report`<br>`dd-polish`<br>`dd-credit-scheme`                                                                                                                               | 报告撰写 / 报告润色 / 授信方案                                               |
| 入口          | `ai-due-diligence-open-workspace`                                                                                                                                              | 打开 AI 尽调助手工作区                                                       |

## 支撑与研究类（不直接跑项目，产出标准/模板/需求）

| 分组      | 技能                                                  | 职责                                                               |
| --------- | ----------------------------------------------------- | ------------------------------------------------------------------ |
| 报告研究  | `ai-due-diligence-real-report-outline-builder`        | 逐份学习真实尽调报告 → 沉淀"撰写大纲要求"文档                      |
| 报告标准  | `ai-due-diligence-report-type-standard-research`      | 综合研究 → 报告类型标准 + 企业名称→模板匹配索引                    |
| 策略模板  | `ai-due-diligence-strategy-template-optimizer`        | 优化 S 系列策略模板 JSON（原文直读、无 KV 依赖）                   |
| Demo/导入 | `ai-due-diligence-demo-sop`                           | Demo 项目 SOP：材料准备、KV 模板命名、系统导入 JSON 规则、验证交接 |
| 需求池    | `ai-due-diligence-system-requirements-pool`           | 系统操作反馈 → PRD 式版本化需求池                                  |
| 产品基线  | `ai-due-diligence-dual-product-requirements-baseline` | SaaS 版与 WorkBuddy 专家团版共性需求基线                           |
| 专家蓝图  | `ai-due-diligence-expert-blueprint-builder`           | WorkBuddy 专家蓝图设计                                             |

## 周边关联（非 AI 尽调专属，场景内复用）

| 技能                                      | 场景                              |
| ----------------------------------------- | --------------------------------- |
| `pptx-ooxml-terminology-revision`         | 既有 PPT 的 R/S/K 术语业务化修订  |
| `bank-architecture-diagram-html-ppt`      | 银行客户架构图 HTML/PNG/PPTX      |
| `pptx-ooxml-speaker-notes-preserve-media` | 含视频/媒体 PPTX 批量写演讲者备注 |

## 边界与重叠核查结论（2026-08 归类）

1. **demo-sop vs system-requirements-pool：无实质重叠**。demo-sop 负责"做 Demo + 导入真实系统（KV 模板 JSON、导入规则）"，requirements-pool 负责"收集 Demo/真实系统反馈 → 写 PRD 式需求"。两者一执行一沉淀，仅在涉及 Demo 系统时易混；如触发歧义，按"是否产出需求文档"分流。
2. **bank-credit-due-diligence-report-expert vs real-report-outline-builder vs report-type-standard-research：生产/研究分离**。report-expert 是"生产送审报告"（执行态）；outline-builder 是"逐份沉淀大纲"（研究态）；standard-research 是"综合标准研究"（研究态，消费 outline 成果）。三者不合并；标准研究产出可反哺报告专家。
3. **命名统一**：建档与画像两个运行态技能已统一为 `ai-due-diligence-*` 前缀，与既有系列一致。

## 使用规则

- 用户问"怎么归类/有哪些技能" → 直接展示本地图，不改动文件
- 用户发起具体任务 → 按本地图加载对应技能执行
- 任务跨步骤（如"从建档到出报告"）→ 按主流程顺序依次加载对应技能，步骤间衔接信息见各技能"与其他技能衔接"章节
