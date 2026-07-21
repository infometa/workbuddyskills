# 模块一：文档内容

读取、修改文档内容以及查找替换功能。

---

## 读取命令

### getFullContent — 读取全文

无需 param。

```json
{"id": "file_xxx", "command": "getFullContent"}
```

返回示例：`{"ok": true, "message": "success", "data": "文档全文内容..."}`

### getParagraphContent — 读取指定段落

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引，从 1 开始 |

```json
{"id": "file_xxx", "command": "getParagraphContent", "param": {"n": 3}}
```

### getRangeContent — 读取指定区间

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置（字符索引，从 0 开始） |
| end | uint32 | 是 | 结束位置 |

```json
{"id": "file_xxx", "command": "getRangeContent", "param": {"begin": 0, "end": 100}}
```

### getParagraphsCount — 获取段落总数

无需 param。

```json
{"id": "file_xxx", "command": "getParagraphsCount"}
```

返回示例：`{"ok": true, "message": "success", "data": 15}`

---

## 修改命令

### modifyParagraphContent — 修改指定段落内容

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| n | uint32 | 是 | 段落索引 |
| str | string | 是 | 新内容，最大 10000 字符 |

```json
{"id": "file_xxx", "command": "modifyParagraphContent", "param": {"n": 1, "str": "新段落内容"}}
```

### modifyRangeContent — 修改指定区间内容

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| begin | uint32 | 是 | 开始位置 |
| end | uint32 | 是 | 结束位置 |
| str | string | 是 | 新内容，最大 10000 字符 |

```json
{"id": "file_xxx", "command": "modifyRangeContent", "param": {"begin": 10, "end": 50, "str": "替换文本"}}
```

超出文档末尾时自动在末尾插入新段落。

---

## 查找替换

### findContent — 查找内容

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| findText | string | 是 | 要查找的文本 |
| isAll | bool | 否 | 是否查找全部，默认 false（只找第一个） |

```json
{"id": "file_xxx", "command": "findContent", "param": {"findText": "关键词"}}
```

```json
{"id": "file_xxx", "command": "findContent", "param": {"findText": "关键词", "isAll": true}}
```

- `isAll=false`：返回 `{begin, end}` 或未找到时 `ok=false`
- `isAll=true`：返回 `[{begin, end}, ...]` 数组，未找到时 `ok=false`

### replaceContent — 替换内容

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| findText | string | 是 | 查找内容 |
| replaceText | string | 是 | 替换内容 |
| isAll | bool | 否 | 是否全部替换，默认 true |

```json
{"id": "file_xxx", "command": "replaceContent", "param": {"findText": "旧词", "replaceText": "新词"}}
```

```json
{"id": "file_xxx", "command": "replaceContent", "param": {"findText": "旧词", "replaceText": "新词", "isAll": false}}
```
