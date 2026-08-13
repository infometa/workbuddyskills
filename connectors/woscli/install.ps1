# woscli installer for Windows
# Usage: powershell -Command "irm <BASE>/install.ps1 | iex"
$ErrorActionPreference = "Stop"

$WoscliHome = Join-Path $env:USERPROFILE ".woscli"
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'amd64' }
$ExeUrl = "https://ipaas-huawei-cloud-1252328573.cos.ap-shanghai.myqcloud.com/wai/woscli-windows-$arch.exe"
$ExePath = Join-Path $WoscliHome "woscli.exe"

Write-Host "==> Installing woscli to $WoscliHome"
New-Item -ItemType Directory -Force -Path $WoscliHome | Out-Null

Write-Host "==> Downloading woscli..."
# -UseBasicParsing is REQUIRED: WorkBuddy runs this in non-interactive PowerShell,
# where the default HTML parser (Internet Explorer) is unavailable and would abort.
Invoke-WebRequest -Uri $ExeUrl -OutFile $ExePath -UseBasicParsing
Write-Host "==> Installed: $(Join-Path $WoscliHome 'woscli.exe')"

# Persist to the user PATH (applies to all NEW terminals / processes)
$oldPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($oldPath -notlike "*$WoscliHome*") {
  $newPath = if ($oldPath) { "$oldPath;$WoscliHome" } else { $WoscliHome }
  [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
  Write-Host "    added woscli to User PATH"
}

# Expose in the CURRENT session so subsequent commands work immediately
$env:Path = "$WoscliHome;$env:Path"

if (Get-Command woscli.exe -ErrorAction SilentlyContinue) {
  Write-Host "==> woscli is ready"
} else {
  Write-Host "==> woscli installed. Run 'woscli.exe' in a new terminal if not found here."
}
Write-Host "Done."
