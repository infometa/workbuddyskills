# WorkBuddy 路由规则

| 用户意图 | 脚本 |
| --- | --- |
| 机票、航班、特价机票 | `scripts/flight-query.js` |
| 火车票、高铁、动车、车次 | `scripts/train-query.js` |
| 酒店、住宿、民宿、位置附近酒店 | `scripts/hotel-query.js` |
| 景区、门票、游玩地点 | `scripts/scenery-query.js` |
| 汽车票、大巴、长途汽车 | `scripts/bus-query.js` |
| 跟团游、自由行、度假、行程规划 | `scripts/travel-query.js` |
| 未指定方式的“怎么走/交通方式” | `scripts/traffic-query.js` |

参数规则：

- 出发地传 `--departure`。
- 目的地或城市传 `--destination`。
- 航班号传 `--flight-number`。
- 车次号传 `--train-number`。
- 低价/特价机票传 `--low-price`。
- 日期、人数、位置、偏好、星级、座席、亲子、早餐等修饰信息全部放入 `--extra`。

缺参时只询问关键缺失参数，不要调用错误脚本兜底。

规划类意图：

- 用户说“规划行程 / 玩几天 / 三日游 / 自由行安排”时，使用一次 `scripts/travel-query.js`。
- 不要拆成酒店、景点、火车三个脚本分别调用；`travel-query.js` 会把多类结果汇总到一个 Markdown 和一个 HTML 文件中。
