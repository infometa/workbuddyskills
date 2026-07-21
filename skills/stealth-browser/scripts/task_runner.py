# -*- coding: utf-8 -*-
"""
稳定任务执行器 - 支持断点续传、超时重试、进度保存
"""
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

TASK_DIR = Path.home() / '.clawdbot' / 'tasks'
TASK_DIR.mkdir(parents=True, exist_ok=True)

class TaskRunner:
    def __init__(self, task_name):
        self.task_name = task_name
        self.state_file = TASK_DIR / f'{task_name}_state.json'
        self.log_file = TASK_DIR / f'{task_name}.log'
        self.state = self._load_state()
    
    def _load_state(self):
        if self.state_file.exists():
            return json.loads(self.state_file.read_text(encoding='utf-8'))
        return {
            'task_name': self.task_name,
            'status': 'pending',
            'progress': 0,
            'total': 0,
            'completed_items': [],
            'failed_items': [],
            'last_update': None,
            'result': None
        }
    
    def save_state(self):
        self.state['last_update'] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def log(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{timestamp}] {msg}\n'
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(line)
        print(msg)
    
    def set_total(self, total):
        self.state['total'] = total
        self.save_state()
    
    def mark_completed(self, item_id, result=None):
        self.state['completed_items'].append(item_id)
        self.state['progress'] = len(self.state['completed_items'])
        if result:
            if 'results' not in self.state:
                self.state['results'] = {}
            self.state['results'][str(item_id)] = result
        self.save_state()
    
    def mark_failed(self, item_id, error):
        self.state['failed_items'].append({'id': item_id, 'error': str(error)})
        self.save_state()
    
    def is_completed(self, item_id):
        return item_id in self.state['completed_items']
    
    def get_progress(self):
        return self.state['progress'], self.state['total']
    
    def finish(self, result=None):
        self.state['status'] = 'completed'
        self.state['result'] = result
        self.save_state()
        self.log(f'Task completed: {self.task_name}')
    
    def fail(self, error):
        self.state['status'] = 'failed'
        self.state['error'] = str(error)
        self.save_state()
        self.log(f'Task failed: {error}')


def run_with_timeout(cmd, timeout=60, task_name=None):
    """运行命令，支持超时和重试"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                print(f'超时，重试 {attempt + 2}/{max_retries}...')
                time.sleep(2)
            else:
                return {'success': False, 'error': 'timeout', 'stdout': '', 'stderr': ''}
        except Exception as e:
            return {'success': False, 'error': str(e), 'stdout': '', 'stderr': ''}


def list_tasks():
    """列出所有任务状态"""
    tasks = []
    for f in TASK_DIR.glob('*_state.json'):
        try:
            state = json.loads(f.read_text(encoding='utf-8'))
            tasks.append({
                'name': state.get('task_name'),
                'status': state.get('status'),
                'progress': f"{state.get('progress', 0)}/{state.get('total', 0)}",
                'last_update': state.get('last_update')
            })
        except:
            pass
    return tasks


def get_task_state(task_name):
    """获取任务状态"""
    state_file = TASK_DIR / f'{task_name}_state.json'
    if state_file.exists():
        return json.loads(state_file.read_text(encoding='utf-8'))
    return None


def clear_task(task_name):
    """清除任务状态"""
    state_file = TASK_DIR / f'{task_name}_state.json'
    log_file = TASK_DIR / f'{task_name}.log'
    if state_file.exists():
        state_file.unlink()
    if log_file.exists():
        log_file.unlink()
    print(f'已清除任务: {task_name}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python task_runner.py list         - 列出所有任务')
        print('  python task_runner.py status <name> - 查看任务状态')
        print('  python task_runner.py clear <name>  - 清除任务')
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        tasks = list_tasks()
        if tasks:
            print(f'{"任务名":<20} {"状态":<12} {"进度":<15} {"最后更新"}')
            print('-' * 70)
            for t in tasks:
                print(f"{t['name']:<20} {t['status']:<12} {t['progress']:<15} {t['last_update'] or 'N/A'}")
        else:
            print('没有任务记录')
    
    elif cmd == 'status' and len(sys.argv) > 2:
        state = get_task_state(sys.argv[2])
        if state:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        else:
            print('任务不存在')
    
    elif cmd == 'clear' and len(sys.argv) > 2:
        clear_task(sys.argv[2])
