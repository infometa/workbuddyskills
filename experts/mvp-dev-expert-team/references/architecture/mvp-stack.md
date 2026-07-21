# MVP 技术选型矩阵

## 前端框架对比

| 框架 | 适用场景 | MVP 速度 | 生态成熟度 | 跨端能力 |
|------|----------|----------|-----------|----------|
| Next.js 14+ | SaaS/B2B/内容站 | ★★★★★ | ★★★★★ | Web |
| React 18+ SPA | 管理后台/工具 | ★★★★ | ★★★★★ | Web |
| Vue 3 + Nuxt 3 | 快速原型/内容站 | ★★★★★ | ★★★★ | Web |
| Taro 3 | 小程序/多端 | ★★★★ | ★★★★ | 微信/支付宝/H5/RN |
| uni-app | 简单小程序 | ★★★★★ | ★★★ | 多端 |
| Flutter | 移动端优先 | ★★★ | ★★★★ | iOS/Android/Web |
| HarmonyOS NEXT | 鸿蒙端 | ★★★ | ★★★ | 鸿蒙 |

## 后端框架对比

| 框架 | 语言 | MVP 速度 | 性能 | 适用场景 |
|------|------|----------|------|----------|
| FastAPI | Python | ★★★★★ | ★★★★ | AI 应用/API 服务 |
| Express | Node.js | ★★★★★ | ★★★ | 全栈 JS/简单 CRUD |
| Nest.js | Node.js | ★★★★ | ★★★★ | 企业级/微服务 |
| Gin | Go | ★★★★ | ★★★★★ | 高并发/API 网关 |
| Spring Boot | Java | ★★★ | ★★★★★ | 企业级/金融 |
| CloudBase | 腾讯云 | ★★★★★ | ★★★ | 小程序/快速上线 |

## 数据库选型

| 数据库 | 适用场景 | MVP 推荐 | 规模上限 |
|--------|----------|----------|----------|
| PostgreSQL | 通用/JSON/全文搜索 | ★★★★★ | 亿级 |
| MySQL | 关系型/事务 | ★★★★ | 亿级 |
| MongoDB | 文档/灵活Schema | ★★★★ | 亿级 |
| SQLite | 嵌入式/桌面端 | ★★★ | 百万级 |
| Redis | 缓存/会话/队列 | ★★★★★ | 内存限制 |
| Supabase | BaaS/快速开发 | ★★★★★ | 中小规模 |

## 部署方案

| 方案 | 成本 | MVP 推荐 | 适用场景 |
|------|------|----------|----------|
| Vercel | 免费→$20/月 | ★★★★★ | Next.js 前端 |
| CloudBase | 免费→按量 | ★★★★★ | 小程序+后端 |
| Docker + 云服务器 | ¥50-200/月 | ★★★★ | 通用 |
| 腾讯云 Serverless | 按量付费 | ★★★★ | API 服务 |
| Railway | $5/月起 | ★★★★ | 全栈快速部署 |

## AI 能力接入

| 方案 | 成本 | 延迟 | 适用场景 |
|------|------|------|----------|
| 腾讯混元 API | ¥0.01/千token | 1-3s | 通用对话/文本 |
| DeepSeek API | ¥0.001/千token | 2-5s | 代码/推理 |
| OpenAI API | $0.01/千token | 1-3s | 通用/多模态 |
| 本地 Ollama | 免费 | 视硬件 | 隐私/离线 |

## 典型 MVP 技术栈推荐

### SaaS 看板/协作工具
Next.js 14 + Tailwind + Radix UI + FastAPI + PostgreSQL + Vercel

### 电商小程序
Taro 3 + Vue 3 + CloudBase + MySQL + 微信支付

### 内容平台
Nuxt 3 + Tailwind + FastAPI + PostgreSQL + MeiliSearch

### AI 应用/Agent
Next.js 14 + FastAPI + Redis + 混元/DeepSeek + CloudBase

### 鸿蒙应用
ArkTS + ArkUI + HTTP + 关系型DB + Push Kit

### 桌面端工具
Tauri + React 18 + SQLite + 本地 AI
