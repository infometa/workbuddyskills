# 询价报文字段词典

> ⛔ **本表仅供内部翻译使用。** 字段名（`quoteStat`、`yield`、`consultRecordId` …）与代码值（`Y` / `N` …）
> **禁止出现在给用户的文字里**。
> 翻译后只输出**中文业务值**：「已报价 / 未报价」「询价中 / 已结束」「收益率 8.5%」「规模 2,000 万」，
> 而不是 `quoteStat=Y` 这类表达式。

查询接口返回的每个询价结构对象的字段含义。渲染表单与向用户提问时，必须用本词典把代码翻译成中文，
禁止向用户展示原始英文代码。

> **重要前提**：当前环境返回的**值**多数已中文化——`structure`、`inquiryState`、`margin` 等直接就是中文
> （如「日观分段雪球（早利结构）」「询价中」「先付」）。
> 因此**不要无条件翻译**：值已是中文就原样展示；只有拿到英文/代码值时才查本表。
> `productType`、`quoteStat`、`highlightFlag` 等**仍为代码**，需翻译。

## 核心字段（表单必展示）

| 字段 | 含义 | 说明 |
|------|------|------|
| `consultRecordId` | **询价 ID** | 提交报价时用这个，原样回传，勿解码 |
| `id` | 明细 ID | ⚠️ **不是**报价用的 ID，勿混淆 |
| `inquiryName` | 询价单名称 | 如 20260904-02 |
| `secuCode` / `secuName` | 标的代码 / 名称 | 如 000852.SH / 中证1000 |
| `structure` | 结构名 | 当前已是中文，直接展示 |
| `productType` | 产品类型 | **代码**：Z=雪球类 X=期权类 SX=收益凭证类 O=场外期权 |
| `deadline` | 期限（月） | 数字 |
| `deadlineDate` | 报价截止时间 | 超过此时间不再询问/提交 |
| `inquiryDate` | 询价日期 | |
| `subscriptionDate` | 认购日期 | |
| `lockExpireDate` | 锁价到期日 | |
| `maxScale` | 最大规模（万） | 带千分位，提交需去逗号 |
| `margin` | 保证金比例 | 已中文，如 先付 / 79 / 100 |
| `highlightFlag` | 重点标记 | **代码**：Y=重点 N=否 |
| `remark` | 客户备注 | 原样展示 |
| `inquiryState` | 询价状态 | 已中文：询价中 / 询价结束 |
| `quoteStat` | 报价状态 | **代码**：Y=已报价 N=未报价 |
| `yield` | 收益率（小数） | 0.085 即 8.5%，直接展示原值不做转换 |
| `submitDate` | 报价提交时间 | 已有报价时才有值 |
| `quoteRemark` | 报价备注 | |
| `enquirySeries` | 询价系列 | 如 招利 / 鑫隆 / 新利 |
| `cyRate` | 参与率类比率 | 小数 |

## 敲出 / 障碍 / 行权

| 字段 | 含义 |
|------|------|
| `outLimit` / `inputLimit` / `inputLimitTwo` | 敲出界限 / 敲入界限 |
| `obstaclePrice` / `obstaclePriceOne` / `obstaclePriceTwo` | 障碍价（多档） |
| `executePrice` / `executivePriceOne` / `executivePriceTwo` | 行权价（多档） |
| `minExecutePrice` / `maxExecutePrice` | 行权价下限 / 上限 |
| `optionType` | 期权类型 EUROPEAN(欧式) / AMERICAN(美式) |
| `memoryOutFlag` | 是否为记忆敲出结构 |
| `initKnockOutLevel` / `resetKnockOutLevel` | 期初 / 重置敲出水平 |
| `noOutProfits` | 未敲出收益 |

## 票息 / 返息

| 字段 | 含义 |
|------|------|
| `bonusCoupon` / `bonusCouponInitial` | 红利票息 / 期初红利票息 |
| `backInterest` / `backInterestTwo` | 返息 |
| `backInterestType` | ABSOLUTE=绝对值 ANNUAL=年化 |
| `backInterestMode` | 返息模式 |
| `annBackInterest` / `annBackInterestTwo` | 年化返息 |
| `absBackInterest` / `absBackInterestTwo` | 绝对值返息 |
| `noBackInterest` / `noBackInterestTwo` | 无返息档位 |
| `twoOutYield` / `threeOutYield` / `fourOutYield` | 分年敲出票息 |
| `*OutYieldInitial` | 对应票息的期初值 |
| `annualOutYield` | 年化敲出票息 |
| `fixOutYield` | 固定敲出票息 |
| `qrbqcYield` / `bxqYield` | 其他票息类字段 |
| `beforeEndRate` | 提前结束利率 |
| `minimumYield` / `middleYield` / `highestYield` | 阶梯收益档位 |

## 费用 / 比例

| 字段 | 含义 |
|------|------|
| `manageFee` / `custodyFee` | 管理费 / 托管费 |
| `riseParticipationRate` | 上涨参与率 |
| `maxDeficitsRatio` | 最大亏损比例 |
| `dividendLimit` | 分红限制 |
| `payInterestFre` | 付息频率 |
| `exePriceXddcyRate` | 行权价相关比率 |

## 观察频率字段

`openSeaObsFre`（开放期与观察频率）、`outObsFre`（敲出）、`inputObsFre`（敲入）、`observeFrequency`。

当前环境这些字段**返回中文描述**（如「每月（第3个月月末开始观察）」），直接展示。
若拿到英文代码，按下列翻译：

| 代码 | 含义 |
|------|------|
| MR | 每月观察 |
| QM / QMGC | 每季观察 / 季度观察 |
| FBSYZHMYKSH | 半年观察 |
| MY_DSGYYMKSGC | 每月锁定收益观察（向下双观察日） |
| MY_DYGYYMKSGC | 每月单一观察日 |
| MRGCQC_DQJS | 每月观察到期敲出（短期） |
| JDFH | 降息保护 |
| JDKFKSH | 降敲复敲 |
| OSQQ | 敲出全权 |

多代码逗号分隔（如 `JDFH,FBSYZHMYKSH`）表示组合条款，逐个翻译后用顿号连接。

## 结构代码（`structure`）

**当前环境返回的已是中文结构名**（如「日观分段雪球（早利结构）」「看涨价差」），直接展示。
下列映射仅用于遇到旧代码值时的兜底：

| 代码 | 中文名 |
|------|--------|
| Z_JG_FPXZZ | 雪球-非保本(保证金) |
| X_JG_XQ | 期权-雪球 |
| X_JG_FDXQ | 期权-分年雪球 |
| X_JG_OSFDXQ | 期权-欧式分年雪球 |
| SX_JG_KZJC | 收益凭证-看涨急跌(参与率) |
| SX_JG_KZXXQAC | 收益凭证-看涨(小雪球AC) |
| SX_JG_KZSYQ | 收益凭证-看涨收益权 |
| O_JG_KDSYJ | 场外期权-看大跌价(欧式) |
| O_JG_KZJC | 场外期权-看涨急跌(参与率)（待确认） |
| X_JG_RGFDXQZLJG | 期权-认购反跌雪球(逐日降钩)（待确认） |

## 交易模式（`dealPattern`）

`SYPZ` = 收益凭证模式，其他代码原样展示。

## 提交报价时必填字段映射

提交接口 `bathInsertTraderQuote` 的报文为 `{ "quotes": [ ... ] }`，每条报价包含：

- `consultRecordId` = **询价 ID**（来自查询结果的 `consultRecordId`，**不是**明细 `id`；原样回传，勿解码）；
- `yield` = 报价收益率（**小数、所见即所得**：填 0.09 即提交 0.09，不做百分数↔小数转换）；
- `quoteRemark` = 可选备注；
- `maxScale` = 规模（**提交时去掉千分位逗号**，如 `"7,000"` → `"7000"`）；
- 券商身份 4 字段（`traderWechatId` / `traderId` / `traderDept` / `deptId`）由用户提供或页面「高级设置」填写。

## 未知值处理

遇到词典里没有的代码或值：**直接展示原始值，并注明「该项待确认」**，不要猜测含义，不要编造中文名。
