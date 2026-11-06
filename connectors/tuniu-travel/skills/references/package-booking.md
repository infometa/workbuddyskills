# 打包订 (package-booking)

**触发词**：打包订、组合预订、一起订、机酒、酒火、机票酒店门票一起订。

**工具链路**：`package_booking_create` →（展示清单并取得确认）→ `package_booking_submit`

参数详情：`tuniu help package-booking <tool>`

## 下单参数红线（非常重要）

> 下文调用模板中的示例 sessionId、姓名/证件号/手机号等**仅为格式示范**；实际提交时必须替换为**真实值**。

1. **create 阶段**：`resourceSpecs` 中的精确 ID（`hotelId`/`roomId`/`flightNo`/`trainNo`/`priceInfoId` 等）须来自对应单品查询结果或用户明确指定，禁止编造；`packageSessionId` 仅由 create 返回，不能预设。
2. **submit 阶段**：`packageSessionId` 必须来自**本轮** `package_booking_create` 返回；用户变更日期/人数/资源偏好后须重新 create，禁止复用旧 session。
3. **用户信息必须真实**：`travelerCommitment` / `commitment` 中的姓名、证件号、手机号须为用户确认提供的真实出游人/联系人信息，禁止虚构；`confirmedByUser=true` 表示用户已确认组合与资料，不能空传。
4. **非幂等**：create/submit 失败或结果不明时不要盲目重试；仅当返回 `orderResult.orderId` 才视为下单成功。

## 调用模板

```bash
# 创建组合清单（不会下单）
tuniu call package-booking package_booking_create --source <source> -a '{
  "baseInfo": {
    "startCityName": "南京",
    "destCityName": "北京",
    "departDate": "2026-10-10",
    "returnDate": "2026-10-13",
    "adultCount": 1,
    "childCount": 0
  },
  "resourceSpecs": [
    {
      "resourceType": "FLIGHT",
      "flight": {
        "startCityName": "南京",
        "destCityName": "北京",
        "journeyScope": "ROUND_TRIP",
        "cabinType": "ECONOMY",
        "internationalFlag": "DOMESTIC"
      }
    },
    {
      "resourceType": "HOTEL",
      "hotel": {
        "day": [1, 2, 3],
        "destCityName": "北京"
      }
    }
  ]
}'

# 提交订单（须用户确认后）
tuniu call package-booking package_booking_submit --source <source> -a '{
  "packageSessionId": "BS6NH32N31EUPS",
  "confirmedByUser": true,
  "travelerCommitment": {
    "manualTravelers": [
      {
        "name": "张三",
        "idType": "身份证",
        "idNumber": "310101199001011234",
        "mobile": "13800138000",
        "passengerType": "ADULT"
      }
    ],
    "contactTourist": {
      "name": "张三",
      "mobile": "13800138000"
    }
  }
}'
```

## 独有规则（红线）

### 打包订创建约束

1. **至少两类资源**：必须有出发/目的城市；显式传至少两类 `resourceSpecs`；不要依赖服务端默认组合。
2. **显式传 `resourceSpecs`**：至少两类不同 `resourceType`（`HOTEL`/`FLIGHT`/`TRAIN`/`TICKET`）。
3. **不要同时放 `FLIGHT` 和 `TRAIN`**，除非用户明确要求。
4. **create 是组合清单生成器**：成功后必须展示资源与价格，等待确认后再 submit；**同一轮不得自动 submit**。
5. **精确 ID** 应来自资源查询结果，不要编造。
6. **非幂等**：失败或超时不要盲目重试；保留 `traceId`。

### 打包订提交约束

1. **`packageSessionId` 必须来自本轮 create**；不要用示例、日志或用户随口编号。
2. **`confirmedByUser` 必须为 `true`**；推荐传 `travelerCommitment`（不能只传 sessionId + `confirmedByUser`）。
3. `travelerCommitment` 与 `commitment` 最多传一个。
4. 变价时须展示新价格且用户明确接受后，才传 `confirmedPriceChange=true`。
5. 用户改变日期/人数/资源偏好后，应重新 create，不要复用旧 sessionId。
6. **非幂等**：超时或结果不明**不要再次提交**；**仅当存在 `orderResult.orderId` 才视为下单成功**。

### 订单结果判断

| 情况 | 处理 |
|------|------|
| 存在 `data.orderResult.orderId` | 展示订单号与 `payUrl`，提醒支付；**不再**调用 submit |
| 含 `MISSING_FIELDS` | 让用户补资料后重新确认再提交 |
| `UPSTREAM_BUSINESS_ERROR` | 展示错误并停止；若带 `orderId` 先核实状态 |
| 结果不明确 | 保留 `traceId`，提示联系客服，**不要再次提交** |

列表无 `package-booking` 时先 `tuniu discovery refresh && tuniu discovery list`。

## 场景示例

**用户**：南京到北京，9月10到13号，往返机票和酒店一起订

```bash
tuniu call package-booking package_booking_create --source <source> -a '{"baseInfo":{"startCityName":"南京","destCityName":"北京","departDate":"2026-10-10","returnDate":"2026-10-13","adultCount":1},"resourceSpecs":[{"resourceType":"FLIGHT","flight":{"startCityName":"南京","destCityName":"北京","journeyScope":"ROUND_TRIP","cabinType":"ECONOMY","internationalFlag":"DOMESTIC"}},{"resourceType":"HOTEL","hotel":{"day":[1,2,3],"destCityName":"北京"}}]}'
```

**后续**：展示资源与总价 → 用户确认组合与出游人资料后，再 `package_booking_submit`（`confirmedByUser=true`）。
