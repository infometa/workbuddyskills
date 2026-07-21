# cwp.DescribeSecurityDynamics 字段说明

> 安全动态接口。**查异常登录/告警事件流应优先用此接口**，不要用 `DescribeHostLoginList`（登录记录审计流水，0 条不代表无异常告警）。
>
> 实测验证：`DescribeHostLoginList` 查到 0 条，但本接口同期查到 3 条 `NON_LOCAL_LOGIN` 异常登录告警（均为近几分钟实时告警）。

## 调用要点

- **无时间范围参数**：返回最近的动态，分析时必须按 `EventTime` 字段筛选目标时段（如 `EventTime.startswith("2026-07-03")` 取今日），否则会把历史动态计入。
- 分页：`--Limit`/`--Offset`，list_key 为 `SecurityDynamics`，TotalCount 为动态总数。

## 返回字段

| 字段 | 含义 |
|------|------|
| `Uuid` | 主机 UUID |
| `EventTime` | 事件时间，格式 `2026-07-03 17:34:37` |
| `EventType` | 事件类型枚举（见下表） |
| `SecurityLevel` | 安全等级枚举（见下表） |
| `Message` | 事件描述，如 `主机172.16.0.4被113.108.77.56异常登录` |

## EventType（事件类型）

> 实测可见 `NON_LOCAL_LOGIN`；其余取值来自模板（`references/workflow/daily_alert_report/run.py` 的 `ET_LABEL`）已验证映射。

| 值 | 含义 |
|----|------|
| `MALWARE` | 木马文件 |
| `TROJAN` | 木马文件 |
| `BRUTEATTACK` | 暴力破解 |
| `HOST_LOGIN` | 异常登录 |
| `NON_LOCAL_LOGIN` | 异地登录 |
| `LOGIN` | 登录审计 |
| `BASH` | 高危命令 |
| `HIGH_RISK_BASH` | 高危命令 |
| `RISK_DNS` | 恶意请求 |
| `MALICIOUS_REQUEST` | 恶意请求 |
| `REVERSE_SHELL` | 反弹 Shell |
| `PRIVILEGE` | 本地提权 |
| `ATTACK_LOGS` | 网络攻击 |
| `CYBER_ATTACK` | 网络攻击 |
| `WEB_ATTACK` | Web 攻击 |
| `SYS_VUL` | 系统漏洞 |
| `WEB_VUL` | Web 漏洞 |
| `VUL` | 漏洞 |
| `EMERGENCY_VUL` | 应急漏洞 |
| `BASE_LINE` | 基线检查 |
| `BASELINE` | 基线检查 |
| `SAFE_BASE_LINE` | 基线检查 |
| `TAMPER` | 文件篡改 |
| `ESCAPE` | 容器逃逸 |
| `K8S_API` | K8s API 异常 |

## SecurityLevel（安全等级）

> 实测可见 `HIGH`/`UNKNOWNED`；`RISK`/`MEDIUM`/`NORMAL`/`LOW`/`INFO`/`NOTICE` 来自模板 `SL_LABEL` 映射。

| 值 | 含义 | 等级色 |
|----|------|--------|
| `RISK` | 严重 | critical |
| `HIGH` | 高危 | high |
| `MEDIUM` | 中危 | medium |
| `NORMAL` | 中危 | medium |
| `LOW` | 低危 | low |
| `INFO` | 提示 | info |
| `NOTICE` | 提示 | info |
| `UNKNOWNED` | 未分级 | info |

## 注意事项

- **统计总数取 `TotalCount`**，禁止用 `len(SecurityDynamics)` 当总数（Limit 截断会失真）。
- `Message` 含主机 IP、源 IP 等信息，可直接用于报告展示，长文本用 `H.code()` 保留完整。
- 此接口聚合了多类安全动态，是 CWP "有无异常" 判断的首选入口；`DescribeHostLoginList` 等审计流水接口仅用于追溯具体登录记录。
