@echo off
setlocal EnableDelayedExpansion
REM pdfkit - environment setup (Windows)
REM Usage: scripts\setup.bat          core dependencies only
REM        scripts\setup.bat --all    all dependencies

chcp 65001 >nul 2>nul

set "SCRIPTS_DIR=%~dp0"
if "!SCRIPTS_DIR:~-1!"=="\" set "SCRIPTS_DIR=!SCRIPTS_DIR:~0,-1!"
set "VENV_DIR=!SCRIPTS_DIR!\venv"
set "REQ_FILE=!SCRIPTS_DIR!\requirements.txt"
set "REQ_OPT_FILE=!SCRIPTS_DIR!\requirements-optional.txt"
set "LOCAL_PYTHON_DIR=!SCRIPTS_DIR!\.python"
set "INSTALL_ALL=0"
set "PY_VERSION=3.13.13"
set "RELEASE_TAG=20260414"

for %%a in (%*) do (
    if "%%a"=="--all" set "INSTALL_ALL=1"
)

echo === pdfkit environment setup (Windows) ===
echo.

REM --- 1. Detect Python 3.10+ ---
set "PYTHON="
set "PV="

REM 1a. Check local downloaded Python
if exist "!LOCAL_PYTHON_DIR!\python.exe" (
    for /f "tokens=*" %%v in ('"!LOCAL_PYTHON_DIR!\python.exe" -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" 2^>nul') do set "PV=%%v"
    if defined PV (
        for /f "tokens=1,2 delims=." %%a in ("!PV!") do (
            if %%a GEQ 3 if %%b GEQ 10 (
                set "PYTHON=!LOCAL_PYTHON_DIR!\python.exe"
                echo [OK] Python !PV! - local
                goto :found_python
            )
        )
    )
    set "PV="
)

REM 1b. Check system Python (python, py launcher)
for %%c in (python py) do (
    where %%c >nul 2>nul
    if !errorlevel! EQU 0 (
        for /f "tokens=*" %%v in ('%%c -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" 2^>nul') do set "PV=%%v"
        if defined PV (
            for /f "tokens=1,2 delims=." %%a in ("!PV!") do (
                if %%a GEQ 3 if %%b GEQ 10 (
                    set "PYTHON=%%c"
                    echo [OK] Python !PV! - system
                    goto :found_python
                )
            )
        )
        set "PV="
    )
)

REM 1c. Not found, download Python
echo [!] Python 3.10+ not found. Downloading standalone Python !PY_VERSION!...
call :download_python
if !errorlevel! NEQ 0 (
    echo [ERROR] Failed to download Python.
    echo   Please install manually: https://www.python.org/downloads/
    exit /b 1
)
set "PYTHON=!LOCAL_PYTHON_DIR!\python.exe"
for /f "tokens=*" %%v in ('"!PYTHON!" -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" 2^>nul') do set "PV=%%v"
echo [OK] Python !PV! - downloaded

:found_python

REM --- 2. Create venv ---
set "VPYTHON=!VENV_DIR!\Scripts\python.exe"

if not exist "!VENV_DIR!" (
    echo   Creating venv...
    "!PYTHON!" -m venv "!VENV_DIR!"
    if not exist "!VPYTHON!" (
        echo [ERROR] venv creation failed
        exit /b 1
    )
    "!VPYTHON!" -m pip --version >nul 2>nul
    if !errorlevel! NEQ 0 (
        "!VPYTHON!" -m ensurepip --upgrade >nul 2>nul
    )
    echo [OK] venv created
) else (
    echo [OK] venv already exists
)

REM --- 3. Install core dependencies ---
echo.
echo Installing core Python dependencies...
"!VPYTHON!" -m pip install -r "!REQ_FILE!" --quiet
if !errorlevel! NEQ 0 (
    echo [WARN] Some packages may have failed to install, retrying with verbose output...
    "!VPYTHON!" -m pip install -r "!REQ_FILE!"
    if !errorlevel! NEQ 0 (
        echo [WARN] Core dependency installation had errors, continuing setup...
    )
)
echo [OK] Core dependencies installed

REM --- 3.1 Optional dependencies ---
if "!INSTALL_ALL!"=="1" (
    if exist "!REQ_OPT_FILE!" (
        echo.
        echo Installing optional dependencies...
        "!VPYTHON!" -m pip install -r "!REQ_OPT_FILE!" --quiet
        if !errorlevel! NEQ 0 (
            echo [WARN] Some optional packages failed, retrying...
            "!VPYTHON!" -m pip install -r "!REQ_OPT_FILE!"
        )
        echo [OK] Optional dependencies installed
    )
)

REM --- 3.2 Download bundled font ---
set "FONT_DIR=!SCRIPTS_DIR!\..\fonts"
set "FONT_FILE=!FONT_DIR!\NotoSansSC-Regular.ttf"
set "FONT_URL=https://docs.gtimg.com/tdocs-font-source/test/NotoSansSC-Regular.ttf"

if exist "!FONT_FILE!" (
    echo [OK] Bundled font already exists
) else (
    echo.
    echo Downloading bundled font (NotoSansSC-Regular^)...
    if not exist "!FONT_DIR!" mkdir "!FONT_DIR!"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!FONT_URL!' -OutFile '!FONT_FILE!' -UseBasicParsing } catch { Write-Host $_.Exception.Message; exit 1 }"
    if exist "!FONT_FILE!" (
        echo [OK] Bundled font downloaded
    ) else (
        echo [--] Font download failed (non-fatal, will use system fonts^)
    )
)

REM --- 4. Smoke test ---
echo.
echo Verifying...
"!VPYTHON!" -c "import fitz; print('  PyMuPDF ' + fitz.version[0])"
if !errorlevel! NEQ 0 (
    echo [ERROR] PyMuPDF import failed
    echo   Try: "!VPYTHON!" -m pip install PyMuPDF
    exit /b 1
)
echo [OK] PyMuPDF OK

"!VPYTHON!" "!SCRIPTS_DIR!\pdfkit.py" help >nul 2>nul
if !errorlevel! NEQ 0 (
    echo [ERROR] pdfkit.py failed to run, check the above errors
    exit /b 1
)
echo [OK] pdfkit.py ready

REM --- 5. Check external tools ---
echo.
echo Optional external tools (not required):
where gs >nul 2>nul
if !errorlevel! EQU 0 (echo   [OK] gs - Ghostscript) else (echo   [--] gs - not found)
where tesseract >nul 2>nul
if !errorlevel! EQU 0 (echo   [OK] tesseract - OCR) else (echo   [--] tesseract - not found)
where soffice >nul 2>nul
if !errorlevel! EQU 0 (echo   [OK] soffice - LibreOffice) else (echo   [--] soffice - not found)

REM --- 6. Remove SKILL.md setup section ---
set "SKILL_MD=!SCRIPTS_DIR!\..\SKILL.md"
if exist "!SKILL_MD!" (
    findstr /c:"END_SETUP" "!SKILL_MD!" >nul 2>nul
    if !errorlevel! EQU 0 (
        "!VPYTHON!" -c "import re,pathlib;p=pathlib.Path(r'!SKILL_MD!');t=p.read_text('utf-8');t=re.sub(r'##[^\n]*环境初始化.*?<!-- END_SETUP -->\n?','',t,flags=re.DOTALL);p.write_text(t,'utf-8')" 2>nul
        echo [OK] SKILL.md setup section removed
    )
)

REM --- 7. Done ---
echo.
echo === Setup complete ===
echo.

if "!INSTALL_ALL!"=="0" (
    echo Note: Only core dependencies installed.
    echo   To install all optional dependencies: %~f0 --all
    echo.
)

echo Usage:
echo   "!VPYTHON!" "!SCRIPTS_DIR!\pdfkit.py" help
exit /b 0


REM ============================================================
REM  Download Python (python-build-standalone)
REM ============================================================
:download_python
set "DL_BASE_URL=https://github.com/astral-sh/python-build-standalone/releases/download/!RELEASE_TAG!"

if "!PROCESSOR_ARCHITECTURE!"=="AMD64" (
    set "DL_ARCH=x86_64"
) else if "!PROCESSOR_ARCHITECTURE!"=="ARM64" (
    set "DL_ARCH=aarch64"
) else (
    echo [ERROR] Unsupported architecture: !PROCESSOR_ARCHITECTURE!
    exit /b 1
)

set "DL_URL=!DL_BASE_URL!/cpython-!PY_VERSION!+!RELEASE_TAG!-!DL_ARCH!-pc-windows-msvc-install_only.tar.gz"
set "DL_TMP=!SCRIPTS_DIR!\.python_download.tar.gz"

echo   URL: !DL_URL!
echo   Downloading...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '!DL_URL!' -OutFile '!DL_TMP!' -UseBasicParsing } catch { Write-Host $_.Exception.Message; exit 1 }"
if !errorlevel! NEQ 0 (
    echo [ERROR] Download failed
    del "!DL_TMP!" 2>nul
    exit /b 1
)

echo   Extracting...
if not exist "!LOCAL_PYTHON_DIR!" mkdir "!LOCAL_PYTHON_DIR!"

tar -xzf "!DL_TMP!" -C "!LOCAL_PYTHON_DIR!" --strip-components=1 2>nul
if !errorlevel! NEQ 0 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "tar -xzf '!DL_TMP!' -C '!LOCAL_PYTHON_DIR!' --strip-components=1"
)
del "!DL_TMP!" 2>nul

if exist "!LOCAL_PYTHON_DIR!\python.exe" (
    echo   [OK] Python !PY_VERSION! installed to !LOCAL_PYTHON_DIR!
    exit /b 0
) else (
    echo [ERROR] Extract failed
    rmdir /s /q "!LOCAL_PYTHON_DIR!" 2>nul
    exit /b 1
)
