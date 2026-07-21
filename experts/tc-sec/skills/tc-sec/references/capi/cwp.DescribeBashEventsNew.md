# cwp.DescribeBashEventsNew 字段说明

> 高危命令事件接口（**新版**，推荐使用）。与老版 `DescribeBashEvents` 的核心差异见下方。

## 与 DescribeBashEvents（老版）的差异

| 维度 | DescribeBashEventsNew（新版）| DescribeBashEvents（老版）|
|------|------------------------------|--------------------------|
| 主机 IP 字段名 | `HostIp`（大写 I）；Filter 键同时支持 `Hostip` 和 `HostIp` | `Hostip`（小写 i）；Filter 键仅 `Hostip` |
| 用途 | 查询/告警管理，返回更完整字段 | 已逐步被新版替代 |
| 溯源字段 | `Uuid`、`Pid`（string）、`BashCmd`——三者均有，可直接传 `compute_alarm_vid` | 同上，字段名相同 |

**结论：做进程链溯源时用 `DescribeBashEventsNew`**，取 `Uuid`/`Pid`/`BashCmd` 计算 AlarmVid。

## 溯源关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `Uuid` | string | 主机 UUID，传给 `DescribeAlarmIncidentNodes --Uuid` |
| `Pid` | string | 进程号（字符串，`compute_alarm_vid` 内建 `str()` 保护） |
| `BashCmd` | string | 高危命令，传给 `compute_alarm_vid(uuid, "高危命令", {"Pid": int(Pid), "BashCmd": BashCmd})` |
| `CreateTime` | string | 告警时间，转时间戳：`time_util.py ts "<CreateTime>"` |
| `HostIp` | string | 主机内网 IP |

## Filter 键名（常用）

| 键名 | 说明 |
|------|------|
| `HostIp` 或 `Hostip` | 按主机内网 IP 过滤 |
| `Status` | 按处理状态过滤 |

## Status（处理状态）

| 值 | 含义 |
|----|------|
| `0` | 待处理 |
| `1` | 已处理 |
| `2` | 已加白 |
| `3` | 已忽略 |
| `4` | 已删除 |
| `5` | 已拦截 |

## RuleLevel（规则危险等级）

| 值 | 含义 |
|----|------|
| `1` | 高 |
| `2` | 中 |
| `3` | 低 |

## RuleCategory（规则来源）

| 值 | 含义 |
|----|------|
| `0` | 系统规则 |
| `1` | 用户规则 |
