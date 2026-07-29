---
name: ipo-kline-chart
description: |
  A 股新股专用 K 线与分时绘制工具。支持日/周/月 K 线及当日 1 分钟分时图，新股专用元素：发行价水位线、上市日竖线、±30%/±60% 临停阈值线。A 股红涨绿跌，底部数据源水印。
  触发词：K线、日K、周K、月K、分时图、盯盘图、首日走势、新股K线、发行价水位、临停线
---

# IPO K 线 / 分时绘制

## 功能说明

为 A 股新股场景提供精准 K 线与分时图绘制。覆盖日/周/月 K 线（含 MA5/MA20/MA60 均线与成交量）及当日 1 分钟分时图（含均价线）。新股专用增强：发行价水位线（橙色虚线）、上市日竖线、±30%/±60% 临停阈值线。视觉遵循 A 股惯例（红涨绿跌），底部强制水印标注数据源与免责声明。

仅支持 A 股（沪深主板/科创板/创业板/北交所），不支持港股美股。

## 调用方式

```bash
# 在 skill 目录下执行（推荐 managed venv 的 python，已含 matplotlib + pandas）
cd <skill-dir>
python3 scripts/kline.py <code> <mode> [options]
```

> `<skill-dir>` 即本 skill 安装目录。专家运行时由 Agent 通过 Bash 工具调用，需先 cd 到本目录。

## 支持的命令

| 命令 | 说明 | 示例 |
|---|---|---|
| `day` | 日 K 线（含 MA + 成交量） | `python3 scripts/kline.py sh688256 day --limit 60` |
| `week` | 周 K 线 | `python3 scripts/kline.py sh688256 week --limit 52` |
| `month` | 月 K 线 | `python3 scripts/kline.py sh688256 month --limit 36` |
| `minute` | 当日 1 分钟分时 | `python3 scripts/kline.py sh688256 minute` |

## 参数说明

| 参数 | 必填 | 说明 |
|---|---|---|
| `code` | ✅ | A 股代码，前缀 sh/sz/bj |
| `mode` | ✅ | `day` / `week` / `month` / `minute` |
| `--limit` | 否 | K 线条数（minute 模式忽略），默认 60 |
| `--issue-price` | 否 | 发行价，提供后绘制水位线 |
| `--listing-date` | 否 | 上市日 YYYY-MM-DD，提供后绘制黑色竖线 |
| `--output-dir` | 否 | 输出目录，默认当前目录。**约定统一传 `<会话工作区>/charts`**，避免图表散落各处、便于用户查找 |

> 输出目录约定：Agent 调用本脚本时应显式传 `--output-dir <会话工作区>/charts`，把所有 K 线/分时图集中到会话工作区下的 `charts/` 目录；目录不存在时脚本会自动创建。

## 输出格式

- 文件名：`<code>_<mode>_<时间戳>.png`
- 标准输出最后一行：`CHART_PATH:<绝对路径>`
- 失败：非零退出码 + stderr 错误信息

```
CHART_PATH:/tmp/sh688256_minute_20260722_120000.png
```

## 新股专用场景

- **上市首日盯盘**：`python3 scripts/kline.py <code> minute --issue-price <发行价>` → 分时图叠加发行价水位 + ±30%/±60% 临停阈值
- **次新股研究**：`python3 scripts/kline.py <code> day --limit 60 --issue-price <发行价> --listing-date <上市日>` → 日 K 叠加发行价水位 + 上市日竖线
