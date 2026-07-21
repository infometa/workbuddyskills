---
name: my-novel-writer
description: >-
  Novel writing assistant with character management, worldbuilding, outline
  control, and chapter generation. Features plot thread tracking, character
  cards, world templates, and quality review. Supports wuxia, urban, sci-fi,
  and fantasy genres. Triggers: 写小说, 创作小说, 人物设定, 世界观, 大纲,
  章节生成, novel writing, character creation.
description_zh: 辅助创作长篇小说，支持人物设定、世界观管理和分章生成
description_en: Novel writing with character management, worldbuilding & chapter generation
version: 1.0.0
---
# Novel Writer 技能

**描述**: 辅助创作长篇小说的智能助手，支持人物设定、世界观管理、大纲控制和分章生成。

---

## 🚀 功能特性

> ⚠️ **重要**：请通过环境变量配置 API 密钥，不要在配置文件中硬编码。

### 环境变量列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `WORKDIR` | 否 | `/app/working` | 工作目录 |
| `NOVEL_API_KEY` | 是 | - | API 密钥 |
| `NOVEL_API_BASE_URL` | 否 | - | API 基础 URL |
| `NOVEL_MODEL` | 否 | `gpt-3.5-turbo` | 模型名称 |
| `NOVEL_TEMPERATURE` | 否 | `0.8` | 温度参数 |
| `NOVEL_MAX_TOKENS` | 否 | `4096` | 最大令牌数 |
| `NOVEL_DEFAULT_STYLE` | 否 | `wuxia` | 默认写作风格 |

### 使用示例

```bash
# Linux/Mac
export NOVEL_API_KEY="sk-xxx"
export NOVEL_API_BASE_URL="https://your-api.com/v1"
export NOVEL_MODEL="qwen/qwen3.5-122b-a10b"

# Windows (CMD)
set NOVEL_API_KEY=sk-xxx

# Windows (PowerShell)
$env:NOVEL_API_KEY="sk-xxx"
```

---

- ✅ **记忆持久化**: 自动保存人物、世界观、大纲和已写章节，避免遗忘。
- ✅ **大纲驱动**: 先规划大纲，再按章生成，确保剧情逻辑连贯。
- ✅ **风格锁定**: 支持自定义写作风格（如：武侠、科幻、悬疑）。
- ✅ **进度管理**: 实时查看创作进度，支持动态调整大纲。
- ✅ **文件输出**: 每章自动生成独立的 `.md` 文件，方便后续编辑。

---

## 📖 使用指南

### 1. 初始化小说
```text
novel_writer --new "我的奇幻世界"
```
> 这将创建一个名为《我的奇幻世界》的新小说项目，并初始化记忆库。

### 2. 设定人物
```text
novel_writer --set-character "林风" "主角，25岁，剑客，性格孤傲但重情义。"
novel_writer --set-character "苏月" "女主角，23岁，医师，温柔善良，擅长草药。"
```

### 3. 设定世界观
```text
novel_writer --set-world "一个充满魔法与剑的奇幻大陆，分为三大王国，常年处于战争边缘。"
```

### 4. 规划大纲
```text
novel_writer --add-outline 1 "初遇" "林风在森林中救下受伤的苏月，两人结伴同行。"
novel_writer --add-outline 2 "危机" "遭遇敌国刺客，林风重伤，苏月用草药救他。"
```

### 5. 生成章节
```text
novel_writer --generate 1 2500
```
> 生成第 1 章，目标字数 2500 字。生成后会自动保存到 `novels/` 目录。

### 6. 查看进度
```text
novel_writer --status
```

### 7. 更新大纲（动态调整）
```text
novel_writer --update-outline 2 "危机升级" "敌国刺客增多，林风发现刺客首领竟是自己失散多年的师兄。"
```

---

## 📂 完整文件结构

```text
/app/working/
├── memory/
│   └── novel_context.json      # 核心记忆库（人物、世界观、大纲、章节摘要）
├── novels/
│   ├── 我的奇幻世界_ch1.md     # 第 1 章内容
│   ├── 我的奇幻世界_ch2.md     # 第 2 章内容
│   └── ...
└── customized_skills/
    └── novel_writer/
        ├── SKILL.md            # 本说明书
        ├── scripts/            # 🛠️ 核心逻辑与实用脚本
        │   ├── __init__.py             # 模块初始化
        │   ├── core.py                 # 核心逻辑
        │   ├── config_models.py        # 配置模型
        │   ├── prompts.py              # Prompt 模板
        │   ├── text_processor.py       # 文本处理器
        │   └── plot_tracker.py         # 伏笔追踪器
        ├── templates/          # 📝 模板资源
        │   ├── character_card.md       # 人物卡模板
        │   ├── world_building.md       # 世界观设定表
        │   └── chapter_outline.md      # 章节大纲模板
        ├── guides/             # 📋 参考指南
        │   └── novel_structure_guide.md # 小说结构指南
        ├── references/         # 📖 参考文档
        │   ├── LESSONS_LEARNED.md      # 经验总结
        │   └── RESOURCE_OVERVIEW.md    # 资源概览
        └── examples/           # 📚 示例项目
            └── project_example.json    # 完整示例
```

---

## ⚙️ 高级技巧

### 1. 风格微调
在生成前，先设定风格：
```text
novel_writer --set-style "古风武侠，语言半文半白，注重意境描写。"
```

### 2. 一致性检查
生成后，可手动检查人物状态是否冲突（如：上一章受伤，下一章完好）。
> 建议：在生成前，先读取 `novel_context.json` 中的 `characters` 状态。

### 3. 批量生成
```text
for i in {1..5}; do
  novel_writer --generate $i 2000
done
```

---

## 🛠️ 技术实现

- **记忆管理**: 使用 JSON 文件存储上下文，支持增量更新。
- **分章生成**: 每次只生成一章，避免上下文超限。
- **摘要机制**: 每章生成后，自动提取摘要存入记忆库，供下一章参考。

---

## 📝 示例：从零开始写第一章

1. **创建小说**:
   ```text
   novel_writer --new "江湖夜雨"
   ```
2. **设定人物**:
   ```text
   novel_writer --set-character "李长风" "中年剑客，背负血海深仇。"
   ```
3. **设定世界观**:
   ```text
   novel_writer --set-world "大周王朝末年，江湖势力割据，朝廷腐败。"
   ```
4. **规划大纲**:
   ```text
   novel_writer --add-outline 1 "雨夜孤剑" "李长风在雨夜中独行，遭遇神秘杀手。"
   ```
5. **生成第一章**:
   ```text
   novel_writer --generate 1 3000
   ```
6. **查看结果**:
   ```text
   cat /app/working/novels/江湖夜雨_ch1.md
   ```

---

> 💡 **提示**: 本技能支持与其他技能（如 `docx`）结合，将生成的章节导出为 Word 文档进行精修。

---

## 🎁 捆绑资源包 (Bundled Resources)

本技能附带了完整的创作资源包，帮助你更高效地构建长篇小说。

---

## 🚀 核心生成规范 v2.0 (基于实战优化)

> **重要**：自本次更新起，所有生成的小说章节必须严格遵守以下规范，确保**字数达标、逻辑闭环、风格纯正**。

### 1. 字数控制 (Word Count)
- **硬性指标**：每章正文（不含标题）必须严格控制在 **2200 - 2500 字**。
- **禁止注水**：严禁通过重复对话、无意义环境描写凑字数。
- **补全机制**：若初稿字数不足，必须自动增加：
  - **心理独白**（主角的内心挣扎、回忆、算计）。
  - **环境渲染**（光影、声音、气味、温度）。
  - **动作细节**（战斗中的慢镜头分解、招式拆解）。
  - **配角反应**（围观群众的震惊、反派的微表情）。

### 2. 逻辑闭环 (Logic Consistency)
- **伏笔追踪**：前文提到的设定（如“绝脉”、“玉坠”），必须在后续章节有明确回收或呼应。
- **人物状态**：
  - 受伤必须恢复（或留下后遗症），不可瞬间痊愈。
  - 获得物品必须使用（或展示效果），不可凭空消失。
  - 情绪必须连贯（愤怒后是冷静，喜悦后是警惕）。
- **战力体系**：
  - 主角升级必须有过程（痛苦、瓶颈、突破）。
  - 反派不可降智（必须有合理的动机和手段）。
  - 战斗结果必须符合逻辑（以弱胜强需有“金手指”或“计谋”支撑）。

### 3. 风格统一 (Style Consistency)
- **第一人称**：严格保持“我”的视角，不可随意切换。
- **爽点密度**：每章至少包含1个“小爽点”（如打脸、突破、获得宝物）。
- **节奏把控**：
  - 开篇：快速切入冲突（黄金三章法则）。
  - 中段：铺垫与博弈（增加悬念）。
  - 结尾：留下钩子（悬念、新危机、新目标）。

### 4. 违禁词与敏感内容 (Safety)
- **替换规则**：
  - “杀” → “陨落”、“寂灭”、“身死”。
  - “死” → “魂飞魄散”、“灰飞烟灭”。
  - “血” → “猩红”、“染血”。
- **审核规避**：避免过度暴力、色情、政治敏感内容。

### 5. 交互与反馈 (Interaction)
- **作者说**：每章末尾必须添加“作者说”，引导读者互动（求收藏、求推荐票）。
- **章节标题**：必须包含“钩子”（如“苏天陨落”、“玉坠觉醒”），吸引点击。

---

## 📂 文件结构

### 📝 1. 模板资源 (`templates/`)
- **人物卡模板** (`character_card.md`)：详细记录人物设定、性格、关系、成长弧光。
- **世界观设定表** (`world_building.md`)：构建宏大的背景，确保设定逻辑自洽。
- **章节大纲模板** (`chapter_outline.md`)：规划每章剧情、场景、伏笔，避免跑偏。

### 📋 2. 参考指南 (`guides/`)
- **小说结构指南** (`novel_structure_guide.md`)：包含三幕式结构、人物弧光设计、伏笔技巧、节奏控制等经典理论。

### 🛠️ 3. 实用脚本 (`scripts/`)
- **核心逻辑** (`core.py`)：小说生成的核心引擎，包含记忆管理、章节生成、摘要提取等。
- **配置模型** (`config_models.py`)：环境变量解析与配置管理。
- **Prompt 模板** (`prompts.py`)：各类生成场景的 Prompt 模板。
- **文本处理器** (`text_processor.py`)：章节文本的后处理（字数统计、格式化等）。
- **伏笔追踪器** (`plot_tracker.py`)：
  - 自动记录伏笔（开启、发展、关闭）。
  - 检查未关闭伏笔，避免烂尾。
  - 生成伏笔追踪表，一目了然。
  - **使用方法**：
    ```bash
    python3 scripts/plot_tracker.py
    ```

### 📚 4. 示例项目 (`examples/`)
- **完整示例** (`project_example.json`)：包含人物、世界观、大纲、伏笔的完整示例，供你参考学习。

---

## 🚀 快速上手：使用资源包

1. **复制模板**：
   ```bash
   cp /app/working/customized_skills/novel_writer/templates/character_card.md examples/characters/李长风.md
   ```
2. **填写人物卡**：打开 `李长风.md`，填写详细信息。
3. **规划大纲**：使用 `chapter_outline.md` 模板，规划每章剧情。
4. **运行伏笔追踪器**：
   ```bash
   python3 scripts/plot_tracker.py
   ```
5. **参考结构指南**：写作时随时查阅 `novel_structure_guide.md`，确保结构合理。

---

> 🌟 **祝你在小说创作的道路上，笔耕不辍，佳作频出！** 🖋️
