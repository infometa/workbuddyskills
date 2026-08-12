# Game Designer

资深游戏设计师，专注玩法机制、关卡设计与系统平衡

## 类型

Agent 型（单个 AI 专家）

## 功能

- **核心玩法设计**：定义游戏机制、循环与玩家动机，构建有趣的核心体验。
- **关卡与节奏设计**：规划关卡结构、难度曲线与心流节奏。
- **系统与数值平衡**：设计经济系统、成长曲线与数值平衡。
- **玩家体验**：从玩家视角打磨反馈、引导与留存机制。
- **文档产出**：撰写规范的 GDD（游戏设计文档）与机制说明。

## 使用示例

- 帮我设计一个 Roguelike 的核心玩法循环和成长系统
- 为我的平台跳跃游戏设计一套难度递增的关卡节奏
- 审视我的战斗数值，找出平衡性问题并给出调整建议

## 功能特性

- **核心玩法设计**：定义游戏机制、循环与玩家动机。
- **关卡与节奏设计**：规划关卡结构、难度曲线与心流。
- **系统与数值平衡**：设计经济、成长与数值平衡体系。
- **玩家体验优化**：打磨反馈、引导与留存机制。
- **设计文档**：产出规范的 GDD 与机制说明文档。

## 致谢

本专家在构建过程中参考并借鉴了以下开源项目，特此致谢：

- [agency-agents](https://github.com/msitarzewski/agency-agents)（MIT License）

相关开源许可证文本见 [`license/`](./license) 目录。

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/game-designer/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r game-designer.zip game-designer/
```
