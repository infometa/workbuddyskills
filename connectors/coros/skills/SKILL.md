---
name: coros-skill
description: COROS 运动与健康数据查询技能 - 训练记录、活动分析、睡眠、心率、HRV、压力、体能评估与训练日程
version: "1.0.0"
author: "COROS"
---

# COROS Skill

本 Skill 指导 AI 通过 COROS Connector 查询用户的 COROS 运动与健康数据。数据来自用户授权绑定的 COROS 账号；所有工具均为只读查询，不会修改或删除用户数据。

## 关键约定（调用前必读）

1. **日期格式**：所有日期参数使用 `yyyyMMdd`（如 `20260824`）。日期窗口按用户 COROS 账号档案中的时区计算，由服务端自动处理，**不要**尝试传入时区。若服务端按 UTC 兜底计算，结果末尾会附带披露说明，请一并转述给用户。
2. **睡眠归属日**：每晚睡眠记在**醒来那天**。"昨晚睡得怎么样"应传**今天**的日期；"前晚"传昨天的日期。用户明确指定某个日期时按原样传入（与 COROS App 当天展示一致）。该规则适用于 `querySleepData`、`querySleepHrv` 以及 `queryDailyHealthData` 的睡眠部分。
3. **活动查询链路**：先用 `querySportRecords` 获取活动的 `labelId`、`sportType`（及起止时间戳），再调用详情/分段/分析/FIT 工具。`labelId` 与 `sportType` 必须来自列表结果，不要臆造。
4. **运动类型传数字代码**：`sportTypeCodes` 只传 COROS 数字代码，不要传名称。完整代码表见 `querySportRecords` 工具下方；按用户的实际意图选择对应代码组，不要机械合并相邻品类（例如用户说"跑步"传 [100,101,102,103]，不要顺带把徒步 104、登山 105 也传上），代码表以外的值不要猜测。
5. **心率问题选对工具**：用户只问心率、平均心率、静息心率或心率趋势时，用 `queryAvgHeartRate` / `queryRestingHeartRate`；`queryDailyHealthData` 是整体每日健康总览，不要用它单查心率。
6. **HRV 结论以官方评估为准**：`querySleepHrv` 同时返回官方日评估与原始时序，日均值和正常范围直接使用官方评估段，不要自行从原始点计算。
7. **参数必填标注**：下方参数表的"必填"列有三种取值——`✓` 必须传有效值；`✓*` 接口 schema 标为必填、但语义上可不指定，**调用时参数仍要携带**，用下述占位值表达"不指定"：日期/字符串传空字符串 `""`，天数/条数直接传默认值（如 7、20），距离/时长筛选传 `0`（服务端把 ≤0 视为不筛选），`sportTypeCodes` 不筛选时传 `[65535]`；`-` 为可省略参数。
8. **返回形式**：除 `downloadActivityFitFiles` 返回 FIT 二进制资源外，其余工具返回面向用户的格式化文本，可直接引用或总结到回答中。

## 可用工具

### 用户与设备

#### queryUserInfo - 查询用户基础信息

查询用户档案：身高、体重、生日（含年龄）、性别、昵称。无参数。

**使用示例**：用户问自己的身高体重、年龄或个人档案时调用。

#### queryDevices - 查询绑定设备

查询用户绑定的 COROS 设备列表，含设备标识、固件类型和自定义名称。无参数。

**使用示例**：用户问"我绑了哪些设备 / 我的手表"时调用。

### 运动记录与活动

#### querySportRecords - 查询运动记录（活动列表入口）

按条件筛选用户的运动记录。这是所有活动详情类工具的入口：后续工具所需的 `labelId`、`sportType`、起止时间戳都来自本工具的返回结果。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd；传 "" 时窗口为包含 endDate 在内的 7 天（两端都传 "" 即最近 7 天，含今天） |
| endDate | string | ✓* | 结束日期 yyyyMMdd；传 "" 时默认今天 |
| sportTypeCodes | integer[] | ✓* | COROS 数字运动类型代码，见下方代码表；不筛选传 [65535] |
| minDistanceKm | number | ✓* | 最小距离（公里）；不筛选传 0 |
| maxDistanceKm | number | ✓* | 最大距离（公里）；不筛选传 0 |
| minDurationMinutes | integer | ✓* | 最短时长（分钟）；不筛选传 0 |
| maxDurationMinutes | integer | ✓* | 最长时长（分钟）；不筛选传 0 |
| maxAveragePace | string | ✓* | 最大平均配速，如 "5:30"；不筛选传 "" |
| locationKeyword | string | ✓* | 地点关键词，如城市名或公园名；不筛选传 "" |
| limit | integer | ✓* | 返回条数上限，默认 20 |

**返回**：日期、运动类型、地点、时长、距离/组数、平均配速或速度、labelId、sportType，以及活动的 startTimestamp/endTimestamp（如有）。

**COROS 运动类型代码表**（sportTypeCodes 只能从中选取）：

| 品类 | 代码 |
|------|------|
| 跑步/徒步 | 100 outdoor run, 101 indoor run, 102 trail run, 103 track run, 104 hike, 105 mountain climb, 106 multi-pitch sub climb |
| 骑行 | 200 outdoor bike, 201 indoor bike, 202 e-bike, 203 gravel bike, 204 mountain bike, 205 mountain e-bike, 299 helmet bike |
| 游泳 | 300 pool swim, 301 open water swim |
| 有氧/力量 | 400 gym cardio, 401 GPS cardio, 402 strength |
| 滑雪 | 500 ski, 501 snowboard, 502 XC ski, 503 alpine touring |
| 飞行 | 600 fighter |
| 划船/水上/钓鱼 | 700 rowing, 701 indoor row, 702 whitewater, 704 flatwater, 705 windsurfing, 706 speedsurfing, 707 boat fishing lure, 708 shore fishing lure, 709 pond fishing lure, 710 kayak fishing lure, 711 inshore fishing, 712 offshore fishing, 713 boat fly fishing, 714 shore fly fishing, 715 surf fishing |
| 攀岩 | 800 indoor single pitch, 801 bouldering, 802 outdoor climb |
| 健走/健身 | 900 walk, 901 jump rope, 902 stair climbing, 903 elliptical, 904 yoga, 905 pilates, 906 boxing |
| 球类 | 1000 badminton, 1001 ping pong, 1002 basketball, 1003 soccer, 1004 pickleball, 1005 tennis, 1006 padel |
| 休闲 | 1100 frisbee, 1101 skateboard |
| 综合体能 | 1200 hybrid fitness |
| 户外自定义 | 9800-9807（球类/休闲/山地/高海拔/机动车/水上/探险/其他） |
| 室内自定义 | 9900-9904（球类/力量/塑形/舞蹈/其他） |
| 通用自定义 | 9999 |
| 多项运动 | 10000 triathlon, 10001 free combine, 10002 climb ski, 10003 multi-pitch climb |
| 跟随路线 | 25301 |
| 全部 | 65535 |

**使用示例**：
- 最近一次跑步：sportTypeCodes 传 [100,101,102,103]，limit 传 1
- 上周所有训练：传上周日期范围，sportTypeCodes 传 [65535]

#### getActivityDetail - 查询活动详情

获取单次训练活动的详细数据：心率、配速/速度、海拔、踏频等。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| labelId | string | ✓ | 活动 labelId，来自 querySportRecords |
| sportType | integer | ✓ | 运动类型代码，如 100=跑步、200=骑行 |

#### analyzeActivityDetail - 教练式活动分析

先获取活动详情，再用通俗语言给出教练风格的训练总结，可指定分析侧重点。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| labelId | string | ✓ | 活动 labelId，来自 querySportRecords |
| sportType | integer | ✓ | 运动类型代码 |
| focus | string | ✓* | 分析侧重点，如配速稳定性、速度、心率；无侧重传 "" |

#### queryActivityLapData - 查询活动分段数据

查询指定活动的分段（lap/segment）数据，仅返回 COROS App 对该运动类型展示的字段。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| labelId | string | ✓ | 活动 labelId，来自 querySportRecords |
| sportType | integer | ✓ | 运动类型代码，如 100=跑步、1200=综合体能 |

#### queryCustomActivityLapData - 查询自选时间窗分段数据

对单次活动中用户指定的精确时间窗做分段统计。适用于"最后 N 分钟""最后一段""某个时间区间"类请求；默认分段请用 queryActivityLapData。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| labelId | string | ✓ | 活动 labelId，来自 querySportRecords |
| sportType | integer | ✓ | 运动类型代码 |
| startTimestamp | integer | ✓ | 选取窗口起点 Unix 秒；"最后 N 分钟"传活动 endTimestamp - N × 60 |
| endTimestamp | integer | ✓ | 选取窗口终点 Unix 秒；"最后 N 分钟"传活动 endTimestamp |

两个时间戳应落在活动时间窗内。

#### downloadActivityFitFiles - 下载活动 FIT 文件（二进制）

以二进制资源形式返回一个或多个活动的原始 FIT 文件，用于深度数据分析。客户端能解析 FIT 时使用解析出的全部数据，不要假设固定字段；无法原生解析时可用 Python（如 fitparse）解码。

**参数说明**（本工具参数在 schema 中均为可选）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| labelId | string | - | 指定单个活动；传了则必须同时传 sportType |
| sportType | integer | - | labelId 存在时必填；日期模式下可作为可选的运动类型过滤 |
| startDate | string | - | 未传 labelId 时按日期范围批量下载，yyyyMMdd；全部省略时默认今天 |
| endDate | string | - | 默认等于 startDate；不得早于 startDate，倒序会报错 |
| limit | integer | - | 返回文件数上限，默认 5，最大 10 |

查询过去某一天的文件时务必传 startDate（endDate 可传同一天或省略）；**不要只传过去的 endDate**——startDate 会默认今天，构成倒序而报错。

**额度**：与 queryActivityFitFileDownloadUrls 共用同一个固定 24 小时计数窗口（后续调用不会延长该窗口），窗口内最多 50 个文件。每个成功返回的 FIT 文件消耗 1 个额度；无匹配结果或调用失败不消耗。

#### queryActivityFitFileDownloadUrls - 查询 FIT 文件下载地址

以文本形式返回活动原始 FIT 文件的下载 URL。仅当客户端无法接收 downloadActivityFitFiles 的二进制资源时作为兜底；参数与 downloadActivityFitFiles 完全一致（含"查过去某天传 startDate"的规则），每个成功返回的 URL 消耗同一个 24 小时窗口 50 个文件的额度。

### 每日健康与睡眠

#### queryDailyHealthData - 查询每日健康总览

返回每日综合健康数据：步数、卡路里、压力、睡眠质量与时长，以及作为总览一部分的心率摘要。只问心率时不要用本工具（见"关键约定"第 5 条）。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| days | integer | - | 最近查询天数，默认 7 |

#### querySleepData - 查询睡眠数据

返回睡眠评分、主睡眠时长、深睡/浅睡/REM 比例、清醒时长与次数、主睡眠窗口和小睡窗口。日期为**醒来日**（见"关键约定"第 2 条）。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd（醒来日）；无明确日期传 "" |
| endDate | string | ✓* | 结束日期 yyyyMMdd（醒来日）；无明确日期传 ""；只传任一端日期时按该日单日查询 |
| days | integer | ✓* | 未给日期时的最近天数，默认 7 |

### 健康统计

#### queryAvgHeartRate - 查询每日平均心率

返回区间内每天的平均心率。显式 yyyyMMdd 日期优先于最近 N 天查询。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | - | 开始日期 yyyyMMdd |
| endDate | string | - | 结束日期 yyyyMMdd，省略时等于 startDate |
| days | integer | - | 未传日期时的最近天数，默认 7 |

#### queryRestingHeartRate - 查询每日静息心率

返回区间内每天的静息心率。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| days | integer | - | 最近查询天数，默认 7 |

#### querySleepHrv - 查询睡眠 HRV

返回官方睡眠 HRV 日评估（平均 HRV、正常范围、基线、评价）及睡眠期间原始 HRV 时序。问睡眠 HRV、恢复状态、某天 HRV 为何偏低时用本工具。日期为醒来日："昨晚"传今天的日期。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd（醒来日）；无明确日期传 "" |
| endDate | string | ✓* | 结束日期 yyyyMMdd；传 "" 时等于 startDate |
| days | integer | ✓* | 未给日期时的最近天数，默认 7，最大 7（超出按 7 处理） |

#### queryStressLevel - 查询每日平均压力

返回区间内每天的平均压力值。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| days | integer | - | 最近查询天数，默认 7 |

#### queryStressTimeSeries - 查询压力原始时序

返回压力时序点（时间戳、时区、压力值、展示分、压力 HRV、压力心率）。适合"今天压力怎么变化的"类问题。**无论显式日期还是最近 N 天，窗口都不得超过 7 天**，显式范围超 7 天会报错。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd；无明确日期传 "" |
| endDate | string | ✓* | 结束日期 yyyyMMdd；传 "" 时等于 startDate |
| days | integer | ✓* | 未给日期时的最近天数，默认 1，最大 7 |

#### queryHealthCheckTimeSeries - 查询健康快测时序

返回最近一次完整健康快测（wellness check）的原始心率、HRV、压力、呼吸率和血氧时序；日期范围与历史兜底规则见下文。

**历史兜底规则**：未指定日期时先查最近 N 天；最近窗口内没有完整快测，会自动兜底返回**历史上最近一次**完整快测（可能远早于查询窗口）。结果中会标注这次快测的实际日期——回答时必须按该实际日期表述，不要把历史记录说成近几天的数据。指定了明确日期时只查该日期范围，不做历史兜底。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd；无明确日期传 "" |
| endDate | string | ✓* | 结束日期 yyyyMMdd；传 "" 时等于 startDate |
| days | integer | ✓* | 未给日期时的最近搜索天数，默认 7，最大 7（超出按 7 处理） |

### 体能与恢复

#### queryFitnessAssessmentOverview - 查询体能评估概览

返回 VO2max、跑力等级、阈值配速和 5 公里/10 公里/半马/全马成绩预测。无参数。

#### queryTrainingLoadAssessment - 查询训练负荷评估

返回近日训练评语、短期负荷、长期负荷和负荷比，用于判断近期训练量是否合适。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| days | integer | - | 最近查询天数，默认 7 |

#### queryRecoveryStatus - 查询恢复状态

返回当前体力恢复百分比、恢复等级和预计完全恢复时间。无参数。

### 训练日程

#### queryTrainingSchedule - 查询训练日程

返回用户的 COROS 训练安排。适合"我这周/明天/某段时间该练什么"类问题。

**注意**：
- 返回结果可能包含内部 Plan ID 和 idInPlan 字段，**不要向用户展示这些内部 ID**。
- 本 Connector 当前**只开放日程查询**：即使工具返回或描述中提到 `queryTrainingPlanDetail`、`updateTrainingPlan` 等训练计划工具，它们目前并未开放，**不要尝试调用**；用户需要修改训练计划时，引导其使用 COROS App。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDate | string | ✓* | 开始日期 yyyyMMdd；无明确日期传 "" |
| endDate | string | ✓* | 结束日期 yyyyMMdd；无明确日期传 "" |

**日期默认规则**：两个参数都传 "" 时查询本周（周一到周日）；只给 startDate 时查询该单日；只给 endDate 时窗口为今天到该日期。

### 生理周期

#### queryMenstruationCycles - 查询生理周期

返回今日经期状态、下次经期开始日期、每日阶段状态、周期日期区间和用户备注。

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| startDay | integer | - | 开始日期 yyyyMMdd 整数；省略或 0 表示今天前 30 天 |
| endDay | integer | - | 结束日期 yyyyMMdd 整数；省略或 0 表示今天后 365 天 |

## 典型工作流

- **分析最近一次跑步**：`querySportRecords`（sportTypeCodes=[100,101,102,103]，limit=1）→ `analyzeActivityDetail`（labelId、sportType、focus 按用户关注点）。
- **上周训练总结**：`querySportRecords`（上周日期范围）→ 必要时对重点活动调 `getActivityDetail` → 配合 `queryTrainingLoadAssessment` 给出负荷结论。
- **最后 10 分钟表现**：`querySportRecords` 拿到活动 endTimestamp → `queryCustomActivityLapData`（startTimestamp=endTimestamp-600，endTimestamp=endTimestamp）。
- **FIT 深度分析**：`downloadActivityFitFiles` 获取二进制并解析；客户端收不了二进制资源时改用 `queryActivityFitFileDownloadUrls`。
- **恢复状态综合判断**：`queryRecoveryStatus` + `querySleepHrv` + `queryRestingHeartRate` 交叉给结论。

## 认证与授权

- 连接采用标准 OAuth 2.1 + PKCE，由 WorkBuddy 自动完成：用户点击"连接"后跳转 COROS 账号登录与授权页面，登录并同意授权即可使用，无需手动获取或填写任何 Token。
- access_token 过期时由 WorkBuddy 使用 refresh_token 自动续期，对用户透明。
- 当工具返回"未绑定 COROS 账号""授权已失效""请重新连接"类提示时，说明授权链路需要重建：引导用户在 WorkBuddy 中对 COROS Connector 重新执行连接（重新授权），不要换参数重试。

## 错误与边界

- **未授权 / 绑定失效**：工具会返回面向用户的可读提示，直接转述并引导重新连接。
- **查询无数据**：属正常情况（当天未佩戴设备、未开启对应功能、无该类型记录），如实告知用户，不要编造数据。
- **FIT 下载额度**：两个 FIT 工具共用同一个固定 24 小时计数窗口（后续调用不会延长该窗口），窗口内最多 50 个文件；单次最多 10 个（默认 5）。每个成功返回的文件或 URL 消耗 1 个额度，无匹配结果或调用失败不消耗。额度用尽时工具会返回提示，此时不要重试，告知用户等窗口过期后再试。
- **日期倒序**：常规查询工具会宽容交换起止日期；FIT 两个工具和生理周期工具遇到倒序/不合法窗口会显式报错，需修正后重试。
- **时序窗口上限**："最近 N 天"模式下压力时序、健康快测、睡眠 HRV 都最多 7 天（超出按 7 处理）；显式日期范围只有压力时序强制不超过 7 天（超出报错），需要更长区间时分段查询；睡眠 HRV 和健康快测需要超过 7 天时，直接改用显式日期范围即可（不受 7 天限制）。
- **重试**：查询类工具失败不改变任何状态，可修正参数后重试；FIT 工具失败同样不消耗额度，但每次**成功**调用都会按返回的文件数计入额度——不要对同一活动重复成功下载。
