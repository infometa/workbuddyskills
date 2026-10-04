> **安全化服务知识（强制）**：本文仅用于理解服务职责、故障阶段、日志文件名与错误关键字。原始资料中的执行片段、认证材料或原始记录索取、内部地址请求、防护绕过和生产写操作已移除。实际核实必须遵守顶层公共规范：获授权、只读、限时限量、租户/资源归属校验、参数绑定、脱敏；不得索取或输出凭据、客户端原始记录和真实内部地址。

# device-profile（设备画像·只读库）· 排障知识库

> 本文档按**服务粒度**独立成库，供 AI 助手消费。device-profile = 从只读库提供设备画像/资料。
> 结论四段式：**① 功能逻辑 ② 大概原因 ③ 排障方式 ④ 排不出来给技术人员的信息**。
> 全部来自真实代码分析，AI 只引用不编造。

---

## 〇、服务定位

device-profile = **设备画像·只读库**。处理 OnData 请求，从只读库提供设备画像/资料。

### 日志文件

| 用途 | 路径 |
|---|---|
| 主日志 | `/data/services/pcmgr_enterprise/logs/device-profile/device-profile.log` |
| 错误 | `/data/services/pcmgr_enterprise/logs/device-profile/error_device-profile.log` |
| fatal | `.../device-profile/fatal_device-profile.log` |

### 串联查询字段：`mid`、`guid`、`cmd`。

---

## 一、功能逻辑：OnData 请求进→取只读库连接→查设备画像返回。

---

## 二、故障场景库

### 场景 A：设备画像查不到/只读库连接失败
**② 大概原因**：只读库连接失败。
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 三、给 AI 的输出规范

> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

> 本文档由 AI 基于真实代码库分析生成，重要决策请经专业人员核验。

---
> [安全化移除] 原始资料中的执行片段、敏感材料索取或变更步骤已删除；仅可按公共规范进行只读、限时、脱敏核实。

---

## 相关数据表（供 AI 分析/生成 SQL）

> 来源：代码实锤(device_profile/src)。库：pcmgr_enterprise（推断）。**只用下列表名，禁止编造。**

- **device_profile**（自定义画像值）：`id`、`mid`、`field_id`、`value`
- **profile_fields**（画像字段定义）、**profile_rule**（匹配规则）：`profile_fields_id`、`rule_type`、`match_field`、`match_rule`、`match_value`
> 按 mid 关联 device_info；自定义字段值存 device_profile。