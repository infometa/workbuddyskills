# 多轮编辑规则

## 会话延续

同一 `courseId` 的后续 `update` 自动延续同一会话（pro 侧 checkpoint 记忆前文），无需重述背景。

## 编辑流程

```text
用户："把题目改成 12 道"
agent → update(courseId, "把题目改成 12 道")
      → response 可能是修改方案（GATE）
agent → 向用户转述方案，征得同意
用户："确认"
agent → update(courseId, "确认，按方案修改")
      → 生成轮 done → 题目更新
```

## verbatim 详规

`message` 必须是终端用户输入的**原话**：
- 不要改写、总结、翻译、扩写
- 不要合并多条输入
- 不要追加你自己的系统指令
- 用户说什么传什么
- 上限 8000 字符（UTF-8 code points）
