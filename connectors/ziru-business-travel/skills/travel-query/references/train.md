# 火车

## ziru_train_list — 火车班次列表

取该线路当天的全量车次，按发车时间窗过滤，**按发车时间升序**返回。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date` | string | 是 | 发车日期，`yyyy-MM-dd` |
| `fromStation` | string | 是 | 出发地，城市名或站名（口径见下） |
| `toStation` | string | 是 | 到达地，城市名或站名（口径见下） |
| `startTime` | string | 否 | 出发时间下限 `HH:mm`，只返回该时刻（含）之后发车的车次 |
| `endTime` | string | 否 | 出发时间上限 `HH:mm`，只返回该时刻（含）之前发车的车次；不能早于 `startTime` |

### 地名口径（重要）

必须传 **12306 口径**的名字，**不带行政后缀**：

| 传这个 | 结果 |
|---|---|
| `北京`、`南京`、`上海` | ✅ |
| `北京南`、`上海虹桥`、`南京南` | ✅ |
| `北京市`、`南京市` | ❌ 查空 |
| `北京南站` | ❌ 查空 |

用户说的地名带后缀时，**去掉 `市`/`县`/`站` 等后缀再传**。例：用户说"南京市"，传 `南京`；说"北京南站"，传 `北京南`。

城市名返回该市主要车站的车次；用户指定了具体站名时传完整站名。

### 返回

| 字段 | 说明 |
|---|---|
| `trainNo` | 车次号，如 `G531` |
| `fromStation` / `toStation` | 出发站 / 到达站，如 `北京南` / `上海虹桥` |
| `departureDate` / `arriveDate` | 发车 / 到达日期时间，`yyyy-MM-dd HH:mm:ss`（含跨天信息） |
| `runTimeSpan` | 运行时长（分钟） |
| `lowerPrice` | 最低价 |
| `trainTypeID` | 车次类型代号，首字母（`G` 高铁 / `D` 动车 / `C` 城际 / `Z``T``K` 普速 等） |
| `trainTypeName` | 车次类型名，如 `高铁` |
| `saleDateTime` | 起售时间，`yyyy-MM-dd HH:mm:ss` |
| `saleStatus` | 销售状态：`正常` / `暂停发售` / `未开售` / `暂售至` |
| `seats` | 坐席列表，见下 |
| `fxhFlag` / `smartFlag` / `quietFlag` | 复兴号 / 智能动车组 / 有静音车厢 |
| `allNoSeatFlag` | 是否无任何符合差旅标准的坐席 |

`seats` 每项：

| 字段 | 说明 |
|---|---|
| `seatCode` | 坐席码 |
| `seatName` | 坐席名，如 `二等座`、`一等座`、`商务座`、`无座` |
| `seatNumber` | 剩余票数（真实数量，数字） |
| `price` | 价格 |

空数组 = 该线路当天没有车次。

### 示例

```
ziru_train_list({ "date": "2026-09-20", "fromStation": "北京", "toStation": "上海" })
→ 55 条，首条：
  { "trainNo": "G531", "fromStation": "北京南", "toStation": "上海虹桥",
    "departureDate": "2026-09-20 06:08:00", "arriveDate": "2026-09-20 12:04:00",
    "runTimeSpan": "356", "lowerPrice": 525.0,
    "trainTypeID": "G", "trainTypeName": "高铁",
    "saleStatus": "正常",
    "seats": [ { "seatCode": "O", "seatName": "二等座", "seatNumber": 171, "price": 525.0 }, … ] }
```

```
ziru_train_list({ "date": "2026-09-20", "fromStation": "南京市", "toStation": "上海市" })
→ ❌ 会查空，要传 "南京" / "上海"
```

### 未开售的车次

**未开售的车次照常返回**，`saleStatus` 会是 `未开售`（有时是 `暂停发售` / `暂售至`）。

这时必须明确告诉用户：

> 该车次 **{saleDateTime} 才开售**

不要把它当成已可购买的车次直接推荐。

### 备注

- `seatNumber` 是真实余票数，`0` 表示无票。
- 车次时间跨天时，`arriveDate` 的日期会大于 `departureDate`。
