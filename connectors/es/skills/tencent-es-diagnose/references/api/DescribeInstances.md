# DescribeInstances（MCP）

> Tool：`DescribeInstances` | MCP tool | 只读

## 功能描述

查询账户下的 ES 集群实例列表或指定集群详情，含规格、状态、节点拓扑等基础信息。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `Region` | String | ✅ | 地域，如 `ap-guangzhou` |
| `InstanceIds` | String[] | ❌ | 集群 ID 列表，按 ID 精确查询 |
| `InstanceNames` | String[] | ❌ | 集群名称列表，按名称查询 |
| `Fields` | String[] | ❌ | **返回字段投影白名单**，用于裁剪响应体、规避上下文截断。见下方「默认精简字段集」 |
| `Limit` | Number | ❌ | 分页大小，默认 20，**最大 100** |
| `Offset` | Number | ❌ | 分页起始位置，默认 0 |
| `OrderByKey` | String | ❌ | 排序字段：1=实例ID，2=实例名称，3=可用区，4=创建时间 |
| `OrderByType` | String | ❌ | 排序方式：0=升序，1=降序 |

>ℹ️ MCP 版本**不支持** `TagList` 与 `HealthStatus` 过滤参数。按健康状态筛选需拉取后在结果中自行过滤。

## ⚠️ 默认只返回精简字段集（最易踩的坑）

**不传 `Fields` 时，响应只含精简字段**：实例 ID / 名称 / 状态 / 健康度 / 版本 / 规格 / 地域 / 创建时间等。

🔴 **`NodeInfoList`（节点拓扑）、`EsAcl` 等字段不在精简集内** —— 需要按节点类型看拓扑、节点数、单节点磁盘时，**必须显式传 `Fields`**，否则会拿到"字段不存在"的错觉并据此做出错误判断。

`Fields` 匹配规则：

- 字段名**精确匹配**（大小写不敏感）
- 某个取值未精确命中时，**退化为关键词子串匹配**（如 `Disk` 会命中 `DiskType` / `DiskSize` / `DiskEncrypt`）
- 传 `["*"]` 返回**全量字段**

```
# 需要节点拓扑时（如核对节点数、单节点磁盘）
DescribeInstances(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"],
                  Fields=["InstanceId","InstanceName","Status","HealthStatus",
                          "EsVersion","NodeInfoList","DiskType","DiskSize"])
```

> ⚠️ **不要动辄传 `Fields=["*"]`** —— 大集群全量字段可能撑爆上下文。按需列举字段名。

## 调用示例

```
# 查询指定集群详情（精简字段集）
DescribeInstances(Region="ap-guangzhou", InstanceIds=["es-xxxxxxxx"])

# 查询该地域全部集群（首页）——批量巡检推荐带 Fields 裁剪
DescribeInstances(Region="ap-guangzhou", Limit=100, Offset=0,
                  Fields=["InstanceId","InstanceName","Status","HealthStatus","EsVersion"])

# 按创建时间降序
DescribeInstances(Region="ap-guangzhou", Limit=100, OrderByKey="4", OrderByType="1")
```

## 分页

返回的 `TotalCount` 为该地域集群总数。当 `TotalCount` > 已取条数时继续翻页：`Offset += Limit`，直到 `Offset >= TotalCount`。

## 返回字段（关键）

| 字段 | 说明 |
|------|------|
| `TotalCount` | 集群总数 |
| `InstanceList[].InstanceId` | 集群 ID |
| `InstanceList[].InstanceName` | 集群名称 |
| `InstanceList[].Status` | **运行状态：1=正常**，0=处理中，-1=停止，-2=删除中，-3=已隔离，-4=已过期 |
| `InstanceList[].HealthStatus` | 健康色：0=Green，1=Yellow，2=Red，**-1=Unknown** |
| `InstanceList[].EsVersion` | ES 版本 |
| `InstanceList[].NodeNum` | 节点数量 |
| `InstanceList[].CpuNum` / `MemSize` | 单节点 CPU 核数 / 内存（MB）|
| `InstanceList[].DiskType` / `DiskSize` | 磁盘类型 / 单节点磁盘（GB）|
| `InstanceList[].TotalStorage` | 总存储（GB）|
| `InstanceList[].Zone` | 可用区；为空或 `-` 表示多可用区部署 |
| `InstanceList[].VpcUid` | VPC ID |
| `InstanceList[].ChargeType` | 计费类型：`POSTPAID_BY_HOUR`=按量，`PREPAID`=包年包月 |
| `InstanceList[].CreateTime` | 创建时间 |
| `InstanceList[].NodeInfoList[]` | 🔴 **需显式传 `Fields` 才返回**。节点分组拓扑，每项含 `Type`（`hotData`/`warmData`/`dedicatedMaster`/`dedicatedCoordinating`/`dedicatedMl`，**空值视为 `hotData`**）、`NodeNum`、`NodeType`、`DiskSize` |

> 🔴 **`HealthStatus` 不可单独采信**：该字段是管控面快照，可能延迟，极端情况返回 `-1`(Unknown) 而集群实际已Red。**必须**与监控 `Status` 指标、`CesClusterHealth` 三路交叉验证并取最严重。历史 bug 曾因此把 Red 集群判成 100 分。详见 [scoring-rules.md#集群健康色判定三路信号取最严重](../scoring-rules.md#集群健康色判定三路信号取最严重)。

## ⚠️ 大返回值处理

不带 `InstanceIds` 查询全量集群时，单次返回可能**超过 10 万字符**触发结果截断并落盘为文件。

**首选做法：用 `Fields` 在服务端裁剪**，从源头避免截断 —— 批量巡检只需要少量字段：

```
DescribeInstances(Region="ap-guangzhou", Limit=100, Offset=0,
                  Fields=["InstanceId","InstanceName","Status","HealthStatus","EsVersion"])
```

**兜底做法**（已经截断落盘时）：

1. **不要**试图分段翻阅全文
2. 用 Python 读取落盘文件并提取所需字段：

```python
import json
d = json.load(open("<落盘文件路径>"))
for x in d["Response"]["InstanceList"]:
    print(x["InstanceId"], x["InstanceName"], x["Status"], x["HealthStatus"])
```

> 📌 环境中**可能没有 `jq`**，优先用 Python 解析。

## 错误码

| 错误码 | 含义 |
|------|------|
| `AuthFailure.*` | CAM 权限不足，需授予 `es:DescribeInstances` |
| `ResourceNotFound.InstanceNotExist` | 集群 ID 不存在或地域不匹配 |
| `RequestLimitExceeded` | 接口限频，需降低调用频率 |
