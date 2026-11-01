# 差旅标准查询接口参考

本文档说明差标查询工具的入参、返回字段和失败情形。

---

## ziru_travel_standard — 差标查询

查询当前用户的差旅标准。

### 入参

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `businessType` | string | 否 | 业务类型：`flight`（机票）/ `train`（火车票）/ `hotel`（酒店）。为空则查全部 |
| `cityName` | string | 否 | 完整官方城市名，如"南京市"、"江阴市"、"恩施土家族苗族自治州" |
| `parentName` | string | 否 | `cityName` 的上级行政区划名称（酒店差标用），需传完整名称。地级市的上级是省（如南京市→江苏省），县级市的上级是地级市（如昆山市→苏州市） |
| `cityLevel` | integer | 否 | 城市级别：`1`-省级，`2`-地级市/自治州（默认），`3`-区县/县级市 |
| `checkInTime` | string | 否 | 入住日期 `yyyy-MM-dd`（酒店差标用） |
| `checkLeaveTime` | string | 否 | 离店日期 `yyyy-MM-dd`（酒店差标用） |

### 返回

| 字段 | 类型 | 说明 |
|---|---|---|
| `standards` | array | 差标列表 |
| `standards[].businessType` | string | 业务类型：flight/train/hotel |
| `standards[].businessTypeName` | string | 业务类型中文：机票/火车票/酒店 |
| `standards[].text` | string | 差标文本描述 |
| `standards[].hasStandard` | boolean | 是否有差标限制 |

### 返回示例

**查询所有差标：**

```
输入：ziru_travel_standard()

返回：
{
  "code": 1,
  "data": {
    "standards": [
      {
        "businessType": "flight",
        "businessTypeName": "机票",
        "text": "可预订经济舱（Y/B/H/K/L/M/N/Q/T/X），折扣不低于5折",
        "hasStandard": true
      },
      {
        "businessType": "train",
        "businessTypeName": "火车票",
        "text": "可预订二等座、一等座",
        "hasStandard": true
      },
      {
        "businessType": "hotel",
        "businessTypeName": "酒店",
        "text": "一线城市：不超过500元/晚\n二线城市：不超过400元/晚",
        "hasStandard": true
      }
    ]
  }
}
```

**查询单项差标：**

```
输入：ziru_travel_standard(businessType=flight)

返回：
{
  "code": 1,
  "data": {
    "standards": [
      {
        "businessType": "flight",
        "businessTypeName": "机票",
        "text": "可预订经济舱（Y/B/H/K/L/M/N/Q/T/X），折扣不低于5折",
        "hasStandard": true
      }
    ]
  }
}
```

**无差标情况：**

```
输入：ziru_travel_standard()

返回：
{
  "code": 1,
  "data": {
    "standards": [
      {
        "businessType": "flight",
        "businessTypeName": "机票",
        "text": "用户未开启飞机差标，请按无差标限制进行后续流程",
        "hasStandard": false
      },
      ...
    ]
  }
}
```

### 失败情形

| message | 含义 |
|---|---|
| `X-Mcp-Key 缺失或无效` | 鉴权失败，提示用户重新填写令牌 |
| `差标查询异常` | 系统异常 |

### 注意

- 差标查询是只读操作，不会修改任何配置
- 酒店差标可能按城市等级有不同限制
- 如果用户需要查询具体城市的酒店差标，需结合城市信息

---

## HTTP 接口

### POST /workBuddy/travelStandard

**请求头：**
- `X-Mcp-Key: sk-xxx`

**请求体：**
```json
{
  "businessType": "flight"
}
```

**响应：**
```json
{
  "code": 1,
  "data": {
    "standards": [
      {
        "businessType": "flight",
        "businessTypeName": "机票",
        "text": "可预订经济舱...",
        "hasStandard": true
      }
    ]
  }
}
```
