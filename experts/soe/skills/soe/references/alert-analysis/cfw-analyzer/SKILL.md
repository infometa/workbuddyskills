---
name: cfw-analyzer
description: 腾讯云防火墙 (CFW) 入侵防御告警日志分析。当用户提到「CFW 日志分析」「云防火墙告警」「分析 eventLog」「CFW 风险报告」「分析防火墙阻断日志」，或提供腾讯云 CFW 导出的 eventLog JSONL 文件时使用此 skill。自动产出 Markdown 分析报告，包含告警概览、风险等级分布、攻击规则 Top 榜、源/目标 IP Top 榜、方向分析（入站/出站）、处置动作分析（阻断率/可疑绕过）、攻击者画像、per-attacker case（供 L2 跨产品关联消费）、处置建议。
version: 1.0.0
triggers:
  - CFW日志分析
  - 云防火墙告警
  - CFW风险报告
  - 分析eventLog
  - 防火墙阻断日志
  - CFW
  - 云防火墙
input_formats:
  - "*.jsonl"
  - SOC导出xlsx(含CFW raw_log)
dependencies:
  - soc-alert-pipeline
---

# CFW 云防火墙告警日志分析 Skill

## 适用范围

- **日志格式**：腾讯云 CFW Syslog 导出的 **JSONL**（双层 JSON：外层 `{AppId,LogType,Tag,Msg}`，Msg 为内层 JSON 字符串需二次解析）。当前仅完整支持 **eventLog（入侵防御日志）**，其他日志类型（operateLog/natFlowLog 等）做最小归并存并标记 partial。
- **输入路径**：L0 输出的 JSONL 文件（由 `soc-alert-pipeline/l0_parse.py --product cfw` 生成），或原始 CFW JSONL 文件（自动经 L0 解析）。
- **分析层级**：L1 分析层，消费 L0 JSONL → 分析报告 + per-attacker case。

> ⚠️ **L0 输入限制**：当前 `l0_parse.py` 仅支持 xlsx 输入。若 CFW 数据在 SOC 导出 xlsx 的 `raw_log` 列（双层 JSON 字符串）中，`cfw_parser` 可直接解析；若为独立 CFW JSONL 文件，需后续增强 `l0_parse.py` 支持 jsonl 输入（待办）。

## 触发词

- "分析 CFW 日志" / "CFW 日志分析" / "云防火墙告警分析"
- "CFW 风险报告" / "生成 CFW 报告"
- "分析 eventLog" / "分析防火墙阻断日志"
- 用户提供 CFW JSONL 文件

## 执行流程

1. **确认输入**：若用户提供原始 CFW JSONL（双层 JSON），先经 L0 解析（在 `references/alert-analysis/soc-alert-pipeline/` 目录下执行）：
   ```bash
   cd references/alert-analysis/soc-alert-pipeline/
   python3 scripts/l0_parse.py <cfw.jsonl> --out l0_output/cfw_l0.jsonl --no-assets
   ```
2. **运行 L1 分析**（在 `references/alert-analysis/cfw-analyzer/` 目录下执行）：
   ```bash
   cd references/alert-analysis/cfw-analyzer/
   python3 scripts/l1_cfw_analyze.py l0_output/cfw_l0.jsonl --out report/ --emit-cases cases/
   ```
3. **生成产物**：
   - `report.md`：分析报告（Markdown），对话内可直接展示。
   - per-attacker case `.md` 文件：供 L2 `l2_correlate.py` 跨产品关联消费。
4. **回复用户**：展示关键结论摘要，附报告文件。

## 用法

> 以下命令均在 `references/alert-analysis/cfw-analyzer/` 目录下执行。

```bash
# 基本用法（报告输出到 stdout）
python3 scripts/l1_cfw_analyze.py <l0_jsonl_path>

# 输出报告 + case 文件
python3 scripts/l1_cfw_analyze.py <l0_jsonl_path> --out report/ --emit-cases cases/

# 限制 case 数量（大日志建议）
python3 scripts/l1_cfw_analyze.py <l0_jsonl_path> --out report/ --emit-cases cases/ --min-count 3 --max-cases 50
```

参数：
- `l0_jsonl`：必填。L0 输出的 JSONL 文件路径。
- `--out`：可选。报告输出目录；缺省输出到 stdout。
- `--emit-cases`：可选。输出 per-attacker case .md 目录（供 L2 消费）。
- `--top`：可选。TOP N 显示数量（默认 20）。
- `--min-count`：可选。case 输出的最小告警次数阈值（默认 1）。
- `--max-cases`：可选。case 输出的最大数量（默认无限制）。

## 报告内容

### Markdown 报告（report.md）

1. **告警概览**（总条数 / 时间范围 / AppId / 源IP数 / 目标IP数 / 方向分布 / 动作分布 / **风险等级分布**）
2. **风险等级分布**（严重 / 高危 / 中危 / 低危 占比）
3. **TOP 攻击规则**（哪些 IPS 规则命中最多，含源/目标 IP 数）
4. **TOP 攻击源 IP**（攻击者画像：告警数 / 规则数 / 目标数 / 时间范围）
5. **TOP 被攻击目标 IP**（受害资产画像）
6. **方向分析**（入站 vs 出站，**出站告警 = 可能失陷主机外连**）
7. **处置动作分析**（阻断率 / 观察+放行的高危告警 = **可疑绕过**）
8. **多向量攻击源 IP**（命中 ≥3 条规则 = 多向量攻击）
9. **处置建议**（按风险等级和方向给出针对性建议）
10. **L2 关联建议**（pivot_keys / cross_product）

### per-attacker case（供 L2 消费）

- 按攻击源 IP 聚合（非逐条输出，避免文件爆炸）
- case_id 以 `cfw_` 开头 → L2 识别 product=cfw
- 包含 `**威胁类型**` / `**置信度**` / `**Kill Chain 阶段**`
- 包含 `| 源 IP |` / `| 目的 IP:端口 |` / `| 事件时间 |` / `| 告警名称 |`
- 安全约束：**不输出 payload 原文**

## 分析维度说明

### 方向分析（CFW 独有）

- **入站（inbound, direction=1）**：外部攻击者 → 内部资产，常规告警
- **出站（outbound, direction=0）**：内部资产 → 外部，**可能是失陷主机外连 C2 / 数据外泄**
- 出站高危告警需重点关注，结合主机安全 (CWP) 关联确认是否失陷

### 处置动作分析

- **阻断（block）**：CFW 已拦截，防护有效
- **观察（observe）**：CFW 仅记录未拦截，**高危观察 = 可疑绕过**
- **放行（allow）**：CFW 放行，**高危放行 = 规则盲区**

### Kill Chain 阶段映射

根据 CFW 规则名推断：
- 侦察类（扫描/探测）→ Reconnaissance
- 利用类（注入/溢出/WebShell）→ Exploitation
- C2类（隧道/外连）→ Command and Control
- 横向移动类 → Lateral Movement

## 与其他 Skill 联动

- **上游**: `soc-alert-pipeline`（L0 适配层，解析 CFW 双层 JSON raw_log → parsed 字段，由 `cfw_parser` 完成）
- **平级**: `cwp-analyzer`（出站告警关联主机安全确认失陷）、`yujie-analyzer`（NDR 流量层交叉验证）、`tianmu-analyzer`（网络层阻断双重防护验证）、`waf-log-analyzer`（应用层攻击关联）
- **下游**: `soc-alert-pipeline` 的 `l2_correlate.py`（消费 per-attacker case 做跨产品关联）
- **资产层**: `asset-manager`（为 CFW 告警中的内网 IP 提供 IP→主机映射）

## 安全约束

- ⚠️ **不要在报告/case 里复制 payload 原文**——只展示规则名与命中情况。payload 属于敏感信息。
- ⚠️ 处置建议保持通用层级，不输出具体 payload 复现步骤。
- ⚠️ 出站告警涉及内网资产 IP，报告中外网 IP 可富化，内网 IP 不外泄。
