# Install agent-browser on Windows PowerShell

$ErrorActionPreference = "Stop"

$AgentBrowser = Get-Command agent-browser -ErrorAction SilentlyContinue
if ($AgentBrowser) {
    Write-Host "agent-browser is already installed"
    exit 0
}

$Npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $Npm) {
    Write-Host "npm not found. Please install Node.js 18+ first: https://nodejs.org/"
    exit 1
}

Write-Host "Installing agent-browser..."
npm install -g agent-browser

if ($LASTEXITCODE -ne 0) {
    Write-Host "agent-browser npm installation failed"
    exit $LASTEXITCODE
}

Write-Host "Installing browser runtime..."
agent-browser install

if ($LASTEXITCODE -ne 0) {
    Write-Host "agent-browser browser installation failed"
    exit $LASTEXITCODE
}

Write-Host "agent-browser installation completed"
