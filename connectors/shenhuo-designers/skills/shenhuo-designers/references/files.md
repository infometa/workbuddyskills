# 原始文件传输

远程服务器无法读取用户电脑路径。调用 MCP `create_upload(filename,mime_type,role,idempotency_key,label)` 获取五分钟有效的 PUT 地址；单文件最多 20 MiB，类型由服务端校验。本人照片用 `subject_photo`，一般素材用 `reference`。保留用户选择的文件顺序。

宿主拥有文件／命令能力时上传原始字节，不需要 Python。macOS 示例（用真实路径、票据替换占位符，严格作 Shell 参数引用，不拼接用户 Brief）：

```sh
curl --fail --silent --show-error --request PUT --upload-file '/absolute/input.png' 'UPLOAD_URL'
shasum -a 256 '/absolute/input.png'
```

读取上传回执 `receipt.asset_id` 和 `receipt.sha256`，核对哈希；响应丢失先调用 `get_upload(transfer_id)`，完成则复用资产，不重复上传。相同票据只能重试相同原始字节；未完成且票据过期，另申请上传票据，不重新创建设计任务。

对已结算作品调用 `get_result`，保留返回的真实文件名及扩展名：

```sh
mkdir -p '/absolute/output-directory'
curl --fail --silent --show-error --output '/absolute/output-directory/returned-filename.jpg' 'DOWNLOAD_URL'
shasum -a 256 '/absolute/output-directory/returned-filename.jpg'
```

将输出路径放在已创建的目标目录中，并确认 HTTP 请求成功、文件非空且内容确为图片后，用宿主产物展示能力呈现本机文件。十分钟下载凭证到期后重新调用 `get_result` 使用新的领取幂等键，不调用生图工具。票据 URL 是短期凭证，不写入公开日志、插件包或审核报告。

## Windows 原生文件传输

Windows 使用 PowerShell，不要求额外安装 Python、Node 或 curl。替换为用户实际选择的路径与服务返回的短期 URL；路径和 URL 作为参数处理，不能拼接用户 Brief 作为命令：

```powershell
$shenhuoSource = 'C:\Users\User\Pictures\input.png'
Invoke-RestMethod -UseBasicParsing -Method Put -Uri 'UPLOAD_URL' -InFile $shenhuoSource -ContentType 'application/octet-stream'
(Get-FileHash -Algorithm SHA256 -LiteralPath $shenhuoSource).Hash
```

下载前创建真实目标目录，文件名与扩展名使用服务端回执：

```powershell
$shenhuoOutputDir = 'C:\Users\User\Pictures\Shenhuo'
New-Item -ItemType Directory -Force -Path $shenhuoOutputDir | Out-Null
$shenhuoOutput = Join-Path $shenhuoOutputDir 'returned-filename.jpg'
Invoke-WebRequest -UseBasicParsing -Uri 'DOWNLOAD_URL' -OutFile $shenhuoOutput
(Get-FileHash -Algorithm SHA256 -LiteralPath $shenhuoOutput).Hash
```

无本地文件能力时可展示远程预览／下载链接及神火原项目入口，明确尚未执行本机下载；无法上传的输入不能宣称已经作为参考图参与设计。Windows 尚未实机验收，不从 macOS 成功推断 Windows 已通过。
