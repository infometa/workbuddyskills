---
name: ipo-kline-chart
description: A 股新股专用 K 线绘制。支持日/周/月 K 线、当日 1 分钟分时图，新股专用元素：发行价水位线、上市日竖线、±30%/±60% 临停阈值。A 股红涨绿跌，底部数据源水印。触发词：K线、日K、周K、月K、分时图、盯盘图、首日走势、新股K线、发行价水位
---

# A 股新股 K 线 / 分时绘制

## 适用范围

仅 A 股：沪深主板 / 科创板 / 创业板 / 北交所。港美股不支持。

## 唯一数据源

`westock-data`（腾讯自选股）。所有图表底部强制水印：`数据源：westock-data ｜ 仅供参考，不构成投资建议`。

## 调用命令

```bash
# 推荐使用 managed venv 的 python，已含 matplotlib + pandas
PY=~/.workbuddy/binaries/python/envs/default/bin/python
SCRIPT=<此 skill 目录>/scripts/kline.py

# 1) 日 K（60 日，含 MA5/MA20/MA60 + 成交量）
$PY $SCRIPT sh688256 day --limit 60

# 2) 周 K / 月 K
$PY $SCRIPT sh688256 week --limit 52
$PY $SCRIPT sh688256 month --limit 36

# 3) 当日 1 分钟分时
$PY $SCRIPT sh688256 minute

# 4) 新股专用：分时 + 发行价水位 + ±30%/±60% 临停线
$PY $SCRIPT sh688256 minute --issue-price 1198.00

# 5) 新股 N 日日 K + 上市日竖线 + 发行价水位
$PY $SCRIPT sh688256 day --limit 30 --issue-price 1198.00 --listing-date 2026-04-15
```

## 参数

| 参数 | 必选 | 说明 |
|---|---|---|
| `code` | ✅ | A 股代码，前缀 sh/sz/bj |
| `mode` | ✅ | `day` / `week` / `month` / `minute` |
| `--limit` | ❌ | K 线条数（minute 模式忽略） |
| `--issue-price` | ❌ | 发行价，提供后绘制水位线（橙色虚线） |
| `--listing-date` | ❌ | 上市日 YYYY-MM-DD，提供后绘制黑色竖线 |
| `--output-dir` | ❌ | 输出目录，默认 cwd |

## 输出

- 文件名：`<code>_<mode>_<时间戳>.png`
- 标准输出最后一行：`CHART_PATH:<绝对路径>`
- 失败：非零退出码 + stderr

## 视觉规范

- 红涨绿跌（A 股惯例）
- 中文字体：Arial Unicode / PingFang / STHeiti
- 主图 + 副图（成交量或分时量）
- 右上角信息盒：最新价 / 日期 / 涨跌幅（对开盘、对发行价）
- 底部水印
- 分时模式自动画 ±30%/±60% 临停阈值线（有发行价时）

## 与其他 Skill 的关系

- `ipo-workflow` 场景 4（首日盯盘）→ `minute --issue-price`
- `ipo-workflow` 场景 6（次新股研究）→ `day --limit 60 --issue-price --listing-date`
- 生成后专家应在回复中插入 `CHART_PATH` 指向的图片，附「数据源：westock-data」说明
