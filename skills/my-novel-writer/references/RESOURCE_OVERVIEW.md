# 📚 Novel Writer 资源包总览

> **生成时间**：2026-03-06  
> **版本**：1.0 (完整版)

---

## ✅ 已生成的资源清单

### 1. 核心逻辑 (Core Logic)
| 文件 | 功能 |
| :--- | :--- |
| `core.py` | 记忆管理、大纲控制、章节生成 |
| `__init__.py` | 模块初始化 |

### 2. 模板资源 (Templates)
| 文件 | 用途 |
| :--- | :--- |
| `templates/character_card.md` | **人物卡模板**：记录姓名、外貌、性格、背景、关系、成长弧光 |
| `templates/world_building.md` | **世界观设定表**：时代背景、规则、历史、地点、文化 |
| `templates/chapter_outline.md` | **章节大纲模板**：场景设计、剧情要点、伏笔、检查清单 |

### 3. 参考指南 (Guides)
| 文件 | 内容 |
| :--- | :--- |
| `guides/novel_structure_guide.md` | **小说结构指南**：三幕式结构、人物弧光、伏笔技巧、节奏控制、叙事技巧 |

### 4. 实用脚本 (Scripts)
| 文件 | 功能 |
| :--- | :--- |
| `scripts/plot_tracker.py` | **伏笔追踪器**：自动记录、检查伏笔，避免前后矛盾 |

### 5. 示例项目 (Examples)
| 文件 | 内容 |
| :--- | :--- |
| `examples/project_example.json` | **完整示例**：包含人物、世界观、大纲、伏笔的示例项目 |

---

## 📂 完整目录结构

```text
/app/working/customized_skills/novel_writer/
├── SKILL.md                  # 📖 使用说明书（已更新）
├── __init__.py               # 模块初始化
├── core.py                   # 🧠 核心逻辑
├── templates/                # 📝 模板资源
│   ├── character_card.md     # 人物卡模板
│   ├── world_building.md     # 世界观设定表
│   └── chapter_outline.md    # 章节大纲模板
├── guides/                   # 📋 参考指南
│   └── novel_structure_guide.md # 小说结构指南
├── scripts/                  # 🛠️ 实用脚本
│   └── plot_tracker.py       # 伏笔追踪器
└── examples/                 # 📚 示例项目
    └── project_example.json  # 完整示例
```

---

## 🚀 如何使用这些资源？

### 步骤 1：准备人物卡
1. 复制模板：
   ```bash
   cp /app/working/customized_skills/novel_writer/templates/character_card.md examples/characters/李长风.md
   ```
2. 打开 `李长风.md`，填写详细信息。
3. 重复此步骤，为所有主要角色创建人物卡。

### 步骤 2：构建世界观
1. 复制模板：
   ```bash
   cp /app/working/customized_skills/novel_writer/templates/world_building.md examples/world.md
   ```
2. 填写世界观设定。

### 步骤 3：规划大纲
1. 为每章复制章节大纲模板：
   ```bash
   cp /app/working/customized_skills/novel_writer/templates/chapter_outline.md examples/outline_ch1.md
   ```
2. 填写每章的剧情要点、场景、伏笔。

### 步骤 4：运行伏笔追踪器
```bash
python3 /app/working/customized_skills/novel_writer/scripts/plot_tracker.py
```
- 自动记录伏笔（开启、发展、关闭）。
- 检查未关闭伏笔，避免烂尾。

### 步骤 5：参考结构指南
- 写作时随时查阅 `guides/novel_structure_guide.md`，确保结构合理。

---

## 💡 进阶建议

1. **集成 LLM API**：在 `core.py` 中调用真实 LLM，实现自动章节生成。
2. **多人协作**：使用 Git 管理 `examples/` 目录，多人共同创作。
3. **导出为 Word**：结合 `docx` 技能，将生成的章节导出为 Word 文档。
4. **可视化人物关系图**：使用 Python 库（如 `graphviz`）生成人物关系图。

---

> 🌟 **祝你在小说创作的道路上，笔耕不辍，佳作频出！** 🖋️
