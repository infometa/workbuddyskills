# 国家与 ISO 码

创建猎客任务时使用大写二位国家码，用户展示中文国家名。以下是随附资料的基线映射；使用新增国家时查询权威字典或实际服务端维度，不凭空补码。

## 对照表

| 中文国名 | 英文 / 别名 | ISO |
|---|---|---|
| 德国 | Germany | DE |
| 荷兰 | Netherlands | NL |
| 奥地利 | Austria | AT |
| 巴西 | Brazil / Brasil | BR |
| 澳大利亚 | Australia | AU |
| 澳洲 | Australia（口语） | AU |
| 美国 | United States / USA | US |
| 英国 | United Kingdom / UK / England | GB |
| 法国 | France | FR |
| 意大利 | Italy | IT |
| 西班牙 | Spain | ES |
| 波兰 | Poland | PL |
| 墨西哥 | Mexico / México | MX |
| 印度尼西亚 | Indonesia | ID |
| 印尼 | Indonesia（简称） | ID |
| 越南 | Vietnam | VN |
| 马来西亚 | Malaysia | MY |
| 日本 | Japan | JP |
| 韩国 | South Korea / Korea | KR |
| 印度 | India | IN |
| 南非 | South Africa | ZA |
| 阿联酋 | UAE / United Arab Emirates / Dubai | AE |
| 沙特阿拉伯 | Saudi Arabia / Saudi | SA |
| 加拿大 | Canada | CA |
| 俄罗斯 | Russia | RU |
| 土耳其 | Turkey | TR |
| 泰国 | Thailand | TH |
| 新加坡 | Singapore | SG |

## 使用规则

1. **传参**：创建任务时目标国**一律用 ISO 码**（本表右列）。
2. **展示**：卡片/对话**一律中文国名**（本表左列）；不得把 ISO 码抛给用户。
3. **禁止混用**：不得把中文国名当参数传（后端不认）；不得把 ISO 码显示到卡片上。
4. **多国**：按后端约定并列传。
5. **命中不了**：如实告知无法确定，**不得编一个码**。
