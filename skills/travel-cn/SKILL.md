---
name: travel-cn
description: 旅行信息查询 - 去哪儿/携程/飞猪数据查询（Expedia 中国版）
description_zh: "聚合去哪儿、携程、飞猪，查机票、酒店、火车票、景点门票"
description_en: "Search flights, hotels and train tickets via Qunar, Ctrip and Fliggy"
version: 1.0.0
allowed-tools: Bash,Read
metadata:
  openclaw:
    emoji: "✈️"
    category: "travel"
    tags: ["travel", "qunar", "ctrip", "fliggy", "china", "booking"]
---

# 旅行信息查询

去哪儿/携程/飞猪数据查询。

## 功能

- ✈️ 机票查询
- 🏨 酒店预订
- 🚄 火车票
- 🎫 景点门票
- 📅 行程规划

## 平台对比

| 平台 | 机票 | 酒店 | 火车 | 特点 |
|------|-----|------|------|------|
| **携程** | ✅ | ✅ | ✅ | 全能 |
| **去哪儿** | ✅ | ✅ | ✅ | 比价 |
| **飞猪** | ✅ | ✅ | ❌ | 阿里系 |
| 12306 | ❌ | ❌ | ✅ | 官方 |

## 机票查询

### 携程 API

```bash
# 需要合作伙伴资质
curl "https://api.ctrip.com/flight/search?from=SHA&to=PEK&date=2026-02-20"
```

### 爬虫方案

```python
# 使用 selenium
pip install selenium

from selenium import webdriver
driver = webdriver.Chrome()
driver.get("https://flight.qunar.com/")
```

## 酒店查询

### 携程 API

```bash
curl "https://api.ctrip.com/hotel/search?city=上海&checkin=2026-02-20"
```

## 火车票查询

### 12306（官方）

```bash
# 使用 12306 API 封装
pip install py12306

from py12306 import Py12306
client = Py12306()
trains = client.query("上海", "北京", "2026-02-20")
```

## 使用场景

### 1. 商务出行

- 机票/酒店比价
- 行程优化
- 费用控制

### 2. 旅行规划

- 景点推荐
- 路线规划
- 预算管理

### 3. 价格监控

- 降价提醒
- 价格趋势
- 最佳购买时机

## 快速脚本

```bash
# 查询机票
./scripts/flight-search.sh --from 上海 --to 北京 --date 2026-02-20

# 查询酒店
./scripts/hotel-search.sh --city 上海 --checkin 2026-02-20

# 查询火车票
./scripts/train-search.sh --from 上海 --to 北京 --date 2026-02-20
```

## 注意事项

1. **API 限制**: 需要合作伙伴资质
2. **爬虫风险**: 可能被封 IP
3. **价格变化**: 实时波动

---

*版本: 1.0.0*
