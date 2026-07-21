---
name: review-to-word
description: 把患教内容六维度审核结果（issues.json）标注回原文 .docx——对问题句高亮并挂 Word 原生批注（右侧批注气泡），文末追加审核结论表与明细清单。当审核助手完成六维度审核、需要输出可在 Word/WPS 直接查看和采纳修改的带批注文档时使用。
---

# 审核意见转 Word 批注（review-to-word）

本技能提供 `scripts/review_to_word.py`，将审核意见直接标注回待审文章的 .docx 原文，产出一份带高亮 + Word 原生批注 + 文末结论表的 .docx，让用户像收到人工审稿一样在 Word / WPS 中直接查看与采纳修改。

## 何时使用

审核助手完成六维度审核后，把每一条问题整理成结构化 `issues.json`，调用本脚本生成带批注的 Word 交付物。这是审核助手的**唯一最终交付形态**（不输出 Markdown 报告）。

## 环境准备

- Python 3.7+
- 依赖：`python-docx >= 1.1`（需支持 `Document.add_comment`；推荐 1.2+）

```bash
pip install "python-docx>=1.1"
# 验证：
python -c "import docx; print(docx.__version__)"
```

## 用法

```bash
python skills/review-to-word/scripts/review_to_word.py \
  --src  "待审文章.docx" \
  --issues issues.json \
  --out  "原文件名_已审核_带批注.docx"
```

参数：
- `--src`：待审文章原文 .docx（若来源是 zip，先解压取出正文 docx）
- `--issues`：审核意见 JSON（结构见下）
- `--out`：输出的带批注 .docx 路径

## issues.json 结构

```json
{
  "title": "文章标题",
  "summary": [
    {"dimension": "严重问题检查", "result": "未发现问题"},
    {"dimension": "科学性审核", "result": "建议优化（2 项）"},
    {"dimension": "出版规范审核", "result": "需修改（1 项）"},
    {"dimension": "语言风格审核", "result": "未发现问题"},
    {"dimension": "医学逻辑审核", "result": "未发现问题"},
    {"dimension": "参考文献审核", "result": "建议优化（1 项）"}
  ],
  "issues": [
    {"anchor": "格外接地气", "level": "建议优化", "dimension": "出版规范", "problem": "编辑口吻/主观评价", "suggestion": "删除主观评价，直接陈述主题"},
    {"anchor": "mp.weixin.qq.com", "level": "需修改", "dimension": "参考文献", "problem": "引用微信公众号推文链接（P8禁用来源）", "suggestion": "删除或替换为权威来源"}
  ]
}
```

## 关键约定

- **anchor**：原文中真实存在、尽量短且唯一的连续字符串，脚本按字符串包含匹配定位并高亮。定位不到的问题会兜底列进文末明细清单，不会丢失。
- **level**：写 `需修改 / 建议优化 / 可接受` 三种**中文文字标签**。写进 Word 正文高亮与结论表的分级一律用文字，**禁止用 🔴🟡🟢 圆点 emoji**（Word/WPS 会渲染成方框/乱码）；分级的视觉区分由脚本自动施加的高亮底色承担（需修改=红 / 建议优化=黄 / 可接受=绿）。批注气泡内部为纯文本，可带 emoji 前缀正常显示。
- 脚本对每个 issue 都会挂批注——**需修改 与 建议优化 均须批注，不得只批红漏黄**。
- 批注格式：`[分级][维度][问题][修改建议]`。

## 脚本产出

1. 对每个 anchor 在原文高亮（红/黄/绿）并挂 Word 原生批注（含分级文字、维度、问题、修改建议）；
2. 文末追加「审核结论表 + 分级明细清单」页；
3. 未能在原文定位到的问题兜底列入文末明细，不丢失。
