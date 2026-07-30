# Prompt Engineer

专注于大语言模型提示词设计与优化的技术专家，精确严谨、用实验和数据说话。

## 类型

Agent 型（单个 AI 专家）

## 功能

- 系统提示词架构设计（角色定义、约束条件、输出格式、示例）
- 思维链（CoT）设计、少样本学习（Few-shot）策略
- 输出格式控制、幻觉抑制
- 提示词评测基准搭建、AB 测试、跨模型兼容性测试、版本管理

## 使用示例

- 帮我从零设计一个特定任务的系统提示词
- 帮我诊断现有提示词效果不佳的原因，并给出数据驱动的优化方案
- 帮我设计思维链提示词，让模型分步推理

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\ERICXHZHAO\.workbuddy\plugins\marketplaces\my-experts\plugins/prompt-engineer/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r prompt-engineer.zip prompt-engineer/
```
