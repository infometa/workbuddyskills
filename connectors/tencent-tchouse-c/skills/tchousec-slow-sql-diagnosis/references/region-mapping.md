# TCHouse-C 地域映射表

## 说明

当用户在问题中提到地域的中文名称时，需要映射为对应的 `Region`（字符串）或 `RegionId`（数字）参数值传入云 API。部分接口使用 `Region` 字符串参数，部分接口使用 `RegionId` 数字参数，请根据具体接口要求选择。

用户可能使用"所属地区"或"地域名称"来描述，例如：
- "广州的集群" → `Region: ap-guangzhou` / `RegionId: 1`
- "华南地区的集群" → 可能是 `ap-guangzhou`、`ap-shenzhen` 等，需通过 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）确认具体地域
- "上海金融区" → `Region: ap-shanghai-fsi` / `RegionId: 7`

> ⚠️ **地域是否被 TCHouseC 支持，以云 API 运行时返回为准**。本表**不做**产品级支持地域白名单校验（业务新增地域时 skill 无需发版即可跟进）。若某个工具返回 `UnsupportedRegion` 错误码，说明该地域未开通 TCHouseC 产品，此时 Agent 必须按 [error-handling.md §1](./error-handling.md#1-unsupportedregion该接口不支持此地域访问) 的规则处理（**不重试、不自动切换地域、必须 `ask_user` 让用户确认**）。

## 工具传参形式速查

> ⚠️ **强制要求**：调用工具前必须查此表确定该工具期望的地域参数形式，不得凭记忆。若上下文只给了 `RegionId` 数字或只给了 `Region` 字符串，必须用下面的映射表补齐另一种形式后再调用。

| 工具（或工具族） | 传 `Region`（字符串） | 传 `RegionId`（数字） | 备注 |
|--------|:---------------------:|:---------------------:|------|
| `TCHouseCXxx` 系全部工具<br/>（如 DescribeInstance / InstanceNodes / InstanceShards / EventTasks / ClusterConfigs / RunningQuery / SlowQueryRecords / SlowQueryTrend / CkSqlApis / TableSchema / Spec / RegionZone / GoodsDetail 等） | ✅ | ❌ | 如 `Region: ap-guangzhou` |
| `BillingCalculatePrice`（询价） | ✅ | ❌ | 使用 `Region` 字符串，如 `ap-guangzhou` |
| `MonitorDescribeDashboardMetricData` | ✅ | ✅ | **两者都必传**，如 `Region: ap-beijing` + `RegionId: 8` |

**归纳规则**（记住这条即可覆盖 99% 场景）：
- **`TCHouseCXxx` 系 / `BillingCalculatePrice`**：**只传 `Region` 字符串**（如 `ap-guangzhou`）。若上下文只拿到 `RegionId` 数字，必须先按下方映射表转成字符串再调用。
- **`MonitorDescribeDashboardMetricData`（Monitor 产品）**：**同时传 `Region` 字符串 和 `RegionId` 数字**，缺一不可。

> 遇到本表未列出的新工具时，默认按"只传 `Region` 字符串"处理；若接口报参数错误，再查该工具的接口文档确认。

## 地域映射表

| RegionId | Region | 所属地区 | 地域名称 | 英文名称 | regionPrefix |
|----------|--------|----------|----------|----------|--------------|
| 1 | ap-guangzhou | 华南地区 | 广州 | South China (Guangzhou) | gz |
| 12 | ap-guangzhou-open | 华南地区 | 广州Open | South China (Guangzhou Open) | gzopen |
| 54 | ap-qingyuan | 华南地区 | 清远 | South China (Qingyuan) | qy |
| 73 | ap-qingyuan-xinan | 华南地区 | 清远信安 | South China (Qingyuan-Xinan) | qyxa |
| 77 | ap-shenzhen-sycft | 华南地区 | 深圳深宇财付通 | Shenzhen Sycft | szsycft |
| 37 | ap-shenzhen | 华南地区 | 深圳 | South China (Shenzhen) | szx |
| 11 | ap-shenzhen-fsi | 华南地区 | 深圳金融 | South China (Shenzhen Finance) | szjr |
| 4 | ap-shanghai | 华东地区 | 上海 | East China (Shanghai) | sh |
| 7 | ap-shanghai-fsi | 华东地区 | 上海金融 | East China (Shanghai Finance) | shjr |
| 33 | ap-nanjing | 华东地区 | 南京 | East China (Nanjing) | nj |
| 31 | ap-jinan-ec | 华东地区 | 济南 | East China (Jinan) | jnec |
| 32 | ap-hangzhou-ec | 华东地区 | 杭州 | East China (Hangzhou) | hzec |
| 34 | ap-fuzhou-ec | 华东地区 | 福州 | East China (Fuzhou) | fzec |
| 55 | ap-hefei-ec | 华东地区 | 合肥 | East China (Hefei) | hfeec |
| 8 | ap-beijing | 华北地区 | 北京 | North China (Beijing) | bj |
| 36 | ap-tianjin | 华北地区 | 天津 | North China (Tianjin) | tsn |
| 53 | ap-shijiazhuang-ec | 华北地区 | 石家庄 | North China (Shijiazhuang) | sjwec |
| 46 | ap-beijing-fsi | 华北地区 | 北京金融 | North China (Beijing Finance) | bjjr |
| 35 | ap-wuhan-ec | 华中地区 | 武汉 | Central China (Wuhan) | whec |
| 45 | ap-changsha-ec | 华中地区 | 长沙 | Central China (Changsha) | csec |
| 71 | ap-zhengzhou-ec | 华中地区 | 郑州 | Central China (ZhengZhou) | cgoec |
| 16 | ap-chengdu | 西南地区 | 成都 | Southwest China (Chengdu) | cd |
| 19 | ap-chongqing | 西南地区 | 重庆 | Southwest China (Chongqing) | cq |
| 56 | ap-shenyang-ec | 东北地区 | 沈阳 | Northeast China (ShenYang) | sheec |
| 57 | ap-xian-ec | 西北地区 | 西安 | Northwest China (XiAn) | xiyec |
| 58 | ap-xibei-ec | 西北地区 | 加速 | Northwest China | xbec |
| 39 | ap-taipei | 中国台北 | 台北 | Taipei, China | tpe |
| 5 | ap-hongkong | 中国香港 | 香港 | Southeast Asia (Hong Kong, China) | hk |
| 72 | ap-jakarta | 东南亚地区 | 雅加达 | Indonesia (Jakarta) | jkt |
| 9 | ap-singapore | 东南亚地区 | 新加坡 | Southeast Asia (Singapore) | sg |
| 23 | ap-bangkok | 亚太地区 | 曼谷 | Asia Pacific (Bangkok) | th |
| 18 | ap-seoul | 亚太地区 | 首尔 | Asia Pacific (Seoul) | kr |
| 25 | ap-tokyo | 亚太地区 | 东京 | Asia Pacific (Tokyo) | jp |
| 21 | ap-mumbai | 亚太南部 | 孟买 | South Asia Pacific (Mumbai) | in |
| 15 | na-siliconvalley | 美国西部 | 硅谷 | Western US (Silicon Valley) | usw |
| 22 | na-ashburn | 美东地区 | 弗吉尼亚 | Eastern US (Virginia) | use |
| 6 | na-toronto | 北美地区 | 多伦多 | North America (Toronto) | ca |
| 17 | eu-frankfurt | 欧洲地区 | 法兰克福 | Europe (Frankfurt) | de |
| 24 | eu-moscow | 欧洲地区 | 莫斯科 | Europe (Moscow) | ru |
| 74 | sa-saopaulo | 南美地区 | 圣保罗 | SouthAmerica (Saopaulo) | sao |

> 📌 **说明**：本表为业务系统整理的固定映射，所有 RegionId / Region 字段均为权威值，**无需通过 `DescribeRegionZone` 等 API 二次校验**。

## 映射规则

1. **精确匹配优先**：如果用户给出的地域名称能精确匹配到某一行的"地域名称"列，直接使用对应的 Region / RegionId 值
2. **所属地区模糊匹配**：如果用户只说了"华南地区"等大区名称，且该大区下有多个地域，需通过 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）让用户确认具体地域
3. **常见简称映射**：
   - "广州" / "GZ" → `ap-guangzhou` (1)
   - "上海" / "SH" → `ap-shanghai` (4)
   - "北京" / "BJ" → `ap-beijing` (8)
   - "深圳" / "SZ" → `ap-shenzhen` (37)
   - "新加坡" / "SG" → `ap-singapore` (9)
   - "香港" / "HK" → `ap-hongkong` (5)
   - "重庆" / "CQ" → `ap-chongqing` (19)
   - "成都" / "CD" → `ap-chengdu` (16)
   - "南京" / "NJ" → `ap-nanjing` (33)
4. **金融区识别**：用户提到"金融"、"金融区"、"金融云"时，优先匹配带 `-fsi` 后缀的地域
5. **无法确定时**：调用 `ask_user`（WorkBuddy 中为 `AskUserQuestion`）询问用户确认具体地域
6. **参数选择**：根据具体接口文档要求，选择传 `Region`（字符串）还是 `RegionId`（数字）

## 所属地区汇总

| 所属地区 | 包含的地域 |
|----------|-----------|
| 华南地区 | 广州、广州Open、清远、清远信安、深圳深宇财付通、深圳、深圳金融 |
| 华东地区 | 上海、上海金融、南京、济南、杭州、福州、合肥 |
| 华北地区 | 北京、天津、石家庄、北京金融 |
| 华中地区 | 郑州、武汉、长沙 |
| 西南地区 | 成都、重庆 |
| 西北地区 | 西安、加速 |
| 东北地区 | 沈阳 |
| 东南亚地区 | 雅加达、新加坡 |
| 亚太地区 | 曼谷、首尔、东京 |
| 亚太南部 | 孟买 |
| 美国西部 | 硅谷 |
| 美东地区 | 弗吉尼亚 |
| 北美地区 | 多伦多 |
| 欧洲地区 | 法兰克福、莫斯科 |
| 南美地区 | 圣保罗 |
| 中国香港 | 香港 |
| 中国台北 | 台北 |
