# 埃及市场营销专家 — 安装指南

## 1. 前置条件

- 已安装 [WorkBuddy](https://workbuddy.com) 桌面版
- Python 3.10+（用于运行脚本，非必须）
- 磁盘空间：~3 MB

## 2. 安装步骤

### 方法 A：通过 WorkBuddy 专家市场导入（推荐）

1. 打开 WorkBuddy → 专家市场
2. 选择「从本地导入」
3. 选择 `egypt-marketing.zip` 文件
4. 等待自动解压和注册完成

### 方法 B：手动安装

1. 解压 `egypt-marketing.zip`，得到 `egypt-marketing/` 目录

2. 将目录复制到 WorkBuddy 插件路径：

   **Windows:**
   ```
   %USERPROFILE%\.workbuddy\plugins\marketplaces\my-experts\plugins\egypt-marketing\
   ```

   **macOS / Linux:**
   ```
   ~/.workbuddy/plugins/marketplaces/my-experts/plugins/egypt-marketing/
   ```

3. 重启 WorkBuddy，专家将自动出现在专家列表中

## 3. 验证安装

安装完成后，在 WorkBuddy 中新建对话，选择「埃及市场营销专家」，然后输入：

```
语料库测试
```

如果专家正常工作，它会进入测试模式并输出带来源标注的回答。

### 可选：运行压力测试

```bash
pip install duckdb
python scripts/pressure_test.py
```

运行后会生成 `EGYPT_MARKETING_PRESSURE_TEST_REPORT.md`，确认 17 份语料和 DuckDB 均可正常读取。

## 4. 目录结构

```
egypt-marketing/
├── .codebuddy-plugin/
│   └── plugin.json              # 插件配置（必须）
├── agents/
│   └── egypt-marketing.md       # Agent 指令定义（核心）
├── avatars/
│   └── egypt-marketing.png      # 专家头像
├── Databases/
│   └── egypt_marketing.duckdb   # 语料库元数据索引（17 行）
├── Reference_Texts/             # 17 份核心语料（~110K 字符）
│   ├── digital_2024_egypt.txt
│   ├── egypt_social_media_guide.txt
│   ├── egypt_marketing_cases.txt
│   ├── egypt_marketing_strategy.txt
│   ├── egypt_consumer_culture.txt
│   ├── egypt_ramadan_playbook.txt
│   ├── egypt_public_opinion.txt
│   ├── egypt_ecommerce_payments.txt
│   ├── egypt_digital_payments.txt
│   ├── egypt_ad_regulations.txt
│   ├── egypt_kol_ecosystem.txt
│   ├── consumer_psychology_toolkit.txt
│   ├── data_analytics_roi.txt
│   ├── competitive_intelligence.txt
│   ├── pr_crisis_management.txt
│   ├── user_journey_aarrr.txt
│   └── hofstede_culture_egypt.txt
├── scripts/
│   ├── corpus_manager.py        # 语料自动整理工具
│   ├── pressure_test.py         # 压力测试脚本
│   ├── pdf_corpus_builder.py    # PDF 语料构建器（通用工具）
│   └── schema_enhancer.py       # DuckDB 字段语义增强
├── skills/
│   └── egypt-marketing-skill/
│       └── SKILL.md             # Skill 定义
├── plugin.json                  # 市场配置
├── README.md                    # 项目说明
└── INSTALL.md                   # 本文件
```

## 5. 语料库说明

| 类别 | 文件数 | 覆盖领域 |
|------|--------|---------|
| 埃及市场专题 | 11 | 数字生态、社媒策略、营销案例、综合策略、消费者文化、斋月营销、民意心理、电商支付、数字支付、广告合规、KOL 生态 |
| 营销内功心法 | 5 | 行为经济学、数据分析ROI、竞品情报、危机管理、增长引擎 |
| 文化基础 | 1 | Hofstede 文化维度 |

数据来源：DataReportal、Arab Barometer、Hofstede、P&S Research、Ken Research、CairoScene、Think Marketing Magazine 等。

## 6. 常见问题

**Q: 安装后看不到专家？**
A: 确认目录路径正确，`.codebuddy-plugin/plugin.json` 文件存在。重启 WorkBuddy。

**Q: 语料库测试模式报错？**
A: 检查 `Reference_Texts/` 目录下是否有 17 个 .txt 文件，`Databases/egypt_marketing.duckdb` 是否存在。

**Q: 脚本运行报错？**
A: 脚本为可选工具，不影响专家核心功能。如需运行，请先 `pip install duckdb PyPDF2`。

**Q: 数据是否最新？**
A: 语料截止 2024 年度报告（DataReportal Digital 2024 Egypt 等）。阿拉伯barometer 为 Wave IX。建议每年 2 月更新 DataReportal 数据。
