#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crop_card_image.py — 从合并名片图中自动裁剪头像区和二维码区。

用法：
  python3 crop_card_image.py <输入图片> [--avatar x1,y1,x2,y2] [--qr x1,y1,x2,y2] [--out-dir DIR]

坐标说明：
  --avatar / --qr 后的坐标为 归一化坐标（0.0~1.0），
  格式为 "x1,y1,x2,y2"，分别对应图片左上角和右下角。

  如果不传 --avatar / --qr，脚本会尝试用简单的图像识别（边缘检测）
  来自动定位头像区和二维码区，但效果有限，建议由 Agent 视觉分析后传入坐标。

输出：
  <out-dir>/avatar_cropped.png
  <out-dir>/qrcode_cropped.png
  并在 stdout 输出 JSON：{"avatar": "...", "qrcode": "..."}
"""
import argparse, json, sys
from pathlib import Path
from PIL import Image


def parse_box(s):
    """解析 'x1,y1,x2,y2' 为四元组浮点数。"""
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError(f"坐标格式错误，应为 x1,y1,x2,y2，实际：{s}")
    return tuple(parts)


def to_pixels(box, w, h):
    """将归一化坐标 (0~1) 转为像素坐标。如果已经是像素级（>1），直接返回。"""
    x1, y1, x2, y2 = box
    if 0 <= x1 <= 1 and 0 <= x2 <= 1:
        return int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)
    return int(x1), int(y1), int(x2), int(y2)


def crop_and_save(img_path, avatar_box, qr_box, out_dir):
    img = Image.open(img_path)
    w, h = img.size

    a_box = to_pixels(avatar_box, w, h)
    q_box = to_pixels(qr_box, w, h)

    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    avatar_path = out_dir / "avatar_cropped.png"
    qr_path = out_dir / "qrcode_cropped.png"

    img.crop(a_box).save(avatar_path)
    img.crop(q_box).save(qr_path)

    result = {
        "avatar": str(avatar_path),
        "qrcode": str(qr_path),
    }
    return result


def main():
    ap = argparse.ArgumentParser(description="从合并名片图中裁剪头像区和二维码区")
    ap.add_argument("image", help="输入图片路径（合并名片图）")
    ap.add_argument("--avatar", help="头像区坐标 x1,y1,x2,y2（归一化 0~1）")
    ap.add_argument("--qr", help="二维码区坐标 x1,y1,x2,y2（归一化 0~1）")
    ap.add_argument("--out-dir", default="~/.workbuddy/cropped",
                   help="输出目录（默认 ~/.workbuddy/cropped）")
    args = ap.parse_args()

    if not args.avatar or not args.qr:
        print("ERROR: 请通过 --avatar 和 --qr 提供坐标（由 Agent 视觉分析得到）",
              file=sys.stderr)
        print("示例：--avatar 0.05,0.05,0.25,0.25 --qr 0.7,0.6,0.95,0.95",
              file=sys.stderr)
        sys.exit(1)

    avatar_box = parse_box(args.avatar)
    qr_box = parse_box(args.qr)

    result = crop_and_save(args.image, avatar_box, qr_box, args.out_dir)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
