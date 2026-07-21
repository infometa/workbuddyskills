<#
.SYNOPSIS
    Windows 系统日志收集工具 - PowerShell版本

.DESCRIPTION
    收集Windows系统的各种日志和安全信息，用于安全分析和勒索病毒溯源

.PARAMETER StepChoice
    指定要执行的步骤（0-8），默认执行所有步骤

.PARAMETER DaysBack
    指定要收集日志的时间范围（天数），默认为7天

.PARAMETER MaxEventCount
    指定要收集的最大事件数量，防止日志文件过大

.PARAMETER UsnMultiplier
    USN日志收集倍数因子，避免USN收集时间过久

.EXAMPLE
    .\get_log_all_in_one.ps1
    执行所有收集步骤

.EXAMPLE
    .\get_log_all_in_one.ps1 -StepChoice 5
    只执行步骤5（收集关键安全事件）

.EXAMPLE
    .\get_log_all_in_one.ps1 -DaysBack 30
    收集最近30天的日志

.EXAMPLE
    .\get_log_all_in_one.ps1 -MaxEventCount 10000
    收集最多10000条事件

.EXAMPLE
    .\get_log_all_in_one.ps1 -MaxEventCount 10000 -UsnMultiplier 0.01
    收集最多100条USN事件
#>

# 在参数定义部分增加时间范围参数
[CmdletBinding()]
param(
[Parameter(Mandatory = $false)]
[ValidateRange(0, 9)]
    [int]$StepChoice,

    [Parameter(Mandatory = $false)]
    [int]$DaysBack = 7,  # 默认从最近7天的日志开始收集

    [Parameter(Mandatory = $false)]
    [int]$DaysRange = 7,  # 默认收集7天的日志，即从前$DaysBack天开始，收集7天的日志。如果数字小于等于0，则收集到现在。

    [Parameter(Mandatory = $false)]
    [int]$MaxEventCount = 2000,  # 最大事件数量限制

    [Parameter(Mandatory = $false)]
    [double]$UsnMultiplier = 0.2 # USN日志收集倍数因子：引入原因为USN日志计算时间非常久。USN不受时间参数控制。
)

#Requires -RunAsAdministrator

# 设置PowerShell使用UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 保存脚本级别的参数绑定状态，供函数内部使用（函数内 $PSBoundParameters 只包含函数自身参数）
$Script:StepChoiceProvided = $PSBoundParameters.ContainsKey('StepChoice')
$Script:StepChoiceValue = if ($Script:StepChoiceProvided) { $StepChoice } else { $null }
$Script:DaysBackProvided = $PSBoundParameters.ContainsKey('DaysBack')

# 严格模式
Set-StrictMode -Version Latest

# 错误处理偏好
# $ErrorActionPreference = 'Continue'
# $WarningPreference = 'Continue'

# 脚本配置
$Script:Config = @{
    ScriptName = "Windows 系统日志收集工具"
    Version = "3.0"
}

# 步骤定义
$Script:Steps = @{
    1 = "收集系统基本信息"
    2 = "收集关键安全事件和关键系统事件"
    3 = "收集进程和服务详细信息"
    4 = "收集网络配置信息"
    5 = "检查并收集IIS日志"
    6 = "收集自启动项信息"
    7 = "收集USN日志（文件系统变更记录）"
    8 = "检查常见文件夹二进制数字签名"
    9 = "收集 PSReadLine 命令历史"
}

# 显示脚本信息
function Show-ScriptHeader
{
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $Script:Config.ScriptName -ForegroundColor Green
    Write-Host "版本: $( $Script:Config.Version )" -ForegroundColor Yellow
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
}

# 显示菜单
function Show-Menu
{
    Write-Host "请选择要执行的步骤（初始化和清理必定执行）：" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "0 或 回车 - 执行所有步骤（默认）" -ForegroundColor Green

    foreach ($step in $Script:Steps.GetEnumerator() | Sort-Object Key)
    {
        Write-Host "  $($step.Key.ToString().PadLeft(2) ) - $( $step.Value )" -ForegroundColor White
    }
    Write-Host ""
}

# 获取用户选择
function Get-UserChoice
{
    # 使用脚本级别变量判断是否通过命令行参数指定了步骤
    if ($Script:StepChoiceProvided)
    {
        return $Script:StepChoiceValue
    }

    Show-Menu

    $choice = Read-Host "请输入选择（0-9）"

    if ([string]::IsNullOrWhiteSpace($choice) -or $choice -eq "0")
    {
        return 0
    }

    if ($choice -match '^\d+$' -and [int]$choice -ge 0 -and [int]$choice -le 9)
    {
        return [int]$choice
    }

    Write-Warning "无效选择，将执行所有步骤"
    return 0
}

# 初始化参数
function Initialize-Parameters
{
    if ($DaysRange -le 0 -or $DaysRange -gt $DaysBack)
    {
        $script:DaysRange = $DaysBack
    }
}

# 创建输出目录结构
function Initialize-OutputDirectories
{
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

    # 修复PowerShell 7中路径获取问题
    $scriptPath = $null

    # 尝试多种方式获取脚本路径
    try
    {
        if ($MyInvocation.MyCommand.Path -and (Test-Path $MyInvocation.MyCommand.Path))
        {
            $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
        }
    }
    catch
    {
        # 忽略错误，继续尝试其他方法
    }

    if (-not $scriptPath -and $PSScriptRoot)
    {
        $scriptPath = $PSScriptRoot
    }

    if (-not $scriptPath)
    {
        $scriptPath = $PWD.Path
    }

    # 确保路径有效
    if (-not $scriptPath -or -not (Test-Path $scriptPath))
    {
        $scriptPath = $PWD.Path
    }


    # 确保脚本路径不为空
    if (-not $scriptPath)
    {
        Write-Error "无法获取脚本路径，脚本将无法正常运行"
        exit 1
    }

    $Script:Directories = @{
        Output = $scriptPath # Join-Path $scriptPath "logs_$( $env:COMPUTERNAME )_$timestamp"
        SystemLogs = $null
        UsnLogs = $null
        StartupItems = $null
    }

    # 验证$Script:Directories是否正确初始化
    if (-not $Script:Directories -or -not $Script:Directories.Output)
    {
        Write-Error "目录结构初始化失败"
        exit 1
    }

    #    # 创建主输出目录
    #    $Script:Directories.SystemLogs = Join-Path $Script:Directories.Output "system_logs"
    #    $Script:Directories.UsnLogs = Join-Path $Script:Directories.Output "usn_logs"
    #    $Script:Directories.StartupItems = Join-Path $Script:Directories.Output "startup_items"
    #
    #    # 创建所有必要的目录
    #    foreach ($dir in $Script:Directories.Values)
    #    {
    #        if ($dir -and -not (Test-Path $dir))
    #        {
    #            New-Item -ItemType Directory -Path $dir -Force | Out-Null
    #        }
    #    }

    Write-Host "[信息] 脚本执行目录: $( $Script:Directories.Output )" -ForegroundColor Cyan
    #    Write-Host "[信息] 系统日志目录: $( $Script:Directories.SystemLogs )" -ForegroundColor Cyan
    Write-Host ""
}

function Check-Weaxor()
{
    # 检查常见用户目录
    $commonPaths = @(
        "$env:USERPROFILE\FILE RECOVERY.txt",
        "$env:PUBLIC\FILE RECOVERY.txt",
        "$env:HomeDrive\Users\*\FILE RECOVERY.txt",
        "$env:HomeDrive\Users\*\Desktop\FILE RECOVERY.txt",
        "$env:HomeDrive\Users\*\Documents\FILE RECOVERY.txt"
    )

    foreach ($pathPattern in $commonPaths)
    {
        try
        {
            if ($pathPattern -like "*\*")
            {
                # 处理通配符路径
                $files = Get-ChildItem -Path $pathPattern -ErrorAction SilentlyContinue
                if ($files)
                {
                    Write-Verbose "通过通配符找到FILE RECOVERY.txt: $($files[0].FullName)"
                    return $files[0]
                }
            }
            else
            {
                # 处理具体路径
                if (Test-Path $pathPattern)
                {
                    Write-Verbose "通过常见路径找到FILE RECOVERY.txt: $pathPattern"
                    return Get-Item $pathPattern
                }
            }
        }
        catch
        {
            Write-Verbose "检查路径 $pathPattern 时出错: $($_.Exception.Message)"
            continue
        }
    }
    return $null
}

function Check-Main()
{
    $fileInfo = Check-Weaxor
    if ($fileInfo)
    {
        $lastModified = $fileInfo.LastWriteTime
        Write-Host "检测到Weaxor - FILE RECOVERY.txt 最后修改时间: $lastModified"

        # 检查用户是否显式指定了DaysBack参数
        if ($Script:DaysBackProvided)
        {
            Write-Host "用户已指定DaysBack参数为 $DaysBack 天，保持用户设定" -ForegroundColor Yellow
        }
        else
        {
            # 用户未指定DaysBack，使用智能调整
            $startTime = $lastModified.AddDays(-$DaysRange + 1)
            $nowTime = Get-Date
            $script:DaysBack = $nowTime.Subtract($startTime).Days  # 使用script:作用域修改参数

            Write-Host "智能调整日志收集时间范围: 收集自 $startTime 起 $script:DaysRange 天的日志" -ForegroundColor Yellow
        }
    }
    else
    {
        Write-Verbose "未检测到Weaxor勒索软件"
    }
}

# ══════════════════════════════════════════════════════════════════════
# 纯文本报告格式化函数
# ══════════════════════════════════════════════════════════════════════

<#
 .SYNOPSIS
    将单个值转换为适合报告输出的字符串
 .DESCRIPTION
    处理 null、布尔、DateTime、数组、字符串等各种类型，返回可直接嵌入报告的文本
#>
function Format-Value {
    param($Value)
    if ($null -eq $Value) { return "(空)" }
    if ($Value -is [bool]) { if ($Value) { return "True" } else { return "False" } }
    if ($Value -is [datetime]) { return $Value.ToString("yyyy-MM-dd HH:mm:ss") }
    if ($Value -is [byte[]]) { return "[Binary: $($Value.Length) bytes]" }
    $s = "$Value" -replace '[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', ''
    return $s
}

<#
 .SYNOPSIS
    获取对象的属性名列表（兼容 PSCustomObject、OrderedDictionary、Hashtable）
 .DESCRIPTION
    仅展开字典类型和 PSCustomObject；拒绝一般 .NET 对象（如 IPAddress、TimeSpan、
    枚举值等），避免 Format-KeyValueBlock 递归进入 .NET 对象图导致调用深度溢出。
#>
function Get-PropertyNames {
    param($Obj)
    if ($null -eq $Obj) { return @() }
    # 字典类型：OrderedDictionary / Hashtable
    if ($Obj -is [System.Collections.IDictionary]) {
        return @($Obj.Keys)
    }
    # PSCustomObject（PowerShell 数据容器，脚本中 [PSCustomObject]@{...} 创建的对象）
    # 排除 .NET 框架对象——它们虽然也有 .PSObject，但展开属性会导致无限递归
    if ($Obj -is [PSCustomObject]) {
        $typeName = $Obj.PSObject.TypeNames[0]
        # 仅展开 PSCustomObject 自身，不展开 .NET 框架类型
        if ($typeName -eq 'System.Management.Automation.PSCustomObject' -or
            $typeName -eq 'Selected.System.Diagnostics.Process' -or
            $typeName -like 'Deserialized.*' -or
            $typeName -like 'Selected.*') {
            return @($Obj.PSObject.Properties | ForEach-Object { $_.Name })
        }
    }
    return @()
}

<#
 .SYNOPSIS
    获取对象指定属性的值
#>
function Get-PropertyValue {
    param($Obj, [string]$Name)
    if ($Obj -is [System.Collections.IDictionary]) {
        if ($Obj.Contains($Name)) { return $Obj[$Name] }
        return $null
    }
    # StrictMode 下 $Obj.$Name 访问不存在的属性会抛异常，需安全检查
    if ($null -ne $Obj -and $Obj.PSObject.Properties.Match($Name).Count -gt 0) {
        return $Obj.$Name
    }
    return $null
}

<#
 .SYNOPSIS
    将对象数组格式化为对齐的文本表格
 .DESCRIPTION
    自动计算列宽，输出带表头和分隔线的对齐表格。
    对于超大数组（>500条），在表尾显示截断提示。
 .PARAMETER Objects
    要格式化的对象数组
 .PARAMETER MaxColumnWidth
    单列最大宽度，超过则截断
 .PARAMETER Indent
    每行前缀缩进
 .PARAMETER MaxRows
    最大输出行数，0 表示不限制
#>
function Format-ObjectArrayAsTable {
    param(
        [Parameter(Mandatory = $true)]
        [array]$Objects,
        [int]$MaxColumnWidth = 80,
        [string]$Indent = "",
        [int]$MaxRows = 0
    )

    if ($Objects.Count -eq 0) { return "${Indent}(无数据)`r`n" }

    # 获取第一个非空元素的属性名作为列名
    $columns = @()
    foreach ($obj in $Objects) {
        if ($null -ne $obj) {
            $columns = @(Get-PropertyNames $obj)
            break
        }
    }
    if ($columns.Count -eq 0) {
        # 可能是简单类型数组（如字符串数组）
        $sb = [System.Text.StringBuilder]::new()
        $idx = 0
        foreach ($item in $Objects) {
            $idx++
            if ($MaxRows -gt 0 -and $idx -gt $MaxRows) {
                [void]$sb.AppendLine("${Indent}... 共 $($Objects.Count) 条，已显示前 $MaxRows 条")
                break
            }
            [void]$sb.AppendLine("${Indent}[$idx] $(Format-Value $item)")
        }
        return $sb.ToString()
    }

    # 添加行号列
    $allColumns = @("#") + $columns

    # 计算实际要输出的行数
    $totalCount = $Objects.Count
    $displayCount = if ($MaxRows -gt 0 -and $totalCount -gt $MaxRows) { $MaxRows } else { $totalCount }

    # 计算各列宽度（遍历要显示的行 + 表头）
    $colWidths = @{}
    foreach ($col in $allColumns) {
        $colWidths[$col] = $col.Length
    }
    for ($i = 0; $i -lt $displayCount; $i++) {
        $obj = $Objects[$i]
        $rowNum = "$($i + 1)"
        if ($rowNum.Length -gt $colWidths["#"]) { $colWidths["#"] = $rowNum.Length }
        foreach ($col in $columns) {
            $val = Format-Value (Get-PropertyValue $obj $col)
            # 取第一行，截断
            $firstLine = ($val -split "`n")[0].Trim()
            if ($firstLine.Length -gt $MaxColumnWidth) {
                $firstLine = $firstLine.Substring(0, $MaxColumnWidth - 3) + "..."
            }
            if ($firstLine.Length -gt $colWidths[$col]) { $colWidths[$col] = $firstLine.Length }
        }
    }

    # 构建表格
    $sb = [System.Text.StringBuilder]::new()

    # 表头
    $headerParts = @()
    foreach ($col in $allColumns) {
        $headerParts += $col.PadRight($colWidths[$col])
    }
    [void]$sb.AppendLine("${Indent}$($headerParts -join '  ')")

    # 分隔线
    $sepParts = @()
    foreach ($col in $allColumns) {
        $sepParts += ("-" * $colWidths[$col])
    }
    [void]$sb.AppendLine("${Indent}$($sepParts -join '  ')")

    # 数据行
    for ($i = 0; $i -lt $displayCount; $i++) {
        $obj = $Objects[$i]
        $rowParts = @()
        $rowParts += "$($i + 1)".PadRight($colWidths["#"])
        foreach ($col in $columns) {
            $val = Format-Value (Get-PropertyValue $obj $col)
            $firstLine = ($val -split "`n")[0].Trim()
            if ($firstLine.Length -gt $MaxColumnWidth) {
                $firstLine = $firstLine.Substring(0, $MaxColumnWidth - 3) + "..."
            }
            $rowParts += $firstLine.PadRight($colWidths[$col])
        }
        [void]$sb.AppendLine("${Indent}$($rowParts -join '  ')")
    }

    if ($MaxRows -gt 0 -and $totalCount -gt $MaxRows) {
        [void]$sb.AppendLine("${Indent}... 共 $totalCount 条记录，已显示前 $MaxRows 条")
    }

    return $sb.ToString()
}

<#
 .SYNOPSIS
    将键值对对象格式化为缩进的纯文本块
 .DESCRIPTION
    递归处理嵌套对象。对于叶子值直接输出 Key: Value，
    对于嵌套字典/对象递归展开，对于数组调用表格格式化。
    内置递归深度保护（MaxDepth），防止 .NET 对象图无限递归导致调用深度溢出。
 .PARAMETER InputObject
    要格式化的对象（支持 PSCustomObject、OrderedDictionary、Hashtable）
 .PARAMETER IndentLevel
    当前缩进层级
 .PARAMETER MaxDepth
    最大递归深度（默认 10），超出后回退到 Format-Value 的 ToString() 输出
#>
function Format-KeyValueBlock {
    param(
        [Parameter(Mandatory = $true)]
        $InputObject,
        [int]$IndentLevel = 0,
        [int]$MaxDepth = 10
    )

    $indent = "  " * $IndentLevel
    $sb = [System.Text.StringBuilder]::new()

    # 递归深度保护：超限时回退到字符串输出
    if ($IndentLevel -ge $MaxDepth) {
        [void]$sb.AppendLine("${indent}$(Format-Value $InputObject)")
        return $sb.ToString()
    }

    if ($null -eq $InputObject) {
        [void]$sb.AppendLine("${indent}(空)")
        return $sb.ToString()
    }

    # 纯字符串：直接输出（支持多行）
    if ($InputObject -is [string]) {
        $cleaned = $InputObject -replace '[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', ''
        foreach ($line in ($cleaned -split "`n")) {
            [void]$sb.AppendLine("${indent}$($line.TrimEnd("`r"))")
        }
        return $sb.ToString()
    }

    # 简单值类型
    if ($InputObject -is [ValueType] -or $InputObject -is [datetime]) {
        [void]$sb.AppendLine("${indent}$(Format-Value $InputObject)")
        return $sb.ToString()
    }

    # 数组
    if ($InputObject -is [Array]) {
        if ($InputObject.Count -eq 0) {
            [void]$sb.AppendLine("${indent}(无数据)")
            return $sb.ToString()
        }
        # 检查第一个元素是否为复合对象
        $first = $null
        foreach ($item in $InputObject) {
            if ($null -ne $item) { $first = $item; break }
        }
        if ($null -ne $first -and (Get-PropertyNames $first).Count -gt 0) {
            [void]$sb.Append((Format-ObjectArrayAsTable -Objects $InputObject -Indent $indent))
        } else {
            # 简单类型数组
            $idx = 0
            foreach ($item in $InputObject) {
                $idx++
                [void]$sb.AppendLine("${indent}[$idx] $(Format-Value $item)")
            }
        }
        return $sb.ToString()
    }

    # 字典 / PSCustomObject：递归展开键值对
    $props = Get-PropertyNames $InputObject
    if ($props.Count -eq 0) {
        [void]$sb.AppendLine("${indent}$(Format-Value $InputObject)")
        return $sb.ToString()
    }

    foreach ($key in $props) {
        $val = Get-PropertyValue $InputObject $key
        if ($null -eq $val) {
            [void]$sb.AppendLine("${indent}${key}: (空)")
        }
        elseif ($val -is [string]) {
            $cleaned = "$val" -replace '[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', ''
            if ($cleaned -match "`n") {
                [void]$sb.AppendLine("${indent}${key}:")
                foreach ($line in ($cleaned -split "`n")) {
                    [void]$sb.AppendLine("${indent}  $($line.TrimEnd("`r"))")
                }
            } else {
                [void]$sb.AppendLine("${indent}${key}: $cleaned")
            }
        }
        elseif ($val -is [ValueType] -or $val -is [datetime]) {
            [void]$sb.AppendLine("${indent}${key}: $(Format-Value $val)")
        }
        elseif ($val -is [Array]) {
            if ($val.Count -eq 0) {
                [void]$sb.AppendLine("${indent}${key}: (无数据)")
            } else {
                $firstItem = $null
                foreach ($item in $val) { if ($null -ne $item) { $firstItem = $item; break } }
                if ($null -ne $firstItem -and (Get-PropertyNames $firstItem).Count -gt 0) {
                    [void]$sb.AppendLine("${indent}${key}: ($($val.Count) 条记录)")
                    [void]$sb.Append((Format-ObjectArrayAsTable -Objects $val -Indent "$indent  "))
                } else {
                    [void]$sb.AppendLine("${indent}${key}:")
                    $idx = 0
                    foreach ($item in $val) {
                        $idx++
                        [void]$sb.AppendLine("${indent}  [$idx] $(Format-Value $item)")
                    }
                }
            }
        }
        else {
            # 嵌套对象
            [void]$sb.AppendLine("${indent}${key}:")
            [void]$sb.Append((Format-KeyValueBlock -InputObject $val -IndentLevel ($IndentLevel + 1) -MaxDepth $MaxDepth))
        }
    }

    return $sb.ToString()
}

<#
 .SYNOPSIS
    将完整的采集汇总数据转换为纯文本报告
 .DESCRIPTION
    接收 Main 函数汇总的 $summary 有序字典，按章节输出面向人工/大模型阅读的纯文本报告。
    报告结构：报告头（元数据）→ 各采集章节 → 执行耗时统计。
 .PARAMETER InputData
    Main 函数的 $summary 有序字典
#>
function ConvertTo-PlainTextReport {
    param(
        [Parameter(Mandatory = $true)]
        $InputData
    )

    # 报告格式化需要处理各种异构对象（混合类型数组、动态属性等），
    # StrictMode -Version Latest 会导致访问不存在的属性或 .Count 时报错，
    # 在格式化作用域内临时降级为 Version 1（仍检查未初始化变量）。
    # ⚠ 注意：StrictMode 是动态作用域的，降级会向下传播到子函数，
    #   且在函数返回后不会自动恢复调用者的 StrictMode。
    #   当前 ConvertTo-PlainTextReport 返回后，Write-Summary 尾部的文件统计代码
    #   也会在 Version 1 下运行，这是可接受的（仅 UI 输出逻辑）。
    # TODO: 后续用 try { Set-StrictMode -Version 1; ... } finally { Set-StrictMode -Version Latest }
    #       包裹格式化逻辑，并添加 Pester 测试验证 StrictMode 在返回后正确恢复。
    Set-StrictMode -Version 1

    $sb = [System.Text.StringBuilder]::new()

    # ── 报告标题 ──────────────────────────────────────────────────
    [void]$sb.AppendLine("======== REPORT_BEGIN ========")
    [void]$sb.AppendLine("  Windows 系统日志收集报告")
    [void]$sb.AppendLine("======== REPORT_BEGIN ========")
    [void]$sb.AppendLine("")

    # ── 采集元数据（如果存在） ────────────────────────────────────
    if ($InputData -is [System.Collections.IDictionary] -and $InputData.Contains('_CollectionMeta')) {
        $meta = $InputData['_CollectionMeta']
        [void]$sb.AppendLine("======== META: _CollectionMeta ========")
        $metaProps = Get-PropertyNames $meta
        foreach ($key in $metaProps) {
            [void]$sb.AppendLine("  ${key}: $(Format-Value (Get-PropertyValue $meta $key))")
        }
        [void]$sb.AppendLine("")
    }

    # ── 执行耗时（如果存在） ──────────────────────────────────────
    if ($InputData -is [System.Collections.IDictionary] -and $InputData.Contains('_ExecutionTiming')) {
        $timing = $InputData['_ExecutionTiming']
        [void]$sb.AppendLine("======== META: _ExecutionTiming ========")
        $timingProps = Get-PropertyNames $timing
        foreach ($key in $timingProps) {
            [void]$sb.AppendLine("  ${key}: $(Format-Value (Get-PropertyValue $timing $key))")
        }
        [void]$sb.AppendLine("")
    }

    # ── 章节标题映射 ──────────────────────────────────────────────
    $sectionTitles = [ordered]@{
        "SystemInfo"       = "系统基本信息"
        "SystemEvent"      = "关键安全事件和系统事件"
        "Processes"        = "进程信息"
        "Network"          = "网络配置信息"
        "IISLogs"          = "IIS日志"
        "Startup"          = "自启动项信息"
        "USNLogs"          = "USN日志（文件系统变更记录）"
        "CheckSignature"   = "文件数字签名检查"
        "PSReadLineHistory"= "PSReadLine 命令历史"
    }

    # ── 逐章节输出 ────────────────────────────────────────────────
    $sectionIndex = 0
    $keys = if ($InputData -is [System.Collections.IDictionary]) {
        @($InputData.Keys)
    } else {
        @($InputData.PSObject.Properties | ForEach-Object { $_.Name })
    }

    foreach ($key in $keys) {
        # 跳过元数据（已在报告头输出）
        if ($key -eq '_CollectionMeta' -or $key -eq '_ExecutionTiming') { continue }

        $sectionIndex++
        $title = if ($sectionTitles.Contains($key)) { $sectionTitles[$key] } else { $key }
        $value = if ($InputData -is [System.Collections.IDictionary]) { $InputData[$key] } else { $InputData.$key }

        [void]$sb.AppendLine("======== SECTION: $key ========")
        [void]$sb.AppendLine("  [$sectionIndex] $title")
        [void]$sb.AppendLine("======== SECTION: $key ========")
        [void]$sb.AppendLine("")

        if ($null -eq $value) {
            [void]$sb.AppendLine("  (无数据)")
            [void]$sb.AppendLine("")
            continue
        }

        # ── SystemEvent 特殊处理：四级分类 ────────────────────
        if ($key -eq 'SystemEvent' -and $value -is [System.Collections.IDictionary]) {
            foreach ($category in @($value.Keys)) {
                $categoryData = $value[$category]
                [void]$sb.AppendLine("  -------- CATEGORY: $category --------")
                [void]$sb.AppendLine("")

                if ($null -eq $categoryData) {
                    [void]$sb.AppendLine("    (无数据)")
                    [void]$sb.AppendLine("")
                    continue
                }

                $eventKeys = if ($categoryData -is [System.Collections.IDictionary]) { @($categoryData.Keys) } else { @() }
                foreach ($eventKey in $eventKeys) {
                    $events = $categoryData[$eventKey]
                    $count = if ($events -is [Array]) { $events.Count } else { 0 }
                    [void]$sb.AppendLine("  ---- EVENTS: $eventKey ($count records) ----")

                    if ($count -eq 0) {
                        [void]$sb.AppendLine("    (无数据)")
                    } else {
                        [void]$sb.Append((Format-ObjectArrayAsTable -Objects $events -Indent "    "))
                    }
                    [void]$sb.AppendLine("")
                }
            }
            continue
        }

        # ── SystemInfo 特殊处理：包含子段落（systeminfo, whoami, users 等） ──
        if ($key -eq 'SystemInfo') {
            $subProps = Get-PropertyNames $value
            foreach ($subKey in $subProps) {
                $subVal = Get-PropertyValue $value $subKey
                [void]$sb.AppendLine("  -------- SUB: $subKey --------")
                [void]$sb.AppendLine("")
                [void]$sb.Append((Format-KeyValueBlock -InputObject $subVal -IndentLevel 2))
                [void]$sb.AppendLine("")
            }
            continue
        }

        # ── Network 特殊处理：包含子段落（ipconfig, route, arp 等） ──
        if ($key -eq 'Network' -and $value -is [System.Collections.IDictionary]) {
            foreach ($subKey in @($value.Keys)) {
                $subVal = $value[$subKey]
                [void]$sb.AppendLine("  -------- SUB: $subKey --------")
                [void]$sb.AppendLine("")
                [void]$sb.Append((Format-KeyValueBlock -InputObject $subVal -IndentLevel 2))
                [void]$sb.AppendLine("")
            }
            continue
        }

        # ── Startup 特殊处理：按类别分组输出 ─────────────────────
        if ($key -eq 'Startup' -and $value -is [System.Collections.IDictionary]) {
            $startupTitles = [ordered]@{
                'WmiStartupCommands' = 'WMI 启动命令'
                'AutoStartServices'  = '自动启动服务（名称列表）'
                'StartupFolders'     = '启动文件夹内容'
                'MSConfigItems'      = 'MSConfig 启动项'
                'RegistryStartup'    = '注册表启动项'
                'BrowserExtensions'  = '浏览器扩展'
                'ScheduledTasks'     = '计划任务'
            }
            foreach ($subKey in @($value.Keys)) {
                $subVal = $value[$subKey]
                $subTitle = if ($startupTitles.Contains($subKey)) { $startupTitles[$subKey] } else { $subKey }
                [void]$sb.AppendLine("  -------- SUB: $subTitle --------")
                [void]$sb.AppendLine("")

                if ($null -eq $subVal -or ($subVal -is [Array] -and $subVal.Count -eq 0)) {
                    [void]$sb.AppendLine("    (无数据)")
                } elseif ($subKey -eq 'AutoStartServices') {
                    # 自动启动服务只输出名称列表（逗号分隔），不用表格
                    [void]$sb.AppendLine("    $($subVal -join ', ')")
                } else {
                    [void]$sb.Append((Format-ObjectArrayAsTable -Objects $subVal -Indent "    "))
                }
                [void]$sb.AppendLine("")
            }
            continue
        }

        # ── PSReadLineHistory 特殊处理：命令列表单独展示 ──
        if ($key -eq 'PSReadLineHistory' -and $value -is [Array]) {
            foreach ($userHist in $value) {
                if ($null -eq $userHist) { continue }
                $userName = Get-PropertyValue $userHist 'UserName'
                [void]$sb.AppendLine("  -------- SUB: User_$userName --------")
                [void]$sb.AppendLine("")

                $histProps = Get-PropertyNames $userHist
                foreach ($hp in $histProps) {
                    if ($hp -eq 'Commands') { continue }
                    [void]$sb.AppendLine("    ${hp}: $(Format-Value (Get-PropertyValue $userHist $hp))")
                }

                $commands = Get-PropertyValue $userHist 'Commands'
                if ($commands -and $commands.Count -gt 0) {
                    [void]$sb.AppendLine("    Commands: ($($commands.Count) 条)")
                    $idx = 0
                    foreach ($cmd in $commands) {
                        $idx++
                        [void]$sb.AppendLine("      [$idx] $cmd")
                    }
                } else {
                    [void]$sb.AppendLine("    Commands: (无)")
                }
                [void]$sb.AppendLine("")
            }
            continue
        }

        # ── 通用处理：数组 → 表格，字典/对象 → 键值对 ─────────
        [void]$sb.Append((Format-KeyValueBlock -InputObject $value -IndentLevel 1))
        [void]$sb.AppendLine("")
    }

    # ── 报告尾 ────────────────────────────────────────────────────
    [void]$sb.AppendLine("======== REPORT_END ========")
    [void]$sb.AppendLine("  报告结束")
    [void]$sb.AppendLine("======== REPORT_END ========")

    return $sb.ToString()
}

function Test-KeyNotExistsOrEmpty
{
    param(
        [System.Collections.IDictionary]$hashTable,
        [string]$key
    )
    # 先问键在不在
    if (-not $hashTable.Contains($key))
    {
        return $true
    }

    $v = $hashTable[$key]
    if ($null -eq $v)
    {
        return $true
    }

    if ($v -is [Array] -and $v.Length -eq 0)
    {
        return $true
    }
    if ($v -is [String] -and $v -eq '')
    {
        return $true
    }

    return $false
}

function Get-UserDataFieldValue
{
    param(
        [xml]$EventXml,
        [string]$FieldName
    )

    $userDataNode = $EventXml.Event.UserData
    if (-not $userDataNode)
    {
        return $null
    }

    foreach ($childNode in @($userDataNode.ChildNodes))
    {
        if (-not $childNode)
        {
            continue
        }

        try
        {
            if ($childNode.LocalName -eq $FieldName -and -not [string]::IsNullOrWhiteSpace($childNode.InnerText))
            {
                return $childNode.InnerText.Trim()
            }

            $fieldNode = $childNode.SelectSingleNode("./*[local-name()='$FieldName']")
            if (-not $fieldNode)
            {
                $fieldNode = $childNode.SelectSingleNode(".//*[local-name()='$FieldName']")
            }

            if ($fieldNode -and -not [string]::IsNullOrWhiteSpace($fieldNode.InnerText))
            {
                return $fieldNode.InnerText.Trim()
            }
        }
        catch
        {
            Write-Verbose "UserData 字段 $FieldName 提取失败: $($_.Exception.Message)"
        }
    }

    return $null
}

function Invoke-SystemInfoCollection
{
    Write-Host "[步骤 1] 正在收集系统基本信息..." -ForegroundColor Cyan

    $commands = @{
        "systeminfo" = {
            $os = Get-CimInstance Win32_OperatingSystem
            $cs = Get-CimInstance Win32_ComputerSystem

            [PSCustomObject]@{
                ComputerName  = $cs.Name
                OSName        = $os.Caption
                OSVersion     = $os.Version
                InstallDate   = $os.InstallDate
                LastBootTime  = $os.LastBootUpTime
                TotalMemoryGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
                Manufacturer  = $cs.Manufacturer
                Model         = $cs.Model
            }
        }
        "whoami" = {
            (whoami /groups) -join [Environment]::NewLine
        }
        "users" = {
            if (Get-Command Get-LocalUser -ErrorAction SilentlyContinue) {
                Get-LocalUser
            } else{
                net user | Out-String
            }
        }
        "administrators" = {
            if (Get-Command Get-LocalGroupMember -ErrorAction SilentlyContinue) {
                Get-LocalGroupMember -Group "Administrators"
            } else{
                net localgroup administrators | Out-String
            }
        }
        "smb_share" = {
            # 将 CIM 对象转为 PSCustomObject，避免 MSFT_SmbShare.ToString() 中
            # 的 $ 在双引号字符串插值上下文中被 PowerShell 误解析为变量引用
            # （例如 ADMIN$ → ADMIN?）
            Get-SmbShare | ForEach-Object {
                [PSCustomObject]@{
                    Name        = $_.Name
                    Path        = $_.Path
                    Description = $_.Description
                    ScopeName   = $_.ScopeName
                    ShareType   = $_.ShareType.ToString()
                }
            }
        }
        "security_hygiene" = {
            $hygiene = [ordered]@{}

            # === 1. OpenSSH sshd.log 状态 ===
            try {
                $sshdLogDir = "$env:ProgramData\ssh"
                $sshdLogPath = "$env:ProgramData\ssh\logs\sshd.log"
                if (Test-Path $sshdLogDir) {
                    $hygiene["OpenSSH_DirExists"] = $true
                    if (Test-Path $sshdLogPath) {
                        $logFile = Get-Item $sshdLogPath -ErrorAction SilentlyContinue
                        $hygiene["OpenSSH_LogExists"] = $true
                        $hygiene["OpenSSH_LogSizeBytes"] = if ($logFile) { $logFile.Length } else { 0 }
                        $hygiene["OpenSSH_LogLastWrite"] = if ($logFile) { $logFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "" }
                        $hygiene["OpenSSH_LogEmpty"] = if ($logFile -and $logFile.Length -eq 0) { $true } else { $false }
                    } else {
                        # sshd.log 可能在 logs 子目录，也可能直接在 ssh 目录
                        $altLogPath = "$env:ProgramData\ssh\sshd.log"
                        if (Test-Path $altLogPath) {
                            $logFile = Get-Item $altLogPath -ErrorAction SilentlyContinue
                            $hygiene["OpenSSH_LogExists"] = $true
                            $hygiene["OpenSSH_LogSizeBytes"] = if ($logFile) { $logFile.Length } else { 0 }
                            $hygiene["OpenSSH_LogLastWrite"] = if ($logFile) { $logFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss") } else { "" }
                            $hygiene["OpenSSH_LogEmpty"] = if ($logFile -and $logFile.Length -eq 0) { $true } else { $false }
                        } else {
                            $hygiene["OpenSSH_LogExists"] = $false
                            $hygiene["OpenSSH_LogSizeBytes"] = 0
                            $hygiene["OpenSSH_LogEmpty"] = $true
                        }
                    }
                } else {
                    $hygiene["OpenSSH_DirExists"] = $false
                    $hygiene["OpenSSH_LogExists"] = $false
                    $hygiene["OpenSSH_LogSizeBytes"] = 0
                    $hygiene["OpenSSH_LogEmpty"] = $true
                }
            } catch {
                $hygiene["OpenSSH_Error"] = $_.Exception.Message
            }

            # === 2. sshd_config 状态 ===
            try {
                $sshdConfigPath = "$env:ProgramData\ssh\sshd_config"
                if (Test-Path $sshdConfigPath) {
                    $hygiene["SSHD_ConfigExists"] = $true
                    $configContent = Get-Content $sshdConfigPath -Raw -ErrorAction SilentlyContinue
                    $hygiene["SSHD_ConfigSizeBytes"] = (Get-Item $sshdConfigPath).Length
                    # 提取 LogLevel
                    $logLevelMatch = $configContent | Select-String -Pattern '^\s*LogLevel\s+(\S+)' -AllMatches
                    if ($logLevelMatch -and $logLevelMatch.Matches.Count -gt 0) {
                        $hygiene["SSHD_LogLevel"] = $logLevelMatch.Matches[0].Groups[1].Value
                    } else {
                        # 检查是否被注释掉
                        $commentedMatch = $configContent | Select-String -Pattern '^\s*#\s*LogLevel\s+(\S+)' -AllMatches
                        if ($commentedMatch -and $commentedMatch.Matches.Count -gt 0) {
                            $hygiene["SSHD_LogLevel"] = "(commented out, default) " + $commentedMatch.Matches[0].Groups[1].Value
                        } else {
                            $hygiene["SSHD_LogLevel"] = "(not set, using default)"
                        }
                    }
                } else {
                    $hygiene["SSHD_ConfigExists"] = $false
                    $hygiene["SSHD_LogLevel"] = "N/A"
                }
            } catch {
                $hygiene["SSHD_ConfigError"] = $_.Exception.Message
            }

            # === 3. Prefetch 状态 ===
            try {
                $prefetchPath = "$env:SystemRoot\Prefetch"
                if (Test-Path $prefetchPath) {
                    $hygiene["Prefetch_DirExists"] = $true
                    $pfFiles = @(Get-ChildItem -Path $prefetchPath -Filter "*.pf" -ErrorAction SilentlyContinue)
                    $hygiene["Prefetch_FileCount"] = $pfFiles.Count
                    if ($pfFiles.Count -gt 0) {
                        # 采集最近 20 个 Prefetch 文件的名称和最后修改时间
                        $hygiene["Prefetch_RecentFiles"] = @($pfFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 20 | ForEach-Object {
                            [ordered]@{
                                Name = $_.Name
                                LastWriteTime = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                                SizeBytes = $_.Length
                            }
                        })
                    } else {
                        $hygiene["Prefetch_RecentFiles"] = @()
                    }
                    # 检查 Prefetch 是否被禁用（注册表检查）
                    try {
                        $prefetchRegPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
                        if (Test-Path $prefetchRegPath) {
                            $enablePrefetcher = (Get-ItemProperty -Path $prefetchRegPath -Name "EnablePrefetcher" -ErrorAction SilentlyContinue).EnablePrefetcher
                            $hygiene["Prefetch_EnablePrefetcher"] = $enablePrefetcher
                            # 0=Disabled, 1=Application, 2=Boot, 3=Both
                            $hygiene["Prefetch_Disabled"] = ($enablePrefetcher -eq 0)
                        }
                    } catch {
                        $hygiene["Prefetch_RegistryError"] = $_.Exception.Message
                    }
                } else {
                    $hygiene["Prefetch_DirExists"] = $false
                    $hygiene["Prefetch_FileCount"] = 0
                    $hygiene["Prefetch_RecentFiles"] = @()
                }
            } catch {
                $hygiene["Prefetch_Error"] = $_.Exception.Message
            }

            # === 4. VSS 影子副本状态 ===
            try {
                $vssItems = @(Get-CimInstance -ClassName Win32_ShadowCopy -ErrorAction SilentlyContinue)
                $hygiene["VSS_ShadowCopyCount"] = $vssItems.Count
                if ($vssItems.Count -gt 0) {
                    $hygiene["VSS_ShadowCopies"] = @($vssItems | ForEach-Object {
                        [ordered]@{
                            ID = $_.ID
                            InstallDate = if ($_.InstallDate) { $_.InstallDate } else { "" }
                            VolumeName = $_.VolumeName
                            DeviceObject = $_.DeviceObject
                        }
                    })
                } else {
                    $hygiene["VSS_ShadowCopies"] = @()
                }
                # 检查 VSS 服务状态
                $vssService = Get-Service -Name VSS -ErrorAction SilentlyContinue
                if ($vssService) {
                    $hygiene["VSS_ServiceStatus"] = $vssService.Status.ToString()
                    $hygiene["VSS_ServiceStartType"] = $vssService.StartType.ToString()
                } else {
                    Write-Warning "VSS 服务不存在或无法获取"
                }
            } catch {
                $hygiene["VSS_Error"] = $_.Exception.Message
            }

            # === 5. 防火墙开关状态（精简提取） ===
            try {
                $fwProfiles = Get-NetFirewallProfile -ErrorAction SilentlyContinue
                if ($fwProfiles) {
                    $hygiene["Firewall_Profiles"] = @($fwProfiles | ForEach-Object {
                        [ordered]@{
                            Name = $_.Name
                            Enabled = $_.Enabled
                            DefaultInboundAction = $_.DefaultInboundAction.ToString()
                            DefaultOutboundAction = $_.DefaultOutboundAction.ToString()
                        }
                    })
                    $hygiene["Firewall_AllEnabled"] = @($fwProfiles | Where-Object { $_.Enabled -eq $true }).Count -eq @($fwProfiles).Count
                    $hygiene["Firewall_AnyDisabled"] = @($fwProfiles | Where-Object { $_.Enabled -eq $false }).Count -gt 0
                } else {
                    Write-Warning "无法获取防火墙配置信息（Get-NetFirewallProfile 返回空）"
                }
            } catch {
                $hygiene["Firewall_Error"] = $_.Exception.Message
            }

            [PSCustomObject]$hygiene
        }
    }

    $systemInfo = [PSCustomObject]@{}

    foreach ($commandName in $commands.Keys)
    {
        try
        {
            $systemInfo | Add-Member -NotePropertyName $commandName -NotePropertyValue (& $commands[$commandName]) -Force
            Write-Verbose "已收集: $commandName"
        }
        catch
        {
            Write-Warning "收集 $commandName 时出错: $($_.Exception.Message)"
            # 可以选择添加错误占位符
            $systemInfo | Add-Member -NotePropertyName $commandName -NotePropertyValue "错误: $($_.Exception.Message)" -Force
        }
    }

    # 返回收集的数据
    return $systemInfo
}

# ConvertTo-PlainTextReport -InputData (Invoke-SystemInfoCollection) | Out-File -FilePath "debug.log" -Encoding UTF8
# return

# 收集系统关键事件 - 精简版，只保留溯源关键字段
function Invoke-SystemEventCollection
{
    Write-Host "[步骤 2] 正在收集关键安全事件和关键系统事件..." -ForegroundColor Cyan

    # 计算时间范围（最近N天）
    $startTimeObj = (Get-Date).AddDays(-$DaysBack)
    $startTime = $startTimeObj.ToString("yyyy-MM-ddTHH:mm:ss")
    $endTimeObj = $startTimeObj.AddDays($DaysRange)
    $endTime = $endTimeObj.ToString("yyyy-MM-ddTHH:mm:ss")
    $timeFilter = "TimeCreated[@SystemTime>='$startTime' and @SystemTime<='$endTime']"

    # 定义要收集的事件 - 只保留关键溯源字段
    $systemEvents = @(
        @{
            Description = "登录成功事件（已过滤 LogonType=5 系统服务登录）";
            # LogonType=5 是 Service 登录（SYSTEM/NT AUTHORITY + IpAddress=- + ProcessName=services.exe）
            # 实测占 4624 总量的 90%+，全是系统内部噪声。过滤后仅保留人类/远程登录（Type 2/3/7/10/11）
            Query = "*[System[(EventID=4624) and $timeFilter] and EventData[Data[@Name='LogonType']!='5']]";
            Count = $MaxEventCount;
            FileName = "login_success_4624";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "TargetUserName", "TargetDomainName", "LogonType", "IpAddress", "WorkstationName", "ProcessName")
            ATTCKTechnique = "T1078"      # Valid Accounts
            ATTCKTactic = "Initial Access"
        },
        @{
            Description = "登录失败事件";
            Query = "*[System[(EventID=4625) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "login_failed_4625";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "TargetUserName", "TargetDomainName", "LogonType", "IpAddress", "WorkstationName", "SubStatus")
            ATTCKTechnique = "T1110.001"  # Brute Force: Password Guessing
            ATTCKTactic = "Credential Access"
            AggregateByIP = $true          # 按 IP 聚合统计，而非逐条输出原始记录
        },
        @{
            Description = "特权登录事件";
            Query = "*[System[(EventID=4672) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "login_privilege_4672";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "SubjectUserName", "SubjectDomainName", "PrivilegeList", "LogonType")
            ATTCKTechnique = "T1078.003"  # Valid Accounts: Local Accounts
            ATTCKTactic = "Privilege Escalation"
            AggregateByUser = $true        # 按用户聚合统计，500 条→几行摘要
        },
        @{
            Description = "账户创建事件";
            Query = "*[System[(EventID=4720) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "account_created_4720";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "TargetUserName", "SubjectUserName", "SubjectDomainName")
            ATTCKTechnique = "T1136.001"  # Create Account: Local Account
            ATTCKTactic = "Persistence"
        },
        @{
            Description = "服务安装事件";
            Query = "*[System[(EventID=7045) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "service_install_7045";
            LogName = "System";
            KeyFields = @("TimeCreated", "EventID", "ServiceName", "ImagePath", "ServiceType", "StartType", "AccountName")
            ATTCKTechnique = "T1543.003"  # Create or Modify System Process: Windows Service
            ATTCKTactic = "Persistence"
        },
        # 注意：7036 服务启停事件已移除——实测 200 条全为系统常规启停噪声（WMI Performance Adapter/BITS/Software Protection 等），
        # 恶意服务行为已被 7045（安装）和 7040（启动类型变更）完全覆盖。
        @{
            Description = "服务启动类型切换事件";
            Query = "*[System[(EventID=7040) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "service_change_startup_type_7040";
            LogName = "System";
            KeyFields = @("TimeCreated", "EventID", "param1", "param2", "param3", "param4")
            ATTCKTechnique = "T1543.003"  # Create or Modify System Process: Windows Service
            ATTCKTactic = "Defense Evasion"
            # 按 param4（服务短名称）聚合，避免 BITS/TrustedInstaller 等系统服务定时切换产生大量噪声
            AggregateByService = $true
        },
        @{
            Description = "系统启动/关闭";
            Query = "*[System[(EventID=6005 or EventID=6006 or EventID=6009 or EventID=6013) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "system_start_stop";
            LogName = "System";
            KeyFields = @("TimeCreated", "EventID", "Message")
            ATTCKTechnique = "T1529"      # System Shutdown/Reboot
            ATTCKTactic = "Impact"
        },
        @{
            Description = "进程创建事件";
            Query = "*[System[(EventID=4688) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "process_creation_4688";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "NewProcessName", "NewProcessId", "CommandLine", "CreatorProcessName", "CreatorProcessId", "TargetUserName")
            ATTCKTechnique = "T1059"      # Command and Scripting Interpreter
            ATTCKTactic = "Execution"
        },
        @{
            Description = "注册表修改事件";
            Query = "*[System[(EventID=4657) and $timeFilter]]";
            Count = $MaxEventCount;
            FileName = "registry_changes_4657";
            LogName = "Security";
            KeyFields = @("TimeCreated", "EventID", "ObjectName", "ObjectValueName", "OldValue", "NewValue", "ProcessName", "TargetUserName")
            ATTCKTechnique = "T1112"      # Modify Registry
            ATTCKTactic = "Defense Evasion"
        },
        # === PowerShell 事件日志 ===
        @{
            Description = "PowerShell脚本块执行日志"
            Query = "*[System[(EventID=4104) and $timeFilter]]"
            Count = $MaxEventCount
            FileName = "powershell_scriptblock_4104"
            LogName = "Microsoft-Windows-PowerShell/Operational"
            Category = "PowerShell"
            KeyFields = @("TimeCreated", "EventID", "ScriptBlockText", "ScriptBlockId", "Path")
            ATTCKTechnique = "T1059.001"
            ATTCKTactic = "Execution"
            FilterSystemPaths = $true      # 过滤系统模块脚本块，只保留用户/可疑脚本
        },
        @{
            Description = "PowerShell模块日志"
            Query = "*[System[(EventID=4103) and $timeFilter]]"
            Count = $MaxEventCount
            FileName = "powershell_module_4103"
            LogName = "Microsoft-Windows-PowerShell/Operational"
            Category = "PowerShell"
            KeyFields = @("TimeCreated", "EventID", "ContextInfo", "Payload")
            ATTCKTechnique = "T1059.001"
            ATTCKTactic = "Execution"
        },
        # === RDP 远程桌面专项日志 ===
        @{
            Description = "RDP远程连接尝试"
            Query = "*[System[(EventID=1149) and $timeFilter]]"
            Count = $MaxEventCount
            FileName = "rdp_connection_1149"
            LogName = "Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational"
            Category = "RDP"
            KeyFields = @("TimeCreated", "EventID", "Param1", "Param2", "Param3")
            ATTCKTechnique = "T1021.001"
            ATTCKTactic = "Lateral Movement"
        },
        @{
            Description = "RDP会话登录/重连"
            Query = "*[System[(EventID=21 or EventID=25) and $timeFilter]]"
            Count = $MaxEventCount
            FileName = "rdp_session_logon_21_25"
            LogName = "Microsoft-Windows-TerminalServices-LocalSessionManager/Operational"
            Category = "RDP"
            KeyFields = @("TimeCreated", "EventID", "User", "SessionID", "Address")
            ATTCKTechnique = "T1021.001"
            ATTCKTactic = "Lateral Movement"
        }
    )

    # 用于汇总的分级结构
    $summary = @{ Security = [ordered]@{}; System = [ordered]@{}; PowerShell = [ordered]@{}; RDP = [ordered]@{} }
    $Script:SystemPathFilteredCount = 0  # 4104 系统模块过滤计数器

    foreach ($evt in $systemEvents)
    {
        Write-Host "正在分析$($evt.Description)..." -ForegroundColor White
        $baseName = $evt.FileName
        $logName  = $evt.LogName
        $keyFields = $evt.KeyFields
        # 使用 Category 字段作为 summary 分级 key（兼容新增的 Operational 日志通道）
        $category = if ($evt.ContainsKey('Category') -and $evt.Category) { $evt.Category } else { $logName }

        try
        {
            # 使用原生 PowerShell cmdlet 收集事件
            # 不使用 SilentlyContinue，改用 Stop 确保日志通道不存在/权限不足等错误能被 catch 捕获
            $events = @(Get-WinEvent -LogName $logName -FilterXPath $evt.Query -MaxEvents $evt.Count -ErrorAction Stop)

            # 只提取关键字段
            $filteredEvents = @()
            foreach ($event in $events)
            {
                $eventXml = [xml]$event.ToXml()
                $filteredEvent = [ordered]@{
                    TimeCreated = $event.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                    EventID = $event.Id
                }

            # 提取关键字段（支持 EventData 和 UserData 两种 XML 结构）
                foreach ($field in $keyFields) {
                    if ($field -ne "TimeCreated" -and $field -ne "EventID") {
                        try {
                            $fieldValue = $null
                            # 先尝试 EventData.Data（Security/System 日志标准格式）
                            $dataNode = $eventXml.Event.EventData.Data | Where-Object { $_.Name -eq $field }
                            if ($dataNode -and $dataNode."#text") {
                                $fieldValue = $dataNode."#text"
                            } else {
                                # 回退到 UserData（RDP/TerminalServices/PowerShell Operational 日志格式）
                                $userDataNodes = $eventXml.Event.UserData
                                if ($userDataNodes) {
                                    $innerNode = $userDataNodes.ChildNodes[0]
                                    if ($innerNode) {
                                        $fieldNode = $innerNode.SelectSingleNode($field)
                                        if ($fieldNode -and $fieldNode.InnerText) {
                                            $fieldValue = $fieldNode.InnerText
                                        }
                                    }
                                }
                            }
                            # 对 ScriptBlockText 等长文本字段截断并单行化，控制报告体积
                            if ($fieldValue -and $field -eq 'ScriptBlockText') {
                                $fieldValue = ($fieldValue -replace '[\r\n]+', ' ').Trim()
                                if ($fieldValue.Length -gt 2000) {
                                    $fieldValue = $fieldValue.Substring(0, 2000) + '...(truncated)'
                                }
                            }
                            $filteredEvent[$field] = if ($fieldValue) { $fieldValue } else { "" }
                        } catch {
                            $filteredEvent[$field] = ""
                        }
                    }
                }
                # === EventID 4104 系统模块路径过滤 ===
                # 过滤来自 Windows 系统目录的脚本块（系统模块噪声），只保留用户/可疑脚本
                # Path 为空的脚本块不过滤（无路径通常是手动执行或远程注入，溯源价值更高）
                if ($evt.ContainsKey('FilterSystemPaths') -and $evt.FilterSystemPaths) {
                    $scriptPath = $filteredEvent['Path']
                    if ($scriptPath -and $scriptPath -ne '') {
                        $isSystemPath = $false
                        $systemPrefixes = @(
                            'C:\Windows\System32\WindowsPowerShell\',
                            'C:\Windows\SysWOW64\WindowsPowerShell\',
                            'C:\Program Files\WindowsPowerShell\Modules\',
                            'C:\Program Files (x86)\WindowsPowerShell\Modules\',
                            'C:\Windows\Microsoft.NET\',
                            'C:\Program Files\PowerShell\7\Modules\',        # PowerShell 7 系统模块
                            'C:\Program Files (x86)\PowerShell\7\Modules\'   # PowerShell 7 (x86) 系统模块
                        )
                        foreach ($prefix in $systemPrefixes) {
                            if ($scriptPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                                $isSystemPath = $true
                                break
                            }
                        }
                        if ($isSystemPath) {
                            $Script:SystemPathFilteredCount++
                            continue  # 跳过系统模块脚本块
                        }
                    }
                }

                $filteredEvents += [PSCustomObject]$filteredEvent
            }

            $count = $filteredEvents.Count

            # === EventID 4625 按 IP 聚合统计 ===
            # 将逐条登录失败记录转换为按 IP 维度的聚合统计，减少暴力破解场景下的报告体积
            if ($evt.ContainsKey('AggregateByIP') -and $evt.AggregateByIP -and $filteredEvents.Count -gt 0) {
                $rawCount = $filteredEvents.Count
                $ipGroups = @{}
                foreach ($record in $filteredEvents) {
                    $ip = if ($record.IpAddress -and $record.IpAddress -ne '' -and $record.IpAddress -ne '-') {
                        $record.IpAddress
                    } else {
                        '(local)'
                    }
                    if (-not $ipGroups.ContainsKey($ip)) {
                        $ipGroups[$ip] = [System.Collections.Generic.List[object]]::new()
                    }
                    $ipGroups[$ip].Add($record)
                }
                $aggregated = @()
                foreach ($kv in $ipGroups.GetEnumerator()) {
                    $ip = $kv.Key
                    $records = $kv.Value
                    $times = $records | ForEach-Object { $_.TimeCreated } | Sort-Object
                    $targetUsers = ($records | ForEach-Object { $_.TargetUserName } | Where-Object { $_ -and $_ -ne '' } | Select-Object -Unique) -join ', '
                    $logonTypes = ($records | ForEach-Object { $_.LogonType } | Where-Object { $_ -and $_ -ne '' } | Select-Object -Unique) -join ', '
                    $subStatuses = ($records | ForEach-Object { $_.SubStatus } | Where-Object { $_ -and $_ -ne '' } | Select-Object -Unique) -join ', '
                    $workstations = ($records | ForEach-Object { $_.WorkstationName } | Where-Object { $_ -and $_ -ne '' } | Select-Object -Unique) -join ', '
                    $aggregated += [PSCustomObject][ordered]@{
                        IpAddress        = $ip
                        AttemptCount     = $records.Count
                        FirstAttempt     = $times[0]
                        LastAttempt      = $times[-1]
                        TargetUserNames  = $targetUsers
                        LogonTypes       = $logonTypes
                        SubStatuses      = $subStatuses
                        WorkstationNames = $workstations
                    }
                }
                # 按尝试次数降序排列，最活跃的攻击源排在前面
                $filteredEvents = $aggregated | Sort-Object -Property AttemptCount -Descending
                $count = $filteredEvents.Count
                Write-Verbose "已聚合 $rawCount 条登录失败事件为 $count 个 IP 统计"
            }

            # === EventID 4672 按用户聚合统计 ===
            # 将逐条特权登录记录转换为按 用户+域名 维度的聚合统计，500 条→几行摘要
            # 动态用户名归一化：sshd_PID → sshd_*，DWM-N → DWM-*
            if ($evt.ContainsKey('AggregateByUser') -and $evt.AggregateByUser -and $filteredEvents.Count -gt 0) {
                $rawCount = $filteredEvents.Count
                $userGroups = @{}
                foreach ($record in $filteredEvents) {
                    $userName = if ($record.SubjectUserName -and $record.SubjectUserName -ne '') {
                        $record.SubjectUserName
                    } else {
                        '(unknown)'
                    }
                    $domainName = if ($record.SubjectDomainName -and $record.SubjectDomainName -ne '') {
                        $record.SubjectDomainName
                    } else {
                        '(unknown)'
                    }
                    # 归一化动态用户名：sshd_7664 → sshd_*，DWM-3 → DWM-*
                    $groupName = $userName
                    if ($userName -match '^sshd_\d+$') { $groupName = 'sshd_*' }
                    elseif ($userName -match '^DWM-\d+$') { $groupName = 'DWM-*' }
                    $key = "$domainName\$groupName"
                    if (-not $userGroups.ContainsKey($key)) {
                        $userGroups[$key] = [System.Collections.Generic.List[object]]::new()
                    }
                    $userGroups[$key].Add($record)
                }
                $aggregated = @()
                foreach ($kv in $userGroups.GetEnumerator()) {
                    $key = $kv.Key
                    $records = $kv.Value
                    $parts = $key -split '\\', 2
                    $domainName = $parts[0]
                    $groupName = $parts[1]
                    $times = $records | ForEach-Object { $_.TimeCreated } | Sort-Object
                    $privileges = ($records | ForEach-Object { $_.PrivilegeList } | Where-Object { $_ -and $_ -ne '' } | Select-Object -Unique) -join ', '
                    $aggregated += [PSCustomObject][ordered]@{
                        SubjectUserName    = $groupName
                        SubjectDomainName  = $domainName
                        EventCount         = $records.Count
                        FirstSeen          = $times[0]
                        LastSeen           = $times[-1]
                        PrivilegeList      = $privileges
                    }
                }
                # 按事件次数降序排列
                $filteredEvents = $aggregated | Sort-Object -Property EventCount -Descending
                $count = $filteredEvents.Count
                Write-Verbose "已聚合 $rawCount 条特权登录事件为 $count 个用户统计"
            }

            # === EventID 7040 按服务名聚合统计 ===
            # 将逐条服务启动类型变更记录转换为按 param4（服务短名称）维度的聚合统计
            # 实测 BITS 等系统服务每 ~4 分钟切换一次启动类型，7 天产生 160+ 条噪声
            # 聚合后 166 条 → ~4 行摘要，同时保留异常服务的可见性
            if ($evt.ContainsKey('AggregateByService') -and $evt.AggregateByService -and $filteredEvents.Count -gt 0) {
                $rawCount = $filteredEvents.Count
                $svcGroups = @{}
                foreach ($record in $filteredEvents) {
                    $svcName = if ($record.param4 -and $record.param4 -ne '') {
                        $record.param4
                    } elseif ($record.param1 -and $record.param1 -ne '') {
                        # 回退到 param1（服务显示名称）
                        $record.param1
                    } else {
                        '(unknown)'
                    }
                    if (-not $svcGroups.ContainsKey($svcName)) {
                        $svcGroups[$svcName] = [System.Collections.Generic.List[object]]::new()
                    }
                    $svcGroups[$svcName].Add($record)
                }
                $aggregated = @()
                foreach ($kv in $svcGroups.GetEnumerator()) {
                    $svcName = $kv.Key
                    $records = $kv.Value
                    # @() 强制数组：单条记录时管道返回标量，$times[0] 会变成字符串索引
                    $times = @($records | ForEach-Object { $_.TimeCreated } | Sort-Object)
                    # 收集所有变更方向（去重）：如"按需启动→自动启动"、"自动启动→按需启动"
                    $transitions = ($records | ForEach-Object {
                        "$($_.param2)→$($_.param3)"
                    } | Select-Object -Unique) -join '; '
                    # 服务显示名称（取第一条的 param1）
                    $displayName = ($records | Select-Object -First 1).param1
                    $aggregated += [PSCustomObject][ordered]@{
                        ServiceName    = $svcName
                        DisplayName    = $displayName
                        ChangeCount    = $records.Count
                        FirstChange    = $times[0]
                        LastChange     = $times[-1]
                        Transitions    = $transitions
                    }
                }
                # 按变更次数降序排列，最频繁的服务排在前面
                $filteredEvents = $aggregated | Sort-Object -Property ChangeCount -Descending
                $count = $filteredEvents.Count
                Write-Verbose "已聚合 $rawCount 条服务启动类型变更事件为 $count 个服务统计"
            }

            # 输出 4104 系统路径过滤统计
            if ($evt.ContainsKey('FilterSystemPaths') -and $evt.FilterSystemPaths -and $Script:SystemPathFilteredCount -gt 0) {
                Write-Verbose "已过滤 $($Script:SystemPathFilteredCount) 条系统模块脚本块"
            }

            # 写入分级汇总（使用 Category 而非 LogName）
            $summary[$category][$baseName] = $filteredEvents
            Write-Verbose "已收集 $($evt.Description)  事件数:$count"
        }
        catch
        {
            # NoMatchingEventsFound 是正常情况（该时间窗口内确实无事件），不需要告警
            # 使用 FullyQualifiedErrorId 而非 Exception.Message 判断，避免中文/英文等不同语言系统的消息文本差异
            if ($_.FullyQualifiedErrorId -match 'NoMatchingEventsFound') {
                Write-Verbose "收集$($evt.Description) : 时间范围内无匹配事件"
            } else {
                Write-Warning "收集$($evt.Description) 时出错: $($_.Exception.Message)"
            }
            $summary[$category][$baseName] = @()
        }
    }

    return $summary
}

# ConvertTo-PlainTextReport -InputData (Invoke-SystemEventCollection) | Out-File -FilePath "debug.log" -Encoding UTF8
# return

# 收集进程和服务信息
function Invoke-ProcessServiceCollection
{
Write-Host "[步骤 3] 正在收集进程详细信息..." -ForegroundColor Cyan
    # 收集进程信息
    try
    {
        Write-Host "正在收集进程信息..." -ForegroundColor White
        $rawProcesses = Get-Process -ErrorAction SilentlyContinue
        
        # 转换进程信息为更易读的格式
        $processes = $rawProcesses | Select-Object Id, ProcessName, StartTime, Path,
            @{Name="WorkingSet_MB"; Expression={if($_.WorkingSet) {[math]::Round($_.WorkingSet / 1MB, 2)} else {"N/A"}}}
        
        # 获取服务与进程的关联关系
        Write-Host "正在建立服务与进程的关联关系..." -ForegroundColor White
        $serviceProcessMap = @{}
        try {
            $wmiServices = Get-CimInstance -ClassName Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.ProcessId -ne 0 }
            foreach ($service in $wmiServices) {
                $key = [string]$service.ProcessId
                $serviceProcessMap[$key] = @{
                    ServiceName = $service.Name
                }
            }
        }
        catch {
            Write-Warning "获取服务进程关联信息时出错: $($_.Exception.Message)"
        }
        # 为进程添加服务绑定信息
        if ($processes) {
            $enhancedProcesses = [System.Collections.Generic.List[object]]::new()
            foreach ($process in $processes) {
                $key = [string]$process.Id
                $serviceInfo = $serviceProcessMap[$key]
                $serviceName = if ($serviceInfo) { $serviceInfo.ServiceName } else { $null }
                $enhancedProcess = $process | Select-Object *, @{Name="ServiceName";Expression={$serviceName}}
                $enhancedProcesses.Add($enhancedProcess)
            }
            $processes = $enhancedProcesses
            Write-Verbose "已收集进程信息并建立服务关联"
        }
        else
        {
            Write-Warning "未能获取进程信息"
            $processes = @()
        }
    }
    catch
    {
        Write-Warning "收集进程信息时出错: $( $_.Exception.Message )"
        $processes = @()
    }

    # 注意：运行中服务列表（Get-Service | Running）已移除——仅有 Name/DisplayName/Status/StartType 四列，
    # 无时间维度/无路径/无启动账户，完全被步骤 6 Startup 的 Win32_Service（含 PathName/StartName/Description）
    # 和步骤 3 Processes 的 ServiceName 列覆盖。
    return @{
        Processes = $processes
    }
}

# 收集网络配置信息
function Invoke-NetworkConfigCollection
{
    Write-Host "[步骤 4] 正在收集网络配置信息..." -ForegroundColor Cyan

    $networkCommands = [ordered]@{
        "ipconfig" = {
            # 获取详细的网络配置信息，包括所有网络适配器
            $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
            # 【警告】逗号不要删除，逗号的作用是当数组只有一个元素时，仍然强制返回数组格式。
            #  天知道我调试了多久
            ,@(foreach ($adapter in $adapters)
            {
                try
                {
                    $ipConfig = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex -ErrorAction SilentlyContinue

                    # 安全获取Dhcp属性，如果不存在则使用默认值
                    $dhcpEnabled = if ($adapter.PSObject.Properties.Name -contains 'Dhcp')
                    {
                        $adapter.Dhcp
                    }
                    else
                    {
                        "N/A"
                    }
                    [PSCustomObject]@{
                        AdapterName = $adapter.Name
                        InterfaceDescription = $adapter.InterfaceDescription
                        MacAddress = $adapter.MacAddress
                        LinkSpeed = $adapter.LinkSpeed
                        Status = $adapter.Status
                        DhcpEnabled = $dhcpEnabled
                        IPAddress = ($ipConfig.IPv4Address | ForEach-Object { $_.IPAddress }) -join ', '
                        SubnetMask = ($ipConfig.IPv4Address | ForEach-Object { $_.PrefixLength }) -join ', '
                        DefaultGateway = ($ipConfig.IPv4DefaultGateway | ForEach-Object { $_.NextHop }) -join ', '
                        DNSServers = ($ipConfig.DNSServer | Where-Object { $_.AddressFamily -eq 2 } | ForEach-Object { $_.ServerAddresses }) -join ', '
                    }
                }
                catch
                {
                    Write-Warning "收集网络适配器 $( $adapter.Name ) 信息时出错: $( $_.Exception.Message )"
                    [PSCustomObject]@{
                        AdapterName = $adapter.Name
                        InterfaceDescription = $adapter.InterfaceDescription
                        MacAddress = $adapter.MacAddress
                        LinkSpeed = $adapter.LinkSpeed
                        Status = $adapter.Status
                        DhcpEnabled = "Error"
                        IPAddress = "Error collecting data"
                        SubnetMask = ""
                        DefaultGateway = ""
                        DNSServers = ""
                    }
                }
            })
        }
        "route" = {
            # 获取路由表信息 — 只保留 IPv4 有意义路由，过滤 link-local/multicast
            $routes = Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                Where-Object { $_.DestinationPrefix -ne '0.0.0.0/0' -and
                               $_.DestinationPrefix -notlike '224.*' -and
                               $_.DestinationPrefix -notlike '255.*' -and
                               $_.DestinationPrefix -ne '127.0.0.0/8' -and
                               $_.DestinationPrefix -ne '127.0.0.1/32' }
            ,@($routes | Select-Object DestinationPrefix, NextHop, InterfaceAlias, RouteMetric |
                    Sort-Object RouteMetric)
        }
        "arp" = {
            # 获取ARP表信息 — 过滤 multicast/link-local 噪声
            $neighbors = Get-NetNeighbor -ErrorAction SilentlyContinue |
                Where-Object { $_.State -ne 'Unreachable' -and
                               $_.IPAddress -notlike '224.*' -and
                               $_.IPAddress -notlike '239.*' -and
                               $_.IPAddress -notlike 'ff0*' -and
                               $_.IPAddress -notlike 'fe80*' }
            ,@($neighbors | Select-Object IPAddress, LinkLayerAddress, State, InterfaceAlias |
                    Sort-Object InterfaceAlias, IPAddress)
        }
        "network_tcp" = { Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess, CreationTime }
    }
    $summary = [ordered]@{ }
    foreach ($file in $networkCommands.Keys)
    {
        try
        {
            $summary[$file] = & $networkCommands[$file]
            Write-Verbose "已收集: $file"
        }
        catch
        {
            Write-Warning "收集 $file 时出错: $( $_.Exception.Message )"
            $summary[$file] = $null
        }
    }
    return $summary
}

# 收集IIS日志
function Invoke-IISLogCollection
{
Write-Host "[步骤 5] 正在检查并收集IIS日志..." -ForegroundColor Cyan

    # 计算时间范围（与 Invoke-SystemEventCollection 保持一致）
    $startDate = (Get-Date).AddDays(-$DaysBack)
    $endDate = $startDate.AddDays($DaysRange)
    Write-Host "IIS日志时间过滤范围: $($startDate.ToString('yyyy-MM-dd HH:mm:ss')) ~ $($endDate.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan

    # 基础日志路径
    $baseLogPaths = @(
        "$env:SystemDrive\Windows\System32\LogFiles\HTTPERR"
    )

    # 动态发现所有IIS站点日志路径
    $allIISLogPaths = @()
    $allIISLogPaths += $baseLogPaths

    Write-Host "正在动态发现IIS站点..." -ForegroundColor White

    # 方法1：通过配置发现站点（如果可用）
    try
    {
        $iisRegPath = "HKLM:\SOFTWARE\Microsoft\InetStp"
        if (Test-Path $iisRegPath)
        {
            Write-Host "检测到IIS安装，正在查找所有站点..." -ForegroundColor Cyan

            # 查找IIS配置中的日志目录
            $webConfigPath = "$env:SystemRoot\System32\inetsrv\config\applicationHost.config"
            if (Test-Path $webConfigPath)
            {
                try
                {
                    [xml]$config = Get-Content $webConfigPath -ErrorAction SilentlyContinue
                    $sites = $config.configuration.'system.webServer'.sites.site

                    if ($sites)
                    {
                        foreach ($site in $sites)
                        {
                            $siteId = $site.id
                            $siteName = $site.name
                            Write-Host "发现IIS站点: $siteName (ID: $siteId)" -ForegroundColor Green

                            # 添加标准路径
                            $standardPath = "$env:SystemDrive\inetpub\logs\LogFiles\W3SVC$siteId"
                            $legacyPath = "$env:SystemDrive\Windows\System32\LogFiles\W3SVC$siteId"

                            $allIISLogPaths += $standardPath
                            $allIISLogPaths += $legacyPath
                        }
                    }
                }
                catch
                {
                    Write-Verbose "解析IIS配置文件失败: $( $_.Exception.Message )"
                }
            }
        }
    }
    catch
    {
        Write-Verbose "读取IIS注册表配置失败: $( $_.Exception.Message )"
    }

    # 方法2：通过PowerShell IIS模块发现站点（如果可用）
    try
    {
        if (Get-Module -ListAvailable -Name WebAdministration -ErrorAction SilentlyContinue)
        {
            Import-Module WebAdministration -ErrorAction SilentlyContinue
            $websites = Get-Website -ErrorAction SilentlyContinue

            if ($websites)
            {
                foreach ($website in $websites)
                {
                    $siteId = $website.Id
                    $siteName = $website.Name
                    Write-Host "通过WebAdministration发现站点: $siteName (ID: $siteId)" -ForegroundColor Green

                    # 获取站点的日志配置
                    try
                    {
                        $logConfig = Get-WebConfiguration -Filter "system.webServer/httpLogging" -PSPath "IIS:\Sites\$siteName" -ErrorAction SilentlyContinue
                        if ($logConfig -and $logConfig.directory)
                        {
                            $customLogPath = $logConfig.directory
                            if ($customLogPath -and (Test-Path $customLogPath))
                            {
                                Write-Host "发现自定义日志路径: $customLogPath" -ForegroundColor Green
                                $allIISLogPaths += $customLogPath
                            }
                        }
                    }
                    catch
                    {
                        Write-Verbose "获取站点 $siteName 日志配置失败: $( $_.Exception.Message )"
                    }

                    # 添加标准路径
                    $standardPath = "$env:SystemDrive\inetpub\logs\LogFiles\W3SVC$siteId"
                    $legacyPath = "$env:SystemDrive\Windows\System32\LogFiles\W3SVC$siteId"

                    $allIISLogPaths += $standardPath
                    $allIISLogPaths += $legacyPath
                }
            }
        }
    }
    catch
    {
        Write-Verbose "使用WebAdministration模块失败: $( $_.Exception.Message )"
    }

    # 方法3：暴力搜索常见路径模式
    Write-Host "正在搜索常见IIS日志路径模式..." -ForegroundColor Cyan

    $searchPaths = @(
        "$env:SystemDrive\inetpub\logs\LogFiles",
        "$env:SystemDrive\Windows\System32\LogFiles"
    )

    foreach ($searchPath in $searchPaths)
    {
        if (Test-Path $searchPath)
        {
            try
            {
                $w3svcDirs = Get-ChildItem -Path $searchPath -Directory -Name "W3SVC*" -ErrorAction SilentlyContinue
                foreach ($dir in $w3svcDirs)
                {
                    $fullPath = Join-Path $searchPath $dir
                    Write-Host "发现W3SVC目录: $fullPath" -ForegroundColor Green
                    $allIISLogPaths += $fullPath
                }
            }
            catch
            {
                Write-Verbose "搜索路径 $searchPath 失败: $( $_.Exception.Message )"
            }
        }
    }

    # 去重并收集日志
    $uniqueLogPaths = @($allIISLogPaths | Sort-Object -Unique)
    $foundLogs = $false

    Write-Host "开始收集IIS日志，共发现 $( $uniqueLogPaths.Count ) 个潜在路径..." -ForegroundColor Cyan
$summary = [System.Collections.Generic.List[object]]::new()
    foreach ($logPath in $uniqueLogPaths)
    {
        if (Test-Path $logPath)
        {
            $foundLogs = $true
            Write-Host "发现IIS日志目录: $logPath" -ForegroundColor Green

            try
            {
                $logFiles = Get-ChildItem -Path $logPath -File -Name "*.*" -ErrorAction SilentlyContinue
                try
                {
                    $logFiles | ForEach-Object {
                        $logFileName = $_   # 保存管道元素，避免 catch 中 $_ 被异常对象覆盖
                        try
                        {
                            $logFilePath = Join-Path $logPath $logFileName
                            $logFileItem = Get-Item -Path $logFilePath
                            $logSize = $logFileItem.Length

                            # 按文件最后修改时间过滤，跳过时间范围外的文件
                            if ($logFileItem.LastWriteTime -lt $startDate -or $logFileItem.LastWriteTime -gt $endDate) {
                                Write-Verbose "跳过时间范围外的日志: $logFilePath (LastWriteTime: $($logFileItem.LastWriteTime))"
                                return  # 在 ForEach-Object 管道中用 return 替代 continue
                            }

                            if ($logFileName -match "\.log$") # -and $logSize -le 409600 # <= 400 KB
                            {
                                $logItem = [PSCustomObject]@{
                                    LogPath = $logFilePath
                                    LogSize = $logSize
                                    LogLastWriteTime = $logFileItem.LastWriteTime
                                    LogContent = Get-Content -Path $logFilePath -Raw
                                }
                                $summary.Add($logItem)
                                }
                                else
                                {
                                    $hashResult = Get-FileHash -Path $logFilePath -Algorithm SHA256 -ErrorAction SilentlyContinue
                                    $logItem = [PSCustomObject]@{
                                        LogPath = $logFilePath
                                        LogSize = $logSize
                                        LogLastWriteTime = $logFileItem.LastWriteTime
                                        LogHash = if ($hashResult -and $hashResult.Hash) { $hashResult.Hash } else { '' }
                                    }
                                    $summary.Add($logItem)
                                }
                            }
                        catch
                        {
                            Write-Warning "收集日志 $logPath\$logFileName 失败: $( $_.Exception.Message )"
                        }
                    }
                }
                catch
                {
                    Write-Warning "IIS日志收集失败: $( $_.Exception.Message )"
                }
            }
            catch
            {
                Write-Warning "IIS日志收集失败: $( $_.Exception.Message )"
            }
        }
        else
        {
            Write-Verbose "路径不存在: $logPath"
        }
    }

    if (-not $foundLogs)
    {
        Write-Host "未找到任何IIS日志目录" -ForegroundColor Yellow

        # 检查IIS是否安装
        try
        {
            # 检查IIS功能状态
            $iisInstalled = $false

            # 方法1：检查Windows功能
            try
            {
                $iisFeature = Get-WindowsFeature -Name IIS-WebServer -ErrorAction SilentlyContinue
                if ($iisFeature -and $iisFeature.InstallState -eq 'Installed')
                {
                    $iisInstalled = $true
                }
            }
            catch
            {
                # 在非Server版本中Get-WindowsFeature可能不可用
            }

            # 方法2：检查服务
            if (-not $iisInstalled)
            {
                $w3svcService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
                if ($w3svcService)
                {
                    $iisInstalled = $true
                }
            }

            # 方法3：检查注册表
            if (-not $iisInstalled)
            {
                if (Test-Path "HKLM:\SOFTWARE\Microsoft\InetStp")
                {
                    $iisInstalled = $true
                }
            }

            if ($iisInstalled)
            {
                Write-Host "IIS已安装但未找到日志文件，可能原因：" -ForegroundColor Yellow
                Write-Host "  1. 日志记录被禁用" -ForegroundColor Yellow
                Write-Host "  2. 日志路径被自定义到其他位置" -ForegroundColor Yellow
                Write-Host "  3. 站点从未接收过请求" -ForegroundColor Yellow
            }
            else
            {
                Write-Host "IIS未安装" -ForegroundColor Cyan
            }
        }
        catch
        {
            Write-Verbose "IIS状态检查失败: $( $_.Exception.Message )"
        }
    }
    else
    {
        Write-Host "IIS日志收集完成" -ForegroundColor Green
    }
return $summary
}

# 收集自启动项信息
function Invoke-StartupItemCollection
{
    Write-Host "[步骤 6] 正在收集自启动项信息..." -ForegroundColor Cyan

    $result = [ordered]@{}

    # 收集启动文件夹内容
    Write-Host "正在收集启动文件夹内容..." -ForegroundColor White

    $startupFolderItems = [System.Collections.Generic.List[object]]::new()
    $startupFolders = @{
        "user_startup_folder" = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
        "all_users_startup_folder" = "$env:ALLUSERSPROFILE\Microsoft\Windows\Start Menu\Programs\Startup"
    }

    foreach ($fileName in $startupFolders.Keys)
    {
        $folderPath = $startupFolders[$fileName]

        if (Test-Path $folderPath)
        {
            try
            {
                $items = @(Get-ChildItem -Path $folderPath -Recurse -ErrorAction SilentlyContinue |
                        Select-Object Name, FullName, Length, LastWriteTime, Attributes)
                if ($items) { $startupFolderItems.AddRange($items) }
                Write-Verbose "已收集启动文件夹: $folderPath"
            }
            catch
            {
                Write-Warning "收集启动文件夹 $folderPath 失败: $( $_.Exception.Message )"
            }
        }
        else
        {
            Write-Verbose "启动文件夹不存在: $folderPath"
        }
    }

    if ($startupFolderItems.Count -gt 0) { $result['StartupFolders'] = @($startupFolderItems) }

    # 收集详细的自启动项信息
    Write-Host "正在收集详细自启动项信息..." -ForegroundColor White

    # 收集WMI自启动项信息
    Write-Host "正在收集WMI启动程序详细信息..." -ForegroundColor White
    try
    {
        # 收集WMI启动命令（保留有实际信息的字段）
        $wmiStartup = @(Get-CimInstance -ClassName Win32_StartupCommand | Select-Object Name, Command, Location, User)
        if ($wmiStartup) { $result['WmiStartupCommands'] = $wmiStartup }
        Write-Verbose "已收集WMI启动命令"
        # 收集服务自启动项（只保留名称列表，因为详细信息与步骤 3 进程信息高度重叠）
        $autoServiceNames = @(Get-CimInstance -ClassName Win32_Service | Where-Object { $_.StartMode -eq 'Auto' } |
                Select-Object -ExpandProperty Name)
        if ($autoServiceNames) { $result['AutoStartServices'] = $autoServiceNames }
        Write-Verbose "已收集WMI启动信息"
    }
    catch
    {
        Write-Warning "收集WMI启动信息失败: $( $_.Exception.Message )"
    }

    # 收集MSConfig启动项
    try
    {
        Write-Host '正在收集MSConfig启动项...' -ForegroundColor White

        $msconfigItems = @()
        $msconfigPaths = @{
            'Registry' = 'HKLM:\SOFTWARE\Microsoft\Shared Tools\MSConfig\startupreg'
            'Folder' = 'HKLM:\SOFTWARE\Microsoft\Shared Tools\MSConfig\startupfolder'
        }

        foreach ($type in $msconfigPaths.Keys)
        {
            $path = $msconfigPaths[$type]
            try
            {
                if (Test-Path $path)
                {
                    $subKeys = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
                    foreach ($subKey in $subKeys)
                    {
                        $props = Get-ItemProperty -Path $subKey.PSPath -ErrorAction SilentlyContinue
                        if ($props)
                        {
                            $msconfigItems += [PSCustomObject]@{
                                Type = $type
                                Name = $subKey.PSChildName
                                Command = $props.command
                                Item = $props.item
                                Key = $props.key
                                HKey = $props.hkey
                                Location = $props.location
                                RegistryPath = $path
                            }
                        }
                    }
                    Write-Verbose "已收集MSConfig $type 项目"
                }
            }
            catch
            {
                Write-Verbose "MSConfig $type 访问失败: $( $_.Exception.Message )"
            }
        }

        if ($msconfigItems) { $result['MSConfigItems'] = $msconfigItems }
        Write-Verbose "已导出MSConfig启动项: $( $msconfigItems.Count ) 个项目"

        # 收集注册表自启动位置
        Write-Host '正在收集注册表启动项...' -ForegroundColor White

        $extendedRegPaths = @(
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices',
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunServicesOnce',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunServicesOnce',
            'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Run',
            'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnce',
            'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
            'HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run',
            'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Shell',
            'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ShellServiceObjectDelayLoad',
            'HKCU:\SOFTWARE\Policies\Microsoft\Windows\System\Scripts',
            'HKLM:\SOFTWARE\Policies\Microsoft\Windows\System\Scripts'
        )

        # Winlogon 路径只关注与自启动/持久化相关的键名，其他属性是系统默认设置，不是启动项
        $winlogonKeys = @('Shell', 'Userinit', 'Taskman', 'AppSetup', 'GinaDLL', 'System', 'VmApplet', 'UIHost')

        $startupItems = @()
        foreach ($path in $extendedRegPaths)
        {
            try
            {
                if (Test-Path $path)
                {
                    $isWinlogon = $path -like '*Winlogon*'
                    $items = Get-ItemProperty -Path $path -ErrorAction SilentlyContinue
                    if ($items)
                    {
                        $validProperties = $items.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' }
                        foreach ($prop in $validProperties)
                        {
                            if ($prop.Value -is [byte[]]) { continue }
                            # Winlogon 路径：只保留与自启动相关的键名
                            if ($isWinlogon -and $prop.Name -notin $winlogonKeys) { continue }
                            $startupItems += [PSCustomObject]@{
                                RegistryPath = $path
                                Name = $prop.Name
                                Value = $prop.Value
                            }
                        }
                    }
                }
            }
            catch
            {
                $startupItems += [PSCustomObject]@{
                    RegistryPath = $path
                    Name = $null
                    Value = "access denied: $( $_.Exception.Message )"
                }
            }
        }

        # 收集特定注册表键值
        $specificValues = @(
            @{ Path = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Windows'; Name = 'load'; Description = '用户登录时加载的程序' },
            @{ Path = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Windows'; Name = 'run'; Description = '用户登录时运行的程序' }
        )

        foreach ($item in $specificValues)
        {
            try
            {
                if (Test-Path $item.Path)
                {
                    $value = Get-ItemProperty -Path $item.Path -Name $item.Name -ErrorAction SilentlyContinue
                    if ($value -and $value.($item.Name))
                    {
                        $startupItems += [PSCustomObject]@{
                            RegistryPath = $item.Path
                            Name = $item.Name
                            Value = $value.($item.Name)
                            Description = $item.Description
                        }
                    }
                    else
                    {
                        # value not set：跳过，不产生噪声记录
                    }
                }
                else
                {
                    # path not exists：跳过，不产生噪声记录
                }
            }
            catch
            {
                $startupItems += [PSCustomObject]@{
                    RegistryPath = $item.Path
                    Name = $item.Name
                    Value = "access error: $( $_.Exception.Message )"
                    Description = $item.Description
                }
            }
        }

        if ($startupItems) { $result['RegistryStartup'] = $startupItems }
        Write-Verbose "已导出扩展注册表启动项: $( $startupItems.Count ) 个项目"

        # 收集浏览器扩展启动项
        Write-Host '正在收集浏览器扩展启动项...' -ForegroundColor White

        $browserExtensions = @()
        $browserPaths = @{
            'BHO_x64' = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects'
            'BHO_x86' = 'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects'
            'Toolbar_x64' = 'HKLM:\SOFTWARE\Microsoft\Internet Explorer\Toolbar'
            'Toolbar_x86' = 'HKLM:\SOFTWARE\Wow6432Node\Microsoft\Internet Explorer\Toolbar'
        }

        foreach ($pathType in $browserPaths.Keys)
        {
            $path = $browserPaths[$pathType]
            try
            {
                if (Test-Path $path)
                {
                    $subKeys = Get-ChildItem -Path $path -ErrorAction SilentlyContinue
                    foreach ($subKey in $subKeys)
                    {
                        $props = Get-ItemProperty -Path $subKey.PSPath -ErrorAction SilentlyContinue
                        if ($props)
                        {
                            $browserExtensions += [PSCustomObject]@{
                                Type = if ($pathType -like '*BHO*')
                                {
                                    'Browser Helper Object'
                                }
                                else
                                {
                                    'Toolbar'
                                }
                                Architecture = if ($pathType -like '*x64*')
                                {
                                    'x64'
                                }
                                else
                                {
                                    'x86'
                                }
                                CLSID = $subKey.PSChildName
                                Name = $props.'(default)'
                                RegistryPath = $path
                                SubKeyPath = $subKey.PSPath
                            }
                        }
                    }
                    Write-Verbose "已收集 $pathType 浏览器扩展"
                }
            }
            catch
            {
                Write-Verbose "$pathType 浏览器扩展访问失败: $( $_.Exception.Message )"
            }
        }

        if ($browserExtensions) { $result['BrowserExtensions'] = $browserExtensions }
        Write-Verbose "已导出浏览器扩展: $( $browserExtensions.Count ) 个项目"

        Write-Host '[成功] 自启动项收集完成' -ForegroundColor Green
    }
    catch
    {
        Write-Warning "PowerShell自启动项收集失败: $( $_.Exception.Message )"
    }

    # 计划任务
    try
    {
        Write-Host "正在收集计划任务..." -ForegroundColor White
        $tasks = Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' } |
                Select-Object TaskName, TaskPath, State,
                @{ Name = 'Triggers'; Expression = { ($_.Triggers | ForEach-Object { $_.CimClass.CimClassName }) -join ';' } },
                @{ Name = 'Actions'; Expression = { ($_.Actions | ForEach-Object { $_.Execute }) -join ';' } },
                @{ Name = 'RunAsUser'; Expression = { $_.Principal.UserId } }

        $items = @($tasks)
        if ($items) { $result['ScheduledTasks'] = $items }
        Write-Host "计划任务信息收集完成" -ForegroundColor Green
    }
    catch
    {
        Write-Warning "计划任务信息收集失败: $( $_.Exception.Message )"
    }

    Write-Host "自启动项收集完成" -ForegroundColor Green
    return $result
}

# 解析USN记录的辅助函数
function Parse-USNRecords {
    param(
        [string]$Drive,
        [array]$RawData
    )

    $records = @()
    $fileRefPattern = '^File Ref#\s*:\s*(0x[0-9a-fA-F]+)'

    for ($i = 0; $i -lt $RawData.Count - 5; $i++) {
        $line = $RawData[$i]
        if ($line -notmatch $fileRefPattern) { continue }

        $fileRef = $matches[1]
        $parentRef = if ($RawData[$i + 1] -match ':\s*(.+)') { $matches[1].Trim() } else { "" }
        $usnHex = if ($RawData[$i + 2] -match ':\s*(.+)') { $matches[1].Trim() } else { "" }
        $reasonHex = if ($RawData[$i + 4] -match ':\s*(.+)') { $matches[1].Trim() } else { "" }
        $name = if ($RawData[$i + 5] -match ':\s*(.+)') { $matches[1].Trim() } else { "" }

        if (-not ($fileRef -and $usnHex -and $name)) { continue }

        try {
            $fileRefNum = [Convert]::ToInt64($fileRef, 16)
            $parentRefNum = if ($parentRef) { [Convert]::ToInt64($parentRef, 16) } else { 0 }
            $usnNum = [Convert]::ToInt64($usnHex, 16)
            $reasonNum = if ($reasonHex) { [Convert]::ToInt64($reasonHex, 16) } else { 0 }

            $filePath = Get-FilePathById -Drive $Drive -FileRef $fileRefNum
            $fileItem = if ($filePath -and (Test-Path $filePath)) { Get-Item $filePath -ErrorAction SilentlyContinue } else { $null }
            $lastWriteTime = if ($fileItem) { $fileItem.LastWriteTime } else { $null }
            $fileHash = if ($fileItem) {
                $hashResult = Get-FileHash -Path $filePath -Algorithm SHA256 -ErrorAction SilentlyContinue
                # Write-Verbose "Get-FileHash -Path $filePath -Algorithm SHA256 -ErrorAction SilentlyContinue"
                if ($hashResult -and $hashResult.Hash) { $hashResult.Hash } else { $null }
            } else { $null }

            $records += [PSCustomObject]@{
                Drive = $Drive
                FileRef = $fileRefNum
                ParentRef = $parentRefNum
                Usn = $usnNum
                Reason = "0x{0:X8}" -f $reasonNum
                Name = $name
                AbsolutePath = $filePath
                Time = $lastWriteTime
                FileHash = $fileHash
            }
        }
        catch {
            Write-Verbose "跳过无效USN记录: $line，错误: $($_.Exception.Message)"
        }
    }

    return $records
}

# 通过文件ID获取路径的辅助函数
function Get-FilePathById {
    param(
        [string]$Drive,
        [int64]$FileRef
    )

    try {
        $path = fsutil file queryfilenamebyid $Drive $FileRef 2>$null
        if ($path) {
            # 清理路径前缀
            $path = $path -replace '^A random link name to this file is ', ''
            $path = $path -replace '^\\\\\?\\', ''
            return $path
        }
    }
    catch {
        Write-Warning "获取路径时出错: $($_.Exception.Message)"
        # 静默处理错误
    }
    return "<无法获取路径>"
}

# 收集USN日志（文件系统变更记录）
function Invoke-USNLogCollection
{
    Write-Host "[步骤 7] 正在收集USN日志（文件系统变更记录）..." -ForegroundColor Cyan

    # 获取所有固定驱动器
    $drives = Get-CimInstance -ClassName Win32_LogicalDisk |
              Where-Object { $_.DriveType -eq 3 } |
              Select-Object -ExpandProperty DeviceID

    if (-not $drives) {
        Write-Warning "未找到可用的固定驱动器"
        return ,@()
    }

    $summary = @(foreach ($drive in $drives) {
        Write-Host "正在处理驱动器 $drive ..." -ForegroundColor White
        # 检查USN日志是否可用
        $journal = fsutil usn queryjournal $drive 2>$null
        if (-not $journal) {
            Write-Host "跳过驱动器 $drive : 不支持USN日志（可能为非NTFS文件系统）" -ForegroundColor Yellow
            continue
        }

        # 提取Next USN —— 若变更日志未启用（如引导/恢复分区），queryjournal 有输出但无 Next Usn 字段
        $nextUsnLine = $journal | Select-String "Next Usn" | Select-Object -First 1
        if (-not $nextUsnLine) {
            Write-Host "跳过驱动器 $drive : USN变更日志未启用（该驱动器可能为引导/恢复分区）" -ForegroundColor Yellow
            continue
        }

        $nextUsnHex = $nextUsnLine.ToString().Split(":")[1].Trim()
        $nextUsn = [Convert]::ToInt64($nextUsnHex, 16)

        # 根据MaxEventCount计算USN范围大小
        $targetRecords = [int]($MaxEventCount * $UsnMultiplier)
        $estimatedBytesPerRecord = 2MB / 333
        $rangeSize = [Math]::Min([int64]($targetRecords * $estimatedBytesPerRecord * 1.01 + 100), 10MB)  # 最大限制10MB
        $startUsn = [Math]::Max($nextUsn - $rangeSize, 0)

        Write-Verbose "读取 $drive USN范围: $startUsn 到 $nextUsn (目标约 $targetRecords 条记录)"

        # 收集USN数据
        $rawData = fsutil usn enumdata 0 $startUsn $nextUsn $drive 2>$null
        if (-not $rawData) {
            Write-Warning "$drive 没有USN数据"
            continue
        }

        # 保存原始数据
        $driveLetter = $drive.Replace(":", "")

        # 解析USN记录并使用Select-Object限制到MaxEventCount条
        $allRecords = @(& Parse-USNRecords -Drive $drive -RawData $rawData)
        Write-Verbose "原始 $($allRecords.Count) 条记录"
        $records = @($allRecords | Select-Object -First $MaxEventCount)

        if ($records.Count -gt 0) {
            Write-Host "驱动器 $drive 收集完成: 原始 $($allRecords.Count) 条记录，筛选后 $($records.Count) 条记录" -ForegroundColor Green
        }
        $records
    })

    Write-Host "USN日志收集完成，成功处理 $($summary.Count) 个驱动器" -ForegroundColor Cyan
    return ,$summary
}

function Test-FileSignature {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )

    try {
        if(Test-Path -Path $FilePath){
            $signature = Get-AuthenticodeSignature -FilePath $FilePath -ErrorAction SilentlyContinue
            $fileHash = Get-FileHash -Path $FilePath -Algorithm SHA256
            if ($signature)
            {
                $result = [PSCustomObject]@{
                    FilePath = $FilePath
                    Status = $signature.Status
                    StatusMessage = $signature.StatusMessage
                    FileHash = $fileHash.Hash
                }
            }
            else
            {
                $result = [PSCustomObject]@{
                    FilePath = $FilePath
                    Status = "Error"
                    StatusMessage = '无法检查签名: $signature为空'
                    FileHash = $fileHash.Hash
                }
            }
        }
        else
        {
            $result = [PSCustomObject]@{
                FilePath = $FilePath
                Status = "NotFound"
                StatusMessage = "文件不存在"
                FileHash = ""
            }
        }

        return $result
    }
    catch {
        return [PSCustomObject]@{
            FilePath = $FilePath
            Status = "Error"
            StatusMessage = "无法检查签名: $($_.Exception.Message)"
            FileHash = ""
        }
    }
}

function Test-IsPEBinary {
    <#
    .SYNOPSIS
        通过读取文件头部魔数判断是否为 PE 二进制文件（MZ header）。
        避免对文本文件、配置文件等误做签名检查。
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    try {
        $stream = [System.IO.File]::OpenRead($FilePath)
        try {
            if ($stream.Length -lt 2) { return $false }
            $header = New-Object byte[] 2
            [void]$stream.Read($header, 0, 2)
            # MZ magic: 0x4D 0x5A
            return ($header[0] -eq 0x4D -and $header[1] -eq 0x5A)
        }
        finally {
            $stream.Close()
        }
    }
    catch {
        return $false
    }
}

function Get-ExecutableFiles {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Directory,

        [Parameter(Mandatory=$true)]
        [string[]]$Extensions,

        [Parameter(Mandatory=$false)]
        [datetime]$StartDate,

        [Parameter(Mandatory=$false)]
        [datetime]$EndDate,

        [Parameter(Mandatory=$false)]
        [int]$MaxDepth = 3
    )

    # 构建正则表达式模式，例如：.*.exe|.*.com|.*.dll
    $regexPattern = ($Extensions | ForEach-Object { '.*' + [regex]::Escape($_) }) -join "|"

    try {
        # MaxDepth 0 = 仅顶层，不递归；>0 = 递归到指定深度
        if ($MaxDepth -le 0) {
            $allFiles = Get-ChildItem -Path $Directory -File -ErrorAction SilentlyContinue
        } else {
            $allFiles = Get-ChildItem -Path $Directory -File -Recurse -Depth $MaxDepth -ErrorAction SilentlyContinue
        }

        # 使用正则表达式过滤扩展名（单次过滤）
        $filteredByExt = $allFiles | Where-Object {
            $_.FullName -match $regexPattern
        }

        # 按 LastWriteTime（最后修改时间）过滤，而非 CreationTime
        # 恶意文件可能伪造 CreationTime，但 LastWriteTime 更能反映实际活动
        if ($StartDate -and $EndDate) {
            $filteredByExt = $filteredByExt | Where-Object {
                $_.LastWriteTime -ge $StartDate -and $_.LastWriteTime -le $EndDate
            }
        }

        # 验证 PE 魔数（MZ header），排除被重命名为 .exe/.dll 的非二进制文件
        $verifiedFiles = $filteredByExt | Where-Object {
            Test-IsPEBinary -FilePath $_.FullName
        }

        return $verifiedFiles
    }
    catch {
        Write-Warning "无法访问目录 $($Directory): $($_.Exception.Message)"
        return @()
    }
}

# 主函数
function Check-Signature {
    Write-Host "[步骤 8] 正在检查常见目录二进制文件签名..." -ForegroundColor Cyan
    # 计算时间范围
    $startDate = (Get-Date).AddDays(-$DaysBack)
    $endDate = $startDate.AddDays($DaysRange)

    # ── 扫描目录列表（分层递归深度） ────────────────────────────────
    # 性能策略：大目录仅扫顶层（Depth 0），小目录浅递归（Depth 1）
    #
    #   ┌──────────────────────────────────┬──────────┬───────────────────────┐
    #   │ 路径                             │ Depth    │ 原因                  │
    #   ├──────────────────────────────────┼──────────┼───────────────────────┤
    #   │ C:\Windows                       │ 0 (顶层) │ 文件极多，仅查顶层投放 │
    #   │ C:\Windows\System32              │ 0 (顶层) │ 同上，已独立扫描       │
    #   │ C:\ProgramData                   │ 0 (顶层) │ 子目录多且深           │
    #   │ C:\Users\*\AppData\Local         │ 0 (顶层) │ 子目录巨大             │
    #   │ C:\Users\*\AppData\Roaming       │ 0 (顶层) │ 子目录巨大             │
    #   │ C:\Windows\Temp                  │ 1        │ 高频投放，文件较少     │
    #   │ C:\Users\*\AppData\Local\Temp    │ 1        │ 高频投放，文件较少     │
    #   │ C:\Users\*\Downloads             │ 1        │ 社工入口，文件较少     │
    #   │ C:\Users\*\Desktop               │ 1        │ 桌面执行文件           │
    #   │ C:\Temp                          │ 1        │ 非标准临时目录         │
    #   └──────────────────────────────────┴──────────┴───────────────────────┘
    #
    # 数据结构：@{ Path = Depth } 字典，每个目录携带自己的递归深度
    $scanTargets = [ordered]@{}

    # 静态大目录 — Depth 0（仅顶层）
    $scanTargets["$env:SystemDrive\Windows"]         = 0
    $scanTargets["$env:SystemDrive\Windows\System32"] = 0
    $scanTargets["$env:SystemDrive\ProgramData"]      = 0

    # 静态小目录 — Depth 1（浅递归）
    $scanTargets["$env:SystemDrive\Windows\Temp"]     = 1
    $scanTargets["$env:SystemDrive\Temp"]             = 1

    # 动态展开每个用户目录下的子路径
    $usersRoot = "$env:SystemDrive\Users"
    if (Test-Path $usersRoot) {
        $userFolders = Get-ChildItem -Path $usersRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notin @('Public', 'Default', 'Default User', 'All Users') }
        foreach ($uf in $userFolders) {
            # 大目录 — Depth 0
            $scanTargets[(Join-Path $uf.FullName "AppData\Local")]   = 0
            $scanTargets[(Join-Path $uf.FullName "AppData\Roaming")] = 0
            # 小目录 — Depth 1
            $scanTargets[(Join-Path $uf.FullName "AppData\Local\Temp")] = 1
            $scanTargets[(Join-Path $uf.FullName "Downloads")]          = 1
            $scanTargets[(Join-Path $uf.FullName "Desktop")]            = 1
        }
    }

    $ExecutableExtensions = @(".exe", ".dll", ".sys", ".ocx", ".drv", ".cpl", ".scr", ".com")

    Write-Host "开始检查数字签名..." -ForegroundColor Cyan
    Write-Host "目标目录 ($($scanTargets.Count) 个):" -ForegroundColor Cyan
    foreach ($entry in $scanTargets.GetEnumerator()) {
        $depthLabel = if ($entry.Value -eq 0) { "仅顶层" } else { "深度 $($entry.Value)" }
        Write-Host "  - $($entry.Key)  [$depthLabel]" -ForegroundColor Cyan
    }
    Write-Host "扫描的文件类型: $($ExecutableExtensions -join ', ')" -ForegroundColor Cyan
    Write-Host "时间范围: 检查 LastWriteTime 在 $($startDate.ToString('yyyy-MM-dd HH:mm:ss')) ~ $($endDate.ToString('yyyy-MM-dd HH:mm:ss')) 内的文件" -ForegroundColor Cyan
    Write-Host ""

    # 检查所有目标目录是否存在，保留有效目录及其深度
    $validTargets = [ordered]@{}
    foreach ($entry in $scanTargets.GetEnumerator()) {
        if (Test-Path -Path $entry.Key) {
            $validTargets[$entry.Key] = $entry.Value
        } else {
            Write-Verbose "目标目录不存在，跳过: $($entry.Key)"
        }
    }

    if ($validTargets.Count -eq 0) {
        Write-Warning "所有指定的目标目录都不存在"
        return ,@()
    }
    Write-Host "有效目录: $($validTargets.Count) 个" -ForegroundColor Green

    # ── 扫描可执行文件（分层递归深度、按 LastWriteTime 过滤、PE 魔数校验） ──
    Write-Host "正在扫描可执行文件（分层递归深度、PE 魔数校验）..." -ForegroundColor Yellow
    $executableFiles = @()
    foreach ($entry in $validTargets.GetEnumerator()) {
        $dir = $entry.Key
        $depth = $entry.Value
        Write-Host "  - $dir" -ForegroundColor Yellow
        $files = Get-ExecutableFiles -Directory $dir -Extensions $ExecutableExtensions -StartDate $startDate -EndDate $endDate -MaxDepth $depth
        if ($files) {
            $executableFiles += @($files)
        }
    }

    if ($executableFiles.Count -eq 0) {
        Write-Host "未找到在指定时间范围内修改的 PE 二进制文件" -ForegroundColor Yellow
        return ,@()
    }

    Write-Host "找到 $($executableFiles.Count) 个已验证的 PE 二进制文件（LastWriteTime 在时间范围内）" -ForegroundColor Green
    Write-Host "开始检查数字签名..." -ForegroundColor Yellow
    Write-Host ""

    # 检查每个文件的签名
    $signatureResults = @()
    $counter = 0

    foreach ($file in $executableFiles) {
        $counter++
        Write-Progress -Activity "检查数字签名" -Status "正在检查: $($file.Name)" -PercentComplete (($counter / $executableFiles.Count) * 100)

        $result = Test-FileSignature -FilePath $file.FullName
        $signatureResults += $result
    }

    Write-Progress -Activity "检查数字签名" -Completed
    Write-Host "签名检查完成，共检查 $($signatureResults.Count) 个文件" -ForegroundColor Green
    return ,$signatureResults
}

# 收集 PSReadLine 命令历史（所有用户）
function Invoke-PSReadLineCollection
{
    Write-Host "[步骤 9] 正在收集 PSReadLine 命令历史..." -ForegroundColor Cyan

    $summary = @()

    # PSReadLine 历史文件的相对路径（位于各用户 AppData 下）
    $relPath = "AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"

    # 获取所有用户 profile 目录
    $usersRoot = "$env:SystemDrive\Users"
    if (-not (Test-Path $usersRoot)) {
        Write-Warning "用户目录 $usersRoot 不存在"
        return $summary
    }

    $userDirs = Get-ChildItem -Path $usersRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notin @('Public', 'Default', 'Default User', 'All Users') }

    if (-not $userDirs) {
        Write-Host "未找到任何用户目录" -ForegroundColor Yellow
        return $summary
    }

    foreach ($userDir in $userDirs) {
        $historyPath = Join-Path $userDir.FullName $relPath
        $userName = $userDir.Name

        if (-not (Test-Path $historyPath)) {
            Write-Verbose "用户 $userName 的 PSReadLine 历史文件不存在: $historyPath"
            continue
        }

        try {
            $fileItem = Get-Item $historyPath -ErrorAction SilentlyContinue
            if (-not $fileItem -or $fileItem.Length -eq 0) {
                Write-Verbose "用户 $userName 的历史文件为空"
                continue
            }

            Write-Host "  发现用户 $userName 的 PSReadLine 历史 ($([Math]::Round($fileItem.Length / 1KB, 1)) KB)" -ForegroundColor Green

            # 读取历史命令（限制最多 50 条，取最近的）
            $maxLines = 50
            $allLines = @(Get-Content -Path $historyPath -Encoding UTF8 -ErrorAction SilentlyContinue)
            $totalLines = $allLines.Count

            if ($totalLines -gt $maxLines) {
                $lines = $allLines[($totalLines - $maxLines)..($totalLines - 1)]
            } else {
                $lines = $allLines
            }

            # 构建用户历史记录对象（仅保留关键字段）
            $userHistory = [ordered]@{
                UserName    = $userName
                HistoryPath = $historyPath
                TotalLines  = $totalLines
                Commands    = @($lines | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
            }

            $summary += [PSCustomObject]$userHistory
            Write-Host "  用户 $userName : 共 $totalLines 条命令，采集 $($lines.Count) 条" -ForegroundColor White
        }
        catch {
            Write-Warning "读取用户 $userName 的 PSReadLine 历史失败: $($_.Exception.Message)"
        }
    }

    if ($summary.Count -eq 0) {
        Write-Host "未找到任何 PSReadLine 历史文件" -ForegroundColor Yellow
    } else {
        Write-Host "PSReadLine 历史收集完成：共 $($summary.Count) 个用户" -ForegroundColor Green
    }

    return ,$summary
}

# 最终完成提示
function Write-Summary
{
    param(
        [Parameter(Mandatory = $true)]
        [PSCustomObject]
        $summary
    )
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "正在生成收集报告..." -ForegroundColor White
    Write-Host ("=" * 60) -ForegroundColor Cyan

    try
    {
        Write-Host ("=" * 60) -ForegroundColor Cyan
        Write-Host "处理报告格式中，请耐心等待..." -ForegroundColor White
        Write-Host ("=" * 60) -ForegroundColor Cyan
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $report = Join-Path $Script:Directories.Output "log_$( $env:COMPUTERNAME )_$timestamp.txt"
        Write-Verbose $summary
        ConvertTo-PlainTextReport -InputData $summary | Out-File -FilePath $report -Encoding UTF8
    }
    catch
    {
        Write-Warning "生成收集报告失败: $_"
    }
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "收集完成！" -ForegroundColor Green
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "输出文件: " -NoNewline -ForegroundColor White
    Write-Host ""
    Write-Host "详细信息请查看: " -NoNewline -ForegroundColor White
    Write-Host $report -ForegroundColor Cyan
    Write-Host ""

    # 显示收集统计
    try
    {
        $totalFiles = (Get-ChildItem $Script:Directories.Output -Recurse -File).Count
        $totalSize = (Get-ChildItem $Script:Directories.Output -Recurse -File | Measure-Object -Property Length -Sum).Sum
        $totalSizeMB = [Math]::Round($totalSize / 1MB, 2)

        Write-Host "收集统计:" -ForegroundColor White
        Write-Host "  总文件数: $totalFiles" -ForegroundColor Green
        Write-Host "  总大小: $totalSizeMB MB" -ForegroundColor Green
    }
    catch
    {
        $errorMessage = $_.Exception.Message
        Write-Verbose "无法计算收集统计: $errorMessage"
    }

    Write-Host "按任意键退出..." -ForegroundColor Yellow

    # 只在交互模式下等待用户输入（通过命令行参数指定步骤时跳过）
    if ([Environment]::UserInteractive -and -not $Script:StepChoiceProvided)
    {
        try
        {
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        catch
        {
            # 在非交互环境中忽略错误
        }
    }
}

function Main
{
    # 获取用户选择
    $UserChoice = Get-UserChoice
    $ExecuteAll = ($UserChoice -eq 0)

    if ($ExecuteAll)
    {
        Write-Host "[信息] 将执行所有步骤" -ForegroundColor Cyan
    }
    else
    {
        Write-Host "[信息] 将执行步骤 $UserChoice - $( $Script:Steps[$UserChoice] )" -ForegroundColor Cyan
    }
    Write-Host ""

    Initialize-Parameters
    Initialize-OutputDirectories
    Check-Main

    # ── 分步计时初始化 ─────────────────────────────────────────────────
    $totalStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $executionTiming = [ordered]@{}

    $summary = [ordered]@{}
    try
    {
    if ($ExecuteAll -or $UserChoice -eq 1)
    {
        Write-Host "[Timing] Step 1/9 开始: 收集系统基本信息"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.SystemInfo = Invoke-SystemInfoCollection
        $sw.Stop()
        $executionTiming["Step1_SystemInfo"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 1/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 2)
    {
        Write-Host "[Timing] Step 2/9 开始: 收集关键安全事件"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.SystemEvent = Invoke-SystemEventCollection
        $sw.Stop()
        $executionTiming["Step2_SystemEvent"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 2/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 3)
    {
        Write-Host "[Timing] Step 3/9 开始: 收集进程信息"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $item = Invoke-ProcessServiceCollection
        $summary.Processes = if ($item -and $item.ContainsKey('Processes')){$item.Processes} else {$null}
        $sw.Stop()
        $executionTiming["Step3_Process"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 3/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 4)
    {
        Write-Host "[Timing] Step 4/9 开始: 收集网络配置信息"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.Network = Invoke-NetworkConfigCollection
        $sw.Stop()
        $executionTiming["Step4_Network"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 4/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 5)
    {
        Write-Host "[Timing] Step 5/9 开始: 检查并收集IIS日志"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.IISLogs = Invoke-IISLogCollection
        $sw.Stop()
        $executionTiming["Step5_IISLogs"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 5/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 6)
    {
        Write-Host "[Timing] Step 6/9 开始: 收集自启动项信息"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.Startup = Invoke-StartupItemCollection
        $sw.Stop()
        $executionTiming["Step6_Startup"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 6/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 7)
    {
        Write-Host "[Timing] Step 7/9 开始: 收集USN日志"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.USNLogs = Invoke-USNLogCollection
        $sw.Stop()
        $executionTiming["Step7_USNLogs"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 7/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 8)
    {
        Write-Host "[Timing] Step 8/9 开始: 检查文件数字签名"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.CheckSignature = Check-Signature
        $sw.Stop()
        $executionTiming["Step8_CheckSignature"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 8/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    if ($ExecuteAll -or $UserChoice -eq 9)
    {
        Write-Host "[Timing] Step 9/9 开始: 收集 PSReadLine 命令历史"
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $summary.PSReadLineHistory = Invoke-PSReadLineCollection
        $sw.Stop()
        $executionTiming["Step9_PSReadLineHistory"] = "$([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
        Write-Host "[Timing] Step 9/9 完成: $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    }
    }
    catch
    {
        Write-Warning "执行时出现错误，日志收集不完全：$($_.Exception.Message)"
    }

    # ── 记录总耗时 ─────────────────────────────────────────────────────
    $totalStopwatch.Stop()
    $executionTiming["TotalElapsed"] = "$([Math]::Round($totalStopwatch.Elapsed.TotalSeconds, 1))s"
    Write-Host "[Timing] 全部步骤完成，总耗时: $($executionTiming['TotalElapsed'])"

    # 注入 _CollectionMeta：记录运行时参数（在 Check-Main 动态调整后的实际值）+ 机器标识
    $summary._CollectionMeta = [ordered]@{
        ScriptVersion      = $Script:Config.Version
        ComputerName       = $env:COMPUTERNAME
        RunAsUser          = $env:USERNAME
        DaysBack           = $DaysBack
        DaysRange          = $DaysRange
        MaxEventCount      = $MaxEventCount
        UsnMultiplier      = $UsnMultiplier
        CollectionTimestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }

    # 注入 _ExecutionTiming：各步骤耗时统计
    $summary._ExecutionTiming = $executionTiming

    Write-Summary -summary $summary
}
Main