# Skill: content-creation-expert-prod（生产版内容创作工具）

## 描述

汽车图文创作团队的配套工具 Skill，提供**文章质量验证**、**通用 Markdown → HTML 渲染**和**小红书风格 HTML 渲染**三个核心能力。

> **⚠️ 生产版说明**：本 Skill 是精简版，只保留 `validate-article`、`render-html` 和 `render-html-xhs` 三个 action。
> 配图由 visual-director Agent 通过 WorkBuddy 内置 ImageGen 完成，不需要 Python 脚本调用。

## 触发条件

| 用户意图 | action | 说明 |
|:---|:---|:---|
| 质检/验证文章质量 | `validate-article` | 程序化检查文章（字数/链接/结构） |
| 渲染通用文章 HTML | `render-html` | Markdown → 通用单栏文章 HTML + COS 可选上传，适合公众号/懂车帝/知乎 |
| 渲染小红书风格 HTML | `render-html-xhs` | Markdown → 小红书 PC 端双栏 UI（左图轮播 + 右文 + 评论 + 互动栏），适合小红书图文 |

## 调用方式

```bash
python3 scripts/main.py '<JSON参数>'
```

## Action 参数说明

### 1. validate-article — 文章质量验证

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| action | string | 是 | - | 固定为 `"validate-article"` |
| article_text | string | 是 | - | 待检文章全文（Markdown） |
| brief_file | string | 否 | "" | Creative Brief 文件路径 |
| phase | string | 否 | "pre-delivery" | 阶段：`"pre-illustrate"` / `"pre-delivery"` |
| min_links | number | 否 | 3 | 最少超链接数 |
| min_words | number | 否 | 800 | 最少字数 |
| max_words | number | 否 | 5000 | 最大字数 |
| expected_images | number | 否 | - | 预期配图数 |

**输出**：
```json
{
  "status": "pass|fail",
  "score": 85,
  "fail_count": 0,
  "warn_count": 2,
  "issues": [{"severity": "FAIL|WARN", "category": "...", "detail": "..."}],
  "stats": {"word_count": 1500, "valid_links": 4, "actual_images": 6}
}
```

### 2. render-html — Markdown → HTML 渲染

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| action | string | 是 | - | 固定为 `"render-html"` |
| article_text | string | 是 | - | 图文混排 MD（图片已替换为 URL） |
| title | string | 否 | 自动提取 | 文章标题 |
| output_dir | string | 否 | 当前目录 | 本地保存目录 |

**输出**：
```json
{
  "status": "success",
  "html_content": "<html>...</html>",
  "html_local_path": "/abs/path/preview.html",
  "md_local_path": "/abs/path/article.md"
}
```

**图片处理双模式（自动选择）**：
- **有 COS 配置**：图片上传到 COS 获取公网 URL，替换 MD/HTML 中的图片路径
- **无 COS 配置**：图片（远程 URL + 本地路径）base64 内嵌到 HTML，MD 保留原路径

### 3. render-html-xhs — 小红书风格 HTML 渲染

将图文混排 Markdown 渲染为**小红书 PC 端双栏 UI**：
- 左侧：图片轮播（黑底 + contain + 浮动圆点指示 + N/M 计数 + 翻页箭头 + 键盘左右翻页）
- 右侧：作者栏（关注按钮）→ 标题 + 一句话定位 → 正文 → tag 蓝字 → 时间地点 → 评论区（含作者回复气泡）→ THE END
- 底部：固定互动栏（♡ ⭐ 💬 ↗）

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|:---|:---|:---|:---|:---|
| action | string | 是 | - | 固定为 `"render-html-xhs"` |
| article_text | string | 是 | - | 图文混排 MD（图片已替换为 URL/本地路径） |
| title | string | 否 | 自动提取 | 文章标题 |
| output_dir | string | 否 | 当前目录 | 本地保存目录 |
| author_name | string | 否 | "图文创作者" | 作者栏名称 |
| author_tag | string | 否 | "小红书博主 · 已认证" | 作者栏副标 |
| author_emoji | string | 否 | "✨" | 作者头像 emoji |
| post_time_loc | string | 否 | "刚刚 北京" | 发布时间地点 |
| likes | string | 否 | "2.3w" | 点赞数（可带 w 等单位） |
| collects | string | 否 | "1.8w" | 收藏数 |
| comments | array | 否 | 默认伪数据 | 评论列表，元素 `{avatar_emoji,name,time,content,likes,reply_count,author_reply?}` |

**输出**：
```json
{
  "status": "success",
  "platform": "xiaohongshu",
  "html_content": "<html>...</html>",
  "html_local_path": "/abs/path/preview.html",
  "md_local_path": "/abs/path/article.md",
  "image_count": 8
}
```

**关键 UI 特征**（小红书原生对齐）：
- 卡片宽度固定 1040px（左 520 + 右 520），高度 `calc(100vh - 48px)` 最大 920px
- 左侧图片 `object-fit:contain` 黑底显示主体完整，不裁切
- 圆点指示器漂浮在图片底部，激活态变红色胶囊
- 右上角带 `N/M` 计数胶囊
- 正文**无水平分隔线**（小红书原文无 `---` 样式），段落间靠 h2 margin 提供视觉分隔
- 正文**无引用样式**（`> quote` 渲染为正常段落，不加黄底框）
- 底部互动栏紧贴右侧内容底部（不会与正文重叠）
- 响应式：< 960px 自动变上下堆叠

**图片处理**：仅做 base64 内嵌（不走 COS），适合截图发布 / 离线预览。

## COS 可选配置

COS 是**可选**功能，用于上传图片获取公网 URL。

**判断逻辑**：检查环境变量 `COS_SECRET_ID`（或 `TENCENT_SECRET_ID`）是否存在。

### 有 COS 配置时
- `render-html` 自动将文章中的图片（远程 URL 下载 + 本地文件读取）上传到 COS，获取公网 URL 替换到 MD/HTML 中
- 图片以公网 URL 方式引用，适合在线分享

### 无 COS 配置时
- `render-html` 将图片 base64 内嵌到 HTML（使 HTML 文件完全自包含，离线可看），MD 保留原路径
- 适合本地预览和通过 WorkBuddy 原生分享

## 凭据配置

在 skill 目录创建 `.env` 文件（参考 `.env.example`）：

```env
# COS 凭据（可选，不填则只保存本地产物）
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=int-ai-1325126984
COS_REGION=ap-guangzhou
COS_PATH_PREFIX=expert-playground
```

## 使用示例

### 示例 1：配图前预检（只检查文字）
```bash
python3 scripts/main.py '{"action":"validate-article","article_text":"# 标题\n\n正文...","phase":"pre-illustrate","min_links":3}'
```

### 示例 2：交付前预检
```bash
python3 scripts/main.py '{"action":"validate-article","article_text":"# 标题\n\n正文...","brief_file":"/abs/brief.md","phase":"pre-delivery"}'
```

### 示例 3：渲染通用 HTML + 图片处理（COS 自动检测）
```bash
python3 scripts/main.py '{"action":"render-html","article_text":"# 标题\n\n![图1](https://img.url)\n\n正文...","title":"比亚迪汉EV评测","output_dir":"/abs/team-artifacts"}'
```

### 示例 4：渲染小红书风格 HTML
```bash
python3 scripts/main.py '{"action":"render-html-xhs","article_text":"# 标题\n\n> 一句话定位\n\n正文...\n\n![](/abs/img.png)\n\n#tag1 #tag2","title":"20万纯电SUV推荐","output_dir":"/abs/team-artifacts","author_name":"汽车博主","post_time_loc":"06-18 北京","likes":"2.3w","collects":"1.8w"}'
```

## HTML 产物特性

- 移动端优先响应式布局
- 支持暗色模式
- 图片 base64 内嵌（离线可看）
- 单文件无外部依赖
- AI 标注自动识别渲染

## Skill 包文件结构

```
content-creation-expert-prod/
├── SKILL.md                    # 本文件
├── .env.example                # COS 凭据模板（可选）
├── .gitignore
├── requirements.txt            # Python 依赖
├── references/
│   └── image-generation-guide.md  # AI 图片生成完整指南（7种场景策略）
├── templates/
│   └── article.html            # Jinja2 HTML 模板
└── scripts/
    ├── main.py                 # 路由入口
    ├── config.py               # 配置加载器
    ├── cos_client.py           # COS 客户端（图片上传）
    ├── html_renderer.py        # HTML 渲染器（含 base64 图片内嵌）
    ├── html_renderer_xhs.py    # 小红书 HTML 渲染器
    ├── utils.py                # 公共工具
    └── handlers/
        ├── validate_article.py # 质量验证
        ├── render_html.py      # HTML 渲染 + 图片双模式处理
        └── render_html_xhs.py  # 小红书风格 HTML 渲染
```
