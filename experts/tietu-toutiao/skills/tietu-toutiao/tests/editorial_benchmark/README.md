# 编辑基准集 v1（editorial benchmark）

> 对应升级方案 W13 / 交付清单第 13 条。目标：**10 份真实报纸标注**，
> 保证换模型、升版本、改排版算法后编辑质量不倒退。

## 诚实原则（不可协商）

- 指标只来自真实标注的 case 文件；case 数不足 `--min-cases` 时脚本报错退出
  （exit 3），**绝不**用少量样本冒充达标率，也**绝不**自动降低门槛凑数。
- 每份 case 的 expected 标注必须来自人工（老杜确认过的版面理解），
  模型输出不得反向写进 expected。
- 跑分结果附每个 case 的逐维明细，不合格项给出差异点，不做聚合后不可解释
  的单一数字。

## case 目录结构

```
tests/editorial_benchmark/
  cases/
    cases_manifest.json        # 已注册 case 清单（脚本据此发现 case）
    <case_id>/
      expected.json            # 人工标注 ground truth
      state.json               # 待评测的模型产出 content-state v2
      (可选) cover_*.png       # 模型产出的头图，供人工复查
```

### expected.json 结构

```json
{
  "case_id": "mzb-2026-08-31-front",
  "source": "原始版面图文件名（只读引用）",
  "expected_headline_text": "报纸原标题（逐字）",
  "expected_items": [
    { "id": "i1", "headline": "条目标题（逐字）" }
  ],
  "expected_photo_bbox": { "x": 0, "y": 0, "w": 0, "h": 0 },
  "notes": "人工备注（可选）"
}
```

### cases_manifest.json 结构

```json
{ "cases": ["mzb-2026-08-31-front", "..."], "min_cases_target": 10 }
```

## 评分维度（每 case 三维，全部通过才算该 case 通过）

| 维度 | 判定 | 阈值 |
|------|------|------|
| headline_agree | state 主标题与 expected 逐字一致（仅规范化空白/全半角） | 完全一致 |
| item_agree | state.items 标题集合与 expected_items 标题集合的重合率 | ≥ 0.5 |
| bbox_fidelity | state 引用图片 bbox 与 expected_photo_bbox 的 IoU | ≥ 0.8 |

## 用法

```bash
# 常规跑分（v1 目标 10 份，不足即报错）
python scripts/test_pipeline.py 之外的基准入口：
python tests/editorial_benchmark/benchmark_score.py \
  --benchmark-dir tests/editorial_benchmark \
  --min-cases 10 --min-agree 0.8

# 自检模式（case 不足时明确报出缺口，用于开发期）
python tests/editorial_benchmark/benchmark_score.py --min-cases 2 --report -
```

退出码：0 全部通过；1 agree_rate 低于阈值；2 case 结构错误（缺文件/坏 JSON）；
3 case 数不足 `--min-cases`（防冒充门禁）。

## v1 建集计划

真实标注随 W17 发布 e2e 逐份灌入：每处理一份真实 8-PDF 素材，人工确认
layout_analysis 与条目选择后，把确认结果固化为一份 case 的 expected.json。
case 数在 cases_manifest.json 里实时反映，达到 10 份前跑分脚本始终
exit 3——这是特性不是缺陷。
