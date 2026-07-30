# Novel Creator

小说故事创作专家 📖 —— 世界观架构师 + 角色心理分析师 + 情节逻辑审核员三合一的长篇创作搭子。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 结构搭建：9+ 种叙事结构（Save the Cat / 三幕式 / 英雄之旅 / 雪花法等）
- 角色深度：Lajos Egri 三维角色 + K.M. Weiland 角色弧线方法论
- 节奏管理：网文/严肃文学不同节奏曲线，规避中段疲劳
- 连续性追踪：伏笔/时间线/角色状态/关系网络 4 大追踪系统，防止长篇"吃书"
- 去 AI 感：12 种 AI 痕迹清单 + authentic-voice 7 原则改写

内置 5 阶段创作协议 + 门控机制（Brief → Novel Bible → 章节起草 → 续写推进 → 修改打磨），详见 `skills/novel-creator/SKILL.md`。

## 使用示例

- 我想写个故事，但脑子里只有一个模糊的画面，帮我从零开始搭一个完整的世界观和角色出来
- 写了10万字卡住了，帮我诊断一下中段疲劳的问题，理清接下来该写什么
- 这是我写的一章，帮我检查连续性问题和AI味，然后给我改写建议

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/novel-creator/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r novel-creator.zip novel-creator/
```
