# DDoS 攻击分析报告模板

本目录包含 DDoS 攻击分析报告的标准模板文件，用于生成统一格式的专业分析报告。

## 文件说明

### 报告模板
- `report_template.md` - 主要的 Markdown 报告模板，包含完整的报告结构和示例数据
***ECharts 图表数据示例***：
```echarts
{
  "title": {
    "text": "DDoS 攻击类型分布",
    "left": "center"
  },
  "tooltip": {
    "trigger": "item",
    "formatter": "{a} <br/>{b}: {c} ({d}%)"
  },
  "series": [
    {
      "name": "包数",
      "type": "pie",
      "radius": "55%",
      "data": [
        {"value": 136615, "name": "SYN Flood"},
        {"value": 7653, "name": "ACK Flood"},
        {"value": 117, "name": "UDP Flood"},
        {"value": 2, "name": "ICMP Flood"}
      ]
    }
  ]
}
```

## 使用方法

1. **报告生成**: 基于 `report_template.md` 模板，将实际分析数据替换模板中的示例数据
2. **图表生成**: 使用对应的 JSON 模板文件，更新其中的数据部分，生成可视化图表，图表的json数据不单独生成文件，而是放在报告中
3. **输出要求**: 确保生成的报告包含所有必需的章节和可视化图表

## 模板特点

- ✅ 符合专业安全分析报告标准
- ✅ 包含详细的攻击特征分析
- ✅ 标准 ECharts 格式，可直接用于可视化


## 注意事项

- 同时输出以国家维度进行的DDOS攻击类型的统计，攻击类型、国家、占比表格，并同时给出相应的echarts图表数据。
- 基于表格 生成 echarts 饼图的 json，每个图放在一个单独的json里，用于后续生成 docx 的需要
- 必须输出标准的ECharts option JSON格式，使用 series数组来定义饼图系列，放在多个json数据中
- 确保JSON语法完全正确，可直接用于echarts.setOption()
- 数据格式严格遵循ECharts规范：
     * 字符串用双引号包围
     * 数组格式正确：["item1", "item2"]
     * 数值不加引号：[100, 200, 300]
- 图表标题简洁明了，符合数据内容