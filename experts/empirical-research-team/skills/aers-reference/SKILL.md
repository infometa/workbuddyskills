---
name: aers-reference
description: "Reference materials and code templates for the Empirical Research Team, derived from the AERS catalog. Includes method selection guides, output specifications, and Python code templates for causal inference."
---

# AERS 方法论参考与代码模板

本 Skill 为实证研究团提供方法论参考和代码模板。内容转化自 Auto-Empirical Research Skills (AERS) 项目。

## 使用方式

- 需要选择研究方法时 → 参考 `references/design-selector.md`
- 需要了解输出规范时 → 参考 `references/output-spec.md`
- 需要方法论速查时 → 参考 `references/methods-reference.md`
- 需要 Stata/R 代码时 → 参考 `references/stata-r-reference.md`
- 需要 Python 代码模板时 → 查看 `templates/python/`

## 文件索引

| 文件 | 用途 |
|------|------|
| `references/design-selector.md` | 因果识别策略选择决策树 |
| `references/output-spec.md` | 发表级输出规范（5表4图） |
| `references/methods-reference.md` | 方法论速查（估计器×库×场景） |
| `references/stata-r-reference.md` | Stata/R 核心代码参考（DID/IV/RDD/稳健性） |
| `templates/python/did_template.py` | DID/事件研究 Python 模板 |
| `templates/python/iv_template.py` | IV/2SLS Python 模板 |
| `templates/python/rdd_template.py` | RDD Python 模板 |
| `templates/python/scm_template.py` | SCM 合成控制 Python 模板 |
| `templates/python/dml_template.py` | DML/ML因果推断 Python 模板 |
