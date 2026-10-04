# 费用估算指南

> **何时使用本文件**：在步骤 3（费用估算）中构造询价参数和解读价格返回时参考。
> **何时不使用**：选型规则和方案生成逻辑请参考 spec-recommendation-rules.md。

---

## 目录

- [§1 询价流程说明](#1-询价流程说明)
- [§2 DescribeGoodsDetail 参数构造](#2-describegoodsdetail-参数构造)
- [§3 CalculatePrice 询价接口](#3-calculateprice-询价接口)
- [§4 计费模式说明](#4-计费模式说明)
- [§5 费用估算经验值](#5-费用估算经验值)
- [§6 成本优化建议](#6-成本优化建议)

---

## ❗ 价格单位强提示（阅读本文档前必看）

> **`BillingCalculatePrice` 返回的所有金额字段（`Price` / `TotalCost` / `RealTotalCost`）单位均为「分」，需除以 100 转换为「元」后再展示给用户。**
>
> 忘记换算会导致报价虚高 100 倍，是本 Skill 最常见的低级错误。任何时候从询价接口取到金额，均先除 100 再参与后续计算和展示。

---

## 重要：PayMode 参数值映射

> ⚠️ 不同接口对计费模式使用不同的枚举值，调用时务必注意区分：

| 接口 | 参数名 | 包年包月 | 按量计费 |
|------|--------|---------|----------|
| TCHouseCDescribeSpec | PayMode | `PREPAID` | `POSTPAID_BY_HOUR` |
| TCHouseCDescribeGoodsDetail → ChargeProperties.ChargeType | ChargeType | `PREPAID` | `POSTPAID_BY_HOUR` |
| BillingCalculatePrice | PayMode | `prePay` | `postPay` |

---

## §1 询价流程说明

询价分为两步：

> 💰 **价格单位：询价接口返回金额均为「分」，展示前必需 ÷100 转换为「元」**（`Price` / `TotalCost` / `RealTotalCost` 均适用）。

```
步骤 1: TCHouseCDescribeGoodsDetail
  └─ 输入：集群配置（Region/Zone/规格/计费等）
  └─ 输出：GoodsCategoryId + GoodsDetail(JSON) + GoodsNum + PayMode + RegionId + ZoneId

步骤 2: BillingCalculatePrice
  └─ 输入：步骤 1 的返回结果（GoodsCategoryId/GoodsDetail/GoodsNum/PayMode/Region/Zone）
  └─ 输出：真实价格（Price/TotalCost/RealTotalCost/Policy 等）
```

> **重要**：`DescribeGoodsDetail` 是 cdwch 业务接口，只返回商品配置信息，不返回价格。真正的价格由 billing 的 `CalculatePrice` 接口返回。

---

## §2 DescribeGoodsDetail 参数构造

### 参数映射

将推荐方案转换为询价参数时，按以下映射关系：

| 方案配置项 | 询价参数 | 说明 |
|-----------|---------|------|
| 地域 | Region | 如 ap-guangzhou |
| 可用区 | Zone | 如 ap-guangzhou-6 |
| 操作类型 | Case | 创建询价固定传 `CREATE_QUERYPRICE` |
| 内核版本 | ProductVersion | 如 `26.3.3.0`，建议必填 |
| 计算节点规格 | Resources[].SpecName (Type=DATA) | 如 S_16_64_H |
| 计算节点数量 | Resources[].Count (Type=DATA) | 偶数（HA 模式） |
| 计算节点磁盘容量 | Resources[].DiskSpec.DiskSize | 单盘容量，单位 GB |
| 计算节点云盘数量 | Resources[].DiskSpec.DiskCount | 每节点挂载的云盘块数 |
| 计算节点磁盘类型 | Resources[].DiskSpec.DiskType | CLOUD_HSSD / CLOUD_PREMIUM / CLOUD_SSD |
| Common 节点规格 | Resources[].SpecName (Type=COMMON) | 如 S_4_16_H |
| Common 节点数量 | Resources[].Count (Type=COMMON) | 通常为 3 |
| Common 节点磁盘 | Resources[].DiskSpec.DiskSize | 单位 GB |
| 计费类型 | ChargeProperties.ChargeType | PREPAID / POSTPAID_BY_HOUR |
| 时长（包年包月） | ChargeProperties.TimeSpan | 数值，配合 TimeUnit 使用 |
| 时长单位 | ChargeProperties.TimeUnit | `m`（月）或 `h`（小时） |
| 是否高可用 | HaFlag | true/false |
| 是否跨可用区 | IsSecondaryZone | true 表示多可用区部署 |
| 跨 AZ 信息 | SecondaryZoneInfo | JSON 数组，指定备可用区。[0]=备可用区1，[1]=备可用区2（可选）。主可用区通过 Zone 参数指定。每个元素只需传入 SecondaryZone 字段 |
| ZK 高可用 | HAZk | 仅单副本（HaFlag=false）时有效。true=开启 ZK 高可用并部署 Common 节点 |
| ClickHouseKeeper | ClickhouseKeeper | 使用 CKKeeper 替代 ZK。仅在需要部署 Common 节点时有效 |
| 无 Keeper | NoKeeper | 仅双副本（HaFlag=true）+ 白名单用户有效。true=不部署 Common 节点 |

### Case 参数取值说明

| 场景 | Case 值 | 说明 |
|------|---------|------|
| 创建询价 | `CREATE_QUERYPRICE` | 新建集群时获取价格 |
| 变配询价 | `MODIFY_QUERYPRICE` | 变更已有集群配置时获取价格差 |
| 续费询价 | `RENEW_QUERYPRICE` | 续费已有集群时获取价格 |

### 跨可用区（多 AZ）参数说明

> ⚠️ **白名单限制**：`IsSecondaryZone=true` 受后端 `SecondaryZoneWhitelist` 控制，非白名单账户无论如何组合 `SecondaryZoneInfo` / `HAZk` / `ClickhouseKeeper` 都会返回 `InvalidParameter`。遇到该错误时**直接回退到单可用区询价**（`IsSecondaryZone=false` 且不传 `SecondaryZoneInfo`）：**跨 AZ 与单 AZ 部署的计费单价一致，跨 AZ 不会引入额外费用**，仅为架构部署差异。报告中需注明「跨 AZ 部署不影响计费单价」。详见 [api-reference.md#跨可用区询价的白名单限制](api-reference.md#%EF%B8%8F-%E8%B7%A8%E5%8F%AF%E7%94%A8%E5%8C%BA%E8%AF%A2%E4%BB%B7%E7%9A%84%E7%99%BD%E5%90%8D%E5%8D%95%E9%99%90%E5%88%B6)。

当需要跨可用区部署时：
- `IsSecondaryZone` 设为 `true`
- 主可用区通过顶层 `Zone` 参数指定（与 `HAZk`、`ClickhouseKeeper` 同一层）
- `SecondaryZoneInfo` 传入 JSON 数组，仅包含备可用区信息，每个元素只需传入 `SecondaryZone` 字段（不再需要 `SecondarySubnet` 和 `SecondaryUserSubnetIPNum`）：
  - `[0]` = 备可用区1（UI 标签为"备可用区1"）
  - `[1]` = 备可用区2（可选，三 AZ 场景，UI 标签为"备可用区2"）

示例（主可用区 ap-guangzhou-6 通过 Zone 参数指定，备可用区1 为 ap-guangzhou-7）：
```json
[
  {"SecondaryZone": "ap-guangzhou-7"}
]
```

示例（三 AZ 部署，主可用区 ap-guangzhou-6，备可用区1 ap-guangzhou-7，备可用区2 ap-guangzhou-4）：
```json
[
  {"SecondaryZone": "ap-guangzhou-7"},
  {"SecondaryZone": "ap-guangzhou-4"}
]
```
### 规格名称编码规则

规格名称通常遵循格式：`{Type}_{CPU}_{Mem}_{DiskType}`

| 后缀 | 含义 | 对应 DiskType |
|------|------|---------------|
| `_P` | Premium | `CLOUD_PREMIUM`（高性能云硬盘） |
| `_H` | HSSD | `CLOUD_HSSD`（增强型SSD云硬盘） |

**HIGHIO 型（H_ 开头）**：
- 数据盘固定为 `LOCAL_BASIC`（本地盘）
- 磁盘大小和数量固定在命名中，如 `H_32_128_2_7140` = 32C128G + 2 块 7140GB 本地盘
- 命名格式：`H_{CPU}_{MEM}` 或 `H_{CPU}_{MEM}_{DiskCount}_{DiskSize}`

> ⚠️ **强制约束**：规格后缀与 DiskType 必须匹配。选了 `S_16_64_P` 就必须配 `CLOUD_PREMIUM`，选了 `S_32_128_H` 就必须配 `CLOUD_HSSD`。不允许规格后缀与 DiskType 不匹配。

示例：
- `S_16_64_H` → 标准型 16C64G，磁盘必须为 `CLOUD_HSSD`
- `S_32_128_P` → 标准型 32C128G，磁盘必须为 `CLOUD_PREMIUM`
- `H_32_128_2_7140` → 高IO型 32C128G，本地盘 2×7140GB（`LOCAL_BASIC`）

---

## §3 CalculatePrice 询价接口

### 接口说明

`BillingCalculatePrice` 封装了 billing 的 `CalculatePrice` 接口（域名 billing.tencentcloudapi.com），用于获取真实价格。

### 参数构造

| 参数 | 来源 | 说明 |
|------|------|------|
| GoodsCategoryId | DescribeGoodsDetail 返回 | 商品类目 ID，如 101444 |
| GoodsDetail | DescribeGoodsDetail 返回 | 商品详情 JSON 字符串 |
| GoodsNum | DescribeGoodsDetail 返回 | 商品数量，通常为 1 |
| PayMode | 用户选择 | `prePay`（包年包月）或 `postPay`（按量计费） |
| Region | 用户指定 | 地域 ap code，如 ap-guangzhou |
| Zone | 用户指定 | 可用区 ap code，如 ap-guangzhou-6 |

### 返回结果解读

> 💰 **价格单位（重要）**：以下所有金额字段（`Price` / `TotalCost` / `RealTotalCost`）单位均为 **分**，使用前必须除以 100 转换为**元**。

| 字段 | 说明 |
|------|------|
| Price | 单价（单位：分） |
| TotalCost | 原价总费用（单位：分） |
| RealTotalCost | 折后实付金额（单位：分） |
| Policy | 折扣率（100 = 无折扣，85 = 85折） |
| TimeSpan | 计费时长 |
| TimeUnit | 时长单位（m=月，h=小时） |
| GoodsNum | 商品数量 |
| ProductCode | 产品编码 |
| SubProductCode | 子产品编码 |
| Currency | 币种（CNY/USD） |

### 价格转换

```
元 = RealTotalCost / 100
月费用 = RealTotalCost / 100（包年包月时 TimeUnit=m，TimeSpan=月数）
小时费用 = RealTotalCost / 100（按量计费时 TimeUnit=h，TimeSpan=1）
预估月费 = 小时费用 × 720
```

### 年费用计算

询价接口默认返回 TimeSpan 对应时长的费用。计算年费用有两种方式：

1. **推荐方式**：以 `TimeSpan=12, TimeUnit=m` 重新调用询价接口，获取含年付折扣的真实年费用
2. **快速估算**：`年费用 = 月费用 × 12 × 年付折扣系数`，参考折扣：1 年约 83 折（×0.83）、2 年约 7 折（×0.7）、3 年约 5 折（×0.5）

### 组件费用拆分

> ⚠️ `BillingCalculatePrice` 返回的是 `RealTotalCost` 总价，**不包含组件级别的费用拆分**。报告中的组件费用明细（计算节点/Common 节点/存储）为基于经验单价的估算值，仅供参考。如需精确组件费用，可分别对 DATA 节点和 COMMON 节点单独构造询价请求。

### 折扣解读

- `Policy = 100`：无折扣（原价）
- `Policy = 85`：85折
- `Policy = 70`：7折
- 实际折扣 = Policy / 100

> ⚠️ **重要提示**：不同账户可能享有不同的折扣策略（如合同折扣、大客户折扣、活动折扣等），实测部分账户折扣可达 ~60%（即 Policy ≈ 40）。因此：
> - 报价时必须以 `RealTotalCost`（折后实付）为准，而非 `TotalCost`（原价）
> - 在报告中提示用户：「实际折扣因账户而异，最终价格以下单页面为准」
> - 不同方案的折扣率可能相同（同一账户），对比时关注绝对金额差异即可

---

## §4 计费模式说明

### 包年包月（PREPAID）

- 预付费，按月/年购买
- 通常享有折扣：1 年约 83 折，2 年约 7 折，3 年约 5 折
- 适合长期稳定运行的生产集群
- 支持自动续费（RenewFlag = 1）

### 按量计费（POSTPAID_BY_HOUR）

- 后付费，按小时扣费
- 无折扣，单价较高
- 适合测试环境、短期项目、弹性需求
- 可随时销毁，不产生后续费用

### 选择建议

| 使用时长 | 推荐计费方式 | 理由 |
|---------|-------------|------|
| < 1 个月 | 按量计费 | 灵活，随用随停 |
| 1-3 个月 | 按量计费或月付 | 视确定性而定 |
| 3-12 个月 | 包年包月（月付/年付） | 年付更优惠 |
| > 1 年 | 包年包月（年付） | 折扣最大 |

---

## §5 费用估算经验值

> 以下为参考估算值，实际价格以询价接口返回为准。

### 计算节点参考价格（包年包月/月）

| 规格 | 参考月费（元） | 说明 |
|------|--------------|------|
| 4C16G | 500-800 | 不含磁盘 |
| 8C32G | 1000-1500 | 不含磁盘 |
| 16C64G | 2000-3000 | 不含磁盘 |
| 32C128G | 4000-6000 | 不含磁盘 |
| 64C256G | 8000-12000 | 不含磁盘 |

### 存储参考价格（包年包月/月/GB）

| 磁盘类型 | 参考单价（元/GB/月） |
|---------|-------------------|
| 高性能云硬盘 | 0.35 |
| SSD 云硬盘 | 1.0 |
| 增强型 SSD | 1.5 |

### 快速估算公式

```
月费用 ≈ (计算节点单价 × 节点数) + (Common 节点单价 × 3) + (磁盘单价 × 总磁盘容量)

示例：16C64G × 4 节点 + 4C16G × 3 Common + 增强型 SSD 2TB/节点
≈ (2500 × 4) + (600 × 3) + (1.5 × 2000 × 4)
≈ 10000 + 1800 + 12000
≈ 23800 元/月
```

---

## §6 成本优化建议

### 降低成本的策略

| 策略 | 节省比例 | 适用场景 | 注意事项 |
|------|---------|---------|---------|
| 包年包月年付 | 15-50% | 长期运行集群 | 需提前规划 |
| 高性能云硬盘替代 SSD | 30-60% 存储费 | 冷数据/日志/对延迟不敏感 | 性能下降 |
| COS 冷热分层 | 50-70% 冷数据存储费 | 历史数据量大 | 查询冷数据延迟增加 |
| 减少副本数 | 50% 存储费 | 非核心/可重建数据 | 可用性降低 |
| 选择性价比地域 | 5-15% | 对地域无强要求 | 网络延迟可能增加 |

### COS 冷热分层说明

- 适合场景：数据量大（>10TB）、历史数据查询频率低
- 原理：将冷数据（超过 N 天未访问）自动迁移到 COS 对象存储
- 成本：COS 存储费约 0.1 元/GB/月，远低于云硬盘
- 限制：查询冷数据时需要从 COS 拉取，延迟增加数秒

### 弹性伸缩建议

- 业务有明显波峰波谷 → 考虑云原生弹性集群（按需扩缩计算节点）
- 日间高峰/夜间低谷 → 基础节点包年包月 + 弹性节点按量计费
