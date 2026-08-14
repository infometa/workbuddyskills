# Windows 环境适配

> **加载时机**：`phases/0-context.md` 检测到 Windows 环境时加载本文件。
> **职责**：一次性完成 bash + python3 环境适配，**不修改任何脚本文件**。
> **Shell 约定**：适配完成后的 GNU 工具兼容性细节见 `shell-conventions.md` Windows 注意事项表。

---

## Step 1：检测 bash 可用性

> 已知是 Windows 环境（由 `0-context.md` 检测后加载本文件），只需判断 bash 是否已就绪。

```bash
python -c "import shutil; print('BASH_OK' if shutil.which('bash') else 'NO_BASH')"
```

| 输出 | 动作 |
|------|------|
| `BASH_OK` | bash 已就绪，跳到 Step 3（python3 包装） |
| `NO_BASH` | 进入 Step 2（自动安装 Git for Windows） |

---

## Step 2：无 bash 时自动安装 Git for Windows

> Git for Windows 提供 bash + GNU coreutils（`mktemp`/`date`/`grep`/`tr`/`seq`/`head`/`sleep` 等），是运行所有脚本的唯一前置依赖。
> 直接从 GitHub 下载安装包并静默安装，不依赖 winget 或其他包管理器。

### 2a. 下载并静默安装 Git for Windows（PowerShell）

```powershell
# 1. 从 GitHub API 获取最新版下载地址
$release = Invoke-RestMethod "https://api.github.com/repos/git-for-windows/git/releases/latest" -Headers @{ "User-Agent" = "agent-boost" }
$asset = $release.assets | Where-Object { $_.name -match "Git-.*-64-bit\.exe$" } | Select-Object -First 1
if (-not $asset) { Write-Error "未找到 Git for Windows 安装包"; exit 1 }

# 2. 下载安装包（约 50MB）
Write-Host " downloading $($asset.name) ..."
$installer = Join-Path $env:TEMP $asset.name
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installer

# 3. 静默安装（/VERYSILENT 无界面，/NORESTART 不重启）
Write-Host " installing ..."
Start-Process -FilePath $installer -ArgumentList "/VERYSILENT","/NORESTART","/SP-","/NOCANCEL","/CLOSEAPPLICATIONS","/RESTARTAPPLICATIONS" -Wait

# 4. 清理安装包
Remove-Item $installer -Force
Write-Host " done"
```

> 安装约 2-4 分钟（含下载）。若弹出 UAC 权限窗口，用户需点击"是"。
> 若网络无法访问 GitHub，提示用户手动下载安装 [Git for Windows](https://git-scm.com/download/win)。

### 2b. 安装后创建 `bash` 全局别名

> Git for Windows 的 `bash.exe` 在 `C:\Program Files\Git\bin\`，但该目录默认不在 PATH 中。
> 在 Python 的 `Scripts` 目录（Python 是 agent-boost 必需依赖，其 Scripts 目录一定在 PATH 中）创建一个 `bash.cmd` 包装脚本，使 `bash` 命令全局可用。

```powershell
# PowerShell 语法
$pyDir = Split-Path (Get-Command python).Source
New-Item -ItemType Directory -Force -Path "$pyDir\Scripts" | Out-Null
Set-Content -Path "$pyDir\Scripts\bash.cmd" -Value '@"C:\Program Files\Git\bin\bash.exe" %*'
# 验证
bash --version | head -1
bash -c "uname -s"   # 期望输出 MINGW64_NT-...
```

> **备选方案**（若 Python Scripts 目录不可写）：将 Git bin 目录加入用户 PATH：
> ```powershell
> $old = [Environment]::GetEnvironmentVariable("PATH", "User")
> [Environment]::SetEnvironmentVariable("PATH", "$old;C:\Program Files\Git\bin", "User")
> ```
> 加入后需**重启 CodeBuddy IDE**使新 PATH 生效。

### 2c. 验证 bash 可用

```bash
bash -c "uname -s"   # 期望输出 MINGW*
```

- 成功 → bash 环境就绪，继续 Step 3

---

## Step 3：创建 `python3` 包装

> Windows 上 Python 通常注册为 `python` 而非 `python3`，所有脚本内联调用 `python3` 会报 `command not found`。
> 在 Git Bash 的 `/usr/bin/` 下创建一个一行包装脚本即可，无需改任何现有脚本。

```bash
if ! command -v python3 &>/dev/null; then
  if command -v python &>/dev/null; then
    printf '#!/usr/bin/env bash\nexec python "$@"\n' > /usr/bin/python3
    chmod +x /usr/bin/python3
    echo "✅ 已创建 python3 → python 包装脚本"
  else
    echo "❌ 未找到 Python，请安装 Python 3 并加入 PATH"
  fi
else
  echo "✅ python3 已可用"
fi
```

---

## Step 4：最终验证

```bash
for cmd in bash python3 curl node; do
  command -v "$cmd" &>/dev/null && echo "✅ $cmd" || echo "⚠️ $cmd 缺失"
done
```

> **适配完成后，所有脚本调用方式不变**（`bash ${SKILL_DIR}/scripts/xxx.sh`）。Windows 下的路径分隔符等 shell 约定见 `shell-conventions.md` Windows 注意事项表。
