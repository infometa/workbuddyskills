# 汽车图文创作专家团（生产版）

> Production-ready automotive content creation team powered by WorkBuddy built-in ImageGen.

## 概述

本专家团是**生产版**汽车图文创作工具，面向 WorkBuddy 平台用户直接使用。与本地开发版（content-creation-expert）的核心差异：

- **配图**：7种场景策略 + 智能工具选型（ImageGen/HY-Image-V3.0/HY-Image-Lite），无需配置 VOD API
- **COS 可选**：配置了 AKSK 则图片上传 COS 获取公网 URL；未配置则图片 base64 内嵌到 HTML
- **文风**：目前只支持懂车帝（D模板）写作风格
- **精简依赖**：去掉 MCP 车型库/素材库、文本 LLM API、VOD AIGC API

## 团队成员

| 角色 | 名称 | 职责 |
|------|------|------|
| 主理人 | 典明轩 | 全流程编排、需求澄清、成员调度、产物交付 |
| 选题研究官 | 柯研之 | web_search 收集选题素材，输出 Creative Brief |
| 汽车主笔 | 文思远 | 懂车帝风格长文写作（大纲+全文），含 IMAGE 标记 |
| 视觉总监 | 邵景 | 7种场景策略智能配图（ImageGen/HY-V3.0/Lite），支持本地图替换 |
| 质检官 | 严慎之 | 质量检查（程序化+增量人工审查） |

## 工作流程

```
Phase 0: 需求澄清（选题/平台/字数/补充信息）
Phase 1: 选题研究（brief-researcher）
Phase 2a: 大纲确认（auto-writer）
Phase 2b: 全文撰写 + 预检（validate-article）
Phase 3: AI 配图（visual-director 7种策略智能配图 + render-html 图片双模式处理）
Phase 4: 质检（quality-editor）
Phase 5: 交付（HTML + MD）
```

## 配置

仅需配置 COS（可选）：

```bash
cp skills/content-creation-expert-prod/.env.example skills/content-creation-expert-prod/.env
# 编辑 .env，填入 COS AKSK（可选）
```

## 本地图替换

用户在任意阶段可以指定替换某个图位为本地图片：
- 告诉主理人"第2张图换成我本地的 /path/to/photo.jpg"
- visual-director 会跳过该图位的 AI 生成，直接使用用户图片
