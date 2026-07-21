# SessionStart hook: 把 financial-analysis 的 rules 作为 additionalContext 注入到会话。
# 纯 PowerShell 实现，不依赖 node/python。

$PluginRoot = $env:CODEBUDDY_PLUGIN_ROOT
if ([string]::IsNullOrWhiteSpace($PluginRoot)) {
  $PluginRoot = Split-Path -Parent $PSScriptRoot
}

$RulesFile = Join-Path $PluginRoot "rules/financial_analysis_rules.md"

# 规则文件缺失时静默退出，不影响会话启动。
if (-not (Test-Path -LiteralPath $RulesFile -PathType Leaf)) {
  exit 0
}

$Text = Get-Content -LiteralPath $RulesFile -Raw -Encoding UTF8
$Text = $Text -replace '(?s)^---\r?\n.*?\r?\n---\r?\n', ''
$Text = $Text.Trim()

$Payload = @{
  hookSpecificOutput = @{
    hookEventName = 'SessionStart'
    additionalContext = $Text
  }
  suppressOutput = $true
}

$Payload | ConvertTo-Json -Depth 5 -Compress
