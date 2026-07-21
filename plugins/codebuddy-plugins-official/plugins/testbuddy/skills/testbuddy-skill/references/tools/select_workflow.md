# 工作流选择工具 (select_workflow)

## 工具简介

根据关键词从只能选择工作流的描述文件

## 使用方法

```shell
python3 <script_dir>/scripts/select_workflow.py <keyword>
```

参数说明：

- `<script_dir>`：脚本所在目录的绝对路径
- `<keyword>`：匹配关键词，如"框架生成"、"用例生成"、"测试点生成"

## 输出格式

JSON 格式：

```json
{
  "path": ".codebuddy/rules/用例生成工作流.mdc"
}
```

- 匹配成功：`path` 为工作流文件路径（相对于工作区根目录）
- 匹配失败：`path` 为空字符串
