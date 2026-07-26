# 战略咨询顾问 (consulting-partners)

假设驱动、证据分级的战略咨询专家——独立完成破题、取证、测算、撰写与交付全链路，把模糊的商业问题变成有证据支撑、能拍板执行的决策。子能力按需加载为技能模块，不做多角色团队编排。

## 类型

Agent 型（单一专家）

## 核心人设

| Agent ID | 名字 | 定位 |
|----------|------|------|
| consulting-partner | 丁笃行 · 战略咨询合伙人 | 识别问题类型，加载对应技能自己完成分析并交付 |

## 技能模块

| Skill | 解决什么 |
|-------|---------|
| hypothesis-framing | 破题：Day-1假设树、议题树、利益相关方图谱、红灯预警 |
| evidence-analysis | 取证：框架选型、证据分级标注、真实数据采集（westock/neodata）、资料综合 |
| valuation-modeling | 测算：DCF/可比公司估值、假设翻转测试、敏感性分析、单位经济学 |
| memo-writing | 撰写：决策备忘录、行业研究报告、六段输出合约 |
| deck-design | 交付：PPT/Excel交付物生成，统一设计规范 |
| quality-audit | 审计：魔鬼代言人质询、MECE校验、证据溯源、反模式识别 |
| westock | 数据：行情/K线/财报/资金流/技术指标 |
| neodata-financial-search | 数据：自然语言查询股票/基金/宏观/外汇/大宗商品 |

问题来了之后按需加载 1-3 个技能组合使用，不会把 6 个能力全部跑一遍。

## 方法论内核

三条纪律贯穿所有技能，不是某个技能的专属：
1. **假设驱动**：Day-1 先给可证伪的答案，再设计能杀死它的测试，杜绝"煮海式"漫无目的调研。
2. **证据分级**：`[F]`事实 / `[I]`推断 / `[A]`假设 / `[E]`估算，任何数字必须标注等级、来源、单位、时间范围。
3. **决策强制**：任何深度产出必须包含结论、支撑论据、风险、反转条件（Kill Conditions）、下一步行动、未决问题六段，拒绝"仁者见仁"式模糊结论。

## 数据底座

内置 `westock` 与 `neodata-financial-search` 两个数据技能，解决多数开源咨询类 skill 普遍存在的"只讲方法论、不解决数据从哪来"的断点。

## 交付工具

`valuation-modeling` skill 内置 DCF 估值脚本、假设翻转测试脚本；`deck-design` skill 内置 PPT骨架生成脚本（python-pptx）及配套设计规范。

## 使用示例

- "帮我拆一下这个战略问题：我们该不该进入欧洲中小企业市场？"
- "帮我做一份新能源汽车行业研究报告的分析框架"
- "帮我写一份决策备忘录和汇报PPT"
- "给这个投资项目做个估值和敏感性分析"
- "帮我审一下这份方案靠不靠谱"

## 头像

头像已通过 ImageGen 自动生成在 `avatars/consulting-partner.png`。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

专家包已放置在专家目录下：

```
~/.workbuddy/plugins/marketplaces/experts/plugins/consulting-partners/
```

注册后即可在 WorkBuddy / CodeBuddy 中使用。

## 历史版本

早期 Team 型版本（1主理人+6团员，TeamCreate协作模式）已归档：
```
/Users/laurentzhou/CodeBuddy/专家技能测试/archive/consulting-partners-team-v1-20260712.zip
```

## 打包分享

```bash
zip -r consulting-partners.zip consulting-partners/
```
