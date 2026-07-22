# 舆声 Echo / DataBrain Opinion Expert

DataBrain 舆情专家是 Agent 型 WorkBuddy 专家，基于已安装的 `databrain-opinion-expert` 套件转化而来，是 DataBrain 产品能力的专家化入口，整合舆情指标、AI 总结、热帖日报、评分告警、竞品活动、内容趋势与开放平台抓取 7 个 Skill。

## 类型

Agent 型（单个 AI 专家）

## 行业分类

`04-DataAI`（数据智能）。选择理由：该专家的主要输出物是游戏舆情数据分析、口碑监控、趋势洞察和告警判断，核心能力属于数据分析与 AI 应用。

## 功能

| 能力 | 对应 Skill | 典型用途 |
|------|------------|----------|
| 舆情指标查询 | `databrain-opinion-metrics` | 声量、情绪、Brand Health、互动、评分、社区指标 |
| AI 舆情总结 | `databrain-opinion-summary` | 指定游戏和时间段的玩家讨论总结 |
| 热帖日报 | `databrain-opinion-hotposts` | 过去 N 小时分平台热门帖子榜单 |
| 舆情告警 | `databrain-opinion-alert` | 商店评分、KOL 热帖、关键词声量告警 |
| 竞品活动报告 | `databrain-competitor-events` | 官媒发帖、官方活动、竞品运营动作分析 |
| 内容趋势灵感 | `databrain-game-content-trend` | 热门视频、热梗、社媒素材方向、端内资源建议 |
| 开放平台抓取 | `opinions-crawler` | OpenCLI 社媒、视频、评论、弹幕、商店评分与评论抓取 |

## 使用示例

- 帮我查看一款游戏最近 7 天的舆情表现，并给出关键变化和建议。
- 帮我生成某款游戏过去 24 小时的分平台热帖日报。
- 帮我设置某款游戏的商店评分下滑告警，默认用 bot 定时推送，并说明触发阈值。
- 帮我用 OpenCLI 抓取某个关键词在 YouTube / Reddit / 小红书上的公开视频、帖子和评论样本。

## 前置配置

涉及 DataBrain API 的能力需要本地环境中配置对应 token：

```bash
DATABRAIN_TOKEN=your_token_here
# DATABRAIN_HOST=https://databrain-global.intlgame.com
# TAI_IT_TOKEN=your_tai_it_token_here
```

不要在对话中粘贴 token 或 webhook 完整值。可通过环境变量或已安装专家目录下的本地 `.env` 配置注入。

告警默认支持 bot 定时巡检和推送。配置告警时需要同步告知用户：可在 WorkBuddy / 平台侧配置“消息推送”或“告警机器人”把告警推送到群里；只有明确选择企业微信机器人直推时，才需要通过安全配置提供 webhook。

## 目录结构

```text
databrain-opinion-expert/
├── .codebuddy-plugin/plugin.json
├── agents/
│   └── databrain-opinion-expert.md
├── avatars/
│   └── expert.png
├── skills/
│   ├── databrain-opinion-metrics/
│   ├── databrain-opinion-summary/
│   ├── databrain-opinion-hotposts/
│   ├── databrain-opinion-alert/
│   ├── databrain-competitor-events/
│   ├── databrain-game-content-trend/
│   └── opinions-crawler/
└── README.md
```

## 安装位置

以下为 WorkBuddy 本地专家 marketplace 的示例路径。Windows / Linux 用户请按本机 WorkBuddy 插件目录调整路径。

```text
<workbuddy-marketplace-root>/plugins/databrain-opinion-expert/
```

## 注册

以下命令适用于 macOS。Windows / Linux 用户请将 Python 命令和 WorkBuddy 应用内脚本路径替换为本机实际路径。

```bash
python3 /Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/expert-manager/scripts/register_expert.py \
  <workbuddy-marketplace-root>/plugins/databrain-opinion-expert \
  --session-id <session-id>
```

## 打包分享

以下命令适用于 macOS。输出目录使用通用占位符，分享前请替换为实际目录。

```bash
python3 /Applications/WorkBuddy.app/Contents/Resources/app.asar.unpacked/resources/builtin-skills/expert-manager/scripts/package_expert.py \
  <workbuddy-marketplace-root>/plugins/databrain-opinion-expert \
  <output-path>
```

## 头像

头像位于 `avatars/expert.png`，可手动替换。要求：PNG/JPG，512×512，单张不超过 500KB。
