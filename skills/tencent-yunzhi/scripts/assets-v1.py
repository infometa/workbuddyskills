"""
乐享 1.0 多媒体资源管理脚本（REST API）
支持：上传图片、下载图片

使用方式:
    python assets-v1.py upload --file photo.jpg --token lxmcp_xxx
    python assets-v1.py upload --files a.jpg b.png --token lxmcp_xxx --public
    python assets-v1.py download --asset-id xxx --token lxmcp_xxx
    python assets-v1.py download --asset-id xxx --token lxmcp_xxx --output ./images
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DEFAULT_API_HOST = "https://lxapi.lexiangla.com"

# 支持的图片格式
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}

# MIME 类型映射
MIME_MAP = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
}


def format_size(size: int) -> str:
    """格式化文件大小"""
    if size is None:
        return "未知"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def upload_single_image(api_host: str, token: str, file_path: str,
                        is_public: bool = False) -> Optional[Dict[str, Any]]:
    """上传单个图片"""
    path = Path(file_path)
    filename = path.name
    file_size = path.stat().st_size

    print(f"\n🖼️  上传图片: {filename} ({format_size(file_size)})")

    url = f"{api_host}/cgi-bin/v1/assets"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            data = {
                'type': 'image',
                'is_public': '1' if is_public else '0'
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=60)

        if resp.status_code == 401:
            print("❌ 上传失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            return None

        resp.raise_for_status()
        result = resp.json()

        asset_id = result.get('asset_id')
        asset_url = result.get('url')
        public_url = result.get('public_url')

        print(f"  ✅ 上传成功")
        print(f"  🆔 Asset ID: {asset_id}")
        print(f"  🔗 URL: {asset_url}")
        if public_url:
            print(f"  🌐 公共 URL: {public_url}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ 上传请求失败: {e}")
        return None


def cmd_upload(args):
    """上传图片"""
    file_paths: List[str] = []
    if args.file:
        file_paths.append(args.file)
    if args.files:
        file_paths.extend(args.files)

    if not file_paths:
        print("❌ 请指定要上传的图片 (--file 或 --files)")
        sys.exit(1)

    # 校验文件
    valid_files = []
    for fp in file_paths:
        abs_path = os.path.abspath(fp)
        path = Path(abs_path)
        if not path.exists():
            print(f"❌ 文件不存在: {fp}")
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"❌ 不支持的图片格式: {path.suffix}")
            print(f"   支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
            continue
        valid_files.append(abs_path)

    if not valid_files:
        print("\n❌ 没有有效的图片文件可以上传")
        sys.exit(1)

    print(f"\n📦 准备上传 {len(valid_files)} 个图片到 {args.host}")

    results = []
    for fp in valid_files:
        result = upload_single_image(args.host, args.token, fp, args.public)
        results.append((fp, result))

    # 汇总
    if len(results) > 1:
        print("\n" + "=" * 60)
        print("📊 上传结果汇总")
        print("=" * 60)
        success_count = 0
        for fp, result in results:
            filename = Path(fp).name
            if result:
                success_count += 1
                print(f"  ✅ {filename} → {result.get('asset_id', '?')}")
            else:
                print(f"  ❌ {filename} → 上传失败")
        print(f"\n  成功: {success_count}/{len(results)}")
        if success_count < len(results):
            sys.exit(1)


def cmd_download(args):
    """下载图片"""
    asset_id = args.asset_id

    # 从 URL 提取 asset_id
    if '/' in asset_id:
        # 可能是完整 URL: https://lexiangla.com/assets/xxx
        parts = asset_id.rstrip('/').split('/')
        asset_id = parts[-1]
        print(f"📎 从 URL 提取 Asset ID: {asset_id}")

    print(f"\n🔍 获取下载链接: {asset_id}...")

    url = f"{args.host}/cgi-bin/v1/assets/{asset_id}"
    headers = {"Authorization": f"Bearer {args.token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 401:
            print("❌ 获取失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            sys.exit(1)
        if resp.status_code == 404:
            print("❌ 获取失败: 资源不存在 (404)")
            sys.exit(1)
        resp.raise_for_status()
        result = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        sys.exit(1)

    download_url = result.get('url')
    mime_type = result.get('mime_type', 'unknown')

    if args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"  MIME: {mime_type}")
    print(f"  ⚠️  链接有效期: 3 分钟")

    if not download_url:
        print("❌ 未获取到下载链接")
        sys.exit(1)

    if args.no_download:
        print(f"\n📥 下载链接:\n{download_url}")
        return

    # 确定文件名
    ext_map = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
    }
    ext = ext_map.get(mime_type, '.bin')
    filename = args.filename or f"{asset_id}{ext}"

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    # 处理文件名冲突
    if os.path.exists(output_path):
        base, file_ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base}_{counter}{file_ext}")
            counter += 1

    print(f"  ⬇️  正在下载...")
    try:
        dl_resp = requests.get(download_url, timeout=60, stream=True)
        dl_resp.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in dl_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        file_size = os.path.getsize(output_path)
        print(f"\n✅ 图片已下载: {os.path.abspath(output_path)} ({format_size(file_size)})")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 下载失败: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='乐享 1.0 多媒体资源管理工具（REST API）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--host', default=DEFAULT_API_HOST,
                        help=f'API Host (默认: {DEFAULT_API_HOST})')

    subparsers = parser.add_subparsers(dest='command', help='操作命令')

    # upload 子命令
    p_upload = subparsers.add_parser('upload', help='上传图片')
    p_upload.add_argument('--file', help='单个图片文件路径')
    p_upload.add_argument('--files', nargs='+', help='多个图片文件路径')
    p_upload.add_argument('--token', required=True, help='MCP Token (lxmcp_xxx)')
    p_upload.add_argument('--public', action='store_true',
                          help='获取公共访问地址 (is_public=1)')

    # download 子命令
    p_download = subparsers.add_parser('download', help='下载图片')
    p_download.add_argument('--asset-id', required=True,
                            help='Asset ID 或完整 URL')
    p_download.add_argument('--token', required=True, help='MCP Token (lxmcp_xxx)')
    p_download.add_argument('--output', default='.', help='保存目录 (默认: 当前目录)')
    p_download.add_argument('--filename', help='保存文件名 (默认: {asset_id}.{ext})')
    p_download.add_argument('--no-download', action='store_true',
                            help='仅获取下载链接，不下载')
    p_download.add_argument('--raw', action='store_true', help='输出原始 JSON')

    args = parser.parse_args()

    if not HAS_REQUESTS:
        print("❌ 需要安装 requests 库: pip install requests")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        'upload': cmd_upload,
        'download': cmd_download,
    }
    cmd_map[args.command](args)


if __name__ == '__main__':
    main()
