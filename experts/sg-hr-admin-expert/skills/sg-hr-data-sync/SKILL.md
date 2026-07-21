---
name: sg-hr-data-sync
description: Periodically fetch and sync annually-updated Singapore HR data — CPF contribution rates, MOM SOL, COMPASS benchmarks, free salary guides, and key policy pages. Run quarterly or on-demand to keep the HR expert's knowledge current.
user-invocable: false
---

# 新加坡人力数据同步 Skill

定期爬取和比对新加坡人力行政关键数据源，确保专家语料库中引用的费率、清单和政策版本为最新。

## 涵盖数据项

数据按模块分文件存储在 `references/data/`，索引文件为 `references/last_known.json`。Agent 按需读取单个模块，无需加载全部 18 个文件。

| 模块文件 | 数据项 | 更新频率 | 来源 |
|---------|--------|---------|------|
| `work_pass_thresholds.json` | EP/SP 门槛 + COMPASS C1 基准 + C6 SEP | 每年调整 | mom.gov.sg |
| `cpf_rates.json` | CPF 费率 + OW/AW 关键规则 + SDL | 每年1月调整 | cpf.gov.sg |
| `foreign_worker_levy.json` | 5 行业 DRC + Levy | 每年 Budget | mom.gov.sg |
| `leave_entitlements.json` | 法定假期天数 | 随 EA 修订 | mom.gov.sg |
| `personal_income_tax_rates.json` | 12 档累进税率 | Budget 年度 | iras.gov.sg |
| `employment_contract_kets.json` | KETs 字段 + 模板 | MOM 更新 | mom.gov.sg |
| `mom_sol.json` | 紧缺职业清单 | 每年 11 月 | mom.gov.sg |
| `labour_market.json` | 劳动力市场数据 | 每季度 | stats.mom.gov.sg |
| `salary_guides.json` | 免费薪资指南版本 | 每年 3 月/年中 | Hays/Robert Half 等 |
| `portal_links.json` | 官网直达链接 | 随时 | 各官网 |
| `enforcement_references.json` | 违规处罚 + 执法数据 | 持续更新 | MOM/PDPC |
| `office_cost_model.json` | 区域租金 + 启动成本 | 每季度 | URA/CBRE/JLL |
| 其他 6 个模块 | 详见索引文件 | — | 各官网 |

## 参考文献

执行前先读索引文件了解结构：
- `@references/last_known.json` — 模块索引 + 元信息

具体数据按需读取：
- `@references/data/{module}.json` — 18 个独立数据模块

## 工作流

### 执行触发条件

1. **自动触发**：由 Automation 调度，每季度首月 1 号（1/4/7/10 月）执行
2. **手动触发**：用户在专家对话中提示"检查数据更新"或"同步语料库"

### 执行步骤

1. **读索引**：读取 `references/last_known.json` 获取当前所有模块的版本信息
2. **并行爬取**：对每个已更新的数据源运行对应 fetch 脚本，独立请求目标 URL
3. **逐模块比对**：将爬取结果与 `references/data/{module}.json` 中的缓存版本比对
4. **差异报告**：若某模块数据变更，生成差异摘要（变更条目 + 旧值/新值）
5. **按模块更新**：仅覆盖有变更的 `data/{module}.json` 文件（不碰未变更模块）
6. **更新索引**：更新 `last_known.json` 中的元信息时间戳
7. **通知专家**：将差异摘要回传给主对话
### 输出格式

```
【数据同步报告】YYYY-MM-DD

1. {模块名}：{ 无变化 | 已更新：具体变更内容 }
2. {模块名}：{ 无变化 | 已更新：具体变更内容 }
...
N. 索引已更新：{updated_at}
```

## 参考文件结构

```
references/
├── last_known.json          # 模块索引（元信息 + module→file 映射）
└── data/
    ├── work_pass_thresholds.json
    ├── cpf_rates.json
    ├── foreign_worker_levy.json
    ├── leave_entitlements.json
    ├── personal_income_tax_rates.json
    ├── employment_contract_kets.json
    ├── ep_application_checklist.json
    ├── sp_application_checklist.json
    ├── retrenchment_mrn.json
    ├── office_cost_model.json
    ├── wsh_industry_requirements.json
    ├── enforcement_references.json
    ├── china_sg_hr_checklist.json
    ├── industry_salary_ep_benchmarks.json
    ├── portal_links.json
    ├── mom_sol.json
    ├── labour_market.json
    └── salary_guides.json
```

## 注意事项

- 脚本仅爬取公开数据，不涉及登录或付费内容
- **按模块独立更新**：仅覆盖有变更的 `data/{module}.json`，不碰未变更模块，降低合规风险
- Agent 按需读取单个模块（如只读 `cpf_rates.json` 解决 CPF 问题），无需加载全部 18 个文件
- 爬取频率需尊重目标网站的 robots.txt 和服务条款
- 若某源连续3次无法访问，在报告中标记为"不可达"并建议手动核查
- 差异报告中的内容需人工审核后更新到 Agent MD 中——自动更新有引入错误数据的风险
