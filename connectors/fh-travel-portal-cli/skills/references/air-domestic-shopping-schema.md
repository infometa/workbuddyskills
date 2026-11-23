# 国内机票 shopping 字段字典

> 加载时机：`domestic_shopping` 返回字段与页面 FL/RR/CC 对不上，或要扩展页面列时。
> 查询出页默认读 [`air-domestic-oneway-page.md`](air-domestic-oneway-page.md)，不必先读本文件。
> 本文件是 `domestic_shopping` 返回结构的权威字典；字段类型以实际返回为准。

## 一、domestic_shopping 请求参数

```json
{
  "searchParams": {
    "airLegs": [{ "fromCity": "CSX", "toCity": "CTU", "flyDate": "2026-09-03" }],
    "journeyType": 0,          // 0=单程  1=往返(推荐往返,airLegs 放去程+返程两段)
    "passengerNum": 1,
    "official": true,          // 关键:因公口径,否则 enterpriseId 全空
    "sortBy": "DEPARTURE_TIME",
    "withCabinRules": true,        // 带舱位规则
    "needRefundChangeRule": false  // 须显式 false：shopping 不带退改文案；页内点退改补查。不传则 Java 仍会开退改
  }
}
```

- 城市码用 `air_city`（`scope=DOMESTIC`）解析，取本轮返回的 `code`。
  **有聚合码就用**（如成都 `CTU1`、北京 `BJS1`），shopping 会带出该城市全部机场，页面才能做机场分布；
  **没有就用三字码**（如 `CTU`/`PEK`），禁止把三字码改写成 `CTU1`。
- 往返(`journeyType=1`)时 `airLegs` 放两条：去程 + 返程，只发起一次 shopping。
- **official=false（缺省/因私）**：所有舱位 `enterpriseId` 为空，无法展示协议价标签。国内分析页必须传 `official=true`。

## 二、返回大结构（三层信封 + 顶层 key）

一条龙落盘的 `shopping.json` 是完整 JSON-RPC，打开就是：

```
jsonrpc / id
└─ result
   ├─ content[0].text     指引信封（kind/ok/summary），没有航班
   ├─ isError
   └─ structuredContent   业务在这里
      ├─ serialNumber
      ├─ flightList
      ├─ airways / types / citys
      ├─ policyDescList / policyDocumentList
```

拆封用 `scripts/unwrap_content.py`，不要自写 unwrap。

- `airways`/`types`/`citys` 是 `flightList` 的关联字典表，页面用它把航司二字码、机型码、
  机场 IATA 映射成中文名，不是业务结果。
- 响应可能很大：不要整份读进大模型的上下文，按本字典 + 对应脚本按需加载；用本轮工具
  返回（stdin 或本轮落盘文件路径均可），不要去磁盘翻历史结果文件。

## 三、flightList 的三种形态（最关键的区分）

`flightList` 每项是 `{ flightId, flight[] }`，`flight` 数组长度随场景变化，**三种形态长得像
但语义完全不同**，先按此表判形态再取字段：

| journeyType | 场景 | `flight[]` 长度 | 每段 `cabins` | 判定特征 |
|---|---|---|---|---|
| 0 单程 | 直飞 | 1 | 多个舱位 | `airLine` 单一 A→B |
| 0 单程 | 中转/经停 | ≥2 | 每段多个舱位 | 首段 A→X、末段 X→B（同向衔接）；`goMore=True` |
| 1 往返 | 去×回组合 | 2 | **每段 1 个舱位** | 段0 A→B、段1 B→A（对向）；两段共用同一 `cabId` |

- **单程中转 vs 往返都是 2 段**，靠 `airLine` 方向区分：中转是同向接力（PEK→TFU→XNN），
  往返是对向（PEK→XNN / XNN→PEK）。不能靠段数或 `stop` 判断。
- **往返每段只 1 个舱位**，是「去程舱位 × 返程舱位」的固定组合价；`normalPrice` 恒 0，
  `serialNumber` 前缀 `back…`。含税总价 = 去程(price+acf+baf) + 返程(price+acf+baf)。
- 单程中转的各段舱位独立，每段各有退改/行李；总价需逐段累加，不是单段价相加。

## 四、航段(flightList[].flight[]) 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 恒 0，无业务意义 |
| `flightId` | str | 航班号,前 2 字母为航司二字码(匹配 airways.companyNo) |
| `airLine` | str | **前3位=起飞机场 IATA,后3位=到达机场 IATA**(如 PEKXNN/PEKTFU/TFUXNN/PKXXNN) |
| `flyDate` / `arrDate` | str | `YYYY-MM-DD HH:MM:SS` |
| `type` | **str** | 机型代码(如 "320"/"32Z"/"319";查 types.type,它是字符串不是数字) |
| `meal` / `mealCode` | str | 餐食描述/代码(样本常为空) |
| `stop` | int | 经停点数量;样本直飞/中转均 0,中转不靠它表达(靠 flight[] 多段) |
| `stopCityCode`/`stopFlyDate`/`stopArrDate` | str | 经停城市码/起降时间(有经停时非空) |
| `fromPort` / `toPort` | str | 起降航站楼(T1/T2/T3,可能为空) |
| `fullPrice` | num | Y 舱全价票价(算折扣基准,非现价) |
| `shareId` | str | 代码共享航班号,空=无 |
| `baf` | int | **燃油附加费**(航班级,同航班所有舱位相同) |
| `acf` | int | **机场建设费**(航班级,同航班所有舱位相同) |
| `onTime` | **str** | 准点率(如 "100.0"/"93.0",中转段可为空串) |
| `mile` | num | 里程 |
| `cabins` | list | 舱位列表(见下) |

**含税价 = `price` + `acf` + `baf`**。`acf`/`baf` 挂在航段上（不在舱位上），同航班所有
舱位共用，页面据此算含税总价；不要把 `price` 当成含税价。

**多变机场侧推断**:只对每项 `flightList` 的**首段**收集起飞机场、**末段**收集到达机场
（中转中间段如 TFUXNN 的前 3 位 TFU 会污染"出发机场"集合，必须排除）。集合更大的
一侧即「多变侧」，页面把该侧机场名作为卡片维度。例:BJS1→XNN 直飞+中转混合,首段出发
{PEK,PKX}、末段到达 {XNN} → 出发侧多变。

## 五、舱位(cabins[]) 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `cab` | str | 舱位代码(字母,如 V/Z/Y/F/P) |
| `cabId` | str | 舱位标识；选择接口回传，页面不展示(往返去返程共用) |
| `cabClass` | str | 舱位大类(如 "Y1"/"Y") |
| `cabName` | str | 等级名(经济舱/公务舱等) |
| `price` | num | 现价(<=0 视为无票,生成页过滤);不含税费 |
| `normalPrice` | num | 门市价(高于现价时显示划线价;往返恒 0) |
| `source` | str | 来源编码；页面用来标代购，不要向用户解释渠道 |
| `enterpriseId` | str | **非空=协议价**；页面只显示「协议价」标签，不展示原文 |
| `num` | str/num | **库存编码:数字 1–8 或字母 A**(A 按业务显示 9 位) |
| `goMore` | bool | 多段/联程标记,中转段 True |
| `luggage` | str | 行李全文(与 baggage.luggage 同) |
| `weight` | str/num | 免费托运额(kg,冗余字段) |
| `portableWeight` | str | 随身行李重量(kg) |
| `refund` / `change` / `issue` | str | 退票/改签/出票规则全文(与 rule.*Text 内容一致) |
| `noMeal` | str | 无餐食标记 |
| `productName` / `productLabel` | str | 销售限制产品名/标签 |
| `adultLimit` / `ageLimit` / `passengerCertLimit` | str | 人数/年龄/证件限制 |
| `pickUpRemark` / `vipLoungeRemark` / `wifiRemark` | str | 接送/贵宾厅/wifi 说明 |
| `flightDelayInsuranceRemark` / `flightAccidentInsuranceRemark` | str | 航延险/航意险说明 |
| `rule` | obj | 见下 |
| `baggage` | obj | 见下 |

### rule（退改规则对象）

```json
{ "refundText": "退票全文", "changeText": "改签全文", "issueText": "出票规则全文" }
```

### baggage（结构化行李）

```json
{
  "luggage": "行李全文",
  "checkBaggage": { "weight": 20, "size": "40×60×100CM", "number": 1 },
  "carryBaggage": { "weight": 5,  "number": 1, "size": "20×40×55CM" }
}
```
`checkBaggage.number` 字段不总是出现（单程样本缺、往返样本有），取用时须容错。

## 六、生成页面内嵌数据(HTML 内 var FL/RR/CC)

> 本节是渲染脚本产出、供页面 JS 消费的中间结构，**不是 shopping 返回**；只在前端层
> 对不上时才参考。

### FL(每个航班一项,按出发时间排序)

```json
{
  "no": "CZ5975", "air": "南方航空",
  "dep": "07:30", "arr": "09:25",
  "apt": "天府",            // 多变机场侧展示名(双流/天府 或 首都/大兴 …)
  "ac": "空客320",          // 机型名(types 映射,未知显示原始码)
  "meal": "早餐",
  "cabins": [
    { "cab": "V", "cn": "经济舱", "price": 400, "np": 460,
      "w": "20", "ent": "DK1303590",   // 空串=非协议价
      "n": "A",                        // 库存编码原样保留
      "cabId": "...", "k": "...",      // 选择接口；不展示
      "rfi": 12, "cci": 8 }            // 退改规则在 RR/CC 的下标;-1=无
  ]
}
```

### RR / CC(退票 / 改签规则表)

- 文本按**内容指纹去重**（`\r\n` 已归一为 `\n`），避免同一规则在页里重复膨胀。
- 舱位经 `rfi/cci` 引用;同一航班同舱字母可能有多行(协议/非协议价规则不同),弹层用按钮
  `data-rk="<航班号>#<舱位行下标>"` 精确定位,避免串行。

## 七、常见数据坑

1. 因私数据无协议价 → 一律用 official:true。
2. `price<=0` 的舱位是占位/无票,生成页已过滤;KPI「最低价」取首个(排序后)舱位价。
3. 机型代码可能在 types 中缺失(如 31D/322),页面直接显示原始机型码,无需补查。
4. 退改规则文本含 `\r\n`,直接全文去重会把同一规则拆成多条 → 先归一换行再入表。
5. 卡片「(+1)」= 次日凌晨到达(由 arr 时刻 < dep 时刻判断),勿当作经停。
6. 中转/多段航班 `flightList[].flight` 有多项,**每段各有自己的 `cabins`**。统计舱位数、
   找最低价、数协议舱都必须遍历所有段;只取 `flight[0]` 会漏掉后续段,且总价不是单段价相加。
7. `type` 和 `onTime` 都是**字符串**不是数字(`"320"`/`"100.0"`),直接当数字算会出错;
   `onTime` 中转段可能是空串。
8. 含税价 = `price` + `acf` + `baf`,税费在**航段**上不在舱位上;往返含税总价是两段之和。
