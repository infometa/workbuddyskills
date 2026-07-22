---
name: soe
description: This skill should be used when the user asks to "analyze security alerts", "parse vulnerability scan report", "analyze vulnerability scan report", "verify CVE fix", "analyze WAF attack log", "analyze CFW firewall log", "analyze cloud firewall alert", "investigate host intrusion", "analyze DDoS traffic", "check host asset", "troubleshoot application logs", or needs security operations analysis covering CWP/WAF/Yujie(NDR)/Tianmu/CFW/SOC platform alerts, vulnerability management, intrusion forensics, or DDoS PCAP analysis.
version: 1.0.0
---

# 腾讯云安全运营专家技能 (Security Operations Expert Skill)

安全运营全栈能力集，覆盖漏洞管理、多产品告警研判、入侵溯源、DDoS流量分析、勒索病毒分析、资产管理、通用日志排查七大领域。本文件为入口索引，按需渐进加载 `references/` 下对应子领域的完整能力说明。

## 意图路由表

根据用户输入内容与提供的数据类型，匹配到下方对应能力，再加载其 `references/<分类>/<能力名>/SKILL.md` 获取详细工作流程、脚本用法与输出规范。

> 告警研判领域采用三层架构：L0 适配层（soc-alert-pipeline，统一解析）→ L1 产品分析层（5 个 analyzer）→ L2 跨产品关联。5 个 L1 analyzer 架构统一，都支持双路径输入、都经过 L0 解析、都参与 L2 关联。

| 分类 | 能力 | 触发场景 / 关键词 | 数据输入 | 详细说明 |
|------|------|-------------------|---------|---------|
| 漏洞管理 | `vul-analyse` | 漏洞扫描、漏扫报告、CVE、CVSS、漏洞清单、漏洞评估 | 漏扫报告(Excel/HTML/JSON/XML/.nessus) | `references/vulnerability-analysis/vul-analyse/SKILL.md` |
| 漏洞管理 | `host-cve-validator` | 主机漏洞修复、CVE修复验证、补丁验证、host CVE、fix validation | CVE 编号/漏扫报告(Excel) | `references/vulnerability-analysis/host-cve-validator/SKILL.md` |
| 漏洞管理 | `container-cve-fix-validator` | 容器漏洞、镜像漏洞、容器修复、容器CVE、Dockerfile修复 | 容器漏扫报告(Excel) | `references/vulnerability-analysis/container-cve-fix-validator/SKILL.md` |
| 告警研判 | `soc-alert-pipeline` | SOC、安全运营中心、告警研判、SIEM、raw_log解析、告警流水线 | SOC导出的xlsx(含raw_log) / 单产品原始日志 | `references/alert-analysis/soc-alert-pipeline/SKILL.md` |
| 告警研判 | `cwp-analyzer` | 主机安全告警、CWP告警、暴力破解、反弹Shell、云镜告警、CWPP事件 | L0 parsed 字段 / SOC导出xlsx / CWP原始日志 | `references/alert-analysis/cwp-analyzer/SKILL.md` |
| 告警研判 | `yujie-analyzer` | 御界、NDR、NTA、网络流量检测、高级威胁检测、C2通信 | L0 parsed 字段 / SOC导出xlsx / 御界原始日志 | `references/alert-analysis/yujie-analyzer/SKILL.md` |
| 告警研判 | `tianmu-analyzer` | 天幕、安全治理、阻断日志、NDR阻断 | L0 parsed 字段 / SOC导出xlsx / 天幕原始日志 | `references/alert-analysis/tianmu-analyzer/SKILL.md` |
| 告警研判 | `cfw-analyzer` | CFW、云防火墙、防火墙告警、防火墙阻断、eventLog、CFW风险报告 | L0 parsed 字段 / SOC导出xlsx / CFW原始日志 | `references/alert-analysis/cfw-analyzer/SKILL.md` |
| 告警研判 | `waf-log-analyzer` | WAF、Web攻击、SQL注入告警、XSS告警、WAF日志、attacklog | L0 parsed 字段 / SOC导出xlsx / WAF attacklog CSV | `references/alert-analysis/waf-log-analyzer/SKILL.md` |
| 入侵溯源 | `host-intrusion-analysis` | 入侵检测、后门、webshell、异常进程、可疑连接、入侵排查、安全排查 | 主机日志数据（需先用采集脚本生成，见下方采集脚本速查表） | `references/intrusion-analysis/host-intrusion-analysis/SKILL.md` |
| 攻击分析 | `ddos-analysis` | DDoS、流量攻击、抓包、pcap、流量分析、攻击流量 | PCAP/CAP 文件(本地路径或URL) | `references/attack-analysis/ddos-analysis/SKILL.md` |
| 攻击分析 | `ransomware-analysis` | 勒索病毒、勒索信、勒索软件、ransomware、文件被加密、勒索家族识别、解密工具 | 勒索信文本 / 加密文件扩展名 / IOC 指标 | `references/attack-analysis/ransomware-analysis/SKILL.md` |
| 资产管理 | `asset-manager` | 资产查询、主机资产、IP归属、资产纳管、主机映射 | 资产CSV / IP列表 | `references/asset-management/asset-manager/SKILL.md` |
| 通用排查 | `log-analysis-troubleshooting` | 应用日志、错误日志、访问日志、排障、故障排查、日志分析 | 通用应用日志文件 | `references/general/log-analysis-troubleshooting/SKILL.md` |

### 入侵分析采集脚本

入侵分析需要标准化的主机日志。采集脚本源文件位于专家包内 `references/intrusion-analysis/host-intrusion-analysis/scripts/<linux|windows>/` 目录，AI 运行时通过 `find ~/.workbuddy/plugins -name "get_log_all_in_one.*"` 定位实际绝对路径，并通过 `present_files` 工具把脚本文件本身展示给用户下载。

| 平台 | 脚本路径（专家包内源路径） | 运行方式 | 输出文件 |
|------|---------|---------|---------|
| Windows | `references/intrusion-analysis/host-intrusion-analysis/scripts/windows/get_log_all_in_one.ps1` | 管理员 PowerShell 运行 `powershell -ExecutionPolicy Bypass -File get_log_all_in_one.ps1` | `log_<主机名>_<时间戳>.txt` |
| Linux | `references/intrusion-analysis/host-intrusion-analysis/scripts/linux/get_log_all_in_one.sh` | `sudo bash get_log_all_in_one.sh` | `log_<IP>_<主机名>_<用户>_<时间戳>.txt` |

> 用户将生成的 `.txt` 文件路径提供后，即可进入入侵分析流程。

### 资产导入说明

资产导入由专家内部完成格式识别与入库，可以从腾讯云 CVM 控制台导出，也支持自定义 CSV / Excel / JSON / 纯文本 IP 列表四种格式，支持智能列名映射，无需按固定模板整理。你只需提供资产文件路径，剩下的交给专家处理。

> 导入后数据存放于 `$CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/`，下次 `load_default_assets()` 自动加载。后台通过通用导入脚本 `scripts/import_assets_flexible.py` 完成识别入库（三段降级：标准 CSV 列名优先 → 智能列名映射兜底）。

## 路由决策流程

### Step 1: 意图识别

从用户输入中提取以下维度：
- **安全事件类型**：漏洞 / 入侵 / DDoS / 告警 / 资产 / 排障
- **数据类型**：扫描报告 / 日志文件 / 流量包 / 样本文件
- **操作目标**：分析 / 修复 / 验证 / 溯源 / 防护 / 研判
- **产品来源**：WAF / CWP / 御界 / 天幕 / CFW / SOC / 通用

### Step 2: 能力匹配

按优先级匹配：

1. **精确匹配** — 用户明确指定产品或能力名称 → 直接加载对应 `references/` 子目录
2. **数据驱动** — 根据用户提供的文件类型匹配：
   - `.pcap`/`.cap` → `ddos-analysis`
   - SOC导出xlsx(含 raw_log) → `soc-alert-pipeline`（L0），再按 product 字段分发到对应 L1
   - 单产品原始日志（CWP/御界/天幕/CFW key=value或JSON、WAF attacklog CSV）→ `soc-alert-pipeline`（L0 解析），再分发到对应 L1
   - 漏扫报告(Nessus/绿盟/深信服等) → `vul-analyse`
   - 主机日志（`log_*.txt` 采集脚本输出 / 原始 var/log 目录 / 多主机 ZIP）→ `host-intrusion-analysis`，若用户无日志文件则引导使用采集脚本（见上方"入侵分析采集脚本"表）
3. **关键词匹配** — 按意图路由表中的触发关键词匹配
4. **上下文推断** — 结合对话历史推断最可能的目标能力

### Step 3: 渐进式加载

匹配到目标能力后，**读取对应的 `references/<分类>/<能力名>/SKILL.md`**，按其内部定义的角色、工作流程、脚本工具执行任务。不要在未加载具体 SKILL.md 前就凭空猜测该能力的操作细节。

## 联动编排规则（跨能力协同）

多个能力之间存在层级依赖关系，联动时遵循：

```
数据输入层:  SOC导出xlsx(多产品混合) / 单产品原始日志(WAF CSV、CFW JSONL、CWP日志等)
     ↓
L0 适配层:  soc-alert-pipeline（统一 raw_log 解析 + 自动调用 asset-manager 关联资产）
     ↓ parsed JSONL（含 correlation_hints 所需字段）
L1 产品分析: cwp-analyzer / yujie-analyzer / tianmu-analyzer / cfw-analyzer / waf-log-analyzer
     ↓ 结构化事件（每个案例输出 correlation_hints）
L2 跨产品关联: l2_correlate（关联多产品 L1 输出，攻击链还原）
     ↓
报告层:     gen_report（HTML + ECharts 可视化）

资产数据层: asset-manager（为所有能力提供 IP→主机映射，可随时调用）
```

### 路径说明

- **路径 A：SOC 导出（多产品混合）** — 用户提供 SOC xlsx → L0 解析 → 按 product 字段分发到各 L1 analyzer → L2 关联
- **路径 B：单产品独立日志** — 用户提供单个产品原始日志 → L0 解析（product=对应产品）→ 对应 L1 analyzer → 可选 L2 关联（单产品时 L2 退化为产品内关联）

### 联动规则

- 当用户提供 SOC 导出数据或单产品原始日志时：先加载 `soc-alert-pipeline`（L0）解析 → 按产品分发到对应 L1 analyzer（cwp/yujie/tianmu/cfw/waf）
- 当需要 IP 归属信息时：L0 自动调用 `asset-manager`，也可由任意 L1/L2 能力随时调用
- 当需要跨产品关联时：先并行运行各 L1 analyzer，再由 L2 合并关联分析结论
- 5 个 L1 analyzer 架构统一：都支持双路径输入、都经过 L0 解析、都输出 correlation_hints、都参与 L2 关联
- 当遭遇勒索病毒攻击时：加载 `ransomware-analysis` 进行家族识别 + 入侵路径分析，可联动 `host-intrusion-analysis` 溯源、`vul-analyse` 分析漏洞利用路径

## 执行原则

- **只读优先**：分析类请求直接执行；修复/变更类操作必须用户确认
- **如实报告**：数据不足时直接说明，不编造、不猜测、不虚构 API 或数据
- **区分事实与推断**：明确标注哪些是原始数据事实，哪些是分析推断
- **安全敏感**：处理过程注意数据脱敏，紧急事件优先给出止损建议
- **结果直达**：分析完成后直接回答用户问题，不能仅说"请查看报告"
- **追问复用**：用户追问时优先复用已采集数据，仅补拉缺失部分

## 输出规范

- 分析报告默认使用 Markdown；涉及可视化/仪表盘类需求时可产出 HTML（各子能力 SKILL.md 中有具体规定）
- 列表类数据需标注总数与当前展示范围，不得用截断后的条数冒充总数
- 关键安全字段（风险等级、告警状态、影响范围）需要高亮标注
- 报告末尾建议注明数据来源与生成时间，避免读者误判数据时效性

## 目录结构

```
skills/soe/
├── SKILL.md                                 # 本文件 — 入口索引 / 意图路由表
└── references/                              # 按安全领域分类的完整能力集
    ├── vulnerability-analysis/               # 漏洞管理
    │   ├── vul-analyse/
    │   ├── host-cve-validator/
    │   └── container-cve-fix-validator/
    ├── alert-analysis/                       # 告警研判
    │   ├── waf-log-analyzer/
    │   ├── cwp-analyzer/
    │   ├── yujie-analyzer/
    │   ├── tianmu-analyzer/
    │   ├── cfw-analyzer/
    │   └── soc-alert-pipeline/
    ├── intrusion-analysis/                   # 入侵溯源
    │   └── host-intrusion-analysis/
    ├── attack-analysis/                      # 攻击分析
    │   ├── ddos-analysis/
    │   └── ransomware-analysis/
    ├── asset-management/                      # 资产管理
    │   └── asset-manager/
    └── general/                               # 通用排查
        └── log-analysis-troubleshooting/
```

每个能力目录下均包含独立的 `SKILL.md`（角色定位/能力范围/工作流程/输出格式）以及可选的 `scripts/`（工具脚本）、`references/`（该能力专属参考资料和示例）。新增能力需遵循 [SKILL_SPEC.md](../../SKILL_SPEC.md) 中的规范约定。
