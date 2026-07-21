# 主机安全字段映射 (OCSF ↔ raw_log ↔ L1 内部)

## 一、OCSF 透出字段 (xlsx 列, L0 透传)

| OCSF 列 | 含义 | L0 输出字段 | 备注 |
|---|---|---|---|
| `event_timestamp` | 事件时间 (字符串) | `event_time_raw` / `event_time` (ISO) | 格式: `2026-07-06 14:44:48.000` |
| `logsource_subtype` | 产品代号 | L0 内部用, 不进 parsed | 当前数据: "腾讯云镜" (中文) |
| `data_type` / `data_subtype` | OCSF 分类 | L0 透传 (空) | 当前数据都是 "-" |
| `event_name` | 告警名称 (人读) | `rule_name` (优先) | 例: "云镜感知到登陆行为" |
| `category` | 一级分类 | `category` | 例: "登录行为" |
| `subcategory` | 二级分类 | `subcategory` | 例: "用户登录" |
| `confidence` | 置信度 (数字串) | 未单独存 (在 OCSF 透传) | 当前数据: "3" |
| `severity` | 严重度 (数字串) | 未单独存 (在 OCSF 透传) | 当前数据: "1" (高? 待确认) |
| `src_ip` / `src_port` | 源 IP / 端口 | `src_ip` / `src_port` | |
| `dst_ip` / `dst_port` | 目的 IP / 端口 | `dst_ip` / `dst_port` | |
| `hostname` | 主机名 | `hostname` | 当前数据都是 "-" |
| `proc_id` / `proc_path` / `proc_commandline` / `proc_user` | 进程信息 | L0 透传 (空) | 当前数据都是 "-" (raw_log 才有) |
| `log_time` | 日志时间 | L0 透传 (空) | 当前数据是 "-" |
| `raw_log` | 原始日志 (kv) | `parsed._raw_kv` | L0 主战场 |

## 二、raw_log 字段 (kv 切分后, L0 主战场)

| raw_log 字段 | 含义 | L0 输出 | 备注 |
|---|---|---|---|
| `type` | 事件类型编码 | `rule_name` (当 OCSF 缺失) | 例: `jdbc_login` (含义待确认) |
| `hostip` | 主机 IP | `host_ip` | **实际数据用 hostip, 不是 host_ip** |
| `username` | 用户名 | `user` | |
| `count` | 次数 (1次/多次) | `_raw_kv.count` | **关键: 暴力破解信号** |
| `src_ip` | 源 IP | `src_ip` (兜底) | |
| `dst_port` | 目的端口 | `dst_port` (兜底) | |
| `modify_time` | 修改时间 | `event_time` (优先) | 格式: `2026-07-06 14:44:48` |
| `status` | 状态码 | `status` | **腾讯内部码, 1=?? (待确认)** |
| `appid` | 应用 ID | `_raw_kv.appid` | 腾讯云 appid |
| `vpc_id` | VPC ID | `_raw_kv.vpc_id` | 内网 VPC |
| `alarm_sended` | 告警已发送? | `_raw_kv.alarm_sended` | 0/1 |
| `uuid` | 事件 UUID | `_raw_kv.uuid` | 唯一标识 |
| `id` | 事件 ID | `_raw_kv.id` | 腾讯内部事件 ID |

## 三、待用户确认 (TODO)

### 3.1 `status` 字段值含义

实际数据里 status="1", 但没说是什么含义:
- (a) 1=成功, 0=失败?
- (b) 1=告警, 0=正常?
- (c) 1=需处置, 0=已处置?
- (d) 其他?

**需要**: 腾讯云镜 status 码表

### 3.2 `type` 字段值含义

实际数据里 type="jdbc_login", 但 dst_port=22 (SSH 端口):
- (a) jdbc_login 是腾讯内部的 SSH 登录事件类型? (jdbc 可能指 jdbc 连接?)
- (b) 命名沿用了旧的 jdbc 协议, 实际是 SSH?
- (c) 其他含义?

**需要**: 腾讯云镜 type 码表

### 3.3 `severity` 字段值含义

实际数据里 severity="1" / "3" (字符串):
- (a) 数字越大越严重? 还是越小?
- (b) 与 OCSF standard severity (informational/low/medium/high/critical) 的映射?

### 3.4 `count` 字段值含义

实际数据里 count="2":
- (a) 同一事件累计 2 次?
- (b) 同一时间窗内 2 次?
- (c) 失败 2 次 (暴力破解信号)?

## 四、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 | 基于 esSearch_20260706144610.xlsx 实际数据 |
