# South Africa HR Admin — Thandiwe（南非人力行政专家）

为中国企业在南非的本地化运营提供全流程 HR 与行政支持：招聘、劳动合同、薪酬社保、签证工签、B-BBEE/EEA 合规、CCMA 争议、办公场地与公司注册。

## 类型

Agent 型（单个 AI 专家）

## 功能

- **强制语料检索**：所有专业问题先查本地语料库（TF-IDF 537 块 + 可选语义向量层），严禁凭记忆答税率/费率。
- **语义跨语言检索（双功能之一）**：`search_corpus_semantic.py` 用 sentence-transformers 句向量做中文提问→英文语料匹配；已生成 `semantic_embeddings.npz` 时自动加载预构建索引，无模型/无索引时自动回退 TF-IDF。**激活只需本机跑一次 `build_semantic_index.py`**（复用同一套 chunk，与 TF-IDF 层严格对齐）。
- **核心法源（双功能之二）**：`references/corpus/south-africa-hr-corpus/primary-sources/` 提供 5 部法案高频条款速查 `key-provisions.md`、必看 Subsection 清单 `subsection-checklist.md`、官文入口 `MANIFEST.md`，以及 `fetch_primary_sources.py`（按 SAFLII→legislation.gov.za→gov.za 顺序镜像兜底下载原文，403 时优雅降级并给出人工步骤）。
- **量化实算**：`references/tools/calculators.py`（PAYE 7 档/ UIF / SDL / COIDA / 净薪 / 雇主成本）、`refs.py`（合规日历 / 签证清单 / B-BBEE 评分卡）。
- **可视化**：`references/widgets/`（payroll / visa_cost / bbbee_scorecard 交互计算器）、`show_widget` 内联 SVG。
- **实时源登记**：`references/supplement/realtime_sources.json` 直连 SARS / DHA / DEL / COIDA 等 13 个权威源。

## 使用示例

- "南非 2026 年 BCEA 收入门槛是多少？低于门槛的员工享有哪些保护？"
- "中国公司收购南非工厂，员工合同怎么处理？（LRA s197 业务转让）"
- "2026 劳工法修正案草案里遣散费改成什么样了？生效了吗？"
- "帮我把月薪 R80,000 的本地员工的净薪和雇主总成本算出来。"
- "我要给 50 人以上的公司在南非做 EEA 就业公平申报，流程是什么？"

## 本地激活（语义层 / 法源原文，需本机联网）

```bash
cd references/corpus/south-africa-hr-corpus
python build_semantic_index.py                 # 生成 semantic_embeddings.npz（约 1–2 分钟）
python primary-sources/fetch_primary_sources.py   # 归档 5 部法案原文（SAFLII 403 时自动换官源）
```

> 沙箱/受限网络下大文件下载与 SAFLII 反爬会被拦截，上述两步请在不受限的本机网络执行。

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换，要求：PNG/JPG、512×512px、单张 ≤ 500KB。

## 安装

将专家包目录放到专家目录下：

```
~/.workbuddy/plugins/marketplaces/my-experts/plugins/south-africa-hr-admin/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r south-africa-hr-admin.zip south-africa-hr-admin/
```
