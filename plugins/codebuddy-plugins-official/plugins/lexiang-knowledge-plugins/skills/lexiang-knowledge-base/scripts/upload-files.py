"""
云知知识库文件上传脚本
支持并行上传文件到云知，使用预签名 URL

使用方式:
    python upload-files.py --files file1.md file2.pdf --entry-id <parent_entry_id>
    python upload-files.py --folder ./docs --entry-id <parent_entry_id> --parallel 5
"""

import os
import sys
import json
import asyncio
import hashlib
import argparse
import mimetypes
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

# 尝试导入 aiohttp，如果不存在则使用 requests
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    import requests


@dataclass
class UploadTask:
    """上传任务"""
    local_path: str
    file_name: str
    parent_entry_id: str
    mime_type: str
    file_size: int
    content_hash: str
    file_id: Optional[str] = None  # 更新时需要
    status: str = 'pending'
    entry_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class UploadSession:
    """上传会话"""
    session_id: str
    upload_url: str
    task: UploadTask


@dataclass
class MCPCallResult:
    """MCP 调用结果（模拟）"""
    tool: str
    args: dict
    note: str


def compute_file_hash(file_path: str) -> str:
    """计算文件 MD5 hash"""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_mime_type(file_path: str) -> str:
    """获取文件 MIME 类型"""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    
    # 自定义扩展名映射
    ext = Path(file_path).suffix.lower()
    custom_types = {
        '.md': 'text/markdown',
        '.markdown': 'text/markdown',
        '.json': 'application/json',
    }
    return custom_types.get(ext, 'application/octet-stream')


class YunzhiUploader:
    """云知文件上传器"""
    
    def __init__(self, parallel: int = 3):
        self.parallel = parallel
        self.mcp_calls: List[MCPCallResult] = []
    
    def generate_apply_upload_call(self, task: UploadTask) -> MCPCallResult:
        """生成申请上传的 MCP 调用参数"""
        args = {
            'parent_entry_id': task.parent_entry_id,
            'name': task.file_name,
            'mime_type': task.mime_type,
            'size': task.file_size,
            'upload_type': 'PRE_SIGNED_URL'
        }
        
        if task.file_id:
            args['file_id'] = task.file_id
            note = f'更新文件: {task.file_name} (file_id={task.file_id})'
        else:
            note = f'新建文件: {task.file_name}'
        
        return MCPCallResult(
            tool='云知.file_apply_upload',
            args=args,
            note=note
        )
    
    def generate_commit_upload_call(self, session_id: str, file_name: str) -> MCPCallResult:
        """生成确认上传的 MCP 调用参数"""
        return MCPCallResult(
            tool='云知.file_commit_upload',
            args={'session_id': session_id},
            note=f'确认上传: {file_name}'
        )
    
    async def upload_file_async(self, upload_url: str, file_path: str, mime_type: str) -> bool:
        """异步上传文件到预签名 URL"""
        if not HAS_AIOHTTP:
            return self.upload_file_sync(upload_url, file_path, mime_type)
        
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            headers = {'Content-Type': mime_type}
            async with session.put(upload_url, data=data, headers=headers) as response:
                return response.status in (200, 201)
    
    def upload_file_sync(self, upload_url: str, file_path: str, mime_type: str) -> bool:
        """同步上传文件到预签名 URL"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        headers = {'Content-Type': mime_type}
        response = requests.put(upload_url, data=data, headers=headers)
        return response.status_code in (200, 201)
    
    def scan_folder(self, folder_path: str, parent_entry_id: str, 
                    extensions: Optional[List[str]] = None,
                    ignore_patterns: Optional[List[str]] = None) -> List[UploadTask]:
        """扫描文件夹生成上传任务"""
        tasks = []
        folder = Path(folder_path)
        
        if ignore_patterns is None:
            ignore_patterns = ['node_modules', '.git', '__pycache__', '.DS_Store']
        
        if extensions is None:
            extensions = ['.md', '.markdown', '.txt', '.json', '.pdf', '.doc', '.docx']
        
        for file_path in folder.rglob('*'):
            if file_path.is_dir():
                continue
            
            # 检查忽略模式
            relative_path = str(file_path.relative_to(folder))
            should_ignore = any(p in relative_path for p in ignore_patterns)
            if should_ignore:
                continue
            
            # 检查扩展名
            if extensions and file_path.suffix.lower() not in extensions:
                continue
            
            task = UploadTask(
                local_path=str(file_path),
                file_name=file_path.name,
                parent_entry_id=parent_entry_id,
                mime_type=get_mime_type(str(file_path)),
                file_size=file_path.stat().st_size,
                content_hash=compute_file_hash(str(file_path))
            )
            tasks.append(task)
        
        return tasks
    
    def generate_upload_plan(self, tasks: List[UploadTask]) -> Dict:
        """生成上传计划（MCP 调用序列）"""
        plan = {
            'total_files': len(tasks),
            'total_size': sum(t.file_size for t in tasks),
            'parallel': self.parallel,
            'steps': []
        }
        
        for i, task in enumerate(tasks, 1):
            # Step 1: 申请上传
            apply_call = self.generate_apply_upload_call(task)
            plan['steps'].append({
                'step': f'{i}.1',
                'description': apply_call.note,
                'mcp_call': {
                    'tool': apply_call.tool,
                    'args': apply_call.args
                }
            })
            
            # Step 2: HTTP PUT 上传（非 MCP）
            plan['steps'].append({
                'step': f'{i}.2',
                'description': f'HTTP PUT 上传文件内容到 upload_url',
                'note': '使用 apply_upload 返回的 upload_url 进行 PUT 请求',
                'code_hint': f'''
# Python 示例
with open("{task.local_path}", "rb") as f:
    requests.put(upload_url, data=f.read(), headers={{"Content-Type": "{task.mime_type}"}})

# curl 示例  
# curl -X PUT -H "Content-Type: {task.mime_type}" --data-binary @"{task.local_path}" "$upload_url"
'''
            })
            
            # Step 3: 确认上传
            plan['steps'].append({
                'step': f'{i}.3',
                'description': f'确认上传完成: {task.file_name}',
                'mcp_call': {
                    'tool': '云知.file_commit_upload',
                    'args': {'session_id': '<从 step {}.1 返回值获取>'.format(i)}
                }
            })
        
        return plan
    
    async def execute_parallel_uploads(self, sessions: List[UploadSession]) -> List[Tuple[UploadSession, bool]]:
        """并行执行文件上传"""
        semaphore = asyncio.Semaphore(self.parallel)
        
        async def upload_with_semaphore(session: UploadSession) -> Tuple[UploadSession, bool]:
            async with semaphore:
                success = await self.upload_file_async(
                    session.upload_url,
                    session.task.local_path,
                    session.task.mime_type
                )
                return session, success
        
        tasks = [upload_with_semaphore(s) for s in sessions]
        return await asyncio.gather(*tasks)


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def print_upload_plan(plan: Dict):
    """打印上传计划"""
    print(f'''
╔══════════════════════════════════════════════════════════════════╗
║                      云知文件上传计划                              ║
╠══════════════════════════════════════════════════════════════════╣
║  文件数量: {plan['total_files']:<10}  总大小: {format_size(plan['total_size']):<15} ║
║  并行数: {plan['parallel']:<12}                                   ║
╚══════════════════════════════════════════════════════════════════╝
''')
    
    print('📋 执行步骤:')
    for step in plan['steps']:
        if 'mcp_call' in step:
            print(f"  [{step['step']}] {step['description']}")
            print(f"       Tool: {step['mcp_call']['tool']}")
            print(f"       Args: {json.dumps(step['mcp_call']['args'], ensure_ascii=False)}")
        else:
            print(f"  [{step['step']}] {step['description']}")
            if 'note' in step:
                print(f"       Note: {step['note']}")


def main():
    parser = argparse.ArgumentParser(description='云知知识库文件上传工具')
    parser.add_argument('--files', nargs='+', help='要上传的文件列表')
    parser.add_argument('--folder', help='要上传的文件夹')
    parser.add_argument('--entry-id', required=True, help='目标父节点 entry_id')
    parser.add_argument('--parallel', type=int, default=3, help='并行上传数量')
    parser.add_argument('--extensions', nargs='+', default=['.md', '.txt', '.pdf'], help='支持的文件扩展名')
    parser.add_argument('--output', help='输出上传计划到 JSON 文件')
    parser.add_argument('--dry-run', action='store_true', help='仅生成计划不执行')
    
    args = parser.parse_args()
    
    uploader = YunzhiUploader(parallel=args.parallel)
    tasks: List[UploadTask] = []
    
    if args.folder:
        tasks = uploader.scan_folder(args.folder, args.entry_id, args.extensions)
    elif args.files:
        for file_path in args.files:
            if not os.path.exists(file_path):
                print(f'⚠️  文件不存在: {file_path}')
                continue
            
            task = UploadTask(
                local_path=file_path,
                file_name=os.path.basename(file_path),
                parent_entry_id=args.entry_id,
                mime_type=get_mime_type(file_path),
                file_size=os.path.getsize(file_path),
                content_hash=compute_file_hash(file_path)
            )
            tasks.append(task)
    else:
        parser.print_help()
        sys.exit(1)
    
    if not tasks:
        print('⚠️  没有找到要上传的文件')
        sys.exit(1)
    
    # 生成上传计划
    plan = uploader.generate_upload_plan(tasks)
    
    # 输出计划
    print_upload_plan(plan)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f'\n📄 计划已保存到: {args.output}')
    
    if args.dry_run:
        print('\n🔍 Dry Run 模式，未执行实际上传')
    else:
        print('\n💡 提示: 实际上传需要通过 AI 助手执行 MCP 调用')
        print('   将上面的 MCP 调用参数提供给 AI 助手即可完成上传')


if __name__ == '__main__':
    main()
