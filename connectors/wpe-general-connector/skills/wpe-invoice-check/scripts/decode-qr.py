#!/usr/bin/env python3
"""
decode-qr.py — 解码发票票面左上角二维码（视觉识别要素后的权威交叉校验源）

背景：数电票 20 位长号码靠视觉识别极易错位/多读 0（实测案例：
票面印刷号码被读成 21 位，渠道报「二维码参数不合法」；二维码解码后立即纠错）。

用法:
  python3 decode-qr.py <发票文件.pdf|png|jpg> [--dpi 400]

输出:
  QR_RAW=<原始内容>
  数电票标准格式解析: 01,<票种>,<发票代码>,<号码>,<金额·元>,<日期yyyyMMdd>,<校验码>,<其他>

依赖: pymupdf（PDF 渲染）+ opencv-python-headless（解码），请安装于当前环境
  （`pip install pymupdf opencv-python-headless`）
"""
import argparse
import os
import subprocess
import sys
import tempfile

def render_pages(src, dpi):
    """PDF → PNG 列表；图片直接返回原路径。"""
    ext = os.path.splitext(src)[1].lower()
    if ext != ".pdf":
        return [src]
    import pymupdf  # noqa: N813
    doc = pymupdf.open(src)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        p = os.path.join(tempfile.mkdtemp(prefix="qr_"), f"p{i+1}.png")
        pix.save(p)
        paths.append(p)
    doc.close()
    return paths

def decode_image(path):
    import cv2
    img = cv2.imread(path)
    if img is None:
        return ""
    det = cv2.QRCodeDetector()
    data, _, _ = det.detectAndDecode(img)
    if data:
        return data
    # 缩小搜索范围：二维码通常在左上角
    h, w = img.shape[:2]
    for ratio in (0.3, 0.5):
        crop = img[0 : int(h * ratio), 0 : int(w * ratio)]
        data, _, _ = det.detectAndDecode(crop)
        if data:
            return data
    return ""

def parse_digital_invoice(raw):
    """数电票二维码标准格式：01,<票种>,<发票代码>,<号码>,<金额元>,<日期>,<校验码>,<其他>"""
    parts = raw.split(",")
    if len(parts) < 6:
        return None
    return {
        "version": parts[0],
        "invoice_type": parts[1],
        "invoice_code": parts[2] or "（空）",
        "invoice_no": parts[3],
        "amount_yuan": parts[4],
        "invoice_date": parts[5],
        "check_code": parts[6] if len(parts) > 6 else "",
        "extra": parts[7] if len(parts) > 7 else "",
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--dpi", type=int, default=400)
    args = ap.parse_args()

    if not os.path.exists(args.file):
        print(f"ERROR: file not found: {args.file}")
        sys.exit(1)

    try:
        pages = render_pages(args.file, args.dpi)
    except Exception as e:
        print(f"ERROR render: {e}")
        sys.exit(1)

    for p in pages:
        raw = decode_image(p)
        if not raw:
            continue
        print(f"QR_RAW={raw}")
        fields = parse_digital_invoice(raw)
        if fields:
            print(f"QR_INVOICE_TYPE={fields['invoice_type']}")
            print(f"QR_INVOICE_NO={fields['invoice_no']}  (len={len(fields['invoice_no'])})")
            print(f"QR_INVOICE_CODE={fields['invoice_code']}")
            print(f"QR_AMOUNT_YUAN={fields['amount_yuan']}")
            print(f"QR_INVOICE_DATE={fields['invoice_date']}")
            if fields["check_code"]:
                print(f"QR_CHECK_CODE={fields['check_code']}")
            if fields["extra"]:
                print(f"QR_EXTRA={fields['extra']}")
            # 长度告警：数电票号码必须 20 位；视觉识别结果若与二维码不一致，以二维码为准
            if len(fields["invoice_no"]) != 20:
                print("WARN: QR 号码不是 20 位，请人工核对")
        sys.exit(0)
    print("NO_DECODE")
    sys.exit(2)

if __name__ == "__main__":
    main()
