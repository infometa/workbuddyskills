---
name: style-makoto-shinkai
description: 生成「新海诚（主流国漫风格）」视觉风格的图像提示词。所属分类：【三】2D风格 / 日漫2D风格（可大量填充）。当用户想要 beautiful cityscape and sky, wistful youthful poetry 等画面，或明确点名「新海诚（主流国漫风格）」风格时使用。
agent_created: true
metadata:
  category_l1: "【三】2D风格"
  category_l2: "日漫2D风格（可大量填充）"
  style_name: "新海诚（主流国漫风格）"
---

# 新海诚（主流国漫风格） · 视觉风格提示词

## 分类定位
- **大类**：【三】2D风格
- **中类**：日漫2D风格（可大量填充）
- **风格名**：新海诚（主流国漫风格）

## 风格参考（Reference）
《你的名字》《天气之子》、新海诚光影美学

## 提示词构成模块
> 完整结构：**风格 - 相机胶片参数/渲染器 - [打光方案] + [色彩调性] + [构图描述] + [画家参照] + [场景/氛围]**，末尾统一追加质感尾缀。

| 模块 | 内容 |
| --- | --- |
| 风格 Style | Makoto Shinkai beautiful anime |
| 相机/渲染器 Camera/Renderer | cel + photoreal bg, lens flare, fine grain |
| 打光 Lighting | backlight flare, Tyndall light, sparkling highlight |
| 色彩 Color | rich translucent high-saturation sky and clouds |
| 构图 Composition | ultra-detailed background, dewy lens flare depth |
| 画家参照 Painter Ref | 新海诚, 天门光影 |
| 场景/氛围 Scene | beautiful cityscape and sky, wistful youthful poetry |

## 结构化提示词（English · 推荐）
```
Makoto Shinkai beautiful anime - cel + photoreal bg, lens flare, fine grain - [backlight flare, Tyndall light, sparkling highlight] + [rich translucent high-saturation sky and clouds] + [ultra-detailed background, dewy lens flare depth] + [新海诚, 天门光影] + [beautiful cityscape and sky, wistful youthful poetry], soft focus edges, gentle edge falloff, film-like softness, halation on highlights, photochemical softness, analog edge bloom, no digital sharpening, restrained detail, minimalist texture, large color blocks, negative space, graphic simplicity, hierarchy of focus, single focal point, unified material, smooth surfaces, clean rendering, matte finish, cohesive texture language, subdued micro-detail
```

## 中文提示词（原始描述）
```
新海诚式唯美日系作画质感，极致细腻的写实背景与梦幻光影，逆光耀斑、丁达尔光与璀璨高光交织，浓郁通透的高饱和天空与云层色彩，水润的镜头光晕与细腻颗粒，精致的城市街景与自然光反射，氛围唯美、清新、治愈而充满淡淡忧伤的青春诗意，极致光影美学的高清动画电影级渲染
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
