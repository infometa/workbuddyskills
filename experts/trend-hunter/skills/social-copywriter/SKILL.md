---
name: social-copywriter
description: "Social media copywriter. 社交媒体文案、朋友圈文案、朋友圈怎么发、微博文案、微博段子、Twitter文案、tweet、Instagram文案、IG caption、社交媒体文案生成、节日祝福、生日祝福文案、美食文案、旅行文案、心灵鸡汤、日常文案、晒照文案、show off、心情文案、搞笑文案、高级感文案、文艺文案、伤感文案、节日营销文案、品牌文案、长线程、病毒传播文案、裂变文案、品牌调性、festival marketing、brand copy、viral copy、thread。Generate copy for WeChat Moments, Weibo, Twitter/X, Instagram, birthdays, holidays, food, travel, festival marketing, brand voice, threaded posts, and viral content. Use when: (1) writing WeChat Moments/朋友圈 posts, (2) creating Weibo content, (3) writing Twitter/X posts, (4) crafting Instagram captions with hashtags, (5) birthday or holiday greetings, (6) food or travel captions, (7) daily inspirational quotes, (8) festival/holiday marketing campaigns, (9) establishing brand voice and copywriting style, (10) creating Twitter/Weibo thread series, (11) designing viral/shareable content for maximum reach, (12) any social media copywriting. 适用场景：发朋友圈、写微博、发Twitter、写Instagram文案、生日祝福、节日祝福、美食打卡、旅行打卡、日常心情、节日营销借势、品牌文案风格、长线程创作、病毒传播文案。"
---

# social-copywriter

社交媒体文案生成器。朋友圈、微博、Twitter、Instagram文案。支持多种场景和风格。

## 为什么用这个 Skill？ / Why This Skill?

- **平台调性**：朋友圈要有生活感+emoji，微博要带#话题#，Twitter要280字符以内，Instagram要大量hashtags
- **3条备选**：每次生成3条不同风格的文案，选你喜欢的
- **场景丰富**：美食、旅行、生日、节日、心情、日常，覆盖常见场景
- Compared to asking AI directly: platform-specific formatting (Moments emoji style, Weibo hashtag format, Twitter char limit, IG hashtags), multiple options per request

## Usage

When the user wants to generate social media copy/captions, run the appropriate command:

```bash
bash "{{skillPath}}/scripts/copy.sh" <command> [args]
```

## Commands

| Command | Description |
|---------|-------------|
| `moments "场景" [--mood MODE]` | 朋友圈文案（mood: happy/sad/funny/deep/show-off/food/travel/work） |
| `weibo "话题"` | 微博文案（带#话题#格式） |
| `twitter "topic"` | Twitter/X文案（英文，280字符内） |
| `instagram "topic"` | Instagram文案（英文+hashtags） |
| `birthday "名字"` | 生日祝福文案 |
| `holiday "节日"` | 节日祝福文案 |
| `food "菜名/餐厅"` | 美食文案 |
| `travel "地点"` | 旅行文案 |
| `daily` | 随机日常文案/心灵鸡汤 |
| `festival "节日"` | 节日营销文案（热点借势+营销建议） |
| `brand "品牌" "调性"` | 品牌文案风格设定（高端/年轻/专业/温暖） |
| `thread "主题"` | Twitter/微博长线程创作 |
| `viral "主题"` | 病毒式传播文案（裂变设计） |
| `help` | 显示帮助信息 |

## Examples

- 用户说"帮我发个朋友圈，今天心情不错" → `moments "心情不错" --mood happy`
- 用户说"写个微博关于加班" → `weibo "加班"`
- 用户说"写个Twitter about AI" → `twitter "AI"`
- 用户说"帮我写生日祝福给小明" → `birthday "小明"`
- 用户说"发个美食朋友圈，吃了火锅" → `food "火锅"`
- 用户说"来碗鸡汤" → `daily`

## Style Guide

- 朋友圈：简短精练，配合emoji，有生活感
- 微博：带#话题#格式，可长可短
- Twitter：英文，简洁有力，280字符内
- Instagram：英文+大量hashtags
- 整体追求"高级感"，不俗不腻

## Output

脚本会输出3条备选文案，用户可以选择或要求微调。
