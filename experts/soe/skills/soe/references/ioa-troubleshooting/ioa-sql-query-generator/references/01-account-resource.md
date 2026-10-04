# 账号 / 组织架构 / 资源授权域（PostgreSQL）

> 数据库引擎：PostgreSQL，默认库 `pcmgr_enterprise`。以下表来自 ioa-backend GORM/xorm 模型 + 真实迁移/查询 SQL 交叉验证。
> 多租户：多数表带 `tenant_id`；部分带 `domain_id`（管理域）。生成 SQL 时若用户提供租户/域范围，应加过滤。

## 表清单速览

| 表名 | 含义 | 主键 |
|---|---|---|
| `accounts` | 账号（用户）主表 | `id` |
| `account_groups` | 账号目录 / 组织架构部门（OU 树） | `id` |
| `account_virtual_groups` | 账号自定义分组（跨部门虚拟组） | `id` |
| `account_virtual_group_to_account` | 自定义分组↔账号 多对多关联 | `id` |
| `resource_to_accounts` | 资源授权关系主表（三条授权路径交汇） | `id` |
| `resource_inherit_config` | 资源继承配置（关闭继承的例外） | `id` |
| `ngn_service_list` | 零信任单个服务/资源（service_id 指向） | `id` |
| `ngn_service_area` | 零信任资源区域（service_area_id 指向） | `area_id` |
| `custom_resource` | 自定义资源（软件/站点等 KV） | `id` |

---

## accounts — 账号主表
每条=一个用户账号，隶属某账号目录（group_id），标记来源（source）。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 账号主键 |
| `user_id` | varchar | 登录账号名/工号（业务唯一键，配合 source/tenant） |
| `user_name` | varchar | 用户显示姓名 |
| `group_id` | int | 所属账号目录 ID → `account_groups.id` |
| `source` | int | 账号来源（枚举见下，≠ group_id） |
| `status` | int | 状态，1=有效/正常 |
| `extra_info` | jsonb | 扩展信息（email/phone/id_card/position/valid_time_int/ioa_disable_account 等） |
| `user_pwd` | varchar | 密码散列 |
| `tenant_id` | varchar | 租户 ID |
| `utime`/`itime` | timestamptz | 更新/创建时间 |

**source 枚举**：0=自建/本地；1=LDAP(AD 域)；5=企业微信；7=政务微信；8=OpenLDAP；11=蜂鸟；15=玉符；16=BDUS；17=希音。

**group_id vs source**：group_id 是组织树挂载位置（人在哪个部门）；source 是来源渠道（账号从哪来）。二者正交。

---

## account_groups — 账号目录 / 组织架构部门
组织架构树（OU），账号挂在节点上，资源可按目录授权并向下继承。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 目录节点 ID |
| `name` | varchar | 部门/目录名称 |
| `parent_id` | int | 父节点 ID（自关联 id），根为 0 |
| `id_path` | varchar | 从根到本节点的 ID 路径，如 `1,2,5` |
| `name_path` | varchar | 名称路径 |
| `id_path_arr` | int[] | ID 路径数组；`id = ANY(id_path_arr)` 可取祖先链 |
| `org_id` | varchar | 外部组织 ID |
| `source` | int | 目录来源（同 accounts.source 语义） |
| `tenant_id` | varchar | 租户 |
| `utime`/`itime` | time | 更新/创建 |

---

## account_virtual_groups — 账号自定义分组
跨部门虚拟用户组，独立于组织架构做授权。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 自定义分组 ID |
| `name` | varchar | 分组名称 |
| `guid` | varchar | 全局唯一标识 |
| `group_id` | int | 分组归属分类 ID（分组自身归类，非账号目录） |
| `source_type` | int | 1=本地创建，2=导入 |
| `domain_id` | int | 管理域 ID |
| `utime`/`itime` | time | 更新/创建 |

---

## account_virtual_group_to_account — 自定义分组↔账号

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 关联 ID |
| `account_virtual_group_id` | int | → `account_virtual_groups.id` |
| `account_id` | int | → `accounts.id` |

---

## resource_to_accounts — 资源授权关系主表 ★核心
把「资源」授权给「主体」。主体三选一（账号/目录/自定义分组），资源二选一（单服务/资源区域）。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 授权 ID |
| `scope_type` | int | 主体类型：1=账号, 2=账号目录, 3=自定义分组 |
| `account_id` | int | scope_type=1 时填 → `accounts.id`（且 >0） |
| `account_group_id` | int | scope_type=2 时填 → `account_groups.id`（且 >0） |
| `account_virtual_group_id` | int | scope_type=3 时填 → `account_virtual_groups.id`（且 >0） |
| `resource_type` | int | 资源类型：1=单个服务, 2=资源区域 |
| `service_id` | int | resource_type=1 时填 → `ngn_service_list.id` |
| `service_area_id` | int | resource_type=2 时填 → `ngn_service_area.area_id` |
| `expire_time` | int | 授权到期 Unix 时间戳；0=长期有效 |
| `utime`/`itime` | time | 更新/创建 |

---

## resource_inherit_config — 资源继承配置
默认目录/子目录/自定义分组授权向下继承；此表记录**关闭继承**的例外。

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | int PK | 配置 ID |
| `inherit_type` | int | 1=用户继承所在OU组, 2=OU组继承父OU组, 3=用户继承虚拟组 |
| `account_id` / `account_group_id` | int | 对象 |
| `service_id` / `service_area_id` | int | 资源 |
| `resource_type` | int | 1=单服务, 2=资源区域 |
| `inherit_switch` | int | 1=不继承(Close), 2=继承(Open) |

---

## ngn_service_list — 零信任单个服务/资源
service_id 指向，一条=一个可访问业务服务。

关键字段：`id`(PK)、`service_name`、`service_type`、`service_address`、`service_port`、`area_id`(→`ngn_service_area.area_id`)、`protocol`、`enableflag`(JOIN 时恒 =1)、`service_network`(1=内网/2=外网)、`domain_id`、`utime`/`itime`。

## ngn_service_area — 零信任资源区域
service_area_id 指向。**主键是 `area_id`**。
关键字段：`area_id`(PK)、`area_name`、`enableflag`(JOIN 时恒 =1)、`domain_id`、`utime`/`itime`。

## custom_resource — 自定义资源（KV）
字段：`id`(PK)、`key`、`value`、`resource_type`(string, software/hyperlink 等)、`resource_group`、`tenant_id`、`itime`/`utime`。

---

##★ 授权路径：一个账号拥有的全部资源 = 三条路径 UNION

给定 `accounts.id = :aid`：

**路径 A｜直接授权给账号（scope_type=1）**
```
resource_to_accounts (scope_type=1 AND account_id=:aid AND account_id>0)
  resource_type=1 → JOIN ngn_service_list ON id=service_id AND enableflag=1
  resource_type=2 → JOIN ngn_service_area ON area_id=service_area_id AND enableflag=1
```

**路径 B｜通过账号目录授权（scope_type=2，含向上级目录继承）**
```
取accounts.group_id → account_groups.id_path_arr 得本目录及所有祖先目录集合 :gids
resource_to_accounts (scope_type=2 AND account_group_id = ANY(:gids) AND account_group_id>0)
  再按 resource_type JOIN service / area
（严格版需排除 resource_inherit_config 中 inherit_switch=1 的例外项）
```

**路径 C｜通过自定义分组授权（scope_type=3）**
```
account_virtual_group_to_account (account_id=:aid) → 得 :vgids
resource_to_accounts (scope_type=3 AND account_virtual_group_id = ANY(:vgids) AND account_virtual_group_id>0)
  再按 resource_type JOIN service / area
```

最终资源 = A ∪ B ∪ C，再用 `expire_time`（=0 或 > 当前时间戳）过滤有效授权。

## 枚举常量表

| 字段 | 值 | 含义 |
|---|---|---|
| scope_type | 1 / 2 / 3 | 账号 / 账号目录 / 自定义分组 |
| resource_type | 1 / 2 | 单个服务(→ngn_service_list) / 资源区域(→ngn_service_area) |
| inherit_switch | 1 / 2 | 不继承 / 继承 |
| accounts.source | 0/1/5/7/8/11/15/16/17 | 自建/AD/企微/政务微信/OpenLDAP/蜂鸟/玉符/BDUS/希音 |
