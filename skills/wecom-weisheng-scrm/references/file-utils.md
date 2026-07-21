# 文件上传与下载

`scripts/file_utils.py` 提供本地图片上传与远程文件下载能力，解决本地图片转为公网 URL 的问题。

## 使用场景

创建海报素材、个人活码等操作需要图片 URL。当用户提供本地文件路径时，需自动上传转换为公网地址。上传返回的 `file_id` 可用于后续创建素材等写操作。

## 函数参考

### ensure_public_image_url（推荐入口）

自动判断图片来源并处理，仅需要 URL 时使用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | `str` | 是 | 远程 URL 或本地文件路径 |
| `client` | `SCRMClient` | 否 | 本地图片上传时必填 |

- 远程 URL → 直接返回原 URL
- 本地路径 → 上传后返回公网地址

```python
url = ensure_public_image_url("https://example.com/img.png", client=client)
url = ensure_public_image_url("/Users/me/photo.png", client=client)
```

### upload_image

需要同时获取 `url` 和 `file_id` 时使用（如创建素材场景）。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | `Path` | 是 | 本地图片文件路径 |
| `client` | `SCRMClient` | 是 | SCRM 客户端实例 |

返回 `dict`：`{"url": "https://...", "file_id": 12345}`

### download_file

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | `str` | 是 | 远程文件地址 |
| `target_dir` | `Path` | 否 | 下载目标目录 |
| `filename` | `str` | 否 | 保存文件名，默认自动生成 |

返回 `Path`（下载后的本地文件路径）。

### is_remote_url

判断字符串是否为公网 URL，返回 `bool`。

## 异常类型

| 异常类 | 触发场景 |
|--------|---------|
| `DownloadError` | 下载地址非法、网络请求失败 |
| `UploadError` | 本地文件不存在、上传失败、响应中无法提取 URL 或 file_id |

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `SCRM_SKIP_SSL_VERIFY` | 设为 `1`/`true`/`yes` 跳过 SSL 验证，适用于内网环境 |
