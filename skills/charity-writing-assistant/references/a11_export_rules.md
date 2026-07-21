# A11 导出说明（详细模板）

> 由 SKILL.md 的 `### A11: 导出` 引用。本文件提供 docx 导出策略的完整用户引导文案与禁止行为清单。

---

## 当前环境的工具能力限制

| 限制项 | 说明 |
|--------|------|
| Bash 工具 | 仅限 `playwright-cli:*`，**不支持** Python/Node.js/任意脚本 |
| 这意味着 | **无法通过脚本生成 docx 文件**（python-docx、docx 库等都不可用） |

## docx 导出策略

### 1. 首选方案（推荐用户使用）

输出以下完整文案：

```
🦞 当前环境不支持自动生成 .docx 文件，但 Markdown 转 Word 非常简单：

方案 1（最快，30 秒）：
① 复制下方 Markdown 文本
② 在 Word/WPS 中新建文档 → 直接粘贴
③ Word 会自动识别标题、列表、加粗等格式

方案 2（更精细）：
① 用 VS Code 安装 "Markdown All in One" 插件
② 右键文件 → "Export Markdown to Word"

现在为您输出格式化的 Markdown 文本：
[文书 Markdown 内容]
```

### 2. 严禁行为

- ❌ 尝试用 Bash 调用 Python/Node.js 生成 docx
- ❌ 尝试调用 python-docx、docx、mammoth 等库
- ❌ 反复尝试不同脚本方案（**1 次失败即停止**）
- ❌ 不告知用户限制就一直"准备中"

### 3. 降级阈值

任何尝试 docx 自动生成的方案，**单次失败即立即降级**到 Markdown，不允许重试。

### 4. 导出后引导

输出 Markdown 后，附目标平台操作指引（如何复制提交到腾讯公益、字节公益、支付宝公益等）。
