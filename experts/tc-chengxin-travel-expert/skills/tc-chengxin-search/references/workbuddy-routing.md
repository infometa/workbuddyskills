# 专家业务路由

| 意图 | 典型说法 | 脚本 |
| --- | --- | --- |
| 机票 | 北京到上海机票、明天飞广州、特价机票 | `scripts/flight-query.js` |
| 火车票 | 北京到上海高铁、苏州到南京火车票 | `scripts/train-query.js` |
| 酒店 | 上海外滩附近酒店、北京五星级酒店 | `scripts/hotel-query.js` |
| 景区/门票 | 苏州园林、杭州亲子景点、迪士尼门票 | `scripts/scenery-query.js` |
| 汽车票 | 苏州到南京大巴、长途汽车票 | `scripts/bus-query.js` |
| 度假/行程 | 三亚自由行、云南旅游团、北京三日游 | `scripts/travel-query.js` |
| 综合交通 | 北京到上海怎么走、去苏州有哪些交通方式 | `scripts/traffic-query.js` |

明确业务用对应脚本；只问怎么走用 traffic-query.js。
规划每天怎么玩用 travel-query.js + --intent itinerary；仅比选跟团/度假产品用 --intent selection，intent 在包装器分隔符 -- 前。不能按响应改变用户目标。
行程先取 travel；缺交通、住宿、景点时由分析 Skill 用回执固化的 completionRequests 并发补查一次，不重新提槽，不按类别串行试查。
