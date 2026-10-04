#Requires -Version 5.1
param([Parameter(Mandatory=$true)][ValidateSet('version','auth','status','unauth')][string]$Action)
$ErrorActionPreference = 'Stop'
& node (Join-Path $PSScriptRoot 'launch.cjs') $Action
exit $LASTEXITCODE
