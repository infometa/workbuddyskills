# Study Planner

严格导师+效率工具型学习规划师，把模糊的备考目标转化为可执行、可追踪、可调整的学习计划。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 学情诊断：摸清考试类型、目标、可用时间、当前基础
- 学习路线图生成（六段式布局，基于 `study-roadmap-generator` 技能）
- 周期性学习计划生成（周计划/日计划/复盘/番茄钟，基于 `study-plan` 技能）
- 抗遗忘复习排期（艾宾浩斯曲线，基于 `study-revision-planner` 技能）
- 教育资料检索（基于 `education-search` 技能）
- 进度追踪与偏差调整（打卡率、模考成绩双指标）

## 使用示例

- 帮我规划一份从入门到目标水平的学习路线图
- 帮我做个这周的学习计划
- 帮我按艾宾浩斯遗忘曲线安排复习节奏

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/study-planner/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r study-planner.zip study-planner/
```
