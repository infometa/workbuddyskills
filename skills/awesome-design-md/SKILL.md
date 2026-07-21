---
name: awesome-design-md
description: "Curated collection of 54 DESIGN.md files extracted from real developer-focused websites (Vercel, Stripe, Linear, Notion, Figma, etc.). Use when a user wants to build UI that matches a specific brand's design system, needs a DESIGN.md template, asks for design tokens/color palettes/typography of known products, or says 'make it look like [brand]'. Load the matching reference file and use it as the design spec."
description_zh: "54 个知名网站设计系统模板，一键复用品牌级 UI 风格"
description_en: "54 ready-to-use DESIGN.md files from top websites for instant brand-quality UI"
version: 1.0.0
homepage: https://github.com/VoltAgent/awesome-design-md
allowed-tools: Read,Write,Bash
---

# Awesome DESIGN.md

A curated collection of **54 DESIGN.md files** extracted from real, developer-focused websites. Each file is a complete design system specification that AI agents can read to generate pixel-perfect, brand-consistent UI.

## What is DESIGN.md?

[DESIGN.md](https://stitch.withgoogle.com/docs/design-md/overview/) is a concept introduced by Google Stitch — a plain-text design system document that AI agents read to generate consistent UI. It's just a markdown file. Drop it into your project root and any AI coding agent instantly understands how your UI should look.

## How to Use

1. **User says "make it look like [brand]"** → Find the matching reference file below
2. **Read the reference file** from `references/{site-name}.md`
3. **Copy the DESIGN.md content** into the user's project root as `DESIGN.md`
4. **Use the design tokens** (colors, typography, spacing, components) when generating UI code

## Available Design Systems

### AI & Machine Learning

| Site | Reference | Style |
|------|-----------|-------|
| Claude | `references/claude.md` | Warm terracotta accent, clean editorial layout |
| Cohere | `references/cohere.md` | Vibrant gradients, data-rich dashboard aesthetic |
| ElevenLabs | `references/elevenlabs.md` | Dark cinematic UI, audio-waveform aesthetics |
| Minimax | `references/minimax.md` | Bold dark interface with neon accents |
| Mistral AI | `references/mistral.ai.md` | French-engineered minimalism, purple-toned |
| Ollama | `references/ollama.md` | Terminal-first, monochrome simplicity |
| OpenCode AI | `references/opencode.ai.md` | Developer-centric dark theme |
| Replicate | `references/replicate.md` | Clean white canvas, code-forward |
| RunwayML | `references/runwayml.md` | Cinematic dark UI, media-rich layout |
| Together AI | `references/together.ai.md` | Technical, blueprint-style design |
| VoltAgent | `references/voltagent.md` | Void-black canvas, emerald accent, terminal-native |
| xAI | `references/x.ai.md` | Stark monochrome, futuristic minimalism |

### Developer Tools & Platforms

| Site | Reference | Style |
|------|-----------|-------|
| Cursor | `references/cursor.md` | Sleek dark interface, gradient accents |
| Expo | `references/expo.md` | Dark theme, tight letter-spacing, code-centric |
| Linear | `references/linear.app.md` | Ultra-minimal, precise, purple accent |
| Lovable | `references/lovable.md` | Playful gradients, friendly dev aesthetic |
| Mintlify | `references/mintlify.md` | Clean, green-accented, reading-optimized |
| PostHog | `references/posthog.md` | Playful hedgehog branding, developer-friendly dark UI |
| Raycast | `references/raycast.md` | Sleek dark chrome, vibrant gradient accents |
| Resend | `references/resend.md` | Minimal dark theme, monospace accents |
| Sentry | `references/sentry.md` | Dark dashboard, data-dense, pink-purple accent |
| Supabase | `references/supabase.md` | Dark emerald theme, code-first |
| Superhuman | `references/superhuman.md` | Premium dark UI, keyboard-first, purple glow |
| Vercel | `references/vercel.md` | Black and white precision, Geist font |
| Warp | `references/warp.md` | Dark IDE-like interface, block-based command UI |
| Zapier | `references/zapier.md` | Warm orange, friendly illustration-driven |

### Infrastructure & Cloud

| Site | Reference | Style |
|------|-----------|-------|
| ClickHouse | `references/clickhouse.md` | Yellow-accented, technical documentation style |
| Composio | `references/composio.md` | Modern dark with colorful integration icons |
| HashiCorp | `references/hashicorp.md` | Enterprise-clean, black and white |
| MongoDB | `references/mongodb.md` | Green leaf branding, developer documentation focus |
| Sanity | `references/sanity.md` | Red accent, content-first editorial layout |
| Stripe | `references/stripe.md` | Signature purple gradients, weight-300 elegance |

### Design & Productivity

| Site | Reference | Style |
|------|-----------|-------|
| Airtable | `references/airtable.md` | Colorful, friendly, structured data aesthetic |
| Cal.com | `references/cal.md` | Clean neutral UI, developer-oriented simplicity |
| Clay | `references/clay.md` | Organic shapes, soft gradients, art-directed layout |
| Figma | `references/figma.md` | Vibrant multi-color, playful yet professional |
| Framer | `references/framer.md` | Bold black and blue, motion-first, design-forward |
| Intercom | `references/intercom.md` | Friendly blue palette, conversational UI patterns |
| Miro | `references/miro.md` | Bright yellow accent, infinite canvas aesthetic |
| Notion | `references/notion.md` | Warm minimalism, serif headings, soft surfaces |
| Pinterest | `references/pinterest.md` | Red accent, masonry grid, image-first |
| Webflow | `references/webflow.md` | Blue-accented, polished marketing site aesthetic |

### Fintech & Crypto

| Site | Reference | Style |
|------|-----------|-------|
| Coinbase | `references/coinbase.md` | Clean blue identity, trust-focused, institutional feel |
| Kraken | `references/kraken.md` | Purple-accented dark UI, data-dense dashboards |
| Revolut | `references/revolut.md` | Sleek dark interface, gradient cards, fintech precision |
| Wise | `references/wise.md` | Bright green accent, friendly and clear |

### Enterprise & Consumer

| Site | Reference | Style |
|------|-----------|-------|
| Airbnb | `references/airbnb.md` | Warm coral accent, photography-driven, rounded UI |
| Apple | `references/apple.md` | Premium white space, SF Pro, cinematic imagery |
| BMW | `references/bmw.md` | Dark premium surfaces, precise German engineering aesthetic |
| IBM | `references/ibm.md` | Carbon design system, structured blue palette |
| NVIDIA | `references/nvidia.md` | Green-black energy, technical power aesthetic |
| SpaceX | `references/spacex.md` | Stark black and white, full-bleed imagery, futuristic |
| Spotify | `references/spotify.md` | Vibrant green on dark, bold type, album-art-driven |
| Uber | `references/uber.md` | Bold black and white, tight type, urban energy |

## What Each DESIGN.md Contains

Every file follows the [Google Stitch DESIGN.md format](https://stitch.withgoogle.com/docs/design-md/format/) with 9 sections:

1. **Visual Theme & Atmosphere** — Mood, density, design philosophy
2. **Color Palette & Roles** — Semantic name + hex + functional role
3. **Typography Rules** — Font families, full hierarchy table
4. **Component Stylings** — Buttons, cards, inputs, navigation with states
5. **Layout Principles** — Spacing scale, grid, whitespace philosophy
6. **Depth & Elevation** — Shadow system, surface hierarchy
7. **Do's and Don'ts** — Design guardrails and anti-patterns
8. **Responsive Behavior** — Breakpoints, touch targets, collapsing strategy
9. **Agent Prompt Guide** — Quick color reference, ready-to-use prompts

## Workflow

### 1. User specifies a brand → Direct match

```
User: "Build me a landing page that looks like Stripe"
→ Read references/stripe.md
→ Copy content to user's project as DESIGN.md
→ Use the design tokens to generate UI code
```

### 2. User wants to browse → Filter and suggest

```
User: "Show me dark-themed design systems"
→ Suggest: Vercel, Cursor, ElevenLabs, Resend, Warp, Supabase, etc.
→ Let user pick, then load that reference
```

### 3. User doesn't specify a style → Smart recommendation

When the user asks to build a UI **without mentioning any brand or style preference** (e.g., "帮我做一个落地页", "写一个 dashboard", "做一个 SaaS 官网"), **proactively recommend** 3–5 design systems based on the project type:

| Project Type | Recommended Styles | Why |
|---|---|---|
| **SaaS 官网 / Landing page** | Stripe, Vercel, Linear | 经典高转化 SaaS 风格，简洁专业 |
| **开发者工具 / 技术产品** | Vercel, Cursor, Raycast, Supabase | 暗色系、代码友好、极客气质 |
| **AI 产品 / Chat UI** | Claude, Mistral AI, ElevenLabs | AI 原生设计语言，温暖或未来感 |
| **Fintech / 金融产品** | Stripe, Revolut, Coinbase | 信任感、精密感、数据密集 |
| **效率工具 / 生产力产品** | Notion, Linear, Superhuman | 极简、信息密度高、键盘优先 |
| **电商 / 消费品牌** | Airbnb, Apple, Spotify | 视觉驱动、大图、情感化设计 |
| **内部后台 / Dashboard** | Sentry, PostHog, ClickHouse | 数据密集型、暗色仪表盘 |
| **创意 / 设计工具** | Figma, Framer, Clay | 大胆配色、动感十足 |
| **企业级 / B2B** | IBM, HashiCorp, MongoDB | 稳重、结构化、Design System 成熟 |

**Recommendation workflow:**

```
User: "帮我做一个 AI 聊天产品的界面"
→ Agent: "推荐以下设计风格供你选择：
   1. 🟠 Claude — 温暖柔和的赤陶色调，编辑式布局，适合对话产品
   2. 🟣 Mistral AI — 法式工程极简，紫色调，优雅专业
   3. 🎬 ElevenLabs — 暗色电影感，波形美学，适合音频/多模态
   4. ⬛ Vercel — 黑白精准，极致简约
   5. 🟢 VoltAgent — 终端风格，翠绿高亮，适合技术型 AI
   选一个编号，我直接用对应的设计系统帮你生成。"
→ User picks one → Load reference → Generate UI
```

**If the user says "随便" or "你决定":**
- Default to **Vercel** (safest all-rounder: clean, modern, professional)
- Mention the choice and offer to switch: "我先用 Vercel 风格（简约黑白），不喜欢随时换。"
