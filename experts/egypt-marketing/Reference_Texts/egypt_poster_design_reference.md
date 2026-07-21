# 埃及市场海报设计参考手册

> 版本：1.0.0
> 用途：egypt-marketing 专家海报生成模式参考文档

---

## §2.4 元素分级体系（完整版）

### S 级 — 独占元素（埃及独有，识别度最高）

| 元素 | 视觉描述 | 文化背景 | 适用场景 |
|------|---------|---------|---------|
| 弯曲金字塔 | 吉萨金字塔群侧视轮廓线 | 世界级地标，象征永恒与稳定 | B2B/B2C通用 |
| 努比亚彩绘 | 红蓝白几何纹样+人形图案 | 努比亚传统民居装饰艺术 | B2C/品牌故事 |
| 闻风节彩蛋 | 彩绘鸡蛋+风筝元素 | 埃及春日传统节日 Sham el-Nessim | 春季/节日营销 |
| 费昂斯釉面 | 青绿色陶器釉面纹理 | 古埃及法老时期陶瓷工艺 | 高端/奢侈品 |

### A 级 — 强辨识元素

| 元素 | 视觉描述 | 文化背景 |
|------|---------|---------|
| 棕榈叶纹 | 金色棕榈枝条交织 | 尼罗河沿岸植被 |
| 莲花图腾 | 蓝/白莲花抽象化 | 古埃及神圣符号，代表重生 |
| 阿拉伯书法 | 库法体/纳斯赫体文字装饰 | 伊斯兰视觉艺术核心 |
| 方格马赛克 | 彩色瓷砖拼接几何图案 | 伊斯兰建筑传统装饰 |
| 阿布辛贝巨像 | 拉美西斯二世石雕剪影 | 世界文化遗产地标 |

### B/C 级 — 通用与慎用

| 元素 | 等级 | 说明 |
|------|------|------|
| 沙漠驼队 | B 级 | 经典但易落入俗套 |
| 金字塔正视图 | C 级 | 太常见，建议用侧视轮廓替代 |
| 法老面具 | C 级 | 博物馆感过重，不适合商业海报 |

---

## §11.3 黄金组合 Prompt 完整模板

### 默认模板（Portrait 9:16）

```
Egyptian brand poster design, curved silhouette of Giza Pyramids on left side composition,
Nubian folk painting patterns in red-blue-white geometric style integrated into background,
Sham el-Nessim decorated egg motifs scattered as Easter-style accents,
faience glaze texture in turquoise-green for premium surface finish,
warm golden hour lighting, asymmetric balanced layout,
short bold text "[BRAND/EVENT]" at center-top area,
professional advertising photography style, high detail, commercial quality
```

### 变量说明
- `[BRAND/EVENT]` → 替换为实际品牌名或节日名（≤2个英文词）
- `portrait 9:16` → 可替换为 `square 1:1` 或 `horizontal 16:9`
- B2B 场景：加 `minimalist corporate color palette`
- B2C 场景：加 `vibrant warm color palette`
- 斋月场景：加 `deep green and gold traditional tones`

---

## §12 推荐模板库

### 📋 模板 A：黄金组合（默认推荐）
**Prompt：**
```
Egyptian brand poster, curved Giza Pyramid silhouette left-side composition,
Nubian folk art patterns (red-blue-white geometric) blended into background layer,
Sham el-Nessim painted eggs as decorative accents,
faience ceramic glaze texture overlay in turquoise,
warm golden light, asymmetric elegant balance,
short bold text "[BRAND]" at top-center,
commercial poster design, professional quality, 9:16 portrait
```
- **元素**：弯曲金字塔 + 努比亚彩绘 + 闻风节彩蛋 + 费昂斯釉面
- **风格**：温暖 · 节日感 · 不对称
- **适用**：通用品牌海报、春季新品、C端消费品
- **评分**：★★★★★ 综合最高分

### 📋 模板 B：阿布辛贝史诗
**Prompt：**
```
Monumental Egyptian brand poster, Abu Simbel Ramses II colossal statues silhouette
as central framing element, faience turquoise glaze texture on stone surfaces,
subtle curved pyramid outline in distant background,
epic symmetrical composition, golden hour dramatic side-lighting,
short bold text "[BRAND]" at upper third,
cinematic wide angle, luxury brand aesthetic, 9:16 portrait
```
- **元素**：阿布辛贝巨像 + 费昂斯 + 弯曲金字塔点缀
- **风格**：史诗 · 对称 · 纪念碑感
- **适用**：品牌故事、高端奢侈品、企业文化
- **评分**：★★★★☆

### 📋 模板 C：白沙漠超现实
**Prompt：**
```
Surrealist Egyptian lifestyle poster, White Desert mushroom rock formations
as dreamlike background, minimalist faience blue accents,
small Nubian amulet charm floating in negative space,
lots of white empty space, cool pastel color palette,
soft diffused lighting, ethereal atmosphere,
short bold text "[BRAND]" at lower third,
editorial fashion photography style, square 1:1 format
```
- **元素**：白沙漠蘑菇岩 + 费昂斯 + 努比亚护符
- **风格**：超现实 · 留白多 · 冷色调
- **适用**：旅游、生活方式、户外品牌
- **评分**：★★★★☆

### 📋 模板 D：努比亚纯文化
**Prompt：**
```
Vibrant Egyptian cultural poster, full-frame Nubian house wall paintings
in traditional red-blue-white-black geometric patterns,
palm frond borders at edges, lotus flower motifs as focal points,
rich saturated colors, handcrafted textile texture feel,
festive celebratory mood, dynamic asymmetry,
short bold text "[BRAND]" centered bold block letters,
cultural festival poster aesthetic, horizontal 16:9 format
```
- **元素**：努比亚彩绘全覆盖 + 棕榈叶边框 + 莲花图腾
- **风格**：浓郁民族 · 高饱和 · 不规则
- **适用**：快消、潮流、青年品牌、文化活动
- **评分**：★★★☆☆

### 📋 模板 E：费昂斯极简商务
**Prompt：**
```
Minimalist Egyptian business poster, clean white base with subtle
faience glaze texture gradient (turquoise to pale green),
thin golden pyramid line-art as geometric accent in corner,
professional grid layout, ample negative space,
corporate teal and gold color scheme only,
short bold text "[BRAND]" at upper-left, clean sans-serif feel,
B2B tech conference keynote visual style, square 1:1 format
```
- **元素**：费昂斯釉面纹理 + 金字塔线条画
- **风格**：极简 · 商务 · 低饱和
- **适用**：B2B、科技/SaaS、企业服务、金融
- **评分**：★★★☆☆

---

## 附录：文化禁忌速查表

| 类别 | 禁止内容 | 替代方案 |
|------|---------|---------|
| 宗教 | 古兰经经文、清真寺内部场景 | 清真寺外观剪影、伊斯兰几何纹 |
| 政治 | 国旗变形、政治人物、地图争议 | 中性国家符号、自然地标 |
| 性别 | 过度暴露女性形象、性别刻板印象 | 多元包容的人物呈现 |
| 文字 | 阿拉伯语长句、错误阿拉伯书法 | 单词级短文（≤1词）、英文为主 |
