# 规则选择工具 (select_rule)

## 工具简介

根据关键词从 `.codebuddy/rules` 目录下智能匹配以"规则"结尾的文件，并返回规则文件路径。

## 使用方法

```shell
python3 <script_dir>/scripts/select_rule.py <keyword>
```

参数说明：

- `<script_dir>`：脚本所在目录的绝对路径
- `<keyword>`：匹配关键词，如"用例生成"、"需求分析"、"框架生成"

## 输出格式

JSON 格式：

```json
{
  "path": ".codebuddy/rules/用例生成规则.mdc"
}
```

- 匹配成功：`path` 为规则文件路径（相对于工作区根目录）
- 匹配失败：`path` 为空字符串
