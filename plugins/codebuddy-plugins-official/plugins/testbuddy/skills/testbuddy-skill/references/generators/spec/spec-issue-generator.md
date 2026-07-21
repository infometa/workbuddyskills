---
name: spec-issue-analyst
description: >
  Spec工作流专用的需求分析规则。基于需求节点信息，深度分析需求要点并整理待澄清问题，
  输出结构化的需求分析文档（test_analysis.md），作为测试点设计的输入。
  Args:
      inputs: {
          issue_uid: # 需求节点的uid
          issue_kind: # STORY 或 BUG
          raw_issue: # 需求详情内容或文件路径
      }
---

## 目标

基于需求节点信息，深度理解业务功能，整理需求要点及待澄清问题，输出结构化的需求分析文档（`test_analysis.md`）。

## 核心工作流程（必须严格遵循）

1. **整理关键点及问题** - 整理需求要点及待澄清问题列表
2. **查询知识库**（如有） - 针对要点及问题，依次查询知识库，并整理结果
3. **输出结果** - 输出**分析结果**，格式必须参考`需求分析格式`

## 需求分析格式（必须为markdown，且必须带有```）

```sys_file
<File name="test_analysis.md" type="file" language="markdown">

## 原始需求
[原始需求详情]

## 需求要点
1. [要点详情1]
2. [要点详情2]

## 问题
1. [问题1]
[答案1]
2. [问题2]
[答案2]

</File>
```
