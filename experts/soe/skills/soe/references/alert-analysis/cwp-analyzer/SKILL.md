---
name: cwp-analyzer
version: 1.0.0
triggers:
  - CWP
  - 云镜
  - 主机安全告警
  - 暴力破解
  - 反弹Shell
  - CWPP
description: |
  腾讯主机安全 (CWP/云镜) 告警 L1 分析 skill

  消费 L0 适配层 (soc-alert-pipeline) 输出的 parsed 字段,
  基于主机安全威胁场景知识库, 产出:
    - 威胁判定 (TTP / ATT&CK 映射)
    - 处置建议
    - 标准化案例文档

  适用场景:
  - 单条主机安全事件的深度分析
  - 批量分析 (L0 JSONL → L1 cases/*.md)
  - 联调: 主机安全 ↔ 御界 (L2 消费 L1 输出)

  不适用:
  - raw_log 解析 (用 soc-alert-pipeline)
  - 跨产品关联 (用 L2, 暂未实现)
---

# cwp-analyzer (L1 主机安全)

## 一、定位

这是 L1 产品分析 skill, 在 L0 适配层之上:

```
SOC 导出 xlsx
      ↓
soc-alert-pipeline (L0)  →  parsed dict
      ↓
cwp-analyzer (L1, 本 skill)  →  案例文档 + 威胁判定
      ↓
L2 关联 (soc-correlation, 暂未实现)
```

## 二、当前覆盖的威胁场景

| 场景 | TTP | 关键信号 | detector |
|---|---|---|---|
| 暴力破解 | T1110 | 同 src_ip 多次 count 累加 / 状态码特征 | `ttp_detectors/brute_force.py` |
| 反弹 Shell | T1059.004 | cmd 含 `/dev/tcp` / `bash -i` / `nc -e` | `ttp_detectors/reverse_shell.py` |
| 持久化 | T1543 / T1546 | crontab / systemd / ssh authorized_keys | `ttp_detectors/persistence.py` |
| 横向移动 | T1021 / T1570 | ssh/smb 跨主机异常 / 端口扫描 | `ttp_detectors/lateral_movement.py` |

详见 `references/threat-catalog.md`。

## 三、快速开始

```bash
# 1. 先用 L0 跑一遍 (确保 parsed 字段可用)
python3 ../soc-alert-pipeline/scripts/l0_parse.py \
    <xlsx_path> --out /tmp/cwp_l0.jsonl

# 2. 用 L1 分析 (单条 / 批量)
python3 scripts/l1_cwp_analyze.py /tmp/cwp_l0.jsonl --out cases/

# 3. 产出: cases/ 目录下一堆 {event_id}.md
ls cases/
```

## 四、L1 输出案例文档格式

详见 `references/case_template.md`, 包含:
- 1. 基础信息
- 2. 威胁判定 (TTP / ATT&CK)
- 3. 处置建议
- 4. 关联建议 (供 L2 消费)

## 五、与 L0 / L2 的接口

**L0 → L1 输入** (`parsed` dict):
```python
{
    "src_ip", "dst_ip", "src_port", "dst_port", "protocol",
    "host_ip", "hostname",
    "process", "process_path", "cmd", "user",
    "rule_id", "rule_name", "status", "category",
    "event_time", "event_time_raw",
    "_raw_kv": { ... }  # 完整 kv 兜底
}
```

**L1 → L2 输出**: 每个案例文档, 含 `correlation_hints` 段, 供 L2 关联键:
```yaml
threat:
  correlation_hints:
    pivot_keys: ["host_ip", "src_ip"]
    time_window_min: 60
```

## 六、待用户确认项 (TODO)

1. **`status` 字段值映射**:
   - 当前数据 status="1" (一次) / "0" (无? 待验证)
   - 实际含义: 1=成功? 0=失败? 还是别的?
   - 需要 L1 接入腾讯云镜的 status 码表

2. **`type` 字段值映射**:
   - 当前数据 type="jdbc_login" (实际是 SSH 登录, 端口 22)
   - 腾讯内部的事件类型编码
   - 需要 L1 接入腾讯事件类型码表

3. **count 字段语义**:
   - 暴力破解场景下 count=2 是什么意思? (连续 2 次失败? 1 次失败 1 次成功?)
   - 需要 L1 接入腾讯字段说明

4. **主机安全产品代号**:
   - 当前 PRODUCT="cwp"
   - 实际 SOC OCSF 透出 logsource_subtype="腾讯云镜"
   - 内部代号用 cwp 没问题, 但需要在文档里说明映射

## 七、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 | L0 跑通后建 L1 |
| TODO | 接入 status / type 码表 | 等用户提供腾讯云镜官方文档 |
