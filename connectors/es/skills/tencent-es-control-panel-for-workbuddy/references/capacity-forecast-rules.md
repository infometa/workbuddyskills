# 容量预测算法口径（Capacity Forecast Rules）

> 🔴 **本文档是容量预测全部阈值、算法、判读口径、推荐分流规则的唯一权威来源（SSOT）**，同时是 `scripts/forecast_calc.py` 的算法说明书。其他文档出现的阈值与本文档冲突时，以本文档为准。
>
> **执行分工**：
> | 环节 | 执行者 |
> |------|-------|
> | 取集群上下文 | `DescribeInstances`（MCP tool）|
> | 取监控时序 | `GetMonitorData`（MCP tool）|
> | **哨兵值剔除 / 线性回归 / P50-P95 / 外推天数 / 目标值计算** | **`scripts/forecast_calc.py`（本地纯计算，零云 API 调用）**|
> | 可行性校验 | `DescribeClusterDiskRange`（MCP tool）|
> | 组织报告、与用户确认、下发变更 | Agent |
>
> 🚫 **Agent 不得自行心算本文档中的任何公式**。线性回归需对上百数据点求 Σxy/Σx²，LLM 计算不可靠，且**算错不会报错**，只会给出看似合理的错误天数 —— 比脚本报错危险得多。本文档的公式**仅用于审阅脚本输出、排查异常**。
>
> 📌 **职责边界**：本流程只输出「何时需要扩」和「扩多少」，**不输出「为什么高」的根因分析**。根因分析（CPU 偶发打高原因、JVM fielddata 问题、慢查询排查等）由 `tencent-es-diagnose` skill 负责。

## 执行流程总览

```
Step 1  取集群基础信息（DescribeInstances，必须带 Fields）        ← MCP tool
Step 2  取监控时序（GetMonitorData × 6 个指标）                    ← MCP tool
Step 3  ┐
Step 4  ├ 交给 forecast_calc.py 一次完成：                         ← 本地脚本
Step 5  ┘ 哨兵值剔除 → 回归/分位数 → 外推天数 → 目标值与推荐分流
Step 6  可行性校验（DescribeClusterDiskRange）                     ← MCP tool
Step 7  Agent 组织报告；用户确认 → 走变更流程
```

---

## Step 1：取集群基础信息

```
DescribeInstances(
  Region=<地域>, InstanceIds=[<集群ID>],
  Fields=["InstanceId","InstanceName","Status","HealthStatus",
          "NodeInfoList","NodeType","NodeNum","DiskType","DiskSize","EsVersion"]
)
```

**必须提取的字段**：

| 字段 | 用途 |
|------|------|
| `DiskType` | **决定磁盘类推荐走向**（本地盘 vs 云盘），见 Step 5 |
| `NodeInfoList[].Type` / `.NodeNum` / `.DiskSize` | 算扩容目标值的基准 |
| `NodeType` | 当前规格，用于规格升配推荐（只读建议）|
| `Status` / `HealthStatus` | 若非 `Status=1`，预测仍可做，但要提示当前无法执行变更 |

### 磁盘类型判定

| `DiskType` | 类别 | 可否扩磁盘 |
|-----------|------|-----------|
| `LOCAL_SSD` | 本地 SSD 盘 | ❌ **不可**（容量与机型绑定）→ 只能加节点 |
| `CLOUD_PREMIUM` | 高性能云硬盘 | ✅ 可 |
| `CLOUD_SSD` | SSD 云硬盘 | ✅ 可 |
| `CLOUD_HSSD` | 增强型 SSD 云硬盘 | ✅ 可 |

---

## Step 2：取监控时序数据

对以下 **6 个指标**分别调用 `GetMonitorData`：

```
GetMonitorData(
  Region=<地域>, InstanceIds=[<集群ID>],
  MetricName=<指标名>,
  Period=3600,                             # 固定 1 小时粒度
  StartTime=<N 天前，ISO 8601 带时区>,
  EndTime=<当前时间，ISO 8601 带时区>
)
```

| 指标名 | 单位 | warn | critical | 标签 |
|-------|------|------|----------|------|
| `CpuUsageMax` | % | 70 | 85 | CPU 使用率（最大）|
| `DiskUsageMax` | % | 65 | 80 | 磁盘使用率（最大）|
| `JvmMemUsageMax` | % | 75 | 85 | JVM 内存使用率（最大）|
| `IndexSpeed` | 次/s | — | — | 写入 QPS |
| `SearchCompletedSpeed` | 次/s | — | — | 查询 QPS |
| `SearchLatencyAvg` | ms | 200 | 500 | 查询**平均**延迟 |

> ⚠️ 延迟指标口径固定为 `SearchLatencyAvg`（**平均值**），阈值 warn=200ms / critical=500ms。本 Skill **不使用 P99 口径**，避免与平均值阈值混用导致误判。

**分析周期（N 天）**：

| N | 适用 | 说明 |
|---|------|------|
| 7 | **默认推荐** | 数据点 ≈ 168 个，足够看趋势 |
| 14 | 更准确 | 用户要求更高准确度，或 7 天数据波动大时 |
| 30 | 长周期规划 | 数据点 ≈ 720 个，注意输出量 |

> ⚠️ `Period` 固定 `3600`。用 60 秒粒度取 7 天会产生上万数据点，撑爆上下文且对趋势判断无增益。
> 💡 `GetMonitorData` 支持 `InstanceIds` 批量。多集群预测时可一次传多个实例 ID，减少调用次数。

---

## Step 3：数据清洗（强制，不可跳过）

### 3.1 剔除哨兵值

云监控探针采集失败时返回 **`-2`（偶见 `-1`）** 而非 `null`。

```
清洗规则：丢弃所有 value < 0 的数据点（不参与任何计算）
```

> 🚨 **漏做此步的后果**：一串 `-2` 会把线性回归斜率拉成负数，得出「磁盘使用率正在下降，无需扩容」的**完全反向结论**，而真实情况可能是磁盘打满导致探针失联 —— 恰恰是最紧急的场景。

### 3.2 数据量校验

| 有效数据点数 | 处理 |
|------------|------|
| 0 | 该指标标记「无数据」，不做预测。若**全部指标都无数据** → 提示可能是探针失联，建议用 `tencent-es-diagnose` 排查 |
| 1 | 只报当前值，**不做趋势外推**（斜率无意义）|
| ≥ 2 | 正常判读 |
| 有效点数 < 总点数 × 50% | 在报告中标注「监控数据缺失较多（有效 X/Y 点），预测置信度低」|

---

## Step 4：逐指标判读（由 `forecast_calc.py` 执行）

调用方式：

```bash
echo '<GetMonitorData 返回，可为多指标 JSON 数组>' | $PYTHON_CMD scripts/forecast_calc.py \
  --node-num 3 --disk-size 300 --disk-type CLOUD_SSD \
  --node-type ES.S1.LARGE16 --node-role hotData
```

脚本对每个指标输出以下字段（以下小节说明其算法）：

| 输出字段 | 含义 |
|---------|------|
| `current` / `min` / `max` / `avg` | 水位统计 |
| `p50` / `p95` | 分布特征（判偶发 vs 持续）|
| `slope_per_day` / `trend` | 趋势 |
| `days_to_warn` / `days_to_critical` | 外推天数（含无法外推时的 `note`）|
| `monthly_growth_rate_pct` | 月增长率 |
| `valid_points` / `raw_points` / `sentinel_dropped` | 数据完整性 |
| `confidence` / `confidence_note` | 置信度 |
| `status` | `normal` / `warn` / `critical` |
| `pattern`（仅 CPU）| `spike` / `sustained` / `normal` |

各项算法如下：

### 4.1 当前水位

取**最后一个有效数据点**的值作为当前水位。

### 4.2 趋势外推（预测达到阈值天数）

脚本采用最小二乘线性回归：

```
线性回归：y = slope × x + intercept
  x = 时间戳（秒），y = 指标值
  slope     = (n×Σxy − Σx×Σy) / (n×Σx² − (Σx)²)
  intercept = (Σy − slope×Σx) / n

预测达到阈值 T 的天数：
  若 slope <= 0        → 「趋势平稳或下降，短期无需扩容」（不外推）
  否则 target_ts = (T − intercept) / slope
       days      = (target_ts − base_ts) / 86400
       days < 0  → 「已超过阈值」

⚠️ base_ts 恒取【最后一个有效数据点的时间】，**不得用 now()**。
   分析区间为历史区间时 now() 会落在数据范围外，导致外推失真。
```

> 💡 数据点较少（< 10）时线性回归不稳定，可用首尾两点斜率法作为近似，但**必须在报告中标注为粗略估算**。

### 4.3 分布特征（P50 / P95）

```
P50 = 有效值排序后的中位数
P95 = 有效值排序后第 95 百分位
```

### 4.4 月增长率（QPS 类指标用）

```
月增长率(%) = (末值 − 首值) / 首值 × 100 × (30 / N)
（首值为 0 时记为 0，避免除零）
```

---

## Step 5：推荐规则分流（由 `forecast_calc.py` 执行）

脚本按下表分流，输出 `recommendations[]`，其中 `tool` + `tool_args` 已是**可直接用于 MCP tool 的目标值**。

### 5.1 磁盘（`DiskUsageMax`）

| 当前水位 | 状态 | 动作 |
|---------|------|------|
| < 65% | ✅ 正常 | 无需处理。若 30 天内预计达 80% → 提示「建议提前规划」|
| 65% ~ 80% | 🟡 预警 | 按下方「磁盘扩容路径」给建议 |
| 80% ~ 85% | 🟠 危险 | 同上，标记**尽快处理** |
| > 85% | 🔴 紧急 | 同上，标记**立即处理**（ES 将触发只读保护）|

**磁盘扩容路径（按 `DiskType` 分流）**：

```
DiskType 为云盘（CLOUD_*）
  → 首选：UpdateInstanceDiskSize（原地扩容，无数据搬迁）
     目标单节点磁盘 = ceil( 当前单节点磁盘 × 当前使用率 / 0.6 )   # 目标使用率 ≤ 60%
     向上取整到 100GB 的整数倍
  → 若已达 DescribeClusterDiskRange 的 Max
     → 次选：UpdateInstanceNodeNum（加节点）

DiskType 为 LOCAL_SSD（本地盘）
  → 唯一路径：UpdateInstanceNodeNum（加节点）
     目标节点数 = ceil( 当前节点数 × 当前使用率 / 0.5 )            # 目标使用率 ≤ 50%
     并校验落在 2~50 区间
```

> 📌 扩容前必须提醒用户先排查：是否有大量历史数据未清理（建议配 ILM）、副本数是否过多。**扩容是最后手段，不是第一反应。**

### 5.2 CPU（`CpuUsageMax`）

先判偶发 vs 持续，**结论完全不同**：

| 判定条件 | 模式 | 动作 |
|---------|------|------|
| `P95 > 85` 且 `P50 < 60` | **偶发打高（spike）** | ⚠️ **不推荐扩容**。扩容解决不了查询/写入模式问题。转交 `tencent-es-diagnose` 分析尖刺原因（大查询、批量写入、merge、snapshot 集中触发）|
| `P50 > 70` | **持续高负载（sustained）** | 推荐纵向升配（增加 CPU 核数）。⛔ **规格升配暂无 MCP tool** → 按 [容量规划指南 · 升配规格选择](capacity-planning-guide.md#cpu与内存升配规格选择) 给出推荐目标规格，明确告知需在控制台执行。若已是最高 CPU 规格 → 改推 `UpdateInstanceNodeNum` 加节点 |
| 其余 | ✅ 正常 | 无需处理，仅在 14 天内预计达 85% 时提示规划 |

### 5.3 JVM 内存（`JvmMemUsageMax`）

| 当前水位 | 状态 | 动作 |
|---------|------|------|
| < 75% | ✅ 正常 | 无需处理 |
| 75% ~ 85% | 🟡 预警（GC 压力增大）| 先建议排查 fielddata / 聚合 / segment 数（转 `tencent-es-diagnose`）|
| 85% ~ 95% | 🟠 危险（熔断风险）| 推荐纵向升配（增加内存）。⛔ 同 5.2，暂无 MCP tool → 只读推荐 + 控制台引导 |
| > 95% | 🔴 紧急（OOM 风险）| 同上，标记**立即处理** |

> 💡 ES 默认 JVM 堆 = 节点内存的 50%，升配后自动增大，无需手动配置。

### 5.4 写入 / 查询 QPS（`IndexSpeed` / `SearchCompletedSpeed`）

| 月增长率 | 动作 |
|---------|------|
| > 30% | 推荐 `UpdateInstanceNodeNum` 横向扩容（分散读写压力），并给出提前规划时机 |
| ≤ 30% | 仅作趋势参考，不触发推荐 |

### 5.5 查询延迟（`SearchLatencyAvg`）

| 当前水位 | 动作 |
|---------|------|
| < 200ms | ✅ 正常 |
| ≥ 200ms | **仅作趋势参考**。延迟根因（wildcard 查询、深度分页、text 字段聚合等）属 `tencent-es-diagnose` 职责，本流程不下结论、不据此单独推荐扩容 |

### 5.6 推荐优先级排序

同时命中多个维度时，按此优先级输出（与容量规划指南一致）：

```
① 扩云硬盘容量（UpdateInstanceDiskSize）        ← 无数据搬迁，影响最小
② 升配规格（⛔ 暂无 MCP tool，只读推荐 + 控制台）
③ 横向扩容加节点（UpdateInstanceNodeNum）        ← 需 rebalance，有 IO 开销
```

> ⚠️ **单次单一变更**：`UpdateInstanceNodeNum` 与 `UpdateInstanceDiskSize` **不可同时发起**（腾讯云不允许同时变更多种类型，且前一个变更未完成时后一个会被阻断）。多维度告警时按上表优先级**排序执行，一次只做一项**，并告知用户后续项需等本次完成。

---

## Step 6：可行性校验

在向用户给出具体扩容数值前：

| 推荐动作 | 校验 tool | 校验内容 |
|---------|----------|---------|
| 扩磁盘 | `DescribeClusterDiskRange` | 目标 `DiskSize` 落在该节点类型 Min/Max 区间 |
| 加节点 | （无需 tool）| 目标节点数落在区间：`dedicatedMaster` 仅 3\|5；`dedicatedMl` 3~5；其余 2~50 |
| 任意变更 | `DescribeInstances` | `Status == 1`；health 为 green（`UpdateInstanceNodeNum` 强制要求）|
| 高风险变更 | `DescribeClusterSnapshot` | 确认存在近期成功快照 |

> 📌 若校验不通过（如目标磁盘超过 Max），**在报告阶段就告知用户可行上限**，不要等到调用变更 tool 被服务端阻断。

---

## Step 7：报告输出模板

```
📈 集群容量预测报告

集群：es-xxxxxxxx（my-es-cluster）
分析周期：最近 7 天（2026-08-11 ~ 2026-08-18，Period=3600）
集群状态：正常（Status=1） / 健康度：Green
磁盘类型：SSD 云硬盘（CLOUD_SSD，可原地扩容）
当前规格：3 × ES.S1.LARGE16（4核16GB），单节点磁盘 300GB，总容量 900GB

── 各维度水位与趋势 ──
指标              当前    P50    P95    趋势        预计达阈值
磁盘使用率        72%     68%    73%    ↗ 上升      约 12 天后达 80%
CPU 使用率        58%     41%    89%    ↗ 上升      —（偶发型）
JVM 内存          61%     58%    66%    → 平稳      —
写入 QPS          1.2k    1.1k   1.5k   ↗ +18%/月   —
查询 QPS          800     760    980    → +6%/月    —
查询平均延迟      95ms    88ms   140ms  → 平稳      —
（有效数据点：165/168，已剔除 3 个哨兵值 -2）

── 结论与建议 ──
🟡 【优先级 1】磁盘：72% 已超预警线(65%)，预计 12 天后达危险线(80%)
   推荐：UpdateInstanceDiskSize(Type="hotData", DiskSize=500)
   依据：目标使用率 ≤60% → 300 × 0.72 / 0.6 = 360GB → 向上取整 400GB
        考虑 12 天增长余量，建议一次扩到 500GB
   可行性：DescribeClusterDiskRange 显示 hotData 磁盘区间 100~2000GB ✅
   影响：蓝绿变更，集群不重启，无数据搬迁；云盘扩容不可逆；产生计费变化

⚠️ 【不建议扩容】CPU：P95=89% 但 P50=41% → 判定为偶发打高
   扩容无法解决查询/写入模式问题。建议使用 tencent-es-diagnose skill
   分析尖刺时段的大查询 / 批量写入 / merge / snapshot 触发情况

✅ JVM 内存、QPS、查询延迟：均在正常范围，无需处理

── 扩容前请先确认 ──
□ 是否有大量历史数据未清理？（建议配置 ILM 策略）
□ 副本数是否合理？（副本过多会占用额外磁盘）
□ 最近是否有成功快照？（DescribeClusterSnapshot 可查）

需要我执行磁盘扩容吗？确认后我会展示完整参数再提交。
```

---

## 局限性说明（必须在报告中体现）

- **线性外推假设增长是线性的**，实际业务常有周期性波动（周末低谷、月末峰值）
- 建议结合业务规划（大促、新业务上线、历史数据导入）综合判断
- 数据点越多（周期越长）预测越准确；有效点数不足时置信度低
- **偶发型指标不适用外推**，应看分布特征（P50/P95）而非斜率
- 探针失联期（哨兵值密集）会显著降低预测可靠性，需在报告中标注

## Anti-Patterns

❌ **不剔除 `-2` / `-1` 哨兵值就做趋势计算** → 得出完全反向的结论，最严重错误
❌ 用 `Period=60` 取 7 天数据 → 上万数据点撑爆上下文，对趋势判断无增益
❌ CPU `P95` 高就直接推荐升配 → 必须先用 `P50` 判偶发 vs 持续，偶发型扩容无效
❌ 本地盘集群（`LOCAL_SSD`）推荐 `UpdateInstanceDiskSize` → 本地盘容量与机型绑定，无法扩容，只能加节点
❌ 同时推荐并发起加节点 + 扩磁盘 → 腾讯云不允许同时变更多种类型，必须按优先级串行
❌ 给出扩容数值前不查 `DescribeClusterDiskRange` → 可能给出超过 Max 的不可行方案
❌ 在容量预测报告里做根因分析（「CPU 高是因为有慢查询」）→ 越界，根因分析属 `tencent-es-diagnose`
❌ 直接把预测结论当成变更依据自动执行 → 预测只输出建议，**变更仍须用户明确确认**
