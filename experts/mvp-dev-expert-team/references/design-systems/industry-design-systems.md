---
id: industry-design-systems
title: 行业设计系统推荐（商业级推理规则）
domain: design-systems
quality_score: 95
last_updated: 2026-07-19
---

# 行业设计系统推荐（商业级推理规则）

针对 30 个商业高频行业，给出可直接落地的设计系统推荐。每条推荐包含落地页模式、风格优先级、配色氛围、字体情绪、关键效果、可执行的决策规则、以及明确不要做什么。决策规则采用 JSON 条件格式，可直接被生成式 Agent 解析使用。

## 1. SaaS（通用）

- **推荐落地页模式**：Hero + Features + CTA
- **风格优先级**：主 Glassmorphism / 备 Flat Design
- **配色氛围**：信任蓝 #2563EB + 橙色 CTA #EA580C 对比
- **字体情绪**：专业 + 层级清晰（Inter / Plus Jakarta Sans）
- **关键效果**：subtle hover 200-250ms + smooth transition
- **决策规则**：
```json
{
  "if_ux_focused": "prioritize-minimalism",
  "if_data_heavy": "add-glassmorphism",
  "if_ai_feature": "add-aurora-hero",
  "if_enterprise_buyer": "switch-to-trust-authority"
}
```
- **反模式**：过度动效、默认深色模式、紫色大面积铺底

## 2. 微 SaaS / 独立开发者产品

- **推荐落地页模式**：Hero-Centric + Trust Strip
- **风格优先级**：主 Motion-Driven / 备 Vibrant & Block-based
- **配色氛围**：Indigo #6366F1 + Emerald CTA #059669
- **字体情绪**：现代 + 活力（Space Grotesk + DM Sans）
- **关键效果**：scroll-triggered + parallax hero
- **决策规则**：
```json
{
  "if_pre_launch": "use-waitlist-pattern",
  "if_video_ready": "add-hero-video",
  "if_no_brand_assets": "use-bold-typography-as-hero"
}
```
- **反模式**：静态设计、无视频、移动端体验差

## 3. 电商（通用）

- **推荐落地页模式**：Feature-Rich Showcase
- **风格优先级**：主 Vibrant & Block-based / 备 Bento Box Grid
- **配色氛围**：成功绿 #059669 + 紧迫橙 #EA580C
- **字体情绪**：清晰可读 + 转化导向（Rubik + Nunito Sans）
- **关键效果**：hover lift + 快速图片加载 + wishlist 心跳
- **决策规则**：
```json
{
  "if_high_sku_count": "add-search-first-hero",
  "if_luxury_sku": "switch-to-liquid-glass",
  "if_promotion_heavy": "add-countdown-banner"
}
```
- **反模式**：纯静态产品图、无价格高亮、CTA 不固定

## 4. 电商奢侈品

- **推荐落地页模式**：Feature-Rich Showcase + Storytelling
- **风格优先级**：主 Liquid Glass / 备 Glassmorphism
- **配色氛围**：深黑 #1C1917 + 金色 #A16207
- **字体情绪**：高贵 + timeless（Cormorant + Montserrat）
- **关键效果**：慢镜头视频、parallax 滚动、产品 360°
- **决策规则**：
```json
{
  "if_no_budget_for_video": "fallback-to-large-photography",
  "if_jewelry": "add-macro-3d",
  "if_fashion": "use-editorial-grid"
}
```
- **反模式**：用荧光色、堆砌徽章、价格过低锚定

## 5. 金融科技 / Fintech

- **推荐落地页模式**：Trust & Authority + Features
- **风格优先级**：主 Minimalism / 备 Accessible & Ethical
- **配色氛围**：金 #F59E0B + 紫 #8B5CF6 + 深底 #0F172A
- **字体情绪**：严肃 + 精确（IBM Plex Sans）
- **关键效果**：数据 ticker + 透明度提示
- **决策规则**：
```json
{
  "if_crypto_wallet": "must-have-wallet-connect",
  "if_trading_dashboard": "use-dark-mode-default",
  "if_compliance_required": "force-accessible-ethics"
}
```
- **反模式**：默认浅色 + 无交易状态 + 隐藏手续费

## 6. 银行 / 传统金融

- **推荐落地页模式**：Trust & Authority + Features
- **风格优先级**：主 Minimalism / 备 Accessible & Ethical
- **配色氛围**：海军蓝 #0F172A + 金 #A16207
- **字体情绪**：权威 + 信赖（IBM Plex Sans / Lexend）
- **关键效果**：极少动效 + logo 信任墙
- **决策规则**：
```json
{
  "if_senior_audience": "force-large-type-and-aaa",
  "if_loan_product": "add-calculator-widget",
  "if_credit_card": "use-3d-card-render"
}
```
- **反模式**：渐变背景、动画过多、字体过细

## 7. 保险

- **推荐落地页模式**：Conversion-Optimized + Trust
- **风格优先级**：主 Trust & Authority / 备 Flat Design
- **配色氛围**：安全蓝 #0369A1 + 保障绿 #16A34A
- **字体情绪**：保障 + 安心（Lexend + Source Sans 3）
- **关键效果**：表单 focus 引导 + 保费实时计算
- **决策规则**：
```json
{
  "if_quote_tool": "use-multi-step-funnel",
  "if_health_insurance": "add-doctor-network-lookup",
  "if_legacy_brand": "preserve-corporate-color"
}
```
- **反模式**：长表单一屏、隐藏免责条款、强紧迫感

## 8. 医疗诊所

- **推荐落地页模式**：Trust & Authority + Conversion
- **风格优先级**：主 Accessible & Ethical / 备 Minimalism
- **配色氛围**：医疗青 #0891B2 + 健康绿 #16A34A
- **字体情绪**：清洁 + 可达（Figtree + Noto Sans）
- **关键效果**：预约日历 + 医生卡 hover
- **决策规则**：
```json
{
  "if_appointment_booking": "add-inline-scheduler",
  "if_insurance_accepted": "show-network-logos",
  "if_pediatric": "soften-to-claymorphism"
}
```
- **反模式**：红色大面积、医疗术语堆砌、无在线预约

## 9. 牙科

- **推荐落地页模式**：Social Proof-Focused + Conversion
- **风格优先级**：主 Soft UI Evolution / 备 Minimalism
- **配色氛围**：医疗青 #0891B2 + 净白 #F0FDFA
- **字体情绪**：温和 + 专业（Figtree + Noto Sans）
- **关键效果**：before/after slider + 评分轮播
- **决策规则**：
```json
{
  "if_cosmetic_dentistry": "add-before-after-gallery",
  "if_emergency_service": "add-prominent-call-button",
  "if_family_clinic": "add-kids-friendly-illustrations"
}
```
- **反模式**：疼痛感图片、过冷蓝色、无医生介绍

## 10. 心理健康 / 冥想

- **推荐落地页模式**：Social Proof-Focused
- **风格优先级**：主 Neumorphism / 备 Accessible & Ethical
- **配色氛围**：薰衣草紫 #8B5CF6 + 平静绿 #059669
- **字体情绪**：平静 + 治愈（Lora + Raleway）
- **关键效果**：呼吸圆环动画 + 渐进 disclosure
- **决策规则**：
```json
{
  "if_crisis_hotline": "add-emergency-prominent-button",
  "if_therapy_session": "add-therapist-matching-flow",
  "if_meditation_app": "use-ambient-sound-on-hero"
}
```
- **反模式**：紧迫感文案、红色警告、强推销感

## 11. 美容水疗 / Wellness

- **推荐落地页模式**：Hero-Centric + Social Proof
- **风格优先级**：主 Soft UI Evolution / 备 Neumorphism
- **配色氛围**：柔粉 #EC4899 + 薰衣草 #8B5CF6
- **字体情绪**：温柔 + 高级（Playfair Display + Inter）
- **关键效果**：服务卡 + 价格透明 + 预约 widget
- **决策规则**：
```json
{
  "if_online_booking": "add-sticky-booking-bar",
  "if_membership": "add-benefits-comparison",
  "if_before_after": "add-slider-comparison"
}
```
- **反模式**：过暗背景、无价格、无地点信息

## 12. 餐饮 / 餐厅

- **推荐落地页模式**：Hero-Centric + Conversion
- **风格优先级**：主 Vibrant & Block-based / 备 Motion-Driven
- **配色氛围**：食欲红 #DC2626 + 暖金 #A16207
- **字体情绪**：诱人 + 优雅（Playfair Display SC + Karla）
- **关键效果**：菜品大图 parallax + 在线点单 CTA
- **决策规则**：
```json
{
  "if_online_order": "add-sticky-order-button",
  "if_reservation": "add-opentable-widget",
  "if_menu_pdf": "replace-with-html-menu"
}
```
- **反模式**：PDF 菜单、无图片、无营业时间、过暗

## 13. 酒店 / 酒店

- **推荐落地页模式**：Hero-Centric + Social Proof
- **风格优先级**：主 Liquid Glass / 备 Minimalism
- **配色氛围**：海军蓝 #1E3A8A + 金 #A16207
- **字体情绪**：高贵 + 服务感（Cormorant + Montserrat）
- **关键效果**：360° 房间预览 + 价格日历
- **决策规则**：
```json
{
  "if_booking_engine": "add-real-time-rate",
  "if_resort": "add-aerial-video",
  "if_business_hotel": "add-meeting-room-showcase"
}
```
- **反模式**：低分辨率房间图、隐藏税费、无取消政策

## 14. 法律服务

- **推荐落地页模式**：Trust & Authority + Minimal
- **风格优先级**：主 Trust & Authority / 备 Minimalism
- **配色氛围**：权威海军蓝 #1E3A8A + 信任金 #B45309
- **字体情绪**：权威 + 传统（EB Garamond + Lato）
- **关键效果**：执业证章 + 案例时间线
- **决策规则**：
```json
{
  "if_free_consultation": "add-prominent-form",
  "if_practice_area_diverse": "add-area-cards",
  "if_high_profile_cases": "add-press-logos"
}
```
- **反模式**：闪亮动效、卡通图标、过度承诺文案

## 15. 教育 / 在线课程

- **推荐落地页模式**：Feature-Rich + Social Proof
- **风格优先级**：主 Claymorphism / 备 Vibrant & Block-based
- **配色氛围**：进度青 #0D9488 + 成就橙 #EA580C
- **字体情绪**：友好 + 进取（Poppins + Open Sans）
- **关键效果**：学习路径可视化 + 进度条 + 讲师卡
- **决策规则**：
```json
{
  "if_k12": "add-parent-testimonials",
  "if_coding_bootcamp": "add-dark-mode-coding-demo",
  "if_self_paced": "add-curriculum-modal"
}
```
- **反模式**：纯文字课程介绍、无试听、隐藏讲师背景

## 16. 作品集 / 个人品牌

- **推荐落地页模式**：Portfolio Grid + Storytelling
- **风格优先级**：主 Motion-Driven / 备 Minimalism
- **配色氛围**：单色 #18181B + 蓝 #2563EB accent
- **字体情绪**：克制 + 个性（Space Grotesk + Archivo）
- **关键效果**：项目卡 hover overlay + lightbox
- **决策规则**：
```json
{
  "if_designer": "use-large-typography-hero",
  "if_developer": "add-github-readme-style-stats",
  "if_photographer": "use-pure-black-fullbleed"
}
```
- **反模式**：长篇自我介绍首屏、低清作品图、无联系方式

## 17. 创意机构 / Agency

- **推荐落地页模式**：Storytelling + Feature-Rich
- **风格优先级**：主 Brutalism / 备 Motion-Driven
- **配色氛围**：大胆撞色 + 黑边
- **字体情绪**：先锋 + 强势（Syne + Manrope）
- **关键效果**：案例研究滚动叙事 + 大字号 manifesto
- **决策规则**：
```json
{
  "if_award_winner": "add-trophy-strip",
  "if_client_logos": "add-marquee-row",
  "if_team_personality": "add-meet-the-team-bento"
}
```
- **反模式**：模板感、行业套话、无作品案例

## 18. 游戏 / 游戏发行

- **推荐落地页模式**：Feature-Rich Showcase
- **风格优先级**：主 3D & Hyperrealism / 备 Dark Mode OLED
- **配色氛围**：霓虹紫 #7C3AED + 玫红 #F43F5E + 深空 #0F0F23
- **字体情绪**：冲击 + 动作（Russo One + Chakra Petch）
- **关键效果**：3D 角色 + 视差场景 + 预告片自动播放
- **决策规则**：
```json
{
  "if_pre_register": "add-countdown-and-rewards",
  "if_multiplayer": "add-friend-invite-cta",
  "if_mobile_game": "add-app-store-badges"
}
```
- **反模式**：静态截图首屏、无视频、无平台标识

## 19. 音乐流媒体

- **推荐落地页模式**：Feature-Rich Showcase
- **风格优先级**：主 Dark Mode OLED / 备 Vibrant & Block-based
- **配色氛围**：深紫 #1E1B4B + 播放绿 #22C55E
- **字体情绪**：沉浸 + 节奏（Righteous + Poppins）
- **关键效果**：波形可视化 + 专辑卡 hover play
- **决策规则**：
```json
{
  "if_artist_led": "add-artist-spotlight",
  "if_podcast_heavy": "add-episode-list",
  "if_social_feature": "add-friend-activity"
}
```
- **反模式**：自动播放音乐、首屏无试听、强注册墙

## 20. 习惯追踪 / 自我提升

- **推荐落地页模式**：Social Proof-Focused + Demo
- **风格优先级**：主 Claymorphism / 备 Vibrant & Block-based
- **配色氛围**：成就感橙 + 成功绿 + 暖背景
- **字体情绪**：鼓励 + 友好（Fredoka + Nunito）
- **关键效果**：streak 计数动画 + 答卡堆叠
- **决策规则**：
```json
{
  "if_premium_unlock": "add-streak-recovery-preview",
  "if_community": "add-shared-goals-feed",
  "if_gamification": "add-badges-showcase"
}
```
- **反模式**：失败惩罚感强、深色压抑、无快速试玩

## 21. 食谱 / 烹饪

- **推荐落地页模式**：Hero-Centric + Feature-Rich
- **风格优先级**：主 Claymorphism / 备 Vibrant & Block-based
- **配色氛围**：食欲红橙 + 暖米
- **字体情绪**：诱人 + 清晰（Playfair Display SC + Karla）
- **关键效果**：步骤图滚动 + 食材清单 sticky + 视频教学
- **决策规则**：
```json
{
  "if_video_recipe": "add-autoplay-muted-loop",
  "if_shopping_list": "add-one-click-export",
  "if_dietary_filter": "add-vegan-gluten-free-toggle"
}
```
- **反模式**：长篇故事前置、无打印版、无份量切换

## 22. 冥想 / 正念

- **推荐落地页模式**：Storytelling + Social Proof
- **风格优先级**：主 Neumorphism / 备 Soft UI Evolution
- **配色氛围**：薰衣草 + 海雾 + 渐变天空
- **字体情绪**：舒缓 + 内省（Lora + Raleway）
- **关键效果**：呼吸圆环 + 环境音试听
- **决策规则**：
```json
{
  "if_sleep_stories": "add-night-mode-default",
  "if_free_trial": "add-7-day-no-card",
  "if_corporate_wellness": "add-b2b-section"
}
```
- **反模式**：强推销、闪烁 banner、紧迫倒计时

## 23. 天气

- **推荐落地页模式**：Hero-Centric
- **风格优先级**：主 Glassmorphism / 备 Aurora UI
- **配色氛围**：天空蓝 + 极光渐变
- **字体情绪**：清晰 + 直观（Inter 单字族）
- **关键效果**：动态背景（晴/雨/雪）+ 数据可视化
- **决策规则**：
```json
{
  "if_severe_weather": "add-warning-system",
  "if_allergy_forecast": "add-pollen-data",
  "if_widget": "add-ios-android-widget-preview"
}
```
- **反模式**：静态背景、首屏无当前位置、信息密度过低

## 24. 日记 / 写作

- **推荐落地页模式**：Storytelling-Driven
- **风格优先级**：主 Soft UI Evolution / 备 Minimalism
- **配色氛围**：纸感米白 + 墨水深色
- **字体情绪**：手写 + 内省（Caveat + Quicksand 或 Lora + Raleway）
- **关键效果**：墨水流动 + 翻页动画
- **决策规则**：
```json
{
  "if_ai_journaling": "add-prompt-suggestions",
  "if_private_lock": "add-biometric-preview",
  "if_mood_tracking": "add-color-coded-calendar"
}
```
- **反模式**：花哨色彩、强社交分享、订阅墙

## 25. Web3 / DeFi / 加密

- **推荐落地页模式**：Feature-Rich Showcase
- **风格优先级**：主 Cyberpunk UI / 备 Glassmorphism
- **配色氛围**：紫 #8B5CF6 + 金 #FBBF24 + 深空 #0F0F23
- **字体情绪**：未来 + 精确（Space Grotesk + Inter + JetBrains Mono）
- **关键效果**：wallet connect 动画 + 实时 gas + 链上数据
- **决策规则**：
```json
{
  "must_have": ["wallet-integration", "gas-fees-display", "network-switcher"],
  "if_nft_marketplace": "add-card-grid-hover",
  "if_defi_yield": "add-apy-calculator",
  "if_token_swap": "add-real-time-price"
}
```
- **反模式**：默认浅色、无交易状态、隐藏合约地址

## 26. NFT 平台

- **推荐落地页模式**：Feature-Rich Showcase
- **风格优先级**：主 Cyberpunk UI / 备 Glassmorphism
- **配色氛围**：紫 + 金 + 黑深空
- **字体情绪**：未来 + 收藏（Orbitron + Exo 2）
- **关键效果**：NFT 卡 hover 3D 倾斜 + 稀有度展示
- **决策规则**：
```json
{
  "if_drop_launch": "add-countdown-and-mint-progress",
  "if_secondary_market": "add-floor-price-ticker",
  "if_creator_tools": "add-mint-studio-preview"
}
```
- **反模式**：无 gas 提示、首屏无 featured drop、隐藏 creator

## 27. AI 产品 / 通用 AI 助手

- **推荐落地页模式**：Interactive Product Demo + Minimal
- **风格优先级**：主 AI-Native UI / 备 Minimalism
- **配色氛围**：紫 #7C3AED + 青 #06B6D4 或黑底高饱和
- **字体情绪**：智能 + 现代（Space Grotesk + DM Sans）
- **关键效果**：prompt 输入即生成预览 + streaming text + shimmer
- **决策规则**：
```json
{
  "if_chat_first": "hero-is-prompt-input",
  "if_generation_long": "add-streaming-and-cancel",
  "if_enterprise": "add-sso-and-data-policy"
}
```
- **反模式**：长篇功能列表、无即时 demo、隐藏模型限制

## 28. 聊天机器人 / Chatbot

- **推荐落地页模式**：Interactive Product Demo + Minimal
- **风格优先级**：主 AI-Native UI / 备 Minimalism
- **配色氛围**：紫 + 青对话气泡
- **字体情绪**：亲切 + 智能（Plus Jakarta Sans）
- **关键效果**：demo 对话自动播放 + typing indicator
- **决策规则**：
```json
{
  "if_customer_service": "add-industry-templates",
  "if_lead_gen_bot": "add-conversion-tracking",
  "if_voice_bot": "add-voice-waveform"
}
```
- **反模式**：无 demo、强注册墙、隐藏 bot 限制

## 29. 网络安全 / Security

- **推荐落地页模式**：Trust & Authority + Real-Time
- **风格优先级**：主 Cyberpunk UI / 备 Dark Mode OLED
- **配色氛围**：矩阵绿 + 警告红 + 黑底
- **字体情绪**：技术 + 严肃（IBM Plex Sans + JetBrains Mono）
- **关键效果**：实时威胁地图 + SOC dashboard 预览
- **决策规则**：
```json
{
  "if_soc_platform": "add-live-threat-feed",
  "if_compliance": "add-hipaa-soc2-badges",
  "if_trial": "add-sandbox-link"
}
```
- **反模式**：浅色 + 卡通 + 无可信资质

## 30. 开发者工具 / IDE / API

- **推荐落地页模式**：Minimal + Documentation
- **风格优先级**：主 Dark Mode OLED / 备 Minimalism
- **配色氛围**：纯黑 + 单一强调色（GitHub 绿 / Vercel 黑白）
- **字体情绪**：技术 + 精确（JetBrains Mono + Inter）
- **关键效果**：code block 实时运行 + CLI 录屏 + API explorer
- **决策规则**：
```json
{
  "if_api_product": "add-interactive-docs",
  "if_cli_tool": "add-terminal-recording",
  "if_open_source": "add-github-stars-and-contributors"
}
```
- **反模式**：营销话术堆砌、无代码示例、强销售 CTA

## 行业推理速查矩阵

| 行业 | 落地页 | 主风格 | 配色主导色 | 字体首选 |
|---|---|---|---|---|
| SaaS 通用 | Hero+Features+CTA | Glassmorphism | 信任蓝 | Inter |
| 微 SaaS | Hero-Centric | Motion-Driven | Indigo+Emerald | Space Grotesk |
| 电商 | Feature-Rich Showcase | Vibrant & Block | 成功绿+橙 | Rubik |
| 奢侈品电商 | Feature-Rich+Story | Liquid Glass | 深黑+金 | Cormorant |
| Fintech | Trust+Features | Minimalism | 金+紫+深底 | IBM Plex Sans |
| 银行 | Trust+Features | Minimalism | 海军蓝+金 | Lexend |
| 保险 | Conversion+Trust | Trust & Authority | 安全蓝+绿 | Lexend |
| 医疗诊所 | Trust+Conversion | Accessible & Ethical | 医疗青+绿 | Figtree |
| 牙科 | Social Proof+Conversion | Soft UI Evolution | 医疗青+白 | Figtree |
| 心理健康 | Social Proof | Neumorphism | 薰衣草+绿 | Lora+Raleway |
| 美容水疗 | Hero+Social Proof | Soft UI Evolution | 粉+紫 | Playfair+Inter |
| 餐饮 | Hero+Conversion | Vibrant & Block | 食欲红+金 | Playfair SC+Karla |
| 酒店 | Hero+Social Proof | Liquid Glass | 海军蓝+金 | Cormorant+Montserrat |
| 法律 | Trust+Minimal | Trust & Authority | 海军蓝+金 | EB Garamond+Lato |
| 教育 | Feature+Social Proof | Claymorphism | 进度青+橙 | Poppins+Open Sans |
| 作品集 | Portfolio Grid+Story | Motion-Driven | 单色+蓝 accent | Space Grotesk |
| 创意机构 | Story+Feature-Rich | Brutalism | 撞色+黑边 | Syne+Manrope |
| 游戏 | Feature-Rich Showcase | 3D & Hyperrealism | 紫+玫红+黑 | Russo One |
| 音乐流媒体 | Feature-Rich Showcase | Dark Mode OLED | 深紫+播放绿 | Righteous+Poppins |
| 习惯追踪 | Social Proof+Demo | Claymorphism | 橙+绿 | Fredoka+Nunito |
| 食谱 | Hero+Feature-Rich | Claymorphism | 红橙+暖米 | Playfair SC+Karla |
| 冥想 | Story+Social Proof | Neumorphism | 薰衣草+海雾 | Lora+Raleway |
| 天气 | Hero-Centric | Glassmorphism | 天空蓝+极光 | Inter |
| 日记 | Storytelling | Soft UI Evolution | 纸感米+墨水深 | Caveat+Quicksand |
| Web3/DeFi | Feature-Rich Showcase | Cyberpunk UI | 紫+金+黑 | Space Grotesk+JetBrains Mono |
| NFT | Feature-Rich Showcase | Cyberpunk UI | 紫+金+黑 | Orbitron+Exo 2 |
| AI 通用 | Interactive Demo+Minimal | AI-Native UI | 紫+青 | Space Grotesk+DM Sans |
| Chatbot | Interactive Demo+Minimal | AI-Native UI | 紫+青气泡 | Plus Jakarta Sans |
| 网络安全 | Trust+Real-Time | Cyberpunk UI | 矩阵绿+警告红 | IBM Plex+JetBrains Mono |
| 开发者工具 | Minimal+Documentation | Dark Mode OLED | 纯黑+单一强调 | JetBrains Mono+Inter |

## 通用反模式清单

1. **金融行业用 Aurora UI / 大渐变** → 监管视角 = 不可信
2. **医疗行业用 Neumorphism** → 对比度不达标被打回
3. **儿童产品用 Brutalism** → 硬边硬色不利于情感建立
4. **B2B 落地页堆 3D 动画** → LCP > 2.5s 决策者跳出
5. **AI 产品完全照搬 ChatGPT 紫** → 同质化无记忆点
6. **Web3 项目默认浅色模式** → 用户期望沉浸深色
7. **餐饮首屏放 PDF 菜单** → 移动端跳出率 70%+
8. **酒店低分辨率房间图** → 直接影响预订决策
9. **法律机构用卡通 icon** → 损害专业形象
10. **教育产品无试听** → 转化率降 40%+
