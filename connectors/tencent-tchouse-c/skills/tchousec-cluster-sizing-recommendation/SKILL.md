---
name: 腾讯云TCHouse-C 集群选型与架构推荐
description: >
  TCHouse-C（ClickHouse）集群选型与架构推荐 Skill。面向首次开通或新增 ClickHouse 集群的用户，AI 根据用户提供的业务画像（数据规模、增长速率、查询模式、并发要求、延迟要求、预算约束），推荐适合的集群规格（节点数/CPU/内存/存储类型/副本数）、可用区与网络方案，并输出多方案费用对比。
  触发词：集群选型、集群推荐、新建集群、新购集群、购买集群、创建集群、集群规格、节点选型、机型推荐、架构推荐、容量规划、sizing、cluster recommendation、cluster sizing、TCHouse-C 新购、cdwch 新建、ClickHouse 选型、选什么规格、买多大的集群、集群配置推荐、存储选型、磁盘选型、高可用方案、跨AZ部署、费用估算、成本对比、包年包月还是按量。
  本 Skill 包含 3 个子能力：①业务画像采集与需求分析 ②集群规格与架构方案推荐 ③多方案费用对比与最终建议。
  何时不触发：已有集群的慢查询诊断、SQL 优化、集群扩缩容操作、集群健康诊断与故障排查、NL2SQL、权限管理、数据导入导出等非新购选型相关问题不走本 Skill。
allowed-tools:
  - TCHouseCDescribeSpec
  - TCHouseCDescribeRegionZone
  - TCHouseCDescribeGoodsDetail
  - BillingCalculatePrice
  - ask_user # WorkBuddy 中为 AskUserQuestion
---

# 集群选型与架构推荐

## 概述

本 Skill 提供 TCHouse-C（ClickHouse）集群的选型与架构推荐能力，包含三个子能力：

1. **业务画像采集与需求分析**：通过结构化问题收集用户的数据规模、查询模式、并发/延迟要求和预算约束
2. **集群规格与架构方案推荐**：基于业务画像和可用规格，推荐节点类型/数量/存储/高可用/网络方案
3. **多方案费用对比与最终建议**：输出 2-3 个方案的配置详情与费用对比，帮助用户决策

## 依赖与运行环境

本 Skill 的所有调用通过 MCP Tool 完成（云 API 类工具由平台封装为 MCP Tool，Agent 直接调用工具名即可）。

**依赖工具清单**：

| #   | Tool 名称                   | 能力定位                                         | 参考文档                                                        |
| --- | --------------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| 1   | TCHouseCDescribeSpec        | 获取集群可用规格                                 | [参考](references/api-reference.md#TCHouseCDescribeSpec)        |
| 2   | TCHouseCDescribeRegionZone  | 获取地域/可用区                                  | [参考](references/api-reference.md#TCHouseCDescribeRegionZone)  |
| 3   | TCHouseCDescribeGoodsDetail | 获取询价所需的商品配置信息                       | [参考](references/api-reference.md#TCHouseCDescribeGoodsDetail) |
| 4   | BillingCalculatePrice       | 调用 billing 询价获取真实价格                    | [参考](references/cost-estimation-guide.md)                     |
| 5   | ask_user                    | 向用户询问确认（WorkBuddy 中为 AskUserQuestion） | —                                                               |

## 凭证 / 环境变量

- `region_id`：从会话 context 的 X-Context header 自动注入，或由用户指定（可能是 `RegionId` 数字、`Region` 字符串或中文地域名）
- 若以上参数缺失，通过 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）询问用户

> ⚠️ **地域参数强制规则**：本 Skill 依赖的全部工具（`TCHouseCDescribeSpec` / `TCHouseCDescribeRegionZone` / `TCHouseCDescribeGoodsDetail` / `BillingCalculatePrice`）都只接受 **`Region` 字符串**（如 `ap-guangzhou`）。**任何工具调用前**都必须先按 [地域映射表](references/region-mapping.md) 将上下文中的地域信息（无论是中文名、英文串还是 `RegionId` 数字）统一转为 `Region` 字符串后再传入，禁止凭记忆填写。详见 [工具传参形式速查](references/region-mapping.md#工具传参形式速查)。
>
> 注意：`TCHouseCDescribeRegionZone` 可用来校验地域/可用区在 TCHouse-C 产品下是否可用，**不用于反推中文名 → `Region` 字符串**（后者必须直接查本地映射表，不得先盲调 API）。

> 💡 **多平台兼容说明**：本文档中所有提到的 `ask_user` 工具，在 WorkBuddy 平台中对应为 `AskUserQuestion`。后文不再重复标注。

## 核心工作流

### 步骤 0：业务画像采集

**目标**：收集足够信息以做出合理推荐。以下为必须了解的维度：

| 维度       | 关键问题                                    | 默认值（用户未提供时） |
| ---------- | ------------------------------------------- | ---------------------- |
| 数据规模   | 当前总数据量（TB）？日增量？                | 需询问，不可假设       |
| 数据保留   | 数据保留周期（月/年）？                     | 需询问                 |
| 查询模式   | 以 OLAP 聚合为主还是点查为主？是否有 JOIN？ | 默认 OLAP 聚合         |
| 并发要求   | 峰值并发查询数？                            | 默认 10-20 QPS         |
| 延迟要求   | 查询响应时间要求（秒级/亚秒级）？           | 默认秒级               |
| 高可用要求 | 是否需要高可用/跨 AZ 部署？                 | 默认需要高可用         |
| 计费偏好   | 包年包月还是按量计费？                      | 需询问                 |
| 预算约束   | 月预算上限？                                | 可选，无则不限         |
| 地域偏好   | 期望部署地域？                              | 需询问                 |

**判断逻辑**：

- ✅ 用户一次性提供了大部分信息 → 补充确认后进入步骤 1
- ❌ 信息严重不足（缺少数据规模 + 地域）→ 调用 `ask_user` 结构化询问
- ⚠️ 部分信息缺失 → 对缺失维度使用合理默认值，并在推荐中注明假设

**询问策略**：一次性询问所有缺失信息，避免多轮来回。推荐使用如下模板：

```
为了给您推荐合适的集群配置，请提供以下信息：
1. 数据规模：当前总数据量约多少 TB？每天新增多少 GB？
2. 数据保留周期：数据需要保留多久？
3. 查询模式：主要是报表/聚合分析，还是实时点查？
4. 并发需求：峰值大约多少个并发查询？
5. 延迟要求：查询响应需要秒级还是亚秒级？
6. 部署地域：期望部署在哪个地域（如广州、上海、北京）？
7. 计费方式：倾向包年包月还是按量计费？
8. 预算：是否有月预算上限？（可选）
```

### 步骤 1：获取可用规格

调用 `TCHouseCDescribeRegionZone` 验证用户指定的地域/可用区是否可用，然后调用 `TCHouseCDescribeSpec` 获取目标地域/可用区的可用规格列表。

#### 步骤 1a：地域参数标准化与可用性验证

**1a-1：地域参数标准化**（调用 API 前必需执行）

无论步骤 0 中收集到的地域信息是中文名（如"广州"）、`Region` 字符串（如 `ap-guangzhou`）还是 `RegionId` 数字（如 `1`），都必须先按 [地域映射表](references/region-mapping.md) 统一转为 **`Region` 字符串**（例如 `ap-guangzhou`），再传入后续工具。若匹配不到或大区模糊（如"华南地区"），先 `ask_user` 确认具体地域。

**1a-2：调用 `TCHouseCDescribeRegionZone` 确认地域/可用区在 TCHouse-C 产品下可用**

**判断逻辑**：

- ✅ 地域/可用区存在且 Available=true → 继续步骤 1b
- ❌ 地域不存在 → 告知用户该地域不支持，建议更换
- ❌ 可用区不存在或不可用 → 推荐该地域下其他可用的可用区
- ⚠️ 用户未指定可用区 → 从返回列表中选取默认可用区（通常取编号最大的），默认地域为广州（`ap-guangzhou`）

#### 步骤 1b：获取可用规格列表

调用 `TCHouseCDescribeSpec` 获取目标地域/可用区的可用规格列表。

**参数**：

- `Region`：用户指定的地域
- `Zone`：用户指定的可用区（未指定则使用该地域默认可用区）
- `PayMode`：`PREPAID`（包年包月）或 `POSTPAID_BY_HOUR`（按量计费）
- `CaseType`：`1`（购买页规格）

**判断逻辑**：

- ✅ 成功返回 DataSpec + CommonSpec → 进入步骤 2
- ❌ 返回为空 → 该可用区暂无可用规格，建议用户更换可用区
- ❌ `InvalidParameter` → 检查 Region/Zone 格式，修正后重试
- ❌ `InternalError` → 等 3 秒重试，最多 3 次；仍失败则基于经验规格给出建议并注明"未能实时获取规格，建议在控制台确认"

**记录信息**：可用的数据节点规格列表（CPU/内存/磁盘类型/磁盘范围）、Common 节点规格列表。

### 步骤 2：规格匹配与方案生成

基于业务画像和可用规格，按 [选型规则](references/spec-recommendation-rules.md) 生成 2-3 个推荐方案。

**方案生成原则**：

| 方案类型           | 定位       | 特点                            |
| ------------------ | ---------- | ------------------------------- |
| 方案 A（推荐）     | 性价比最优 | 满足需求的最小配置 + 适当冗余   |
| 方案 B（性能优先） | 高性能     | 更高规格/更多节点，留足扩展空间 |
| 方案 C（经济型）   | 成本最低   | 满足基本需求，冗余较少          |

**每个方案必须包含**：

1. **计算节点**：机型（CPU/内存）、节点数量、磁盘类型、单盘容量、云盘数量
2. **Common 节点**：机型、节点数量（高可用时 3 节点）、磁盘类型（CLOUD_PREMIUM/CLOUD_HSSD）、磁盘大小、云盘数量
3. **高可用配置**：是否开启 HA、是否跨 AZ
4. **网络方案**：VPC/子网建议
5. **存储方案**：磁盘类型选择理由（SSD vs 高性能云硬盘 vs 增强型 SSD）
6. **内核版本**：推荐版本及理由

**选型核心逻辑**（详见 [references/spec-recommendation-rules.md](references/spec-recommendation-rules.md#选型决策树)）：

- 数据量 < 1TB → 4C16G 起步，2-3 节点
- 数据量 1-10TB → 16C64G，3-5 节点
- 数据量 10-50TB → 32C128G 或 64C256G，5-10 节点
- 数据量 > 50TB → 大数据型机型（BIGDATA），10+ 节点
- 高并发（>50 QPS）→ 增加节点数而非单节点规格
- 亚秒级延迟 → 优先 SSD/增强型 SSD + 更多内存

### 步骤 2.5：存储容量校验（ASSERT）

**目标**：在输出推荐方案前，强制校验每个方案的存储容量是否满足需求，不满足则自动上调磁盘大小。

**校验公式**：

```
集群可用存储 = 节点数 × 盘数 × 单盘大小 × 0.9（格式化损耗）
需求存储 = 数据量 × 副本数 × 1.3（冗余系数）

ASSERT: 集群可用存储 ≥ 需求存储
```

**其中**：

- `数据量`：用户当前总数据量经 ClickHouse 压缩后的实际存储量（= 原始数据量 × 压缩比），若用户提供的是日增量 + 保留天数，则 `数据量 = 日增量 × 保留天数 × 压缩比`。压缩比根据业务场景选择：OLAP 聚合分析 0.25~0.35、实时写入/日志 0.35~0.50、混合负载 0.30~0.45、时序数据 0.15~0.25，用户未明确时默认 0.35。详见 [压缩比参考表](references/spec-recommendation-rules.md#压缩比参考值按业务场景)
- `副本数`：高可用（HA）模式为 2，非高可用为 1
- `节点数`：数据节点数量
- `盘数`：每节点的云盘数量（DiskCount）。**标准版（STANDARD 规格）默认每节点 1 块数据盘**（`TCHouseCDescribeSpec` 返回的 `DataSpec[].DataDisk.DiskCount` 表示的是「最大云盘数量」上限，实际下单/询价时若未显式指定，默认取 1 块）。数据量较大时可增加到 2-10 块以并行 IO；HIGHIO 型（本地盘）盘数固定在规格名中，不可调整
- `单盘大小`：单块云盘容量（GB）
- `0.9`：文件系统格式化损耗系数
- `1.3`：冗余系数（预留 30% 空间用于 merge/临时文件/增长缓冲）

**校验流程**：

```
对每个方案执行：
1. 计算 集群可用存储 = 节点数 × 盘数 × 单盘大小(GB) × 0.9
2. 计算 需求存储 = 数据量(GB) × 副本数 × 1.3
3. IF 集群可用存储 ≥ 需求存储:
     → 校验通过，进入步骤 3
4. ELSE:
     → 自动上调单盘大小：
        新单盘大小 = ceil(需求存储 / (节点数 × 盘数 × 0.9))
        将新单盘大小向上取整到最近的合法磁盘规格（如 100GB 的整数倍）
     → 若上调后超出该规格最大单盘容量（MaxDiskSize）：
        尝试增加云盘数量（DiskCount），重新计算
     → 若云盘数量也达到上限（MaxDiskCount）：
        增加节点数（向上取偶数，HA 场景），重新计算
     → 更新方案配置，重新执行校验直到通过
```

**注意事项**：

- 每个方案独立校验，校验不通过时只调整该方案
- 调整后需在报告中注明：「已自动上调磁盘大小以满足存储需求」
- 校验计算过程需在报告的「选型理由」中展示，便于用户理解

### 步骤 3：费用估算

费用估算分为两步：先获取商品配置信息，再调用 billing 询价接口获取真实价格。

> 💰 **价格单位强提示**：**`BillingCalculatePrice` 返回的所有金额字段（`Price` / `TotalCost` / `RealTotalCost`）单位均为「分」，展示给用户前必须除以 100 转换为「元」**。忘记换算会导致报价虚高 100 倍，属于最常见的低级错误，必须在每次读取价格时立即完成换算。

> ⚠️ **跨可用区询价的白名单限制**：`DescribeGoodsDetail` 的 `IsSecondaryZone=true`（多可用区部署询价）在部分账户下会返回 `InvalidParameter`，原因是跨 AZ 询价能力受后端白名单（`SecondaryZoneWhitelist`）管控。**推荐做法**：跨 AZ 部署与单 AZ 部署的计费单价一致（差异仅在架构层面），因此若跨 AZ 询价报错，直接**改用单可用区参数（`IsSecondaryZone=false` 且不传 `SecondaryZoneInfo`）获取单价**即可，无需为白名单问题阻塞流程；在报告中注明「跨 AZ 部署不影响计费单价，仅为架构部署差异」。

#### 步骤 3.1：获取商品配置信息

调用 `TCHouseCDescribeGoodsDetail` 获取询价所需的商品配置信息（GoodsCategoryId、GoodsDetail 等）。

**参数构造**：根据方案配置组装参数，核心字段如下：

- `Region`：地域（如 ap-guangzhou）
- `Case`：固定传 `CREATE_QUERYPRICE`（创建询价场景）
- `Zone`：主可用区（如 ap-guangzhou-6）
- `HaFlag`：是否高可用（true/false）
- `ProductVersion`：内核版本号（如 26.3.3.0）
- `Resources`：JSON 数组，包含 DATA 节点和 COMMON 节点的规格、数量、磁盘类型/容量/数量（DiskCount）
- `ChargeProperties`：计费信息（ChargeType + TimeSpan + TimeUnit + RenewFlag）
- `IsSecondaryZone`：是否跨可用区（多 AZ 部署时设为 true）。⚠️ **受白名单管控**：非白名单账户传 `true` 会返回 `InvalidParameter`，此时回退到 `false` 使用单可用区参数询价即可（单价一致，不影响费用估算准确性）
- `SecondaryZoneInfo`：跨 AZ 时必填，JSON 数组仅包含备可用区信息（主可用区通过 Zone 参数指定，与 HAZk/ClickhouseKeeper 同层）。[0]=备可用区1，[1]=备可用区2（可选，三 AZ 场景）。每个元素只需传入 `SecondaryZone` 字段
- `HAZk`：ZK 高可用，仅单副本（HaFlag=false）时有效，true=开启 ZK 高可用并部署 3 个 Common 节点。双副本时始终为 false
- `ClickhouseKeeper`：是否使用 ClickHouseKeeper 替代 ZooKeeper，仅在需要部署 Common 节点时有效（双副本+部署Common 或 单副本+HAZk=true）
- `NoKeeper`：双副本下不部署独立 Keeper 节点（白名单功能），仅 HaFlag=true 时有效，true=不部署 Common 节点

> **HAZk/ClickhouseKeeper/NoKeeper 组合规则**：双副本时 HAZk 始终为 false；NoKeeper=true 仅白名单用户可用；当 NoKeeper=true 时 Resources 中不应包含 COMMON 节点。详见 [api-reference.md](references/api-reference.md#hazk--clickhousekeeper--nokeeper-组合语义)

> **注意**：Resources 中每个节点的 DiskSpec 必须包含 `DiskCount`（云盘数量）和 `DiskSize`（单盘容量 GB），总存储 = DiskCount × DiskSize。

**返回信息**：`GoodsCategoryId`（商品类目 ID）、`GoodsDetail`（商品详情 JSON）、`GoodsNum`（商品数量）、`PayMode`（付费模式数值）、`RegionId`（地域数字 ID）等。

#### 步骤 3.2：调用 billing 询价

将步骤 3.1 的返回结果传入 `BillingCalculatePrice` 进行真实询价。

**参数构造**：

- `GoodsCategoryId`：来自步骤 3.1 返回
- `GoodsDetail`：来自步骤 3.1 返回的 GoodsDetail（JSON 字符串）
- `GoodsNum`：来自步骤 3.1 返回（通常为 1）
- `PayMode`：`prePay`（包年包月）或 `postPay`（按量计费）
- `Region`：地域 ap code（如 ap-guangzhou）
- `Zone`：可用区 ap code（如 ap-guangzhou-6）

**返回信息**：`Price`（原价）、`TotalCost`（总费用）、`RealTotalCost`（折后实付）、`Policy`（折扣率）、`TimeSpan`（时长）、`TimeUnit`（时长单位）等。

> 💰 **价格单位（再次强调）**：**`Price` / `TotalCost` / `RealTotalCost` 单位均为「分」，输出报告前务必除以 100 转换为「元」**。

**判断逻辑**：

- ✅ 成功返回价格 → 进入步骤 4
- ❌ 询价失败 → 最多重试 3 次（每次间隔 3 秒）；仍失败则该方案不提供具体价格，在报告中注明「询价失败，无法获取该方案的真实价格，建议前往控制台手动询价确认」
- ❌ 部分方案询价失败 → 对失败方案标注「询价失败」，其余方案正常展示价格

> **MCP 调用失败兜底策略**：任何 MCP 工具调用失败时，最多重试 3 次。超过 3 次仍失败的，对应方案不提供具体价格数字（不做估算），明确告知用户询价失败并建议前往 [TCHouse-C 控制台](https://console.cloud.tencent.com/cdwch) 手动确认价格。

**费用展示**：

- 包年包月：月费用 + 年费用（含折扣）
- 按量计费：小时费用 + 预估月费用（按 720 小时/月）
- 对比维度：总费用、单 TB 存储成本、单 QPS 成本

> ⚠️ **关于折扣**：询价接口返回的 `RealTotalCost` 为折后实付金额，不同账户可能享有不同折扣（如合同折扣、活动折扣等，实测可达 ~60% 折扣）。报价时应以折后价（`RealTotalCost`）为准展示，并提示用户「实际折扣因账户而异，最终价格以下单页面为准」。

### 步骤 4：生成推荐报告

按 [输出报告格式](references/spec-recommendation-rules.md#输出报告格式) 生成选型推荐报告。

**报告必须包含**：

1. 业务画像摘要（确认理解正确）
2. 推荐方案对比表（配置 + 费用）
3. 每个方案的详细配置说明
4. 最终推荐及理由
5. 后续操作指引（如何在控制台创建 / 注意事项）

**报告末尾必须给出购买页跳转提示（严格规则）**：

- ✅ **唯一允许的购买页链接格式**：`https://buy.cloud.tencent.com/tchousec?region={Region}`
  - `{Region}` 必须替换为本次推荐使用的 Region 字符串（如 `ap-guangzhou`、`ap-shanghai`、`ap-beijing`），**严禁省略 `?region=` 参数**。
  - 示例：广州 → `https://buy.cloud.tencent.com/tchousec?region=ap-guangzhou`
- ❌ **禁止使用以下任何形式**（这些是常见的错误猜测，模型必须避免）：
  - `https://console.cloud.tencent.com/cdwch/createStandard?rid=xxx`
  - `https://console.cloud.tencent.com/cdwch/create` 或任何 `cdwch/*` 的创建/新建路径
  - 不带 `?region=` 参数的 `https://buy.cloud.tencent.com/tchousec`
  - 任何使用 `rid=` 数字 ID 的形式
- 链接以 Markdown 链接形式呈现，例如：`[前往 TCHouse-C 购买页创建集群](https://buy.cloud.tencent.com/tchousec?region=ap-guangzhou)`，方便用户点击后在浏览器中打开。

### 步骤 5：用户确认与调整

- 用户对方案有疑问 → 解释选型理由
- 用户要求调整 → 基于新约束重新生成方案（回到步骤 2）
- 用户确认方案 → 提供中文友好的部署参数参考（地域/可用区/计费模式/磁盘类型/规格等均使用「中文名称（英文代码）」格式展示）

## 频率控制

| 限制                        | 阈值         | 说明                  |
| --------------------------- | ------------ | --------------------- |
| 工具总调用频率              | ≤ 15 次/分钟 | 避免触发平台限流      |
| TCHouseCDescribeSpec 调用   | ≤ 3 次/轮    | 通常只需 1 次         |
| TCHouseCDescribeGoodsDetail | ≤ 5 次/轮    | 每个方案获取配置 1 次 |
| BillingCalculatePrice       | ≤ 5 次/轮    | 每个方案询价 1 次     |

**超限处理**：连续收到 `RequestLimitExceeded` → 等 5 秒重试，连续 3 次仍失败 → 基于经验估算费用，告知用户被限流。

## 错误码与处理策略

| 错误码/场景            | Agent 行为                                                                                                                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AuthFailure.*`        | 报告鉴权失败，提示用户检查访问权限                                                                                                                                                                    |
| `InvalidParameter.*`   | 检查 Region/Zone/PayMode 格式，尝试修正后重试 1 次；无法修正 → 报告问题                                                                                                                               |
| `ResourceInsufficient` | 该规格在目标可用区售罄，自动推荐替代规格或建议更换可用区                                                                                                                                              |
| `InternalError`        | 等 3 秒重试，最多 3 次；仍失败 → 基于经验给出建议并注明未实时验证                                                                                                                                     |
| `RequestLimitExceeded` | 等 5 秒重试；连续 3 次 → 降低频率，基于经验估算                                                                                                                                                       |
| `UnsupportedRegion`    | 该地域未开通 TCHouseC 产品。**不重试、不自动切换地域**，必须调用 `ask_user` 让用户确认地域。详见 [error-handling.md §1](references/error-handling.md#1-unsupportedregion该接口不支持此地域访问) |
| 内核版本不匹配         | 使用经验沉淀库中的「已知可用内核版本」重试，优先选择「推荐」版本                                                                                                                                      |
| 兜底（未列出错误码）   | 报告完整错误信息 + RequestId                                                                                                                                                                          |

## 安全规则

1. **本 Skill 为纯只读咨询**：所有操作均为查询类（DescribeSpec/询价），不涉及实际创建资源
2. **不自动创建集群**：即使用户说"帮我创建"，也只输出配置方案和参数，不执行 CreateInstanceNew
3. **费用信息仅供参考**：明确标注"实际费用以下单时为准"
4. **凭据安全**：不在输出中展示任何凭据信息
5. **关键参数不假设**：数据规模、地域等核心参数缺失时必须询问，不自行假设

## 经验沉淀库

| 经验                                   | 置信度 | 说明                                                 |
| -------------------------------------- | ------ | ---------------------------------------------------- |
| 16C64G 是最通用的起步规格              | ⭐⭐⭐ | 适合大多数中等规模（1-10TB）的 OLAP 场景             |
| 节点数建议为偶数（HA 场景）            | ⭐⭐⭐ | 高可用模式下数据节点需成对部署（2 副本）             |
| 增强型 SSD 适合低延迟场景              | ⭐⭐⭐ | IOPS 和吞吐量显著优于高性能云硬盘，适合亚秒级查询    |
| 磁盘容量建议预留 30% 冗余              | ⭐⭐   | 考虑数据增长 + 合并操作临时空间 + 系统开销           |
| 大数据型机型适合冷数据存储             | ⭐⭐   | BIGDATA 机型本地盘容量大、单 TB 成本低，适合历史数据 |
| 跨 AZ 部署增加约 10-15% 延迟           | ⭐⭐   | 跨可用区网络延迟，对延迟敏感场景需权衡               |
| Common 节点 3 节点是 ZK 高可用最低要求 | ⭐⭐⭐ | ZooKeeper/ClickHouseKeeper 需要奇数节点保证选举      |
| 按量计费适合测试/短期项目              | ⭐⭐   | 长期运行（>3 个月）包年包月更划算（通常 6-7 折）     |

## 已知可用内核版本

> 更新时间：2026-06-13

| 版本号    | 状态      | 说明                         |
| --------- | --------- | ---------------------------- |
| 26.3.3.0  | ✅ 推荐   | 当前最新稳定版，支持全部功能 |
| 23.8.12.0 | ✅ 可用   | 较旧稳定版，兼容性好         |
| 22.8.17.0 | ⚠️ 仅存量 | 不再推荐新建集群使用         |

**使用规则**：

- 新建集群默认使用「推荐」版本
- 若询价报错提示版本不可用，尝试下一个「可用」版本
- 用户有特定版本要求时优先满足用户需求
