# 可用能力目录

本文档列出系统当前具备的全部流程能力，供总控专家判断能力可用性。

## 项目管理能力

| 能力         | 对应 Skill         | 对应 MCP 工具                                   |
| ------------ | ------------------ | ----------------------------------------------- |
| 项目查询     | dd-project-manager | `list_projects`, `get_project`                  |
| 项目创建     | dd-project-manager | `create_project`, `update_project_company_info` |
| 企业搜索     | dd-project-manager | `search_company`                                |
| 流程状态推进 | 总控专家           | `update_project_stage`                          |

## 进件管理能力

| 能力         | 对应 Skill                                 | 对应 MCP 工具                                       |
| ------------ | ------------------------------------------ | --------------------------------------------------- |
| 上传材料     | dd-intake-manager / dd-intake-preprocess   | `create_intake_file_upload_url`, `save_intake_file` |
| 材料列表     | dd-intake-manager                          | `get_intake_files`, `get_intake_file`               |
| 材料内容     | dd-intake-manager                          | `get_intake_file_content`                           |
| 材料识别     | dd-intake-recognition                      | `update_intake_file_info`, `list_intake_tags`       |
| 材料删除     | dd-intake-manager                          | `delete_intake_file`                                |
| 材料重解析   | dd-intake-manager                          | `reparse_intake_file`                               |
| 进件总结     | dd-intake-recognition / dd-access-analysis | `save_intake_summary`                               |
| 准入风险评估 | dd-access-analysis                         | `save_intake_summary` (accessRisk)                  |

## 财务核验能力

| 能力           | 对应 Skill                                | 对应 MCP 工具                                     |
| -------------- | ----------------------------------------- | ------------------------------------------------- |
| 财务核验上下文 | dd-finance-verify                         | `get_finance_workflow_context`                    |
| 财务核验详情   | dd-finance-verify                         | `get_finance_run`                                 |
| 发起财务核验   | dd-finance-verify                         | `create_finance_run`                              |
| 标准化确认  | dd-finance-verify                         | `confirm_finance_p0`                              |
| P1 三表修订    | dd-finance-verify                         | `save_finance_p1_draft`, `recalculate_finance_p1` |
| P1 提交        | dd-finance-verify                         | `submit_finance_p1`                               |
| P4 行业基准    | dd-finance-verify / dd-financial-analysis | `resolve_finance_p4_benchmark`（自动，仅需 runId）；`confirm_finance_p4_industry`（人工纠偏，一般不用） |

## 专项分析能力

| 能力         | 对应 Skill            | 对应 MCP 工具                             | 依赖         |
| ------------ | --------------------- | ----------------------------------------- | ------------ |
| 企业画像分析 | dd-profile-analysis   | `save_profile_data`, `get_profile_data`   | 进件材料     |
| 财务分析     | dd-financial-analysis | `get_finance_data`                        | 财务核验完成 |
| 经营分析     | dd-business-analysis  | `save_business_data`, `get_business_data` | 进件材料     |
| 行业分析     | dd-industry-analysis  | `save_industry_data`, `get_industry_data` | 在线信源开启 |

## 专项报告能力

| 能力         | 对应 Skill            | 对应 MCP 工具                                  |
| ------------ | --------------------- | ---------------------------------------------- |
| 画像专项报告 | dd-profile-analysis   | `get_profile_reports`, `save_profile_report`   |
| 经营专项报告 | dd-business-analysis  | `get_business_reports`, `save_business_report` |
| 行业专项报告 | dd-industry-analysis  | `get_industry_reports`, `save_industry_report` |
| 财务专项报告 | dd-financial-analysis | `get_project_finance_reports`, `save_finance_report`, `search_templates`, `get_report_template` |
| 报告文件上传 | 所有报告 Skill        | `create_report_upload_url`                     |

## 最终报告能力

| 能力           | 对应 Skill | 对应 MCP 工具                                                |
| -------------- | ---------- | ------------------------------------------------------------ |
| 创建报告占位   | dd-report  | `create_report`                                              |
| 标记生成中     | dd-report  | `mark_report_generating`                                     |
| 提交报告       | dd-report  | `submit_report`                                              |
| 标记失败       | dd-report  | `mark_report_failed`                                         |
| 报告状态查询   | dd-report  | `get_report_status`                                          |
| 拉取各维度数据 | dd-report  | `get_profile_data`, `get_business_data`, `get_industry_data` |

## 模板管理能力

| 能力         | 对应 Skill | 对应 MCP 工具                                    |
| ------------ | ---------- | ------------------------------------------------ |
| 历史模板     | dd-report  | `get_last_report_template`                       |
| 搜索模板     | dd-report  | `search_templates`                               |
| 模板列表     | dd-report  | `list_report_templates`, `get_enabled_templates` |
| 模板详情     | dd-report  | `get_report_template`                            |
| 创建模板     | dd-report  | `create_report_template`                         |
| 模板状态切换 | dd-report  | `toggle_template_status`                         |

## 联网搜索能力（受项目在线信源开关控制）

| 能力              | 对应 MCP 工具         | 信源字段                       |
| ----------------- | --------------------- | ------------------------------ |
| WSA 独立搜索      | `web_search`          | `onlineSources.webSearch`      |
| TokenHub 模型搜索 | `web_search_enhanced` | `onlineSources.tokenhubSearch` |
| 企业库查询        | `search_company`      | `onlineSources.horae`          |

> `onlineSources` 字段为 `null` 时视为全部开启。
