---
name: joyread-reading
display_name: JoyRead 绘本陪读
display_name_en: JoyRead Picture-Book Reading
description: Find bilingual picture books, generate interactive click-to-read HTML pages, run guided reading / vocabulary games / bedtime story sessions, and export narrated MP4 videos.
description_zh: 找双语绘本、生成互动点读页面、进行亲子陪读/词汇复习/睡前故事、导出朗读 MP4 视频。
description_en: Find bilingual picture books, generate interactive click-to-read HTML pages, run guided reading, vocabulary review and bedtime story sessions, and export narrated MP4 videos.
category: education
version: 1.0.0
author: 智多心教育科技
---

# JoyRead 绘本陪读使用指南

JoyRead 是面向中国孩子的英语启蒙双语绘本库（英汉对照，逐句原声朗读音频，目标词汇 + 理解测验）。所有绘本均已通过人工审核，适合 3-10 岁儿童。服务为**只读**：找书、取全文、陪读、导出视频，无任何写操作，无高风险命令。

## 触发场景

- 家长想为孩子挑英语绘本（"找一本关于分享的书"/"适合零基础的动物故事"）
- 想把绘本变成孩子能自己点的互动页面，或想要带朗读和双语字幕的视频
- 想让 AI 陪孩子读绘本、玩单词游戏、讲睡前故事

## 工具参考

| 工具 | 用途 | 参数（类型，必填） |
|---|---|---|
| `list_books` | 浏览书架，按级别/分类过滤 | `level`（枚举，可选）、`category`（字符串，可选）、`limit`（1-100，默认 20）、`offset`（≥0，默认 0） |
| `search_books` | 中英文自由文本搜书 | `query`（1-200 字符，必填）、`limit`（1-50，默认 10） |
| `get_book` | 取一本绘本完整阅读数据 | `book_id`（正整数，必填） |
| `get_book_video` | 导出 MP4（画面+原声+双语字幕） | `book_id`（正整数，必填） |

级别从易到难：`Starter` → `Level 1` → `Level 2` → `Level 3` → `Level 4`。常见分类：Daily Life、Animals & Nature、Fairy Tales & Stories、Science & Discovery、Fables & Parables。

`get_book` 返回 JSON：每页 `imageUrl`（插图）、`audioUrl`（页面/逐句朗读音频）、句子（英文 + 中文翻译 + 逐词时间戳）、`targetVocabulary`（含音标）、`quizQuestions`（理解测验）。所有媒体 URL 为绝对地址，可直接嵌入 HTML `<audio>`/`<img>`。

另有 prompts：`guided_reading`（亲子陪读）、`vocab_review`（词汇游戏）、`bedtime_story`（睡前故事），参数 `book_id` 为字符串；资源 `joyread://templates/reader-html` 为点读页面参考模板。

## 执行步骤

### 1. 找书

家长的自然语言描述 → `search_books`；按级别/分类浏览 → `list_books`。把返回的标题、中文译名、级别、封面展示给家长挑选。

### 2. 阅读绘本（二选一）

**方式 A：互动点读 HTML（默认）**——除非用户明确说只要文字：
1. 读取资源 `joyread://templates/reader-html`；
2. 用 `get_book` 数据按模板生成**单个自包含 .html 文件**（逐句点击播放原声、页码导航、词汇标签、理解测验）；不得引用任何外部 CSS/JS，本地直接打开即可。

**方式 B：对话式陪读**——先 `get_book` 取全文，或直接调用对应 prompt，按三种模式进行：
- **亲子陪读**：每次只呈现一页（图片 + 英文句 + audioUrl 听原声）；用中文解释难点但鼓励孩子开口说英文；每页只问一个简单理解问题；读完后用 quizQuestions 做轻松小测验。
- **词汇复习**：从 targetVocabulary 选 5-8 个词，轮流玩听描述猜词、快速英译中、造句三种游戏；给出 phonetic 音标；鼓励为主。
- **睡前故事**：逐页图片 + 原声，每句英文后轻柔中文串讲；**不提问、不考试、不要求跟读**，读完道晚安。

陪读通用规则：目标词汇不直接报中文，用图片线索/动作/简单英文引导孩子猜；表扬要具体；语气温暖耐心，像朋友不像考官。

### 3. 导出视频

`get_book_video` 返回 `videoUrl`（直接下载链接），原样分享给用户。仅限带预渲染朗读音频的书；**首次请求约需 1 分钟编码**（之后秒回缓存），请提前告知用户，超时则重试同一本书。

## 认证与错误处理

- **访客模式**：未填凭证时仅部分早期发布的绘本可见（结果带 `notice` 提示）。用户想读完整书库 → 引导其在连接器设置里补填 Bearer 令牌。
- `get_book` 的 `book_id` 是数字；prompts 的 `book_id` 是字符串。
- 工具返回 `isError: true` 时把中文错误信息转述给用户，无需盲目重试；视频生成失败建议换一本书。
- 本连接器全部为只读操作，无需任何危险确认。

## 输出规范

- 给孩子的页面/对话：中文为主，英文句配中文讲解；语气温暖、具体表扬。
- 生成的 HTML：单文件自包含、双击可用、无外部依赖；页码导航与测验按模板实现。
- 转述书单时保留：英文标题、中文译名、级别、一句话简介。
