# 3 · 电影写实（剧情片质感）

仅在 style_id=cinematic-realism 且选择已确认时读取。来源：style-cinematic-realism。

## 定位与参考

- 大类：仿真人；中类：都市/当代现实。
- 参考：《海边的曼彻斯特》《白日焰火》、Roger Deakins摄影、Edward Hopper画作的光与空间。
- 参考画作仅取光影、空间与情绪，不把真人剧情片变成油画。核心是生活写实、安静情感瞬间与克制叙事。

## 七模块常量

| 模块 | 常量 |
| --- | --- |
| Style | Cinematic photorealistic drama |
| Camera/Film | ARRI Alexa LF + Kodak Vision3 500T 35mm film look, 40mm anamorphic |
| Lighting | soft motivated natural window light, low-key practical fill |
| Color | desaturated teal-amber, refined low-contrast grade |
| Composition | balanced rule-of-thirds, shallow depth of field, story-driven framing |
| Visual Ref | Roger Deakins cinematography, Edward Hopper light and space |
| Scene | intimate everyday urban realism, quiet emotional moment |

ARRI Alexa LF为数字摄影机；源文中“+ Kodak Vision3 500T 35mm film”在这里明确为胶片模拟观感，而非同时使用两套真实感光介质。

## 中文风格底

电影级写实剧情片风格，胶片质感的细腻颗粒与宽容度，自然真实的环境动机光、柔和电影调色，低饱和青琥珀与克制低反差层次；40mm变形宽银幕镜头观感，浅景深与背景虚化，沉稳三分构图，生活空间中的安静情绪与故事感；35mm胶片模拟质感和清晰主体细节，保留真实皮肤、织物与环境痕迹。

## English assembly template

```text
Cinematic photorealistic drama — [subject, visible action and everyday environment] — ARRI Alexa LF digital-cinema look with Kodak Vision3 500T 35mm film emulation, 40mm anamorphic — [soft motivated natural window light, low-key practical fill, specified light direction] + [desaturated teal-amber, refined low-contrast grade] + [balanced rule-of-thirds, shallow depth of field, story-driven framing] + [Roger Deakins cinematography, Edward Hopper-inspired light and spatial composition] + [quiet emotional moment expressed through visible posture and environment] — [compatible film-texture suffix from common.md].
```

交付时替换全部方括号。保留源文“4K超清电影画面”的精度意图，但不得将文字宣称成实际生成文件规格。

## 分支质量门禁

- 镜头内的主光必须有来源，例如窗户或实景灯，不能只写悬空的“电影光”。
- 保持自然肤质、胶片颗粒、衣物纹理；避免塑料皮肤与CG打磨感。
- 低饱和不等于黑白、无色或丢失肤色；低反差不等于全画面发灰。
- 不带入太空硬件、废土装备、UE5、NPR或2D人物，除非这些是用户明确提供的主体事实且媒介仍保持真人观感。
- 从common.md选取兼容胶片尾缀，仅出现一次。
