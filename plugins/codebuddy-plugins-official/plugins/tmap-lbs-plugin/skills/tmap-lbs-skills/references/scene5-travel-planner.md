## 场景五：智能旅游规划

用户想去某个城市旅游，提供了多个想去的景点，需要规划最佳行程路线，并可选推荐餐厅、酒店等。需要先通过地理编码 API 获取各景点的经纬度，再拼接旅游规划链接。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。
**返回步骤** 严格按照下面的步骤，获取到经纬度后，直接拼接成旅游规划链接，返回给用户，规划链接里会做具体的路线规划和周边的搜索，不需要单独调用路线规划接口和搜索接口

### 执行步骤

#### 第一步：解析用户输入

从用户输入中拆分出以下要素：

- **景点列表**：用户想去的具体地点（如"故宫"、"颐和园"、"香山"、"环球影城"）
- **推荐类型**（可选）：用户是否需要推荐餐厅、酒店等（如"推荐餐厅和酒店"）

| 用户输入                                 | 景点列表             | 推荐类型         |
| ---------------------------------------- | -------------------- | ---------------- |
| 我想去北京玩，想去故宫、颐和园、香山     | 故宫、颐和园、香山   | 无               |
| 去上海玩，外滩、南京路、城隍庙，推荐酒店 | 外滩、南京路、城隍庙 | hotel            |
| 去杭州，西湖、灵隐寺，推荐餐厅和酒店     | 西湖、灵隐寺         | restaurant,hotel |

#### 第二步：检查 API Key

- 如果用户之前未提供过 Key，**先提示用户提供腾讯地图 API Key**，等待用户回复后再继续
- 如果用户已提供 Key，直接使用

**请求 Key 的回复模板：**

```
🔑 规划旅游行程需要使用腾讯地图 API，请提供你的腾讯位置服务 API Key。

（如果还没有 Key，可以在 https://lbs.qq.com 注册并创建应用获取）
```

#### 第三步：逐个调用地理编码 API 获取各景点经纬度

对景点列表中的**每一个景点**，调用地理编码 API 获取其经纬度。

**API 格式：**

```
https://apis.map.qq.com/ws/geocoder/v1?policy=1&address={景点名称}&key={用户的key}
```

**执行 curl 请求（对每个景点都执行一次）：**

```bash
curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=故宫&key={用户的key}"
curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=颐和园&key={用户的key}"
```

**API 返回示例：**

```json
{
  "status": 0,
  "message": "query ok",
  "result": {
    "title": "故宫",
    "location": {
      "lng": 116.397026,
      "lat": 39.918058
    }
  }
}
```

从每个返回结果中提取 `result.location`，记录 `{name, lat, lng}`。

#### 第四步：拼接旅游规划链接

将所有景点的名称和坐标组装成 `spots` JSON 数组，拼接到旅游规划 URL 中。

**URL 格式：**

```
https://mapapi.qq.com/web/claw/travel.html?spots={spots_json}&recommend={推荐类型}&key={用户的key}
```

**参数说明：**

- **域名**：`mapapi.qq.com`
- **路由**：`/web/claw/travel.html`
- **参数**：
  - `spots` = JSON 数组，每个元素包含 `name`（景点名）、`lat`（纬度）、`lng`（经度）
  - `recommend`（可选）= 推荐类型，值为 `hotel`、`restaurant` 或 `restaurant,hotel`

**spots 参数格式：**

```json
[
  { "name": "故宫", "lat": 39.918, "lng": 116.397 },
  { "name": "颐和园", "lat": 39.999, "lng": 116.275 },
  { "name": "香山", "lat": 39.993, "lng": 116.188 },
  { "name": "环球影城", "lat": 39.843, "lng": 116.681 }
]
```

> **注意：** spots 参数需要进行 URL 编码（encodeURIComponent），浏览器会自动处理。

#### 第五步：返回链接给用户

### 完整示例

**用户输入：** "我想去北京玩，想去故宫、颐和园、香山、环球影城，给我规划最佳行程路线，并推荐餐厅和酒店。"

1. 解析：景点列表 = `故宫、颐和园、香山、环球影城`，推荐类型 = `restaurant,hotel`
2. 调用地理编码 API（每个景点各调一次）：
   ```bash
   curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=故宫&key=xxx"
   curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=颐和园&key=xxx"
   curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=香山&key=xxx"
   curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&address=环球影城&key=xxx"
   ```
3. 获取各景点坐标：
   - 故宫：`{lat: 39.918, lng: 116.397}`
   - 颐和园：`{lat: 39.999, lng: 116.275}`
   - 香山：`{lat: 39.993, lng: 116.188}`
   - 环球影城：`{lat: 39.843, lng: 116.681}`
4. 拼接链接：
   ```
   https://mapapi.qq.com/web/claw/travel.html?&spots=[{"name":"故宫","lat":39.918,"lng":116.397},{"name":"颐和园","lat":39.999,"lng":116.275},{"name":"香山","lat":39.993,"lng":116.188},{"name":"环球影城","lat":39.843,"lng":116.681}]&recommend=restaurant,hotel&key={用户的key}
   ```

**重要** 完成这一步后，不需要再调用路线规划接口和搜索接口，直接返回给用户，规划链接里会做具体的路线规划和周边的搜索

### 回复模板

```
🗺️ 已为你规划好旅游行程！以下是各景点的坐标信息：

| 景点 | 纬度 | 经度 |
| ---- | ---- | ---- |
| 故宫 | 39.918 | 116.397 |
| 颐和园 | 39.999 | 116.275 |
| 香山 | 39.993 | 116.188 |
| 环球影城 | 39.843 | 116.681 |

📍 点击下方链接查看最佳行程路线规划：

https://mapapi.qq.com/web/claw/travel.html?spots=[{"name":"故宫","lat":39.918,"lng":116.397},{"name":"颐和园","lat":39.999,"lng":116.275},{"name":"香山","lat":39.993,"lng":116.188},{"name":"环球影城","lat":39.843,"lng":116.681}]&recommend=restaurant,hotel&key={用户的key}

地图会为你智能规划最佳游览顺序，并推荐沿途的餐厅和酒店 🎉，同时直接预览这个网页。
```
