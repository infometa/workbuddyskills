# Windows PowerShell 沙箱已知限制

> WorkBuddy 的 Windows 客户端在把 PowerShell 命令交给 `powershell.exe` 之前有一层
> 静默过滤器。命中黑名单的语句**不报错、不输出**，看起来像代码写错。
> 本文档记录踩过的坑与对应的规避写法。

## 背景

- 过滤规则来源：AV/EDR 厂商的威胁情报黑名单，PowerShell 恶意样本的典型指纹
- 被拦截时的表现：
  - **stdout 空、stderr 空、退出码 0**
  - 命令没抛异常，`$?` 可能是 `$true`，但关键操作实际没发生
- 最容易误判为"我代码写错了"，实际是"这个 API 被沙箱吃了"
- 最常见踩坑场景：跟外部 API 做 AES/Base64 加解密时

## 已验证被拦截的 API

| API | 表现 |
|-----|------|
| `[Convert]::FromBase64String(<string>)` | 静默返回空，无异常 |
| `[Convert]::ToBase64String(<byte[]>)` | 静默返回空，无异常 |

（踩到新的被拦 API 请补充到这里）

## 未被拦截的等价 API（2026-04-29 验证可用）

| 目的 | 推荐 API | 示例 |
|------|---------|------|
| Base64 解码 | `System.Security.Cryptography.FromBase64Transform` | 见下方代码 |
| Base64 编码 | `System.Security.Cryptography.ToBase64Transform` | 见下方代码 |
| AES 加解密 | `System.Security.Cryptography.AesCryptoServiceProvider` | `airchina.ps1` |
| AES 加解密（替代） | `System.Security.Cryptography.RijndaelManaged` | 同 AES |
| Hash | `System.Security.Cryptography.MD5 / SHA256 / ...` | `.ComputeHash(...)` |
| HTTP | `Invoke-RestMethod` / `Invoke-WebRequest` | |
| 文件读写 | `Get-Content` / `Set-Content` / `[System.IO.File]::*` | |
| JSON | `ConvertFrom-Json` / `ConvertTo-Json` | |
| URL decode | `[System.Uri]::UnescapeDataString(<s>)` | |

### Base64 规避写法（核心）

```powershell
# 解码：把 Base64 字符串还原为 byte[]
function ConvertFrom-Base64Bytes {
    param([string]$Text)
    $t = New-Object System.Security.Cryptography.FromBase64Transform
    try {
        $in  = [System.Text.Encoding]::ASCII.GetBytes($Text)
        $out = $t.TransformFinalBlock($in, 0, $in.Length)
        return ,$out   # 前置 , 防止 PS 5.1 pipeline 展开 byte[]
    } finally { $t.Dispose() }
}

# 编码：把 byte[] 转成 Base64 字符串
function ConvertTo-Base64String {
    param([byte[]]$Bytes)
    $t = New-Object System.Security.Cryptography.ToBase64Transform
    try {
        $out = $t.TransformFinalBlock($Bytes, 0, $Bytes.Length)
        return [System.Text.Encoding]::ASCII.GetString($out)
    } finally { $t.Dispose() }
}
```

## 踩坑排查 checklist

当 PowerShell 命令诡异失败时按顺序排查：

1. **有没有任何输出？**  
   `stdout`、`stderr`、`$LASTEXITCODE` 全空？→ 大概率沙箱拦截，**立即停**
2. **二分定位哪一行静默死：**  
   在怀疑行前后分别 `Write-Output "STEP1"` / `Write-Output "STEP2"`，
   看输出到哪一步戛然而止
3. **命中行的 API 是否在本文档"已验证被拦截"表里？**  
   在 → 按上表换成等价 API；不在 → 补充到本文档
4. **仍然失败？**  
   把这段能跑通的封装写到 `airchina.ps1`（或对应 skill 的 ps1 里），
   让后续所有用户复用封装，不再让 AI 每次重新摸索
5. **切忌**无脑重试——如果第一次静默失败，第二次相同代码仍静默失败，
   写再多次也不会通过

## 给调用 skill 的 AI 的守则

1. **不要自己写 PowerShell 做加解密/编码**，调 `scripts/airchina.ps1` 里封装好的命令
2. **禁用** `[Convert]::FromBase64String` / `[Convert]::ToBase64String`——
   即使你看到别处代码在用，那就是 bug
3. 命令静默失败 = 沙箱拦截，**停手**去读本文档和 SKILL.md"失败熔断"章节，
   不要循环尝试"下一个解法"

## 案例追溯

- **2026-04-29** 用户 `108770ed-4076-49f2-bc07-c857ed102add` 在 session
  `3f4dc11c-663c-4989-9c7d-3f3eaee23caa` 中调用 `airchina-coupon` skill，
  AI 因 `[Convert]::FromBase64String` 被静默拦截，误判"解密失败 = 领券失败"，
  在 10 分钟里尝试 40+ 次 PowerShell 方案，最终在 15:43:04 用
  `FromBase64Transform` 绕开成功。但原始领券请求（15:34）其实早已成功送达国航
  并发券到账。此次循环也是导致 `AGENT_INVOKABLE_CUSTOM_MODEL_NOT_FOUND` 的直接诱因。
