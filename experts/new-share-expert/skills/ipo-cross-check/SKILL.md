---
name: ipo-cross-check
description: |
  A 股新股关键字段多源交叉验证工具。对发行价、申购日、上市日、行业、名称等字段从 westock-data 与 NeoData 两个数据源同时拉取并对比，输出结构化校验报告。
  触发词：交叉验证、多源比对、校验、核对发行价、核对上市日期、数据可靠性、数据来源
---

# IPO 多源交叉校验

## 功能说明

对单只 A 股新股的关键事实字段做多源比对，确保数据可溯源、可校验、不臆造。比对结果分三类：一致（✅）、差异（⚠️ 同时输出两边值）、单源缺失（⚠️ 标注缺失方）。

## 调用方式

```bash
# 在 skill 目录下执行（推荐 managed venv 的 python，已含 requests）
cd <skill-dir>
python3 scripts/cross_check.py <code> [--name <名称>] [--json]
```

> `<skill-dir>` 即本 skill 安装目录。专家运行时由 Agent 通过 Bash 工具调用，需先 cd 到本目录。

## 支持的参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `code` | ✅ | A 股代码，前缀 sh/sz/bj |
| `--name` | 否 | 股票名称，提升 NeoData 召回准确率 |
| `--json` | 否 | 输出 JSON 而非 Markdown 表格 |

## 校验字段

| 字段 | westock 来源 | NeoData 来源 | 判定规则 |
|---|---|---|---|
| 名称 | `ipo hs` 或 `search` | 召回文本 | 字符串相等 |
| 申购日 | `ipo hs` sgrq | 召回文本正则 | 字符串相等 |
| 上市日 | `ipo hs` ssrq | 召回文本正则 | 字符串相等 |
| 发行价 | `ipo hs` price | 召回文本正则 | 数值相对差异 < 1% |
| 行业 | `ipo hs` hy | 召回文本正则 | 中文关键词重叠 |

## 输出格式

结构化 Markdown 表格，末尾附「差异条数」与「用户复核建议」：

```
═══ 多源交叉校验报告 ═══
代码：sz301669    名称：高特电子
westock 状态：OK
NeoData 状态：OK

| 字段 | westock | NeoData | 一致 |
| --- | --- | --- | --- |
| 名称 | 高特电子 | 高特电子 | ✅ |
| 发行价 | 7.08 | 7.080 | ✅ |
...

总结：✅ 关键字段一致 / ⚠️ 共 N 个字段存在差异，请用户根据券商发行公告复核
数据时间：YYYY-MM-DD HH:MM:SS
来源：westock-data（ipo hs / search）｜ NeoData query
```

## 退出码

- 0：校验完成（无论一致或差异）
- 1：参数错误
- 2：westock 调用失败
- 3：NeoData 调用失败
- 4：两源均失败
