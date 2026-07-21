# SOC 导出 xlsx 字段说明 (基于 esSearch_*.xlsx 实际样本)

> 基于实际拿到的 3 份样本 (御界 + 主机安全), 整理 SOC 导出 xlsx 的字段分布。
> 注意: **不同产品导出的字段不完全一致**, 主机安全比御界字段多。

## 一、通用 OCSF 字段 (3 份数据都有的)

| 字段 | 类型 | 含义 | 示例 |
|---|---|---|---|
| `event_id` | str | 事件 ID | `e_xxx` |
| `event_name` | str | 告警名称 (人读) | `WireGuard隧道通信` |
| `event_timestamp` | str | 事件时间 (ISO 8601) | `2026-07-06T14:30:22+08:00` |
| `severity` | enum | 严重度 | `high` / `medium` / `low` / `informational` |
| `confidence` | int (0-100) | 产品置信度 | `85` |
| `category` | str | 类别 (一级) | `Network Activity` |
| `subcategory` | str | 子类别 (二级) | `Tunneling` |
| `src_ip` | str | OCSF 透出的源 IP (⚠️ NAT 前) | `10.0.0.4` |
| `src_port` | int | OCSF 透出的源端口 | `51820` |
| `dst_ip` | str | OCSF 透出的目的 IP (⚠️ NAT 前) | `172.16.114.118` |
| `dst_port` | int | OCSF 透出的目的端口 | `51820` |
| `hostname` | str | 主机名 (主机类才有) | `web-prod-01` |
| `logsource_subtype` | str | **产品代号** (parser 选择依据) | `yujie` / `cwp` |
| `data_type` | str | OCSF data_type | `Network Connection` |
| `data_subtype` | str | OCSF data_subtype | `VPN` |
| `raw_log` | str | 原始日志 (L0 解析入口) | (见各产品样例) |

## 二、字段非空率差异

| 字段 | 御界 (esSearch_...45614) | 主机安全 (esSearch_...144610) |
|---|---|---|
| `src_ip` / `dst_ip` | 高 (~100%) | 中 (~80%, 部分失败事件没有) |
| `src_port` / `dst_port` | 高 (~100%) | 低 (~30%) |
| `hostname` | 无 | 高 (~70%) |
| `raw_log` | 中 (~50%, 部分重导后才有) | 高 (~95%) |
| `category` | 高 | 高 |
| `severity` | 高 | 高 |
| `confidence` | 高 | 高 |
| `event_name` | 高 | 高 |

**关键观察**:
- 主机安全比御界多了 `hostname` 字段 (天然带资产视角)
- 主机安全的 `src_port`/`dst_port` 非空率低, 因为有些事件是 "进程执行" 而非 "网络连接"
- 御界的 `raw_log` 在第一次导出时**全部为空** (3 年前的旧数据), 重导后才有完整 JSON

## 三、御界专属字段 (在 raw_log 内的 ext 段)

| 字段 | 类型 | 含义 | 示例 |
|---|---|---|---|
| `attacker_ip` | str | **真实攻击源** (NAT 还原后) | `123.103.18.70` |
| `victim_ip` | str | **真实受害 IP** | `172.16.114.119` |
| `asset_ip` | str | 资产视角 IP | (与 victim_ip 可能不同) |
| `src_mac` | str | 源 MAC | `00:0a:f7:12:34:56` |
| `dst_mac` | str | 目的 MAC | `00:0a:f7:65:43:21` |
| `app_proto` | str | DPI 协议识别结果 | `failed` (识别失败时) |
| `score` | float | 御界内部威胁打分 (0-100) | `85.000000` |
| `attack_result` | str | 攻击尝试/成功 | `attempt` / `success` |
| `raw_packet_hex` | str | 完整 packet 字节流 (hex) | `450001...` |
| `flow` | object | 单包流统计 | `{bytes_toserver, pkts_toserver, ...}` |
| `gre` | object | GRE 封装信息 | `{src, dst, vpcid}` |
| `alert` | object | Suricata 规则详情 | `{signature_id, gid, rule_type}` |

## 四、主机安全专属字段 (在 raw_log 的 kv 段)

| 字段 | 类型 | 含义 | 备注 |
|---|---|---|---|
| `src_ip` | str | 源 IP | 与 OCSF 字段重复, **以 raw_log 为准** |
| `src_port` | int | 源端口 | |
| `dst_ip` | str | 目的 IP | |
| `dst_port` | int | 目的端口 | 例: 22 (SSH) / 3389 (RDP) |
| `process` | str | 进程名 | `sshd` / `bash` / `nginx` |
| `process_path` | str | 进程完整路径 | `/usr/sbin/sshd` |
| `cmd` | str | 命令行 | `bash -i >& /dev/tcp/...` |
| `user` | str | 用户名 | `root` / `www-data` |
| `event_type` | str | 事件类型 (规则名) | `SSH登录成功` |
| `status` | str | 事件结果 | `success` / `failure` |
| `event_time` | str | 事件时间 (字符串原值) | `2026-07-05 15:30:22` |

**待确认字段**:
- `host_ip` 是否在 raw_log 里? 还是只在 OCSF 的 `hostname` / `dst_ip`?
- 不同事件类型 (暴力破解 / 反弹 shell / 进程执行) 的 kv 字段是否完全一致?

## 五、SOC 导出格式注意事项

### 5.1 xlsx 的 dimension 异常

`openpyxl.load_workbook()` 读取时 `dimensions` 显示 `A1`, 但实际有 10000+ 行数据。

**解决方案**: 不用 openpyxl, 直接解压 xlsx 读 `xl/worksheets/sheet1.xml` (本 skill 的 `xlsx_reader.py` 已实现)。

### 5.2 sharedStrings 可能为空

部分 xlsx 的 `xl/sharedStrings.xml` 是空文件, 但 cell 的 `t="s"` 仍引用 index 0。

**影响**: openpyxl 会爆 `IndexError`, 但直接读 XML 不受影响 (我们按 cell 类型分别处理)。

### 5.3 同一事件被重复

御界样本里, 同一 5 元组 + 规则的事件被重复 6 次, 是 SOC 内部的告警去重/合并机制导致, 解析时需要按 `event_id` 去重 (由 l0_parse.py 做)。

## 六、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版, 基于 3 份实际样本 | 等更多产品数据补充 |
