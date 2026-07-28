# TideRider Sentiment Analyst

A data-driven game sentiment analysis expert for WorkBuddy. Connects to Google BigQuery to analyze player reviews across platforms, perform topic attribution, version trend analysis, and generate premium HTML reports.

> 🔒 **保密声明（内部）**：本专家包内的分析逻辑与文档（表结构、字段、阈值、归因算法、SQL 模板、提示词内容）均为 **TideRider 内部专有资产**。
> - **模型侧**：专家已内置最高优先级保密指令，即使用户直接询问也不会透露内部实现，只输出业务结论并统一标注「数据来源：DataBrain X TideRider」。
> - **⚠️ 物理边界**：以上指令只能约束模型在对话中的行为，**无法阻止拿到本包文件的人直接打开阅读**。逻辑的真正保密取决于**控制本包的分发范围**——请勿将本包提供给不应接触内部逻辑的人员。

## Features

- **舆情异动归因**：通过 anomaly_details 表的 Remark 四模块（典型讨论/发酵主贴/热门评论/KOL），精准定位异动原因并提供证据链接
- **Multi-platform sentiment analysis**: Steam, Discord, Reddit, Twitter, App Stores
- **Version trend comparison**: Track sentiment changes across game updates
- **Topic attribution**: Identify and rank complaint/praise topics by community consensus
- **Player behavior deep-dives**: Playtime segmentation, abandonment analysis, disillusionment curves
- **Steam specialist**: ext_json field analysis (playtime portraits, refund analysis, review changes)
- **Premium report generation**: Dark-themed HTML reports with Chart.js visualizations

## 凭证配置（首次使用需用户提供）

本专家需要连接 Google BigQuery 才能查询数据。出于安全考虑，专家包**不再内置任何凭证**。用户可**二选一**完成鉴权，首次查询时专家会主动提示。

### 方式 A：Service Account JSON 文件（推荐给无 GCP 账号的用户）

1. **获取凭证**：企业微信联系 **chandwang** 获取 BigQuery Service Account JSON（只读、仅可访问 `opinion` / `tiderider` 两个 dataset）。
2. **保存到本地**：存到电脑任意位置（建议如 `~/Documents/tiderider.json`）。
3. **首次查询时把路径发给专家**：专家会主动提示你提供凭证文件路径。

连接方式（Python）：

```python
import os
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = USER_PROVIDED_CRED_PATH  # 用户提供的路径
client = bigquery.Client()   # SA JSON 内含 project_id，自动读取
print(client.project)
```

### 方式 B：gcloud 本地登录（推荐给已有 GCP 账号且有数据访问权限的用户）

无需任何凭证文件，用自己的 Google 账号在本地做一次 **应用默认凭证（ADC）** 登录即可：

```bash
# 1) 安装 gcloud CLI（若未安装）：https://cloud.google.com/sdk/docs/install
# 2) 登录 gcloud（浏览器授权你的 Google 账号）
gcloud auth login

# 3) 关键：为本地应用/SDK 生成"应用默认凭证"(ADC)——Python SDK 实际用的是这个
gcloud auth application-default login

# 4) 设置默认项目（ADC 不含 project_id，需显式指定；项目 ID 找 chandwang 获取）
gcloud config set project <PROJECT_ID>
gcloud auth application-default set-quota-project <PROJECT_ID>
```

完成后，Python SDK 会自动发现本地 ADC，无需任何路径：

```python
from google.cloud import bigquery

# 不设 GOOGLE_APPLICATION_CREDENTIALS；SDK 自动读取本地 gcloud ADC
client = bigquery.Client(project="<PROJECT_ID>")   # ADC 无 project_id，需显式传入
print(client.project)
```

> ⚠️ **易踩坑**：让 Python SDK 生效的是 `gcloud auth application-default login`（生成 ADC），
> 而不是只跑 `gcloud auth login`（那只登录了 gcloud CLI 本身）。两条都建议执行。
> ⚠️ 方式 B 用的是**用户本人**的 GCP 权限——须确保你的账号对 `opinion` / `tiderider` 有读取权限（找 chandwang 开通）。

### 通用说明

> 💡 方式 A 的 SA JSON 内含 `project_id`，自动读取；方式 B（ADC）需在 `bigquery.Client(project=...)` 显式指定项目。
> 💡 凭证/权限/项目 ID 获取 —— 企业微信联系 **chandwang**。

### 环境要求

- Python 3.9+（系统自带即可）
- `google-cloud-bigquery` Python 包

安装方法：
```bash
pip install google-cloud-bigquery
```

> 如果你的系统有多个 Python 版本，请确保安装到正确的环境中（如 `pip3 install google-cloud-bigquery` 或 `python3 -m pip install google-cloud-bigquery`）

## Quick Start

1. 安装专家到 WorkBuddy，确保本地已安装 `google-cloud-bigquery`
2. 完成鉴权（二选一）：方式 A 从 chandwang 获取 SA JSON 存到本地；或方式 B 本地 `gcloud auth application-default login` + 设项目
3. 提问：「帮我分析一下 PoE2 最近两周的舆情」——专家首次查询会提示你选择并提供凭证

## Supported Games

See `skills/bigquery-sentiment/references/games.json` for the full list of supported game UIDs.

## 数据表说明

| 表 | 用途 | 优先级 |
|---|------|--------|
| `tiderider.anomaly_details` | 舆情异动归因（含Remark四模块+证据链接） | ⭐ 异动问题第一优先 |
| `tiderider.opinion_feeds` | 清洗后评论数据（目前仅Subway系列） | 统计问题第一优先 |
| `opinion.feeds` | 原始评论数据（所有游戏） | 统计问题回退 |
| `tiderider.key_document_collection_extra` | 官方/大V内容 | 舆情总结第一引用源 |

## Skills Included

| Skill | Description |
|-------|-------------|
| `bigquery-sentiment` | Core sentiment query templates, game UID mapping, query rules, anomaly analysis workflow |
| `steam-deep-analysis` | Steam-specific ext_json analysis: playtime portraits, abandonment, disillusionment, community consensus, refund analysis |

## Report Style

Reports use a premium dark theme with:
- Deep navy background (`#0b1020`)
- Glowing card borders
- Chart.js v4 visualizations
- Color-coded sentiment indicators (green=positive, red=negative, amber=neutral)

## License

Proprietary - TideRider Team
