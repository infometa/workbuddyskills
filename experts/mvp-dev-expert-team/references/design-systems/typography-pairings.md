---
id: typography-pairings
title: 字体配对库（精选 25 套 + Google Fonts 导入）
domain: design-systems
quality_score: 95
last_updated: 2026-07-19
---

# 字体配对库（精选 25 套 + Google Fonts 导入）

从大量字体配对资产中蒸馏出 25 套商业命中率最高的组合。每套均给出标题字、正文字、情绪关键词、适用场景、可直接粘贴的 Google Fonts URL 与 CSS `@import`、Tailwind config 片段、以及实战注意事项。所有配对均默认提供可访问性、可读性、加载性能三项商业级评估。

## 通用规范

- 所有字体均来自 Google Fonts（免费可商用），少数顶级品牌字体（Satoshi、Clash Display）会给出 Fontshare 替代方案
- 字重选择遵循"少即是多"原则：单字族 3-4 个字重足够，避免全字重加载
- 中文场景需补 `Noto Sans SC` 或 `Noto Serif SC` 作为 fallback
- 性能建议：`<link rel="preconnect" href="https://fonts.googleapis.com">` + `display=swap`

## 1. Classic Elegant 经典优雅

- **类别**：Serif + Sans
- **标题字**：Playfair Display
- **正文字**：Inter
- **情绪关键词**：elegant、luxury、timeless、editorial、premium
- **最适用于**：奢侈品牌、时尚、SPA、美容、高端电商、编辑杂志
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Playfair Display', 'serif'], sans: ['Inter', 'sans-serif'] }
```
- **注意事项**：Playfair Display 高对比衬线，标题 ≥ 32px 才能体现优雅；小字勿用。

## 2. Modern Professional 现代专业

- **类别**：Sans + Sans
- **标题字**：Poppins
- **正文字**：Open Sans
- **情绪关键词**：modern、professional、corporate、friendly、approachable
- **最适用于**：SaaS、企业站、商业应用、初创公司、专业服务
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Poppins', 'sans-serif'], body: ['Open Sans', 'sans-serif'] }
```
- **注意事项**：几何 Poppins 配人文 Open Sans，是 B2B SaaS 的"安全牌"。

## 3. Tech Startup 科技创业

- **类别**：Sans + Sans
- **标题字**：Space Grotesk
- **正文字**：DM Sans
- **情绪关键词**：tech、startup、innovative、bold、futuristic
- **最适用于**：科技公司、初创、SaaS、开发者工具、AI 产品
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Space Grotesk', 'sans-serif'], body: ['DM Sans', 'sans-serif'] }
```
- **注意事项**：Space Grotesk 字符独特性强，适合需要差异化的科技品牌。

## 4. Editorial Classic 编辑经典

- **类别**：Serif + Serif
- **标题字**：Cormorant Garamond
- **正文字**：Libre Baskerville
- **情绪关键词**：editorial、classic、literary、refined、bookish
- **最适用于**：出版、博客、新闻、文学杂志、书籍封面
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Libre+Baskerville:wght@400;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Cormorant Garamond', 'serif'], body: ['Libre Baskerville', 'serif'] }
```
- **注意事项**：全衬线组合在长文阅读时偏复古，需保证正文 ≥ 16px。

## 5. Minimal Swiss 极简瑞士

- **类别**：Sans + Sans（单字族）
- **标题字**：Inter
- **正文字**：Inter
- **情绪关键词**：minimal、clean、swiss、functional、neutral
- **最适用于**：仪表盘、管理后台、文档、企业应用、设计系统
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { sans: ['Inter', 'sans-serif'] }
```
- **注意事项**：极简单字族靠字重差建立层级，标题必须 700+ 配大字号。

## 6. Wellness Calm 健康平静

- **类别**：Serif + Sans
- **标题字**：Lora
- **正文字**：Raleway
- **情绪关键词**：calm、wellness、relaxing、natural、organic
- **最适用于**：健康应用、Wellness、SPA、冥想、瑜伽、有机品牌
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Raleway:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Raleway:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Lora', 'serif'], sans: ['Raleway', 'sans-serif'] }
```
- **注意事项**：Lora 有机曲线配 Raleway 简约，冥想 App 的默认选择。

## 7. Developer Mono 开发者等宽

- **类别**：Mono + Sans
- **标题字**：JetBrains Mono
- **正文字**：IBM Plex Sans
- **情绪关键词**：code、developer、technical、precise、functional
- **最适用于**：开发者工具、文档、代码编辑器、技术博客、CLI 应用
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { mono: ['JetBrains Mono', 'monospace'], sans: ['IBM Plex Sans', 'sans-serif'] }
```
- **注意事项**：JetBrains Mono 用于 code block 与数据 label，不要用于正文段落。

## 8. Brutalist Raw 粗野原色

- **类别**：Mono + Mono（单字族）
- **标题字**：Space Mono
- **正文字**：Space Mono
- **情绪关键词**：brutalist、raw、technical、monospace、stark
- **最适用于**：粗野设计、开发者作品集、实验性、技术艺术
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { mono: ['Space Mono', 'monospace'] }
```
- **注意事项**：字重只有 400/700，全等宽用于原色 Brutalism 风。

## 9. Luxury Serif 奢侈衬线

- **类别**：Serif + Sans
- **标题字**：Cormorant
- **正文字**：Montserrat
- **情绪关键词**：luxury、high-end、fashion、elegant、refined
- **最适用于**：时尚品牌、奢侈品电商、珠宝、高端服务
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Cormorant:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Cormorant:wght@400;500;600;700&family=Montserrat:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Cormorant', 'serif'], sans: ['Montserrat', 'sans-serif'] }
```
- **注意事项**：Cormorant 字身窄长，适合 hero 大标题；Montserrat 几何感强做正文不抢戏。

## 10. Friendly SaaS 友好 SaaS

- **类别**：Sans + Sans（单字族）
- **标题字**：Plus Jakarta Sans
- **正文字**：Plus Jakarta Sans
- **情绪关键词**：friendly、modern、saas、clean、approachable
- **最适用于**：SaaS、Web 应用、Dashboard、B2B、生产力工具
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { sans: ['Plus Jakarta Sans', 'sans-serif'] }
```
- **注意事项**：Inter 的现代替代，比 Inter 多一分亲和力，2024 年后流行度上升。

## 11. Corporate Trust 企业信赖

- **类别**：Sans + Sans
- **标题字**：Lexend
- **正文字**：Source Sans 3
- **情绪关键词**：corporate、trustworthy、accessible、readable、professional
- **最适用于**：企业、政府、医疗、金融、无障碍优先项目
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Lexend', 'sans-serif'], body: ['Source Sans 3', 'sans-serif'] }
```
- **注意事项**：Lexend 为可读性优化，特别适合阅读障碍友好场景。

## 12. News Editorial 新闻编辑

- **类别**：Serif + Sans
- **标题字**：Newsreader
- **正文字**：Roboto
- **情绪关键词**：news、editorial、journalism、trustworthy、readable
- **最适用于**：新闻站、博客、杂志、新闻业、内容密集站
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Newsreader', 'serif'], sans: ['Roboto', 'sans-serif'] }
```
- **注意事项**：Newsreader 长文阅读舒适，标题 ≤ 28px 最佳。

## 13. Geometric Modern 几何现代

- **类别**：Sans + Sans
- **标题字**：Outfit
- **正文字**：Work Sans
- **情绪关键词**：geometric、modern、clean、balanced、versatile
- **最适用于**：通用、作品集、机构、现代品牌、落地页
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Work+Sans:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Work+Sans:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Outfit', 'sans-serif'], body: ['Work Sans', 'sans-serif'] }
```
- **注意事项**：Outfit 比 Poppins 多一分个性，适合不想"撞脸"的现代品牌。

## 14. Bold Statement 强势宣言

- **类别**：Display + Sans
- **标题字**：Bebas Neue
- **正文字**：Source Sans 3
- **情绪关键词**：bold、impactful、strong、dramatic、headlines
- **最适用于**：营销页、作品集、机构、活动页、体育
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { display: ['Bebas Neue', 'sans-serif'], body: ['Source Sans 3', 'sans-serif'] }
```
- **注意事项**：Bebas Neue 仅用于大型 hero 标题（≥ 48px），全大写场景。

## 15. Playful Creative 童趣创意

- **类别**：Display + Sans
- **标题字**：Fredoka
- **正文字**：Nunito
- **情绪关键词**：playful、friendly、fun、creative、warm
- **最适用于**：儿童应用、教育、游戏、创意工具、娱乐
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Fredoka', 'sans-serif'], body: ['Nunito', 'sans-serif'] }
```
- **注意事项**：圆润字体专为孩子和娱乐场景，B2B 勿用。

## 16. Financial Trust 金融信赖

- **类别**：Sans + Sans（单字族）
- **标题字**：IBM Plex Sans
- **正文字**：IBM Plex Sans
- **情绪关键词**：financial、trustworthy、professional、corporate、serious
- **最适用于**：银行、金融、保险、投资、Fintech、企业
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { sans: ['IBM Plex Sans', 'sans-serif'] }
```
- **注意事项**：IBM Plex 在数据密集表格中表现优异，金融 Dashboard 默认选项。

## 17. Legal Professional 法律权威

- **类别**：Serif + Sans
- **标题字**：EB Garamond
- **正文字**：Lato
- **情绪关键词**：legal、professional、traditional、trustworthy、formal
- **最适用于**：律所、法律、合同、正式文档、政府
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&family=Lato:wght@300;400;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&family=Lato:wght@300;400;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['EB Garamond', 'serif'], sans: ['Lato', 'sans-serif'] }
```
- **注意事项**：EB Garamond 古典感强，搭配 Lato 不显陈旧。

## 18. Medical Clean 医疗清洁

- **类别**：Sans + Sans
- **标题字**：Figtree
- **正文字**：Noto Sans
- **情绪关键词**：medical、clean、accessible、professional、trustworthy
- **最适用于**：医疗、诊所、制药、健康应用、无障碍
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&family=Noto+Sans:wght@300;400;500;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&family=Noto+Sans:wght@300;400;500;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { heading: ['Figtree', 'sans-serif'], body: ['Noto Sans', 'sans-serif'] }
```
- **注意事项**：Noto Sans 国际字符覆盖广，多语言医疗站必备。

## 19. Crypto/Web3 加密未来

- **类别**：Sans + Sans
- **标题字**：Orbitron
- **正文字**：Exo 2
- **情绪关键词**：crypto、web3、futuristic、tech、blockchain
- **最适用于**：加密平台、NFT、区块链、Web3、未来科技
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&family=Orbitron:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { display: ['Orbitron', 'sans-serif'], body: ['Exo 2', 'sans-serif'] }
```
- **注意事项**：Orbitron 仅用于标题与 logo，正文字勿用。

## 20. Gaming Bold 游戏冲击

- **类别**：Display + Sans
- **标题字**：Russo One
- **正文字**：Chakra Petch
- **情绪关键词**：gaming、bold、action、esports、energetic
- **最适用于**：游戏、电竞、动作游戏、竞技体育、娱乐
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Russo+One&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Russo+One&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { display: ['Russo One', 'sans-serif'], body: ['Chakra Petch', 'sans-serif'] }
```
- **注意事项**：Chakra Petch 科技感强，搭配 Russo One 形成游戏 HUD 美学。

## 21. Magazine Style 杂志风格

- **类别**：Serif + Sans
- **标题字**：Libre Bodoni
- **正文字**：Public Sans
- **情绪关键词**：magazine、editorial、publishing、journalism、print
- **最适用于**：杂志、在线出版物、编辑内容、新闻业
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Libre+Bodoni:wght@400;500;600;700&family=Public+Sans:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Libre+Bodoni:wght@400;500;600;700&family=Public+Sans:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Libre Bodoni', 'serif'], sans: ['Public Sans', 'sans-serif'] }
```
- **注意事项**：Bodoni 高对比衬线，标题 ≤ 28px 会失去冲击力。

## 22. Chinese Simplified 中文简体

- **类别**：Sans + Sans（单字族）
- **标题字**：Noto Sans SC
- **正文字**：Noto Sans SC
- **情绪关键词**：chinese、simplified、modern、professional、readable
- **最适用于**：简体中文站、中国大陆市场、商业应用
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { sans: ['Noto Sans SC', 'sans-serif'] }
```
- **注意事项**：Noto Sans SC 字体文件大（≥ 1MB），建议子集化或使用 CDN 分片。

## 23. Chinese Traditional 中文繁体

- **类别**：Serif + Sans
- **标题字**：Noto Serif TC
- **正文字**：Noto Sans TC
- **情绪关键词**：chinese、traditional、elegant、cultural、readable
- **最适用于**：繁体中文站、文化内容、港台市场
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Noto+Serif+TC:wght@400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Noto+Serif+TC:wght@400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { serif: ['Noto Serif TC', 'serif'], sans: ['Noto Sans TC', 'sans-serif'] }
```
- **注意事项**：繁体字笔画多，正文 ≥ 16px 阅读舒适。

## 24. Accessibility First 无障碍优先

- **类别**：Sans + Sans（单字族）
- **标题字**：Atkinson Hyperlegible
- **正文字**：Atkinson Hyperlegible
- **情绪关键词**：accessible、readable、inclusive、dyslexia-friendly、clear
- **最适用于**：无障碍关键场景、政府、医疗、包容性设计
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { sans: ['Atkinson Hyperlegible', 'sans-serif'] }
```
- **注意事项**：Braille Institute 设计，字母形态对低视力用户更友好。

## 25. Dashboard Data 仪表盘数据

- **类别**：Mono + Sans
- **标题字**：Fira Code
- **正文字**：Fira Sans
- **情绪关键词**：dashboard、data、analytics、technical、precise
- **最适用于**：仪表盘、分析、数据可视化、管理后台
- **Google Fonts URL**：
```
https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap
```
- **CSS @import**：
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```
- **Tailwind config**：
```js
fontFamily: { mono: ['Fira Code', 'monospace'], sans: ['Fira Sans', 'sans-serif'] }
```
- **注意事项**：Fira Code 用于数据/代码，Fira Sans 用于 UI 标签，单字族一致性强。

## 字体选择决策树

### 步骤 1：按行业大类锁定情绪

```
金融/银行/保险/法律 → 关键词"trustworthy + serious" → 候选 {Financial Trust, Legal Professional, Corporate Trust}
医疗/健康/无障碍 → 关键词"clean + accessible" → 候选 {Medical Clean, Accessibility First, Wellness Calm}
SaaS/生产力/工具 → 关键词"modern + professional" → 候选 {Modern Professional, Friendly SaaS, Tech Startup}
奢侈品/时尚/酒店 → 关键词"elegant + premium" → 候选 {Classic Elegant, Luxury Serif, Magazine Style}
媒体/出版/博客 → 关键词"editorial + readable" → 候选 {News Editorial, Editorial Classic, Magazine Style}
游戏/电竞/娱乐 → 关键词"bold + impactful" → 候选 {Gaming Bold, Bold Statement, Playful Creative}
开发者/技术文档 → 关键词"technical + precise" → 候选 {Developer Mono, Brutalist Raw, Dashboard Data}
Web3/加密/AI → 关键词"futuristic + tech" → 候选 {Crypto/Web3, Tech Startup}
儿童/教育轻量 → 关键词"playful + friendly" → 候选 {Playful Creative, Friendly SaaS}
中文场景 → 强制叠加 {Chinese Simplified 或 Chinese Traditional}
```

### 步骤 2：按品牌人格二次筛选

```
人格 = 严肃权威 → 选 Serif + Sans 组合（标题衬线 + 正文无衬线）
人格 = 现代专业 → 选 Sans + Sans（单字族或几何风）
人格 = 创意前卫 → 选 Display + Sans（强表现力标题）
人格 = 温暖亲和 → 选 Rounded Sans（Fredoka / Nunito / Varela Round）
人格 = 技术极客 → 选 Mono + Sans 或全 Mono
人格 = 高端奢华 → 选高对比 Serif（Playfair / Bodoni / Cormorant）
```

### 步骤 3：按落地场景三选

```
场景 = 落地页/营销页 → 标题字重 700+ 配大字号，允许 Display 字体
场景 = SaaS Dashboard → 优先单字族（Inter / Plus Jakarta Sans / IBM Plex Sans）
场景 = 长文阅读 → 优先 Serif 正文（Libre Baskerville / Newsreader / Lora）
场景 = 移动端 → 避开 Bebas Neue / Orbitron 等过窄过宽字体
场景 = 多语言 → 必须用 Noto Sans 系列
场景 = 极致性能 → 单字族 + 3 个字重，preload woff2
```

## 反模式与避坑

1. **同一页面 3+ 字族**：性能差且无层级感
2. **正文字重 < 400**：小屏阅读困难
3. **标题字重 < 600**：缺乏视觉锚点
4. **Cormorant / Playfair 用于正文**：太装饰，阅读疲劳
5. **Bebas Neue 用于长段落**：全大写 + 窄身，无法阅读
6. **加载全字重 (100-900)**：浪费 200KB+，按需选 3-4 个字重
7. **中文站用纯英文字族**：fallback 链断裂，中文回退到系统字
8. **忽视 `display=swap`**：首屏白屏 1-3s
9. **Noto Sans SC 全量加载**：1MB+ 文件，必须子集化
10. **Atkinson Hyperlegible 用于奢侈品**：可读性优先但缺乏优雅感
11. **未设置 fallback**：`font-family: 'Inter'` 必须补 `sans-serif`
12. **等宽字体用于正文**：阅读速度降 30%
