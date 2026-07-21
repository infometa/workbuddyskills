# JD 关键词分类词典（Keyword Taxonomy）

> 用于 `scripts/parse_jd.py` 的关键词抽取与权重计算。
> 结构：`category × role_family × keyword → {weight, aliases, category_tag}`。
> 权重区间 `[0.1, 1.0]`，越靠近 1.0 越不可替代。

## 类别总览

| 类别 | 中文名 | 权重区间 | 说明 |
|---|---|---|---|
| `hard_skills` | 硬技能 | 0.7-1.0 | 编程语言 / 框架 / 工具 / 具体方法论（SQL / React / A/B Test）|
| `industry_terms` | 行业术语 | 0.5-0.9 | 领域专有概念（LLM 微调 / 用户留存 / GMV）|
| `soft_skills` | 软技能 | 0.3-0.5 | 沟通 / 协作 / leadership（英文简历慎用，中文酌情）|
| `seniority_markers` | 职级标记 | 0.4-0.7 | "主导" / "owner" / "lead" —— 触发 Provenance 警告 |
| `company_culture` | 公司文化词 | 0.1-0.3 | "字节范" / "狼性" —— **不写入简历 bullet**，仅用于了解 |

## role_family 分类

| role_family | 覆盖岗位 |
|---|---|
| `tech` | 研发 / 算法 / 数据 / 测试 / 运维 / 架构 |
| `biz` | 产品 / 运营 / 市场 / 商务 / 战略 / 咨询 |
| `design` | UI / UX / 交互 / 视觉 / 游戏美术 |
| `ops` | HR / 财务 / 法务 / 行政 / 供应链 |

---

## tech × hard_skills（权重 0.7-1.0）

### 编程语言

| keyword | weight | aliases | 子类 |
|---|---:|---|---|
| `python` | 0.95 | Python, py | language |
| `java` | 0.95 | Java | language |
| `golang` | 0.9 | Go, Goland, Golang | language |
| `c++` | 0.9 | cpp, C++, CPP | language |
| `typescript` | 0.85 | TypeScript, ts | language |
| `javascript` | 0.85 | JavaScript, js | language |
| `rust` | 0.85 | Rust | language |
| `sql` | 0.9 | SQL | language |
| `kotlin` | 0.8 | Kotlin | language |
| `swift` | 0.8 | Swift | language |
| `scala` | 0.75 | Scala | language |

### 前端框架

| keyword | weight | aliases |
|---|---:|---|
| `react` | 0.9 | React, React.js, ReactJS |
| `vue` | 0.85 | Vue, Vue.js, VueJS |
| `angular` | 0.75 | Angular |
| `nextjs` | 0.85 | Next.js, NextJS |

### 后端/系统

| keyword | weight | aliases |
|---|---:|---|
| `springboot` | 0.9 | Spring Boot, SpringBoot |
| `django` | 0.85 | Django |
| `flask` | 0.8 | Flask |
| `fastapi` | 0.85 | FastAPI, fast-api |
| `grpc` | 0.8 | gRPC, grpc |
| `kafka` | 0.85 | Kafka, Apache Kafka |
| `redis` | 0.85 | Redis |
| `mysql` | 0.85 | MySQL |
| `postgresql` | 0.8 | Postgres, PostgreSQL, pg |
| `mongodb` | 0.75 | Mongo, MongoDB |
| `elasticsearch` | 0.75 | ES, Elastic, Elasticsearch |

### 大数据/数据工程

| keyword | weight | aliases |
|---|---:|---|
| `spark` | 0.9 | Spark, Apache Spark, PySpark |
| `flink` | 0.9 | Flink, Apache Flink |
| `hadoop` | 0.75 | Hadoop |
| `hive` | 0.8 | Hive |
| `airflow` | 0.8 | Airflow, Apache Airflow |
| `dbt` | 0.7 | dbt, DBT |
| `clickhouse` | 0.8 | ClickHouse, CK |

### 云/基础设施

| keyword | weight | aliases |
|---|---:|---|
| `kubernetes` | 0.9 | k8s, Kubernetes, K8S |
| `docker` | 0.85 | Docker |
| `aws` | 0.9 | AWS, Amazon Web Services |
| `gcp` | 0.8 | Google Cloud, GCP |
| `azure` | 0.8 | Azure, Microsoft Azure |
| `terraform` | 0.8 | Terraform |
| `ci_cd` | 0.75 | CI/CD, CICD, CI\\CD |

### AI/ML

| keyword | weight | aliases |
|---|---:|---|
| `pytorch` | 0.95 | PyTorch, torch |
| `tensorflow` | 0.85 | TensorFlow, TF |
| `llm` | 0.95 | LLM, 大模型, 大语言模型 |
| `transformer` | 0.9 | Transformer, transformers |
| `rag` | 0.9 | RAG, 检索增强生成 |
| `fine_tuning` | 0.9 | 微调, finetuning, SFT, LoRA |
| `rlhf` | 0.85 | RLHF, 强化学习人类反馈 |
| `prompt_engineering` | 0.75 | 提示词工程, Prompt Engineering |
| `agent` | 0.85 | Agent, 智能体, AutoGPT, LangChain |
| `langchain` | 0.8 | LangChain, langchain |
| `vector_db` | 0.8 | 向量数据库, Vector DB, Pinecone, Milvus, FAISS |

### 测试/工程方法

| keyword | weight | aliases |
|---|---:|---|
| `unit_test` | 0.75 | 单元测试, unit test, UT |
| `ab_test` | 0.9 | A/B Test, AB测试, ABTest |
| `code_review` | 0.65 | Code Review, CR |

---

## tech × industry_terms（权重 0.5-0.9）

| keyword | weight | aliases | 说明 |
|---|---:|---|---|
| `高并发` | 0.9 | high concurrency, 高并发场景 | 后端岗必备 |
| `分布式系统` | 0.85 | distributed system, 分布式 | 后端/系统岗 |
| `微服务` | 0.8 | microservice, 微服务架构 | 后端 |
| `qps` | 0.85 | QPS, 每秒查询数 | 性能指标 |
| `p99` | 0.8 | P99, P99延迟, 99分位 | 性能指标 |
| `sla` | 0.7 | SLA, 服务等级协议 | 基础设施 |
| `模型训练` | 0.85 | model training | AI |
| `模型部署` | 0.85 | model deployment, 模型上线, inference | AI |
| `推荐系统` | 0.9 | recommendation system, RecSys | 算法 |
| `搜索排序` | 0.85 | search ranking, LTR | 算法 |
| `广告系统` | 0.85 | ad system, 广告投放 | 算法 |
| `nlp` | 0.85 | NLP, 自然语言处理 | 算法 |
| `cv` | 0.85 | CV, 计算机视觉, Computer Vision | 算法 |

---

## biz × hard_skills（权重 0.7-1.0）

### 产品/数据分析

| keyword | weight | aliases |
|---|---:|---|
| `sql` | 0.95 | SQL | 数据必备 |
| `excel` | 0.75 | Excel, 数据透视表 |
| `tableau` | 0.8 | Tableau |
| `powerbi` | 0.75 | Power BI, PowerBI |
| `ab_test` | 0.95 | A/B Test, AB测试 |
| `axure` | 0.75 | Axure |
| `figma` | 0.75 | Figma |
| `墨刀` | 0.7 | 墨刀, MockingBot |
| `产品文档` | 0.85 | PRD, MRD, BRD, 产品需求文档 |

### 运营工具

| keyword | weight | aliases |
|---|---:|---|
| `裂变增长` | 0.85 | growth hacking, 增长黑客 |
| `私域运营` | 0.85 | 私域, 社群运营 |
| `抖音小店` | 0.8 | 抖店, TikTok Shop |
| `淘宝后台` | 0.7 | 千牛, 生意参谋 |

---

## biz × industry_terms（权重 0.5-0.9）

| keyword | weight | aliases | 说明 |
|---|---:|---|---|
| `用户增长` | 0.9 | user growth, UG | 产品/运营 |
| `用户留存` | 0.9 | retention, 留存率 | 产品/运营 |
| `daily_active_user` | 0.85 | DAU, 日活 | 产品 |
| `monthly_active_user` | 0.85 | MAU, 月活 | 产品 |
| `gmv` | 0.9 | GMV, 成交额 | 电商 |
| `ltv` | 0.85 | LTV, 用户生命周期价值 | 运营 |
| `cac` | 0.85 | CAC, 获客成本 | 运营 |
| `roi` | 0.8 | ROI, 投资回报率 | 通用 |
| `转化率` | 0.9 | conversion rate, 转化漏斗 | 产品/运营 |
| `冷启动` | 0.75 | cold start | 产品 |
| `okr` | 0.65 | OKR, 目标与关键结果 | 管理 |

---

## soft_skills（权重 0.3-0.5，**英文简历慎用**）

| keyword | weight | aliases | ⚠️ 简历使用规则 |
|---|---:|---|---|
| `团队协作` | 0.4 | teamwork, collaboration | 中文可用，英文避免直说，应用动词体现 |
| `沟通能力` | 0.4 | communication | 同上 |
| `主动性` | 0.4 | proactive, self-motivated | 英文可用 proactive 形容动作 |
| `学习能力` | 0.3 | learning agility, fast learner | 中英避免直说，用"X 周掌握 Y"体现 |
| `抗压能力` | 0.3 | work under pressure | **英文禁用**（文化冲突）|
| `吃苦耐劳` | 0.2 | — | **英文禁用**（法规风险）|
| `服从安排` | 0.2 | — | **中英都避免**（显得没主见）|
| `leadership` | 0.5 | 领导力, 带团队 | 通用，需 Provenance 审核（是否真带过团队）|
| `ownership` | 0.5 | 主人翁精神, 担当 | 英文职场标准词 |

---

## seniority_markers（权重 0.4-0.7，**触发 Provenance 警告**）

凡是这些词被 AI 加入 bullet 但用户原始素材没有 → 必须标记 `hallucination_risk: "high"`。

| keyword | weight | 警告级别 | 原因 |
|---|---:|:---:|---|
| `主导` | 0.7 | ⚠️ high | 是否"主导"需用户确认 |
| `负责` | 0.5 | ⚠️ medium | 程度模糊 |
| `参与` | 0.4 | ✅ low | 最保守表述 |
| `lead` | 0.7 | ⚠️ high | 同"主导" |
| `own` | 0.7 | ⚠️ high | 同"主导" |
| `drive` | 0.6 | ⚠️ medium | 需核实 |
| `optimize` | 0.5 | ⚠️ medium | 需有量化 |
| `architect` | 0.8 | ⚠️ high | 职称级别用词 |
| `从 0 到 1` | 0.7 | ⚠️ high | 是否真的从 0 构建 |

---

## company_culture（权重 0.1-0.3，**不写入 bullet**）

这些词仅用于理解 JD 风格，**不进简历 bullet**。

| keyword | weight | 说明 |
|---|---:|---|
| `字节范` | 0.2 | 字节跳动文化词 |
| `狼性` | 0.2 | 华为类文化词 |
| `拼搏` | 0.2 | 创业公司风格 |
| `技术驱动` | 0.3 | 技术型公司 |
| `客户第一` | 0.3 | 阿里类文化 |

---

## 匹配规则（parse_jd.py 实现）

1. **大小写不敏感匹配**：`Python` == `python` == `PY`
2. **中英文 aliases 匹配**：`LLM` 命中 `llm` 同时命中 `大模型`
3. **权重聚合**：同一 keyword 多次出现只记一次，权重不翻倍
4. **role_family 推断**：
   - 从 JD 标题关键词（如"算法工程师" / "产品经理" / "UI 设计师"）先判断
   - 若标题不明确 → 看 hard_skills 命中分布（tech 词汇 > 50% → `tech`）
5. **覆盖率计算**：
   ```
   coverage = sum(weight_i for i in matched_keywords) / sum(weight_i for i in jd_keywords)
   ```

## 扩展

- v0.2 计划增加 `design` 和 `ops` 族的详细词典
- v0.3 计划加入英文 JD 专用词典（与中文词典分开）
- v1.0 词典从 Markdown 迁移为 YAML/JSON 以便脚本直接 import
