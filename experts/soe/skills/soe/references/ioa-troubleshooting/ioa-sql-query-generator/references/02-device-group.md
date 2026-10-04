# 终端设备 / 终端分组 / 终端自定义分组域（PostgreSQL）

> PostgreSQL 默认库 `pcmgr_enterprise`。结论来自 GORM struct、TableName()、真实 Raw JOIN SQL 验证。

## 表清单速览

| 表名 | 含义 | 主键 |
|---|---|---|
| `devices` | 终端设备主表（一台装了 iOA 客户端的终端=一行） | `id` |
| `device_info` | 终端硬件/系统/风险扩展信息（1:1，按 mid） | `id`（mid 唯一） |
| `device_detail` | 终端资产/网络分类明细（公司/私人、内外网） | `mid` |
| `device_profile` | 终端自定义字段值（KV，配合 profile_fields） | `id` |
| `groups` | 终端普通分组（部门/组织树） | `id` |
| `device_virtual_groups` | 终端自定义分组（虚拟分组） | `id` |
| `device_virtual_group_to_device` | 终端↔自定义分组 多对多关联 | `id` |
| `device_organizational_structure` | 终端↔账号 关联（哪台终端由哪个账号登录） | `id`（mid 唯一） |

⚠ **关联键规则（极重要）**：
- `device_virtual_group_to_device.device_id = devices.id`（数值主键）
- `device_info` / `device_detail` / `device_profile` / `device_organizational_structure` 全部 `.mid = devices.mid`（字符串业务键）
- 二者不可混用。

---

## devices — 终端设备主表
> 注意：`internal/pkg/dbmodel/devices.go` 的极简版只有 name/mid，不完整。完整字段以 device-mgr/devices/model与open-api entity 为准。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | bigint PK | 终端主键（关联表 device_id / host_id 指向它） |
| `mid` | varchar | 终端机器唯一标识（扩展表按此JOIN） |
| `name` | varchar | **终端名称**（"根据终端名称查询"用此字段） |
| `group_id` | bigint | 所在普通分组 ID → `groups.id` |
| `username` | varchar | 终端登录用户名（展示用 COALESCE(di.username,d.username) 兜底） |
| `guid` | varchar | 终端 GUID |
| `machine_guid` | varchar | 机器 GUID（硬件标识） |
| `ip` | varchar | 终端 IP |
| `local_ip_list` | text | 本地 IP 列表 |
| `ostype` | int | 系统类型（1 Win / 2 Linux / 3 macOS 等） |
| `status` | int | 终端状态。**有效终端恒 `status IN (4,5)`**，其他为已删除/待清理 |
| `online_status` | int | 在线状态 |
| `active_status` | int | 活跃状态 |
| `version`/`strversion` | varchar | 客户端版本 |
| `conn_active_time` | timestamp | 最近连接活跃时间（最接近"last_online_time"） |
| `locked` | int | 是否锁定 |
| `description` | varchar | 备注 |
| `host_id` | int | 宿主机终端 ID（虚拟机场景，自关联 devices.id） |
| `tenant_id` | varchar | 租户 |
| `utime`/`itime` | timestamp | 更新/入库时间 |

> 无独立 `last_online_time`；序列号不在此表（在 device_info.serial_num / base_board_sn）。

---

## groups — 终端普通分组（部门树）

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | bigint PK | 分组主键（devices.group_id 指向它） |
| `name` | varchar | 分组名称（查询常输出为 group_name） |
| `parent_id` | bigint | 父分组 ID |
| `id_path` | varchar | ID 物化路径，形如 `1.2.5.` |
| `name_path` | varchar | 名称路径 |
| `ostype` | int | 系统类型 |

**终端→普通分组**：`devices d INNER JOIN groups g ON d.group_id = g.id`
按某分组及子孙分组过滤终端：`string_to_array(g.id_path,'.')::int[] && ARRAY[分组id列表]`

---

## device_virtual_groups — 终端自定义分组（虚拟分组）

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 自定义分组主键（关联表指向它） |
| `name` | varchar | 分组名称 |
| `en_name` | varchar | 英文名（内置分组用） |
| `ostype` | int | 系统类型 |
| `domain_id` | int | 管理域 ID（权限隔离） |
| `tenant_id` | varchar | 租户 |
| `inside_id` | int | 0=普通自定义分组；>0=系统内置分组（资产/内外网/登录状态等） |
| `status` | int | 状态 |
| `itime`/`utime` | timestamp | 创建/更新 |

关联规则表`group_auto_partition_rule`（`vgroupid`→device_virtual_groups.id，自动分组规则）。

## device_virtual_group_to_device — 终端↔自定义分组

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 主键 |
| `device_id` | bigint | **→ `devices.id`（注意是 id 不是 mid）** |
| `device_virtual_group_id` | int | → `device_virtual_groups.id` |
| `tenant_id` | varchar | 租户 |

**终端→自定义分组**：
```
device_virtual_group_to_device dvgd
  INNER JOIN devices dON d.id = dvgd.device_id
  INNER JOIN device_virtual_groups dvg ON dvg.id = dvgd.device_virtual_group_id
```

---

## device_organizational_structure — 终端↔账号 桥表
devices 表本身无 user_id/account_id，登录账号靠此桥表（按 mid）。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 主键 |
| `mid` | varchar | → `devices.mid`（唯一） |
| `account_id` | int | → `accounts.id` |
| `account_group_id` | int | → `account_groups.id` |
| `login_type` | int | 登录类型（账号/AD 域等） |
| `state` | int | 登录状态（0=已登录） |
| `utime`/`itime` | timestamp | 最近登录时间/创建 |

**终端→账号**：
```
devices d
  LEFT JOIN device_organizational_structure dos ON dos.mid = d.mid
  LEFT JOIN accounts aON dos.account_id = a.id
  LEFT JOIN account_groups ag ON ag.id = a.group_id
```

---

## device_info — 终端扩展信息（1:1按 mid）
硬件/系统/风险/合规/模块状态。JOIN：`devices d LEFT JOIN device_info di ON d.mid = di.mid`

关键字段（节选）：`mid`、`os`/`osversion`/`osbits`/`oslanguage`、`computername`/`domainname`/`macaddr`、`cpu`/`mainboard`/`memory`/`hdd`/`videocard`/`networkcard`、`serial_num`/`base_board_sn`(序列号)、`username`、`tags`、`vulcount`/`risk_count`、`real_time_protection_status`、`epp_module_status`/`edr_module_status`/`dlp_module_status`/`rpt_module_status`、`compliance_result_status`/`compliance_risk_level`。

## device_detail — 资产/网络分类（按 mid）
`mid`、`class_asset`(1 公司资产/2 私人资产/0 未分类)、`class_net`(1 内网/2 外网/0 未知)、`inside_tag`、`installation_status`、`tenant_id`。

## device_profile — 自定义字段值
`mid`、`field_id`(配合 profile_fields.id)、`value`；`field_id=1` 约定为终端 profile 名称。

---

##★ 查询所有终端 + 所在分组 + 所在自定义分组（已验证生产SQL 骨架）

```sql
SELECT d.id, d.mid, d.name AS device_name,
       g.name  AS group_name,                -- 所在普通分组(部门)
       a.user_id AS login_user,               -- 登录账号
       vg.virtual_group_names                 -- 所在自定义分组(聚合)
FROM devices d
INNER JOIN groups g ON d.group_id = g.id
LEFT JOIN device_organizational_structure dos ON dos.mid = d.mid
LEFT JOIN accounts aON dos.account_id = a.id
LEFT JOIN (
  SELECT dvgd.device_id, string_agg(dvg.name, ',') AS virtual_group_names
  FROM device_virtual_group_to_device dvgd
  JOIN device_virtual_groups dvg ON dvg.id = dvgd.device_virtual_group_id
  GROUP BY dvgd.device_id
) vg ON vg.device_id = d.id
WHERE d.status IN (4,5);
```

## 关键约定
1. 终端主键 `devices.id`（关联表用）；跨表业务键 `devices.mid`（扩展表用）。
2. 终端名称查询：`WHERE devices.name = ...` 或 `LIKE`。
3. 有效终端过滤：默认加 `devices.status IN (4,5)`。
4. 普通分组一台终端只有一个（groups，直连 group_id）；自定义分组一台可有多个（device_virtual_groups，经多对多桥表）。
5. 终端↔账号须经 device_organizational_structure（按 mid），登录人显示字段 `accounts.user_id`。
6. 序列号在 `device_info.serial_num` / `base_board_sn`。
