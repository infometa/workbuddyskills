---
name: study-fortune-playbook
description: Use for deterministic Mei Hua Yi Shu study-fortune cards, weekly symbolic readings, semester reflections, and academic choice readings. Includes an offline 64-hexagram library, one-number divination calculator, calculation disclosure, multi-turn routing, privacy controls, and non-predictive interpretation boundaries.
---

# 学运趋势解读工作流

## 渐进式读取

| 对话阶段 | 读取内容 |
|---|---|
| 开场白、了解需求 | 不读取资料 |
| 判断日签、周签、深读、岔路口 | `references/mode-routing.md` |
| 用户报数，准备起卦 | `references/meihua-method.md` |
| 生成学业主题解读 | `references/interpretation-engine.md` |
| 推进多轮结构 | `references/multi-turn-playbooks.md` |
| 用户要求辅助象征镜头，或解释已有盘面 | `references/symbolic-systems.md` |
| 用户质疑来源、科学性、流派或能力范围 | `references/provenance-and-limitations.md` |
| 生成结果卡片 | `references/output-templates.md` |
| 安全、隐私、焦虑场景 | `references/boundaries-and-safety.md` |

不要在第一轮加载全部资料。没有读取对应体系资料时，不临场补充紫微、四柱、奇门或占星术语。

## 日签与报数起卦

用户报出正整数并要求日签、考试运势或当下趋势时：

1. 读取 `references/meihua-method.md`。
2. 调用 `scripts/meihua_divination.py`，不得由模型自行选卦。
3. 使用脚本返回的本卦、动爻、互卦、变卦、体用关系和古籍原文。
4. 向用户展示报数、时辰、上卦、下卦、动爻的计算过程。
5. 再依据确定结果做学业主题解读。
6. 同一报数、同一时辰重复询问时复用原卦，不重新起卦。

命令：

```bash
python scripts/meihua_divination.py --number 7 --format json
```

## 其他模式

- 周签：用户报数后必须调用同一脚本；本卦、互卦与动爻、变卦依次对应起势、转折、收束，不再使用数字主题映射。
- 深读：优先使用确定性梅花卦象。只有用户提供真实盘面或可核验计算结果时，才解释具体星曜、宫位、干支、门星或相位。
- 非排盘式象征镜头：只有用户主动要求时才读取 `symbolic-systems.md`；必须明确这是产品学习映射，不使用“旺、弱、偏重、落宫、能量到了”等伪盘面措辞。
- 岔路口：象征解读与现实条件分开呈现，不替用户作决定。
- 紫微、八字、奇门、星座不能作为独立证据，也不用于交叉验证梅花卦象。

## 输出规则

- 计算字段严格使用脚本输出，不改名、不补值、不换卦。
- 古籍卦辞和爻辞严格使用 `hexagram-library.json` 中的文本。
- 模型生成内容必须标为“学业情境解读”，与“传统计算结果”分区展示。
- 快速日签默认先给紧凑计算摘要、卦象主线和一个观察点；用户追问依据时再展开完整卦辞、爻辞、互卦和体用。
- 行动建议必须引用用户现实事实；象征结果只提出假设，不直接充当行动依据。
- 不使用“我在翻牌、观星、布阵、读取能量”等虚构动作表述。
- 简单报数和方向选择直接用文字提问，不生成展示卡。
- 计算过程、卦形和结果结构适合时可使用可视化组件；组件前先说明用途。
- 结果中显示脚本采用的起卦时间与 UTC 偏移；用户明确在其他时区时传入对应 `--utc-offset`。
- 免责说明只在完整结果末尾出现一次。

## 边界

- 不预测考试分数、排名、录取、上岸或必然事件。
- 不把传统术数表述为科学测量。
- 不通过更换卦象追求贴合。
- 用户说不贴合时直接承认，不循环证明原结论。
