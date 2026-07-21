#!/usr/bin/env pwsh

# run-cli.ps1 — Execute tencent-news-cli with --caller injected from SKILL.md.
# Usage: powershell scripts/run-cli.ps1 <command> [args...]

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  Write-Error "Error: $Message"
  exit 1
}

function Get-CommandOutput {
  param(
    [string]$Command,
    [string[]]$CommandArgs = @()
  )

  if ([string]::IsNullOrWhiteSpace($Command)) {
    return @{
      ExitCode = 1
      Output = "command path is empty"
    }
  }

  try {
    $output = & $Command @CommandArgs 2>&1
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    return @{
      ExitCode = $exitCode
      Output = ($output | Out-String).Trim()
    }
  } catch {
    $exitCode = if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) { [int]$LASTEXITCODE } else { 1 }
    return @{
      ExitCode = $exitCode
      Output = ($_ | Out-String).Trim()
    }
  }
}

function Resolve-CommandCliPath([string]$CliCommandName) {
  $resolved = $null
  try {
    $resolved = (Get-Command $CliCommandName -ErrorAction SilentlyContinue).Source
  } catch {
    return $null
  }

  if (-not $resolved) { return $null }

  try {
    $null = & $resolved help 2>&1
    if ($LASTEXITCODE -ne 0) { return $null }
  } catch {
    return $null
  }

  return $resolved
}

function Resolve-SkillCaller {
  $ScriptDir = Split-Path -Parent $MyInvocation.ScriptName
  $SkillDir = Split-Path -Parent $ScriptDir
  $skillMdPath = Join-Path $SkillDir "SKILL.md"

  if (-not (Test-Path $skillMdPath)) {
    Fail "SKILL.md not found: $skillMdPath"
  }

  $content = Get-Content -Path $skillMdPath -Raw

  # Extract frontmatter between --- markers
  if ($content -notmatch '(?s)^---\s*\r?\n(.*?)\r?\n---') {
    Fail "SKILL.md missing YAML frontmatter: $skillMdPath"
  }

  $frontmatter = $Matches[1]

  # Extract name field
  $skillName = $null
  if ($frontmatter -match '(?m)^name:\s*(.+)$') {
    $skillName = $Matches[1].Trim().Trim('"').Trim("'")
  }

  if (-not $skillName) {
    Fail "name field not found in $skillMdPath"
  }

  # Extract version field
  $skillVersion = $null
  if ($frontmatter -match '(?m)^version:\s*(.+)$') {
    $skillVersion = $Matches[1].Trim().Trim('"').Trim("'")
  }

  if ($skillVersion) {
    return "${skillName}_${skillVersion}"
  }

  return $skillName
}

function Compare-SemVer {
  param(
    [string]$Left,
    [string]$Right
  )

  # Normalize: remove quotes, leading v, pre-release suffix
  $Left = $Left.Trim().Trim('"').Trim("'") -replace '^v', '' -replace '-.*$', ''
  $Right = $Right.Trim().Trim('"').Trim("'") -replace '^v', '' -replace '-.*$', ''

  if (-not $Left -or -not $Right) { return $null }

  $leftParts = $Left.Split(".")
  $rightParts = $Right.Split(".")

  $length = [Math]::Max($leftParts.Length, $rightParts.Length)
  for ($i = 0; $i -lt $length; $i++) {
    $l = if ($i -lt $leftParts.Length) { [int]$leftParts[$i] } else { 0 }
    $r = if ($i -lt $rightParts.Length) { [int]$rightParts[$i] } else { 0 }
    if ($l -gt $r) { return 1 }
    if ($l -lt $r) { return -1 }
  }

  return 0
}

function Test-SupportsCallerArg([string]$CliPath) {
  $versionResult = Get-CommandOutput -Command $CliPath -CommandArgs @("version")
  if ($versionResult.ExitCode -ne 0) { return $false }

  try {
    $parsed = $versionResult.Output | ConvertFrom-Json
  } catch {
    return $false
  }

  $currentVersion = $parsed.current_version
  if (-not $currentVersion -or $currentVersion -isnot [string]) { return $false }
  $currentVersion = $currentVersion.Trim()
  if (-not $currentVersion) { return $false }

  $cmp = Compare-SemVer -Left $currentVersion -Right "1.0.12"
  return ($null -ne $cmp -and $cmp -ge 0)
}

# ── main ─────────────────────────────────────────────────────────────

if ($args.Count -eq 0) {
  Fail "missing CLI command"
}

# Check for manually passed --caller
foreach ($a in $args) {
  if ($a -eq "--caller" -or $a -like "--caller=*") {
    Fail "do not pass --caller manually; scripts/run-cli.ps1 injects it from SKILL.md"
  }
}

# ── resolve CLI path ─────────────────────────────────────────────────

$CliCommandName = "tencent-news-cli"
$CliFilename = "tencent-news-cli.exe"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir
$LocalCliPath = Join-Path $SkillDir $CliFilename

$InstallEnvName = "TENCENT_NEWS_INSTALL"
$InstallRoot = [Environment]::GetEnvironmentVariable($InstallEnvName, "Process")
if (-not $InstallRoot) {
  $InstallRoot = Join-Path $HOME ".tencent-news-cli"
}
$GlobalCliPath = Join-Path (Join-Path $InstallRoot "bin") $CliFilename

$CliPath = Resolve-CommandCliPath $CliCommandName

if (-not $CliPath) {
  if (Test-Path $GlobalCliPath) {
    $CliPath = $GlobalCliPath
  } elseif (Test-Path $LocalCliPath) {
    $CliPath = $LocalCliPath
  } else {
    Fail "cli not found. Run powershell scripts/cli-state.ps1 to inspect installation state first."
  }
}

# ── resolve caller and inject ────────────────────────────────────────

$Caller = Resolve-SkillCaller

if (Test-SupportsCallerArg $CliPath) {
  $finalArgs = @($args) + @("--caller", $Caller)
} else {
  $finalArgs = @($args)
}

# ── execute ──────────────────────────────────────────────────────────

& $CliPath @finalArgs
exit $LASTEXITCODE
