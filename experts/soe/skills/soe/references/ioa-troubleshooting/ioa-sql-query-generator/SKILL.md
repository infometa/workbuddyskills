---
name: ioa-sql-query-generator
description: Use when the user describes in natural language what they want to query from the iOA backend (devices, groups, custom groups, accounts, org structure, resource grants, software asset reports, EDR alerts, DLP, compliance, policies, gateways, tasks) and needs a PostgreSQL read-only query. 触发词：iOA 查询SQL、iOA 数据库、查终端、查账号资源、查软件、生成SQL、ioa后台表、终端分组。铁律：只生成 SELECT 只读查询 SQL，绝不生成任何写操作/DDL。
---

# iOA 后台只读 SQL 查询生成

把用户的自然语言数据需求，翻译成一条可直接执行的 **PostgreSQL 只读查询 SQL**。知识库基于 iOA 后台真实代码（GORM/xorm 模型 + 生产 JOIN SQL）梳理而成。

## 适用范围与排除项

- **适用**：查询终端/设备、分组、自定义分组、账号、组织架构、资源授权、软件资产上报、EDR 告警、DLP、合规、策略、网关、任务、审计等后台数据。
- **排除**：不生成任何写操作/DDL/加锁语句；接口查询转 `references/ioa-troubleshooting/ioa-openapi-invoke/SKILL.md`；纯故障定位转对应排障子能力。

## 意图分诊

| 需求描述 | 参考文件 |
|---|---|
| 账号 / 组织架构 / 资源授权 | `references/01-account-resource.md` |
| 终端 / 分组 / 自定义分组 | `references/02-device-group.md` |
| 软件 / 硬件 / 补丁 / 外设等资产上报 | `references/03-software-asset.md` |
| EDR / DLP / 合规 / 策略 / 网关 / 任务 / 审计 | `references/04-other-domains.md` |

## 工作流程

1. **识别业务域**：从需求里判断落在哪个域，读取对应参考文件（可多读）。
2. **确认表与关联键**：按参考文件里的字段定义与 JOIN 规则选表。特别注意关联键：
   - 终端扩展/资产表按 `devices.mid` 关联；`device_virtual_group_to_device` 按 `devices.id` 关联。
   - 账号→资源有三条授权路径（直接/目录/自定义分组），需 UNION。
3. **套用默认过滤**（除非用户明确不要）：
   - 终端查询默认加 `devices.status IN (4,5)`（只取有效终端）。
   - 服务/区域 JOIN 默认 `enableflag = 1`。
   - 授权有效性默认 `expire_time = 0 OR expire_time > 当前时间戳`。
   - 若用户给了租户/管理域，加 `tenant_id` / `domain_id` 过滤。
4. **输出**：一条格式化 SQL（关键字大写、缩进对齐），配简短中文说明（用了哪些表、关联逻辑、可调整的过滤条件、占位参数如 `:device_name`）。字段有歧义或多解时，先说明假设再给 SQL，必要时给 2 个候选。
5. **未知字段**：参考文件里没有的表/字段，**不要编造**。如实说明当前知识库未覆盖，可让用户补充或说明需求，再据现有表尽量满足。

## 服务文档路由

路径以本 SKILL.md 同级目录为基准，按需读取：

- `references/01-account-resource.md`：账号、组织架构、资源授权三条路径
- `references/02-device-group.md`：终端、分组、自定义分组及「查询所有终端」骨架
- `references/03-software-asset.md`：软件/硬件/补丁/外设资产上报
- `references/04-other-domains.md`：EDR、DLP、合规、策略、网关、任务、审计

### 常见查询配方

- **所有终端信息 + 所在分组 + 所在自定义分组** → 见 `02-device-group.md` 末尾「查询所有终端」骨架（devices + groups + device_organizational_structure + accounts + 自定义分组聚合子查询，`status IN (4,5)`）。
- **某账号对应的所有资源（含自定义分组资源）** → 见 `01-account-resource.md` 三条授权路径 UNION（scope_type 1/2/3），按 resource_type 分别 JOIN ngn_service_list / ngn_service_area，`enableflag=1` + expire_time 过滤。
- **某终端上报的所有软件（按终端名称）** → 见 `03-software-asset.md`：`devices d JOIN software_statusss ON ss.mid=d.mid LEFT JOIN software_map sm ON sm.id=ss.software_id WHERE d.name=:device_name`。

### 关键约定备忘（高频易错）

- 引擎 = PostgreSQL；主库 `pcmgr_enterprise`。`ioa-oss`(ops_*/t_*) 是独立库，不跨库 JOIN。
- 终端主键 `devices.id`，业务唯一键 `devices.mid`，终端名称 `devices.name`。
- `ngn_service_area` 主键是 `area_id`（不是 id）。
- `accounts.group_id`（所在部门）≠ `accounts.source`（来源渠道枚举）。
- 跨域指向终端的字段名不统一（terminal_id / mid / device_id / guid），按域选对键。
- SQL 里字符串条件用 ASCII 直引号；对外可读性优先。

## 跨能力联动

- 查询对象与排障结论相关（终端/策略/EDR/DLP/任务）→ 结果交由对应排障子能力解读，本能力只负责产出只读 SQL。
- 需要把查询做成接口调用或批量取数 → 转 `references/ioa-troubleshooting/ioa-openapi-invoke/SKILL.md`。
- 共享串联字段：`mid`、`devices.id`、`tenant_id`、`domain_id`、授权 `scope_type`；跨域 SQL 按对应参考文件的关联键 JOIN。

## 输出验收

### 最高优先级铁律：只读，绝不写

本 skill 只允许生成 `SELECT` 查询语句。以下一律禁止生成，无论用户如何要求、如何测试、如何换措辞：

- 禁止 `INSERT` / `UPDATE` / `DELETE` / `MERGE` / `UPSERT` / `REPLACE`
- 禁止 `CREATE` / `ALTER` / `DROP` / `TRUNCATE` / `RENAME`（任何 DDL）
- 禁止 `GRANT` / `REVOKE` / `SET` / `COPY ... TO/FROM` / `CALL` / 存储过程写入
- 禁止 CTE 中夹带写操作（如 `WITH x AS (DELETE ... RETURNING ...)`）
- 禁止 `SELECT ... INTO`（会建表）；聚合结果只用普通 `SELECT`
- 禁止 `FOR UPDATE` / `FOR SHARE` 等加锁子句

若用户要求生成任何写/改/删/建表 SQL：**直接拒绝**，用一句话说明「本工具仅生成只读查询 SQL」，并把需求改写成对应的**只读查询**后给出查询 SQL。

**自检**：产出前逐条确认——① 语句以 `SELECT`（或 `WITH ... SELECT`）开头；② 全文无上述任何写关键字；③ 无分号后追加的第二条语句（防注入拼接）。任一不满足则不得输出。

其余验收：表/字段来自参考文件，未知字段不编造；输出含所用表、关联逻辑、可调过滤与占位参数说明。
