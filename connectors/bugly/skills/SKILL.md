---
name: bugly
description: "View the product quality overview"
description_zh: "查看产品的质量概览"
description_en: "View the product quality overview"
version: "1.0.0"
---

# Bugly 质量概览 Skill

## 功能说明

通过 Bugly MCP 服务查询应用的质量概览数据，支持以下维度：

- **大盘质量概览**：查看应用整体维度的崩溃率、ANR 率、FOOM（OOM）率、启动耗时等关键指标
- **版本质量概览**：按应用版本维度查看各项质量指标
- **今日质量概览**：查看应用当天的最新质量数据

## 调用原则

- 优先返回汇总数据，再根据用户需求提供细分维度的详情
- 指标数据附带时间范围说明，方便用户理解数据时效

## 典型使用场景

1. 查看应用的整体质量趋势
2. 对比不同版本之间的质量表现
3. 监控当天质量异常
