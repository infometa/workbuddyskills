# lingxi-financialsearch-skill

> 国泰海通金融数据查询 Skill — 通过自然语言查询 A 股实时行情与财务数据

## 功能简介

本 Skill 接入国泰海通证券金融数据服务，支持通过自然语言查询 A 股市场的多维度数据。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 实时行情 | 涨跌幅、成交量、成交额等实时盘口数据 |
| 基本财务 | 个股营收、净利润等财报基本面数据 |
| 衍生财务 | 市盈率、市净率、PEG 等衍生指标 |
| 技术形态 | MACD、K线形态、支撑压力位等技术面数据 |
| 资金面 | 主力资金流向变动数据 |
| 批量查询 | 单次请求查多只股票的不同指标 |

## 能力边界

**可以做的：**
- 查询 A 股个股行情、财务数据、技术指标
- 查询板块、指数行情
- 批量查询多只股票的不同指标
- 统计排名（市值排名、涨幅排名等）

**不能做的：**
- 不支持研报数据查询
- 不提供投资建议或策略推荐
- 不支持港股、美股等非 A 股市场数据
- 不支持实时交易或下单操作
- 不支持基金净值、期货行情、债券数据等品种（仅限 A 股）

## 快速开始

### 1. 安装

将本 Skill 目录放置到 `~/.workbuddy/skills/lingxi-financialsearch-skill/`。

### 2. 授权

首次使用时需要完成授权，运行以下命令获取授权链接：

```bash
node skill-entry.js authChecker auth
```

按照提示完成扫码授权，或手动将 API Key 写入 `./gtht-skill-shared/gtht-entry.json`。

### 3. 使用

```bash
# 查询单只股票
node skill-entry.js mcpClient call financial financial-search query='贵州茅台净利润'

# 批量查询
node skill-entry.js mcpClient call financial financial-search query='查询科大讯飞营业收入和贵州茅台净利润'
```

## 查询示例

```
科大讯飞营业收入
贵州茅台净利润
比亚迪毛利率
宁德时代ROE
格力电器资产负债率
宁德时代总市值
A股市值前十的公司
今日涨幅最大的股票
创业板成交额排名
同时获取宁德时代市值、比亚迪市盈率、格力电器换手率
```

## 目录结构

```
lingxi-financialsearch-skill/
├── SKILL.md                  # Skill 定义与 Agent 指令
├── README.md                 # 本文件
├── skill-entry.js            # 运行时入口（授权 + MCP 调用）
├── gateway-config.json       # MCP 网关配置
├── gtht-skill-shared/        # API Key 存储目录（授权后自动生成）
│   └── gtht-entry.json
└── references/
    ├── troubleshooting.md    # 故障排除指南
    └── api-reference.md      # 错误码与 API 参考
```

## 免责声明

以上信息源自第三方数据整理，仅供参考。金融数据查询 Skill 仅提供客观数据，调用本 Skill 后生成的内容，不构成投资建议。
