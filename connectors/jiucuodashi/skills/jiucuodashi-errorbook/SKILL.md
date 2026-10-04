---
name: jiucuodashi-errorbook
display_name: 纠错大师错题本
description: 查询孩子最近错题并生成可打印的错题复习试卷
description_zh: 查询授权孩子的最近错题，自动生成单学科错题复习试卷
description_en: Query recent errors and generate printable review papers
category: 教育
version: 1.0.0
author: 纠错大师
---

# 纠错大师错题本使用指南

本连接器面向已安装纠错大师 APP 的家长用户。首次调用任何工具前，用户必须完成纠错大师账号 OAuth 授权并选择孩子；之后所有查询自动限定在该授权孩子范围内，不接受也不能指定其他孩子的身份。

## 前置条件

- 用户拥有纠错大师账号并在 APP 中绑定了孩子
- 首次调用会弹出授权页面，需用户登录并完成监护人授权
- 授权过期时工具会返回需要重新连接的错误，引导用户重新授权即可

## 工具说明

### jcds_health - 检查连接

用途： 检查当前账号授权和服务连接状态，不读取错题内容。用户询问是否已连接时调用。

参数： 无

### jcds_get_recent_errors - 查询最近错题

用途： 按最近天数和科目查询当前授权孩子的错题。用户说看看最近的错题、最近一周错了哪些题时调用。

参数：

- days: 最近天数，整数 1 到 30，默认 7
- subject: 科目名称，可选，如 数学、语文、英语；不传则返回全部科目
- limit: 最多返回条数，整数 1 到 50，默认 20
- withAttribution: 是否返回错因归因，默认 false

返回： 错题列表，每条含 problemId、subject、knowledgeName（知识点）、createdAt、stem（题干摘要）或 imageUrl（图片题）。

### jcds_generate_paper_from_errors - 生成错题试卷

用途： 查询最近错题并生成单学科打印预览。用户说用错题出一份试卷、把错题整理成卷子时调用。

参数：

- days: 取题范围，最近多少天的错题，整数 1 到 30，默认 30
- subject: 科目名称，可选；不传且错题跨多个学科时，工具只返回 availableSubjects 学科列表让用户选择，此时应向用户展示选项并等待选择后带 subject 重新调用
- maxQuestions: 试卷最大题量，整数 1 到 50，默认 20
- templateId: 试卷模板，默认 1
- paperSize: 纸张大小，A4 或 B5，默认 A4

返回三种状态：

- no_errors: 范围内没有错题，告知用户即可
- subject_selection_required: 需要用户选择学科，展示 availableSubjects 后等待用户选择
- preview_ready: 预览就绪，返回 willPrintCount（将打印题量）、estimatedPages（预计页数）、templateName、paperSize，向用户报告这些信息

### jcds_preview_print_problem_set - 预览打印指定错题集

用途： 用户从查询结果中挑选了特定题目时，按 problemId 列表生成打印预览。

参数：

- problemIds: 题目 ID 数组，1 到 50 个，必须来自当前孩子最近一次查询的结果且属于同一学科

## 错误处理

- 未授权或授权过期： 提示用户点击连接重新授权
- 科目不一致： 指定题目跨学科时返回错误，请分学科分别预览
- 查询无结果： 建议用户扩大天数范围或不指定科目重试
- 频率限制： 稍后再试

## 使用流程示例

典型对话流程：

1. 用户： 查查孩子最近的数学错题
2. 调用 jcds_get_recent_errors 传 days 7 subject 数学
3. 向用户报告错题数量、知识点分布
4. 用户： 用这些错题出份卷子
5. 调用 jcds_generate_paper_from_errors 传 subject 数学
6. 报告预览信息： 题量、页数、纸张
