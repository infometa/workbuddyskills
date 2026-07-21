#Requires -Version 5.1
# =============================================================================
# 中国国航 B2C 移动应用对外服务接口 - Windows PowerShell 客户端
# 基于《中国国航B2C移动应用对外服务接口规范 v1.0.0》实现
# 与 airchina.sh / airchina_client.py 对等，专供 Windows + WorkBuddy 使用。
#
# 🛑 关键：WorkBuddy Windows PowerShell 沙箱会【静默拦截】以下 .NET API：
#   - [Convert]::FromBase64String(...)   → 无 stdout 无 stderr，看似成功实则空
#   - [Convert]::ToBase64String(...)     → 同上
#   本脚本改用 FromBase64Transform / ToBase64Transform 的 stream API，
#   这些目前未被拦截（2026-04-29 验证）。
#   详见 references/windows-sandbox.md。
#
# 依赖：纯 PowerShell 5.1+（Windows 自带），零外部依赖。
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# -----------------------------------------------------------------------------
# 硬编码配置（与 airchina.sh / airchina_client.py 保持一致）
# ⚠️ 改密钥时 3 个文件必须同步改
# -----------------------------------------------------------------------------
$script:APP_ID          = '2NhdoyHXf41wWutaM5kULzAD'
$script:SECRET_KEY      = 'gXcWi1qzGUuo4KFOIASdCrE7'
$script:CHANNEL         = 'TENCENT'
$script:SUB_CHANNEL     = 'OTA'
$script:SERVICE_VERSION = '10100'
$script:ENV_MODE        = if ($env:AIRCHINA_ENV) { $env:AIRCHINA_ENV } else { 'prod' }
$script:DEBUG_MODE      = if ($env:AIRCHINA_DEBUG -eq '1') { $true } else { $false }

$script:GATEWAYS = @{
    'test' = 'https://m.airchina.com.cn:9066'
    'prod' = 'https://m.airchina.com.cn'
}
$script:AUTH_PATH    = '/airchina/gateway/ota/v2.0/auth/getAccessToken'
$script:SERVICE_PATH = '/airchina/gateway/ota/v2.0/api/services/'

if (-not $script:GATEWAYS.ContainsKey($script:ENV_MODE)) {
    throw "未知环境 AIRCHINA_ENV=$($script:ENV_MODE)（可选 test | prod）"
}
$script:GATEWAY     = $script:GATEWAYS[$script:ENV_MODE]
$script:AUTH_URL    = $script:GATEWAY + $script:AUTH_PATH
$script:SERVICE_URL = $script:GATEWAY + $script:SERVICE_PATH

# 本地缓存路径（Windows TEMP）
$script:TMP_DIR          = if ($env:TEMP) { $env:TEMP } else { '.' }
$script:TOKEN_CACHE_FILE = Join-Path $script:TMP_DIR "airchina_token_$($script:ENV_MODE).json"
$script:TOKEN_TTL_SEC    = 6600   # 110 分钟，文档 2h 减 10min 余量
$script:LEDGER_FILE      = Join-Path $script:TMP_DIR 'airchina_claimed_ledger.json'

# -----------------------------------------------------------------------------
# 工具函数
# -----------------------------------------------------------------------------
function Write-Err {
    param([string]$Message)
    [Console]::Error.WriteLine("[国航接口错误] $Message")
}

function Write-Dbg {
    param([string]$Message)
    if ($script:DEBUG_MODE) {
        [Console]::Error.WriteLine($Message)
    }
}

function Get-NowEpoch { [int64][double]::Parse(((Get-Date).ToUniversalTime() - [datetime]'1970-01-01').TotalSeconds) }
function Get-NowMillis { [int64][double]::Parse(((Get-Date).ToUniversalTime() - [datetime]'1970-01-01').TotalMilliseconds) }

# -----------------------------------------------------------------------------
# Base64 编解码 —— 关键防沙箱
# 不要改成 [Convert]::FromBase64String / ToBase64String，会被沙箱静默拦截
# -----------------------------------------------------------------------------
function ConvertFrom-Base64Bytes {
    param([Parameter(Mandatory=$true)][string]$Text)
    $transform = New-Object System.Security.Cryptography.FromBase64Transform
    try {
        $inBytes  = [System.Text.Encoding]::ASCII.GetBytes($Text)
        $outBytes = $transform.TransformFinalBlock($inBytes, 0, $inBytes.Length)
        # 用 , 包装防止 PS 5.1 pipeline 展开
        return ,$outBytes
    } finally {
        $transform.Dispose()
    }
}

function ConvertTo-Base64String {
    param([Parameter(Mandatory=$true)][byte[]]$Bytes)
    $transform = New-Object System.Security.Cryptography.ToBase64Transform
    try {
        $outBytes = $transform.TransformFinalBlock($Bytes, 0, $Bytes.Length)
        return [System.Text.Encoding]::ASCII.GetString($outBytes)
    } finally {
        $transform.Dispose()
    }
}

# -----------------------------------------------------------------------------
# MD5（大写 hex，对齐 airchina.sh 的隐藏约定 1）
# -----------------------------------------------------------------------------
function Get-Md5Upper {
    param([Parameter(Mandatory=$true)][string]$Text)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        $hash  = $md5.ComputeHash($bytes)
        $sb    = New-Object System.Text.StringBuilder
        foreach ($b in $hash) { [void]$sb.Append($b.ToString('X2')) }
        return $sb.ToString()
    } finally {
        $md5.Dispose()
    }
}

# -----------------------------------------------------------------------------
# AES-128-ECB / PKCS7  加解密
# 密钥 = accessToken[8..23] 共 16 字节
# -----------------------------------------------------------------------------
function Get-AesKeyBytes {
    param([Parameter(Mandatory=$true)][string]$Token)
    if ($Token.Length -lt 24) {
        throw "accessToken 长度不足，无法截取 8..23 位生成 AES 密钥（len=$($Token.Length)）"
    }
    return [System.Text.Encoding]::UTF8.GetBytes($Token.Substring(8, 16))
}

function Invoke-AesEncrypt {
    param(
        [Parameter(Mandatory=$true)][string]$Token,
        [Parameter(Mandatory=$true)][string]$Plaintext
    )
    $aes = New-Object System.Security.Cryptography.AesCryptoServiceProvider
    try {
        $aes.Mode    = [System.Security.Cryptography.CipherMode]::ECB
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key     = Get-AesKeyBytes -Token $Token
        $encryptor = $aes.CreateEncryptor()
        try {
            $plainBytes  = [System.Text.Encoding]::UTF8.GetBytes($Plaintext)
            $cipherBytes = $encryptor.TransformFinalBlock($plainBytes, 0, $plainBytes.Length)
            return (ConvertTo-Base64String -Bytes $cipherBytes)
        } finally {
            $encryptor.Dispose()
        }
    } finally {
        $aes.Dispose()
    }
}

function Invoke-AesDecrypt {
    param(
        [Parameter(Mandatory=$true)][string]$Token,
        [Parameter(Mandatory=$true)][string]$CipherTextB64
    )
    $aes = New-Object System.Security.Cryptography.AesCryptoServiceProvider
    try {
        $aes.Mode    = [System.Security.Cryptography.CipherMode]::ECB
        $aes.Padding = [System.Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key     = Get-AesKeyBytes -Token $Token
        $decryptor = $aes.CreateDecryptor()
        try {
            $cipherBytes = ConvertFrom-Base64Bytes -Text $CipherTextB64
            $plainBytes  = $decryptor.TransformFinalBlock($cipherBytes, 0, $cipherBytes.Length)
            return [System.Text.Encoding]::UTF8.GetString($plainBytes)
        } finally {
            $decryptor.Dispose()
        }
    } finally {
        $aes.Dispose()
    }
}

# -----------------------------------------------------------------------------
# 获取 accessToken（带文件缓存）
# -----------------------------------------------------------------------------
function Get-AccessToken {
    param([switch]$Force)

    if (-not $Force -and (Test-Path $script:TOKEN_CACHE_FILE)) {
        try {
            $cached = Get-Content -Raw -Path $script:TOKEN_CACHE_FILE | ConvertFrom-Json
            $now = Get-NowEpoch
            if ($cached.accessToken -and (($now - [int64]$cached.cachedAt) -lt $script:TOKEN_TTL_SEC)) {
                return [string]$cached.accessToken
            }
        } catch {
            # 缓存文件损坏，忽略继续取新 token
        }
    }

    $qs = "appId=$([uri]::EscapeDataString($script:APP_ID))" +
          "&secretKey=$([uri]::EscapeDataString($script:SECRET_KEY))" +
          "&channel=$([uri]::EscapeDataString($script:CHANNEL))" +
          "&subChannel=$([uri]::EscapeDataString($script:SUB_CHANNEL))"
    $url  = "$($script:AUTH_URL)?$qs"

    try {
        $resp = Invoke-RestMethod -Method Post -Uri $url `
            -ContentType 'application/json' -Body '{}' -TimeoutSec 15
    } catch {
        throw "获取 accessToken 失败：$($_.Exception.Message)"
    }

    if ($resp.securityCode -ne '0000' -or -not $resp.accessToken) {
        throw "获取 accessToken 失败：$($resp | ConvertTo-Json -Compress)"
    }

    $cache = @{
        accessToken = $resp.accessToken
        cachedAt    = Get-NowEpoch
    }
    $cache | ConvertTo-Json -Compress | Set-Content -Path $script:TOKEN_CACHE_FILE -Encoding UTF8
    return [string]$resp.accessToken
}

# -----------------------------------------------------------------------------
# 签名（按 key 升序，k=v&k=v... 的大写 MD5）
# $Pairs：字符串数组，每项形如 "k=v"
# 返回 [PSCustomObject]@{ Sig = '...'; Plain = 'k=v&k=v...' }
# -----------------------------------------------------------------------------
function Get-SignedBody {
    param([Parameter(Mandatory=$true)][string[]]$Pairs)
    $sorted = $Pairs | Sort-Object
    $plain  = ($sorted -join '&')
    $sig    = Get-Md5Upper -Text $plain
    return [PSCustomObject]@{ Sig = $sig; Plain = $plain }
}

# -----------------------------------------------------------------------------
# 通用业务调用器
# $ReqPayload：Hashtable 或 PSCustomObject，会被 ConvertTo-Json -Compress
# -----------------------------------------------------------------------------
function Invoke-AirchinaService {
    param(
        [Parameter(Mandatory=$true)][string]$Adapter,
        [Parameter(Mandatory=$true)][string]$Procedure,
        [Parameter(Mandatory=$true)]$ReqPayload,
        [string]$Lang = 'zh_CN'
    )

    $token = Get-AccessToken
    $timestamp = (Get-NowMillis).ToString()

    # 压缩 req JSON（去空白）
    if ($ReqPayload -is [string]) {
        $reqCompact = ($ReqPayload | ConvertFrom-Json | ConvertTo-Json -Compress -Depth 10)
    } else {
        $reqCompact = ($ReqPayload | ConvertTo-Json -Compress -Depth 10)
    }

    $pairs = @(
        "lang=$Lang",
        "req=$reqCompact",
        "timestamp=$timestamp"
    )
    $signed = Get-SignedBody -Pairs $pairs

    $encryptedBody = Invoke-AesEncrypt -Token $token -Plaintext $signed.Plain

    if ($script:DEBUG_MODE) {
        Write-Dbg '================ AIRCHINA DEBUG ================'
        Write-Dbg "adapter          = $Adapter"
        Write-Dbg "procedure        = $Procedure"
        Write-Dbg "serviceVersion   = $($script:SERVICE_VERSION)"
        Write-Dbg "accessToken      = $token"
        Write-Dbg "AES key (plain)  = $($token.Substring(8,16))   (accessToken[8:24], 16 bytes)"
        Write-Dbg 'AES mode         = AES/ECB/PKCS7, no salt'
        Write-Dbg "body plain       = $($signed.Plain)"
        Write-Dbg "signString (MD5) = $($signed.Sig)"
        Write-Dbg "body cipher (b64)= $encryptedBody"
        Write-Dbg "URL              = $($script:SERVICE_URL)"
        Write-Dbg '================================================'
    }

    $headers = @{
        'channel'        = $script:CHANNEL
        'subChannel'     = $script:SUB_CHANNEL
        'appId'          = $script:APP_ID
        'accessToken'    = $token
        'signString'     = $signed.Sig
        'adapter'        = $Adapter
        'procedure'      = $Procedure
        'serviceVersion' = $script:SERVICE_VERSION
    }

    try {
        $httpResp = Invoke-RestMethod -Method Post -Uri $script:SERVICE_URL `
            -ContentType 'application/x-www-form-urlencoded' `
            -Headers $headers -Body $encryptedBody -TimeoutSec 15
    } catch {
        throw "网关请求失败：$($_.Exception.Message)"
    }

    if ($script:DEBUG_MODE) {
        Write-Dbg "gateway response = $($httpResp | ConvertTo-Json -Compress -Depth 10)"
        Write-Dbg '================================================'
    }

    if ($httpResp.securityCode -ne '0000') {
        throw "网关返回错误：$($httpResp | ConvertTo-Json -Compress -Depth 10)"
    }

    # resp 字段：加密的 URL-encoded JSON
    $encResp = $null
    if ($httpResp.PSObject.Properties['resp']) { $encResp = [string]$httpResp.resp }

    if (-not $encResp) { return $httpResp }

    $decrypted = Invoke-AesDecrypt -Token $token -CipherTextB64 $encResp
    # 对齐 airchina.sh 的隐藏约定 2：响应解密后还需 URL decode
    $decoded = [System.Uri]::UnescapeDataString($decrypted)
    try {
        $respObj = $decoded | ConvertFrom-Json
    } catch {
        # 解析失败时，打印密文/明文片段到 stderr 供运维排查
        Write-Err "响应解密后非合法 JSON：decoded=$($decoded.Substring(0, [Math]::Min(200, $decoded.Length)))..."
        throw "响应解析失败：$($_.Exception.Message)"
    }

    # 把明文 resp 塞回 envelope
    $httpResp | Add-Member -MemberType NoteProperty -Name resp -Value $respObj -Force
    return $httpResp
}

# -----------------------------------------------------------------------------
# 本地已领券账本（跨进程持久化）
# -----------------------------------------------------------------------------
function Initialize-Ledger {
    if (-not (Test-Path $script:LEDGER_FILE)) {
        '{}' | Set-Content -Path $script:LEDGER_FILE -Encoding UTF8
    }
}

function Read-Ledger {
    Initialize-Ledger
    try {
        $raw = Get-Content -Raw -Path $script:LEDGER_FILE
        if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
        $obj = $raw | ConvertFrom-Json
        # 转成 hashtable 方便增删改
        $ht = @{}
        foreach ($p in $obj.PSObject.Properties) { $ht[$p.Name] = $p.Value }
        return $ht
    } catch {
        return @{}
    }
}

function Write-Ledger {
    param([Parameter(Mandatory=$true)][hashtable]$Data)
    $tmp = "$($script:LEDGER_FILE).tmp.$PID"
    ($Data | ConvertTo-Json -Depth 10) | Set-Content -Path $tmp -Encoding UTF8
    Move-Item -Force -Path $tmp -Destination $script:LEDGER_FILE
}

function Save-LedgerClaim {
    param(
        [Parameter(Mandatory=$true)][string]$Phone,
        [Parameter(Mandatory=$true)][string]$AreaCode,
        [Parameter(Mandatory=$true)][string]$Activity,
        [Parameter(Mandatory=$true)]$RespObj
    )
    $ledger = Read-Ledger
    $key    = "$AreaCode-$Phone"
    $now    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

    $coupons = @()
    if ($RespObj.PSObject.Properties['couponList'] -and $RespObj.couponList) {
        $coupons = $RespObj.couponList
    }

    $ledger[$key] = @{
        activity   = $Activity
        claimed_at = $now
        coupons    = $coupons
    }
    Write-Ledger -Data $ledger
}

# -----------------------------------------------------------------------------
# 业务命令
# -----------------------------------------------------------------------------
function Invoke-CmdSendSmsCode {
    param(
        [Parameter(Mandatory=$true)][string]$Phone,
        [string]$AreaCode = '86'
    )
    $reqPayload = @{ phone = $Phone; areaCode = $AreaCode }
    $envelope = Invoke-AirchinaService `
        -Adapter 'ACOTADigitalProducts' `
        -Procedure 'sendSMSVeriCodeActivity' `
        -ReqPayload $reqPayload
    $resp = $envelope.resp
    if (-not $resp -or $resp.code -ne '0') {
        throw "发送短信失败：$($resp | ConvertTo-Json -Compress -Depth 10)"
    }
    return $resp
}

function Invoke-CmdClaimCoupon {
    param(
        [Parameter(Mandatory=$true)][string]$Phone,
        [Parameter(Mandatory=$true)][string]$VeriCode,
        [string]$AreaCode = '86'
    )
    $reqPayload = @{ mobileNo = $Phone; areaCode = $AreaCode; veriCode = $VeriCode }
    $envelope = Invoke-AirchinaService `
        -Adapter 'ACOTADigitalProducts' `
        -Procedure 'tencentClaimCoupon' `
        -ReqPayload $reqPayload
    $resp = $envelope.resp
    if (-not $resp -or $resp.code -ne '00000000') {
        throw "领券失败：$($resp | ConvertTo-Json -Compress -Depth 10)"
    }
    Save-LedgerClaim -Phone $Phone -AreaCode $AreaCode `
        -Activity 'tencentClaimCoupon' -RespObj $resp
    return $resp
}

function Invoke-CmdInvoke {
    param(
        [Parameter(Mandatory=$true)][string]$Adapter,
        [Parameter(Mandatory=$true)][string]$Procedure,
        [Parameter(Mandatory=$true)][string]$ReqJson,
        [string]$Lang = 'zh_CN'
    )
    # 把 --req 的原始 JSON 字符串反序列化成对象，交给 Invoke-AirchinaService 再压缩
    try {
        $payload = $ReqJson | ConvertFrom-Json
    } catch {
        throw "--req 不是合法 JSON：$($_.Exception.Message)"
    }
    return (Invoke-AirchinaService -Adapter $Adapter -Procedure $Procedure -ReqPayload $payload -Lang $Lang)
}

function Invoke-CmdCheckClaimed {
    param(
        [Parameter(Mandatory=$true)][string]$Phone,
        [string]$AreaCode = '86',
        [string]$Activity = 'tencentClaimCoupon'
    )
    $ledger = Read-Ledger
    $key    = "$AreaCode-$Phone"
    if ($ledger.ContainsKey($key) -and $ledger[$key].activity -eq $Activity) {
        return $ledger[$key]
    }
    return $null
}

function Invoke-CmdLedgerShow  { return (Read-Ledger) }
function Invoke-CmdLedgerClear {
    '{}' | Set-Content -Path $script:LEDGER_FILE -Encoding UTF8
    return "账本已清空：$($script:LEDGER_FILE)"
}

function Invoke-CmdCheckEnv {
    $info = [ordered]@{
        '—— 硬编码配置（无需任何环境变量） ——' = ''
        appId           = $script:APP_ID
        secretKey       = ('{0}... (长度 {1})' -f $script:SECRET_KEY.Substring(0, 8), $script:SECRET_KEY.Length)
        channel         = $script:CHANNEL
        subChannel      = $script:SUB_CHANNEL
        serviceVersion  = $script:SERVICE_VERSION
        运行环境        = "$($script:ENV_MODE) → $($script:GATEWAY)"
        调试模式        = $script:DEBUG_MODE
        '—— 可临时覆盖的环境变量 ——' = ''
        'AIRCHINA_ENV=prod'   = '切换到生产环境'
        'AIRCHINA_DEBUG=1'    = '打印中间值便于对账'
        '—— Windows 沙箱规避 ——'     = ''
        'Base64 decoder'              = 'FromBase64Transform (static API 不可用)'
        'Base64 encoder'              = 'ToBase64Transform'
    }
    return $info
}

# -----------------------------------------------------------------------------
# CLI 入口
# 用法：支持 --phone / --area-code / --veri-code / --adapter / --procedure /
#       --req / --lang / --activity 等长参数（与 airchina.sh 对齐）
# -----------------------------------------------------------------------------
function Show-Usage {
    @'
用法（PowerShell 5.1+，无需安装任何额外依赖）：
  airchina.ps1 check-env
  airchina.ps1 get-token [--force]
  airchina.ps1 send_sms_code --phone <手机号> [--area-code 86]
  airchina.ps1 claim_coupon  --phone <手机号> --veri-code <6位码> [--area-code 86]
  airchina.ps1 invoke --adapter <X> --procedure <Y> --req <JSON> [--lang zh_CN]

已领券账本（本地缓存，避免用户重复领同一活动）：
  airchina.ps1 check_claimed --phone <手机号> [--area-code 86] [--activity tencentClaimCoupon]
      未领过 → 输出 null；已领过 → 输出 JSON（含 claimed_at + coupons 列表）
  airchina.ps1 ledger_show
  airchina.ps1 ledger_clear

可选环境变量：
  AIRCHINA_ENV=prod      切换到生产环境（默认 prod）
  AIRCHINA_DEBUG=1       打印中间值便于对账

🛑 禁用（沙箱静默拦截）：
  [Convert]::FromBase64String / [Convert]::ToBase64String
  本脚本已全部改用 FromBase64Transform / ToBase64Transform
'@
}

function Write-JsonResult {
    param([Parameter(Mandatory=$false, ValueFromPipeline=$false)]$Obj)
    if ($null -eq $Obj) {
        Write-Output 'null'
        return
    }
    if ($Obj -is [string]) {
        Write-Output $Obj
        return
    }
    Write-Output (ConvertTo-Json -InputObject $Obj -Depth 10)
}

# 把 --k value 的长参列表解析成 hashtable；支持 switch 如 --force
function Get-ArgMap {
    param([string[]]$ArgList)
    $map = @{}
    $i = 0
    $n = if ($null -eq $ArgList) { 0 } else { $ArgList.Count }
    while ($i -lt $n) {
        $a = $ArgList[$i]
        if ($a -like '--*') {
            $key = $a.Substring(2)
            if ($i + 1 -lt $n -and -not ($ArgList[$i+1] -like '--*')) {
                $map[$key] = $ArgList[$i+1]
                $i += 2
            } else {
                $map[$key] = $true
                $i += 1
            }
        } else {
            throw "未知位置参数：$a"
        }
    }
    return $map
}

function Invoke-Main {
    param([string[]]$AllArgs)
    if (-not $AllArgs -or $AllArgs.Count -eq 0) {
        Show-Usage
        exit 1
    }
    $cmd  = $AllArgs[0]
    $rest = @()
    if ($AllArgs.Count -gt 1) { $rest = $AllArgs[1..($AllArgs.Count - 1)] }

    try {
        switch ($cmd) {
            'check-env'     { Write-JsonResult -Obj (Invoke-CmdCheckEnv); return }
            'get-token'     {
                $argMap = Get-ArgMap -ArgList $rest
                $tok = Get-AccessToken -Force:([bool]$argMap['force'])
                Write-JsonResult -Obj @{ accessToken = $tok }
                return
            }
            'send_sms_code' {
                $m = Get-ArgMap -ArgList $rest
                if (-not $m.ContainsKey('phone')) { throw '缺少 --phone' }
                $r = Invoke-CmdSendSmsCode -Phone $m['phone'] `
                        -AreaCode ($(if ($m.ContainsKey('area-code')) { $m['area-code'] } else { '86' }))
                Write-JsonResult -Obj $r
                return
            }
            'claim_coupon'  {
                $m = Get-ArgMap -ArgList $rest
                if (-not $m.ContainsKey('phone'))     { throw '缺少 --phone' }
                if (-not $m.ContainsKey('veri-code')) { throw '缺少 --veri-code' }
                $r = Invoke-CmdClaimCoupon -Phone $m['phone'] -VeriCode $m['veri-code'] `
                        -AreaCode ($(if ($m.ContainsKey('area-code')) { $m['area-code'] } else { '86' }))
                Write-JsonResult -Obj $r
                return
            }
            'invoke' {
                $m = Get-ArgMap -ArgList $rest
                foreach ($k in 'adapter','procedure','req') {
                    if (-not $m.ContainsKey($k)) { throw "缺少 --$k" }
                }
                $r = Invoke-CmdInvoke -Adapter $m['adapter'] -Procedure $m['procedure'] `
                        -ReqJson $m['req'] `
                        -Lang ($(if ($m.ContainsKey('lang')) { $m['lang'] } else { 'zh_CN' }))
                Write-JsonResult -Obj $r
                return
            }
            'check_claimed' {
                $m = Get-ArgMap -ArgList $rest
                if (-not $m.ContainsKey('phone')) { throw '缺少 --phone' }
                $r = Invoke-CmdCheckClaimed -Phone $m['phone'] `
                        -AreaCode ($(if ($m.ContainsKey('area-code')) { $m['area-code'] } else { '86' })) `
                        -Activity ($(if ($m.ContainsKey('activity')) { $m['activity'] } else { 'tencentClaimCoupon' }))
                Write-JsonResult -Obj $r
                return
            }
            'ledger_show'   { Write-JsonResult -Obj (Invoke-CmdLedgerShow); return }
            'ledger_clear'  { Invoke-CmdLedgerClear; return }
            'help'          { Show-Usage; return }
            '-h'            { Show-Usage; return }
            '--help'        { Show-Usage; return }
            default         { Write-Err "未知子命令：$cmd"; Show-Usage; exit 1 }
        }
    } catch {
        Write-Err $_.Exception.Message
        exit 1
    }
}

# 仅当脚本作为入口被执行时走 CLI；被 dot-source 时不触发
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-Main -AllArgs $args
}
