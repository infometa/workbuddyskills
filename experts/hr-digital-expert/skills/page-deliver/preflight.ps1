# =============================================================================
# page-deliver preflight (Windows)
# =============================================================================
# Purpose: Ensure co-available Node + npm (Node >= v18),
#          output NPM_BIN=... and NODE_BIN=... for the caller.
#
# Decision order (each tier requires node and npm from the same directory):
#   1) System PATH node >= v18 + same-dir npm.cmd/npm.ps1/npm -> use directly
#   1.5) ~/.workbuddy/binaries/node/ recursively search for node.exe >= v18 + same-dir npm -> use
#   2) Cache ~/.page-deliver/bin/node-win-x64/{node.exe,npm.cmd} exists -> use
#   3) Otherwise download Node v20.11.1 win-x64.zip (includes npm.cmd) + SHA256 verify
#
# Exit codes:
#   0 = success (last two lines: NPM_BIN=<path>, NODE_BIN=<path>, NODE_BIN always last line)
#   1 = network/download failure
#   2 = SHA256 verification failure
#   3 = extraction failure / path validation failure
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File preflight.ps1
# Caller gets NODE_BIN (backward compatible):
#   $line = powershell ... preflight.ps1 | Select-String '^NODE_BIN='
# Caller gets NPM_BIN:
#   $line = powershell ... preflight.ps1 | Select-String '^NPM_BIN='
# =============================================================================

$ErrorActionPreference = 'Stop'

# ---- constants -------------------------------------------------------------
$NODE_VERSION = 'v20.11.1'
$NODE_FILENAME = "node-$NODE_VERSION-win-x64"
$DOWNLOAD_URL = "https://nodejs.org/dist/$NODE_VERSION/$NODE_FILENAME.zip"
$SHASUMS_URL = "https://nodejs.org/dist/$NODE_VERSION/SHASUMS256.txt"
$MIN_MAJOR = 18

$CACHE_ROOT = Join-Path $env:USERPROFILE '.page-deliver\bin'
$CACHE_DIR = Join-Path $CACHE_ROOT 'node-win-x64'
$NODE_EXE = Join-Path $CACHE_DIR 'node.exe'

$ZIP_PATH = Join-Path $env:TEMP "page-deliver-node-$NODE_VERSION-$([guid]::NewGuid().ToString('N').Substring(0,8)).zip"
$EXTRACT_TMP = Join-Path $env:TEMP "page-deliver-extract-$([guid]::NewGuid().ToString('N').Substring(0,8))"

# ---- helpers ---------------------------------------------------------------

function Get-NodeMajor {
    param([string]$VersionString)
    if ($VersionString -match '^v?(\d+)\.') {
        return [int]$Matches[1]
    }
    return 0
}

function Test-NodeBin {
    param([string]$Bin)
    if (-not (Test-Path $Bin)) { return $false }
    try {
        $ver = & $Bin --version 2>$null
        if ($LASTEXITCODE -ne 0) { return $false }
        return ((Get-NodeMajor $ver) -ge $MIN_MAJOR)
    } catch {
        return $false
    }
}

# Find npm executable in the same directory as a node.exe
# Common names on Windows: npm.cmd (official), npm.ps1, npm (no extension)
function Find-NpmForNode {
    param([string]$NodeBin)
    if (-not $NodeBin) { return $null }
    $nodeDir = Split-Path -Parent $NodeBin
    if (-not $nodeDir) { return $null }
    $candidates = @('npm.cmd', 'npm.ps1', 'npm')
    foreach ($name in $candidates) {
        $candidate = Join-Path $nodeDir $name
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        $out = & cmd /c """$candidate"" --version" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) {
            return $candidate
        }
    }
    return $null
}

# Safely get npm version string (for logging only)
function Get-NpmVersion {
    param([string]$NpmBin)
    if (-not $NpmBin) { return 'unknown' }
    $v = & cmd /c """$NpmBin"" --version" 2>$null
    if ($LASTEXITCODE -eq 0 -and $v) { return ($v | Select-Object -First 1).ToString().Trim() }
    return 'unknown'
}

function Cleanup {
    if (Test-Path $ZIP_PATH) { Remove-Item $ZIP_PATH -Force -ErrorAction SilentlyContinue }
    if (Test-Path $EXTRACT_TMP) { Remove-Item $EXTRACT_TMP -Recurse -Force -ErrorAction SilentlyContinue }
}

# ---- step 1: system Node ---------------------------------------------------

$sysNode = Get-Command node -ErrorAction SilentlyContinue
if ($sysNode) {
    $sysVer = & node --version 2>$null
    if ($LASTEXITCODE -eq 0 -and (Get-NodeMajor $sysVer) -ge $MIN_MAJOR) {
        $sysNpm = Find-NpmForNode $sysNode.Source
        if (-not $sysNpm) {
            $pathNpm = Get-Command npm -ErrorAction SilentlyContinue
            if ($pathNpm) {
                $probe = & cmd /c """$($pathNpm.Source)"" --version" 2>$null
                if ($LASTEXITCODE -eq 0 -and $probe) { $sysNpm = $pathNpm.Source }
            }
        }
        if ($sysNpm) {
            $npmVer = Get-NpmVersion $sysNpm
            Write-Host "[preflight] using system Node: $($sysNode.Source) ($sysVer) + npm: $sysNpm ($npmVer)"
            Write-Output "NPM_BIN=$sysNpm"
            Write-Output "NODE_BIN=$($sysNode.Source)"
            exit 0
        }
        Write-Host "[preflight] system Node $sysVer OK but npm not found, falling back to managed"
    } else {
        Write-Host "[preflight] system Node $sysVer < v$MIN_MAJOR, falling back to managed"
    }
}

# ---- step 1.5: workbuddy Node ----------------------------------------------
# workbuddy installs Node under ~/.workbuddy/binaries/node with varying layouts:
#   versions/<ver>/node.exe
#   versions/<ver>/bin/node.exe
#   versions/<ver>.installing.<n>.__extract_temp__/node-v<ver>-win-x64/node.exe

$WORKBUDDY_NODE_ROOT = Join-Path $env:USERPROFILE '.workbuddy\binaries\node'

if (Test-Path $WORKBUDDY_NODE_ROOT) {
    $found = Get-ChildItem -Path $WORKBUDDY_NODE_ROOT -Filter 'node.exe' -File -Recurse -Depth 4 -ErrorAction SilentlyContinue |
            Select-Object -First 20
    foreach ($f in $found) {
        if (-not (Test-NodeBin $f.FullName)) { continue }
        $wbNpm = Find-NpmForNode $f.FullName
        if (-not $wbNpm) {
            Write-Host "[preflight] workbuddy Node $($f.FullName) has no usable npm sibling, skipping"
            continue
        }
        $wbVer = & $f.FullName --version 2>$null
        $npmVer = Get-NpmVersion $wbNpm
        Write-Host "[preflight] using workbuddy Node: $($f.FullName) ($wbVer) + npm: $wbNpm ($npmVer)"
        Write-Output "NPM_BIN=$wbNpm"
        Write-Output "NODE_BIN=$($f.FullName)"
        exit 0
    }
}

# ---- step 2: cached managed Node ------------------------------------------

if (Test-NodeBin $NODE_EXE) {
    $cachedNpm = Find-NpmForNode $NODE_EXE
    if ($cachedNpm) {
        $cachedVer = & $NODE_EXE --version 2>$null
        $npmVer = Get-NpmVersion $cachedNpm
        Write-Host "[preflight] using cached Node: $NODE_EXE ($cachedVer) + npm: $cachedNpm ($npmVer)"
        Write-Output "NPM_BIN=$cachedNpm"
        Write-Output "NODE_BIN=$NODE_EXE"
        exit 0
    }
    Write-Host "[preflight] cached Node found at $NODE_EXE but npm sibling missing, will re-download"
}

# ---- step 3: download + verify + extract ----------------------------------

Write-Host "[preflight] no usable Node found, downloading $NODE_VERSION ..."
New-Item -ItemType Directory -Path $CACHE_ROOT -Force | Out-Null

try {
    Write-Host "[preflight] GET $DOWNLOAD_URL"
    $start = Get-Date
    Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $ZIP_PATH -UseBasicParsing
    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    $sizeMB = [math]::Round((Get-Item $ZIP_PATH).Length / 1MB, 1)
    Write-Host "[preflight] downloaded ${sizeMB}MB in ${elapsed}s"
} catch {
    $errMsg = if ($_.Exception -and $_.Exception.Message) { $_.Exception.Message } else { "$_" }
    if (-not $errMsg) { $errMsg = '<no error message>' }
    Cleanup
    Write-Error "[preflight] download failed: $errMsg"
    exit 1
}

# SHA256 verify
try {
    Write-Host "[preflight] verifying SHA256 ..."
    $shasumsRaw = (Invoke-WebRequest -Uri $SHASUMS_URL -UseBasicParsing).Content
    $expected = $null
    foreach ($line in $shasumsRaw -split "`n") {
        $line = $line.Trim()
        if ($line.EndsWith(" $NODE_FILENAME.zip")) {
            $expected = ($line -split '\s+')[0]
            break
        }
    }
    if (-not $expected) {
        Cleanup
        Write-Error "[preflight] cannot find $NODE_FILENAME.zip in SHASUMS256.txt"
        exit 2
    }
    $actual = (Get-FileHash -Path $ZIP_PATH -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected.ToLower()) {
        Cleanup
        Write-Error "[preflight] SHA256 mismatch: expected=$expected actual=$actual"
        exit 2
    }
    Write-Host "[preflight] SHA256 OK"
} catch {
    $errMsg = if ($_.Exception -and $_.Exception.Message) { $_.Exception.Message } else { "$_" }
    if (-not $errMsg) { $errMsg = '<no error message>' }
    Cleanup
    Write-Error "[preflight] SHA256 verification failed: $errMsg"
    exit 2
}

# Extract
try {
    Write-Host "[preflight] extracting ..."
    New-Item -ItemType Directory -Path $EXTRACT_TMP -Force | Out-Null
    Expand-Archive -Path $ZIP_PATH -DestinationPath $EXTRACT_TMP -Force

    $innerList = @(Get-ChildItem -Path $EXTRACT_TMP -Directory -ErrorAction SilentlyContinue)
    if ($innerList.Count -eq 0) {
        Cleanup
        Write-Error "[preflight] zip layout unexpected: no top-level directory under $EXTRACT_TMP"
        exit 3
    }
    $inner = $innerList[0]
    if (-not $inner.FullName) {
        Cleanup
        Write-Error "[preflight] zip layout unexpected: empty inner path"
        exit 3
    }

    $cacheNew = "$CACHE_DIR.new"
    if (Test-Path $cacheNew) { Remove-Item $cacheNew -Recurse -Force }
    Move-Item -LiteralPath $inner.FullName -Destination $cacheNew

    $newNode = Join-Path $cacheNew 'node.exe'
    if (-not (Test-NodeBin $newNode)) {
        Remove-Item $cacheNew -Recurse -Force -ErrorAction SilentlyContinue
        Cleanup
        Write-Error "[preflight] extracted node.exe failed self-check at $newNode"
        exit 3
    }
    $newNpm = Find-NpmForNode $newNode
    if (-not $newNpm) {
        Remove-Item $cacheNew -Recurse -Force -ErrorAction SilentlyContinue
        Cleanup
        Write-Error "[preflight] extracted package missing npm next to $newNode"
        exit 3
    }

    if (Test-Path $CACHE_DIR) { Remove-Item $CACHE_DIR -Recurse -Force }
    Move-Item -LiteralPath $cacheNew -Destination $CACHE_DIR
} catch {
    $errMsg = if ($_.Exception -and $_.Exception.Message) { $_.Exception.Message } else { "$_" }
    if (-not $errMsg) { $errMsg = '<no error message>' }
    Cleanup
    Write-Error "[preflight] extract failed: $errMsg"
    exit 3
}

Cleanup

$ver = & $NODE_EXE --version
$NPM_EXE = Find-NpmForNode $NODE_EXE
if (-not $NPM_EXE) {
    Write-Error "[preflight] managed Node ready but npm missing next to $NODE_EXE"
    exit 3
}
$npmVer = Get-NpmVersion $NPM_EXE
Write-Host "[preflight] managed Node ready: $NODE_EXE ($ver) + npm: $NPM_EXE ($npmVer)"
Write-Output "NPM_BIN=$NPM_EXE"
Write-Output "NODE_BIN=$NODE_EXE"
exit 0
