---
name: emr-query-skill
description: 腾讯云 EMR 只读查询技能 — 基于官方 tccli 的 48 个只读查询接口文档与调用模板
version: "1.1.0"
author: "Tencent Cloud EMR"
---

# 腾讯云 EMR 查询 Skill

本 Skill 以官方 `tccli` 为主路径，整理腾讯云 EMR 当前可直接调用的 48 个只读接口文档，覆盖集群资源、节点、服务、用户、作业（Spark/Hive/Yarn/Impala/Trino/StarRocks/Kyuubi）、监控、事件、巡检、扩缩容、询价等查询场景。

> 📂 每个接口的详细参数见 `references/<分类>/<Action>.md`（48 个独立文件）
> 📋 总限制规则见 `references/query-rules.md`
> 🧪 统一模板与命令组织见 `references/unified-template.md`
> ✅ 当前连接器主路径已切换为官方 `tccli`；`scripts/tc_api.py` 仅保留为开发调试备用

---

## 可用命令

所有操作通过 `tccli emr <Action>` 执行。

### 模板 1：简单参数直接展开

```bash
tccli emr <Action> --region <region> --version 2019-01-03 --cli-unfold-argument --Param1 value1 --Param2 value2
```

适用场景：只有标量参数，或参数较少、无复杂嵌套结构。

### 模板 2：复杂 / 嵌套参数走 JSON 文件

```bash
tccli emr <Action> --generate-cli-skeleton > /tmp/<Action>.json
# 编辑 /tmp/<Action>.json 填入真实参数

tccli emr <Action> --region <region> --version 2019-01-03 --cli-input-json file:///tmp/<Action>.json
```

适用场景：`Filters`、`FlowParam`、`ResourceSpec`、数组/对象嵌套参数。

### 命令自查

```bash
# 看参数列表
tccli emr <Action> help

# 看详细参数说明
tccli emr <Action> help --detail

# 生成官方 JSON 骨架
tccli emr <Action> --generate-cli-skeleton
```

---

## 常用命令示例

### 集群资源

```bash
# 查询集群列表
tccli emr DescribeInstancesList --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --DisplayStrategy clusterList --Limit 100

# 查询集群详情
tccli emr DescribeInstances --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --DisplayStrategy clusterList --InstanceIds emr-e3orculh --ProjectId -1

# 查询集群节点
tccli emr DescribeClusterNodes --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh --NodeFlag all
```

### 作业与引擎查询

```bash
# Spark 查询记录
tccli emr DescribeSparkQueries --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh --StartTime 1750780800 --EndTime 1750867200 --Offset 0 --Limit 20

# Hive 查询记录
tccli emr DescribeHiveQueries --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh --StartTime 1750780800 --EndTime 1750867200 --Offset 0 --Limit 20
```

### 监控与流程

```bash
# 巡检结果
tccli emr DescribeInspectionTaskResult --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh

# 流程状态（复杂参数示例）
tccli emr DescribeClusterFlowStatusDetail --generate-cli-skeleton > /tmp/DescribeClusterFlowStatusDetail.json
# 编辑 JSON 后执行：
tccli emr DescribeClusterFlowStatusDetail --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeClusterFlowStatusDetail.json
```

### 扩缩容与调度

```bash
# 自动扩缩容记录
tccli emr DescribeAutoScaleRecords --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh --Offset 0 --Limit 20

# YARN 队列
tccli emr DescribeYarnQueue --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-e3orculh --Scheduler capacity
```

---

## 接口分类速查

| 分类 | 数量 | 说明 |
|------|------|------|
| cluster-resource | 10 | 集群、节点、配额、续费、询价 |
| cluster-service | 2 | 全局配置、资源调度 |
| user-management | 2 | 用户、用户组 |
| info-query | 23 | 作业、监控、事件、巡检、节点与服务 |
| autoscaling | 4 | 扩缩容配置、策略、记录、节点数据盘 |
| configuration | 1 | 服务配置组 |
| misc | 2 | JobFlow、旧版调度历史 |
| yarn-schedule | 2 | 调度差异、队列 |
| sl-hbase | 2 | Serverless HBase |

---

## 认证与状态

### 认证方式

- 主路径使用 `tccli auth login`
- 也兼容已存在的 `~/.tccli/default.credential`
- 认证成功后，连接器通过 `DescribeInstancesList` 检查 EMR 访问是否可用

### 状态判定

连接器 `status` 命令以以下调用作为健康检查：

```bash
tccli emr DescribeInstancesList --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --DisplayStrategy clusterList --Limit 1
```

返回成功即视为“已认证且具备 EMR 访问能力”。

### 退出认证

```bash
tccli auth logout
```

---

## 调用纪律

| 规则 | 说明 |
|------|------|
| 严格只读 | 仅允许 `Describe*` / `Inquiry*` / `Inquire*` |
| 禁止并发调用 | tccli 并行调用存在配置文件竞争，**必须串行**，一个接口结束后再调下一个 |
| 先查后用 | `InstanceId` / `ClusterId` 先用 `DescribeInstancesList` 获取 |
| Region 必确认 | 用户未指定时先确认地域 |
| 时间范围受限 | 多数作业/监控接口需要最近时间窗口，避免盲填超长区间 |
| 简单参数优先展开 | 无嵌套时优先 `--cli-unfold-argument` |
| 复杂参数优先 skeleton | 有对象/数组嵌套时优先 `--generate-cli-skeleton` + `file:///tmp/<Action>.json` |
| 不在命令行透传密钥 | 禁止显式拼接 `--secretId` / `--secretKey` / `--token` |
| 大结果分页 | 默认只展示首屏摘要，必要时用 `Offset` / `Limit` / `Page` / `PageSize` 翻页 |

---

## 错误处理

`tccli` 默认返回 JSON，失败时关注：

| 错误码前缀 | 含义 | 处理 |
|-----------|------|------|
| `AuthFailure.*` | CAM 权限不足 | 提示用户授权 `emr:<Action>` |
| `UnauthorizedOperation` | 资源级未授权 | 检查 `qcs::emr` 资源权限 |
| `InvalidParameter.*` | 参数格式/范围错误 | 对照接口文件或 `help --detail` 修正 |
| `MissingParameter` | 必传参数缺失 | 先看该接口独立文档，再必要时用 skeleton 补齐 |
| `ResourceNotFound.*` | 资源不存在 | 检查集群 ID / 节点 ID |
| `FailedOperation` | 集群类型不匹配 | 检查是否对非 TKE / 非 SL / 未配置调度器集群调用 |
| `LimitExceeded` | 频率限制 | 减少并发并稍后重试 |

---

## 注意事项

- ⛔ 禁止调用任何写接口：`Create*`、`Modify*`、`Terminate*`、`Run*`、`Delete*`
- 🔒 优先使用 tccli 已持久化凭证，不在命令行中传明文密钥
- 📘 参数真值以 `tccli emr <Action> help --detail` 与各接口独立文件为准
- 🧩 对于嵌套 JSON 参数，优先走 skeleton 文件而不是手写超长命令
- 🧪 `scripts/tc_api.py` 保留用于仓库内开发调试，不再作为连接器主调用入口
