# 终端软件与资产上报域（PostgreSQL）

> 存储引擎：全部 PostgreSQL（非ES/ClickHouse）。所有资产/上报表统一按 **`mid`** 关联 `devices`（不是 device_id，也不是 devices.id）。

## 软件资产（字典 + 关联 两表设计）

### software_map — 软件字典表
全局唯一「软件名+版本」字典，分配整型 id 供各终端引用。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 软件唯一 ID（被 software_status.software_id 引用） |
| `name` | varchar | 软件名 |
| `version` | varchar | 软件版本 |

### software_status — 终端已安装软件清单 ★最核心
一行=某终端(mid)装了某软件(software_id)。

| 字段 | 类型 | 含义 |
|---|---|---|
| `mid` | varchar | 终端业务唯一键 → `devices.mid` |
| `software_id` | int | → `software_map.id` |
| `install_date` | varchar(YYYY/MM/DD) | 安装日期 |
| `ext_info` | varchar | 扩展信息（安装路径等） |

### ★ 根据终端名称查询该终端上报的所有软件（官方查询接口等价实现）
```sql
SELECT sm.name    AS software_name,
       sm.version AS software_version,
       ss.install_date,
       ss.ext_info,
       d.name     AS device_name,
       d.mid
FROM devices d
JOIN software_status ss ON ss.mid = d.mid
LEFT JOIN software_map sm ON sm.id = ss.software_id
WHERE d.name = :device_name;
```
> 统计每台终端软件数：`SELECT mid, count(*) FROM software_status GROUP BY mid`。

---

## 其他终端资产/上报表（均按 mid 关联 devices）

| 表名 | 含义 | 关键字段 |
|---|---|---|
| `hardware_changes` | 硬件变更流水 | `mid`, `key`(硬件项), `old`, `new`, `itime` |
| `disk_partition` | 磁盘分区容量上报 | `mid`, `os_type`, `partition`, `file_system`, `capacity`, `used`, `unuse`（唯一键 mid+partition） |
| `outdev` | 外设/外接设备(USB等)上报 | `mid`, `class_guid`, `class_name`, `name`, `pid`, `vid`, `disableable`（唯一键 mid+class_guid+instance） |
| `shared_folder` | 网络共享文件夹上报 | `mid`, `folder_name`, `folder_path`, `current_conn`, `max_conn` |
| `vul_install_info` | 已安装补丁(KB)清单 | `mid`, `kb`, `install_date`, `title`, `description` |
| `vul_ignore_info` | 已忽略漏洞清单 | `mid`, `kb`, `ignore`, `security` |
| `risk_info` | 风险/病毒扫描结果(未修复) | `mid`, `name`(风险名), `path`, `type`, `is_sysrep` |
| `device_discovery` | 网络设备发现(资产发现) | 主键 `mac`（按 mac 而非 mid 关联）, `natip`, `netid`, `name` |
| `trusted_assets` | 可信资产(cmd 7740) | `mid`（一台一行） |

> 通用 JOIN 模式：`devices d JOIN <资产表> t ON t.mid = d.mid WHERE d.name = :device_name`。

## device_info 中的资产汇总字段
`device_info`（按 mid 1:1）含软件/资产汇总计数：`vul_ignore_count`、`vul_install_count`、`risk_count`，以及硬件汇总字段。

> 注意区分：`software-mgr` 模块是**软件分发/软件库管理**（下发安装包、软件策略），与「终端已装软件资产上报」（software_map/software_status）不是同一回事。
