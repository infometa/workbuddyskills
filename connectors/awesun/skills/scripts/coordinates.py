#!/usr/bin/env python3
# Copyright (c) 2026 Oray Inc. All rights reserved.
#
# No Part of this file may be reproduced, stored
# in a retrieval system, or transmitted, in any form, or by any means,
# electronic, mechanical, photocopying, recording, or otherwise,
# without the prior consent of Oray Inc.
#
# @Author: wuwenze <wuwenze@oray.com>
# @Date: 2026-07-08 12:56:00
# @FileName: coordinates.py

"""
UI 元素坐标计算工具，仅用于计算归一化坐标
"""

import sys
from typing import Tuple


def calculate_coordinates(
    pixel_x: int, pixel_y: int, image_width: int, image_height: int
) -> Tuple[float, float]:
    """
    计算归一化坐标

    公式：
    x = pixel_x / image_width
    y = pixel_y / image_height

    Args:
        pixel_x: 像素 X 坐标
        pixel_y: 像素 Y 坐标
        image_width: 图片宽度
        image_height: 图片高度

    Returns:
        (x, y) 归一化坐标元组，范围 [0.0, 1.0]
    """
    x = pixel_x / image_width
    y = pixel_y / image_height
    return (round(x, 6), round(y, 6))


def validate_coordinates(x: float, y: float) -> bool:
    """
    验证归一化坐标是否在有效范围内

    Args:
        x: X 方向归一化坐标
        y: Y 方向归一化坐标

    Returns:
        如果坐标在 [0.0, 1.0] 范围内返回 True
    """
    return 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 coordinates.py norm <pixel_x> <pixel_y> <width> <height>")
        print("  python3 coordinates.py validate <x> <y>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "norm":
        x, y = calculate_coordinates(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
        print(f"归一化坐标: ({x}, {y})")

    elif cmd == "validate":
        x, y = float(sys.argv[2]), float(sys.argv[3])
        valid = validate_coordinates(x, y)
        print(f"坐标 ({x}, {y}) 有效: {'是' if valid else '否'}")
        sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
