# 商机优先级排序（Lead Scoring）

> **两阶段模型**：第一阶段用免费 data.gov.sg 字段评分筛选 → 第二阶段对高潜力 Lead 购买 ACRA 付费数据做尽调。不得因 paid-up capital 缺失停止 Lead Scoring。

---

## 1. 数据来源

| 数据源 | 类型 | 阶段 | 链接 |
|--------|------|------|------|
| data.gov.sg 企业数据 Collection 2（免费） | `[API]` | 第一阶段 | https://data.gov.sg/collections/2/view |
| Collection Metadata API | `[API]` | 第一阶段 | https://api-production.data.gov.sg/v2/public/api/collections/2/metadata |
| ACRA API Marketplace（收费） | `[API]` | 第二阶段 | https://www.acra.gov.sg/resources/eservice-tools-portals/api-marketplace/ |
| ACRA Business Information Products | `[知识库]` | 第二阶段 | https://www.acra.gov.sg/resources/business-information-products |
| ACRA CCFP（含 capital + annual return compliance + 财务指标） | `[知识库]` | 第二阶段 | https://www.acra.gov.sg/resources/eservice-tools-portals/business-information-products-ccfp |
| SSIC 2025 | `[知识库]` | 第一阶段 | https://www.singstat.gov.sg/standard-classifications/national-classifications/singapore-standard-industrial-classification-ssic |

---

## 2. 第一阶段：免费评分（data.gov.sg 字段）

### 2.1 评分维度与权重

| 维度 | 权重 | 评分逻辑 |
|------|------|----------|
| **SSIC 匹配度** | 40% | Primary SSIC 完全匹配目标代码 = 100分；同大类子类匹配 = 70分；Secondary SSIC 匹配 = 40分 |
| **Annual Return / Accounts Due Date 及时性** | 20% | `annual_return_date` 存在且未超过法定截止日期 = 100分；存在但逾期 < 1年 = 60分；逾期 ≥ 1年 = 20分；缺失 = 0分 |
| **企业年龄** | 15% | 注册日期距当前 ≥ 10年 = 100分；5-9年 = 75分；2-4年 = 50分；< 2年 = 25分 |
| **Entity Status** | 10% | Live Company = 100分；Live（其他类型）= 60分；非活跃 = 0分（直接排除） |
| **Officer 数量** | 5% | ≥ 5人 = 100分；3-4人 = 70分；1-2人 = 40分；0人 = 10分 |
| **Audit Firm 信息** | 5% | 有审计事务所记录 = 100分；无记录 = 0分（不扣分，仅加分） |
| **其他主体稳定性** | 5% | 无曾用名 = 100分；1-2条曾用名 = 60分；≥ 3条 = 20分。注册地址为商业地址 = +20附加分 |

### 2.2 最终分数与分级

```
Stage 1 Score = Σ (维度得分 × 权重)
满分 = 100
```

| 等级 | 分数 | 操作 |
|------|------|------|
| **A** | ≥ 75 | 进入第二阶段尽调 |
| **B** | 55-74 | 纳入 pipeline，定期监控 |
| **C** | < 55 | 批量 marketing，不主动一对一出击 |

---

## 3. 第二阶段：付费尽调（针对 A 级企业）

> **仅对评分前 5%—10% 的候选企业执行**。

### 3.1 补充数据源

| 产品 | 包含信息 | 费用 | 链接 |
|------|----------|------|------|
| **ACRA Business Profile** | issued/paid-up share capital、注册地址、股东、董事 | 收费 | https://www.acra.gov.sg/resources/business-information-products |
| **ACRA CCFP** | Business Profile 全部内容 + annual return compliance + 财务指标 | 收费 | https://www.acra.gov.sg/resources/eservice-tools-portals/business-information-products-ccfp |

### 3.2 第二阶段评分补充

| 补充维度 | 数据来源 | 判断 |
|----------|----------|------|
| paid-up share capital | Business Profile / CCFP | ≥ S$100K = 高信号；S$1-S$99K = 正常；S$0 = 需关注 |
| Annual Return 合规历史 | CCFP | 连续 3 年按时提交 = 正面；有缺失 = 负面 |
| 财务指标 | CCFP | 如有 XBRL 财务数据，分析盈利能力/偿债能力 |

> ⚠️ **不得因 paid-up capital 缺失停止第一阶段 Lead Scoring**。第一阶段使用全部免费字段，第二阶段再补充。

---

## 4. 合规趋势判断

| 信号 | 来源 | 逻辑 |
|------|------|------|
| Annual Return 连续 ≥2 年缺失 | `annual_return_date` | 高风险，降级至 C |
| 被 Struck Off 后恢复 | `entity_status` 历史 | 极高风险，直接排除 |
| 长期合规经营 | `annual_return_date` + CCFP | 正面信号，可升级 |

> 趋势判断依赖**月度快照 diff**（详见 `sg-automation-monitoring.md`）。

---

## 5. 实施流程

```
1. data.gov.sg API 筛选 Live Company + 目标 SSIC
2. 第一阶段评分 → 排名
3. Top 5-10% A 级 → 购买 ACRA Business Profile / CCFP
4. 第二阶段评分 → 最终排序 → 触达计划
5. 月度更新快照 → 追踪状态变化
```
