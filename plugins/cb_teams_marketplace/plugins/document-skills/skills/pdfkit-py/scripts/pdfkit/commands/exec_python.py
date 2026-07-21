#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 自定义代码执行器。
允许 AI 通过 MCP 协议直接执行 Python 代码片段，形成闭环。

安全机制：
1. 禁止 os.system / subprocess 等危险操作
2. 限制执行超时（默认 120 秒）
3. 限制输出大小（默认 1MB）
4. 只允许导入白名单中的模块
"""
import sys
import os
import tempfile

COMMAND = "exec_python"
DESCRIPTION = "安全执行用户 Python 代码片段，支持白名单模块导入和超时控制。"
CATEGORY = "meta"
PARAMS = [
    {"name": "code", "type": "str", "required": True, "help": "要执行的 Python 代码"},
    {"name": "timeout", "type": "int", "required": False, "default": 120, "help": "超时秒数"},
    {"name": "working_dir", "type": "str", "required": False, "help": "工作目录（默认系统临时目录）"},
    {"name": "variables", "type": "json", "required": False, "help": "预注入的变量（JSON 对象）"},
]

# 允许导入的模块白名单
ALLOWED_MODULES = {
    # PDF 处理库
    "fitz", "PyPDF2", "pypdf", "pdfplumber", "pikepdf",
    "reportlab", "pdf2docx", "camelot", "tabula",
    # 图片处理
    "PIL", "Pillow",
    # 数据处理
    "json", "csv", "re", "math", "statistics",
    "collections", "itertools", "functools",
    "datetime", "time", "hashlib", "base64",
    "io", "pathlib", "glob", "shutil", "tempfile",
    # 科学计算（可选）
    "numpy", "pandas",
}

# 禁止的内置函数
BLOCKED_BUILTINS = {"exec", "eval", "compile", "__import__"}

MAX_OUTPUT_SIZE = 1 * 1024 * 1024  # 1MB 输出限制


def safe_import(name, *args, **kwargs):
    """安全导入：只允许白名单中的模块"""
    top_level = name.split(".")[0]
    if top_level not in ALLOWED_MODULES:
        raise ImportError(
            f"模块 '{name}' 不在允许列表中。"
            f"允许的模块: {', '.join(sorted(ALLOWED_MODULES))}"
        )
    return __builtins__.__import__(name, *args, **kwargs) if hasattr(__builtins__, '__import__') else __import__(name, *args, **kwargs)


def handler(params):
    """执行用户提供的 Python 代码片段。

    Args:
        params: dict，包含：
            - code (str): 要执行的 Python 代码
            - timeout (int): 超时秒数，默认 120
            - working_dir (str): 工作目录，默认系统临时目录
            - variables (dict): 预注入的变量

    Returns:
        dict: 执行结果
    """
    import io
    import signal
    import traceback

    code = params.get("code", "")
    if not code or not code.strip():
        raise ValueError("'code' 参数不能为空")

    timeout = params.get("timeout", 120)
    working_dir = params.get("working_dir") or tempfile.gettempdir()
    variables = params.get("variables", {})

    # 安全检查：禁止危险操作
    dangerous_patterns = [
        "os.system", "subprocess", "os.popen", "os.exec",
        "shutil.rmtree(\"/\"", "shutil.rmtree('/'",
        "__import__('os').system", "__import__('subprocess')",
    ]
    for pattern in dangerous_patterns:
        if pattern in code:
            raise ValueError(f"代码包含禁止的操作: {pattern}")

    # 切换工作目录
    original_dir = os.getcwd()
    os.makedirs(working_dir, exist_ok=True)
    os.chdir(working_dir)

    # 构建安全的执行环境
    safe_builtins = {}
    import builtins
    for name in dir(builtins):
        if name not in BLOCKED_BUILTINS and not name.startswith("_"):
            safe_builtins[name] = getattr(builtins, name)
    safe_builtins["__import__"] = safe_import
    safe_builtins["__builtins__"] = safe_builtins

    # 预注入常用模块和变量
    exec_globals = {
        "__builtins__": safe_builtins,
        "__name__": "__main__",
    }

    # 注入用户变量
    if isinstance(variables, dict):
        exec_globals.update(variables)

    # 捕获 stdout
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()

    # 设置超时
    timed_out = False
    _use_sigalrm = hasattr(signal, "SIGALRM")
    old_handler = None

    if _use_sigalrm:
        # Unix: 使用 SIGALRM
        def timeout_handler(signum, frame):
            nonlocal timed_out
            timed_out = True
            raise TimeoutError(f"代码执行超时（{timeout}秒）")
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    else:
        # Windows: 使用 threading.Timer 中断主线程
        import threading
        import ctypes

        def _win_timeout():
            nonlocal timed_out
            timed_out = True
            # 向主线程注入 KeyboardInterrupt 以中断执行
            try:
                # 使用 c_ulonglong 以兼容 64 位 Windows（c_ulong 在 Windows 上只有 32 位）
                tid = threading.main_thread().ident
                ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_ulonglong(tid),
                    ctypes.py_object(TimeoutError),
                )
            except Exception:
                pass

        _timer = threading.Timer(timeout, _win_timeout)
        _timer.daemon = True
        _timer.start()

    exec_error = None
    exec_traceback = None
    return_value = None

    try:
        # 重定向 stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        try:
            # 使用 compile + exec 执行代码
            compiled = compile(code, "<mcp_exec>", "exec")
            exec(compiled, exec_globals)

            # 检查是否有 result 变量作为返回值
            if "result" in exec_globals:
                return_value = exec_globals["result"]
        except TimeoutError as e:
            exec_error = str(e) if str(e) else f"代码执行超时（{timeout}秒）"
        except Exception as e:
            exec_error = str(e)
            exec_traceback = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    finally:
        # 恢复工作目录和信号/定时器
        os.chdir(original_dir)
        if _use_sigalrm:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        else:
            _timer.cancel()

    # 构建结果
    stdout_text = captured_stdout.getvalue()
    stderr_text = captured_stderr.getvalue()

    # 限制输出大小
    if len(stdout_text) > MAX_OUTPUT_SIZE:
        stdout_text = stdout_text[:MAX_OUTPUT_SIZE] + f"\n... [输出被截断，超过 {MAX_OUTPUT_SIZE // 1024}KB 限制]"
    if len(stderr_text) > MAX_OUTPUT_SIZE:
        stderr_text = stderr_text[:MAX_OUTPUT_SIZE] + f"\n... [输出被截断]"

    result = {
        "success": exec_error is None,
        "stdout": stdout_text,
        "stderr": stderr_text,
    }

    if return_value is not None:
        try:
            # 尝试 JSON 序列化 result 变量
            import json
            json.dumps(return_value)  # 测试是否可序列化
            result["return_value"] = return_value
        except (TypeError, ValueError):
            result["return_value"] = str(return_value)

    if exec_error:
        result["error"] = exec_error
        if exec_traceback:
            result["traceback"] = exec_traceback

    # 收集执行过程中创建的文件
    if working_dir != tempfile.gettempdir():
        created_files = []
        for f in os.listdir(working_dir):
            fpath = os.path.join(working_dir, f)
            if os.path.isfile(fpath):
                created_files.append({
                    "path": fpath,
                    "size": os.path.getsize(fpath),
                })
        if created_files:
            result["created_files"] = created_files

    return result


if __name__ == "__main__":
    from pdfkit.base import main
    main(handler, params_schema=PARAMS, description=DESCRIPTION)
