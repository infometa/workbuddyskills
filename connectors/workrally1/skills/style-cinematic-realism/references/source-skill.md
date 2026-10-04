---
name: style-cinematic-realism
description: 生成「电影写实（剧情片质感）」视觉风格的图像提示词。所属分类：【一】仿真人 / 都市/当代现实。当用户想要 intimate everyday urban realism, quiet emotional moment 等画面，或明确点名「电影写实（剧情片质感）」风格时使用。
agent_created: true
metadata:
  category_l1: "【一】仿真人"
  category_l2: "都市/当代现实"
  style_name: "电影写实（剧情片质感）"
---

# 电影写实（剧情片质感） · 视觉风格提示词

## 分类定位
- **大类**：【一】仿真人
- **中类**：都市/当代现实
- **风格名**：电影写实（剧情片质感）

## 风格参考（Reference）
《海边的曼彻斯特》《白日焰火》、Roger Deakins 摄影、Edward Hopper 油画

## 提示词构成模块
> 完整结构：**风格 - 相机胶片参数/渲染器 - [打光方案] + [色彩调性] + [构图描述] + [画家参照] + [场景/氛围]**，末尾统一追加质感尾缀。

| 模块 | 内容 |
| --- | --- |
| 风格 Style | Cinematic photorealistic drama |
| 相机/渲染器 Camera/Renderer | ARRI Alexa LF + Kodak Vision3 500T 35mm film, 40mm anamorphic |
| 打光 Lighting | soft motivated natural window light, low-key practical fill |
| 色彩 Color | desaturated teal-amber, refined low-contrast grade |
| 构图 Composition | balanced rule-of-thirds, shallow depth of field, story-driven framing |
| 画家参照 Painter Ref | Roger Deakins, Edward Hopper light |
| 场景/氛围 Scene | intimate everyday urban realism, quiet emotional moment |

## 结构化提示词（English · 推荐）
```
Cinematic photorealistic drama - ARRI Alexa LF + Kodak Vision3 500T 35mm film, 40mm anamorphic - [soft motivated natural window light, low-key practical fill] + [desaturated teal-amber, refined low-contrast grade] + [balanced rule-of-thirds, shallow depth of field, story-driven framing] + [Roger Deakins, Edward Hopper light] + [intimate everyday urban realism, quiet emotional moment], soft focus edges, gentle edge falloff, film-like softness, halation on highlights, photochemical softness, analog edge bloom, no digital sharpening, restrained detail, minimalist texture, large color blocks, negative space, graphic simplicity, hierarchy of focus, single focal point, unified material, smooth surfaces, clean rendering, matte finish, cohesive texture language, subdued micro-detail
```

## 中文提示词（原始描述）
```
电影级写实剧情片风格，胶片质感的细腻颗粒与宽容度，自然真实的环境光与柔和的电影级调色，低饱和高级的色调层次，浅景深与虚化背景，沉稳克制的镜头构图，富有故事感的氛围光影，35mm 胶片质感，4K 超清电影画面
```

## 统一质感尾缀
```
soft focus edges, gentle edge falloff, film-like softness, halation on highlights, photochemical softness, analog edge bloom, no digital sharpening, restrained detail, minimalist texture, large color blocks, negative space, graphic simplicity, hierarchy of focus, single focal point, unified material, smooth surfaces, clean rendering, matte finish, cohesive texture language, subdued micro-detail
```

## 使用说明
1. 文生图时，将上方「结构化提示词」整段作为风格底，拼接你的主体内容（人物 / 场景 / 动作）。
2. 结构化提示词适合 Midjourney / Stable Diffusion 等；需要中文模型可改用「中文提示词」。
3. 末尾「统一质感尾缀」已内置于结构化提示词，单独使用其他描述时也建议手动追加，保证全库风格统一的胶片柔焦质感。
4. 可按需替换 [打光]/[色彩]/[构图]/[画家参照]/[场景] 模块强化或微调风格倾向。
