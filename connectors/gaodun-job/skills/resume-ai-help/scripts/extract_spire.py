# -*- coding: utf-8 -*-
"""Extract plain text from legacy Word .doc files via Spire.Doc.

用法：
    python extract_spire.py <输入.doc> [输出.txt]

  - 输入文件为命令行参数，用户上传什么就传什么，禁止写死路径；
  - 省略输出路径时文本直接写到 stdout（UTF-8），可管道给后续处理；
  - 依赖：pip install Spire.Doc（Windows 下已验证可用）。
"""
import sys


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    try:
        from spire.doc import Document
    except ModuleNotFoundError:
        print('缺少依赖：pip install Spire.Doc；或改用兜底脚本 extract_doc_text.py', file=sys.stderr)
        sys.exit(2)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None

    doc = Document()
    doc.LoadFromFile(src)
    text = doc.GetText()

    # 与 extract_doc_text.py 保持一致的空白归一化
    lines = [ln.rstrip() for ln in text.split('\r')]
    text = '\n'.join(lines)

    if dst:
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(text)
        print('OK:%s chars=%d' % (dst, len(text)), file=sys.stderr)
    else:
        sys.stdout.buffer.write(text.encode('utf-8'))


if __name__ == '__main__':
    main()
