# 文档类型与大纲规范

写入文档前，先确定文档类型，按对应大纲组织内容。

---

## 类型一：推广文案型

**适用场景**: 功能推广、工具介绍、方案宣传

```
1. [callout:primary] 一句话核心价值
2. [h2] 你是否遇到这些问题？
   - [bulleted_list] 痛点场景
3. [divider]
4. [h2] 解决方案
   - [callout:tip] 核心能力
   - [numbered_list] 功能列表
5. [divider]
6. [h2] 对比效果
   - [table] 传统方式 vs 新方案
7. [divider]
8. [h2] 快速上手
   - [h3] 步骤一
   - [code] 配置代码
9. [divider]
10. [h2] 最佳实践
    - [numbered_list] 实践建议
11. [divider]
12. [callout:success] 总结 + 行动召唤
```

---

## 类型二：技术文档型

**适用场景**: API 文档、开发指南、技术规范

```
1. [h1] 文档标题
2. [h2] 概述
   - [p] 功能描述
   - [callout:tip] 适用场景
3. [h2] 快速开始
   - [code] 最小示例
4. [h2] 详细说明
   - [h3] 参数说明
     - [table] 参数名 | 类型 | 必填 | 说明
   - [h3] 返回值
     - [code] 返回结构
5. [h2] 示例
6. [h2] 注意事项
   - [callout:warning] 重要提醒
```

---

## 类型三：操作指南型

**适用场景**: 使用教程、操作手册、配置指南

```
1. [callout:primary] 本指南帮你实现 XXX
2. [h2] 前置准备
   - [bulleted_list] 环境要求
   - [callout:warning] 注意事项
3. [h2] 操作步骤
   - [h3] 步骤 1：XXX
     - [numbered_list] 详细操作
     - [code] 命令/代码
     - [callout:tip] 小技巧
4. [h2] 验证结果
5. [h2] 常见问题
6. [callout:success] 完成确认
```

---

## Callout 语义映射

| 关键词模式 | Callout 类型 | 配色 |
|-----------|-------------|------|
| 核心/重要/价值 | primary | #E3F2FD |
| 提示/建议/tips | tip | #FFF3E0 |
| 成功/完成/搞定 | success | #E8F5E9 |
| 警告/注意/风险 | warning | #FFF8E1 |
| 错误/禁止/危险 | error | #FFEBEE |
