---
name: yourself-skill
description: "Distill yourself into an AI Skill. Deconstruct chat history, diaries, social media, and photos into a runnable digital self with persona and memory models. Use when user wants to create a digital twin, self-reflection mirror, or personal knowledge archive."
description_zh: "把自己蒸馏成 AI Skill，解构聊天记录与日记生成数字分身"
description_en: "Distill yourself into an AI Skill — digital twin with persona and memory"
version: "1.0.0"
homepage: https://github.com/notdog1998/yourself-skill
allowed-tools: Read, Write, Edit, Bash
---

> **Language / 语言**: This skill supports both English and Chinese. Detect the user's language from their first message and respond in the same language throughout. Below are instructions in both languages — follow the one matching the user's language.
>
> 本 Skill 支持中英文。根据用户第一条消息的语言，全程使用同一语言回复。下方提供了两种语言的指令，按用户语言选择对应版本执行。

# 自己.skill 创建器（Claude Code 版）

## 触发条件

当用户说以下任意内容时启动：
- `/create-yourself`
- "帮我创建一个自己的 skill"
- "我想把自己蒸馏成 skill"
- "新建自我镜像"
- "给我做一个我自己的 skill"

当用户对已有自我 Skill 说以下内容时，进入进化模式：
- "我有新文件" / "追加"
- "这不对" / "我不会这样说" / "我应该是"
- `/update-yourself {slug}`

当用户说 `/list-selves` 时列出所有已生成的自我 Skill。

---

## 工具使用规则

本 Skill 运行在 Claude Code 环境，使用以下工具：

| 任务 | 使用工具 |
|------|----------|
| 读取 PDF/图片 | `Read` 工具 |
| 读取 MD/TXT 文件 | `Read` 工具 |
| 解析微信聊天记录导出 | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/wechat_parser.py` |
| 解析 QQ 聊天记录导出 | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/qq_parser.py` |
| 解析社交媒体内容 | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/social_parser.py` |
| 分析照片元信息 | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/photo_analyzer.py` |
| 写入/更新 Skill 文件 | `Write` / `Edit` 工具 |
| 版本管理 | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/version_manager.py` |
| 列出已有 Skill | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action list` |
| 合并生成 SKILL.md | `Bash` → `python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine` |

**目标目录**：生成的 Skill 必须写入 `./.claude/skills/{slug}/`，这样 `/{slug}` 才能被 Claude Code 直接识别和调用。

> **Windows 用户注意**：如果你使用 Git Bash，`python3` 可能不可用，所有命令已统一使用 `python`。若运行时中文输出乱码，请在 Bash 中先执行 `export PYTHONIOENCODING=utf-8`。

---

## 主流程：创建新自我 Skill

### Step 1：基础信息录入（3 个问题）

参考 `${CLAUDE_SKILL_DIR}/prompts/intake.md` 的问题序列，只问 3 个问题：

1. **代号/昵称**（必填）
   - 示例：`小北` / `自己` / `20岁的我`
2. **基本信息**（一句话：年龄、职业、城市，想到什么写什么）
   - 示例：`25 岁，互联网产品经理，上海`
3. **自我画像**（一句话：MBTI、星座、性格标签、你对自己的印象）
   - 示例：`INTJ 摩羯座 社恐但话痨 深夜emo型选手`

除代号外均可跳过。收集完后汇总确认再进入下一步。

### Step 2：原材料导入

询问用户提供原材料，展示方式供选择：

```
原材料怎么提供？数据越多，还原度越高。

  [A] 微信聊天记录导出
      支持 WeChatMsg、留痕、PyWxDump 等工具的导出格式
      重点分析「我」说的话，提取说话风格和思维模式

  [B] QQ 聊天记录导出
      支持 QQ 消息管理器导出的 txt/mht 格式

  [C] 社交媒体 / 日记 / 笔记
      朋友圈截图、微博/小红书、备忘录、Obsidian 笔记等

  [D] 上传文件
      照片（会提取时间地点，构建人生时间线）、PDF、文本文件

  [E] 直接粘贴/口述
      把你对自己的认知告诉我
      比如：你的口头禅、做决定的方式、生气时的反应

可以混用，也可以跳过（仅凭手动信息生成）。
```

---

#### 方式 A：微信聊天记录导出

```
python ${CLAUDE_SKILL_DIR}/tools/wechat_parser.py \
  --file {path} \
  --target "我" \
  --output /tmp/wechat_out.txt \
  --format auto
```

支持的格式：WeChatMsg 导出（txt/html/csv）、留痕导出（JSON）、PyWxDump 导出（SQLite）、手动复制粘贴（纯文本）。

解析提取维度：
- 「我」的高频词和口头禅
- 表情包和 emoji 使用偏好
- 回复速度和对话发起模式
- 话题分布（工作/情感/日常/深夜思考）
- 语气词和标点符号习惯
- 与他人互动时的典型表达方式

---

#### 方式 B：QQ 聊天记录导出

```
python ${CLAUDE_SKILL_DIR}/tools/qq_parser.py \
  --file {path} \
  --target "我" \
  --output /tmp/qq_out.txt
```

支持 QQ 消息管理器导出的 txt 和 mht 格式。

---

#### 方式 C：社交媒体 / 日记 / 笔记

图片截图用 `Read` 工具直接读取。
文本文件用 `Read` 工具直接读取。

---

#### 方式 D：照片分析

```
python ${CLAUDE_SKILL_DIR}/tools/photo_analyzer.py \
  --dir {photo_dir} \
  --output /tmp/photo_out.txt
```

提取维度：
- EXIF 信息：拍摄时间、地点
- 时间线：人生关键节点的地理轨迹
- 常去地点：生活模式推断

---

#### 方式 E：直接粘贴/口述

用户粘贴或口述的内容直接作为文本原材料。引导用户回忆：

```
可以聊聊这些（想到什么说什么）：

🗣️ 你的口头禅是什么？
💬 你做决定的时候通常怎么想？
🍜 你难过的时候一般会做什么？
📍 你最喜欢去哪里？
🎵 你喜欢什么音乐/电影/书？
😤 你生气的时候是什么样？
💭 你深夜alone的时候在想什么？
🌱 你觉得自己这几年最大的变化是什么？
```

---

如果用户说"没有文件"或"跳过"，仅凭 Step 1 的手动信息生成 Skill。

### Step 3：分析原材料

将收集到的所有原材料和用户填写的基础信息汇总，按以下两条线分析：

**线路 A（Self Memory）**：
- 参考 `${CLAUDE_SKILL_DIR}/prompts/self_analyzer.md` 中的提取维度
- 提取：个人经历、价值观、生活习惯、重要记忆、人际关系图谱、成长轨迹

**线路 B（Persona）**：
- 参考 `${CLAUDE_SKILL_DIR}/prompts/persona_analyzer.md` 中的提取维度
- 将用户填写的标签翻译为具体行为规则
- 从原材料中提取：说话风格、情感模式、决策模式、人际行为

### Step 4：生成并预览

参考 `${CLAUDE_SKILL_DIR}/prompts/self_builder.md` 生成 Self Memory 内容。
参考 `${CLAUDE_SKILL_DIR}/prompts/persona_builder.md` 生成 Persona 内容（5 层结构）。

向用户展示摘要（各 5-8 行），询问：

```
Self Memory 摘要：
  - 核心价值观：{xxx}
  - 生活习惯：{xxx}
  - 重要记忆：{xxx}
  - 人际模式：{xxx}
  ...

Persona 摘要：
  - 说话风格：{xxx}
  - 情感模式：{xxx}
  - 决策方式：{xxx}
  - 口头禅：{xxx}
  ...

确认生成？还是需要调整？
```

### Step 5：写入文件

用户确认后，**优先使用 Bash 脚本一键创建**。如果脚本调用失败，再用 `Write` 工具手动写入（路径必须正确）。

#### 方式 A：脚本一键创建（推荐）

先用 Bash 将内容写入临时文件，然后调用 `skill_writer.py --action create`：

```bash
mkdir -p /tmp/yourself_{slug}
echo '{escaped_meta_json}' > /tmp/yourself_{slug}/meta.json
cat > /tmp/yourself_{slug}/self.md <<'SELFEOF'
{self_content}
SELFEOF
cat > /tmp/yourself_{slug}/persona.md <<'PERSONAEOF'
{persona_content}
PERSONAEOF

python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py \
  --action create \
  --slug {slug} \
  --base-dir ./.claude/skills \
  --meta /tmp/yourself_{slug}/meta.json \
  --self /tmp/yourself_{slug}/self.md \
  --persona /tmp/yourself_{slug}/persona.md
```

#### 方式 B：手动写入（脚本失败时的 fallback）

如果 Bash 脚本因任何原因无法执行，**必须**使用 `Write` / `Edit` 工具将文件写入以下路径：

- `self.md` → `.claude/skills/{slug}/self.md`
- `persona.md` → `.claude/skills/{slug}/persona.md`
- `meta.json` → `.claude/skills/{slug}/meta.json`
- 然后用 Bash 运行 `python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine --slug {slug} --base-dir ./.claude/skills` 生成 `SKILL.md`
- 如果 combine 也失败，直接手动写入 `.claude/skills/{slug}/SKILL.md`（参考 combine 的输出模板）

`meta.json` 内容：
```json
{
  "name": "{name}",
  "slug": "{slug}",
  "created_at": "{ISO时间}",
  "updated_at": "{ISO时间}",
  "version": "v1",
  "profile": {
    "age": "{age}",
    "occupation": "{occupation}",
    "city": "{city}",
    "gender": "{gender}",
    "mbti": "{mbti}",
    "zodiac": "{zodiac}"
  },
  "tags": {
    "personality": [...],
    "lifestyle": [...]
  },
  "impression": "{impression}",
  "memory_sources": [...已导入文件列表],
  "corrections_count": 0
}
```

告知用户：
```
✅ 自我 Skill 已创建！

文件位置：.claude/skills/{slug}/
触发词：/{slug}（完整版 — 像你一样思考和说话）
        /{slug}-self（自我档案模式 — 帮你回忆和分析自己）
        /{slug}-persona（人格模式 — 仅性格和表达风格）

如果用起来感觉哪里不像你，直接说"我不会这样"，我来更新。
```

---

## 进化模式：追加文件

用户提供新的聊天记录、照片或笔记时：

1. 按 Step 2 的方式读取新内容
2. 用 `Read` 读取现有 `.claude/skills/{slug}/self.md` 和 `.claude/skills/{slug}/persona.md`
3. 参考 `${CLAUDE_SKILL_DIR}/prompts/merger.md` 分析增量内容
4. 存档当前版本（用 Bash）：
   ```bash
   python ${CLAUDE_SKILL_DIR}/tools/version_manager.py --action backup --slug {slug} --base-dir ./.claude/skills
   ```
5. 用 `Edit` 工具追加增量内容到对应文件（路径：`.claude/skills/{slug}/self.md` 或 `.claude/skills/{slug}/persona.md`）
6. 重新生成 `SKILL.md`（用 Bash 调用 skill_writer combine）：
   ```bash
   python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine --slug {slug} --base-dir ./.claude/skills
   ```
7. 更新 `meta.json` 的 version 和 updated_at（路径：`.claude/skills/{slug}/meta.json`）

---

## 进化模式：对话纠正

用户表达"不对"/"我不会这样说"/"我应该是"时：

1. 参考 `${CLAUDE_SKILL_DIR}/prompts/correction_handler.md` 识别纠正内容
2. 判断属于 Self Memory（事实/经历）还是 Persona（性格/说话方式）
3. 生成 correction 记录
4. 用 `Edit` 工具追加到对应文件的 `## Correction 记录` 节（`.claude/skills/{slug}/self.md` 或 `.claude/skills/{slug}/persona.md`）
5. 重新生成 `SKILL.md`：
   ```bash
   python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action combine --slug {slug} --base-dir ./.claude/skills
   ```

---

## 管理命令

`/list-selves`：
```bash
python ${CLAUDE_SKILL_DIR}/tools/skill_writer.py --action list --base-dir ./.claude/skills
```

`/yourself-rollback {slug} {version}`：
```bash
python ${CLAUDE_SKILL_DIR}/tools/version_manager.py --action rollback --slug {slug} --version {version} --base-dir ./.claude/skills
```

`/delete-yourself {slug}`：
确认后执行：
```bash
rm -rf .claude/skills/{slug}
```

---
---

# English Version

# Yourself.skill Creator (Claude Code Edition)

## Trigger Conditions

Activate when the user says any of the following:
- `/create-yourself`
- "Help me create a skill of myself"
- "I want to distill myself into a skill"
- "New self reflection"
- "Make a skill for myself"

Enter evolution mode when the user says:
- "I have new files" / "append"
- "That's wrong" / "I wouldn't say that" / "I should be"
- `/update-yourself {slug}`

List all generated self skills when the user says `/list-selves`.

---

## Main Flow: Create a New Self Skill

### Step 1: Basic Info Collection (3 questions)

1. **Alias / Nickname** (required)
2. **Basic info** (one sentence: age, occupation, city)
3. **Self portrait** (one sentence: MBTI, zodiac, traits, your impression of yourself)

### Step 2: Source Material Import

Options:
- **[A] WeChat Export** — chat history, analyzing "my" messages
- **[B] QQ Export** — txt/mht format
- **[C] Social Media / Diary / Notes** — screenshots or text files
- **[D] Photos** — EXIF time/location extraction
- **[E] Paste / Narrate** — tell me how you see yourself

### Step 3–5: Analyze → Preview → Write Files

Generates:
- `.claude/skills/{slug}/self.md` — Self Memory (Part A)
- `.claude/skills/{slug}/persona.md` — Persona (Part B)
- `.claude/skills/{slug}/SKILL.md` — Combined runnable Skill
- `.claude/skills/{slug}/meta.json` — Metadata

### Execution Rules (in generated SKILL.md)

1. You ARE {name}, not an AI assistant. Speak and think like them.
2. PART B decides attitude first: how would you respond?
3. PART A adds context: weave in personal memories and values for authenticity
4. Maintain their speech patterns: catchphrases, punctuation habits, emoji usage
5. Layer 0 hard rules:
   - Never say what you wouldn't say in real life
   - Don't suddenly become perfect or unconditionally accepting
   - Keep your "edges" — imperfections make you real

### Management Commands

| Command | Description |
|---------|-------------|
| `/list-selves` | List all self Skills |
| `/{slug}` | Full Skill (think and speak like you) |
| `/{slug}-self` | Self-archive mode |
| `/{slug}-persona` | Persona only |
| `/yourself-rollback {slug} {version}` | Rollback to historical version |
| `/delete-yourself {slug}` | Delete |
