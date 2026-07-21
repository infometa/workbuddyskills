## 场景四：路径规划

使用腾讯地图 Web 服务 API 通过 shell curl 规划不同出行方式的路线。支持步行、驾车、骑行（自行车）、电动车、公交等多种出行方式。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。

### API 端点

| 出行方式     | API 端点                                              |
| ------------ | ----------------------------------------------------- |
| 步行         | `https://apis.map.qq.com/ws/direction/v1/walking/`    |
| 驾车         | `https://apis.map.qq.com/ws/direction/v1/driving/`    |
| 骑行（自行车）| `https://apis.map.qq.com/ws/direction/v1/bicycling/` |
| 电动车       | `https://apis.map.qq.com/ws/direction/v1/ebicycling/` |
| 公交         | `https://apis.map.qq.com/ws/direction/v1/transit/`    |

### 通用参数

| 参数     | 说明                             | 必填 | 示例                      |
| -------- | -------------------------------- | ---- | ------------------------- |
| `key`    | 腾讯地图 Web Service Key         | 是   | `YOUR_KEY`                |
| `from`   | 起点坐标（纬度,经度）            | 是   | `39.90923,116.397428`     |
| `to`     | 终点坐标（纬度,经度）            | 是   | `39.903719,116.427281`    |
| `output` | 输出格式                         | 否   | `json`                    |

**坐标格式：** 腾讯地图使用 `纬度,经度` 格式（如 `39.90923,116.397428`），与高德地图的 `经度,纬度` 相反。

### 使用方法

**步行路线：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/walking/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&output=json"
```

**驾车路线：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/driving/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&output=json"
```

**驾车路线（带途经点和策略）：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/driving/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&waypoints=39.910000,116.410000&policy=LEAST_TIME&output=json"
```

**骑行路线（自行车）：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/bicycling/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&output=json"
```

**电动车路线：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/ebicycling/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&output=json"
```

**公交路线：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/transit/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&output=json"
```

**公交路线（带策略）：**

```bash
curl -s "https://apis.map.qq.com/ws/direction/v1/transit/?key=YOUR_KEY&from=39.90923,116.397428&to=39.903719,116.427281&policy=LEAST_TRANSFER&output=json"
```

### 驾车专有参数

| 参数           | 说明                         | 示例                            |
| -------------- | ---------------------------- | ------------------------------- |
| `waypoints`    | 途经点坐标，多个用 `;` 分隔  | `39.91,116.41;39.92,116.42`     |
| `policy`       | 驾车策略                     | `LEAST_TIME`                    |
| `plate_number` | 车牌号，用于避开限行         | `京A12345`                      |

**驾车策略（policy）：**

- `LEAST_TIME` — 时间最短（默认）
- `LEAST_FEE` — 少收费
- `AVOID_HIGHWAY` — 不走高速
- `HIGHWAY_FIRST` — 高速优先

### 公交专有参数

| 参数             | 说明                    | 示例              |
| ---------------- | ----------------------- | ----------------- |
| `policy`         | 公交策略                | `LEAST_TIME`      |
| `departure_time` | 出发时间（Unix 时间戳） | `1700000000`      |

**公交策略（policy）：**

- `LEAST_TIME` — 时间短（默认）
- `LEAST_TRANSFER` — 少换乘
- `LEAST_WALKING` — 少步行
- `RECOMMEND` — 推荐策略

### 返回数据说明

**步行 / 骑行 / 电动车 / 驾车返回：**

```json
{
  "status": 0,
  "message": "query ok",
  "result": {
    "routes": [
      {
        "distance": 3200,
        "duration": 40,
        "steps": [...]
      }
    ]
  }
}
```

**公交返回：**

```json
{
  "status": 0,
  "message": "query ok",
  "result": {
    "routes": [
      {
        "distance": 5000,
        "duration": 35,
        "steps": [...]
      }
    ]
  }
}
```

| 字段                  | 说明                           |
| --------------------- | ------------------------------ |
| `distance`            | 路线总距离，单位：米           |
| `duration`            | 预计耗时，单位：分钟           |
| `toll`                | 过路费（驾车），单位：元       |
| `traffic_light_count` | 红绿灯数量（驾车）             |
| `steps`               | 详细步骤数组                   |

### 错误处理

- `status` 不为 `0` 时表示请求失败，`message` 字段包含错误原因
- 常见错误：Key 无效、配额不足、坐标格式错误、起终点太近或太远
