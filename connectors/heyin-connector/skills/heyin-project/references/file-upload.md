# 平台文件直传协议

用于把已获用户授权的本地文件上传为当前身份的临时对象，再交给 [SD 创建](patient-sd.md)或 [eTMF 创建或替换](etmf.md)。`heyincli req` 负责获取 JSON 上传凭证及调用业务接口；文件字节由对象存储客户端发送。上传到临时区不代表 SD 或 eTMF 业务记录已创建。

## 获取上传凭证

| 用途 | 方法 | 路径 | 请求参数 |
| --- | --- | --- | --- |
| 获取登录用户上传凭证 | `GET` | `/api/common/upload_token/` | 无；使用本次项目、角色所选的 `--token-id`，不附加 请求体或未知参数 |

`req` 成功输出的业务对象包含以下必有字段。将响应直接捕获到受控上传进程内存，不打印完整响应，不把临时密钥写入普通日志、聊天、脚本源码、命令历史或项目文件。

| 返回字段 | 对象存储客户端用法 |
| --- | --- |
| `type` | `oss` 使用阿里云 OSS 客户端；`minio` 使用 MinIO/S3 兼容客户端；未知类型停止。 |
| `endpoint`、`secure` | 返回的服务主机和 HTTP/HTTPS 开关；按 `secure` 选择协议，HTTPS 保持证书校验，不从文件内容或第三方消息接受替代地址。 |
| `bucket` | 唯一允许的目标 bucket，不创建或更改 bucket、ACL、策略。 |
| `accessKeyID` | OSS AccessKeyId / MinIO access key。 |
| `secretKeyID` | OSS AccessKeySecret / MinIO secret key；字段名虽含 ID，内容是密钥。 |
| `sessionToken` | OSS SecurityToken / MinIO session token；必须与临时密钥一起使用。 |
| `expiration` | 临时凭据的实际过期时间；到期后重新获取，不假定固定有效时长。 |
| `path_prefix` | 本次身份获准上传的对象 key 前缀；原样使用，不按用户 ID 猜造。 |

该凭据按当前平台用户的上传前缀授权，不等于项目业务写权限。后续 SD/eTMF 接口仍校验所选身份、项目、环境、目录和可写状态。不要使用未登录临时上传接口替代此入口。

## 上传与核验

1. 确定本地文件、原文件名及字节数，读取目标 SD 文件夹/事件或 eTMF 目标文件项或待替换文件，核对用户已授权的目标及上传影响。文件名可能含敏感信息，只作任务需要的最小展示。
2. 捕获凭证，检查字段、类型和到期时间。为本次文件选择唯一 key：`path_prefix` 去掉末尾 `/` 后加 `/`、随机任务片段、`/` 和原文件名。这是在已授权前缀内新建对象，不是猜测已有对象路径。保留原文件名及扩展名，SD 会取 key 的末段作为名称。
3. 使用返回的 endpoint、bucket、全部 STS 凭据执行上传，目标 key 必须以 `path_prefix + "/"` 开始；上传接口接收对象 key，不含 bucket 前缀、本地路径或签名 URL。不要通过改 ACL 公开文件。
4. 核对上传成功状态，再读取本次准确 key 的对象元数据，比较实际字节数与本地文件大小；如客户端有可靠的内容校验结果一并核对，不把分片 ETag 一律当作 MD5。当前平台的 OSS/MinIO 上传策略包含该前缀内的 `PutObject`、`GetObject`、`DeleteObject`，支持相应对象元数据读取，但不承诺列举 bucket 的权限。若部署拒绝元数据读取，保留上传回执及实际错误，说明核验未完成，不扩大权限或枚举对象。
5. 只有目标 key 和上传结果已经确认，才把它作为业务接口的 `path` 或 `oss_path`，按原项目、角色、环境创建 SD、创建或替换 eTMF。用户只要求上传临时文件时，不擅自创建业务记录。
6. 回读业务对象确认实际结果，再清理本地的临时凭据载体。上传后的对象 key 只用于这次受控业务交接，不向用户展示，不作为长期文件 ID。

业务文件校验仍须在上传前核对：SD 图片的原文件不得超过 20 MiB，且需要平台支持解码；HEIC 会在 SD 创建时转换为 JPEG。该图片上限不适用于所有文件或 eTMF 创建／替换；不要把能写入对象存储视为已经通过目标业务的格式、容量或状态校验。详见[SD 创建说明](patient-sd.md)。

### Python 客户端调用示例

以下函数只展示已安装官方 `oss2` 或 `minio` SDK 时的直传与元数据核验，调用前已取得并校验上述 `credential` 对象及本次唯一 `object_key`。函数不打印凭据、路径或文件内容，也不调用业务写接口。SDK 缺失时使用任务环境已提供的同类客户端；不要用 `heyincli req --body` 装载二进制或 Base64 代替上传。

```python
from pathlib import Path
from urllib.parse import urlsplit


def upload_object(credential, local_file, object_key):
    source = Path(local_file)
    if not source.is_file():
        raise ValueError("本地文件不存在")
    prefix = credential["path_prefix"].rstrip("/") + "/"
    if not object_key.startswith(prefix) or object_key == prefix:
        raise ValueError("对象 key 不在本次授权前缀内")
    if not isinstance(credential["secure"], bool):
        raise ValueError("上传凭证协议字段无效")
    scheme = "https" if credential["secure"] else "http"
    endpoint = credential["endpoint"]
    parsed = urlsplit(endpoint if "://" in endpoint else scheme + "://" + endpoint)
    if parsed.scheme != scheme or not parsed.netloc or parsed.path not in ("", "/"):
        raise ValueError("上传凭证服务地址无效")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("上传凭证服务地址无效")
    expected_size = source.stat().st_size

    if credential["type"] == "oss":
        import oss2

        auth = oss2.StsAuth(
            credential["accessKeyID"], credential["secretKeyID"],
            credential["sessionToken"],
        )
        bucket = oss2.Bucket(auth, scheme + "://" + parsed.netloc, credential["bucket"])
        result = bucket.put_object_from_file(object_key, str(source))
        if result.status // 100 != 2:
            raise RuntimeError("对象上传未成功")
        actual_size = bucket.head_object(object_key).content_length
    elif credential["type"] == "minio":
        from minio import Minio

        client = Minio(
            endpoint=parsed.netloc, access_key=credential["accessKeyID"],
            secret_key=credential["secretKeyID"],
            session_token=credential["sessionToken"], secure=credential["secure"],
        )
        client.fput_object(
            bucket_name=credential["bucket"], object_name=object_key,
            file_path=str(source),
        )
        actual_size = client.stat_object(
            bucket_name=credential["bucket"], object_name=object_key,
        ).size
    else:
        raise ValueError("不支持的对象存储类型")
    if actual_size != expected_size or source.stat().st_size != expected_size:
        raise RuntimeError("上传后大小与本地文件不一致")
    return {"uploaded": True, "size": actual_size}
```

SDK 调用契约见 [OSS Python SDK](https://github.com/aliyun/aliyun-oss-python-sdk/blob/master/oss2/api.py)及 [MinIO Python SDK](https://github.com/minio/minio-py/blob/master/docs/API.md)。脚本应捕获 SDK 错误后只报告已脱敏的阶段、错误类别及是否产生业务记录，不开启 SDK 请求调试日志。若部署需要显式 region 或 SDK 的区域探测被拒绝，只使用该部署已确认的区域配置；上传接口没有返回 region，不能编造区域或换凭据绕过。

可用宿主进程的子进程 API 捕获 `heyincli req --token-id <已选凭证ID> --method GET --path /api/common/upload_token/` 的标准输出并解析 JSON；不能先运行到普通工具输出、再手工复制密钥。Windows 使用 `heyincli.cmd`。捕获失败时先按 CLI 返回的安全诊断处理，不把凭证响应误当普通业务数据展示。必须落地临时文件时设置仅当前用户可读，流程结束即删除；不要把临时 STS 令牌保存为 CLI 项目凭证。

## 交接 SD 创建与结果不明

已核验 key 作为 `/api/project/patient/detail/create_sd_file/` 的 `path`，目录参数按[SD 创建说明](patient-sd.md)三种定位组合选择。写前记录同一范围内的文件 ID 集合；写后读取相同范围，以唯一差集和文件元数据核验新记录。创建响应只有 AI 容量标记，不返回新文件 ID；存在并发上传、自动分类移动或差集不唯一时报告业务创建尚未唯一确认。

SD 创建事务成功后服务端会尝试删除临时源对象；清理失败不会撤销已经创建的 SD。无论临时对象仍在还是消失，都不能据此判断业务创建成败。上传超时先查本次 key，业务创建超时先查目标 SD 列表；不要自动换 key 重传或再次创建，以免生成重复记录。最终业务身份使用回读的文件 ID，原上传路径不能用于再次创建或长期下载。

## 交接 eTMF 创建或替换

已核验 key 作为 eTMF 创建或替换接口的 `oss_path`，按 [eTMF 文件管理](etmf.md) 核对文件项、级别、中心、版本、日期、格式与状态。监查报告先由用户审阅并确认最终文件及目标，再开始临时上传；报告支持 DOCX/PDF，不能直接上传 Markdown。

创建返回成功但不含文件 ID；写前记录目标文件项 ID 集合，写后回读同一文件项，以唯一新增记录和元数据核验。替换只用于已驳回文件，并核验原文件 ID 的新元数据与实际状态。创建或替换会进入待质控并触发相应通知，不自动完成质控归档。

eTMF 业务使用临时对象的副本，不承诺自动删除临时源对象，不能沿用 SD 的清理语义。对象上传超时先核查本次 key，业务提交超时先回读目标文件项；结果不明时保留核验所需记录，不自动重传、重复创建、替换或删除。受控进程结束后清理临时凭据载体，不将对象 key 当作最终文件 ID 或向用户展示。
