@echo off
rem 跨平台 launcher（Windows；macOS / Linux 见同名无扩展名文件）。
rem 定位与本文件同目录的 init_task.py，用可用的 python 解释器执行；
rem 不依赖当前工作目录；静默、永不阻塞主流程（失败也返回 0）。
where python >nul 2>&1
if %errorlevel%==0 (
  python "%~dp0init_task.py" %* 2>nul
) else (
  where py >nul 2>&1 && py "%~dp0init_task.py" %* 2>nul
)
exit /b 0
