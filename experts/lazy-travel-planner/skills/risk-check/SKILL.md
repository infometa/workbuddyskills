---
name: risk-check
description: 出行风险体检 · 天气预警 / 限行 / 节假日人流 / 当地骗局 / 应急联系。结合 risk_knowledge.json 静态知识 + online-search 实时天气 + xhs-explore skill"避雷"搜索。按置信度绿/黄/灰输出。
version: 1.0.0
author:
tags: [travel, risk, safety, weather, scam, glue]
license: MIT
triggers:
  - 07/08 完成后，进入阶段 3 成稿前
  - 用户问"X 月去 Y 有什么要注意的"
  - 用户问"这个景点会不会被坑"
inputs:
  - name: itinerary
    type: object
    required: true
  - name: trip_request
    type: object
    required: true
outputs:
  - name: risk_report
    type: object
    doc: 五大类风险 + 行前清单 + 应急联系
---

# 风险体检（risk-check）

## 我做什么

按五大类查风险，给用户出发前一份"防坑清单"：

1. **天气** — online-search 查实时天气
2. **限行** — online-search 查当地最新规则
3. **节假日 / 人流** — 静态规则 + xhs-explore skill 当年实时反馈
4. **骗局** — `risk_knowledge.json` + xhs-explore skill "X 避雷"搜索
5. **应急** — `risk_knowledge.json.emergency_contacts` 直接附上

## 工作流程

```
itinerary + trip_request
   ↓
Step 1: 拉天气
   ├─ online-search 查天气预报
   └─ 出行日 > 7 天 → 标 ⚪ "建议出行前 3 天再核实"
   ↓
Step 2: 检节假日
   按 risk_knowledge.holiday_warnings 匹配 trip_request.start_date
   命中 → 给警示 + 改期建议
   ↓
Step 3: 检限行（仅自驾）
   online-search "{城市} 限行 2026"
   ↓
Step 4: 拉防坑（按行程城市）
   ├─ risk_knowledge.city_specific_warnings[城市]
   ├─ risk_knowledge.general_scams（通用）
   └─ xhs-explore skill "X 避雷" / "X 被坑" 取最新案例
   ↓
Step 5: 行前清单
   risk_knowledge.general_kit + 按 user_profile 微调
   ↓
risk_report.json
```

## 输出 schema

```json
{
  "trip_id": "uuid",
  "weather": {
    "summary": "整体晴好，D3 有小雨概率 60%",
    "by_day": [
      { "date": "2026-04-15", "min": 18, "max": 26, "condition": "晴", "rain_prob": 0.1, "alert": null }
    ],
    "recommendations": [
      "D3 把户外景点（杜甫草堂）调到 D2，改为博物馆室内（金沙）"
    ],
    "confidence": "green"
  },
  "holiday_alert": {
    "is_holiday": true,
    "holiday_name": "清明小长假",
    "level": "warning",
    "details": "4/4-4/6 江浙沪短途游爆炸，景点限流，住宿涨 50%-100%。建议提前 2 周订房",
    "alternative_dates": ["2026-04-08 之后"]
  },
  "traffic_restrictions": {
    "applicable": false,
    "_doc": "用户不自驾，跳过"
  },
  "scams_to_watch": [
    {
      "category": "city_specific",
      "city": "成都",
      "items": [
        "宽窄巷子是游客街，本地人去玉林路",
        "茶馆人均超过 100 多半宰客"
      ],
      "source": "risk_knowledge.json + xhs 2026 最新案例 18 条",
      "confidence": "green"
    },
    {
      "category": "general",
      "items": [
        "机场/火车站警惕黑车，认准车顶灯+车牌",
        "陌生人邀请喝茶/看展一律拒绝（多发于网红景区）"
      ]
    }
  ],
  "emergency_contacts": {
    "police": "110",
    "tourism_complaint": "12301",
    "consumer": "12315",
    "weather_alert": "12379"
  },
  "pre_trip_checklist": {
    "ids": ["身份证"],
    "health": ["晕车药（你的 profile 有 motion_sickness）"],
    "weather": ["雨伞（D3 可能下雨）", "防晒（紫外线指数 7）"],
    "tech": ["充电宝", "耳机"],
    "money": ["少量现金（古镇可能不收手机支付）"]
  }
}
```

## 置信度标记

- 🟢 天气 ≤ 7 天 + 节假日匹配 + 城市具体骗局
- 🟡 天气 > 7 天 + WebSearch 限行
- ⚪ references/ 静态兜底

每条都标，HTML 行程书里渲染对应颜色。

## 反模式

- ❌ 给 7 天后的精确天气（不靠谱，要降级标灰）
- ❌ 不区分通用骗局和城市特定（全部混一起用户记不住）
- ❌ 应急联系不附上（关键时刻找不到）
- ❌ 行前清单千篇一律（要按 user_profile 微调）

---

_这个 skill 是 agent 的"安全网"，能挽救用户一次大坑就值回票价。_
