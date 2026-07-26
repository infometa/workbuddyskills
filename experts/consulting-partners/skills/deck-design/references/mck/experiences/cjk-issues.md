# CJK Issues — Chinese/Japanese/Korean Rendering Experience

> Self-Refinement 经验沉淀。AI 在 S3 内容填充前必须读取。

## Experience 001: Chinese Text Missing KaiTi Font

**Date**: 2026-05-02
**Problem**: 生成的 PPTX 在 PowerPoint 中打开后中文显示为宋体或系统默认字体，不是楷体。
**Root Cause**: 只设置了 latin font（Arial），未设置 ea (East Asian) font。
**Fix**: 所有含中文的 run 必须调用 `set_ea_font(run, 'KaiTi')`。
**Rule**: MckEngine 内置处理，但直接写 `add_text()` 时必须手动调用。

```python
# ✅ 正确的中文字体设置
def set_ea_font(run, typeface='KaiTi'):
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', typeface)
```

## Experience 002: Chinese Text Line Spacing Issue

**Date**: 2026-05-02
**Problem**: 中文正文14pt 行间距过大，导致多行文字超出容器高度。
**Root Cause**: KaiTi 字体本身行间距比 Arial 更大。
**Fix**: 中文内容区估算高度时，按每行 1.4×14pt = ~19.6pt，即 ~0.27" 计算。
**Rule**: S3 门禁中的字符密度检查需用 CJK 行高系数 1.4 而非 1.2。
