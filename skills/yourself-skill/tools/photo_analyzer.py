#!/usr/bin/env python3
"""照片元信息分析器

提取照片 EXIF 信息（拍摄时间、地点），构建个人时间线和常去地点。

Usage:
    python3 photo_analyzer.py --dir <photo_dir> --output <output_path>
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def get_exif_data(image_path: str) -> dict:
    """提取单张图片的 EXIF 信息"""
    if not HAS_PIL:
        return {'error': 'Pillow 未安装，无法读取 EXIF'}

    try:
        img = Image.open(image_path)
        exif_raw = img._getexif()
        if not exif_raw:
            return {}

        exif = {}
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value

        result = {
            'file': os.path.basename(image_path),
            'path': image_path,
        }

        # 拍摄时间
        date_taken = exif.get('DateTimeOriginal') or exif.get('DateTime')
        if date_taken:
            result['date_taken'] = str(date_taken)

        # GPS 信息
        gps_info = exif.get('GPSInfo')
        if gps_info:
            gps_data = {}
            for key in gps_info:
                decode = GPSTAGS.get(key, key)
                gps_data[decode] = gps_info[key]

            if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                lat = _convert_to_degrees(gps_data['GPSLatitude'])
                lon = _convert_to_degrees(gps_data['GPSLongitude'])
                if gps_data.get('GPSLatitudeRef') == 'S':
                    lat = -lat
                if gps_data.get('GPSLongitudeRef') == 'W':
                    lon = -lon
                result['gps'] = {'lat': lat, 'lon': lon}

        return result
    except Exception as e:
        return {'file': os.path.basename(image_path), 'error': str(e)}


def _convert_to_degrees(value):
    """将 GPS 坐标转换为十进制度"""
    d, m, s = value
    return float(d) + float(m) / 60 + float(s) / 3600


def main():
    parser = argparse.ArgumentParser(description='照片元信息分析器')
    parser.add_argument('--dir', required=True, help='照片目录')
    parser.add_argument('--output', required=True, help='输出文件路径')

    args = parser.parse_args()

    if not os.path.isdir(args.dir):
        print(f"错误：目录不存在 {args.dir}", file=sys.stderr)
        sys.exit(1)

    image_exts = {'.jpg', '.jpeg', '.png', '.heic', '.heif'}
    photos = []

    for root, dirs, files in os.walk(args.dir):
        for fname in sorted(files):
            if Path(fname).suffix.lower() in image_exts:
                fpath = os.path.join(root, fname)
                exif = get_exif_data(fpath)
                photos.append(exif)

    # 按时间排序
    dated_photos = [p for p in photos if p.get('date_taken')]
    dated_photos.sort(key=lambda x: x['date_taken'])
    undated_photos = [p for p in photos if not p.get('date_taken')]

    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(f"# 照片时间线分析\n\n")
        f.write(f"扫描目录：{args.dir}\n")
        f.write(f"总照片数：{len(photos)}\n")
        f.write(f"有时间信息：{len(dated_photos)}\n")
        f.write(f"有位置信息：{len([p for p in photos if p.get('gps')])}\n\n")

        if dated_photos:
            f.write("## 时间线\n\n")
            for p in dated_photos:
                line = f"- **{p['date_taken'][:10]}** — {p['file']}"
                if p.get('gps'):
                    line += f" (GPS: {p['gps']['lat']:.4f}, {p['gps']['lon']:.4f})"
                f.write(line + "\n")
            f.write("\n")

        if undated_photos:
            f.write(f"## 无时间信息的照片（{len(undated_photos)} 张）\n\n")
            for p in undated_photos:
                f.write(f"- {p.get('file', p.get('path', 'unknown'))}\n")

        if not HAS_PIL:
            f.write("\n⚠️ Pillow 未安装，仅列出文件。安装方法：pip3 install Pillow\n")

    print(f"分析完成，结果已写入 {args.output}")


if __name__ == '__main__':
    main()
