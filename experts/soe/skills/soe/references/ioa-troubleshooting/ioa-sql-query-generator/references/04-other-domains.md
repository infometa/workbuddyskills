# 外围业务域表清单（EDR/DLP/合规/策略/网关/任务运维/审计）

> 求全不求深：主键 + 关键外键 + 少量业务字段。多数表带 `tenant_id`（租户）、`domain_id`（管理域），生成 SQL 时按需过滤。
> ⚠ `ioa-oss`（ops_* / t_* / server_info）是**独立运维库（SQLite 语法）**，不要与主 PostgreSQL 库跨库JOIN。

## 域 1：EDR / 安全告警
关系链：`edr_incident (1) ─< edr_event (N) ─> edr_rule / edr_policy / edr_terminal / edr_log`，取证走 `edr_evidence.event_id`。

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `edr_incident` | 安全事件（一次攻击聚合体） | id | tenant_id |
| `edr_event` | EDR 告警事件（单条命中明细） | id | incident_id→edr_incident; rule_id→edr_rule; policy_id→edr_policy; terminal_id→edr_terminal; account_id; matched_log_id→edr_log |
| `edr_incident_comment` | 事件处置备注 | id | incident_id |
| `edr_incident_judg` | 事件研判流水 | id | incident_id |
| `edr_evidence` | 事件取证（证据节点） | id | incident_id; event_id; account_id |
| `edr_event_agg` | 告警聚合视图 | id/uuid | event_id |
| `edr_event_graph_trace` | 攻击溯源图轨迹 | id | event_id; tenant_id |
| `edr_attack_graph_node` | 攻击图节点 | id | 关联事件/溯源图 |
| `edr_rule` | EDR 检测规则（树） | id | policy_id; parent_node_id 自关联 |
| `edr_policy` | EDR 检测策略 | id | tenant_id |
| `edr_policy_group` | EDR 策略分组（树） | id | parent_id 自关联 |
| `edr_white_policy` | 白名单/放行策略 | id | policy_id; ostype |
| `edr_active_defense_rule` | 主动防御规则 | id | tenant_id; defense_type/ostype |
| `edr_terminal` | EDR 终端资产快照 | id | terminal_group_id; last_account_id; domain_id |
| `edr_log` | EDR 原始行为日志(可SQL检索) | id | event_type/action_type |
| `edr_yara_rule` / `edr_yara_group` | YARA 规则 / 分组 | id | group_id→edr_yara_group |
| `edr_store_policy`/`edr_store_record`/`edr_store_cos` | 取证存储策略/记录/COS桶 | id | cos_id→edr_store_cos |
| `edr_tix_intelligence`/`edr_tix_sandbox` | 威胁情报 / 沙箱结果 | id | tix_task_id |
| `edr_async_exec_log`/`edr_job` | 异步执行日志 / 后台作业 | id | tenant_id |
| `edr_log_sql_history`/`edr_log_sql_favorite`/`edr_log_sql_favorite_group` | 日志SQL检索历史/收藏/收藏分组 | id | fav_id→favorite; group_id→favorite_group; parent_id 自关联 |
| `report_vul_device` | 漏洞/风险上报设备清单 | id | device_id→devices; devices_group_id→groups |
| `edr_*_config`（一组字典） | 规则字段/算子/枚举/攻击手法/事件类型/风险标签配置 | id | 纯字典表 |

## 域 2：DLP 数据防泄漏

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `dlp_alarm`（含分表 `dlp_alarm_split_*`） | DLP 告警（敏感数据外发/操作） | id | policy_id; account_id/user_id; file_category_id |
| `dlp_alarm_policy` | DLP 告警策略 | id | data_rule_id→dlp_data_rule |
| `dlp_alarm_policy_scope` | 告警策略作用范围 | id | dlp_alarm_id; object_id+object_type |
| `dlp_alarm_commment` | 告警处置备注 | id | dlp_alarm_id |
| `dlp_approval`/`dlp_approval_record` | 外发审批配置 / 申请记录 | id | approval_id; account_name/user_id |
| `dlp_policy_item` | 策略项（控制通道明细） | id | policy_id; data_rule_id; template_id→dlp_tips_template |
| `dlp_data_rule`/`dlp_data_rule_info` | 敏感数据识别规则 / 明细 | id | category_id; library_id; file_source_id |
| `dlp_data_category`/`dlp_data_label`/`dlp_data_level` | 数据分类 / 标签 / 密级 | id | domain_id |
| `dlp_data_library` | 数据识别库（指纹/词典） | id | library_id; rule_type |
| `dlp_file_source`/`dlp_file_source_config`/`dlp_file_result` | 文件来源 / 配置 / 识别结果 | id | source_type |
| `dlp_tips_template` | 提示语/告知模板 | id | template_type; lang_type |
| `dlp_custom_channel`/`dlp_internal_address` | 自定义管控通道 / 内部地址 | id | domain_id |
| `dlp_flyback_policy`/`_scope`/`dlp_flyback_task`/`_scope` | 数据回捞策略/范围/任务/范围 | id | policy_id; data_rule_id; object_id+object_type |
| `dlp_self_scan_task`/`dlp_nonsensitive_file` | 终端自查任务 / 非敏感白名单 | id | policy_id; task_id |
| `dlp_status`/`dlp_store_status` | 终端DLP开启状态 / 上传状态 | id | user_id |
| `dlp_store_policy`/`_scope`/`dlp_store_cos`/`dlp_store_config`/`dlp_store_record` | 落地存储策略/范围/COS/配置/记录 | id | cos_id→dlp_store_cos; rule_ids→dlp_data_rule |
| `wechat_dlp_store_policy`/`_scope` | 企微DLP 存储策略及范围 | id | object_id+object_type |

## 域 3：合规检查 & 客户端健康

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `client_health_policy` | 客户端健康/合规基线策略 | id | domain_id; os_type; time_effect_type |
| `client_health_policy_scope` | 健康策略作用范围 | id | policy_id→client_health_policy; object_id+object_type; guid(终端); apply_type |
| `compliance` | 合规检查结果/判定（准入引擎与报表引用） | id | 关联终端/账号 |

## 域 4：策略类（access / 准入 / 通用）
范式：`*_policy` 主表 ←(policy_id)— `*_scope` 从表；范围表用 `object_type + object_id`（或 guid）指向账号/分组/终端。

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `apply_control_policy` | 应用管控/访问控制策略(ACL引擎核心) | id | area_id→ngn_ip_area; user_scope/resource_scope(JSON) |
| `policy` | 通用策略实体 | id | tenant_id |
| `ngn_strategys`/`security_ngn_strategys` | 零信任访问策略 / 安全访问策略 | id | 关联账号/资源/网关 |

## 域 5：网关 / 访问代理（NGN / WebGW）

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `ngn_gateway_status` | 网关(SPA)节点状态同步 | id | mid(网关机器); ip; spa_status/status/version |
| `ngn_black_device` | 网关黑名单设备 | id | mid→设备; ticket(工单) |
| `ngn_ip_area` | IP 区域/网段定义 | id | 被 apply_control_policy.area_id 引用 |
| `ngn_service_webgw`/`ngn_service_client` | WebGW侧/客户端侧访问服务列表 | id | service_id |
| `ngn_service_audit` | 访问服务/URL 审计 | id | service_id; area_id→ngn_ip_area |
| `certificate_webgw`/`cert_res_webgw` | WebGW证书 / 证书资源关联 | id | cert_id |
| `api_secret_webgw`/`custom_host_webgw` | WebGW API密钥 / 自定义Host | id | tenant_id |
| `connector_client` | Connector 客户端列表 | id | connector_id |
| `key_login_address` | 密钥登录地址配置 | id | 关联 webgw |

## 域 6：任务 / 运维
### 任务下发（主库）
| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `task_seq` | 任务序列（一次下发批次） | seq | task_id; business_id; mid_list |
| `task_seq_mid` | 任务-终端明细（每终端一条状态） | id | task_seq→task_seq; mid |
| `task_result` | 任务执行结果 | task_seq+mid | task_id/task_seq; mid |

### ioa-oss运维库（⚠独立库，SQLite）
`ops_deploy`/`ops_deploy_info`/`ops_deploy_patch*`/`ops_deploy_kb*`（部署/补丁/KB）、`ops_task`/`ops_new_task`/`ops_async_task`（任务）、`ops_server_info`/`ops_server_group`（服务器）、`ops_opt_log`（运维审计）、`ops_user`/`ops_user_session`/`ops_auth_role`/`ops_auth_router`/`ops_auth_role_router`（RBAC）、`file_distributes`/`file_operations`、`t_*`（旧版遗留）。

## 域 7：审计 / 日志 / 告警通知

| 表名 | 含义 | 主键 | 关键外键 |
|---|---|---|---|
| `account_activity` | 账号活跃度/最近上报 | id | uid→accounts; active_state; last_active_report_time |
| `ngn_service_audit` | 访问服务/URL 审计 | id | service_id; area_id |
| `warn_notice_log` | 告警通知发送日志 | id | type |
| `warn_config`/`warn_subscribe`/`notify_chan_config` | 告警配置/订阅/通知渠道 | id | chan↔config |
| `alert_rule_template` | 告警规则模板 | id | — |

## 通用建模提示
1. 多租户：多数表有 tenant_id（+ 很多有 domain_id），用户指定范围时加过滤。
2. 策略↔范围范式：`*_policy` ← `*_scope`（policy_id 外键），object_type+object_id 指向对象。
3. 跨域指向终端字段名不统一：EDR 用 terminal_id/edr_terminal；任务/网关黑名单用 mid；策略范围用 guid/object_id；报表用 device_id→devices。按域选对键。
4. ioa-oss 独立库，不与主库跨库 JOIN。
5. DLP 告警有`dlp_alarm_split_*` 分表。
