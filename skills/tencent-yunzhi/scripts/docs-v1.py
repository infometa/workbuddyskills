"""
乐享 1.0 文档管理脚本（REST API）
支持：查询、创建、上传、编辑、删除文档

使用方式:
    python docs-v1.py query --doc-id xxx --token lxmcp_xxx
    python docs-v1.py query --url "https://lexiangla.com/docs/xxx" --token lxmcp_xxx
    python docs-v1.py create --title "标题" --content "<p>内容</p>" --token lxmcp_xxx
    python docs-v1.py upload --file report.pdf --token lxmcp_xxx
    python docs-v1.py edit --doc-id xxx --title "新标题" --token lxmcp_xxx
    python docs-v1.py edit --url "https://lexiangla.com/docs/xxx" --title "新标题" --content "<p>新内容</p>" --token lxmcp_xxx
    python docs-v1.py edit --doc-id xxx --target-type file --name "新文件名" --downloadable 1 --token lxmcp_xxx
    python docs-v1.py delete --doc-id xxx --token lxmcp_xxx
"""

import os
import re
import sys
import json
import argparse
import html
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DEFAULT_API_HOST = "https://lxapi.lexiangla.com"

# 支持的文件格式白名单（上传用）
SUPPORTED_EXTENSIONS = {'.doc', '.docx', '.ppt', '.pptx', '.xlsx', '.xls', '.pdf', '.csv'}

# 链接中提取文档 ID 的正则
DOC_ID_PATTERN = re.compile(r'/docs/([a-f0-9]{32})')

PRIVILEGE_MAP = {0: "公开", 1: "部分人可见", 2: "仅创建者可见"}
PRIVILEGE_MAP_UPLOAD = {1: "公开", 2: "仅自己可见", 3: "指定人员可见"}


def format_size(size: int) -> str:
    """格式化文件大小"""
    if size is None:
        return "未知"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def extract_doc_id(url: str) -> Optional[str]:
    """从乐享链接中提取文档 ID"""
    match = DOC_ID_PATTERN.search(url)
    if match:
        return match.group(1)
    return None


def html_to_text(html_content: str) -> str:
    """简单的 HTML 转纯文本"""
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<(p|div|h[1-6])(\s[^>]*)?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ═══════════════════════════════════════════════════════
# 查询文档
# ═══════════════════════════════════════════════════════

def cmd_query(args):
    """查询文档"""
    doc_id = args.doc_id
    if args.url:
        doc_id = extract_doc_id(args.url)
        if not doc_id:
            print(f"❌ 无法从链接中提取文档 ID: {args.url}")
            print("  链接应包含 /docs/{{32位十六进制ID}}")
            sys.exit(1)
        print(f"📎 从链接提取文档 ID: {doc_id}")

    print(f"\n🔍 正在查询文档 {doc_id}...")
    url = f"{args.host}/cgi-bin/v1/docs/{doc_id}"
    headers = {"Authorization": f"Bearer {args.token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 401:
            print("❌ 查询失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            sys.exit(1)
        if resp.status_code == 404:
            print("❌ 查询失败: 文档不存在或无权访问 (404)")
            sys.exit(1)
        resp.raise_for_status()
        response = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 查询请求失败: {e}")
        sys.exit(1)

    if args.raw:
        print(json.dumps(response, ensure_ascii=False, indent=2))
        return

    # 提取元信息
    data = response.get("data", {})
    attrs = data.get("attributes", {})
    included = response.get("included", [])

    # 检测文档类型
    doc_type = "unknown"
    for item in included:
        if item.get("type") == "file":
            doc_type = "file"
            break
        if item.get("type") == "document":
            doc_type = "richtext"
            break

    if not args.text_only:
        creator_name = None
        for item in included:
            if item.get("type") == "staff":
                creator_name = item.get("attributes", {}).get("name")
                break

        print(f"""
╔══════════════════════════════════════════════════════════╗
║              乐享 1.0 文档查询结果                         ║
╠══════════════════════════════════════════════════════════╣
║  📄 标题:   {attrs.get('name', '无标题'):<46}║
║  🆔 ID:     {data.get('id', ''):<46}║
║  👤 创建者: {(creator_name or '未知'):<46}║
║  📅 创建:   {(attrs.get('created_at') or '未知'):<46}║
║  📅 更新:   {(attrs.get('updated_at') or '未知'):<46}║
║  👁️ 浏览:   {str(attrs.get('read_count', 0)):<46}║
║  💬 评论:   {str(attrs.get('comment_count', 0)):<46}║
║  🔒 权限:   {PRIVILEGE_MAP.get(attrs.get('privilege_type'), '未知'):<46}║
╚══════════════════════════════════════════════════════════╝""")

    if doc_type == "richtext":
        html_content = md_content = None
        for item in included:
            if item.get("type") == "document":
                item_attrs = item.get("attributes", {})
                html_content = item_attrs.get("content")
                md_content = item_attrs.get("md_content")
                break

        if args.text_only:
            if md_content:
                print(md_content)
            elif html_content:
                print(html_to_text(html_content))
            else:
                print("(文档内容为空)")
        else:
            print(f"\n📝 文档类型: 富文本")
            print("─" * 60)
            if md_content:
                print("\n【Markdown 内容】\n")
                print(md_content)
            elif html_content:
                print("\n【正文内容】\n")
                print(html_to_text(html_content))
            else:
                print("\n(文档内容为空)")
            print("\n" + "─" * 60)

    elif doc_type == "file":
        file_info = None
        for item in included:
            if item.get("type") == "file":
                item_attrs = item.get("attributes", {})
                links = item.get("links", {})
                file_info = {
                    "name": item_attrs.get("name", "download"),
                    "size": item_attrs.get("size"),
                    "mime_type": item_attrs.get("mime_type"),
                    "download_url": links.get("download")
                }
                break

        if not file_info:
            print("❌ 无法提取文件信息")
            sys.exit(1)

        if not args.text_only:
            print(f"\n📎 文档类型: 文件")
            print(f"  文件名:  {file_info['name']}")
            if file_info.get('size'):
                print(f"  文件大小: {format_size(file_info['size'])}")
            if file_info.get('mime_type'):
                print(f"  MIME:    {file_info['mime_type']}")

        if file_info.get('download_url'):
            if args.download:
                output_dir = args.output
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, file_info['name'])
                if os.path.exists(output_path):
                    base, ext = os.path.splitext(file_info['name'])
                    counter = 1
                    while os.path.exists(output_path):
                        output_path = os.path.join(output_dir, f"{base}_{counter}{ext}")
                        counter += 1

                print(f"  ⬇️  正在下载: {file_info['name']}")
                dl_resp = requests.get(file_info['download_url'], timeout=120, stream=True)
                dl_resp.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in dl_resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"\n✅ 文件已下载: {os.path.abspath(output_path)}")
            else:
                if not args.text_only:
                    print(f"\n  💡 提示: 使用 --download 参数可自动下载文件")
                    print(f"  ⚠️  下载链接有效期仅 3 分钟")
                print(f"\n📥 下载链接:\n{file_info['download_url']}")
    else:
        print(f"⚠️  无法识别文档类型，输出原始 JSON:")
        print(json.dumps(response, ensure_ascii=False, indent=2))

    print()


# ═══════════════════════════════════════════════════════
# 创建文档
# ═══════════════════════════════════════════════════════

def cmd_create(args):
    """创建富文本文档"""
    print(f"\n📝 正在创建文档: {args.title}")

    payload = {
        "data": {
            "type": "doc",
            "attributes": {
                "title": args.title,
                "content": args.content,
                "is_markdown": 1 if args.markdown else 0,
                "privilege_type": args.privilege
            }
        }
    }

    if args.tags:
        payload["data"]["attributes"]["tags"] = args.tags

    url = f"{args.host}/cgi-bin/v1/docs"
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 401:
            print("❌ 创建失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            sys.exit(1)
        resp.raise_for_status()
        data = resp.json()
        doc_id = data.get("data", {}).get("id")
        print(f"✅ 文档创建成功!")
        print(f"  🆔 ID: {doc_id}")
        if doc_id:
            print(f"  🔗 链接: {args.host.replace('lxapi.', '')}/docs/{doc_id}")

        if args.raw:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"❌ 创建请求失败: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# 上传文件类型文档
# ═══════════════════════════════════════════════════════

def upload_single_file(api_host: str, token: str, file_path: str,
                       doc_name: Optional[str] = None,
                       downloadable: int = 1, privilege_type: int = 2) -> Optional[Dict]:
    """完整的单文件上传流程（三步）"""
    path = Path(file_path)
    filename = path.name
    display_name = doc_name or path.stem
    file_size = path.stat().st_size
    encoded_filename = urllib.parse.quote(filename, safe='')

    print(f"\n📄 上传文件: {filename} ({format_size(file_size)})")

    # Step 1
    print("  [1/3] 获取资源签名...")
    url = f"{api_host}/cgi-bin/v1/docs/cos-param"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"filename": filename, "type": "file"}, timeout=30)
        if resp.status_code == 401:
            print("❌ Step 1 失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            return None
        resp.raise_for_status()
        attrs = resp.json().get("data", {}).get("attributes", {})
        if not attrs.get("accessUrl"):
            print(f"❌ Step 1 失败: 返回数据异常")
            return None
        cos_params = {
            "accessUrl": attrs["accessUrl"],
            "authorization": attrs["authorization"],
            "securityToken": attrs["securityToken"],
            "state": attrs["state"]
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Step 1 请求失败: {e}")
        return None
    print("  [1/3] ✅ 签名获取成功")

    # Step 2
    print("  [2/3] 上传到腾讯云 COS...")
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        cos_headers = {
            "Authorization": cos_params["authorization"],
            "x-cos-security-token": cos_params["securityToken"],
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}; filename={encoded_filename}"
        }
        resp = requests.put(cos_params["accessUrl"], headers=cos_headers, data=file_data, timeout=120)
        if resp.status_code != 200:
            print(f"❌ Step 2 失败: HTTP {resp.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Step 2 请求失败: {e}")
        return None
    print("  [2/3] ✅ COS 上传成功")

    # Step 3
    print("  [3/3] 创建文档实体...")
    url = f"{api_host}/cgi-bin/v1/docs/upload?state={cos_params['state']}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "data": {
            "type": "doc",
            "attributes": {
                "name": display_name,
                "downloadable": downloadable,
                "privilege_type": privilege_type
            }
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            data = resp.json()
            doc_id = data.get("data", {}).get("id")
            print(f"  [3/3] ✅ 文档创建成功 (ID: {doc_id})")
            return {"id": doc_id, "name": display_name, "raw": data}
        else:
            print(f"❌ Step 3 失败: HTTP {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Step 3 请求失败: {e}")
        return None


def cmd_upload(args):
    """上传文件类型文档"""
    file_paths: List[str] = []
    if args.file:
        file_paths.append(args.file)
    if args.files:
        file_paths.extend(args.files)

    if not file_paths:
        print("❌ 请指定要上传的文件 (--file 或 --files)")
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
            print(f"❌ 不支持的文件格式: {path.suffix}")
            print(f"   支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
            continue
        valid_files.append(abs_path)

    if not valid_files:
        print("\n❌ 没有有效的文件可以上传")
        sys.exit(1)

    print(f"\n📦 准备上传 {len(valid_files)} 个文件到 {args.host}")

    if args.dry_run:
        for fp in valid_files:
            p = Path(fp)
            print(f"  📄 {p.name} ({format_size(p.stat().st_size)})")
        print("\n🔍 Dry Run 模式，未执行实际上传")
        return

    results = []
    for fp in valid_files:
        doc_name = args.name if len(valid_files) == 1 else None
        result = upload_single_file(args.host, args.token, fp, doc_name,
                                    args.downloadable, args.privilege)
        results.append((fp, result))

    # 汇总
    print("\n" + "=" * 60)
    print("📊 上传结果汇总")
    print("=" * 60)
    success_count = 0
    for fp, result in results:
        filename = Path(fp).name
        if result:
            success_count += 1
            print(f"  ✅ {filename} → ID: {result['id']}")
        else:
            print(f"  ❌ {filename} → 上传失败")
    print(f"\n  成功: {success_count}/{len(results)}")
    if success_count < len(results):
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# 编辑文档
# ═══════════════════════════════════════════════════════

def cmd_edit(args):
    """编辑文档"""
    doc_id = args.doc_id
    if args.url:
        doc_id = extract_doc_id(args.url)
        if not doc_id:
            print(f"❌ 无法从链接中提取文档 ID: {args.url}")
            sys.exit(1)
        print(f"📎 从链接提取文档 ID: {doc_id}")

    print(f"\n✏️  正在编辑文档 {doc_id}...")

    attributes = {}
    if args.title:
        attributes["title"] = args.title
    if args.content:
        attributes["content"] = args.content
    if args.name:
        attributes["name"] = args.name
    if args.privilege is not None:
        attributes["privilege_type"] = args.privilege
    if args.allow_comment is not None:
        attributes["allow_comment"] = args.allow_comment
    if args.signature:
        attributes["signature"] = args.signature
    if args.source:
        attributes["source"] = args.source
    if args.reship_url:
        attributes["reship_url"] = args.reship_url
    if args.picture_url:
        attributes["picture_url"] = args.picture_url
    if args.only_team is not None:
        attributes["only_team"] = args.only_team
    if args.downloadable is not None:
        attributes["downloadable"] = args.downloadable
    if args.enable_watermark is not None:
        attributes["enable_watermark"] = args.enable_watermark
    if args.enable_copy_limit is not None:
        attributes["enable_copy_limit"] = args.enable_copy_limit
    if args.enable_image_watermark is not None:
        attributes["enable_image_watermark"] = args.enable_image_watermark
    if args.tags:
        attributes["tags"] = args.tags

    relationships = {}
    if args.category_id:
        relationships["category"] = {"data": {"type": "category", "id": args.category_id}}
    if args.team_id:
        relationships["team"] = {"data": {"type": "team", "id": args.team_id}}
    if args.directory_id:
        relationships["directory"] = {"data": {"type": "directory", "id": args.directory_id}}

    if not attributes and not relationships:
        print("❌ 请至少指定一个要修改的属性")
        sys.exit(1)

    payload = {"data": {"type": "doc", "attributes": attributes}}
    if relationships:
        payload["data"]["relationships"] = relationships

    target_type = args.target_type or "document"
    url = f"{args.host}/cgi-bin/v1/docs/{doc_id}?target_type={target_type}"
    headers = {
        "Authorization": f"Bearer {args.token}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 401:
            print("❌ 编辑失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            sys.exit(1)
        if resp.status_code == 404:
            print("❌ 编辑失败: 文档不存在或无权访问 (404)")
            sys.exit(1)
        resp.raise_for_status()
        print(f"✅ 文档编辑成功!")
        if args.raw:
            print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"❌ 编辑请求失败: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# 删除文档
# ═══════════════════════════════════════════════════════

def cmd_delete(args):
    """删除文档"""
    if not args.force:
        confirm = input(f"⚠️  确认删除文档 {args.doc_id}？此操作不可恢复 [y/N]: ")
        if confirm.lower() != 'y':
            print("已取消")
            return

    print(f"\n🗑️  正在删除文档 {args.doc_id}...")
    url = f"{args.host}/cgi-bin/v1/docs/{args.doc_id}"
    headers = {"Authorization": f"Bearer {args.token}"}

    try:
        resp = requests.delete(url, headers=headers, timeout=30)
        if resp.status_code == 401:
            print("❌ 删除失败: Token 无效或已过期 (401)，请打开 /mcp 页面点击续期")
            sys.exit(1)
        if resp.status_code == 404:
            print("❌ 删除失败: 文档不存在或无权访问 (404)")
            sys.exit(1)
        if resp.status_code == 204:
            print(f"✅ 文档已删除: {args.doc_id}")
        else:
            resp.raise_for_status()
            print(f"✅ 文档已删除: {args.doc_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 删除请求失败: {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='乐享 1.0 文档管理工具（REST API）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--host', default=DEFAULT_API_HOST,
                        help=f'API Host (默认: {DEFAULT_API_HOST})')

    subparsers = parser.add_subparsers(dest='command', help='操作命令')

    # query 子命令
    p_query = subparsers.add_parser('query', help='查询文档')
    group = p_query.add_mutually_exclusive_group(required=True)
    group.add_argument('--doc-id', help='文档 ID')
    group.add_argument('--url', help='乐享文档链接')
    p_query.add_argument('--token', required=True, help='MCP Token (lxmcp_xxx)')
    p_query.add_argument('--download', action='store_true', help='自动下载文件')
    p_query.add_argument('--output', default='.', help='下载保存目录')
    p_query.add_argument('--raw', action='store_true', help='输出原始 JSON')
    p_query.add_argument('--text-only', action='store_true', help='仅输出正文')

    # create 子命令
    p_create = subparsers.add_parser('create', help='创建富文本文档')
    p_create.add_argument('--title', required=True, help='文档标题')
    p_create.add_argument('--content', required=True, help='正文内容 (HTML 或 Markdown)')
    p_create.add_argument('--token', required=True, help='MCP Token')
    p_create.add_argument('--markdown', action='store_true', help='内容为 Markdown 格式')
    p_create.add_argument('--privilege', type=int, default=2, choices=[0, 1, 2],
                          help='可见性: 0=公开, 1=部分人, 2=仅自己(默认)')
    p_create.add_argument('--tags', nargs='+', help='标签列表')
    p_create.add_argument('--raw', action='store_true', help='输出原始 JSON')

    # upload 子命令
    p_upload = subparsers.add_parser('upload', help='上传文件类型文档')
    p_upload.add_argument('--file', help='单个文件路径')
    p_upload.add_argument('--files', nargs='+', help='多个文件路径')
    p_upload.add_argument('--token', required=True, help='MCP Token')
    p_upload.add_argument('--name', help='文档名称 (仅单文件)')
    p_upload.add_argument('--privilege', type=int, default=2, choices=[1, 2, 3],
                          help='可见性: 1=公开, 2=仅自己(默认), 3=指定人员')
    p_upload.add_argument('--downloadable', type=int, default=1, choices=[0, 1],
                          help='允许下载: 1=允许(默认), 0=禁止')
    p_upload.add_argument('--dry-run', action='store_true', help='仅检查文件')

    # edit 子命令
    p_edit = subparsers.add_parser('edit', help='编辑文档')
    edit_id_group = p_edit.add_mutually_exclusive_group(required=True)
    edit_id_group.add_argument('--doc-id', help='文档 ID')
    edit_id_group.add_argument('--url', help='乐享文档链接')
    p_edit.add_argument('--token', required=True, help='MCP Token')
    p_edit.add_argument('--target-type', choices=['document', 'file'],
                        help='文档类型: document(富文本) 或 file(文件)')
    # 基本属性
    p_edit.add_argument('--title', help='新标题（富文本类型）')
    p_edit.add_argument('--content', help='新内容（富文本类型，HTML）')
    p_edit.add_argument('--name', help='新文档名（文件类型）')
    p_edit.add_argument('--privilege', type=int, choices=[0, 1, 2],
                        help='可见性: 0=公开, 1=部分人, 2=仅创建者')
    p_edit.add_argument('--allow-comment', type=int, choices=[0, 1],
                        help='允许评论: 0=不允许, 1=允许')
    p_edit.add_argument('--signature', help='署名')
    p_edit.add_argument('--source', choices=['original', 'reship'],
                        help='来源: original=原创, reship=转载')
    p_edit.add_argument('--reship-url', help='转载来源链接')
    p_edit.add_argument('--picture-url', help='封面图片 URL')
    p_edit.add_argument('--only-team', type=int, choices=[0, 1],
                        help='0=发布到公共知识库, 1=仅团队')
    p_edit.add_argument('--downloadable', type=int, choices=[0, 1],
                        help='允许下载（文件类型）: 0=禁止, 1=允许')
    p_edit.add_argument('--enable-watermark', type=int, choices=[0, 1],
                        help='页面文字水印: 0=关, 1=开')
    p_edit.add_argument('--enable-copy-limit', type=int, choices=[0, 1],
                        help='禁止复制文字: 0=关, 1=开')
    p_edit.add_argument('--enable-image-watermark', type=int, choices=[0, 1],
                        help='图片水印: 0=关, 1=开')
    p_edit.add_argument('--tags', nargs='+', help='标签列表（最多5个）')
    # 关联关系
    p_edit.add_argument('--category-id', help='分类 ID')
    p_edit.add_argument('--team-id', help='K吧/团队 ID')
    p_edit.add_argument('--directory-id', help='目录 ID')
    p_edit.add_argument('--raw', action='store_true', help='输出原始 JSON')

    # delete 子命令
    p_delete = subparsers.add_parser('delete', help='删除文档')
    p_delete.add_argument('--doc-id', required=True, help='文档 ID')
    p_delete.add_argument('--token', required=True, help='MCP Token')
    p_delete.add_argument('--force', action='store_true', help='跳过确认')

    args = parser.parse_args()

    if not HAS_REQUESTS:
        print("❌ 需要安装 requests 库: pip install requests")
        sys.exit(1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_map = {
        'query': cmd_query,
        'create': cmd_create,
        'upload': cmd_upload,
        'edit': cmd_edit,
        'delete': cmd_delete,
    }
    cmd_map[args.command](args)


if __name__ == '__main__':
    main()
