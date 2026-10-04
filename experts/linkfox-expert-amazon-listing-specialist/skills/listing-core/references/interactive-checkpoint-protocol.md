# Listing Interactive Checkpoint Protocol

完整 Listing 编排的确认点协议适用于 `listing-core` 的 benchmark、rewrite、create 与 batch；历史入口只能转发到 Core，不得维护独立确认流程。

不适用本协议的场景：

- 批量快速任务：批量改标题、补 Item Highlights、字段清洗、字符数校验、Excel/飞书回写等，只做一次输入确认或直接分块执行，不对每行或每个 listing 设置大量选择。
- 工具型报告任务：用户上传已写好的 Listing、ASIN 链接、PDF/HTML/Excel 文档，只要求“检查/评分/诊断/生成报告”时，直接进入报告模式，不插入 L3→L4 写作确认点。
- 已有用户明确选择后的续跑：sandbox 回传选择后继续执行，不再次产出同一 checkpoint。

## Canonical stage names

对用户和新说明只使用以下命名：

| Stage | Name | Purpose |
|------|------|---------|
| L1 | 输入确认 | 识别 ASIN、站点、语言、模式、批量范围和必要授权 |
| L2 | 数据采集 | 拉取商品、竞品、图片搜索、关键词矩阵、评论或表格输入 |
| L3 | 策略分析 | 整理关键词、竞品、诊断、卖点、对标维度和写作策略 |
| Checkpoint | 交互确认 | 用户选择复刻方式、关键词布局、保留重点、写作角度或批量范围 |
| L4 | 文案生成 | 调用 writer 生成 title、Item Highlights、bullets、description、search terms |
| L5 | 质检交付 | 合规、差异度、反聚类、报告组装和 HTML 渲染 |

历史文档中的 `Phase A/B/C/D`、`C.x/D.x`、`Step 2/Step 3` 仅视为旧别名。新文案和用户可见进度不得继续使用这些旧名：

| Legacy alias | Canonical stage |
|-------------|-----------------|
| Phase A | L1 输入确认 |
| Phase B | L2 数据采集 |
| Phase C 的分析/诊断/卖点部分 | L3 策略分析 |
| Phase C 的 writer 生成部分 | L4 文案生成 |
| Phase D | L5 质检交付 |
| Step 2 | L3 中间策略产物 |
| Step 3 | L5 最终报告 |

## auto_run

- 默认 `auto_run=true`。完整 Listing 编排一气呵成跑完，不在 L3 后停策略确认点。
- 仅当用户在本轮指令中明确要求「分步确认 / 每步和我确认 / 需要断点 / stepwise / confirm each step」等分步执行意图时，才设置 `auto_run=false`，在 L3 产出会影响写作方向的策略结果后停在交互确认点。
- 用户从 sandbox 回传 `[Listing交互断点选择]` 或 `[关键词矩阵用途选择]` 后，不重新判断 `auto_run`，也不重跑同参数的 L2/L3 检索。

## Required checkpoints

根据实际产物出现情况设置最近的确认点，不要求全部出现：

| Scenario | Checkpoint timing | Required choices |
|---------|-------------------|------------------|
| benchmark | L2 商品详情 + keyword matrix 完成、L3 卖点/对标策略落盘后，L4 writer 前 | 复刻方式、写作风格、关键词布局 |
| rewrite | L3 诊断评分和问题清单落盘后，L4 优化生成前 | 保留/迁移重点、关键词补强方向、改写强度 |
| create/newlisting | L2 图片搜竞品/类目节点 + L3 事实清单/关键词布局完成后，L4 writer 前 | 参考方式、关键词布局、待确认事实处理方式 |
| batch | L1 批量输入解析完成后，L2 批量执行前；必要时 L3 批量策略后，L4 前 | 商品范围、执行模式、并发/成本、是否继续全量 |

批量完整 listing 只在批次级设置确认点。不要让用户为每一个商品重复选择复刻方式、关键词布局或写作角度；除非用户主动进入某个单品做二次精修。

若数据置信度门禁判定 `unavailable`，失败确认优先级高于策略确认：先用 `AskUserQuestion` 让用户选择重试、facts_only 或终止。

## Artifact contract

每个策略确认点必须额外落盘一个 JSON 产物，slug 固定为 `listing-decision-checkpoint`，供 sandbox 特殊渲染：

```bash
node <agent-listing-result-html-skill>/scripts/save-text-artifact.mjs \
  --stdin \
  --slug=listing-decision-checkpoint \
  --ext=json \
  --label="JSON artifact" <<'EOF'
{
  "type": "listingDecisionCheckpoint",
  "checkpoint": "keyword_matrix",
  "title": "关键词矩阵用途选择",
  "summary": "已生成关键词矩阵，选择后会复用当前矩阵继续写作，不会重复付费检索。",
  "multiSelect": true,
  "options": [
    {
      "id": "title",
      "label": "用于标题",
      "description": "优先把核心品类词放入 Title 与 Item Highlights。",
      "prompt": "[关键词矩阵用途选择]\n用途：标题\n请复用当前关键词矩阵继续，不要重跑 listing-keyword-matrix-build。"
    }
  ],
  "context": {
    "sourceArtifacts": {
      "keywordMatrixPath": "/absolute/path/to/matrix.json"
    }
  }
}
EOF
```

Rules:

- `context.sourceArtifacts` 必须使用脚本 stdout 打印过的真实绝对路径，不得写相对路径。
- 真实中间产物仍按各 skill 原脚本落盘；decision checkpoint 只负责 UI 展示与选择回灌。
- 同一候选集只产出一次 checkpoint。用户选择后继续 L4，不要再次产出同一个 checkpoint。
- 若用户调整导致候选集或关键词矩阵发生变化，可以产出新的 checkpoint。
- 命名必须匹配选项含义：`对标差异化 / 直接复刻强化 / 礼品场景优先` 这类选项属于 `复刻方式`，不得命名为 `关键词用途`；只有“用于标题/五点/描述/搜索词”等字段分配类选项才可命名为 `关键词用途` 或 `关键词布局`。

## Preservation rules

- 不改变原有并发：benchmark 的商品详情与关键词矩阵仍必须并行；batch 的行级并发仍按配置执行。
- 不改变原有分支：benchmark / rewrite / create 的触发条件、facts_only 降级、批量局部处理绕过完整报告链路等规则保持不变。
- 不改变成本预算：同一 ASIN/region/time_window 的 matrix、以图搜竞品、SIF 检索失败或空结果也视为已消耗；继续检索前必须询问用户。
