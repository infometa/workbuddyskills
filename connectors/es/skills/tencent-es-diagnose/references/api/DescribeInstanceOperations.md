# DescribeInstanceOperations（MCP）

> Tool：`DescribeInstanceOperations` | MCP tool | 只读

## 功能描述

查询指定 ES 集群在某时间范围内的操作记录，含节点重启、扩缩容、配置变更等，用于审计与变更关联排查。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Region` | String | ✅ | 地域，如 `ap-guangzhou` |
| `InstanceId` | String | ✅ | 集群 ID，如 `es-xxxxxxxx` |
| `StartTime` | String | ❌ | 起始时间 `YYYY-MM-DD HH:mm:ss`，**默认 `2017-01-01 00:00:00`** |
| `EndTime` | String | ❌ | 结束时间 `YYYY-MM-DD HH:mm:ss`，默认当前时间 |
| `Limit` | Number | ❌ | 分页大小，默认 20，最大 100 |
| `Offset` | Number | ❌ | 分页起始位置，默认 0 |

> 🔴 **必须显式传时间窗口**：不传时默认查询 **2017-01-01 至今的全部记录**，对老集群会返回海量数据。诊断场景请按分析时段传入 `StartTime`/`EndTime`。

批量查询多个集群：本接口无批量参数，需逐个集群调用。

## 调用示例

```
# 查询单集群最近 24 小时变更记录
DescribeInstanceOperations(Region="ap-guangzhou", InstanceId="es-xxxxxxxx",
                           StartTime="2026-08-04 20:00:00",
                           EndTime="2026-08-05 20:00:00",
                           Limit=20)
```

## 返回字段（关键）

| 字段 | 说明 |
|------|------|
| `TotalCount` | 变更记录总数 |
| `Operations[].StartTime` / `EndTime` | 操作起止时间 |
| `Operations[].Type` | 操作类型，见下表 |
| `Operations[].Progress` | 操作状态：**1=成功，0=失败，-1=进行中** |
| `Operations[].SubAccountUin` | 操作人子账号 UIN |
| `Operations[].Detail` | 操作详情（变更前后配置）|

> 📌 打分规则 2l：统计 `Progress == 0` 的记录数作为「失败变更操作」，存在即-10分。

## 常见操作类型

| Type | 含义 |
|------|------|
| `es_cvm_restart_node` | 节点重启 |
| `ces_cvm_scaleup_instance` | 节点升配（垂直扩容）|
| `ces_cvm_scaledown_*` | 节点降配|
| `ces_cvm_scaleout_instance` | 增加节点（水平扩容）|
| `ces_cvm_scalein_instance` | 减少节点 |
| `ces_update_instance` | 更新集群配置 |
| `ces_create_instance` | 创建集群 |

## 关注点（排障场景）

- **时间线对齐**：变更时间是否与异常发生时间吻合 —— 这是判断「异常是否由变更引发」的第一依据
- 是否有节点重启、扩缩容、配置变更操作
- 是否存在失败变更（`Progress=0`）
- 节点重启后建议用 `CesGetNode` 核对当前节点状态是否已全部恢复

## 错误码

| 错误码 | 含义 |
|------|------|
| `AuthFailure.*` | CAM 权限不足，需授予 `es:DescribeInstanceOperations` |
| `ResourceNotFound.InstanceNotExist` | 集群 ID 不存在或地域不匹配 |
