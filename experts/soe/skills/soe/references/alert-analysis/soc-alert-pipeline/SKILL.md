---
name: soc-alert-pipeline
version: 1.0.0
triggers:
  - SOC
  - 安全运营中心
  - raw_log解析
  - 告警流水线
  - SIEM
description: |
  SOC 告警分析流水线 (L0 适配层) - 项目级 skill

  提供腾讯安全产品 raw_log 的统一解析入口, 作为 L1 产品分析 (cwp-analyzer / yujie-analyzer) 和 L2 跨产品关联的共同底座。

  适用场景:
  - 解析从 SOC 导出的 xlsx (含 OCSF 透出字段 + raw_log)
  - 把异构 raw_log (JSON / key=value / packet hex) 统一成结构化事件
  - 跑批处理 / 单元测试 / 二次开发

  不适用:
  - 单产品深度威胁分析 → 用 cwp-analyzer / yujie-analyzer
  - 跨产品关联 → 暂未实现 (等 L1 落地)
  - 在线 SOC API 实时拉取 → 当前仅支持 xlsx 离线导入
---

# SOC 告警分析流水线 (L0 适配层)

## 一、定位

这是 **L0 适配层**, 三层架构的底座:

```
L2 跨产品关联 (soc-alert-pipeline/scripts/l2_correlate.py)    ← 已实现 v1
        ↑ 消费 L1 输出
L1 产品分析 (cwp-analyzer / yujie-analyzer / ...)
        ↑ 消费 L0 输出
L0 适配 (soc-alert-pipeline 本 skill)
    ├── 消费 SOC 导出 xlsx
    └── 调用 asset-manager 进行 IP→主机 资产关联
```

**L0 的职责**: 把 SOC 导出的 xlsx 里的 `raw_log` 字符串解析成结构化 dict, **不做任何业务判断** (不打分、不判威胁、不关联)。

## 二、目录速查

| 路径 | 用途 |
|---|---|
| `scripts/parsers/` | 各产品 L0 解析器 (注册式, 加新产品加一个文件) |
| `scripts/xlsx_reader.py` | 通用 xlsx 读取 (绕过 openpyxl 的 dimension bug) |
| `scripts/l0_parse.py` | CLI 入口, 批量解析 xlsx → JSONL (调用 asset-manager 做资产关联) |
| `scripts/packet_decode.py` | 网络包解码库 (IPv4 / UDP / GRE / WireGuard) |
| `scripts/gen_report.py` | 标准报告生成器 (HTML + ECharts, 9 段) |
| `scripts/l2_correlate.py` | L2 跨产品关联 → 攻击链还原 (v1) |
| `references/event-schema.md` | 统一事件 schema (L1 输出要遵循) |
| `references/l0-parser-contract.md` | L0 parser 的输入/输出契约 |
| `references/tencent-product-naming.md` | 腾讯产品命名 (TODO 待用户填) |
| `references/soc-export-format.md` | SOC 导出 xlsx 字段说明 |

## 三、快速开始

### 1. 解析单文件

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/l0_parse.py" \
    "<xlsx_path>" \
    --out /tmp/yujie_l0.jsonl

# 不加 --out 直接打 stdout
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/l0_parse.py" \
    "<xlsx_path>" | head -3
```

### 2. 加新产品

只需要 3 步:
1. 在 `scripts/parsers/` 下加一个 `xxx_parser.py`, 继承 `BaseParser`
2. 在 `scripts/parsers/registry.py` 注册 (`_REGISTRY[parser.PRODUCT] = parser()`)
3. 在 `references/tencent-product-naming.md` 记录产品名 (TODO)

### 3. 在 Python 里直接调用

```python
import os, sys
sys.path.insert(0, os.path.join(
    os.environ["CODEBUDDY_PLUGIN_ROOT"],
    "skills/soe/references/alert-analysis/soc-alert-pipeline/scripts"
))
from parsers.registry import get_parser

parser = get_parser("yujie")
result = parser.parse(raw_log_str, ocsf_fields={"src_ip": "10.0.0.4"})
print(result.to_dict())
```

## 四、当前支持的产品

| product code | 产品 | 输入格式 | parser 文件 | L1 analyzer |
|---|---|---|---|---|
| `yujie` | 御界 (高级威胁检测 / NDR) | SOC xlsx (raw_log JSON) | `parsers/yujie_parser.py` | `yujie-analyzer/` |
| `cwp` | 主机安全 (云镜 / CWP) | SOC xlsx (raw_log key=value) | `parsers/cwp_parser.py` | `cwp-analyzer/` |
| `tianmu` | 天幕 (安全治理) | 天幕直出 xlsx (中文列头, 无 raw_log) | `parsers/tianmu_parser.py` | `tianmu-analyzer/` |
| `waf` | WAF (Web 应用防火墙) | WAF 直出 CSV/XLSX (中文列头, 12 字段) | `parsers/waf_parser.py` | `waf-log-analyzer/` |

> **输入格式说明**:
> - SOC 导出 xlsx: 含 `raw_log` 列, 御界/主机安全走此路径
> - 直出格式 (天幕/WAF): 无 `raw_log`, 中文列头, `l0_parse.py` 按列头关键词自动识别产品

> ⚠️ 产品代号 (yujie / cwp / tianmu / waf) 是合理推断, **需要你对照腾讯产品命名文档确认**。代码里所有 product 字段加了 TODO 注释, 你确认后直接改 `BaseParser.PRODUCT` 即可。

## 五、与 L1 的接口约定

L0 输出 (`ParseResult.parsed` dict) 是 L1 的输入。L1 必须能消费以下两种最小字段集:

**网络事件 (yujie)**:
```python
{
    "src_ip", "src_port", "dst_ip", "dst_port",
    "real_attacker_ip", "real_victim_ip",  # NAT 还原
    "ip_discrepancy",                      # bool
    "encapsulation": {"gre": {...}},
    "packet_header": {...},                 # 解析后的网络包头
    "flow_stats": {...},
    "app_proto", "rule_id", "rule_name",
    "score", "vpcid", "event_timestamp",
}
```

**主机事件 (cwp)**:
```python
{
    "src_ip", "src_port", "dst_ip", "dst_port",
    "host_ip", "process", "process_path", "cmd", "user",
    "event_type", "status",
    "event_time", "event_time_iso",
    "_raw_kv": {...},  # 完整 kv 供 L1 兜底
}
```

**WAF 攻击事件 (waf)**:
```python
{
    "src_ip",              # 攻击IP
    "victim_domain",       # 被攻击域名
    "http_uri", "http_method", "user_agent", "appid",
    "rule_name",           # 攻击类型
    "attack_payload",      # 攻击内容 (L0 保留, L1 输出时不复制原文)
    "action", "action_raw",       # 归一 / 原值 (block/observe/allow)
    "severity", "risk_level_raw", # 归一 / 原值 (high/medium/low)
    "event_time", "event_time_raw",
    "has_obfuscation", "is_simple_payload",  # payload 特征标记
    "real_attacker_ip",    # = src_ip (WAF 无 NAT)
    "protocol", "app_proto",       # tcp / http
}
```

详细 schema 见 `references/event-schema.md`。

## 六、资产关联

资产查询已独立为 **`asset-manager`** skill, 本 skill 在 L0 解析时自动调用其 API。

```bash
# 自动调用 asset-manager (两级 fallback)
python3 l0_parse.py input.xlsx --out output.jsonl

# 手动指定资产目录
python3 l0_parse.py input.xlsx --assets /path/to/my-assets/

# 跳过资产关联 (性能模式)
python3 l0_parse.py input.xlsx --no-assets
```

详见 `../asset-manager/SKILL.md`。

## 七、约束与禁止

- **L0 不读文件**: 解析函数只接受字符串, 由调用方 (l0_parse.py) 读 xlsx 后传入
- **L0 不写网络**: 离线运行, 不会主动连接 SOC / API
- **L0 不做时间归一化**: 时间字段保留字符串原值, L1 决定怎么归一
- **L0 不判威胁**: 只还原事实, 命中规则的事 L1 做

## 八、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-15 | 新增 WAF parser (`waf_parser.py`) + 注册 | 支持 WAF 攻击日志直出 CSV/XLSX 解析 |
| 2026-07-15 | `l0_parse.py` 支持 `.csv` 输入 (不只 xlsx) | WAF 攻击日志原生格式是 CSV |
| 2026-07-15 | `l0_parse.py` 支持 WAF 直出格式识别 (中文列头) | WAF 无 raw_log, 按列头关键词识别 |
| 2026-07-09 | 资产查询独立为 asset-manager skill | 解耦资产数据与告警分析逻辑 |
| 2026-07-09 | 资产库两级 fallback + CODEBUDDY_PLUGIN_DATA | 资产数据独立存储, 不随 skill 分发 |
| 2026-07-06 | 初始化 L0 骨架 | 支持御界 + 主机安全 raw_log 解析 |
| TODO | 增加 CFW parser | CFW eventLog JSONL (双层 JSON), cfw-analyzer 在等这个 |
