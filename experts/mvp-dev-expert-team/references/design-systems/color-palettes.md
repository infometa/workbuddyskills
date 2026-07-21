---
id: color-palettes
title: 商业级配色库（精选 30 套 × 17 语义色）
domain: design-systems
quality_score: 95
last_updated: 2026-07-19
---

# 商业级配色库（精选 30 套 × 17 语义色）

从大量配色资产中精选 30 套在商业项目命中率最高的配色方案。每套均给出 17 个语义色完整定义（可直接对接 shadcn/ui、Radix、Material 3 等设计系统）、适用行业、设计意图、以及可直接粘贴的 Tailwind config 片段。

## 通用规范

- 所有配色均按 WCAG AA+ 校验（正文 ≥ 4.5:1，大字 ≥ 3:1）
- Primary / Accent 区分：Primary 是品牌色，Accent 是 CTA 行动色
- 深色模式配色采用"反相 + 调暗"策略，避免直接反色
- Tailwind 用法：将下列颜色赋给 `theme.colors`，按语义命名

## 1. SaaS 通用信任蓝

- **适用行业**：SaaS、B2B 工具、企业应用
- **设计意图**：蓝色建立信任，橙色 CTA 形成强对比拉动点击

| 语义色 | Hex |
|---|---|
| Primary | #2563EB |
| On Primary | #FFFFFF |
| Secondary | #3B82F6 |
| On Secondary | #FFFFFF |
| Accent | #EA580C |
| On Accent | #FFFFFF |
| Background | #F8FAFC |
| Foreground | #1E293B |
| Card | #FFFFFF |
| Card Foreground | #1E293B |
| Muted | #E9EFF8 |
| Muted Foreground | #64748B |
| Border | #E2E8F0 |
| Destructive | #DC2626 |
| On Destructive | #FFFFFF |
| Ring | #2563EB |

```json
// tailwind.config.js
"colors": {
  "primary": { DEFAULT: "#2563EB", foreground: "#FFFFFF" },
  "secondary": { DEFAULT: "#3B82F6", foreground: "#FFFFFF" },
  "accent": { DEFAULT: "#EA580C", foreground: "#FFFFFF" },
  "background": "#F8FAFC",
  "foreground": "#1E293B",
  "card": { DEFAULT: "#FFFFFF", foreground: "#1E293B" },
  "muted": { DEFAULT: "#E9EFF8", foreground: "#64748B" },
  "border": "#E2E8F0",
  "destructive": { DEFAULT: "#DC2626", foreground: "#FFFFFF" },
  "ring": "#2563EB"
}
```

## 2. 微 SaaS 靛紫

- **适用行业**：独立开发者产品、AI 工具、SaaS 移动端
- **设计意图**：Indigo 比蓝色更现代，Emerald CTA 在金融场景更具信任感

| Primary | On Primary | Secondary | On Secondary | Accent | On Accent | Background | Foreground |
|---|---|---|---|---|---|---|---|
| #6366F1 | #FFFFFF | #818CF8 | #0F172A | #059669 | #FFFFFF | #F5F3FF | #1E1B4B |

| Card | Card FG | Muted | Muted FG | Border | Destructive | On Destructive | Ring |
|---|---|---|---|---|---|---|---|
| #FFFFFF | #1E1B4B | #EBEFF9 | #64748B | #E0E7FF | #DC2626 | #FFFFFF | #6366F1 |

```json
"colors": { "primary": "#6366F1", "accent": "#059669", "background": "#F5F3FF", "foreground": "#1E1B4B", "ring": "#6366F1" }
```

## 3. 电商成功绿

- **适用行业**：电商、订阅、零售
- **设计意图**：绿色暗示"成功购买"，橙色制造紧迫感（限时/库存）

| Primary | #059669 | Background | #ECFDF5 | Muted | #E8F1F3 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #064E3B | Muted FG | #64748B |
| Secondary | #10B981 | Card | #FFFFFF | Border | #A7F3D0 |
| On Secondary | #0F172A | Card FG | #064E3B | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #059669 |
| On Accent | #FFFFFF | | | | |

## 4. 奢侈品黑金

- **适用行业**：奢侈品电商、高端品牌、酒店、婚礼
- **设计意图**：黑 + 金是奢侈品默认语言，金色 CTA 比橙色更优雅

| Primary | #1C1917 | Background | #FAFAF9 | Muted | #E8ECF0 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #0C0A09 | Muted FG | #64748B |
| Secondary | #44403C | Card | #FFFFFF | Border | #D6D3D1 |
| On Secondary | #FFFFFF | Card FG | #0C0A09 | Destructive | #DC2626 |
| Accent | #A16207 | On Destructive | #FFFFFF | Ring | #1C1917 |
| On Accent | #FFFFFF | | | | |

## 5. B2B 服务深海军

- **适用行业**：B2B 服务、企业咨询、法律
- **设计意图**：深海军蓝 + 蓝 CTA = 极致专业感

| Primary | #0F172A | Background | #F8FAFC | Muted | #E8ECF1 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #020617 | Muted FG | #64748B |
| Secondary | #334155 | Card | #FFFFFF | Border | #E2E8F0 |
| On Secondary | #FFFFFF | Card FG | #020617 | Destructive | #DC2626 |
| Accent | #0369A1 | On Destructive | #FFFFFF | Ring | #0F172A |
| On Accent | #FFFFFF | | | | |

## 6. 金融 Dashboard 深色

- **适用行业**：金融行情、交易终端、加密货币
- **设计意图**：深色背景突出数据，绿色为正向指标（盈），红色为负向（亏）

| Primary | #0F172A | Background | #020617 | Muted | #1A1E2F |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #1E293B | Card | #0E1223 | Border | #334155 |
| On Secondary | #FFFFFF | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #22C55E | On Destructive | #FFFFFF | Ring | #0F172A |
| On Accent | #0F172A | | | | |

## 7. 医疗青绿

- **适用行业**：医疗 App、诊所、健康追踪
- **设计意图**：青色比纯蓝更柔和，绿色暗示健康

| Primary | #0891B2 | Background | #ECFEFF | Muted | #E8F1F6 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #164E63 | Muted FG | #64748B |
| Secondary | #22D3EE | Card | #FFFFFF | Border | #A5F3FC |
| On Secondary | #0F172A | Card FG | #164E63 | Destructive | #DC2626 |
| Accent | #059669 | On Destructive | #FFFFFF | Ring | #0891B2 |
| On Accent | #FFFFFF | | | | |

## 8. 教育靛橙

- **适用行业**：在线课程、K12、编程训练营
- **设计意图**：靛色活泼但不失专业，橙色刺激学习行动

| Primary | #4F46E5 | Background | #EEF2FF | Muted | #EBEEF8 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #1E1B4B | Muted FG | #64748B |
| Secondary | #818CF8 | Card | #FFFFFF | Border | #C7D2FE |
| On Secondary | #0F172A | Card FG | #1E1B4B | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #4F46E5 |
| On Accent | #FFFFFF | | | | |

## 9. 创意机构撞色

- **适用行业**：创意机构、设计工作室、广告公司
- **设计意图**：粉 + 青撞色表达创意胆识

| Primary | #EC4899 | Background | #FDF2F8 | Muted | #F1EEF5 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #831843 | Muted FG | #64748B |
| Secondary | #F472B6 | Card | #FFFFFF | Border | #FBCFE8 |
| On Secondary | #0F172A | Card FG | #831843 | Destructive | #DC2626 |
| Accent | #0891B2 | On Destructive | #FFFFFF | Ring | #EC4899 |
| On Accent | #FFFFFF | | | | |

## 10. 个人作品集单色

- **适用行业**：个人作品集、设计师、摄影师
- **设计意图**：单色背景让作品自己说话

| Primary | #18181B | Background | #FAFAFA | Muted | #E8ECF0 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #09090B | Muted FG | #64748B |
| Secondary | #3F3F46 | Card | #FFFFFF | Border | #E4E4E7 |
| On Secondary | #FFFFFF | Card FG | #09090B | Destructive | #DC2626 |
| Accent | #2563EB | On Destructive | #FFFFFF | Ring | #18181B |
| On Accent | #FFFFFF | | | | |

## 11. 游戏霓虹紫

- **适用行业**：游戏、电竞、虚拟世界
- **设计意图**：紫 + 玫红 + 深空 = 沉浸式游戏语言

| Primary | #7C3AED | Background | #0F0F23 | Muted | #27273B |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #E2E8F0 | Muted FG | #94A3B8 |
| Secondary | #A78BFA | Card | #1E1C35 | Border | #4C1D95 |
| On Secondary | #0F172A | Card FG | #E2E8F0 | Destructive | #EF4444 |
| Accent | #F43F5E | On Destructive | #FFFFFF | Ring | #7C3AED |
| On Accent | #FFFFFF | | | | |

## 12. Fintech 金紫

- **适用行业**：加密货币、DeFi、投资 App
- **设计意图**：金 = 价值信任，紫 = 技术未来感

| Primary | #F59E0B | Background | #0F172A | Muted | #272F42 |
|---|---|---|---|---|---|
| On Primary | #0F172A | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #FBBF24 | Card | #222735 | Border | #334155 |
| On Secondary | #0F172A | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #8B5CF6 | On Destructive | #FFFFFF | Ring | #F59E0B |
| On Accent | #FFFFFF | | | | |

## 13. 社交媒体玫红

- **适用行业**：社交、社区、婚恋
- **设计意图**：玫红表达情感连接，蓝色辅助交互

| Primary | #E11D48 | Background | #FFF1F2 | Muted | #F0ECF2 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #881337 | Muted FG | #64748B |
| Secondary | #FB7185 | Card | #FFFFFF | Border | #FECDD3 |
| On Secondary | #0F172A | Card FG | #881337 | Destructive | #DC2626 |
| Accent | #2563EB | On Destructive | #FFFFFF | Ring | #E11D48 |
| On Accent | #FFFFFF | | | | |

## 14. 生产力青绿

- **适用行业**：生产力工具、笔记、任务管理
- **设计意图**：Teal 让人专注，橙 CTA 推动行动

| Primary | #0D9488 | Background | #F0FDFA | Muted | #E8F1F4 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #134E4A | Muted FG | #64748B |
| Secondary | #14B8A6 | Card | #FFFFFF | Border | #99F6E4 |
| On Secondary | #0F172A | Card FG | #134E4A | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #0D9488 |
| On Accent | #FFFFFF | | | | |

## 15. AI 紫青

- **适用行业**：AI 助手、Chatbot、生成式工具
- **设计意图**：紫表达智能，青表达对话流动

| Primary | #7C3AED | Background | #FAF5FF | Muted | #ECEEF9 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #1E1B4B | Muted FG | #64748B |
| Secondary | #A78BFA | Card | #FFFFFF | Border | #DDD6FE |
| On Secondary | #0F172A | Card FG | #1E1B4B | Destructive | #DC2626 |
| Accent | #0891B2 | On Destructive | #FFFFFF | Ring | #7C3AED |
| On Accent | #FFFFFF | | | | |

## 16. NFT/Web3 深空金紫

- **适用行业**：NFT 市场、Web3 平台、加密艺术
- **设计意图**：深空黑 + 紫 + 金 = 数字收藏品高级感

| Primary | #8B5CF6 | Background | #0F0F23 | Muted | #27273B |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #A78BFA | Card | #1E1D35 | Border | #4C1D95 |
| On Secondary | #0F172A | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #FBBF24 | On Destructive | #FFFFFF | Ring | #8B5CF6 |
| On Accent | #0F172A | | | | |

## 17. 心理健康薰衣草

- **适用行业**：冥想、心理健康、自助
- **设计意图**：薰衣草降低焦虑，绿色暗示成长

| Primary | #8B5CF6 | Background | #FAF5FF | Muted | #EDEFF9 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #4C1D95 | Muted FG | #64748B |
| Secondary | #C4B5FD | Card | #FFFFFF | Border | #EDE9FE |
| On Secondary | #0F172A | Card FG | #4C1D95 | Destructive | #DC2626 |
| Accent | #059669 | On Destructive | #FFFFFF | Ring | #8B5CF6 |
| On Accent | #FFFFFF | | | | |

## 18. 智能家居/IoT 深色科技

- **适用行业**：智能家居、IoT、能源管理
- **设计意图**：深色 = 科技感，绿色 = 设备在线状态

| Primary | #1E293B | Background | #020617 | Muted | #272F42 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #334155 | Card | #1B2336 | Border | #475569 |
| On Secondary | #FFFFFF | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #22C55E | On Destructive | #FFFFFF | Ring | #1E293B |
| On Accent | #0F172A | | | | |

## 19. EV/充电生态青

- **适用行业**：电动车、充电、可持续能源
- **设计意图**：青 = 电力，绿 = 环保

| Primary | #0891B2 | Background | #ECFEFF | Muted | #E8F1F6 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #164E63 | Muted FG | #64748B |
| Secondary | #22D3EE | Card | #FFFFFF | Border | #A5F3FC |
| On Secondary | #0F172A | Card FG | #164E63 | Destructive | #DC2626 |
| Accent | #16A34A | On Destructive | #FFFFFF | Ring | #0891B2 |
| On Accent | #FFFFFF | | | | |

## 20. 订阅盒紫橙

- **适用行业**：订阅盒、潮玩、惊喜购物
- **设计意图**：紫表达惊喜，橙催促下单

| Primary | #D946EF | Background | #FDF4FF | Muted | #F0EEF9 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #86198F | Muted FG | #64748B |
| Secondary | #E879F9 | Card | #FFFFFF | Border | #F5D0FE |
| On Secondary | #0F172A | Card FG | #86198F | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #D946EF |
| On Accent | #FFFFFF | | | | |

## 21. 播客深紫暖橙

- **适用行业**：播客、音频平台
- **设计意图**：深紫 = 音频沉浸，橙 = 收听行动

| Primary | #1E1B4B | Background | #0F0F23 | Muted | #27273B |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #312E81 | Card | #1B1B30 | Border | #4338CA |
| On Secondary | #FFFFFF | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #F97316 | On Destructive | #FFFFFF | Ring | #1E1B4B |
| On Accent | #0F172A | | | | |

## 22. 知识库/文档中性

- **适用行业**：文档站、知识库、技术文档
- **设计意图**：中性灰让内容为主，蓝链接不抢戏

| Primary | #475569 | Background | #F8FAFC | Muted | #EAEFF3 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #1E293B | Muted FG | #64748B |
| Secondary | #64748B | Card | #FFFFFF | Border | #E2E8F0 |
| On Secondary | #FFFFFF | Card FG | #1E293B | Destructive | #DC2626 |
| Accent | #2563EB | On Destructive | #FFFFFF | Ring | #475569 |
| On Accent | #FFFFFF | | | | |

## 23. 美容/SPA 柔粉薰衣草

- **适用行业**：美容、SPA、Wellness
- **设计意图**：粉表达女性气质，紫暗示奢华

| Primary | #EC4899 | Background | #FDF2F8 | Muted | #F1EEF5 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #831843 | Muted FG | #64748B |
| Secondary | #F9A8D4 | Card | #FFFFFF | Border | #FBCFE8 |
| On Secondary | #0F172A | Card FG | #831843 | Destructive | #DC2626 |
| Accent | #8B5CF6 | On Destructive | #FFFFFF | Ring | #EC4899 |
| On Accent | #FFFFFF | | | | |

## 24. 餐厅食欲红金

- **适用行业**：餐厅、外卖、食谱
- **设计意图**：红激发食欲，金暗示品质

| Primary | #DC2626 | Background | #FEF2F2 | Muted | #F0EDF1 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #450A0A | Muted FG | #64748B |
| Secondary | #F87171 | Card | #FFFFFF | Border | #FECACA |
| On Secondary | #0F172A | Card FG | #450A0A | Destructive | #DC2626 |
| Accent | #A16207 | On Destructive | #FFFFFF | Ring | #DC2626 |
| On Accent | #FFFFFF | | | | |

## 25. 健身能量橙深

- **适用行业**：健身、运动、训练
- **设计意图**：橙 = 能量，绿 = 完成度

| Primary | #F97316 | Background | #1F2937 | Muted | #37414F |
|---|---|---|---|---|---|
| On Primary | #0F172A | Foreground | #F8FAFC | Muted FG | #94A3B8 |
| Secondary | #FB923C | Card | #313742 | Border | #374151 |
| On Secondary | #0F172A | Card FG | #F8FAFC | Destructive | #EF4444 |
| Accent | #22C55E | On Destructive | #FFFFFF | Ring | #F97316 |
| On Accent | #0F172A | | | | |

## 26. 房地产青蓝

- **适用行业**：房地产、物业、室内设计
- **设计意图**：青蓝 = 信任专业，蓝 CTA = 联系

| Primary | #0F766E | Background | #F0FDFA | Muted | #E8F0F3 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #134E4A | Muted FG | #64748B |
| Secondary | #14B8A6 | Card | #FFFFFF | Border | #99F6E4 |
| On Secondary | #0F172A | Card FG | #134E4A | Destructive | #DC2626 |
| Accent | #0369A1 | On Destructive | #FFFFFF | Ring | #0F766E |
| On Accent | #FFFFFF | | | | |

## 27. 旅游天空蓝橙

- **适用行业**：旅游、出行、机票
- **设计意图**：天空蓝 = 旅途，橙 = 立即行动

| Primary | #0EA5E9 | Background | #F0F9FF | Muted | #E8F2F8 |
|---|---|---|---|---|---|
| On Primary | #0F172A | Foreground | #0C4A6E | Muted FG | #64748B |
| Secondary | #38BDF8 | Card | #FFFFFF | Border | #BAE6FD |
| On Secondary | #0F172A | Card FG | #0C4A6E | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #0EA5E9 |
| On Accent | #FFFFFF | | | | |

## 28. 法律权威蓝金

- **适用行业**：法律、会计、咨询
- **设计意图**：深蓝 + 金 = 律所传统色彩

| Primary | #1E3A8A | Background | #F8FAFC | Muted | #E9EEF5 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #0F172A | Muted FG | #64748B |
| Secondary | #1E40AF | Card | #FFFFFF | Border | #CBD5E1 |
| On Secondary | #FFFFFF | Card FG | #0F172A | Destructive | #DC2626 |
| Accent | #B45309 | On Destructive | #FFFFFF | Ring | #1E3A8A |
| On Accent | #FFFFFF | | | | |

## 29. 保险安全蓝绿

- **适用行业**：保险、保障类
- **设计意图**：蓝 = 安全保障，绿 = 续保成功

| Primary | #0369A1 | Background | #F0F9FF | Muted | #E7EFF5 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #0C4A6E | Muted FG | #64748B |
| Secondary | #0EA5E9 | Card | #FFFFFF | Border | #BAE6FD |
| On Secondary | #0F172A | Card FG | #0C4A6E | Destructive | #DC2626 |
| Accent | #16A34A | On Destructive | #FFFFFF | Ring | #0369A1 |
| On Accent | #FFFFFF | | | | |

## 30. 物流追踪蓝橙

- **适用行业**：物流、快递、配送
- **设计意图**：蓝 = 追踪可视化，橙 = 配送行动

| Primary | #2563EB | Background | #EFF6FF | Muted | #E9EFF8 |
|---|---|---|---|---|---|
| On Primary | #FFFFFF | Foreground | #1E40AF | Muted FG | #64748B |
| Secondary | #3B82F6 | Card | #FFFFFF | Border | #BFDBFE |
| On Secondary | #FFFFFF | Card FG | #1E40AF | Destructive | #DC2626 |
| Accent | #EA580C | On Destructive | #FFFFFF | Ring | #2563EB |
| On Accent | #FFFFFF | | | | |

## 通用 Tailwind 完整模板

下面给出可直接粘贴到 `tailwind.config.js` 的完整模板（以 SaaS 通用信任蓝为例），其余 29 套按相同结构替换 hex 即可：

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
};
```

CSS 变量层（以 SaaS 通用信任蓝为例，使用 HSL 表达便于深浅色切换）：

```css
:root {
  --background: 210 40% 98%;       /* #F8FAFC */
  --foreground: 215 28% 17%;       /* #1E293B */
  --card: 0 0% 100%;
  --card-foreground: 215 28% 17%;
  --primary: 221 83% 53%;          /* #2563EB */
  --primary-foreground: 0 0% 100%;
  --secondary: 217 91% 60%;        /* #3B82F6 */
  --secondary-foreground: 0 0% 100%;
  --accent: 24 95% 53%;            /* #EA580C */
  --accent-foreground: 0 0% 100%;
  --muted: 214 32% 91%;            /* #E9EFF8 */
  --muted-foreground: 215 16% 47%; /* #64748B */
  --border: 214 32% 91%;           /* #E2E8F0 */
  --destructive: 0 72% 51%;        /* #DC2626 */
  --destructive-foreground: 0 0% 100%;
  --ring: 221 83% 53%;
  --radius: 0.5rem;
}

.dark {
  --background: 222 47% 11%;       /* #0F172A */
  --foreground: 210 40% 98%;
  --card: 222 47% 14%;
  --card-foreground: 210 40% 98%;
  --primary: 217 91% 60%;
  --primary-foreground: 222 47% 11%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --border: 217 33% 20%;
}
```

## 配色选择决策树（行业 → 情绪 → 转化目标）

### 步骤 1：按行业大类锁定主色

```
金融/银行/保险/法律 → 主色锁定深海军蓝 #0F172A 或 #1E3A8A
医疗/健康/心理 → 主色锁定医疗青 #0891B2 或薰衣草 #8B5CF6
电商/零售/订阅 → 主色锁定成功绿 #059669 或品牌色
奢侈品/酒店/婚礼 → 主色锁定深黑 #1C1917 + 金 #A16207
游戏/音乐/Web3 → 主色锁定深空 #0F0F23 + 紫 #7C3AED
AI/SaaS/生产力 → 主色锁定蓝 #2563EB 或紫 #6366F1
餐饮/外卖 → 主色锁定食欲红 #DC2626
```

### 步骤 2：按情绪选 Accent

```
情绪 = 信任 → Accent 用金 #A16207 或海军蓝
情绪 = 行动 → Accent 用橙 #EA580C（最高 CTA 转化）
情绪 = 成功 → Accent 用绿 #059669 / #22C55E
情绪 = 紧迫 → Accent 用红 #DC2626（限促销）
情绪 = 高级 → Accent 用金 #A16207 + 留白
情绪 = 智能 → Accent 用青 #06B6D4
情绪 = 惊喜 → Accent 用洋红 #D946EF
```

### 步骤 3：按转化目标调整 Background

```
转化 = 注册/Lead → 浅色 Background（#F8FAFC / #FAFAF5）降低抗拒
转化 = 试用/Demo → 浅色 + 卡片白底突出产品截图
转化 = 订阅/付费 → 深色 Background（#0F172A）+ 金 Accent 提升高级感
转化 = 品牌曝光 → 极光/Aurora 渐变背景
转化 = 留存 → 深色 + 强 accent（金融/游戏场景）
转化 = 信任 → 中性灰背景 + 蓝 Primary + 金 Accent
```

## 反模式与避坑

1. **同一界面使用 3+ 高饱和色**：视觉疲劳、CTA 失焦
2. **金融用大渐变背景**：监管视角 = 不可信
3. **医疗用红 Destructive 作主色**：用户联想到"危险"
4. **奢侈品用荧光橙**：破坏高级感
5. **儿童产品用深色**：影响情感建立
6. **深色模式直接反色**：对比度坍塌，需手动调整
7. **CTA 与 Primary 同色**：用户找不到行动入口
8. **Muted Foreground 对比 < 4.5:1**：WCAG AA 不达标
9. **Border 用纯黑**：显得廉价，应用 #E2E8F0 类中性色
10. **忽视 Ring 色**：键盘导航用户失去焦点指示
