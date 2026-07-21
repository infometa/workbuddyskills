---
id: landing-patterns
title: 落地页模式库（24 种 + section 顺序 + 转化优化）
domain: design-systems
quality_score: 95
last_updated: 2026-07-19
---

# 落地页模式库（24 种 + section 顺序 + 转化优化）

24 种商业级落地页模式，每种均给出可照搬的版块顺序、主 CTA 放置位置、配色策略、推荐效果与转化优化要点。所有模式均按真实商业项目频率加权，覆盖 SaaS、电商、AI、Web3、活动、企业等全部主流场景。

## 通用规范

- "主 CTA 放置位置"指首屏可见 + 滚动后重复出现的位置
- 配色策略中的"7:1"指 CTA 与背景对比比，最低不低于 AA 4.5:1
- 推荐效果均需配合 `prefers-reduced-motion` 提供 fallback

## 1. Hero + Features + CTA 经典三段式

- **关键词**：hero-centric、features、call-to-action
- **版块顺序**：
  1. Hero（headline + image）
  2. Value proposition
  3. Key features（3-5 个）
  4. CTA section
  5. Footer
- **主 CTA 放置位置**：Hero（sticky navbar）+ Bottom
- **配色策略**：Hero 用品牌主色或鲜艳色；Features 卡片底 #FAFAFA；CTA 用对比 accent
- **推荐效果**：hero parallax、feature card hover lift、CTA glow on hover
- **转化优化要点**：CTA 对比 ≥ 7:1；navbar 持续 sticky CTA；features 一卡一核心信息

## 2. Hero + Testimonials + CTA 信任驱动

- **关键词**：testimonials、social proof、reviews
- **版块顺序**：
  1. Hero
  2. Problem statement
  3. Solution overview
  4. Testimonials carousel
  5. CTA
- **主 CTA 放置位置**：Hero（sticky）+ Post-testimonials
- **配色策略**：Hero 品牌色；Testimonials 浅底 #F5F5F5；引文斜体 muted #666；CTA 鲜艳
- **推荐效果**：testimonial 轮播滑动、引号动画、avatar fade-in
- **转化优化要点**：3-5 条证言；含照片 + 姓名 + 职位；CTA 紧跟 social proof 之后

## 3. Product Demo + Features 产品演示

- **关键词**：product demo、interactive、showcase
- **版块顺序**：
  1. Hero
  2. 产品视频/mockup（居中）
  3. 功能分解（每节一功能）
  4. 对比（可选）
  5. CTA
- **主 CTA 放置位置**：视频中心 + 右下/底部
- **配色策略**：视频区品牌色覆盖；Features icon #0080FF；正文 #222
- **推荐效果**：play button pulse、scroll reveal feature、demo interaction highlight
- **转化优化要点**：嵌入产品 Demo 提升参与度；交互 mockup 优于静态图；视频静音自动播放

## 4. Minimal Single Column 极简单栏

- **关键词**：minimal、simple、direct、single-column
- **版块顺序**：
  1. Hero headline
  2. 简短描述
  3. 3 个利益点 bullet
  4. CTA
  5. Footer
- **主 CTA 放置位置**：居中大按钮
- **配色策略**：品牌色 + 纯白 + accent；按钮对比 ≥ 7:1
- **推荐效果**：minimal hover、smooth scroll、CTA scale hover
- **转化优化要点**：单一 CTA 聚焦；大字号；大量留白；移动端优先

## 5. Funnel 3-Step Conversion 漏斗三步

- **关键词**：funnel、conversion、steps、wizard
- **版块顺序**：
  1. Hero
  2. Step 1（problem）
  3. Step 2（solution）
  4. Step 3（action）
  5. CTA progression
- **主 CTA 放置位置**：每步 mini-CTA + 最终 main CTA
- **配色策略**：Step 1 红（problem）/ Step 2 橙（process）/ Step 3 绿（solution）；CTA 品牌色
- **推荐效果**：step number 动画、progress bar 填充、smooth scroll 过渡
- **转化优化要点**：渐进 disclosure；每步仅核心信息；进度指示器；多 CTA 重复

## 6. Comparison Table + CTA 对比表

- **关键词**：comparison、versus、compare
- **版块顺序**：
  1. Hero
  2. Problem intro
  3. 对比表（你 vs 竞品）
  4. 价格（可选）
  5. CTA
- **主 CTA 放置位置**：表格右列 + 表格下方
- **配色策略**：交替行（白/浅灰）；你的产品行高亮 #FFFACD 或绿；正文深色
- **推荐效果**：表格行 hover、价格 toggle、checkmark 动画
- **转化优化要点**：突出你的行；价格行含"free trial"

## 7. Lead Magnet + Form 引磁表单

- **关键词**：lead、form、signup、email、magnet
- **版块顺序**：
  1. Hero（benefit headline）
  2. Lead magnet 预览（ebook 封面、checklist 等）
  3. Form（最少字段）
  4. CTA submit
- **主 CTA 放置位置**：Form submit 按钮
- **配色策略**：Lead magnet 专业设计；Form 白底；输入框浅边框 #CCC；CTA 品牌色
- **推荐效果**：form focus state、validation 实时、success 确认
- **转化优化要点**：表单字段 ≤ 3；提供有价值的预览；显示提交进度

## 8. Pricing Page + CTA 定价页

- **关键词**：pricing、plans、tiers
- **版块顺序**：
  1. Hero（pricing headline）
  2. 价格对比卡（3 档）
  3. 功能对比表
  4. FAQ
  5. Final CTA
- **主 CTA 放置位置**：每卡 CTA + Navbar sticky CTA
- **配色策略**：Free 灰 / Starter 蓝 / Pro 绿或金 / Enterprise 深
- **推荐效果**：月/年切换动画、卡片对比高亮、FAQ accordion
- **转化优化要点**：预选/高亮 starter；显示年付折扣 20-30%；FAQ 解决顾虑

## 9. Video-First Hero 视频首屏

- **关键词**：video、hero、media、engaging
- **版块顺序**：
  1. Hero（video 背景）
  2. Key features overlay
  3. Benefits section
  4. CTA
- **主 CTA 放置位置**：视频上叠加（中下）+ 底部
- **配色策略**：视频 60% 暗覆盖；品牌 accent CTA；白色文字
- **推荐效果**：video autoplay muted、parallax scroll、text fade-in
- **转化优化要点**：视频提升 86% 参与度；加字幕；压缩视频

## 10. Scroll-Triggered Storytelling 滚动叙事

- **关键词**：storytelling、scroll、narrative、immersive
- **版块顺序**：
  1. Intro hook
  2. Chapter 1（problem）
  3. Chapter 2（journey）
  4. Chapter 3（solution）
  5. Climax CTA
- **主 CTA 放置位置**：每章末尾 mini + 最终 climax CTA
- **配色策略**：渐进 reveal；每章不同色；构建 intensity
- **推荐效果**：ScrollTrigger、parallax layers、progressive disclosure、chapter transition
- **转化优化要点**：叙事提升 3x 停留时长；进度指示器；移动端简化动画

## 11. AI Personalization Landing AI 个性化

- **关键词**：ai、personalization、smart、recommendation
- **版块顺序**：
  1. Dynamic hero（个性化）
  2. 相关 features
  3. 定制 testimonials
  4. Smart CTA
- **主 CTA 放置位置**：基于用户 segment 上下文放置
- **配色策略**：基于用户数据自适应；A/B 测试 per segment
- **推荐效果**：dynamic content swap、fade transition、个性化推荐
- **转化优化要点**：个性化提升 20%+ 转化；需 analytics 集成；新用户 fallback

## 12. Waitlist / Coming Soon 候补名单

- **关键词**：waitlist、coming-soon、launch、early-access
- **版块顺序**：
  1. Hero with countdown
  2. Product teaser/preview
  3. Email capture form
  4. Social proof（waitlist count）
- **主 CTA 放置位置**：Email form above fold + sticky on scroll
- **配色策略**：anticipation 深色 + accent 高亮；countdown 品牌色；urgency 指示
- **推荐效果**：countdown 动画、email validation、success confetti、social share
- **转化优化要点**：稀缺性 + 独占性；展示候补人数；早鸟权益；推荐奖励

## 13. Comparison Table Focus 对比表主导

- **关键词**：comparison、versus、features
- **版块顺序**：
  1. Hero（problem statement）
  2. 对比矩阵（你 vs 竞品）
  3. Feature deep-dive
  4. Winner CTA
- **主 CTA 放置位置**：对比表后（高亮行）+ 底部
- **配色策略**：你的列高亮（accent 底或绿）；竞品中性；checkmark 绿
- **推荐效果**：表格行 hover、checkmark 动画、sticky header
- **转化优化要点**：展示对竞品价值；转化率提升 35%；事实为主；价格友好时展示

## 14. Pricing-Focused Landing 定价主导

- **关键词**：pricing、price、cost、plans、subscription
- **版块顺序**：
  1. Hero（value proposition）
  2. 定价卡（3 档）
  3. 功能对比
  4. FAQ
  5. Final CTA
- **主 CTA 放置位置**：每定价卡 + Navbar sticky + 底部
- **配色策略**：Popular plan 高亮（品牌色边框/底）；Free 灰；Enterprise 深/premium
- **推荐效果**：月/年切换动画、卡片 hover lift、FAQ accordion
- **转化优化要点**：年付折扣 20-30%；推荐 mid-tier "most popular" 徽章；FAQ 解决顾虑

## 15. App Store Style Landing 应用商店风

- **关键词**：app、mobile、download、store、install
- **版块顺序**：
  1. Hero（设备 mockup）
  2. Screenshots 轮播
  3. Features with icons
  4. Reviews/ratings
  5. Download CTAs
- **主 CTA 放置位置**：Download 按钮（App Store + Play Store）通栏
- **配色策略**：应用商店风深/浅适配；星评金；截图带设备框
- **推荐效果**：设备 mockup 旋转、screenshot slider、star animation、download pulse
- **转化优化要点**：真实截图；评分 4.5+；移动端 QR code；平台专属 CTA

## 16. FAQ / Documentation Landing 文档主导

- **关键词**：faq、documentation、help、support、knowledge base
- **版块顺序**：
  1. Hero（搜索框）
  2. Popular categories
  3. FAQ accordion
  4. Contact/support CTA
- **主 CTA 放置位置**：搜索框突出 + 未解决问题 Contact CTA
- **配色策略**：高可读性；最小色彩；类别 icon 品牌色；已解决绿
- **推荐效果**：search autocomplete、accordion 平滑开合、category hover
- **转化优化要点**：减少 support ticket；跟踪搜索分析；相关文章；联系升级路径

## 17. Immersive / Interactive Experience 沉浸交互

- **关键词**：immersive、interactive、3d、animation
- **版块顺序**：
  1. Full-screen interactive element
  2. Guided product tour
  3. Key benefits revealed
  4. CTA after completion
- **主 CTA 放置位置**：交互完成后 + Skip 选项
- **配色策略**：沉浸色；深色背景聚焦；高亮交互元素
- **推荐效果**：WebGL、3D 交互、gamification、progress indicator、reward animation
- **转化优化要点**：参与度提升 40%；性能权衡；提供 skip；移动端 fallback 必备

## 18. Event / Conference Landing 活动会议

- **关键词**：event、conference、meetup、registration、schedule
- **版块顺序**：
  1. Hero（日期/地点/countdown）
  2. Speakers grid
  3. Agenda/schedule
  4. Sponsors
  5. Register CTA
- **主 CTA 放置位置**：Register sticky + Speakers 后 + 底部
- **配色策略**：urgency 色（countdown）；活动品牌；speaker 卡专业；sponsor 中性
- **推荐效果**：countdown timer、speaker hover bio、agenda tabs、early bird countdown
- **转化优化要点**：早鸟价 + 截止时间；过往参会 social proof；speaker 信誉；多票折扣

## 19. Product Review / Ratings Focused 评价驱动

- **关键词**：reviews、ratings、testimonials、stars
- **版块顺序**：
  1. Hero（product + aggregate rating）
  2. Rating breakdown
  3. Individual reviews
  4. Buy/CTA
- **主 CTA 放置位置**：reviews summary 后 + Buy 旁
- **配色策略**：trust 色；星评金；verified 绿；review sentiment 色
- **推荐效果**：star fill animation、review filtering、helpful vote、photo lightbox
- **转化优化要点**：UGC 建立信任；verified purchase；按评分筛选；回应差评

## 20. Community / Forum Landing 社区论坛

- **关键词**：community、forum、social、members、discussion
- **版块顺序**：
  1. Hero（社区价值主张）
  2. Popular topics/categories
  3. Active members showcase
  4. Join CTA
- **主 CTA 放置位置**：Join 突出 + member showcase 后
- **配色策略**：温暖欢迎；member 照片增人情；topic 徽章品牌色；activity 绿
- **推荐效果**：member avatar 动画、activity feed live update、topic hover preview、join celebration
- **转化优化要点**：展示活跃社区（成员数、今日帖子）；突出权益；预览内容；easy onboarding

## 21. Before-After Transformation 前后对比

- **关键词**：before-after、transformation、results、comparison
- **版块顺序**：
  1. Hero（problem state）
  2. Transformation slider/comparison
  3. How it works
  4. Results CTA
- **主 CTA 放置位置**：transformation 揭示后 + 底部
- **配色策略**：对比 muted/grey（前）vs vibrant（后）；success 绿表结果
- **推荐效果**：slider 对比、reveal 动画、result counter、testimonial video
- **转化优化要点**：视觉价值证明；转化率提升 45%；真实结果；具体指标；保证 offer

## 22. Marketplace / Directory 市场目录

- **关键词**：marketplace、directory、search、listing
- **版块顺序**：
  1. Hero（搜索主导）
  2. Categories
  3. Featured Listings
  4. Trust/Safety
  5. CTA（Become a host/seller）
- **主 CTA 放置位置**：Hero 搜索栏 + Navbar 'List your item'
- **配色策略**：搜索高对比；Categories 视觉 icon；Trust 蓝/绿
- **推荐效果**：search autocomplete、map hover pins、card carousel
- **转化优化要点**：搜索栏即 CTA；降低搜索摩擦；热门搜索建议

## 23. Newsletter / Content First 简报内容

- **关键词**：newsletter、content、writer、blog、subscribe
- **版块顺序**：
  1. Hero（Value Prop + Form）
  2. Recent Issues/Archives
  3. Social Proof（Subscriber count）
  4. About Author
- **主 CTA 放置位置**：Hero inline form + Sticky header form
- **配色策略**：极简；纸感背景；文字聚焦；Subscribe accent
- **推荐效果**：text highlight、typewriter effect、subtle fade-in
- **转化优化要点**：单字段表单（仅 Email）；显示"Join X,000 readers"；sample 阅读链接

## 24. Webinar Registration 网络研讨会注册

- **关键词**：webinar、registration、event、training、live
- **版块顺序**：
  1. Hero（Topic + Timer + Form）
  2. What you'll learn
  3. Speaker Bio
  4. Urgency/Bonuses
  5. Form（再次）
- **主 CTA 放置位置**：Hero（右侧 form）+ 底部锚点
- **配色策略**：urgency 红橙；professional 蓝海军；Form 高对比白
- **推荐效果**：countdown timer、speaker avatar float、urgent ticker
- **转化优化要点**：限座逻辑；"Live" 指示；自动填充时区

## 落地页模式选择指南

### 步骤 1：按产品类型初选

```
SaaS / B2B 工具 → 候选 {1. Hero+Features+CTA, 4. Minimal Single Column, 8. Pricing Page}
新产品发布 → 候选 {3. Product Demo, 9. Video-First Hero, 12. Waitlist}
AI 产品 → 候选 {11. AI Personalization, 30. AI-Driven Dynamic, 3. Product Demo}
移动 App → 候选 {15. App Store Style, 4. Minimal Single Column}
电商 / 零售 → 候选 {1. Hero+Features, 6. Comparison Table, 14. Pricing-Focused}
企业 / B2B 服务 → 候选 {25. Enterprise Gateway, 33. Trust & Authority, 8. Pricing Page}
活动 / 会议 → 候选 {18. Event/Conference, 24. Webinar Registration}
内容 / 出版 → 候选 {23. Newsletter, 16. FAQ/Documentation}
社区 / 社交 → 候选 {20. Community/Forum, 19. Product Review}
NFT / Web3 → 候选 {12. Waitlist, 17. Immersive, 29. Interactive 3D}
奢华品牌 → 候选 {10. Scroll Storytelling, 17. Immersive, 26. Portfolio Grid}
```

### 步骤 2：按转化目标二选

```
目标 = 注册/Lead → 7. Lead Magnet + Form, 4. Minimal Single Column
目标 = 试用/Demo → 3. Product Demo, 29. Interactive 3D Configurator
目标 = 付费/订阅 → 8. Pricing Page, 14. Pricing-Focused
目标 = 候补/预热 → 12. Waitlist/Coming Soon
目标 = 信任/成交 → 2. Hero+Testimonials, 19. Product Review, 33. Trust & Authority
目标 = 报名/参会 → 18. Event, 24. Webinar Registration
目标 = 加入/活跃 → 20. Community/Forum
目标 = 教育/支持 → 16. FAQ/Documentation
目标 = 品牌叙事 → 10. Scroll Storytelling, 17. Immersive
目标 = 对比胜出 → 6. Comparison Table, 13. Comparison Table Focus
```

### 步骤 3：按受众特征三选

```
受众 = 企业决策者 → 优先 {25. Enterprise Gateway, 33. Trust & Authority}
受众 = 开发者 → 优先 {16. FAQ/Documentation, 29. Interactive 3D}
受众 = Z 世代 → 优先 {17. Immersive, 27. Horizontal Scroll Journey, 28. Bento Grid}
受众 = 高净值 → 优先 {26. Portfolio Grid, 10. Scroll Storytelling, 17. Immersive}
受众 = 移动端为主 → 优先 {4. Minimal Single Column, 15. App Store Style}
受众 = 理性比较型 → 优先 {6. Comparison Table, 8. Pricing Page}
受众 = 感性叙事型 → 优先 {10. Scroll Storytelling, 21. Before-After}
受众 = 紧迫驱动型 → 优先 {12. Waitlist, 18. Event, 24. Webinar}
```

## 通用转化优化清单

### CTA 设计

1. 主 CTA 必须出现在 hero + 中段 + 底部，至少 3 次
2. CTA 按钮对比 ≥ 7:1（远超 WCAG AA 4.5:1）
3. CTA 文案用动词 + 利益（"Get Free Audit" > "Submit"）
4. Navbar CTA 必须 sticky，滚动后持续可见
5. 移动端 CTA 在底部 sticky bar 重复出现

### Hero 区域

1. Hero 必须在 6 秒内传达：你是谁、做什么、为谁做
2. Headline ≤ 12 字，subheadline ≤ 30 字
3. Hero 视觉必须直接展示产品或结果，避免抽象图
4. 首屏 CTA 之上不能有 3+ 链接分流
5. LCP < 2.5s，移动端首屏 < 3s

### Social Proof

1. 至少 3-5 条证言，含照片 + 全名 + 职位 + 公司
2. 优先展示知名公司 logo（含客户数 + 案例）
3. 数据型 social proof（"10,000+ users"）比形容词更有力
4. 第三方评测（G2 / Capterra / Trustpilot）可信度 > 自证言
5. 视频证言转化率比文字高 2x

### 价格与对比

1. 3 档定价是黄金结构（Free / Pro / Enterprise 或 Starter / Pro / Team）
2. 中档预选 + "Most Popular" 徽章提升 30% 选择率
3. 年付折扣 20-30% + 月付默认切换
4. 价格对比表 highlight 你的列
5. FAQ 解决"隐藏费用""退款""升级"三大顾虑

### 表单优化

1. 字段 ≤ 3（Email + Name + Company 即可）
2. 实时 validation，错误提示友好
3. 多步表单（wizard）比单页长表单转化高 27%
4. progress bar 必备，让用户知道还剩几步
5. 提交后立即明确下一步（"我们将在 24h 内联系您"）

## 反模式与避坑

1. **首屏无 CTA**：30% 用户在 hero 即决定跳出
2. **CTA 文案用"Submit"**：转化率比"Get Started"低 35%
3. **Hero 用抽象插图**：用户不知道你做什么
4. **功能堆砌 10+ 卡片**：信息过载，用户记不住
5. **价格隐藏在 FAQ 后**：B2B 用户跳出率 60%
6. **证言无照片无职位**：可信度归零
7. **表单字段 7+ 项**：转化率降 50%
8. **首屏视频自动播放有声音**：移动端跳出率 70%
9. **countdown 倒计时无意义**：虚假紧迫感损害信任
10. **comparison 表硬黑竞品**：失去可信度，事实胜过形容词
11. **忽视 mobile sticky CTA**：移动端转化损失 40%
12. **Hero 用 LCP > 3s 的视频/3D**：50% 用户在 3s 内跳出
