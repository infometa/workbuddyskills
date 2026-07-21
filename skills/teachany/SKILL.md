---
name: teachany
description: K-12 interactive courseware creation. Use for school-subject lesson pages, animations, AI tutor, TTS, knowledge graph, PBL learning paths, or TeachAny publishing.
description_zh: K12 互动课件开发技能：用于制作或优化学科课件、教学动画、AI 学伴、TTS、知识图谱、PBL 学习路径与 TeachAny 发布。
description_en: Create K-12 interactive lesson pages, animations, AI tutor, TTS, knowledge graphs & PBL paths for TeachAny
version: 7.14.1
allowed-tools: Read,Write,Edit,Bash,Glob,Grep
---

# TeachAny：K12 互动课件执行摘要

TeachAny 的目标不是把知识堆进页面，而是把一节课做成**有问题锚点、有互动、有讲解、有评估、有发布闭环**的学习体验。主文件只保留决策骨架；细节按需读取卫星文档。

## 何时使用

使用本技能：

- 用户要制作、改造、调试或发布 K12 学科课件、互动网页、微课、教学动画、PBL 探究课。
- 用户提到：`课件`、`教学设计`、`AI 学伴`、`TTS`、`知识图谱`、`课标`、`PBL`、`学习路径`、`发布到 Gallery`、`rebuild-index`。
- 用户是家长/教师/学生，目标是帮助中小学生理解一个具体知识点。

不要使用：企业培训、成人职业技能课、通用网站/App、纯 PPT/Word 格式转换、非 K12 展览页。

## Quick Start

用户：`我儿子初二搞不懂浮力，做个能玩的页面。`

标准输出路径：

1. 查 `node_id`：`python3 scripts/find_nodes.py "浮力"`。
2. 复制 `templates/course-skeleton.html` 和 `templates/manifest-template.json`。
3. 用"为什么沉浮不同？"做问题锚点，加入拖拽物体/液体密度的 Canvas 互动。
4. 接入五件套：AI 学伴、TTS、section hints、知识图谱、导师卡片。
5. 生成 Hero 知识结构图（`gen-hero-svg.py`）。
6. 本地验证通过后走发布流程。

## 模式说明

TeachAny **只有一种模式**：完整模式。没有"快速模式"，没有"先做个简版"。

所有课件必须完整包含 19 项基线（见 `references/baseline-rules.md`），包括：manifest、五件套模块、Hero 图、TTS、知识图谱挂树、发布闭环。

**唯一允许豁免的情形**：某项依赖外部资源，在**当前网络环境下反复尝试（≥2 次，每次间隔 ≥30 秒）确实无法连接**，且无本地替代方案时，该单项可临时跳过并在交付说明中明确注明：
- 豁免原因（具体报错或 HTTP 状态码）
- 已尝试次数和方式
- 后续补齐的操作步骤

**不构成豁免理由的情形**：
- "用户只是想先看看效果"
- "先做简版，之后再补"
- "这个功能感觉用不上"
- 任何主观判断或时间压力

### 基础设施模式（维护 TeachAny 本身）

适用：修 `scripts/`、模板、Gallery、知识树、PBL、发布链路。

- 直接定位问题、修复、验证。
- 不套用课件制作的全流程，但必须遵守闭环验证。
- **课件发布仍须走正规路径**：批量修复/升级课件后，不要 `git commit && git push`——必须先检测凭据，无 GitHub 权限则逐门跑 `publish_course.sh`（见规则 #25a）。

## 4-Phase 流程

```text
Phase 0  定义与检索：学生/学段/主题/课型，定位 node_id
Phase 1  教学骨架：问题锚点 + ABT 叙事 + 互动/评估设计（必须完整，不可跳过）
Phase 2  构建页面：复制模板，填内容，接入标准模块与资源
Phase 3  验证交付：运行质量检查，浏览器/命令闭环验证
Phase 4  发布注册：执行 Git/Registry/Gallery 流程，验证线上 URL
```

完整细节见 `phases/workflow.md`；发布细节见 `phases/packaging.md`。

## 核心规则（最终有效版）

1. **模板优先**：新课件先复制 `templates/course-skeleton.html` 与 `templates/manifest-template.json`，不要从空白页手写平台接线。
2. **学习闭环优先**：每课必须有问题锚点、互动尝试、即时反馈、总结迁移；视觉炫技不能替代学习设计。
3. **标准模块优先**：AI 学伴、导师卡片、TTS narrator、section hints、知识图谱优先用标准模块 API，不重复手写。
4. **真实互动**：标题写"互动/实验/探究/地图/画布"就必须可操作；静态图不能伪装互动。
5. **知识图谱入树**：优先匹配官方 `node_id`；没有则注册；确实无法归类才用 `free_mode` 或 `ext-*`。
6. **地图库优先**：历史/地理先用 `scripts/find-map.py` 查 bundled map library，再考虑外部数据或生成。
7. **数理化必须加载仿真工具文档**：制作**数学/物理/化学/生物**课件时，**在 Phase 2 开始前必须先读** `tech/iframe-resources.md`，按学科-工具快查表选择并嵌入至少 1 个外部交互工具（PhET / GeoGebra / Desmos / 3Dmol.js 等）。不得用纯静态图或简单 Canvas 代替已有成熟工具的场景。
8. **发布先检测环境**：没有目标仓库、权限或远端不可达时，不要假设 `weponusa/*` 可写；先提示 fork/跳过发布/本地交付。
9. **依赖豁免须有证据**：某项外部资源无法连接，必须给出具体报错（curl 输出或 HTTP 状态码）、已重试次数，才允许该单项豁免；不得以"可能慢"或"先跳过"为由省略。
10. **闭环验证**：说"完成/修复/可用"前必须跑命令或浏览器验证，并给出关键输出。URL 未返回 200 不得声称发布完成。
11. **一类问题一起扫**：修一个模块或模式后，检查同类文件、模板、courseware/opensource 双仓是否同步。
12. **图片资产必须真实**：禁止在 hero/header 后面堆叠裸 `<img>` 标签；禁止 assets/ 下放 <5KB 的占位图（webp/png/jpg）。概念图、示意图必须嵌入对应教学 section 内部。如果图片资源暂未生成，不引用、不放文件——宁缺勿占。

完整硬规则、基线清单与反模式：按需读 `references/baseline-rules.md`、`RULES.md`。

## 文档路由（按需加载）

| 场景 | 读取 |
| --- | --- |
| 完整 Phase 细节 | `phases/workflow.md` |
| 打包、Registry、Gallery、Git 发布 | `phases/packaging.md` |
| TTS、Remotion、视频音频 | `phases/video-audio.md` |
| 19 项基线与反模式 | `references/baseline-rules.md` |
| Phase 1 问卷 | `references/phase1-checklist.md` |
| 互动形态 | `guides/interaction-patterns.md` |
| PBL/探究课 | `guides/project-based.md` |
| 练习评估 | `guides/assessment.md` |
| 页面结构与 CSS | `tech/page-structure.md`, `tech/design-system.md` |
| 数学/科学仿真 | `tech/math-animations.md`（数学课件**必读**）, `tech/science-simulations.md`（物理/化学/生物课件**必读**） |
| **可嵌入 iframe 资源总目录** | `tech/iframe-resources.md`（**数理化必读**，PhET/GeoGebra/Desmos/3Dmol/LearningApps 等完整清单） |
| 地图 / 3D / PPTX | `topics/maps-and-3d.md` |
| 示例 | `guides/examples.md` |

## 常用脚本

假设 `TEACHANY_SKILL` 指向 skill 安装目录，`COURSE_DIR` 指向课件目录：

```bash
export TEACHANY_SKILL=/path/to/teachany/skill
export COURSE_DIR=~/CodeBuddy/一次函数/teachany-courseware/community/<course-id>
python3 "$TEACHANY_SKILL/scripts/preflight-check.py"
python3 "$TEACHANY_SKILL/scripts/find_nodes.py" "一次函数"
python3 "$TEACHANY_SKILL/scripts/find-hero.py" <course-id>
python3 "$TEACHANY_SKILL/scripts/gen-hero-svg.py" "$COURSE_DIR"
python3 "$TEACHANY_SKILL/scripts/tts-engine.py" --text "讲解文本" --voice zh-CN-XiaoxiaoNeural --output "$COURSE_DIR/tts/s01.mp3"
python3 "$TEACHANY_SKILL/scripts/apply-standard-modules.py" --only "$COURSE_DIR/index.html"
python3 "$TEACHANY_SKILL/scripts/find-map.py" 唐
python3 "$TEACHANY_SKILL/scripts/apply-historical-maps.py"
node "$TEACHANY_SKILL/scripts/validate-courseware.cjs" "$COURSE_DIR"
```

**发布课件（两种路径）**：

```bash
# ① 普通用户 / 社区投稿 — 走 Cloudflare Worker，无需 GitHub token
bash "$TEACHANY_SKILL/scripts/publish_course.sh" "$COURSE_DIR" <course-id>

# ② 仓库维护者直推 — 需要 SSH 或 GH_TOKEN
bash "$TEACHANY_SKILL/scripts/auto-publish.sh" <course-id>
```

**默认走 ① `publish_course.sh`**：课件提交到 `teachany-community.pages.dev` Worker，Worker 自动走 PR 质检流程合并到仓库，用户无需任何 GitHub 凭据。

`auto-publish.sh` 仅供仓库维护者使用，完成：验证目录 → `rebuild-index.py`（注册+挂树）→ `git commit/push` → 验证线上 URL。

**认证说明（`auto-publish.sh` 专用，普通用户忽略）**：
- SSH 已配置（本地 Mac 默认走 SSH，无需额外操作）
- CI / Agent 环境：`export GH_TOKEN=<github_pat>` 后再跑脚本，脚本会自动配置 HTTPS remote
- 也可运行一次 `bash "$TEACHANY_SKILL/scripts/setup.sh"` 永久配置

如果脚本不存在，先在仓库根 `scripts/` 与 `skill/scripts/` 中搜索；不要引用不存在的脚本名。

## 交付标准

所有课件（无论场景）统一标准：

- 通过 `validate-courseware.cjs` 质检
- 关键资源存在：index.html、manifest.json、PLAN.md、assets/、tts/（或豁免记录）
- 控制台无错误，核心互动可用，移动端不崩
- Registry/Gallery 可访问，线上 URL 返回 HTTP 200

## 版本说明

当前执行摘要版本：`7.14.0`。历史变更不放入主文件，避免污染执行上下文；需要考古时查 Git 历史或仓库发布记录。
