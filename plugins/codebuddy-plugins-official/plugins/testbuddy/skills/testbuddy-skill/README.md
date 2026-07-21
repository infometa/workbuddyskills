# testbuddy-skill

TestBuddy 测试设计技能包。

## 简介

本技能包提供测试设计相关的 AI 能力，包括：

- 生成测试框架 / 模块 / 场景 / 测试点 / 用例
- 根据 TAPD 需求或缺陷链接生成测试内容
- 根据任意文本（PRD / 接口文档 / 代码 / 表格 / 功能描述）生成测试用例
- 打开 / 跳转到脑图、测试设计、TestBuddy 页面
- 进行测试设计、需求分析、缺陷分析

## 目录结构

```
testbuddy-skill/
├── README.md               # 本文件
├── SKILL.md                # 技能主入口（意图识别 & 工作流调度）
├── references/
│   ├── tools/              # 工具使用文档
│   └── workflows/          # 工作流文档
└── scripts/                # 工具调用脚本
```

## 详细说明

请参阅 [SKILL.md](./SKILL.md) 了解完整的执行流程和工具能力说明。
