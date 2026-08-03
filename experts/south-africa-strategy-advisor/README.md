# South African Strategy

A specialized AI advisor for the South African market, covering macro environment, industry trends, competition analysis, investment site selection, market entry models, risk assessment, and long-term strategy — powered by 28 distilled knowledge summaries from 137 official source documents.

## 类型

Agent 型（单个 AI 专家）

## 功能

- 南非国家宏观经济环境与政策解读（NDP 2030, MTSF, Budget, OECD）
- 24个行业Master Plan与Fact Sheet数据覆盖
- 九省投资选址指南（含各SEZ/IDZ/具体项目）
- 投资激励与税收体系（12R SEZ, 12L能效, AIS汽车等）
- B-BBEE评分卡与合规路径
- 外汇管制、签证移民、环境EIA等实操流程
- 本地化知识与COS远程语料库双通道

## 使用示例

- 分析南非当前的经济形势和主要投资风险
- 企业进入南非市场的最佳模式和选址建议
- 南非矿业和能源行业的竞争格局与进入机会

## 云端语料库

137份原始PDF公开存储在腾讯云COS：
`https://southafrica-strategicadvisory-1257812465.cos.ap-shanghai.myqcloud.com/knowledge-base/`

## 安装

将专家包解压到插件目录后注册：

```bash
python3 scripts/register_expert.py south-africa-strategy-advisor/
```
