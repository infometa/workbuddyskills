## 场景二：基于位置的周边或者附近搜索

用户想搜索**某个位置周边或者附近**的某类地点。需要先通过地理编码 API 获取该位置的经纬度，再拼接带坐标的搜索链接。

**前置条件：** 需要用户提供腾讯位置服务的 API Key。
**注意** 严格按照下面的步骤，不要生成代码后者调取其他脚本后者接口

### 执行步骤

#### 第一步：解析用户输入

从用户输入中拆分出两个要素：

- **位置**：用户指定的中心位置（如"西直门"、"北京南站"）
- **搜索类别**：要搜索的内容（如"美食"、"酒店"）

| 用户输入             | 位置     | 搜索类别 |
| -------------------- | -------- | -------- |
| 西直门周边美食       | 西直门   | 美食     |
| 北京南站附近酒店     | 北京南站 | 酒店     |
| 天坛周边有什么好吃的 | 天坛     | 美食     |

#### 第二步：检查 API Key

- 如果用户之前未提供过 Key，**先提示用户提供腾讯地图 API Key**，等待用户回复后再继续
- 如果用户已提供 Key，直接使用

**请求 Key 的回复模板：**

```
🔑 搜索「{位置}」周边的{搜索类别}需要使用腾讯地图 API，请提供你的腾讯位置服务 API Key。

（如果还没有 Key，可以在 https://lbs.qq.com 注册并创建应用获取）
```

#### 第三步：调用地理编码 API 获取经纬度

**API 格式：**

```
https://apis.map.qq.com/ws/geocoder/v1?policy=1&location={位置}&key={用户的key}
```

**执行 curl 请求：**

```bash
curl -s "https://apis.map.qq.com/ws/geocoder/v1?policy=1&location={位置}&key={用户的key}"
```

**API 返回示例：**

```json
{
  "status": 0,
  "message": "query ok",
  "result": {
    "title": "西直门",
    "location": {
      "lng": 116.353138,
      "lat": 39.939385
    }
  }
}
```

从返回结果中提取 `result.location`，格式为 `{lat, lng}`（注意：腾讯地图坐标格式为 纬度,经度）

#### 第四步：拼接带坐标的搜索链接

**URL 格式：**

```
https://mapapi.qq.com/web/claw/nearby-search.html?center={纬度},{经度}&keyword={搜索类别}&radius=1000&key={用户的key}
```

- **域名**：`map.qq.com`
- **路由**：`/m/place/search`
- **参数**：
  - `keyword` = 搜索类别（如"美食"）
  - `center` = 纬度,经度
  - `radius` = 搜索范围（单位：米，默认 1000）
  - `policy` = 1 (必要参数，不加的话需要 address 里需要带上城市，默认为 1)

#### 第五步：返回链接给用户

### 完整示例

**用户输入：** "搜索西直门周边美食"

1. 解析：位置 = `西直门`，搜索类别 = `美食`
2. 调用地理编码 API：`curl -s "https://apis.map.qq.com/ws/geocoder/v1/?policy=1&address=西直门&key=xxx"`
3. 获取坐标：`{lat: 39.939385, lng: 116.353138}`
4. 拼接链接：`https://mapapi.qq.com/web/claw/nearby-search.html?keyword=美食&center=39.939385,116.353138&radius=1000&key={用户的key}`

### 回复模板

```
📍 已查询到「{位置}」的坐标（{纬度},{经度}），为你生成周边{搜索类别}的搜索链接：

https://mapapi.qq.com/web/claw/nearby-search.html?center={纬度},{经度}&keyword={搜索类别}&radius=1000&key={用户的key}

点击链接即可查看「{位置}」周边 1 公里内的{搜索类别}，同时直接预览这个网页。
```
