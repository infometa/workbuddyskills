# 2 · 硬核废土3D（灵笼级CG角色渲染）

仅在 style_id=wasteland-3d 且选择已确认时读取。来源：style-hardcore-wasteland-3d；融合来源署名保留：资产-CG角色资产建立（CG-3D-CHARACTER-RENDER-v5.0）＋21-hardcore-wasteland-3d。九层框架已收录在本文件，无需另找外部技能。

## 定位与参考

- 大类：3D风格；中类：国漫3D。
- 主对标：艺画开天3D动画《灵笼》。辅助参考：《爱死机》废土集、Ash Thorp概念设定、《赛博朋克：边缘行者》的机械设计。
- 保持末世废土科幻、高精度3D CG、NPR+PBR混合、光影分明、明暗鲜明和主体定帧清晰。机械设计参考不改变输出的3D媒介。

## 风格模块

| 模块 | 常量 |
| --- | --- |
| Style | Hardcore wasteland sci-fi 3D, Ling Cage-grade CG character render |
| Renderer | UE5 path tracing, NPR+PBR hybrid；面部NPR赛璐璐色阶＋服饰道具PBR；SSS skin, AO, GI |
| Lighting | strong hard key, heavy shadow, cold-blue tech glow, rim light on metal |
| Color | cold grey, dark green, rust brown + cold-blue tech light |
| Composition | gritty mechanical depth, oppressive industrial scale, cinematic character staging |
| Concept Ref | 灵笼美术、硬核机甲设定、Ash Thorp |
| Scene | dim wasteland, distressed metal, wet concrete, apocalypse survivor |

## 九层结构化框架（角色任务强制顺序）

1. **主风格锚定**：UE5路径追踪式CG观感、灵笼级定帧目标、NPR+PBR混合。
2. **角色核心外貌**：性别年龄→体型比例→面部结构→发型发色→眼瞳→皮肤SSS。只使用已知事实，缺关键身份先询问。
3. **服装与装备**：名称→款式→颜色→材质→纹理→装饰。布料、皮革、金属的PBR属性与锈蚀做旧明确区分。
4. **姿态与表情**：身体朝向→重心→脊柱→四肢手势→面部表情。用可见动作表达气场，不只写抽象形容词。
5. **场景与环境**：由远到近，保留核心废土空间锚点。
6. **光影系统**：主光方向、色温、强度→轮廓光→AO→有介质时的体积光→GI。
7. **镜头规格**：焦距、光圈、景深、构图、视角。
8. **技术画质目标**：8K, ray tracing GI, SSS, AO, PBR metalness/roughness, path tracing, micro-detail, noise-free。作为视觉目标而非实际输出承诺。
9. **约束与输出**：必须元素、禁止元素、比例、解剖约束；末尾追加下方固定画质尾缀。

纯场景或道具任务沿用该顺序的相关层，第2–4层改为主体形体、结构、材质和朝向，不虚构人物；不输出没有对象的SSS皮肤描述。

## 中文风格底

硬核废土科幻3D动画风格，对标《灵笼》定帧画质，冷峻写实的末世硬核质感；精密粗粝机械与做旧金属PBR材质，灰暗废土和潮湿混凝土；低饱和冷灰、暗绿、锈褐点缀冷蓝科技光；强硬主光与厚重阴影，面部NPR色阶结合皮肤SSS，服饰道具PBR；保持三维体积与主体清晰，外围光学柔和。

## English assembly template（严格按九层展开）

```text
A UE5 path-traced cinematic 3D CG character render, benchmarked to Chinese 3D animation "Ling Cage" frame quality, NPR+PBR hybrid architecture (NPR cel-shaded face + PBR wardrobe/metal). [Identity and appearance, SSS skin]. [Wardrobe and equipment: shape, color, material, texture, weathering]. [Body orientation, balance, hands and visible facial expression]. [Wasteland environment from far to near: distressed metal, wet concrete, industrial scale]. [Hard key direction and temperature, heavy shadow, cold-blue tech glow, metal rim light, GI and AO]. [Focal length, aperture, depth of field, composition and viewing angle]. 8K visual-detail target, ray tracing global illumination, subsurface scattering where applicable, ambient occlusion, PBR metalness/roughness workflow, micro-detail texture maps, noise-free render. [Required elements, anatomy and aspect ratio]. [Compatible optical-edge texture suffix from common.md].
```

完成占位符替换后，必须在末尾追加以下英文原句，**不可删减、改写或替换**；中文提示词可以附等义中文约束，但不能代替固定英文句：

```text
Clean and polished image, controlled details, smooth and consistent texture, clear subject-background separation, no over-sharpening, no color blotches, no noise, no broken patterns, no artifacts, no distortion.
```

“smooth and consistent texture”解释为纹理连续、无断裂伪影，不把锈蚀金属变成无纹理平面。

## 角色锚点系统（九维）

面部结构 / 眼瞳特征 / 发型 / 身体比例 / 肤色材质 / 服装 / 装备 / 表情 / 特殊独有特征。

把已确认值组合成可粘贴锚点串，每张复用。默认锁定全部已确认字段；表情、姿态、场景、镜头仅在用户允许变化时调整。改服装装备或身份字段须明确标为用户要求的版本变体。

## 质量分层（中文主体描述字数参考）

| 级别 | 建议字数 | 用途 |
| --- | --- | --- |
| L1 快速预览 | 80–150字 | 造型与构图验证 |
| L2 标准产出 | 200–350字 | 常规配图，未指定时采用 |
| L3 商业精稿 | 400–600字 | 海报、角色主视觉 |
| L4 影视顶级 | 600–1000字 | 动画定帧、设定集 |

字数不含固定英文尾缀，不是模型token或分辨率保证。短版仍保留九层信息，允许每层只用短语。

## 标准布光方案

保留原八种可选方案：伦勃朗光 / 分光（亦正亦邪）/ 轮廓光主导（神秘）/ 三点布光（展示）/ 顶光（神圣压迫）/ 底光（反派诡异）/ 黄金时刻暖光（唯美）/ 冷白月光（冷峻）。

废土优先轮廓光主导、冷白月光、分光的适用组合；根据场景挑选，不无脑堆叠八种方案。用户指定的光向与时间优先。

## 分支质量门禁

- 保持角色三维体积；NPR只限定面部色阶设计，不能把全图变成纯2D赛璐璐。
- 区分粗糙金属、锈蚀、皮革、布料与皮肤，SSS不等于塑料或磨皮。
- 主体清晰与材质可辨优先；common.md的柔化只落在边缘/景深外，不抹掉关键微细节。
- 不以 illustration、纯2D anime cel、watercolor 作为整幅主风格。
- 每轮仅改1–2项，注明“严格保持其他所有元素不变”。固定尾缀必须逐字存在。
