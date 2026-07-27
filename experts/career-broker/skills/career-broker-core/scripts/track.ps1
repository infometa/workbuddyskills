# SKILL_TRACKER_BASE_VERSION=v2026.06
# =============================================================================
# skill-tracker: track.ps1
# Zero-dependency PowerShell reporter for Windows runtimes that don't have
# bash. Algorithmic twin of scripts/track.sh — produces the SAME A2 / A2_v2
# hash for the same machine + user.
#
# Why this file exists
# --------------------
# scripts/track.sh requires bash + curl + md5sum/openssl, none of which are
# guaranteed on native Windows. PowerShell IS guaranteed on every supported
# Windows version (5.1+ ships with the OS, 7+ ships with most dev runtimes).
# So on Windows we hand reporting to PowerShell, get the same Beacon payload,
# and the downstream skill author writes one extra line in SKILL.md instead
# of forcing every Windows user to install Git Bash / WSL.
#
# Algorithm (must match scripts/track.sh::generate_a2_v2 EXACTLY)
# ---------------------------------------------------------------
#   stable_id =
#       1. HKLM\SOFTWARE\Microsoft\Cryptography\MachineGuid
#       2. ~/.skill-tracker/device-id (auto-generated UUID, persisted)
#       3. literal "no-device-id"
#   A2 = A2_v2 = MD5("hostname:username:stable_id")
#
# We deliberately do NOT use a MAC fallback (the unix-side v1 also drops it
# on Windows now) because `getmac` / `Get-NetAdapter` enumeration order is
# not stable across Python uuid.getnode() / bash / PowerShell, which would
# produce different A2 values on the same machine.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\track.ps1 `
#       -AppKey "YOUR_KEY" -SkillName "my-skill" -EventName "skill_invoked"
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\track.ps1 `
#       "YOUR_KEY" "my-skill" "task_done" '{"status":"success"}'
#
# Exit codes:
#   0 - Always returns 0 (never blocks the caller, mirrors track.sh)
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true,  Position = 0)] [string] $AppKey,
    [Parameter(Mandatory = $true,  Position = 1)] [string] $SkillName,
    [Parameter(Mandatory = $true,  Position = 2)] [string] $EventName,
    [Parameter(Mandatory = $false, Position = 3)] [string] $JsonData = '',
    [Parameter(Mandatory = $false, Position = 4)] [string] $UserId   = $env:SKILL_TRACKER_USER_ID
)

$ErrorActionPreference = 'SilentlyContinue'
# Force the same UTF-8 byte-for-byte hashing input as bash / Python.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Configuration (mirrors track.sh) ---
$BeaconUrl     = 'https://otheve.beacon.qq.com/analytics/v2_upload'
$SdkId         = 'js'
$SdkVersion    = '4.3.4-web'
$AppVersion    = '1.0.0'
$PlatformId    = 3
$TimeoutSec    = 3

# --- Guard: reject placeholder app_key (mirrors track.sh) ---
$placeholders = @('0WEB072A8COTIIZC', 'your_app_key', 'YOUR-APP-KEY', '')
if ($placeholders -contains $AppKey) {
    Write-Host "[skill-tracker] WARNING: app_key is not configured (got '$AppKey'). Skipping event '$EventName'." -ForegroundColor Yellow
    Write-Host "[skill-tracker] Get a real Appkey at https://trackmate.woa.com/" -ForegroundColor Yellow
    exit 0
}

# --- Beacon special-character escaping (mirrors replace_symbol in track.sh) ---
function Convert-BeaconValue {
    param([string] $Value)
    if ([string]::IsNullOrEmpty($Value)) { return '' }
    return $Value.Replace('|', '%7C').Replace('&', '%26').Replace('=', '%3D').Replace('+', '%2B')
}

# --- Stable hostname / username (PowerShell guarantees these env vars) ---
function Get-Hostname {
    if ($env:COMPUTERNAME) { return $env:COMPUTERNAME }
    try { return [System.Net.Dns]::GetHostName() } catch { return 'unknown-host' }
}
function Get-UserName {
    if ($env:USERNAME) { return $env:USERNAME }
    try { return [System.Environment]::UserName } catch { return 'unknown-user' }
}

# --- Stable device id ---
# Priority must match scripts/track.sh::generate_a2_v2 EXACTLY:
#   1. MachineGuid (Windows-native, written by Windows itself)
#   2. ~/.skill-tracker/device-id (auto-generated UUID, persisted)
#   3. literal "no-device-id"
function Get-StableDeviceId {
    # 1. MachineGuid via registry
    try {
        $mg = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Cryptography' -Name MachineGuid -ErrorAction Stop).MachineGuid
        if ($mg) { return $mg.Trim() }
    } catch { }

    # 2. Persistent UUID file (~/.skill-tracker/device-id)
    #    USERPROFILE is what bash $HOME and Python os.path.expanduser("~") resolve
    #    to on Windows, so all three reporters land on the same file.
    $home_   = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath('UserProfile') }
    $didDir  = Join-Path $home_   '.skill-tracker'
    $didFile = Join-Path $didDir  'device-id'
    try {
        if (Test-Path $didFile) {
            $existing = (Get-Content -Path $didFile -Raw -ErrorAction Stop).Trim()
            if ($existing) { return $existing }
        }
        if (-not (Test-Path $didDir)) {
            New-Item -ItemType Directory -Path $didDir -Force | Out-Null
        }
        $newId = [guid]::NewGuid().ToString().ToLower()
        # -NoNewline keeps the file byte-identical to what `echo "$id" > file` from
        # bash produces after `tr -d '[:space:]'` is applied at read-time.
        Set-Content -Path $didFile -Value $newId -NoNewline -Encoding ascii
        return $newId
    } catch { }

    # 3. Final fallback
    return 'no-device-id'
}

# --- MD5 over UTF-8 bytes (matches bash md5sum and Python hashlib.md5) ---
function Get-MD5Hex {
    param([string] $InputString)
    $md5   = [System.Security.Cryptography.MD5]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($InputString)
        $hash  = $md5.ComputeHash($bytes)
        return -join ($hash | ForEach-Object { $_.ToString('x2') })
    } finally {
        $md5.Dispose()
    }
}

function Get-A2 {
    $h   = Get-Hostname
    $u   = Get-UserName
    $sid = Get-StableDeviceId
    return Get-MD5Hex "${h}:${u}:${sid}"
}

# --- Lightweight project-type detection (parallels track.sh) ---
function Get-ProjectType {
    param([string] $Dir)
    if (-not $Dir -or -not (Test-Path $Dir)) { return 'unknown' }
    if (Test-Path (Join-Path $Dir 'package.json'))     { return 'nodejs' }
    if (Test-Path (Join-Path $Dir 'go.mod'))           { return 'go' }
    if (Test-Path (Join-Path $Dir 'pyproject.toml'))   { return 'python' }
    if (Test-Path (Join-Path $Dir 'requirements.txt')) { return 'python' }
    if (Test-Path (Join-Path $Dir 'Cargo.toml'))       { return 'rust' }
    if (Test-Path (Join-Path $Dir 'pom.xml'))          { return 'java' }
    if (Test-Path (Join-Path $Dir 'build.gradle'))     { return 'java' }
    if (Test-Path (Join-Path $Dir 'CMakeLists.txt'))   { return 'cpp' }
    return 'unknown'
}

# --- Detect the AI runtime platform (parallels track.sh::detect_platform) ---
function Get-PlatformTag {
    if ($env:CLAUDE_CODE_ENTRYPOINT -or $env:CLAUDE_SKILL_DIR) { return 'claude-code' }
    if ($env:CODEBUDDY_ENV -or $env:CODEBUDDY_VERSION -or $env:CODEBUDDY_PROJECT_DIR) { return 'codebuddy' }
    if ($env:OPENCLAW_SHELL -or $env:OPENCLAW_ENV -or $env:OPENCLAW_VERSION) { return 'openclaw' }
    if ($env:BOXAI_ENV -or $env:BOXAI_VERSION) { return 'boxai' }
    # Distinguish raw PowerShell from a shell that just doesn't expose bash.
    return 'windows-ps'
}

# --- Detect runtime context: terminal vs cloud-sandbox ---
# Mirrors scripts/track.sh::detect_runtime. On Windows the answer is almost
# always 'terminal' (no production AI sandbox runs Windows containers), but
# we still honor SKILL_TRACKER_RUNTIME and the CI env vars so a self-hosted
# Windows GitHub Actions runner is correctly tagged as cloud-sandbox.
function Get-RuntimeTag {
    $override = $env:SKILL_TRACKER_RUNTIME
    if ($override) {
        $o = $override.Trim().ToLower()
        if ($o -eq 'terminal' -or $o -eq 'cloud-sandbox') { return $o }
    }
    if ($env:ANTHROPIC_SANDBOX -or $env:CODE_INTERPRETER -or $env:GITHUB_ACTIONS `
        -or $env:GITLAB_CI -or $env:JENKINS_URL -or $env:CIRCLECI `
        -or $env:BUILDKITE -or $env:CODEBUILD_BUILD_ID -or $env:RUNNER_OS `
        -or $env:CODESPACE_NAME) {
        return 'cloud-sandbox'
    }
    return 'terminal'
}

# --- Build mapValue ---
$projectDir   = if ($env:CLAUDE_SKILL_DIR) { $env:CLAUDE_SKILL_DIR }
                elseif ($env:CODEBUDDY_PROJECT_DIR) { $env:CODEBUDDY_PROJECT_DIR }
                else { (Get-Location).Path }

$platformTag  = Get-PlatformTag
$runtimeTag   = Get-RuntimeTag
$projectType  = Get-ProjectType -Dir $projectDir

$mapValue = [ordered]@{
    skill_name     = (Convert-BeaconValue $SkillName)
    skill_platform = (Convert-BeaconValue $platformTag)
    skill_runtime  = (Convert-BeaconValue $runtimeTag)
    skill_user     = (Convert-BeaconValue (Get-UserName))
    skill_os       = (Convert-BeaconValue 'Windows')
    arch           = (Convert-BeaconValue $env:PROCESSOR_ARCHITECTURE)
    project_dir    = (Convert-BeaconValue (Split-Path -Leaf $projectDir))
    project_type   = (Convert-BeaconValue $projectType)
}

# Merge user-supplied JSON data (if any). Errors are silent — never block.
if ($JsonData -and $JsonData.Trim()) {
    try {
        $extra = $JsonData | ConvertFrom-Json -ErrorAction Stop
        if ($extra) {
            foreach ($p in $extra.PSObject.Properties) {
                $mapValue[$p.Name] = (Convert-BeaconValue ([string]$p.Value))
            }
        }
    } catch { }
}

# --- Build common block (A2 + A2_v2 sidecar; A1 only if user_id provided) ---
$a2 = Get-A2
$common = [ordered]@{
    A2    = $a2
    A2_v2 = $a2  # Same algorithm — reported twice for parity with track.sh.
}
if ($UserId) { $common['A1'] = (Convert-BeaconValue $UserId) }

$payload = [ordered]@{
    appVersion  = $AppVersion
    sdkId       = $SdkId
    sdkVersion  = $SdkVersion
    mainAppKey  = (Convert-BeaconValue $AppKey)
    platformId  = $PlatformId
    common      = $common
    events      = @(
        [ordered]@{
            eventCode = (Convert-BeaconValue $EventName)
            eventTime = ([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds().ToString())
            mapValue  = $mapValue
        }
    )
}

$body = $payload | ConvertTo-Json -Depth 10 -Compress

# --- Async fire-and-forget POST ---
# Start-Job spins up a child PowerShell that survives this script's exit.
# Equivalent to nohup + disown in track.sh — when the IDE reaps the parent
# (Stop / SessionEnd hooks), the in-flight request still completes.
try {
    Start-Job -ScriptBlock {
        param($url, $payload, $timeout)
        try {
            Invoke-RestMethod -Uri $url -Method POST -Body $payload `
                -ContentType 'application/json;charset=UTF-8' `
                -TimeoutSec $timeout -ErrorAction SilentlyContinue | Out-Null
        } catch { }
    } -ArgumentList $BeaconUrl, $body, $TimeoutSec | Out-Null
} catch {
    # Fallback: if Start-Job is unavailable (locked-down policy),
    # send synchronously. Slower but still 0-exits.
    try {
        Invoke-RestMethod -Uri $BeaconUrl -Method POST -Body $body `
            -ContentType 'application/json;charset=UTF-8' `
            -TimeoutSec $TimeoutSec -ErrorAction SilentlyContinue | Out-Null
    } catch { }
}

exit 0
