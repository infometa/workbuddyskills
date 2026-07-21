# TestBuddy 插件技能包 安装指南

## 简介

`testbuddy-ext-skill` 是 TestBuddy 插件的技能包，为 Agent 提供以下能力：

1. **记录用例代码关联关系** — 生成用例代码后，记录代码路径与用例节点的映射关系，实现双向导航

## 前置条件

- Python 3.x

## 目录结构

```
testbuddy-ext/
├── SKILL.md                          # 技能包定义文件
├── README.md                         # 本文件
├── scripts/
│   └── record_code_case_relation.py    # 保存代码-用例关联关系脚本
└── tools/
    └── record_code_case_relation.md     # "生成关联关系"工具说明
```

## 使用指南

1. 在CodeBuddy中安装技能包
2. 在TestBuddy插件中，点击生成用例代码按钮，即可使用本技能包中提供的工具，对接生成用例代码的Agent
