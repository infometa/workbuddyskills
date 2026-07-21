## 场景三：POI 详细搜索

使用腾讯地图 Web 服务 API 通过 shell curl 进行 POI 搜索，支持关键词搜索、城市限定、周边搜索等。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。

### API 接口

```
GET https://apis.map.qq.com/ws/place/v1/search
```

### 参数说明

| 参数        | 说明                                       | 必填 | 示例                 |
| ----------- | ------------------------------------------ | ---- | -------------------- |
| `key`       | 腾讯地图 Web Service Key                   | 是   | `YOUR_KEY`           |
| `keyword`   | 搜索关键词                                 | 是   | `肯德基`             |
| `boundary`  | 搜索范围（城市或周边）                     | 是   | 见下方格式说明       |
| `page_index`| 页码，从 1 开始                            | 否   | `1`                  |
| `page_size` | 每页数量（最大 20）                        | 否   | `10`                 |
| `filter`    | 筛选条件                                   | 否   | `category=餐饮`      |
| `output`    | 输出格式                                   | 否   | `json`               |

**boundary 参数格式：**

- 城市搜索：`region(城市名,0)` — 例如 `region(北京,0)`，第二个参数 `0` 表示不自动扩大范围
- 周边搜索：`nearby(纬度,经度,半径)` — 例如 `nearby(39.90923,116.397428,1000)`

**注意：** 腾讯地图坐标格式为 `纬度,经度`（纬度在前，经度在后），与高德相反。

### 使用方法

**城市关键词搜索：**

```bash
curl -s "https://apis.map.qq.com/ws/place/v1/search?key=YOUR_KEY&keyword=肯德基&boundary=region(北京,0)&page_index=1&page_size=10&output=json"
```

**周边搜索（指定坐标和半径）：**

```bash
curl -s "https://apis.map.qq.com/ws/place/v1/search?key=YOUR_KEY&keyword=酒店&boundary=nearby(39.90923,116.397428,1000)&page_index=1&page_size=10&output=json"
```

**带分类筛选的搜索：**

```bash
curl -s "https://apis.map.qq.com/ws/place/v1/search?key=YOUR_KEY&keyword=餐厅&boundary=region(上海,0)&filter=category=餐饮&page_index=1&page_size=20&output=json"
```

### 返回数据格式

```json
{
  "status": 0,
  "message": "query ok",
  "count": 100,
  "data": [
    {
      "id": "...",
      "title": "肯德基(王府井店)",
      "address": "北京市东城区王府井大街...",
      "tel": "010-12345678",
      "category": "餐饮:快餐",
      "location": {
        "lat": 39.914,
        "lng": 116.410
      },
      "_distance": 500
    }
  ]
}
```

### 返回字段说明

| 字段        | 说明                       |
| ----------- | -------------------------- |
| `status`    | 状态码，`0` 表示成功       |
| `message`   | 状态说明                   |
| `count`     | 结果总数                   |
| `data`      | POI 结果数组               |
| `title`     | 地点名称                   |
| `address`   | 地址                       |
| `tel`       | 电话                       |
| `category`  | 分类                       |
| `location`  | 坐标 `{lat, lng}`          |
| `_distance` | 距中心点距离（周边搜索时） |

### 错误处理

- `status` 不为 `0` 时表示请求失败，`message` 字段包含错误原因
- 常见错误：Key 无效、配额不足、参数格式错误
