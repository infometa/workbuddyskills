---
name: weather-open-meteo
version: 0.1.7
description: "通过 open-meteo.com 公共 API 查询指定地点的当前天气和未来预报，无需 API key；当 open-meteo 请求失败时可降级使用 wttr.in。"
homepage: https://open-meteo.com/
metadata:
  openclaw:
    emoji: "\U0001F324️"
    requires:
      bins:
        - curl
        - jq
display_name: "天气查询"
display_name_en: "Weather (Open-Meteo)"
description_zh: "基于 Open-Meteo 公共 API 查询全球任意地点的当前天气与未来 7 天预报，无需 API Key；支持城市名或经纬度查询，Open-Meteo 请求失败时自动降级到 wttr.in。"
description_en: "Query current weather and 7-day forecast for any location worldwide via the free Open-Meteo API (no API key). Supports city name or coordinates, with automatic fallback to wttr.in."
visibility: "public"
---

# Weather Open‑Meteo Skill

本 skill 通过查询 open‑meteo.com 公共 API 获取当前天气和简单预报。如果地理编码查询或天气请求失败，可降级使用 **wttr.in** 作为轻量替代方案。

## 📌 适用范围与注意事项
* 本 skill **依赖** `curl` **和** `jq`。
* 地点参数在发送给 API 前会先做编码。
* 下方示例演示了如何使用 jq @uri 安全地构造查询。

## ✅ 使用场景
✔ 用户询问某地的天气、预报、气温或降雨概率。
✖ 不适用于历史数据、灾害预警或详细气候分析。

## 📋 命令
本 skill 接受单个参数：地点名称（城市、地区，或 `lat,lon` 格式的坐标）。

## Open‑Meteo（主用，JSON）

**地理编码**（获取地点坐标）：

```bash
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Beijing&count=1" | jq '.results[0] | {name, latitude, longitude}'
```

**当前天气**（按坐标查询）：

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=39.91&longitude=116.40&current_weather=true" | jq '.current_weather'
```

**7 天预报**（按坐标查询）：

```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=39.91&longitude=116.40&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=7" | jq '.daily'
```

**JSON 返回示例**

```json
{
  "latitude": 39.91,
  "longitude": 116.40,
  "current_weather": {
    "temperature": -5.3,
    "windspeed": 3.9,
    "winddirection": 200,
    "weathercode": 80,
    "time": "2024-02-18T14:00"
  }
}
```

📖 [Open‑Meteo API 文档](https://open-meteo.com/en/docs)

## wttr.in（降级方案）

**一行查询**（HTML 文本）：

```bash
curl -s "https://wttr.in/Beijing?format=3"
```

**紧凑纯文本**：

```bash
curl -s "https://wttr.in/Beijing?format=1"
```

**PNG 图片**（用于终端或嵌入）：

```bash
curl -s -o beijing.png "https://wttr.in/Beijing.png"
```

## 📚 示例（用户提问）
> **用户：** *北京现在天气怎么样？*
> **助手：**
> `北京当前天气：🌤️ +10 °C，20% 降雨概率`

## Tips（小贴士）

- **对城市名做 URL 编码**（中文或含空格的城市名尤其需要）：
  ```bash
  curl -s "https://geocoding-api.open-meteo.com/v1/search?name=$(echo 北京 | jq -sRr @uri)"
  ```
- **用 `jq`** 动态构造查询：
  ```bash
  city="北京"
  lat=$(curl -s "https://geocoding-api.open-meteo.com/v1/search?name=$(echo $city | jq -sRr @uri)" | jq -r '.results[0].latitude')
  lon=$(curl -s "https://geocoding-api.open-meteo.com/v1/search?name=$(echo $city | jq -sRr @uri)" | jq -r '.results[0].longitude')
  ```
- 如果已知 `latitude` 和 `longitude`，可直接传入。
- API 有速率限制（约 100 次/分钟）。请缓存结果或控制调用间隔。
