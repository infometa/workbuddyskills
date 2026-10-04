---
name: wangxiaobao-project-daily-report
description: >
  地产项目营销日报生成器。基于旺小宝 API 拉取来访、客户画像、成交数据，
  生成结构化 HTML + PDF 日报。触发词：营销日报、项目日报、生成日报、daily report。
agent_created: true
---

# 旺小宝项目日报生成技能

## 概述

基于旺小宝API自动拉取数据，生成 `<项目名>` 营销日报HTML+PDF文件（排版完全一致）。

## 功能特性

- 自动拉取旺小宝来访数据、客户画像、成交数据
- 意向等级分析（A/B/C/D）
- 渠道分布分析（中介/自渠/顺访等）
- 存量客户复访分析
- 生成专业排版HTML日报（与参考模板完全一致）
- **同时生成同名PDF文件，排版与HTML 1:1一致**（需Chrome/Edge）

## 触发词

```
营销日报
项目日报
生成日报
daily report
```

## 使用方法

### 方式一：直接语音/文字命令（推荐）

```
生成项目日报
```

### 方式二：指定日期

```
生成2026年5月19日的项目日报
```

### 方式三：本地执行脚本

```bash
cd <skill目录>/scripts
python generate_report.py 2026-05-19
```

可通过环境变量或命令行参数指定项目：

```bash
python generate_report.py 2026-05-19 \
  --tenant-id <你的租户ID> \
  --project-id <你的项目ID> \
  --project-name "<项目名>"
```

### 方式四：一键运行（自动用昨日日期）

```bash
python3 run.py                 # 不带日期参数，自动用昨天的日期
python3 run.py 2026-05-19      # 也可指定日期，参数原样透传给 generate_report.py
```

## 输出文件

每次生成同时产生两个文件，默认写入当前工作目录：

```
<工作目录>/<项目名>_日报_YYYYMMDD.html
<工作目录>/<项目名>_日报_YYYYMMDD.pdf
```

- **HTML**：可直接在浏览器中打开查看、打印
- **PDF**：由 Chrome/Edge headless 打印生成，排版与 HTML 完全一致，可直接转发

## 日报内容结构

| 模块 | 说明 |
|------|------|
| KPI概览 | 本月来访、来访进度达成、本月成交、昨日本月来访 |
| 来访指标 | 月度客储指标、截至昨日来访、完成率、进度达成率 |
| 来访意向等级 | A级/B级/C级/D级分布及占比 |
| 销售指标 | 月度销售指标、截至昨日成交、完成率、进度达成率 |
| 成交意向等级 | 成交客户的意向等级分布 |
| 来访渠道分布 | 中介/自渠/顺访/约访等渠道统计 |
| 存量客户汇总 | 近3月未成交客户按渠道分布 |
| 存量客户明细 | 预计本周复访客户完整信息（10条） |
| 昨日来访明细 | 昨日来访客户记录 |
| 顾问来访统计 | 顾问来访排行 |
| 数据说明 | 数据来源及状态说明 |

## 数据来源

| 数据类型 | 来源 | 说明 |
|---------|------|------|
| 来访数据 | 旺小宝 `/ai-open/visits/page` | 来访时间、顾问、次数、时长 |
| 客户画像 | 旺小宝 `/ai-open/customers/page` | 意向等级、渠道、成交状态 |
| 成交数据 | 旺小宝客户画像 dealStatus=1 | 成交套数 |
| KPI指标 | 配置项（环境变量/命令行参数） | 来访目标、销售目标 |

## 依赖

- 旺小宝OAuth授权（首次使用需授权）
- Python 3.x（内置urllib，无需额外依赖）
- Google Chrome 或 Microsoft Edge（用于生成PDF，已安装可跳过）

## 首次使用

1. 如果没有授权旺小宝，系统会提示授权
2. 打开授权链接，输入验证码完成授权
3. 重新执行生成命令

## 项目配置

项目标识与KPI指标均可配置，优先级为：命令行参数 > 环境变量 > 默认值。

### 方式一：环境变量

```bash
export XIAOBAO_TENANT_ID="你的租户ID"
export XIAOBAO_PROJECT_ID="你的项目ID"
export XIAOBAO_PROJECT_NAME="项目名称"
export XIAOBAO_MONTH_VISIT_TARGET="500"     # 月度来访目标
export XIAOBAO_MONTH_SALES_TARGET="21000"   # 月度销售目标（万元）
```

### 方式二：命令行参数

```bash
python generate_report.py 2026-05-19 \
  --tenant-id <你的租户ID> \
  --project-id <你的项目ID> \
  --project-name "<项目名>" \
  --month-visit-target 500 \
  --month-sales-target 21000
```

## 文件结构

```
wangxiaobao-project-daily-report/
├── SKILL.md                    # 本文档
├── _meta.json                  # Skill元数据
├── scripts/
│   ├── fetch_data.py           # 数据拉取脚本
│   ├── generate_report.py      # 主生成脚本
│   └── run.py                  # 一键运行入口（默认昨日日期，跨平台）
└── references/
    └── report_template.html     # HTML模板参考
```

## 技术细节

- 使用Python原生urllib调用API，彻底避免PowerShell中文编码乱码问题
- HTML模板完全参照参考文件样式
- PDF由Chrome/Edge headless `--print-to-pdf` 生成，排版与HTML 1:1一致
- 数据自动关联来访记录与客户画像
- 客户姓名自动脱敏
- **PDF打印优化**：
  - 使用 `--print-background` 参数强制打印背景色
  - `@media print` CSS块中强制所有表头元素背景色+文字颜色（`print-color-adjust: exact !important`）
  - 表头文字统一白色（`color: #fff !important`），深色背景确保可读性
  - KPI卡片打印布局使用 `flex-wrap: nowrap`，4个卡片强制1行排列
  - 所有 `.section-title` / `.table-header td` / `.table-header-peach` 等表头类均有独立打印样式声明
