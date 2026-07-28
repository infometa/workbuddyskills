# docx-js 编码防错清单

生成 .docx 文件时必须逐条检查。

## 1. Bullet 列表文本类型

❌ **错误写法**（TextRun 收到数组，内容为空白）:
```js
[
  ["第一条要点"],
  ["第二条要点"]
].map((text) => new Paragraph({
  numbering: { reference: "bullet-main", level: 0 },
  children: [new TextRun({ text: text, font: "Microsoft YaHei" })]
}))
```

✅ **正确写法**（TextRun 收到字符串）:
```js
[
  "第一条要点",
  "第二条要点"
].map((text) => new Paragraph({
  numbering: { reference: "bullet-main", level: 0 },
  children: [new TextRun({ text: text, font: "Microsoft YaHei" })]
}))
```

## 2. 表格列数一致性

所有表格的每一行必须有相同的列数。表头有几列，数据行就有几列。

❌ **错误**（前两行缺列）:
```js
buildTimelineTable([
  ["2025年1月", "特定对象调研", "沟通内容"],   // 只有3列！
  ["2025年2月", "特定对象调研", "沟通内容"],   // 只有3列！
  ["1", "2025年3月", "特定对象调研", "沟通内容"]  // 4列！
])
```

✅ **正确**（用占位符补齐）:
```js
buildTimelineTable([
  ["—", "2025年1月", "特定对象调研", "沟通内容"],
  ["—", "2025年2月", "特定对象调研", "沟通内容"],
  ["1", "2025年3月", "特定对象调研", "沟通内容"]
])
```

## 3. 生成后验证

每次生成 docx 后，运行:
```bash
python3 scripts/validate_docx.py <生成的docx文件路径>
```

验证脚本会检查：
- 所有表格列数一致
- 关键章节（7.2、8.1、8.2）的 bullet 段落不为空
- 封面、目录、免责声明等结构元素存在

## 4. 中文字体

为所有含中文的 TextRun 设置 `font: "Microsoft YaHei"`。
表格单元格中的文本用 `line.split("\n")` 处理可能的多行。
