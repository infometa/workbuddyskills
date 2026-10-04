# Audit output contract

```json
{
  "kind": "listingAuditReport",
  "schema_version": 2,
  "target": {"asin": "B0...", "marketplace": "US"},
  "scorePanel": {},
  "aiReadiness": {},
  "diagnosticLenses": [
    {
      "key": "funnel",
      "state": "ok|warn|bad|na",
      "confidence": "verified|partial|unavailable",
      "findings": []
    }
  ],
  "auditHandoff": {
    "kind": "listingAuditHandoff",
    "schema_version": 1,
    "target": {"asin": "B0...", "marketplace": "US"},
    "source_listing_path": "/abs/listing-normalized.json",
    "evidence_paths": {},
    "field_actions": [],
    "operational_actions": [],
    "locked_fields": [],
    "data_freshness": {"captured_at": "ISO-8601", "cache_window_hours": 24}
  },
  "rewrite_ready": true,
  "next_actions": []
}
```

`diagnosticLenses` 允许 `ai_shopping_assistant`、`mobile_visual`、`voc`、`funnel`、`architecture`。这些视角解释问题，但不生成第二套 overall，也不改变 canonical scorePanel。

当上层场景是“诊断并优化”时，同一次语义响应还必须形成 Core S3 所需的 `keywords.json`、`buyer-questions.json` 和 `insight.md`，并把三个绝对路径写入 `auditHandoff.evidence_paths`。它们与诊断共用同一 Product Detail、评论和 SIF 快照；禁止再起一轮重复洞察。

语义阶段允许先产生宽松 JSON，但保存或交给 Core 前必须执行：

```bash
python3 scripts/normalize_audit_report.py \
  --source /abs/raw-audit.json \
  --out /abs/listing-audit-report.json \
  --workspace-root "$PWD"
```

脚本会把历史 `target_asin/reason` 等字段归一为正式契约、把证据路径解析为绝对路径，并为所有改写动作补上事实与最终复检守门。任一目标冲突、路径缺失或字段动作无效都会失败；失败时不得提供直接改写入口。

每条 finding：

```json
{
  "severity": "high|medium|low",
  "observation": "...",
  "evidence": [{"source": "...", "value": "..."}],
  "impact": "...",
  "action_type": "field|operational|data_gap",
  "action": "...",
  "confidence": "verified|partial"
}
```

默认输出 Markdown + JSON。评分只使用同一份 canonical `scorePanel`，展示层不得重算。
