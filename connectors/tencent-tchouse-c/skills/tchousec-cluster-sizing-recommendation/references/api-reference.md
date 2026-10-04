# 云 API 工具参考

> 本文件描述 tchousec-cluster-sizing-recommendation Skill 依赖的云 API 工具的输入输出参数。

---

## TCHouseCDescribeSpec

### 功能

获取目标地域/可用区的集群可用规格列表（数据节点规格 + Common/ZK 节点规格 + 云盘规格）。

### 输入参数

| 参数名称 | 必选 | 类型 | 说明 |
|---------|------|------|------|
| Region | 是 | String | 地域，如 `ap-guangzhou` |
| Zone | 是 | String | 可用区，如 `ap-guangzhou-6` |
| PayMode | 否 | String | 计费类型：`PREPAID`（包年包月）/ `POSTPAID_BY_HOUR`（按量计费） |
| IsElastic | 否 | Boolean | 是否弹性 CK，默认 false |
| CaseType | 否 | Integer | 是否购买页规格，传 `1` 表示购买页 |

### 输出参数

| 参数名称 | 类型 | 说明 |
|---------|------|------|
| CommonSpec | Array of ResourceSpec | ZooKeeper/Common 节点可用规格列表 |
| DataSpec | Array of ResourceSpec | 数据节点可用规格列表 |
| AttachCBSSpec | Array of DiskSpec | 可挂载的云盘规格列表 |
| RequestId | String | 请求唯一 ID |

### ResourceSpec 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| Name | String | 规格名称，如 `S_16_64_H` |
| Cpu | Integer | CPU 核数 |
| Mem | Integer | 内存 GB |
| DisplayName | String | 展示名称，如 `16C64G` |
| Type | String | 规格类型（STANDARD 等） |
| Available | Boolean | 是否可用 |
| MaxNodeSize | Integer | 最大节点数 |
| DataDisk | DiskSpec | 数据盘规格约束 |
| SystemDisk | DiskSpec | 系统盘规格约束 |

### DiskSpec 结构

| 字段 | 类型 | 说明 |
|------|------|------|
| DiskType | String | 磁盘类型：`CLOUD_PREMIUM`（高性能）/ `CLOUD_HSSD`（增强型 SSD）/ `CLOUD_SSD`（SSD） |
| DiskDesc | String | 磁盘类型描述 |
| DiskCount | Integer | 最大云盘数量 |
| MaxDiskSize | Integer | 最大单盘容量（GB） |
| MinDiskSize | Integer | 最小单盘容量（GB） |

### 示例输出

```json
{
  "Response": {
    "DataSpec": [
      {
        "Name": "S_16_64_H",
        "Cpu": 16,
        "Mem": 64,
        "DisplayName": "16C64G",
        "Type": "STANDARD",
        "Available": true,
        "MaxNodeSize": 50,
        "DataDisk": {
          "DiskType": "CLOUD_HSSD",
          "DiskDesc": "增强型SSD云硬盘",
          "DiskCount": 10,
          "MaxDiskSize": 320000,
          "MinDiskSize": 200
        }
      }
    ],
    "CommonSpec": [
      {
        "Name": "S_4_16_H",
        "Cpu": 4,
        "Mem": 16,
        "DisplayName": "4C16G",
        "Type": "STANDARD",
        "Available": true,
        "MaxNodeSize": 50,
        "DataDisk": {
          "DiskType": "CLOUD_HSSD",
          "DiskDesc": "增强型SSD云硬盘",
          "DiskCount": 1,
          "MaxDiskSize": 32000,
          "MinDiskSize": 100
        }
      }
    ],
    "AttachCBSSpec": [
      {
        "DiskType": "CLOUD_HSSD",
        "DiskDesc": "增强型SSD云硬盘",
        "DiskCount": 1,
        "MaxDiskSize": 32000,
        "MinDiskSize": 1000
      }
    ],
    "RequestId": "e378c73e-a52a-4897-9155-ba2aa797006d"
  }
}
```

---

## TCHouseCDescribeRegionZone

### 功能

获取 TCHouse-C 支持的地域和可用区列表，用于确认用户指定的地域/可用区是否可用。

### 输入参数

| 参数名称 | 必选 | 类型 | 说明 |
|---------|------|------|------|
| 无额外参数 | — | — | 该接口无需业务参数，自动返回所有可用地域和可用区 |

### 输出参数

返回各地域及其下属可用区的列表，包含：

| 字段 | 说明 |
|------|------|
| Region | 地域 ap code，如 `ap-guangzhou` |
| RegionName | 地域中文名，如 `广州` |
| Zone | 可用区 ap code，如 `ap-guangzhou-6` |
| ZoneName | 可用区中文名，如 `广州六区` |
| Available | 该可用区是否可用 |

### 常用地域参考

| 地域 | ap code | 常用可用区 |
|------|---------|-----------|
| 广州 | ap-guangzhou | ap-guangzhou-6, ap-guangzhou-7 |
| 上海 | ap-shanghai | ap-shanghai-4, ap-shanghai-5 |
| 北京 | ap-beijing | ap-beijing-6, ap-beijing-7 |
| 南京 | ap-nanjing | ap-nanjing-1, ap-nanjing-2 |
| 成都 | ap-chengdu | ap-chengdu-1, ap-chengdu-2 |
| 重庆 | ap-chongqing | ap-chongqing-1 |
| 中国香港 | ap-hongkong | ap-hongkong-2 |
| 新加坡 | ap-singapore | ap-singapore-3 |
| 硅谷 | na-siliconvalley | na-siliconvalley-2 |
| 法兰克福 | eu-frankfurt | eu-frankfurt-1 |

---

## TCHouseCDescribeGoodsDetail

### 功能

获取询价所需的商品配置信息（GoodsCategoryId、GoodsDetail 等）。本接口不返回价格，需将返回结果传入 `BillingCalculatePrice` 进行真实询价。

### 输入参数

| 参数名称 | 必选 | 类型 | 说明 |
|---------|------|------|------|
| Region | 是 | String | 地域，如 `ap-guangzhou` |
| Case | 是 | String | 操作类型：`CREATE_QUERYPRICE`（创建询价）/ `MODIFY_QUERYPRICE`（变配询价）/ `RENEW_QUERYPRICE`（续费询价） |
| Zone | 否 | String | 可用区，如 `ap-guangzhou-6`。CREATE 场景建议必填 |
| HaFlag | 否 | Boolean | 是否高可用，true 表示高可用集群 |
| InstanceId | 否 | String | 集群 ID，CREATE 时为空，MODIFY/RENEW 时必填 |
| Resources | 否 | String | 集群资源规格 JSON 字符串（ResourceNodeSpec 数组），详见下方结构说明 |
| ChargeProperties | 否 | String | 计费信息 JSON 字符串，详见下方结构说明 |
| ProductVersion | 否 | String | 内核版本号，如 `26.3.3.0`。CREATE 场景建议必填 |
| IsSecondaryZone | 否 | Boolean | 是否跨可用区部署（多 AZ），true 表示跨 AZ。⚠️ **白名单限制**：跨 AZ 询价受后端 `SecondaryZoneWhitelist` 控制，非白名单账户传 true 会返回 `InvalidParameter`。若遇到该错误，请回退到 false（单 AZ 询价）：跨 AZ 与单 AZ 的计费单价一致，仅架构部署形式不同，跨 AZ 不会引入额外费用 |
| SecondaryZoneInfo | 否 | String | 备可用区信息 JSON 数组字符串，IsSecondaryZone=true 时必填。注意：主可用区通过 Zone 参数指定（与 HAZk、ClickhouseKeeper 同层），不在此数组中。[0]=备可用区1，[1]=备可用区2（可选，三 AZ 场景）。每个元素只需传入 SecondaryZone 字段 |
| HAZk | 否 | Boolean | ZK 高可用，仅单副本（HaFlag=false）时有效。true=单副本下开启 ZK 高可用（部署 3 个 Common 节点）。双副本时始终为 false |
| ClickhouseKeeper | 否 | Boolean | 是否使用 ClickHouseKeeper 替代 ZooKeeper。仅在需要部署 Common 节点时有效（双副本+openKeeper 或 单副本+HAZk=true） |
| NoKeeper | 否 | Boolean | 双副本下是否不部署独立 Keeper 节点（白名单功能）。仅 HaFlag=true 时有效，true=不部署 Common 节点 |

### Resources 结构说明

```json
[
  {
    "Type": "DATA",          // 节点类型：DATA（数据节点）或 COMMON（协调节点）
    "SpecName": "S_16_64_H", // 规格名称，来自 TCHouseCDescribeSpec 返回
    "Count": 12,             // 节点数量（HA 模式下为偶数）
    "DiskSpec": {
      "DiskType": "CLOUD_HSSD",  // 磁盘类型
      "DiskSize": 200,           // 单盘容量(GB)
      "DiskCount": 10            // 每节点云盘数量
    },
    "Encrypt": 0             // 是否加密，0=否
  },
  {
    "Type": "COMMON",
    "SpecName": "S_4_16_H",
    "Count": 3,
    "DiskSpec": {
      "DiskType": "CLOUD_HSSD",
      "DiskSize": 100,
      "DiskCount": 1
    }
  }
]
```

### ChargeProperties 结构说明

```json
{
  "ChargeType": "PREPAID",   // PREPAID（包年包月）或 POSTPAID_BY_HOUR（按量计费）
  "TimeSpan": 2,             // 时长数值
  "TimeUnit": "m",           // 时长单位：m（月）或 h（小时）
  "RenewFlag": 0             // 自动续费：0=否，1=是
}
```

### SecondaryZoneInfo 结构说明

数组索引含义（主可用区的配置不在这一层，而是通过顶层 Zone 参数指定，和 HAZk、ClickhouseKeeper 同一层）：

| 索引 | 含义 | UI 标签 |
|------|------|--------|
| [0] | 备可用区1 | 备可用区1 |
| [1] | 备可用区2（可选，三 AZ 场景） | 备可用区2 |

每个元素只需传入 `SecondaryZone` 字段（备可用区 ap code），不再需要传入 `SecondarySubnet` 和 `SecondaryUserSubnetIPNum`。

```json
// 示例：主可用区为 ap-guangzhou-6（通过 Zone 参数指定），备可用区1为 ap-guangzhou-7
[
  {"SecondaryZone": "ap-guangzhou-7"}
]
```

```json
// 示例：三 AZ 部署，主可用区 ap-guangzhou-6，备可用区1 ap-guangzhou-7，备可用区2 ap-guangzhou-4
[
  {"SecondaryZone": "ap-guangzhou-7"},
  {"SecondaryZone": "ap-guangzhou-4"}
]
```

### ⚠️ 跨可用区询价的白名单限制

**背景**：`IsSecondaryZone=true` 的询价能力受后端 `SecondaryZoneWhitelist` 白名单控制，非白名单账户无论如何组合 `SecondaryZoneInfo` / `HAZk` / `ClickhouseKeeper` 等参数，都会得到 `InvalidParameter`。

**处理策略**：

1. **首次遇到 `InvalidParameter` 且确认参数无误时，直接回退到单可用区询价**：设 `IsSecondaryZone=false`、不传 `SecondaryZoneInfo`，其他参数（规格、磁盘、节点数、计费方式）保持不变。
2. **不需要让用户先去申请白名单**才能完成询价：跨 AZ 与单 AZ 部署的计费单价相同，仅为架构层面差异（主/备可用区分布），跨 AZ 本身不引入额外价格。
3. **在报告中明确提示**：跨 AZ 部署的计费单价 = 单 AZ 部署单价，跨 AZ 不会额外收费；仅在架构上为多可用区容灾。
4. 若用户确需获取真实的跨 AZ 询价（包含多 AZ 专属的高可用型号 sku），引导其前往 [TCHouse-C 控制台](https://console.cloud.tencent.com/cdwch) 或联系商务开白名单后重试。

### HAZk / ClickhouseKeeper / NoKeeper 组合语义

这三个布尔值分别控制不同维度：

| 字段 | 含义 | 赋值逻辑 |
|------|------|----------|
| `HAZk` | ZK 高可用（单副本模式下额外开启 ZK 高可用） | 仅在单副本（HaFlag=false）时可为 true |
| `ClickhouseKeeper` | 使用 ClickHouseKeeper 替代 ZooKeeper | 需要部署 Common 节点时才有意义 |
| `NoKeeper` | 高可用模式下不部署 Common 节点 | 仅在双副本（HaFlag=true）且为白名单用户时可为 true |

**组合真值表**：

| 场景 | HaFlag | HAZk | ClickhouseKeeper | NoKeeper | Resources 中 COMMON 节点 |
|------|--------|------|-----------------|----------|-------------------------|
| 单副本，无 ZK 高可用 | false | false | false | false | 不需要 |
| 单副本，ZK 高可用，用 ZooKeeper | false | true | false | false | 需要（3 节点） |
| 单副本，ZK 高可用，用 CKKeeper | false | true | true | false | 需要（3 节点） |
| 双副本，部署 Common，用 ZooKeeper | true | false | false | false | 需要（3 节点） |
| 双副本，部署 Common，用 CKKeeper | true | false | true | false | 需要（3 节点） |
| 双副本，不部署 Common（白名单） | true | false | false | true | 不需要 |

**关键约束**：
- 双副本（HaFlag=true）时，`HAZk` 始终为 `false`（双副本自带高可用）
- `NoKeeper=true` 仅白名单用户可用，且仅在双副本模式下有效
- `ClickhouseKeeper=true` 要求内核版本 ≥ 23.8
- 当 `NoKeeper=true` 时，Resources 中不应包含 Type=COMMON 的节点

**逻辑决策树**：

```
HaFlag (双副本/高可用)
├── true (双副本)
│   ├── 部署 Common 节点 → NoKeeper=false
│   │   ├── 用 ZooKeeper → ClickhouseKeeper=false
│   │   └── 用 ClickHouseKeeper → ClickhouseKeeper=true
│   └── 不部署 Common 节点（白名单）→ NoKeeper=true
└── false (单副本)
    ├── 开启 ZK 高可用 → HAZk=true，部署 Common 节点
    │   ├── 用 ZooKeeper → ClickhouseKeeper=false
    │   └── 用 ClickHouseKeeper → ClickhouseKeeper=true
    └── 不开启 ZK 高可用 → HAZk=false，无 Common 节点
```

### 完整请求示例（包年包月 + 广州 + 多可用区 + 双副本）

```
Tool: TCHouseCDescribeGoodsDetail
参数:
  Region: "ap-guangzhou"
  Case: "CREATE_QUERYPRICE"
  Zone: "ap-guangzhou-6"
  HaFlag: true
  ProductVersion: "26.3.3.0"
  IsSecondaryZone: true
  HAZk: false
  ClickhouseKeeper: false
  NoKeeper: false
  Resources: '[{"Type":"DATA","SpecName":"S_16_64_H","Count":12,"DiskSpec":{"DiskType":"CLOUD_HSSD","DiskSize":20,"DiskCount":10},"Encrypt":0},{"Type":"COMMON","SpecName":"S_4_16_H","Count":3,"DiskSpec":{"DiskType":"CLOUD_HSSD","DiskSize":100,"DiskCount":1}}]'
  ChargeProperties: '{"ChargeType":"PREPAID","TimeSpan":2,"TimeUnit":"m","RenewFlag":0}'
  SecondaryZoneInfo: '[{"SecondaryZone":"ap-guangzhou-7"}]'
```

### 输出参数

| 字段 | 类型 | 说明 |
|------|------|------|
| GoodsCategoryId | Integer | 商品类目 ID（传给 BillingCalculatePrice） |
| GoodsDetail | String | 商品详情 JSON 字符串（传给 BillingCalculatePrice） |
| GoodsNum | Integer | 商品数量（通常为 1） |
| PayMode | Integer | 付费模式数值 |
| RegionId | Integer | 地域数字 ID |
| ZoneId | Integer | 可用区数字 ID |

---

## BillingCalculatePrice

### 功能

调用 billing 的 CalculatePrice 接口进行真实询价，返回含折扣的实际价格。

### 输入/输出参数

详见 [cost-estimation-guide.md §3](cost-estimation-guide.md#3-calculateprice-询价接口)。
