# 御界事件分析 - {event_id}

> 生成时间: {generated_at}
> 来源: {source_file} row={row}

## 1. 事件元数据

| 字段 | 值 |
|---|---|
| 规则 | ? |
| 严重度 (OCSF) | - |
| 置信度 (OCSF) | - |
| 御界 score | - |
| DPI 协议 | - |
| 事件时间 | - |

## 2. 网络五元组 (OCSF vs NAT 还原)

| 视角 | 源 | 目的 |
|---|---|---|
| **OCSF 透出** | ?:? | ?:? |
| **真实 (NAT 还原)** | ?:? | ?:? |

## 3. NAT 链分析

- **封装链**: ?
- **攻击者 IP 性质**: ?
- **受害 IP 性质**: ?
- **还原可信度**: ?
- **分析**: ?

## 4. 协议与流量特征

**包结构**:
```json
{}
```

**流统计**:
```json
{}
```

## 5. 威胁判定

- **威胁类型**: ?
- **TTP**: ?
- **置信度**: ?
- **Kill Chain 阶段**: ?
- **检测器**: ?

## 6. 处置建议

- [ ] 隔离 → 排查 → 恢复 → 加固

## 7. 关联建议 (供 L2 消费)

```yaml
threat:
  threat_type: null
  confidence: 0
  kill_chain_phase: null
  mitre_attack: []
  iocs:
    ips: []
  correlation_hints:
    pivot_keys: []
    time_window_min: 60
    rationale: ""
```

## 8. 附录: 原始数据

```json
{}
```
