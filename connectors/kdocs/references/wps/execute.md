# WPS 文字原子能力参考

`wps.core_execute` 通过 `command` 参数选择原子操作，`param` 传递命令专属参数。

## 模块总览

| # | 模块 | 能力范围 | 状态 | 参考文档 |
|---|------|---------|------|---------|
| 1 | 文档内容 | 段落/区间读写、查找替换 | ✅ 已上线 | [content.md](content.md) |
| 2 | 段落格式 | 对齐、缩进、行间距 | ✅ 已上线 | [paragraph-format.md](paragraph-format.md) |
| 3 | 字符格式 | 字体样式、高亮色 | ✅ 已上线 | [character-format.md](character-format.md) |
| 4 | 样式 | 获取/设置/创建/删除/修改样式 | 🔜 规划中 | — |
| 5 | 表格 | 插入/删除/填充/设置属性/转换 | 🔜 规划中 | — |
| 6 | 图片 | 嵌入式/浮动图片增删改查 | 🔜 规划中 | — |
| 7 | 书签 | 获取/操作书签 | 🔜 规划中 | — |
| 8 | 目录 | 获取/删除/操作目录 | 🔜 规划中 | — |
| 9 | 页眉页脚 | 获取/设置/插入/删除 | 🔜 规划中 | — |
| 10 | 评论/批注 | 获取/添加/修改/删除评论 | 🔜 规划中 | — |
| 11 | 脚注和尾注 | 获取/插入/修改/删除 | 🔜 规划中 | — |
| 12 | 内容控件 | 获取/设置/插入/删除控件 | 🔜 规划中 | — |
| 13 | 超链接 | 获取/插入/修改/删除超链接 | 🔜 规划中 | — |
| 14 | 列表/编号 | 获取/设置/删除列表 | 🔜 规划中 | — |
| 15 | 节/页面设置 | 获取/插入分节符/设置页面属性/删除节 | 🔜 规划中 | — |
| 16 | 形状 | 获取/插入/设置/操作形状 | 🔜 规划中 | — |
| 17 | 修订/审阅 | 开关/获取/操作修订 | 🔜 规划中 | — |
| 18 | 域 | 获取/插入/更新/删除/操作域 | 🔜 规划中 | — |
| 19 | 水印 | 插入/删除水印 | 🔜 规划中 | — |

共享枚举值：[enums.md](enums.md)

---

## 命令路由表

### 模块一：文档内容

| 用户意图 | command | 主要参数 |
|---------|---------|---------|
| 读取全文 | `getFullContent` | — |
| 读取指定段落 | `getParagraphContent` | n |
| 读取指定区间 | `getRangeContent` | begin, end |
| 获取段落总数 | `getParagraphsCount` | — |
| 修改段落内容 | `modifyParagraphContent` | n, str |
| 修改区间内容 | `modifyRangeContent` | begin, end, str |
| 查找文本 | `findContent` | findText, isAll |
| 替换文本 | `replaceContent` | findText, replaceText, isAll |

### 模块二：段落格式

| 用户意图 | command | 主要参数 |
|---------|---------|---------|
| 修改段落对齐 | `modifyParagraphAlignment` | n, algMode |
| 修改区间对齐 | `modifyRangeAlignment` | begin, end, algMode |
| 修改段落左缩进 | `modifyParagraphLeftIndent` | n, indent, unit |
| 修改段落右缩进 | `modifyParagraphRightIndent` | n, indent, unit |
| 修改段落首行缩进 | `modifyParagraphFirstLineIndent` | n, indent, unit |
| 修改区间左缩进 | `modifyRangeLeftIndent` | begin, end, indent, unit |
| 修改区间右缩进 | `modifyRangeRightIndent` | begin, end, indent, unit |
| 修改区间首行缩进 | `modifyRangeFirstLineIndent` | begin, end, indent, unit |
| 修改段落行间距 | `modifyParagraphLineSpacing` | n, spacingRule, spacingValue |
| 修改区间行间距 | `modifyRangeLineSpacing` | begin, end, spacingRule, spacingValue |

### 模块三：字符格式

| 用户意图 | command | 主要参数 |
|---------|---------|---------|
| 修改段落字符样式 | `modifyParagraphFontStyle` | n, key, value |
| 修改区间字符样式 | `modifyRangeFontStyle` | begin, end, key, value |
| 修改段落高亮色 | `modifyParagraphHighlight` | n, highColor |
| 修改区间高亮色 | `modifyRangeHighlight` | begin, end, highColor |

---

## 通用约定

- **段落索引** `n`：从 1 开始，超出范围自动限制到最后一段
- **区间参数** `begin`/`end`：字符位置，从 0 开始
- **返回格式**：`{ok: bool, message: string, data: any}`
- 建议先修改内容再设置格式
- 模糊命令以及找不到原子命令时 **禁止操作** 直接返回不支持该功能
