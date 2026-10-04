# 门店人员 KPI 细则

> 本文件是 `jumper-kpi-analysis` 的**人员维度**细则。共用规则（只读边界、ID 别名、分页、消歧、量纲与时点对照）在 `SKILL.md` 里，本文件只写人员维度特有的部分，不再重复。

## 目标与边界

使用 `search_staff`、`query_staff_kpi`、`query_staff_daily_kpi`、`query_hospital_staff_summary` 四个只读工具，回答下钻到「人」的 KPI 问题（按月、按天都能答）。

- 只使用本文件列出的字段。人员数据里**没有**线索、客资、商机、渠道、成交笔数、退款，也没有个人的门店经营额；这些问题属于门店维度，见 `references/hospital-kpi.md`。
- **人员维度所有金额单位是「万元」**，门店经营金额单位是「元」，相差 1 万倍。禁止把人员完成金额与门店销售额比较、相减或算占比（详见 `SKILL.md` 的量纲对照表）。
- 姓名是真实人员信息，只在回答用户明确问到的范围内使用，不做与 KPI 无关的人员画像。

## 数据模型：必须先理解的四件事

### 1. 这是「每日快照」表，不是每日增量

同一个人同一个 KPI 月份，每天都会写一行；`completedAmount` 是**截至该快照日的当月累计完成金额**，不是当天新增。

正因为它是「月累计」，两个粒度的取数方式完全不同，服务端都已经做好，你只要选对工具：

- **月度**（`query_staff_kpi`）：取每个月的最新快照，得到该月的最终/当前完成情况。
- **日粒度**（`query_staff_daily_kpi`）：保留区间内的每一天，用相邻两天**相减**得到当日新增（`dailyAmount`），同时保留累计值（`completedAmount`）。

**不要把多行金额相加**——`completedAmount` 是月累计，把逐日的累计值加起来会把同一笔业绩重复计几十次；把不同人、不同月的行加起来同样没有意义。要算某段时间的业绩，只能加 `dailyAmount`，或用「区间末日累计 − 区间前一日累计」。

### 2. 一个人可能同时背多条业务线

`businessType`：`1`=VIP业务，`2`=居家健康管理。一个人一个月可能两条线都有 KPI。

工具返回的顶层 `kpiAmount`/`completedAmount`/`completionRate` 已经是**该人各业务线的合计口径**，`completionRate = completedAmount ÷ kpiAmount`。分线明细在 `businessLines` 里。

不要自己把 `businessLines` 里各行的 `completionRate` 平均——两条线目标不等时，平均值与真实合计完成率相差很大（例：100/100=100% 与 0/900=0%，平均 50%，真实是 10%）。要分线口径就直接引用 `businessLines`，要总口径就直接引用顶层字段。

顶层合计**只累加配置了 KPI 的业务线**：某人居家配了 200 万、VIP 没配时，顶层 `kpiAmount=200`，而 `businessLines` 里仍会出现 VIP 那一行（其 `kpiAmount`/`completedAmount`/`completionRate` 为 `null`）。所以顶层金额不一定等于 `businessLines` 各行之和，也不要因为某条线是 `null` 就说这个人「没有 KPI」。

### 3. 金额单位是万元

`kpiAmount`、`completedAmount`、`gapAmount` 以及 `businessLines` 里的同名字段，单位一律是**万元**。

- 展示时按万元说，或换算成元（×10000）后明确写单位，不要只报数字。例：`kpiAmount=15` 是「15 万元」，不是「15 元」。
- `completionRate` 是比值，与单位无关，不受影响。
- 门店经营工具（`query_hospital_kpi` 等）的金额单位是**元**。两边差 1 万倍，禁止直接比较、相减或算「人员完成占门店业绩的比例」。

### 4. 「未配置 KPI」不等于「完成率 0%」

`hasKpi=false` 表示这个人本月没有 KPI 目标，此时 `kpiAmount`、`completedAmount`、`completionRate`、`gapAmount`、`achieved` 全是 `null`。

- 必须表述为「未配置 KPI 目标」，禁止表述为「完成率 0%」「业绩为 0」「垫底」。
- 找业绩最差的人时，这些人由服务端固定排在最后，不要把他们当成倒数第一。
- 汇总工具里他们计入 `staffCount` 和 `staffWithoutKpiCount`，但**不进入**达标率的分母。

另有一种少见情形要区分开：`hasKpi=true` 但 `kpiAmount=0`（配了 KPI，但目标是 0）。此时 `completionRate` 为 `null`（除数为 0，算不出），`achieved` 为 `false`，`gapAmount` = 0 − 完成金额（≤0）。要表述为「本月 KPI 目标为 0，完成率无从计算」，既不能说成「完成率 0%」，也不能因为 `completionRate=null` 就当成未配置 KPI——**判断是否配置只看 `hasKpi`，不看完成率是否为 null**。

## 人员维度的传参规则

先遵守 `SKILL.md` 的共用硬规则（ID 别名、字符串/整数类型、可选参数省略、`Asia/Shanghai`、消歧后只传 ID），本节只列人员维度特有的：

1. `startMonth`/`endMonth` 是**月份** `yyyy-MM`（如 `2026-08`），不是日期。查单月时两者相同。服务端对 `yyyy-MM-dd` 做了容错（按其所在月处理），但那只是防笔误：传 `2026-08-15` 查的是**整个 8 月**，不是「从 8 月 15 日起」。要按天截断请用 `asOfDate`。
2. `startDate`/`endDate`（日粒度工具）是日期 `yyyy-MM-dd`，跨度上限 92 天；传 `yyyy-MM` 时按整月处理（起始取1日、结束取月末）。
3. `asOfDate` 是日期 `yyyy-MM-dd`，且不得早于 `startMonth` 的月初。
4. `businessType`、`page`、`pageSize` 传 JSON 整数，`includeStaffDetail` 传 JSON 布尔值。

## 按天还是按月

KPI 目标是**月度**的，所以「目标 / 缺口 / 达标」只有月度口径；日粒度只有「截至该日的累计」和「当日新增」。

| 用户问的 | 用哪个 |
|---|---|
| 「8 月完成率是多少 / 达标了吗 / 还差多少」 | `query_staff_kpi`（缺口、达标只有月度口径） |
| 「8 月 15 日当天做了多少」 | `query_staff_daily_kpi`，`startDate=endDate="2026-08-15"`，看 `dailyAmount` |
| 「这个月截至 15 号他做了多少」 | `query_staff_daily_kpi` 单天看 `completedAmount`；或 `query_staff_kpi` + `asOfDate="2026-08-15"` |
| 「这半个月每天的业绩走势」 | `query_staff_daily_kpi` 查区间，默认按日期升序 |
| 「他哪天做得最多」 | `query_staff_daily_kpi` + `sortBy="dailyAmount"` + `order="desc"` |
| 「今年每个月的完成率走势」 | `query_staff_kpi` 跨月查（日粒度上限 92 天，不适合看一年） |

## 跨多院时不返回顾问明细（核心规则）

**命中 2 家及以上医院、且没有指定具体人员时，默认不返回顾问明细。**

- 这条规则由服务端强制：此时 `query_staff_kpi` 与 `query_staff_daily_kpi` 都会直接报错，提示改用 `query_hospital_staff_summary`。日粒度行数是「人数 × 天数」，跨院时更容易失控。
- 正确做法是先用 `query_hospital_staff_summary` 看各院汇总，用户再指定门店后用 `query_staff_kpi` 下钻。
- 只有用户**明确要求**看到每个顾问（如「把这几家医院所有顾问的完成率都列出来」「精确到顾问」），才传 `includeStaffDetail=true`。
- **例外**：传了 `staffName` 或 `staffId` 即为「查某个人」，不受此限制，哪怕这个人跨了多家门店也照常返回明细。

判断口径：用户点名一家门店 → 明细；用户问多家门店或全部门店 → 汇总；用户点名某个人 → 明细。

## 人员与医院消歧

1. 用户点名某个人（如「麦翠婷这个月完成情况」）：先调用 `search_staff` 确认。
   - 唯一匹配：用该项的 `staffId` 查询。
   - 多个同名或跨院同名：列出姓名、所属医院、角色、有数据的月份范围，让用户选择；未确认前不要下结论。
   - 无匹配：说明当前账号可见范围内未找到这个人的 KPI 数据，**不要**回答成「完成率为 0」。
   - 姓名足够独特时，也可以直接给 `query_staff_kpi` 传 `staffName` 模糊匹配，但返回多人时必须如实列出、不要默认取第一个。
2. 用户点名医院：先调用 `search_hospitals` 拿 `hospitalId`（该ID在门店工具与人员工具之间通用）。人员工具的 `hospitalKeyword` 也认医院**简称**（服务端会先把简称解析成医院ID再匹配），但简称可能命中多家，仍以 `search_hospitals` 确认后传 `hospitalId` 为准。
3. 用户问「各门店」「所有门店」：不加医院过滤，直接用 `query_hospital_staff_summary`。

## 工具选择决策

| 用户意图 | 使用工具 | 关键规则 |
|---|---|---|
| 确认是哪个人 | `search_staff` | 同名或跨院时必须先消歧 |
| 某个人某月/某几个月的完成情况 | `query_staff_kpi` + `staffId` 或 `staffName` | 不受跨院明细限制 |
| 某一家门店全员完成情况、谁最差 | `query_staff_kpi` + 唯一 `hospitalId` | `sortBy="completionRate"`, `order="asc"` |
| 多家门店 / 全部门店的人员KPI对比 | `query_hospital_staff_summary` | 不返回顾问明细 |
| 多家门店但用户明确要顾问明细 | `query_staff_kpi` + `includeStaffDetail=true` | 仅在用户明确要求时 |
| 截至某一天的完成进度 | `query_staff_kpi` + `asOfDate`，或 `query_staff_daily_kpi` 查该天 | 用于「截至8月15日完成率」 |
| 某人某天做了多少业绩 | `query_staff_daily_kpi`（`startDate=endDate`） | 看 `dailyAmount`，不是 `completedAmount` |
| 某人一段时间每天的走势 | `query_staff_daily_kpi` | 跨度上限92天，默认按日期升序 |
| 门店整体经营额、线索、渠道 | 改读 `references/hospital-kpi.md` | 人员工具不含这些指标 |

## 四个工具的精确合同

### `search_staff`

用途：按姓名模糊搜索人员，确认身份。

- 可选：`staffName`、`hospitalKeyword`、`hospitalId`。
- 返回：`staffId`、`staffName`、`hospitalId`、`hospitalName`、`roleName`、`jobLevel`、`kpiGrade`、`earliestKpiMonth`、`latestKpiMonth`、`latestSnapshotDate`。
- 单次最多 100 人；`total` 是实际匹配人数，`truncated=true` 时不要用返回条数回答「一共多少人」。
- `jobLevel`/`kpiGrade`/`roleName` 取该人最新一次快照（对应 `latestSnapshotDate`），历史月份可能不同；为 `null` 时说明「未配置」，不要臆测。
- 本工具**不按月份过滤**，扫的是该人全部历史数据，因此可用来区分「系统里没有这个人」与「这个人那个月没数据」。

### `query_staff_kpi`

用途：查询人员 KPI 完成情况，每人每月一行。

- 必填：`startMonth`、`endMonth`（`yyyy-MM`）。
- 可选：
  - `hospitalKeyword`、`hospitalId`：限定门店。
  - `staffName`、`staffId`：限定人员。
  - `businessType`：`1`=VIP、`2`=居家；**不传即为合并全部业务线，推荐不传**。
  - `asOfDate`：`yyyy-MM-dd`，只看截至该日的快照。
  - `sortBy`：`completionRate`（默认）/`completedAmount`/`kpiAmount`/`gapAmount`。
  - `order`：`asc`（默认）/`desc`。
  - `includeStaffDetail`：布尔，默认 `false`，见上文跨院规则。
  - `page`（默认1）、`pageSize`（默认100，最大500）。
- 返回 `items` 字段：
  - 身份：`kpiMonth`、`staffId`、`staffName`、`hospitalId`、`hospitalName`、`roleName`、`jobLevel`、`kpiGrade`。
  - KPI：`hasKpi`、`kpiAmount`、`completedAmount`、`completionRate`、`gapAmount`、`achieved`。
  - 分线：`businessLines[]`，每项含 `businessType`、`businessTypeName`、`kpiAmount`、`completedAmount`、`completionRate`。
  - 时点：`snapshotDate`、`dataAsOf`、`monthInProgress`、`monthEnded`（两个时点标志的用法见下文「时点判断」）。

要「最差的 N 个人」：`sortBy="completionRate"`、`order="asc"`、`pageSize=N`，取第 1 页即可。要「最好的 N 个人」把 `order` 改成 `desc`。两个方向都由服务端把未配置 KPI 的人固定排在最后。

**排序是对返回的全部「人-月」行做的**：跨月查询时前 N 行可能来自不同月份，同一个人也可能占好几行。要「某个月最差的 N 个人」，必须 `startMonth=endMonth` 限定单月再排序。同理 `total` 是「人-月」行数，只有单月查询时它才等于人数。

跨月查询（`startMonth` ≠ `endMonth`）时每人每月各一行，用于看逐月完成率走势。月份跨度上限 36 个月，超出会报错要求收窄。

### `query_staff_daily_kpi`

用途：查询人员 KPI 的逐日进度，每人每天一行。

- 必填：`startDate`、`endDate`（`yyyy-MM-dd`）。查某一天时两者相同；**跨度上限 92 天**，超出会报错。
- 可选：
  - `hospitalKeyword`、`hospitalId`、`staffName`、`staffId`、`businessType`：与月度工具同义。
  - `sortBy`：`statDate`（默认，看走势）/`dailyAmount`/`completedAmount`/`completionRate`。
  - `order`：`asc`（默认）/`desc`。
  - `includeStaffDetail`：布尔，默认 `false`，跨院规则同上。
  - `page`（默认1）、`pageSize`（默认100，最大500）。
- 返回 `items` 字段：
  - 身份：`statDate`、`kpiMonth`、`staffId`、`staffName`、`hospitalId`、`hospitalName`、`roleName`、`jobLevel`、`kpiGrade`。
  - 金额：`hasKpi`、`kpiAmount`（**当月**目标）、`completedAmount`（截至该日的月累计）、`dailyAmount`（当日新增）、`completionRate`（截至该日的月完成率）。
  - 断档：`prevSnapshotDate`、`daysCovered`。
  - 分线：`businessLines[]`，每项含 `businessType`、`businessTypeName`、`kpiAmount`、`completedAmount`、`dailyAmount`、`completionRate`。
  - 时点：`dataAsOf`、`monthInProgress`、`monthEnded`。

三条硬规则：

1. **`statDate` 的含义是「截至这一天」**，不是「这一天当天」。当天做了多少看 `dailyAmount`；这个月到这天做了多少看 `completedAmount`。
2. **KPI 目标是月度的，不存在「当日目标」**。禁止用 `dailyAmount ÷ kpiAmount` 算「当日完成率」；`completionRate` 是截至该日的**月**进度。
3. **禁止把多天的 `completedAmount` 相加**。要算某段时间的业绩，加 `dailyAmount`，或用「末日累计 − 区间前一日累计」。

日期区间跨月时（如 `8-25`~`9-05`），同一天可能出现两行：一行属于上个 KPI 月份（月末结转的收官快照），一行属于本月。看 `kpiMonth` 区分，不要把它们当成重复数据合并或相加。

`daysCovered` 与 `prevSnapshotDate` 是数据质量信号，正常每日跑批时 `daysCovered=1`：

- `daysCovered>1`：中间有快照断档（跑批失败或未跑），该行 `dailyAmount` 是这几天的**合计**，必须写成「A日~B日合计 X 万元」，不能说成「B 日当天做了 X」。
- `prevSnapshotDate=null`：这是当月的首张快照，`dailyAmount` 是从月初攒到该日的量，`daysCovered` 等于该日在当月的日序号。

`dailyAmount` **为负是正常的**：当日发生退款或数据回溯修正。如实表述为「当日净额 −X 万元（含退款/回溯修正）」，不要抹成 0，也不要据此评价这个人。

### `query_hospital_staff_summary`

用途：按医院汇总人员 KPI，每院每月一行，**不含顾问明细**。

- 必填：`startMonth`、`endMonth`。
- 可选：`hospitalKeyword`、`hospitalId`、`businessType`、`asOfDate`、`page`、`pageSize`。
- 传了 `businessType` 时，**人数与金额都只统计该业务线**（只看 VIP 时，只背居家的人不计入 `staffCount`），会让「全院多少人」失真；默认不传。
- 结果按「月份优先、再医院」排序：分页被截断时，前几页是完整的前几个月（覆盖全部医院），不会变成「少数几家医院的完整时间序列」。
- 返回 `items` 字段：
  - `kpiMonth`、`hospitalId`、`hospitalName`。
  - 人数：`staffCount`（总人数）、`staffWithKpiCount`（已配置KPI）、`staffWithoutKpiCount`（未配置KPI）、`achievedCount`（达标人数）。
  - 比率：`achievedRate` = `achievedCount ÷ staffWithKpiCount`；`completionRate` = `completedAmount ÷ kpiAmount`（金额加权）；`avgCompletionRate`（人均算术平均）。
  - 金额：`kpiAmount`、`completedAmount`。
  - 时点：`snapshotDate`（各人中最新的快照日）、`minStaffSnapshotDate`（各人中最早的）、`dataAsOf`、`monthInProgress`、`monthEnded`。

**`snapshotDate` 与 `minStaffSnapshotDate` 不一致时，汇总口径是不齐的**：每个人各取自己在该月的最新快照，有人离职或停用后就不再写快照，他的金额停在较早的日期却仍计入合计。此时要说「数据截至 A 日~B 日（各人不一）」，不能说成单一的「截至 B 日」。

**两个完成率口径不同，引用时必须说清用的是哪个**：`completionRate` 受大目标的人影响大，`avgCompletionRate` 每个人权重相同。默认用 `completionRate`（整体完成率），用户问「平均每个人完成得怎么样」时用 `avgCompletionRate`。

`completedAmount` 只统计配置了 KPI 的人员，**不等于门店整体经营额**；且单位是万元而门店销售额单位是元。两者既不同口径也不同量纲，禁止相互印证、比较或相减。

## 时点判断：两个标志一起看

数据是「截至某日的累计」，所以「这个数是不是最终值」要靠两个字段一起判断，**不能只看一个**：

- `monthInProgress`：本行数据只统计到 `snapshotDate`/`statDate`，**没有覆盖到月末**。
- `monthEnded`：该 KPI 月份**按今天算是否已经结束**。

| `monthEnded` | `monthInProgress` | 含义 | 正确措辞 |
|---|---|---|---|
| false | true | 月份还在进行中，数据也只到快照日 | 「截至 X 日，完成率 Y%，本月尚未走完」 |
| true | true | 月份早已结束，但数据断在月末之前（跑批漏跑/停更） | 「X 月完成率 Y%，但数据只统计到 Z 日，缺月末几天，可能偏低」 |
| true | false | 月份结束且数据覆盖到月末 | 「X 月最终完成率 Y%」，可以下确定结论 |

- 前两种情况都**禁止**表述为「没完成 KPI」「未达标」「完成率只有 X%」这种定论。
- 只看 `monthInProgress` 会在第二种情况下说出「本月尚未走完」——那是错的，月份早结束了，是数据缺了几天。
- 跨月对比时，如果本月还在进行中而历史月份是完整月，要明确说明两者不可直接比较；需要同进度对比时，用 `asOfDate` 把历史月份也截到相同日序。

## 人员维度的分页补充

分页通则见 `SKILL.md`。人员维度特有：

1. `search_staff` **不分页**，其 `page`/`pageSize` 为 `null`，`total` 是实际匹配人数。
2. 日粒度的 `total` 是「人-天」行数，月度跨月查询的 `total` 是「人-月」行数，都不等于人数。
3. 需要全量时首次传 `pageSize=500`；只要前 N 名时传 `pageSize=N` 即可，不必取全。
4. 未取全结果前，不做「全店平均」「达标率」这类整体结论——除非该结论直接来自 `query_hospital_staff_summary`。

## 报错与恢复

先按 `SKILL.md` 区分 OAuth 认证、权限、参数校验和网络/服务错误；只有明确的参数错误才按下表修改后重试一次。`401` 由 MCP 客户端重新授权，`403` 核对账号权限，超时保持原条件最多重试一次；**禁止**索取密码、令牌或 API Key，也禁止把报错转述成「这个人没有数据」「这家门店没有 KPI」。

| 报错含义 | 正确的下一步 |
|---|---|
| 「本次条件命中 N 家医院……请改用 query_hospital_staff_summary」 | 改调 `query_hospital_staff_summary`；只有用户明确要顾问明细时才加 `includeStaffDetail=true` 重调 |
| 「hospitalId/staffId 格式不正确」 | 传的是数字ID或自造ID；先调 `search_hospitals`/`search_staff`，原样回传别名 |
| 「staffId 无效或该人员无KPI数据」「hospitalId 无效或该医院无数据」 | 别名不存在或已失效，重新 `search_*` 取；不要拿同一个ID反复重试 |
| 「startMonth/endMonth 格式错误」「startMonth 不能晚于 endMonth」 | 改成 `yyyy-MM`，并把起止顺序摆正 |
| 「月份跨度过大（上限36个月）」 | 收窄 `startMonth`/`endMonth` 后重查 |
| 「日期跨度过大（上限92天）」 | 收窄 `startDate`/`endDate`；要看更长区间的走势改用 `query_staff_kpi` 按月查 |
| 「startDate/endDate 格式错误」「startDate 不能晚于 endDate」 | 改成 `yyyy-MM-dd`，并把起止顺序摆正 |
| 「asOfDate 早于 startMonth 的月初」 | 该范围内没有任何快照；把 `asOfDate` 提到不早于起始月月初，或直接不传 |
| 「sortBy 仅支持 completionRate/completedAmount/kpiAmount/gapAmount」 | 月度工具只用这四个值，其余字段（如姓名、职级）不支持排序，需要时自己在输出里排 |
| 「sortBy 仅支持 statDate/dailyAmount/completedAmount/completionRate」 | 这是日粒度工具的白名单，别把月度工具的 `gapAmount` 传进来 |
| 「order 仅支持 asc/desc」「businessType 仅支持 1/2」 | 只用白名单值 |

## 结果判定

- `total=0` 且 `items=[]`：**先读 `hint`**。服务端会在空结果时告诉你人员 KPI 数据截止到哪个月：查询月份晚于它，是「数据尚未更新到该月」；在它之内，再用 `search_staff` 核对该人的 `earliestKpiMonth`/`latestKpiMonth`，区分「查无此人」与「这个月没有他的数据」。**任何一种都不等于「这个人没有业绩」**，不要下这个结论。
- 字段为 `null`：说明未配置或无法计算，如实说明，不擅自改成 0。
- 金额单位统一为万元（`kpiAmount`、`completedAmount`、`gapAmount`）；展示时写明单位，必要时换算成元（×10000）。
- `completionRate`、`achievedRate`、`avgCompletionRate` 都是小数，展示时乘以 100 加 `%`（`0.3031` → `30.31%`）。
- `gapAmount` 为正表示还差多少，为负表示超额完成。
- `achieved` 按**金额**判定（目标 > 0 且 完成金额 ≥ 目标金额），不是按四舍五入后的完成率；汇总里的 `achievedCount` 同口径。因此完成率显示 `100.00%` 却 `achieved=false` 是可能的（小数位被舍入），以 `achieved` 为准。
- 日粒度里 `dailyAmount=0` 表示当天确实没有新增业绩（有目标但没动），与 `hasKpi=false`（没有目标）是两回事，措辞要分开。
- 只描述数据支持的事实，不从完成率推断原因（不说「因为不努力」「因为客户少」）。

## 输出格式

先给结论，再给证据，最后集中说明限制。

**问某一个人**：一句话结论 +「姓名 / KPI档级 / 职级 / 该月完成率」，必要时附目标金额、完成金额、缺口，以及分业务线明细。跨月时按月列出每月完成率。

**问某一家门店**：一句话结论（谁最好、谁最差）+ 顾问明细表，列：`姓名 | KPI档级 | KPI目标(万元) | 完成金额(万元) | 完成率 | 是否达标`。未配置 KPI 的人单列一组，标注「未配置 KPI 目标」，不参与排名。

**问多家门店**：只给汇总表，列：`门店 | 总人数 | 已配置KPI人数 | 达标人数 | 达标率 | 整体完成率`。不要列顾问明细，除非用户明确要求。

**问某一天**：一句话给当天结论 +「当日新增 X 万元 / 截至当日月累计 Y 万元 / 截至当日月完成率 Z%」。`daysCovered>1` 时必须改写成「A日~B日合计 X 万元」并说明中间断档。

**问一段时间的走势**：按日期升序列表，列：`日期 | 当日新增(万元) | 截至当日累计(万元) | 截至当日完成率`。末尾点出峰值日与为负的日子（注明是退款/回溯修正）。断档的行单独标注覆盖区间。

**数据限制**统一列在最后：该月是否尚未走完、未配置 KPI 的人数、分页是否取全、快照日与统计截止时间。

## 常见请求的固定路径

- 「麦翠婷 8 月的完成情况」：`search_staff` 确认身份 → `query_staff_kpi`（`startMonth=endMonth="2026-08"`，唯一 `staffId`）→ 输出姓名、档级、完成率、明细。
- 「麦翠婷今年每个月的完成率」：`search_staff` → `query_staff_kpi`（`startMonth="2026-01"`, `endMonth="2026-08"`）→ 按月列出，注明最后一个月是否 `monthInProgress`。
- 「宝安妇幼 8 月的完成情况」：`search_hospitals` 消歧 → `query_staff_kpi`（唯一 `hospitalId`，8月）→ 输出顾问姓名、档级、完成率、明细。
- 「宝安妇幼 8 月谁业绩最差」：同上，加 `sortBy="completionRate"`、`order="asc"`、`pageSize=5`；明确排除未配置 KPI 的人，并说明是「完成率最低」而非「最不努力」。
- 「各门店 8 月 KPI 完成情况」：直接 `query_hospital_staff_summary`（8月，不加医院过滤），只给汇总，不列顾问。
- 「截至 8 月 15 日大家完成得怎么样」：`query_staff_kpi` 加 `asOfDate="2026-08-15"`，结论里写明「截至 8 月 15 日」。
- 「麦翠婷 8 月 15 日做了多少」：`search_staff` 确认身份 → `query_staff_daily_kpi`（`startDate=endDate="2026-08-15"`，唯一 `staffId`）→ 报 `dailyAmount`（当日新增），顺带给 `completedAmount`（截至当日月累计）。
- 「麦翠婷这个月每天的业绩」：`query_staff_daily_kpi`（`startDate="2026-08-01"`、`endDate="2026-08-31"`，唯一 `staffId`）→ 按日期升序列出，标注断档日与为负的日子。
- 「麦翠婷 8 月哪天做得最多」：同上加 `sortBy="dailyAmount"`、`order="desc"`、`pageSize=5`；`daysCovered>1` 的行要说明是多天合计，不能直接当成单日冠军。
- 「宝安妇幼 8 月 15 日各顾问做了多少」：`search_hospitals` 消歧 → `query_staff_daily_kpi`（唯一 `hospitalId`，`startDate=endDate="2026-08-15"`）。

## 禁止事项

- 禁止把不同快照日或不同月份的 `completedAmount` 相加当作总业绩。
- 禁止把各业务线的 `completionRate` 平均当作个人合计完成率。
- 禁止把 `hasKpi=false`（未配置 KPI）说成完成率 0%、业绩为 0 或垫底。
- 禁止把 `monthInProgress=true` 的月份说成「没完成 KPI」。
- 禁止只看 `monthInProgress` 就说「本月尚未走完」——`monthEnded=false` 且 `monthInProgress=true` 才是月份进行中且数据未到月末；两者都为 true 则是月份已结束但数据断在月末之前。
- 禁止把空结果说成「这个人没有业绩」——先看 `hint` 里的数据截止月。
- 禁止在命中多家医院时不加 `includeStaffDetail` 就臆造顾问明细，或在服务端拒绝后仍编造数据。
- 禁止把人员 `completedAmount`（万元）与门店销售额（元）相互印证、相减或算差额——两者既不同口径也差 1 万倍。
- 禁止把万元金额当成元来报（如把 `kpiAmount=15` 说成「KPI 目标 15 元」）。
- 禁止把 `achievedRate` 的分母当成 `staffCount`（分母是 `staffWithKpiCount`）。
- 禁止把 `staffId`/`hospitalId` 当数字或数组传递，或使用未经 `search_*` 返回的自造ID。
- 禁止在人员未消歧时用模糊姓名混查多个人后只取第一个。
- 禁止把 `completionRate=null` 一律当成「未配置 KPI」——目标为 0 时它也是 `null`，判断依据是 `hasKpi`。
- 禁止把顶层 `kpiAmount` 当成 `businessLines` 各行之和（未配置的业务线不计入合计）。
- 禁止把服务端报错说成「没有数据」，或不区分认证、权限、参数与网络错误就反复调用。
- 禁止用跨月查询的前 N 行回答「某个月最差的 N 个人」（那些行来自不同月份）。
- 禁止把逐日的 `completedAmount` 相加当作区间业绩——它是月累计，相加会重复计几十次；要加就加 `dailyAmount`。
- 禁止用 `dailyAmount ÷ kpiAmount` 算「当日完成率」——KPI 目标是月度的，没有当日目标。
- 禁止把 `daysCovered>1` 的行说成「某天当天做了多少」（那是断档几天的合计）。
- 禁止把为负的 `dailyAmount` 抹成 0 或说成数据错误——那是当日退款/回溯修正，如实呈现。
- 禁止把 `statDate` 读成「这一天当天」：它的含义是「截至这一天」，当天的量只有 `dailyAmount`。
