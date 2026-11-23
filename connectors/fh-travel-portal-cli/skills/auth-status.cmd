@echo off
rem Launcher next to SKILL.md. Runs node on cli\cli.js. There is no fh.exe.
node "%~dp0cli\cli.js" --base-url https://travel.feiheair.com/api/portal --credentials-file credentials auth status
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo [fh] status failed exit=%RC%. This file is next to SKILL.md.
  echo [fh] It runs: node cli\cli.js in this folder. node must be on PATH.
  echo [fh] Do not search the disk. exit 3 means not logged in. Then run auth-login.cmd in the foreground.
)
exit /b %RC%
