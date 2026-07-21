---
name: egypt-marketing-skill
description: 埃及市场营销CMO级专家语料库。包含17份核心语料（~110K字符），覆盖埃及数字生态、消费者文化、社交媒体策略、斋月营销、品牌本地化、消费者心理学、数据分析ROI、竞品情报、危机管理、全渠道增长。当用户询问埃及市场营销相关问题时，自动激活本语料库进行优先检索。
---

# 埃及市场营销语料库

## 🚨🚨🚨 语料库优先 — 双轮暴力检索铁律 (CORPUS-FIRST MANDATE)

> **底线原则：质量压倒一切。Token 成本不是你需要考虑的事情——Agent 的质量越高，消耗的资源越多是天经地义的。负责人要的是质量，不是性价比。宁可多查三遍也不能漏掉一行数据。**

### ⚡ 强制检索流程（每条回答必须按序执行，不可跳步）

```
┌──────────────────────────────────────────────────────────────────┐
│  STEP 0: 接收用户问题                                             │
│     ↓                                                             │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  PASS 1 — 宽搜                                                ║ │
│  ║  根据触发矩阵确定 3-5 个文件，读目录/标题索引，记录发布日期       ║ │
│  ║  digital_2024_egypt.txt 永远是基线                                ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│     ↓                                                             │
│  ╔══════════════════════════════════════════════════════════════╗ │
│  ║  PASS 2 — 深读                                                ║ │
│  ║  命中章节完整读，至少 3 份不同来源交叉印证                       ║ │
│  ╚══════════════════════════════════════════════════════════════╝ │
│     ↓                                                             │
│  STEP 3: 判断本地语料是否充足                                      │
│     → 充足 → 基于 PASS 1+2 结果输出回答                            │
│     → 不足 → 进入 STEP 4                                           │
│     ↓                                                             │
│  STEP 4: 降级 — 定向搜索 → 通用搜索（C级可信度）                  │
└──────────────────────────────────────────────────────────────────┘
```

### 🔴 铁律细则

1. **双轮 Reference_Texts 强制读取**：PASS 1 宽搜扫 3-5 个文件 + PASS 2 深读命中的章节。**只读一轮 = 违规。**
2. **🎯 强制语料覆盖率：每条回答应尽可能多使用 Reference_Texts，简单事实性问题至少 3 份，复杂分析/方案类问题建议 5-8 份。回答底部必须列出具体使用了哪些文件及对应章节。**
3. **至少 3 份文本交叉验证**：任何结论必须从至少 3 份不同来源的 Reference_Texts 中交叉印证。单一文件不可信。
4. **digital_2024_egypt.txt 永远基线**：无论什么问题，PASS 1 必须读取 digital_2024_egypt.txt。它是所有埃及问题的基础背景。
5. **网络搜索是最后手段**：本地两遍 PASS 都无覆盖 → 才允许上网。**禁止跳过任何一轮 PASS 直接上网。**
6. **禁止使用训练数据输出数字**：任何具体数字必须从本地语料库中提取，严禁从 LLM 训练数据中编造。
7. **数据时效标注**：从语料库提取数据时，在来源引用中标注文件发布时间和距今月份。格式：`（发布于{年月}，距今{月}个月）`。超过 12 个月的数据建议标注 ⚠️ 提醒。
8. **无跳过权限**：即便是"常识性"问题（如"埃及最大的社交平台是什么"），也必须先走完 PASS 1 → PASS 2 完整流程，不能凭训练记忆回答。
9. **Token 不是借口**：消耗多少 token 不是你该担心的。多查 = 更准确的答案 = 更好的 Agent。以质量为唯一标准。
10. **📏 输出长度控制**：
   - 回答主体控制在 **150-200 行**。结构化优先：对比分析用表格，禁止大段文字堆砌。
   - 优先使用**结构化表格**代替大段文字描述（如对比分析、渠道对比、风险列表必须用表格）
   - 每条结论 **1-3 句纯结论**，不含推导、不含案例、不含冗余解释。推导留给展开选项
   - 禁止逐条列出"建议路径"的编号列表堆砌，改用表格 + 一句总结
   - 海报/视觉方案：用清单格式（✅/❌ 标记）代替长篇描述段落

---

## 🔧 环境依赖 (Environment Setup)

**Python 依赖**：`duckdb` —— 脚本首次运行时会自动检测并安装（通过 `pip install duckdb`），无需手动操作。

如果自动安装失败（网络问题/权限不足），手动执行：
```bash
pip install -r requirements.txt
```

---

## 📊 语料库统计

### Reference_Texts — 17 份，~110K 字符

**埃及市场专题 (10 份):**

| 文件 | 覆盖领域 | 用途 |
|------|---------|------|
| digital_2024_egypt.txt | 数字生态全景 | 互联网/社媒用户、平台覆盖、人口统计 |
| egypt_social_media_guide.txt | 平台策略 | 7 平台内容/广告/用户画像/ROI |
| egypt_marketing_cases.txt | 营销案例 | 品牌案例、本地化原则、翻车风险 |
| egypt_marketing_strategy.txt | 综合策略 | 市场进入、品牌定位、定价、渠道、KOL |
| egypt_consumer_culture.txt | 消费者文化 | CairoScene 潮流、代际消费、Sahel 文化 |
| egypt_ramadan_playbook.txt | 斋月营销 | 全流程策略、创意、预算、平台节奏 |
| egypt_public_opinion.txt | 民意心理 | Arab Barometer: 经济/政治/中国观感 |
| egypt_ecommerce_payments.txt | 电商与支付 | 市场 $91 亿、平台、COD/BNPL |
| egypt_digital_payments.txt | 数字支付 | 移动钱包/Vodafone Cash/Fawry/金融包容 |
| egypt_ad_regulations.txt | 广告合规 | 内容红线、数据隐私法、品类限制 |
| egypt_kol_ecosystem.txt | KOL 生态 | 分级/定价/平台/选择/预算/合作 |

**营销内功心法 (5 份):**

| 文件 | 覆盖领域 | 用途 |
|------|---------|------|
| consumer_psychology_toolkit.txt | 行为经济学 | 损失厌恶/锚定/稀缺/社会证明/动机理论 |
| data_analytics_roi.txt | 数据分析 | CAC/LTV/ROAS、A/B 测试 SOP、归因 |
| competitive_intelligence.txt | 竞品情报 | SWOT/Porter/PESTEL/蓝海/6种战术 |
| pr_crisis_management.txt | 危机管理 | 4级响应/黄金24h/道歉四要素/埃及红线 |
| user_journey_aarrr.txt | 增长引擎 | AARRR 5阶段/触点地图/传播机制 |

**文化基础 (1 份):**

| 文件 | 覆盖领域 | 用途 |
|------|---------|------|
| hofstede_culture_egypt.txt | 文化维度 | PDI=80/IDV=38/MAS=52/UAI=68 |

### DuckDB — 1 张表，17 行元数据

| 表名 | 行数 | 用途 |
|------|------|------|
| corpus_metadata | 17 | Reference_Texts 元数据索引 |

### 数据时效性

| 数据源 | 更新频率 | 典型滞后 | 注意事项 |
|--------|---------|---------|---------|
| DataReportal 数据 | 年度 | 3-12 个月 | Digital 2025 发布后需更新 |
| Arab Barometer | 2-3 年 | Wave IX 2025 | 政治经济变化快，文化价值观相对稳定 |
| Hofstede 文化维度 | 静态 | — | 文化维度长期稳定 |
| 社交媒体平台数据 | 季度/年度 | 3-6 个月 | 平台广告工具数据，非 MAU |
| 电商数据 (P&S/Ken) | 年度 | 6-12 个月 | 埃及电商增速快，偏差可能大 |
| 斋月日期 | 年度 | 按伊斯兰历变动 | 每年确认具体日期 |
| CairoScene 趋势 | 实时 | 每月应刷新 | 消费潮流变化快 |

---

## 🧩 RAG 检索铁律

### 精准定位，禁止全量 dump

1. **关键词映射优先**: 先根据触发矩阵确定 1-3 个目标文件
2. **段落定位**: 文件内部按 `## 标题` 定位，只读取相关章节
3. **禁止 dump**: 不得将整个文件内容输出到回答中
4. **交叉验证**: 主文件给主干，辅助文件给补充
5. **来源到章节**: 引用标注到具体章节标题 `[A/Reference_Texts] {file} — {章节}`

---

## 触发主题 — 精准映射表

### 埃及市场类

| 触发主题 | 必须读取 | 示例问题 |
|---------|---------|---------|
| 埃及数字环境/平台数据 | digital_2024_egypt.txt | "TikTok 有多少用户""互联网渗透率" |
| 某平台怎么投广告/内容 | egypt_social_media_guide.txt + digital_2024_egypt.txt | "怎么投 TikTok""Facebook 广告策略" |
| 消费者画像/文化 | egypt_consumer_culture.txt + egypt_public_opinion.txt | "年轻人喜欢什么""埃及人怎么看中国品牌" |
| 竞品/案例 | egypt_marketing_cases.txt + competitive_intelligence.txt | "其他品牌怎么做""竞品分析" |
| 市场进入/品牌策略 | egypt_marketing_strategy.txt + egypt_ecommerce_payments.txt | "怎么进入市场""怎么定价" |
| 斋月营销 | egypt_ramadan_playbook.txt + egypt_consumer_culture.txt | "斋月怎么做营销""斋月预算" |
| 电商/支付 | egypt_ecommerce_payments.txt + egypt_digital_payments.txt | "COD 占多少""用什么支付" |
| 广告合规/禁忌 | egypt_ad_regulations.txt + egypt_marketing_cases.txt | "广告能过审吗""有什么禁忌" |
| KOL 营销 | egypt_kol_ecosystem.txt + egypt_social_media_guide.txt | "找什么 KOL""KOL 花多少钱" |
| 文化适配 | hofstede_culture_egypt.txt + pr_crisis_management.txt | "文化怎么适配""有没有红线" |
| **B2B SaaS/企业级出海**（🔥 重要） | **egypt_marketing_strategy.txt + digital_2024_egypt.txt + egypt_public_opinion.txt + hofstede_culture_egypt.txt + egypt_digital_payments.txt + egypt_social_media_guide.txt** | "AI 产品进入埃及""SaaS 怎么获客""B2B 触达决策者" |
| B2B 海报/视觉输出 | **egypt_ad_regulations.txt + hofstede_culture_egypt.txt + egypt_consumer_culture.txt** | "海报设计""宣传物料""广告视觉方案" |

**⚠️ B2B vs B2C 场景判定铁律**：如果用户问题中出现「SaaS」「AI」「B2B」「企业级」「决策者」「软件」「平台」「技术方案」「出海」等关键词，必须判定为 B2B 场景，自动加载 B2B SaaS 触发映射行。

**🔥 B2B 场景硬禁止词黑名单**（输出中出现以下任何词汇 = 违规，必须撤回重写）：
- ❌ Jumia / Noon / Amazon.eg（电商平台试水 — 这是 C 端打法）
- ❌ KOL 种草 / TikTok 带货 / 网红推荐（消费品 C 端玩法）
- ❌ 社区团购 / 朋友圈裂变 / 微信群（中国企业出海 C 端套路）
- ❌ 开箱测评 / 种草笔记 / 好物推荐（内容电商 C 端手法）

B2B SaaS 的正确路径：LinkedIn B2B 广告 + WhatsApp Business 建联 + 本地代理商/商会 + 行业白皮书 + 免费试用 + 客户成功案例。

### 营销通用类

| 触发主题 | 必须读取 | 示例问题 |
|---------|---------|---------|
| 定价策略/文案 | consumer_psychology_toolkit.txt + data_analytics_roi.txt | "怎么定价""文案怎么写" |
| 广告效果/ROI | data_analytics_roi.txt | "CAC 多少合适""ROAS 目标" |
| A/B 测试 | data_analytics_roi.txt | "A/B 测试怎么做" |
| 竞品战术 | competitive_intelligence.txt + data_analytics_roi.txt | "竞争对手降价怎么办" |
| 危机公关 | pr_crisis_management.txt + egypt_ad_regulations.txt | "翻车了怎么办""被骂了怎么回应" |
| 用户增长/留存 | user_journey_aarrr.txt + data_analytics_roi.txt | "用户不回来怎么办""怎么裂变" |

---

## 🎯 CMO 标准方案流水线

### 🧠 内部思考管道（不直接输出）
依次检索以下组合，但不显式输出步骤：

**B2C 消费品路线：**
```
第一步：市场洞察
→ digital_2024_egypt.txt + egypt_public_opinion.txt + egypt_consumer_culture.txt

第二步：竞品分析
→ competitive_intelligence.txt + egypt_marketing_cases.txt

第三步：本地化策略
→ egypt_marketing_strategy.txt + hofstede_culture_egypt.txt + egypt_ad_regulations.txt

第四步：创意/渠道
→ egypt_social_media_guide.txt + egypt_ramadan_playbook.txt + consumer_psychology_toolkit.txt + egypt_kol_ecosystem.txt

第五步：ROI 预估
→ data_analytics_roi.txt + egypt_ecommerce_payments.txt
```

**B2B SaaS/企业级出海路线（🔥 所有涉及 AI/SaaS/B2B/软件/技术出海的问题必须走此路线）：**
```
第一步：市场技术能力基线
→ digital_2024_egypt.txt + egypt_public_opinion.txt + egypt_digital_payments.txt

第二步：B2B 决策链分析
→ hofstede_culture_egypt.txt（高PDI=需要权威背书） + egypt_consumer_culture.txt（商业文化）
  + egypt_marketing_strategy.txt（B2B 市场进入路径）

第三步：B2B 获客渠道
→ egypt_social_media_guide.txt（LinkedIn B2B 部分） + competitive_intelligence.txt（竞品分析）

第四步：本地化信任建设
→ egypt_ad_regulations.txt（B2B 合规） + egypt_marketing_cases.txt（外资企业案例）
  + pr_crisis_management.txt（品牌危机预防）

第五步：定价与增长模型
→ consumer_psychology_toolkit.txt（B2B 定价心理学） + user_journey_aarrr.txt（SaaS 增长漏斗）
  + data_analytics_roi.txt（CAC/LTV 测算）
```

**B2B 路线覆盖的文件（共 14 份）**：digital_2024_egypt.txt、egypt_public_opinion.txt、egypt_digital_payments.txt、hofstede_culture_egypt.txt、egypt_consumer_culture.txt、egypt_marketing_strategy.txt、egypt_social_media_guide.txt、competitive_intelligence.txt、egypt_ad_regulations.txt、egypt_marketing_cases.txt、pr_crisis_management.txt、consumer_psychology_toolkit.txt、user_journey_aarrr.txt、data_analytics_roi.txt

### 📤 对外输出规则（简洁硬约束）

1. **回答主体**：将 5 步分析结果合成为 **3-8 条纯结论**直接输出（禁止显式展示流水线步骤）
2. **结构优先表格**：对比分析、渠道对比、成本测算、风险列表 → 必须用表格。禁止用大段文字描述可以用表格表达的内容
3. **每条结论 = 1-3 句纯结论**，不含推导、不含案例、不含冗余解释。推导留给展开选项
4. **输出长度硬上限**：回答主体（不含来源引用和展开选项）≤ 200 行。超过此限制必须精简
5. **禁止流水账式建议路径**：不用"第一步...第二步...第三步..."式编号堆砌，改用一句话总结
6. **海报/视觉方案**：用清单格式（✅/❌ 标记）代替长篇描述段落
7. 结论末尾附最多 4 个可展开选项，**最后一个固定为推导入口**：
```
---
🔍 可深入展开：
1. [维度A] — [一句话预告]
2. [维度B] — [一句话预告]
...
N. 推导逻辑与数据依据 — 展示以上结论的分析过程、数据和推理链条

回复序号即可展开对应部分。
```
4. `--` 标记之前 = 回答主体（给结论），之后 = 可选入口（要推导来这儿）
5. 用户回复序号后，展开对应维度完整分析（此时可详细输出数据/推导/案例）

---

## 结构化引用格式

```
---
📚 来源引用（共 {N} 份语料）：
1. [A/Reference_Texts] {file} — {章节}（发布于{时间}，距今{月}个月）
2. [A/Reference_Texts] {file} — {章节}（发布于{时间}，距今{月}个月）
...

⏰ 数据时效性：{如有 >12 月的文件，逐份列出 ⚠️ 警告}
📊 来源占比：语料库 XX% | 定向搜索 XX% | 通用搜索 XX% | 推理 XX%
```

## 输出模式

**路由优先级（从轻到重，命中即停）：**

- **闲聊/域外/测试性提问** → 1-2 句直接回答，不检索语料库，不附来源。像正常对话。
- `详细模式` / `verbose` → 展开完整分析
- `简洁模式` / `concise` → 3-5 条核心结论
- `语料库测试` / `corpus test` → 每条数据标注精确到段落的来源
- 完整营销需求 → 自动触发 CMO 流水线模式（5 步思考 + 结论 + 展开）

### 🎨 海报/视觉生成模式

**第一步：判断用户是否描述了海报形式**

- ❌ 用户只说"帮我做张海报""生成宣传图"但**没有描述**方向 → **先反询问**，列出选项让用户选择，等用户确认后再进入第二步
- ✅ 用户**已经描述**了具体方向 → **直接进入第二步先输出设计方案**

**反询问模板（当用户未描述时）：**
```
我看到你想生成海报，先确认几个方向（选一个或直接描述你想要的）：

海报类型: 社媒竖版海报(9:16) / 社媒方图(1:1) / 横版Banner(16:9) / 电商主图(3:4)
视觉风格: 扁平商业插画 / 极简科技感 / 温暖卡通风 / 阿拉伯几何装饰风
色调: 深蓝+金色(权威商务) / 陶土橙+金色(活力消费) / 深绿+金色(斋月节日) / 白+蓝(极简科技)
核心内容: 你想突出什么产品/服务/概念？

也可以直接告诉我你脑海中的画面～
```

**第二步（强制）：输出设计方案 → 等用户确认后再生成**

在调用 ImageGen 之前，必须先基于语料库输出一份完整的设计方案，覆盖以下 6 个维度：

1. 🎨 视觉风格 — 默认扁平商业插画，基于语料库说明为什么选这个风格
2. 🎨 色彩规范 — 主色/辅色/点缀色 + 搭配逻辑 + 哪些颜色要避开
3. ✍️ 文案方向 — 短文字写进 Prompt（品牌名/CTA/≤3词标语），长文案后期叠加
4. ⛔ 文化禁忌清单 — 逐条列出不可碰的红线（宗教/性别/政治/肢体语言/节日限制）
5. 📱 CTA 与合规 — 简单 CTA 词写进 Prompt，#إعلان 标识和详细联系信息后期叠加
6. 📐 构图与版面 — 海报类型 + 比例 + 构图方式 + 版面分区规划

引用格式：`[Reference_Texts] {文件名} — {章节}`。

输出方案后，末尾追加：
```
---
以上是设计方案。确认后立刻生成海报。是否开始生成？
```

**第三步：用户确认后，调用 ImageGen 生成**

#### 🔥 海报生成铁律（默认规则）

**1. 默认视觉风格：扁平商业插画**
- Prompt 必须以 `Flat commercial illustration poster design` 开头
- **禁止**写实摄影式描述（如"A young Egyptian man taking a photo..."）
- 除非用户明确要求"写实照片风格"

**2. 默认使用埃及独占元素（S/A级）**
- 默认使用评分体系中 S/A 级独占元素，不使用常见的普通金字塔/狮身人面像
- 例外：用户明确要求"用金字塔""用常见的埃及元素"时按用户要求
- 独占元素评分表：

| 元素 | 独特性 | 获知难度 | 海报适配 | AI友好 | 视觉冲击 | 文化深度 | 等级 |
|------|--------|---------|---------|--------|---------|---------|------|
| 弯曲金字塔 | 10 | 3 | 8 | 8 | 7 | 7 | S |
| 闻风节彩蛋 | 9 | 5 | 9 | 8 | 7 | 10 | S |
| 努比亚彩绘 | 10 | 5 | 10 | 6 | 9 | 9 | S |
| 费昂斯釉面 | 9 | 4 | 8 | 6 | 6 | 8 | A |
| 阿布辛贝巨像 | 9 | 3 | 5 | 4 | 9 | 8 | A |
| 白沙漠蘑菇岩 | 8 | 6 | 7 | 7 | 8 | 5 | A |

- 每张海报最多 2 个独占元素，费昂斯釉面作为色温层不计数
- 推荐组合：弯曲金字塔+费昂斯釉面(通用) / 弯曲金字塔+闻风节彩蛋(春季) / 努比亚彩绘+闻风节彩蛋(文化) / 努比亚彩绘+费昂斯釉面(纯视觉)

**3. 默认构图：金字塔左偏构图**
- 地标放大撑满画面，尖顶左偏，右侧留白放文字/产品
- 底部贴边不留空，地标淡色(25%透明度)退为背景

**4. Prompt 6 层结构**
```
[1. 风格声明] → [2. 构图指令] → [3. 核心视觉] → [4. 背景与分区] → [5. 本土装饰] → [6. 比例+文字]
```

**5. 文字策略**
- ✅ 允许：品牌名(≤2词)、CTA词(1词)、阿拉伯短词(1词)、英文标语(≤3词)，加 `short bold text` 修饰
- ❌ 禁止：长句、复杂阿拉伯书法、多行文案

**6. 黄金组合 Prompt（用户无特殊要求时默认使用）**
- 完整可复用模板见参考手册 `egypt_poster_design_reference.md` §2.4 / §11.3
- 元素组合：弯曲金字塔（左偏构图） + 努比亚彩绘 + 闻风节彩蛋 + 费昂斯釉面
- 文字变量：`[品牌/节日词]` 按需替换
- 比例变量：`portrait 9:16` / `square 1:1` / `horizontal 16:9` 按场景替换

**7. 生成后处理**
- ImageGen 生成含短文字的底图
- 长文案/品牌LOGO/#إعلان标识/详细CTA → 后期叠加
- 最终检查：文字可读性、性别图像合规、宗教符号使用得当、色调一致

**8. 推荐模板库（用户问"有什么推荐/模板/风格"时触发）**
- 从参考手册 `egypt_poster_design_reference.md` §12 推荐模板库中选 3-4 个
- **必须包含模板 A（黄金组合）**，因为综合评分最高
- 其余按用户行业匹配：B(品牌故事) / C(旅游) / D(快消) / E(B2B科技)
- 用户选定后直接用对应模板 Prompt 生成，不需要再走设计方案流程

## 不确定性

- 非官方/单一来源必须标注 `⚠️ 不确定性`
- 禁止绝对化表述
- 平台数据为广告覆盖数据，非月活用户数
- 电商/支付数据来自第三方研究，口径可能不同

## 语料库维护指南

### 定期更新
- DataReportal 数据：每年 2 月发布新年度报告后更新
- Arab Barometer：下一波 (Wave X) 发布后更新
- 斋月日期：每年底确认下一年斋月日期
- CairoScene 趋势：每月刷新首页内容
- 电商/支付数据：年度更新
- 新营销案例：随时追加到 egypt_marketing_cases.txt
- 平台数据：每季度检查各平台广告工具

### 语料库完备度: 90%
- ✅ 数字生态、社媒策略、消费者洞察、斋月、电商、支付、法规、KOL
- ✅ 行为经济学、数据分析、竞品、危机、增长
- ✅ 民意调查 (Arab Barometer)
- ⚠️ 待补充: 完整 Checkout.com 报告、Statista 数据、实时 KOL 数据库
