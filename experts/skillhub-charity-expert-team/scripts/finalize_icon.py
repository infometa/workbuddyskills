#!/usr/bin/env python3
"""
finalize_icon.py — 技术公益专家团 · 图标设计专家定稿处理工具

用途：
    把用户最终选定的图标候选草稿，统一处理为 512x512 的 PNG 定稿文件，并尝试用 pngquant 压缩。
    由图标设计专家在 Phase 2.5 步骤 4（定稿落盘）调用，替代此前"按操作系统分别敲 sips/convert/magick"
    的做法，保证 macOS / Linux / Windows 三端每次执行的缩放结果完全一致（用 Pillow 统一实现缩放，
    不依赖系统自带或需另装的 sips / ImageMagick）。

    压缩仍依赖本机可选安装的 pngquant（各平台均有官方版本，但需用户自行安装）：
    - 检测到则压缩，quality 区间可通过 --quality 调整（默认 65-80）
    - 未检测到则跳过压缩，直接交付未压缩的 512x512 PNG，并在输出 JSON 的 warning 字段说明，
      不抛异常、不中断整个定稿流程

用法：
    python3 finalize_icon.py <选中草稿绝对路径> <定稿输出路径，通常为 <技能目录>/icons/icon.png>
    python3 finalize_icon.py <选中草稿绝对路径> <定稿输出路径> --quality 65-80

    Windows 上如未注册 python3 命令，改用: python finalize_icon.py ...

依赖：
    Pillow（pip install -r scripts/requirements.txt）
    pngquant（可选，未安装不影响脚本运行，只是不压缩）

输出（stdout，单行 JSON，供 Agent 解析，不要用 AI 口算/复述代替）：
    成功: {"icon_path": "...", "size": "512x512", "compressed": true/false,
           "quantize_quality": "65-80" 或 null, "warning": null 或 "..."}
    失败: 非 0 退出码 + stderr 输出 {"error": "..."}
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(
        json.dumps({"error": "缺少 Pillow 依赖，请先执行: pip install -r scripts/requirements.txt"}, ensure_ascii=False),
        file=sys.stderr,
    )
    sys.exit(1)

TARGET_SIZE = (512, 512)


def resize_to_512(src: Path, dst: Path) -> None:
    """用 Pillow 统一实现缩放，跨平台行为一致，不依赖 sips/ImageMagick。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        im = im.resize(TARGET_SIZE, Image.LANCZOS)
        im.save(dst, format="PNG")


def compress_with_pngquant(target: Path, quality: str) -> bool:
    """尝试用本机 pngquant 压缩；未安装或压缩失败时返回 False，不抛异常。"""
    pngquant_bin = shutil.which("pngquant")
    if not pngquant_bin:
        return False
    tmp = target.with_suffix(".tmp.png")
    try:
        result = subprocess.run(
            [pngquant_bin, "--force", f"--quality={quality}", "--output", str(tmp), "--", str(target)],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    if result.returncode == 0 and tmp.exists():
        tmp.replace(target)
        return True
    if tmp.exists():
        tmp.unlink()
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="图标定稿处理：缩放至 512x512 + pngquant 压缩（跨平台一致）")
    parser.add_argument("src", type=Path, help="用户选中的候选草稿绝对路径")
    parser.add_argument("dst", type=Path, help="定稿图标输出路径，通常为 <技能目录>/icons/icon.png")
    parser.add_argument("--quality", default="65-80", help="pngquant 压缩质量区间，默认 65-80")
    args = parser.parse_args()

    if not args.src.exists():
        print(json.dumps({"error": f"源文件不存在: {args.src}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    try:
        resize_to_512(args.src, args.dst)
    except Exception as exc:  # noqa: BLE001 — 需要把任意图片解码/写入异常都转成可读 JSON 错误
        print(json.dumps({"error": f"缩放失败: {exc}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    compressed = compress_with_pngquant(args.dst, args.quality)

    print(
        json.dumps(
            {
                "icon_path": str(args.dst.resolve()),
                "size": "512x512",
                "compressed": compressed,
                "quantize_quality": args.quality if compressed else None,
                "warning": None if compressed else "本机未检测到 pngquant，已跳过压缩，交付的是未压缩的 512x512 PNG",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
