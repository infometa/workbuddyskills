---
name: style-hard-scifi-realistic
description: 生成「硬科幻（纪实写实）」视觉风格的图像提示词。所属分类：【一】仿真人 / 科幻。当用户想要 realistic spacesuit, NASA-accurate hardware, weightless documentary realism 等画面，或明确点名《地心引力》《登月第一人》《火星救援》式写实硬科幻风格时使用。
agent_created: true
metadata:
  category_l1: "【一】仿真人"
  category_l2: "科幻"
  style_name: "硬科幻（纪实写实）"
---

# 硬科幻（纪实写实） · 视觉风格提示词

## 分类定位
- **大类**：【一】仿真人
- **中类**：科幻
- **风格名**：硬科幻（纪实写实）

## 风格参考（Reference）
《地心引力》(Gravity)、《登月第一人》(First Man)、《火星救援》(The Martian)；摄影指导 Emmanuel Lubezki、Linus Sandgren、Dariusz Wolski。强调真人实拍胶片质感、NASA 级硬件真实度、失重纪实感，**不含太空歌剧 / 星云史诗 / 奇幻巨制元素**。

## 提示词构成模块
> 完整结构：**风格 - 相机胶片参数 - [打光方案] + [色彩调性] + [构图描述] + [摄影师参照] + [场景/氛围]**，末尾统一追加质感尾缀。

| 模块 | 内容 |
| --- | --- |
| 风格 Style | Photorealistic hard sci-fi, documentary realism |
| 相机/胶片 Camera/Film | IMAX 70mm + 16mm grain, Kodak Vision3 500T, handheld POV |
| 打光 Lighting | single hard sunlight in vacuum, raking light, Earth-reflected fill, high contrast, no atmospheric scatter |
| 色彩 Color | desaturated naturalistic palette, muted steel-white, Mars ochre accents |
| 构图 Composition | claustrophobic helmet/capsule POV, or vast isolating wide shot, long-take handheld |
| 摄影师参照 DP Ref | Emmanuel Lubezki, Linus Sandgren, Dariusz Wolski |
| 场景/氛围 Scene | realistic spacesuit, NASA-accurate hardware, weightless silence, lonely tension |

## 结构化提示词（English · 推荐）
```
Photorealistic hard sci-fi, documentary realism - IMAX 70mm with 16mm film grain, Kodak Vision3 500T, handheld POV - [single hard sunlight in vacuum, raking light, Earth-reflected fill, high contrast, no atmospheric scatter] + [desaturated naturalistic palette, muted steel-white, Mars ochre accents] + [claustrophobic helmet/capsule POV or vast isolating wide shot, long-take handheld] + [Emmanuel Lubezki, Linus Sandgren, Dariusz Wolski cinematography] + [realistic spacesuit, NASA-accurate hardware, weightless silence, lonely tension], soft focus edges, gentle edge falloff, film-like softness, halation on highlights, photochemical softness, analog edge bloom, no digital sharpening, restrained detail, minimalist texture, large color blocks, negative space, graphic simplicity, hierarchy of focus, single focal point, unified material, smooth surfaces, clean rendering, matte finish, cohesive texture language, subdued micro-detail
```

## 中文提示词（原始描述）
```
纪实写实硬科幻风格，对标《地心引力》《登月第一人》《火星救援》，真人实拍电影胶片质感，NASA 级精确的宇航服与航天器硬件细节，真空中单一硬光阳光与地球反照补光、高反差无大气散射，去饱和的自然色调（钢白为主、火星赭石点缀），手持长镜头纪实构图，头盔/舱内幽闭主观视角或孤独渺小的宏大远景，失重的寂静与紧张感，无任何太空歌剧奇幻元素
```

## 统一质感尾缀
```
soft focus edges, gentle edge falloff, film-like softness, halation on highlights, photochemical softness, analog edge bloom, no digital sharpening, restrained detail, minimalist texture, large color blocks, negative space, graphic simplicity, hierarchy of focus, single focal point, unified material, smooth surfaces, clean rendering, matte finish, cohesive texture language, subdued micro-detail
```

## 使用说明
1. 文生图时，将上方「结构化提示词」整段作为风格底，拼接你的主体内容（人物 / 场景 / 动作）。
2. 结构化提示词适合 Midjourney / Stable Diffusion 等；需要中文模型可改用「中文提示词」。
3. 本风格主打**纪实写实**：避免使用 nebula、epic、majestic、space opera 等词，会破坏真实感；如需更强纪实感可加 "shot on real film, subtle lens vignette, authentic NASA mission photography"。
4. 可按需替换 [打光]/[色彩]/[构图]/[摄影师参照]/[场景] 模块强化或微调风格倾向。
