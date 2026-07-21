---
name: waf-log-analyzer
version: 2.0.0
triggers:
  - WAF
  - 攻击日志
  - attacklog
  - WAF风险报告
description: 腾讯云 WAF 攻击日志分析 (L1 层)。当用户提到「WAF 攻击日志分析」「分析 WAF 日志」「WAF 风险报告」「分析 attacklog」，或提供腾讯云 WAF 导出的 attacklog-*.csv / 攻击日志*.xlsx 文件/目录时使用此 skill。消费 L0 适配层 (soc-alert-pipeline) 输出的 JSONL，自动产出 Markdown 简版报告 + HTML 详版可视化报告 + per-attacker case (供 L2 跨产品关联消费)，包含统计概览、风险等级分布、攻击类型/源 IP/URI Top 榜、配置异常告警（observe-only 域名）、扫描器/已知漏洞探测指纹、真实性研判、攻击者画像、可疑绕过检测、威胁情报富化、业务影响评估，以及按攻击类型给出的通用处置建议。
dependencies:
  - soc-alert-pipeline
---

# WAF 攻击日志分析 Skill (L1)

## 一、定位

这是 **L1 产品分析 skill**, 在 L0 适配层之上, 与其他 4 个 analyzer (cwp/yujie/tianmu/cfw) 架构一致:

```
腾讯云 WAF CSV/XLSX (中文列头, 12 字段)
      ↓
soc-alert-pipeline (L0, waf_parser.py)  →  parsed dict (扁平 JSONL)
      ↓
waf-log-analyzer (L1, 本 skill)  →  分析报告 + per-attacker case
      ↓
L2 关联 (soc-alert-pipeline/scripts/l2_correlate.py)
```

**L0 的职责**: 把 WAF CSV/XLSX 的中文列头映射成统一 schema (英文键), 归一化动作/风险等级/时间, 不做威胁判断。

**L1 的职责** (本 skill): 消费 L0 JSONL, 做真实性研判 / 配置异常检测 / 扫描器指纹识别 / 处置建议, 输出报告 + case。

## 二、适用范围

- **日志格式**: 腾讯云 WAF 控制台导出的中文 **CSV 或 XLSX**（字段：`攻击IP,被攻击域名,URI,方法,攻击类型,攻击内容,UserAgent,APPID,uuid,动作,风险等级,攻击时间`）。其他格式直接报错退出，不做兼容。
- **输入路径**: L0 输出的 JSONL 文件（由 `soc-alert-pipeline/l0_parse.py --product waf` 生成）。
- **分析层级**: L1 分析层，消费 L0 JSONL → 分析报告 + per-attacker case。

## 三、触发词

- "分析 WAF 攻击日志" / "WAF 攻击日志分析" / "WAF 日志分析"
- "WAF 风险报告" / "生成 WAF 报告"
- "分析 attacklog" / 用户提供 `attacklog-*.csv` 或 `攻击日志*.xlsx`

## 四、执行流程

1. **L0 解析**（在 `references/alert-analysis/soc-alert-pipeline/` 目录下执行）:
   ```bash
   cd references/alert-analysis/soc-alert-pipeline/
   python3 scripts/l0_parse.py <attacklog.csv> --out l0_output/waf_l0.jsonl --product waf --no-assets
   ```
   > WAF 是应用层日志, 无内网资产关联需求, 建议加 `--no-assets` 加速。

2. **L1 分析**（在 `references/alert-analysis/waf-log-analyzer/` 目录下执行）:
   ```bash
   cd references/alert-analysis/waf-log-analyzer/
   python3 scripts/l1_waf_analyze.py l0_output/waf_l0.jsonl --out report/ --emit-cases cases/
   ```

3. **生成产物**:
   - `report.md`：简版概要，对话内可直接展示。
   - `report.html`：详版可视化报告（含 SVG 图表、KPI 卡片、攻击者画像、威胁情报富化）。
   - per-attacker case `.md` 文件：供 L2 `l2_correlate.py` 跨产品关联消费。

4. **回复用户**：展示关键结论摘要，附报告文件。

## 五、用法

> 以下命令均通过 `${CODEBUDDY_PLUGIN_ROOT}` 环境变量定位 skill 脚本，禁止硬编码任何本机绝对路径。

### 完整流程 (L0 → L1)

```bash
# Step 1: L0 解析 (CSV → JSONL)
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/l0_parse.py" \
  "/path/to/attacklog-1780556626.csv" \
  --out /tmp/waf_l0.jsonl \
  --product waf \
  --no-assets

# Step 2: L1 分析 (JSONL → 报告 + case)
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/soe/references/alert-analysis/waf-log-analyzer/scripts/l1_waf_analyze.py" \
  /tmp/waf_l0.jsonl \
  --out /tmp/waf-report/ \
  --emit-cases /tmp/waf-cases/ \
  --no-enrich
```

### 仅 L1 (已有 L0 JSONL)

```bash
# 基本用法 (报告输出到 stdout)
python3 scripts/l1_waf_analyze.py <l0_jsonl_path>

# 输出报告 + case 文件
python3 scripts/l1_waf_analyze.py <l0_jsonl_path> --out report/ --emit-cases cases/

# 限制 case 数量 (大日志建议)
python3 scripts/l1_waf_analyze.py <l0_jsonl_path> --emit-cases cases/ --min-count 3 --max-cases 50
```

Windows 环境下 `${CODEBUDDY_PLUGIN_ROOT}` 同样生效，无需切换为反斜杠路径。

### 参数

**l0_parse.py 参数**:
- `input`：必填。`.csv` 或 `.xlsx` 文件路径。
- `--out`：可选。输出 JSONL 文件路径；缺省输出到 stdout。
- `--product waf`：强制指定产品为 waf（跳过自动识别）。
- `--no-assets`：可选。跳过资产关联（WAF 建议加，加速）。

**l1_waf_analyze.py 参数**:
- `l0_jsonl`：必填。L0 输出的 JSONL 文件路径。
- `--out`：可选。报告输出目录；缺省输出到 stdout。
- `--emit-cases`：可选。输出 per-attacker case .md 目录（供 L2 消费）。
- `--min-count`：可选。case 输出的最小告警次数阈值（默认 1）。
- `--max-cases`：可选。case 输出的最大数量（默认无限制）。
- `--no-enrich`：可选。跳过威胁情报富化（默认会对公网 IP 调用 ip-api.com 免费接口，每分钟 ≤45 次）。**对于大日志（>1000 条）建议先用 `--no-enrich` 快速出结果，再按需复跑富化。**

## 六、报告内容

### Markdown 简版（report.md）
1. 数据概览（总条数 / 时间范围 / 域名数 / 攻击 IP 数 / 动作分布 / **风险等级分布**）
2. **真实性研判**（启发式判定：测试流量 / 自动化扫描 / 真实定向攻击）
3. 攻击类型 Top10
4. 源 IP Top10（含归属地）
5. 被攻击 URI Top10
6. **配置异常告警**：识别整域 observe-only 的高危配置异常
7. **扫描器/已知漏洞探测指纹**：Nmap / masscan / zgrab / Nuclei / sqlmap / Nikto / Acunetix / Censys / xray 等 UA 指纹 + HNAP / phpunit eval-stdin / .git / .env / actuator / druid / swagger / phpmyadmin / wordpress / solr / jenkins / vmware sdk 等已知弱点 URI 指纹
8. 可疑绕过 / 观察模式记录（已自动剔除"配置异常"那批，避免 false positive）
9. 业务影响（按域名）
10. 通用处置建议（按攻击类型给出针对性建议）

### HTML 详版（report.html）
- 顶部 KPI 卡片：总攻击数、拦截率、独立 IP 数、覆盖时长、**高危记录数**
- **真实性研判面板**：判定结论 + 五维度证据卡
- **攻击类型饼图**（纯 SVG，无外部依赖）
- **时间分布折线图**（按小时聚合）
- **攻击者画像**：每个 Top IP（前 15）的攻击节奏、UA、目标域名、攻击类型组合
- **配置异常告警**：observe-only 域名表
- **扫描器指纹表**：UA + URI 双维度
- **可疑绕过检测**：剔除配置异常后的真绕过事件
- **业务影响评估**：按 域名/APPID 分组的攻击量与高危占比
- **威胁情报富化**：公网 IP 的 ASN / 国家 / 组织 / 是否数据中心
- **通用处置建议**：按攻击类型折叠展示
- 攻击明细表（前 200 行，可折叠）

### per-attacker case（供 L2 消费）

- 按攻击源 IP 聚合（非逐条输出，避免文件爆炸）
- case_id 以 `waf_` 开头 → L2 识别 product=waf
- 包含 `**威胁类型**` / `**置信度**` / `**Kill Chain 阶段**`
- 包含 `| 源 IP |` / `| 事件时间 |` / `| 告警名称 |`
- 包含 `correlation_hints`（pivot_keys / time_window_min），供 L2 跨产品关联
- 安全约束：**不输出 payload 原文**

## 七、真实性研判规则（启发式）

判定为 **测试流量** 的信号（命中 ≥3 条即判为测试）：
1. 全部源 IP 落在保留段（10/8、172.16/12、192.168/16、127/8）
2. UA 单一且为常见命令行工具（curl/wget/python-requests/postman）
3. Payload 全部为最简形态（`alert(1)`、`1 union select`、`id=1 and 1=1` 等教科书载荷）
4. 域名包含 `test/demo/dev/staging/ngwaftest` 关键词
5. 攻击类型分布过于均衡（明显是逐个规则验证）
6. 自定义策略命中比例 >30%

判定为 **真实定向攻击** 的信号（命中 ≥2 条即判为真实）：
1. 存在公网 IP（且非已知扫描器云厂商 IP 段）
2. 多种 UA 轮换 / UA 高度伪装
3. Payload 含混淆/编码（URL/Base64/十六进制/Unicode）
4. 单 IP 覆盖多类攻击类型（侦察 → 利用模式）
5. 存在动作 ≠ 拦截 的高危记录（疑似绕过）—— **已剔除整域 observe-only 域名**避免误判
6. 时间分布呈现自动化节奏（亚秒级高频 / 固定间隔）

强覆盖：UA 单一为 CLI 工具 + 域名含测试关键词 → 强制判为「测试流量」（即便有公网 IP/亚秒级节奏等噪声）。

其余情况判为 **自动化扫描器流量**。

## 八、配置异常识别规则

**整域 observe-only**：单个域名同时满足
- 攻击数 ≥ 50
- 拦截率 < 5%
- 高危数 ≥ 50

→ 视为"该域名规则被错配为观察模式"，单列章节告警，并从"可疑绕过"中剔除避免误报。

## 九、扫描器指纹库

UA 关键词：`nmap` `masscan` `zgrab` `nuclei` `sqlmap` `nikto` `acunetix` `nessus` `burpsuite` `xray` `censys` `shodan` `paloaltonetworks.com` `internet-measurement.com`

URI 关键词：`/HNAP1` `/sdk` `/evox/about` `eval-stdin.php` `/.git/` `/.env` `/actuator` `/druid/` `/wp-admin` `/wp-login.php` `/phpmyadmin` `/solr/` `/console` `/swagger` `/.well-known` `/jenkins`

## 十、与其他 Skill 联动

- **上游**: `soc-alert-pipeline`（L0 适配层，解析 WAF CSV/XLSX 中文列头 → 统一 schema JSONL，由 `waf_parser.py` 完成）
- **平级**: `cwp-analyzer`（应用层攻击是否突破到主机层）、`yujie-analyzer`（NDR 流量层交叉验证）、`tianmu-analyzer`（网络层阻断双重防护验证）、`cfw-analyzer`（防火墙边界防护验证）
- **下游**: `soc-alert-pipeline` 的 `l2_correlate.py`（消费 per-attacker case 做跨产品关联）

## 十一、安全约束

- ⚠️ **不要在报告/case 里复制 payload 原文**——只展示攻击类型与命中情况。日志里的 payload 仍属于敏感信息。
- ⚠️ **威胁情报富化只调用 ip-api.com 等只读公开接口**，不上传任何 payload、URI、UA、域名。
- ⚠️ **私网/回环 IP 跳过富化**，避免泄漏内网拓扑。
- 处置建议保持通用层级，不输出具体 Payload 复现步骤。

## 十二、变更记录

| 日期 | 版本 | 变更 | 原因 |
|---|---|---|---|
| 2026-07-16 | 2.1.0 | 脚本移至 scripts/ 目录；恢复 HTML 详版报告输出 | 符合标准 skill 格式；与 analyzer.py 报告模板对齐 |
| 2026-07-15 | 2.0.0 | 重构为纯 L1 消费者架构 | 与 cwp/yujie/tianmu/cfw 4 个 analyzer 架构统一，消费 L0 JSONL，输出 report + cases + correlation_hints |
| 2026-07-15 | 2.0.0 | CSV/XLSX 解析逻辑移至 L0 (waf_parser.py) | L0/L1 职责分离，L0 只做字段映射，L1 只做威胁分析 |
| 2026-07-15 | 2.0.0 | 新增 per-attacker case 输出 | 供 L2 跨产品关联消费 |
| - | 1.0.0 | 初版 (独立单体 analyzer.py) | 直接读 CSV/XLSX → 出报告 |
