@echo off
rem Launcher next to SKILL.md. Runs node on cli\cli.js. There is no fh.exe.
node "%~dp0cli\cli.js" --base-url https://travel.feiheair.com/api/portal --credentials-file credentials --client-name WorkBuddy auth login %*
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo [fh] command failed exit=%RC%. This file is next to SKILL.md.
  echo [fh] It runs: node cli\cli.js in this folder. node must be on PATH. Do not npm install to create a command named fh.
  echo [fh] Do not search the disk. Do not ask the user to find the skill folder.
  echo [fh] Login opens the system browser. Do not paste authorize URLs into chat or use a built-in browser.
  echo [fh] If the desktop browser did not open, retry with auth-login.cmd --manual. Keep this process in the foreground until it exits, up to 5 minutes.
  echo [fh] After any exit code, run auth-status.cmd first; if a token exists, do not login again.
  echo [fh] exit 3 means not logged in. Missing node or cli\cli.js means the runtime or the skill package is incomplete.
)
exit /b %RC%
