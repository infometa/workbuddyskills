# 4 · 2D动画（新海诚式日系光影）

仅在 style_id=anime-2d 且选择已确认时读取。来源：style-makoto-shinkai；原目录为「资产-2D（主流国漫风格）」，但原文分类、参考与提示词实际均为新海诚式日系2D。本模块不宣称覆盖全部主流国漫。

## 定位与参考

- 大类：2D风格；实际中类：日系2D动画电影光影。
- 对标《你的名字》《天气之子》及新海诚式城市、天空、逆光与青春诗意。
- 保持赛璐璐人物与精细写实背景的融合，不改变为真人摄影或全3D CG。

## 七模块常量

| 模块 | 常量 |
| --- | --- |
| Style | Makoto Shinkai beautiful anime |
| Rendering | cel + photoreal bg, lens flare, fine grain |
| Lighting | backlight flare, Tyndall light, sparkling highlight |
| Color | rich translucent high-saturation sky and clouds |
| Composition | ultra-detailed background, dewy lens flare depth |
| Visual Ref | 新海诚光影、城市天空与青春情绪 |
| Scene | beautiful cityscape and sky, wistful youthful poetry |

源文“新海诚, 天门光影”保存在原稿中；“天门光影”没有给出可执行视觉定义，不补造摄影归属。运行时展开为明确的逆光、天空层次、水汽光晕和精细背景。

## 中文风格底

新海诚式唯美日系2D作画观感，赛璐璐人物与极细腻的写实城市背景，逆光耀斑、环境允许时的丁达尔光、璀璨高光；浓郁通透的高饱和天空与云层，水润镜头光晕和细腻颗粒；精致街景与自然光反射，清新、治愈又带淡淡忧伤的青春诗意，动画电影级光影层次。

## English assembly template

```text
Makoto Shinkai-inspired beautiful 2D anime — [subject and visible action], cel-shaded characters with finely painted photorealistic backgrounds, lens flare, fine grain — [backlight flare, physically situated shafts of light where appropriate, sparkling highlights] + [rich translucent high-saturation sky and clouds] + [ultra-detailed cityscape background, layered atmospheric depth and dewy lens flare] + [Shinkai-inspired urban-sky lighting and youthful visual poetry] + [specific setting and visible emotional cues] — [compatible optical and composition suffix from common.md].
```

替换全部占位符；中文与英文保持同一主体、天空色彩、光向与构图。English段落使用英文，不机械复制原稿的中英混杂参考标签。

## 分支质量门禁

- 人物赛璐璐与背景精细写实并存；photorealistic只限定背景表现，不把人物变成实拍脸。
- 高饱和应通透有层次，不变成荧光溢色；逆光与光束有对应光源及空气介质。
- 光晕只服务层次，不覆盖眼睛、五官、轮廓与关键动作。
- common.md的极简纹理可用于人物或远景色块，不能推翻本分支精细街景与云层要求。
- 不加入UE5、全图PBR、SSS皮肤作为主媒介；不把本分支重新命名为未定义的通用国漫。
