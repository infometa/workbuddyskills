---
name: tianmu-analyzer
version: 1.0.0
triggers:
  - 天幕
  - 安全治理
  - 阻断日志
  - NDR阻断
description: |
  天幕 (安全治理) 阻断日志 L1 分析 skill

  消费 L0 适配层 (soc-alert-pipeline) 输出的 parsed 字段,
  基于天幕阻断日志的聚合统计, 产出:
    - 阻断概览 (总阻断次数 / 规则数 / 源IP数 / 目标IP数)
    - TOP 阻断规则排名
    - 攻击者画像 (高频源IP / 多规则命中 / 多目标攻击)
    - 被攻击目标排名
    - 误报识别 (黑名单 vs 规则类)
    - 处置建议 (加黑 / 放行 / 调规则)
    - L2 关联建议 (天幕阻断 ↔ 御界检测 ↔ 主机安全)

  适用场景:
  - 天幕安全治理阻断日志的批量分析
  - 攻击者画像与高频阻断源识别
  - 阻断规则效果评估与误报筛查

  不适用:
  - 天幕 xlsx 解析 (用 soc-alert-pipeline L0)
  - 跨产品关联 (用 L2, 消费本 skill 的 correlation 输出)
---

# tianmu-analyzer (L1 天幕安全治理)

## 一、定位

这是 L1 产品分析 skill, 在 L0 适配层之上:

```
天幕阻断日志 xlsx (直出格式, 无 raw_log)
      ↓
soc-alert-pipeline (L0, tianmu_parser)  →  parsed dict
      ↓
tianmu-analyzer (L1, 本 skill)  →  阻断分析报告 (Markdown)
      ↓
L2 关联 (天幕阻断 ↔ 御界检测 ↔ 主机安全)
```

## 二、天幕数据特点

与御界/主机安全不同, 天幕的数据是**聚合阻断统计**:

| 维度 | 御界/主机安全 | 天幕 |
|---|---|---|
| 数据粒度 | 单次检测事件 | 聚合统计 (规则+源IP+目标IP) |
| 动作 | 检测/告警 | **阻断** |
| 每行含义 | 一次事件 | 累计阻断次数 |
| 时间字段 | 事件时间 | 首次/最新告警时间范围 |

因此 L1 分析逻辑是**批量聚合统计**, 而非逐条 TTP 检测.

## 三、分析维度

| 维度 | 内容 | 输出 |
|---|---|---|
| 阻断概览 | 总阻断次数/规则数/源IP数/目标IP数 | 表格 |
| TOP 规则 | 哪些规则命中最多 | 排名表 |
| 攻击者画像 | 高频源IP/多规则命中/多目标攻击 | 排名表 + 风险标注 |
| 被攻击目标 | 哪些目标IP被攻击最多 | 排名表 |
| 误报识别 | 黑名单(低风险) vs 规则类(中风险) | 规则表标注 |
| 处置建议 | 加黑/放行/调规则 | checklist |
| L2 关联 | 天幕阻断 ↔ 御界/主机安全 | YAML |

## 四、快速开始

```bash
# 1. 先用 L0 跑一遍 (天幕 xlsx → JSONL)
python3 ../soc-alert-pipeline/scripts/l0_parse.py \
    <天幕xlsx> --out /tmp/tianmu_l0.jsonl --no-assets

# 2. 用 L1 分析 (生成报告)
python3 scripts/l1_tianmu_analyze.py /tmp/tianmu_l0.jsonl --out report.md

# 3. 查看报告
cat report.md
```

## 五、天幕规则分类

| 规则前缀 | 类型 | 误报风险 | 说明 |
|---|---|---|---|
| GB0xxxx | 黑名单类 | 低 | 已知恶意IP, 阻断合理 |
| GB1xxxx | 特征匹配类 | 中 | 需确认是否误报 |
| GB2xxxx | 行为类 | 中 | 需确认攻击行为是否真实 |

详见 `references/tianmu-rules.md`.

## 六、与 L0 / L2 的接口

**L0 → L1 输入** (`parsed` dict):
```python
{
    "rule_id": "GB00002",
    "first_alert_time": "2026-06-24T05:47:52-03:00",
    "last_alert_time": "2026-07-07T23:40:01-03:00",
    "alert_source": "黑名单",
    "status": "已拦截（已发送阻断报文）",
    "block_count": 141,
    "protocol": "tcp",
    "src_ip": "223.71.46.114",
    "src_port": 44066,
    "dst_ip": "109.244.106.31",
    "dst_port": 80,
    "http_host": null,
    "http_uri": null,
    "action": "block",
    "action_result": "blocked",
    "is_aggregated": true,
    "event_time": "2026-07-07T23:40:01-03:00",
    ...
}
```

**L1 → L2 输出** (报告末尾 YAML):
```yaml
correlation:
  product: tianmu
  pivot_keys:
    - ip: "223.71.46.114"
  time_window_min: 60
  rationale: "天幕阻断的源IP, 在御界/主机安全是否有对应检测告警"
  cross_product:
    - yujie: 查 src_ip 是否有流量检测告警
    - cwp: 查 src_ip 是否有主机入侵告警
```
