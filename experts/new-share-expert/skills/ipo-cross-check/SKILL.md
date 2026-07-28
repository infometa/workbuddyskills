---
name: ipo-cross-check
description: A 股新股关键字段多源交叉验证。对发行价、申购日、上市日、行业、名称等字段从 westock-data + NeoData 两个数据源同时拉取并对比，自动输出结构化校验报告。触发词：交叉验证、多源比对、校验、核对发行价、核对上市日期、数据可靠性
---

# 新股关键字段多源交叉验证

## 用途

对单只 A 股新股的关键事实字段做多源比对，确保数据可溯源、可校验、不臆造。

## 调用命令

```bash
# 推荐使用 managed venv 的 python，已含 requests
PY=~/.workbuddy/binaries/python/envs/default/bin/python

$PY <此 skill 目录>/scripts/cross_check.py <code> [--name <名称>]

# 示例
$PY <此 skill 目录>/scripts/cross_check.py sz301669 --name 高特电子
```

## 校验字段

| 字段 | westock 来源 | NeoData 来源 | 判定 |
|---|---|---|---|
| 名称 | `search` 或 `ipo hs` | NeoData 召回 | 字符串相等 |
| 申购日 | `ipo hs` sgrq | NeoData 召回 | 字符串相等 |
| 上市日 | `ipo hs` ssrq | NeoData 召回 | 字符串相等 |
| 发行价 | `ipo hs` price | NeoData 召回 | 数值相对差异 < 1% |
| 行业 | `ipo hs` hy | NeoData 召回 | 中文关键词重叠 |

## 输出

- 一致：标注「✅」
- 差异 / 单源缺失 / 两源均缺：标注「⚠️」+ 具体原因
- 报告末尾给出「差异条数」和「用户复核建议」

## 退出码

- 0：完成（无论一致或差异）
- 1：参数错误
- 2：westock 失败
- 3：NeoData 失败
- 4：两源均失败

## 与其他 Skill 的关系

- `ipo-workflow` 场景 2「事实矩阵」中，在填 A 段前必调用
- 若发现差异，事实矩阵 A 段的「多源校验结果」行必须原样写入
