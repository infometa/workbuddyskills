# pyright: reportMissingImports=false
"""
腾讯云 COS 客户端（生产版）
============================
封装图片文件上传到 COS 桶的能力。
COS 是可选功能：未配置凭据时返回 error dict，不抛异常。
"""

import os
import time
import hashlib
from urllib.parse import quote

from config import get_cos_config, is_cos_available
from utils import log_info, log_warn

# 尝试导入 COS SDK（可选依赖）
try:
    from qcloud_cos import CosConfig, CosS3Client
    HAS_COS_SDK = True
except ImportError:
    HAS_COS_SDK = False


def _build_image_object_key(filename: str, path_prefix: str) -> str:
    """
    生成 COS 图片对象路径
    格式: {path_prefix}/{YYYY-MM-DD}/images/{filename_hash}_{original_ext}
    """
    date_str = time.strftime("%Y-%m-%d")
    timestamp = str(int(time.time() * 1000))
    suffix = hashlib.md5((filename + timestamp).encode()).hexdigest()[:8]

    # 提取文件扩展名
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".jpg"
    ext = ext.lower()

    # 安全化文件名
    safe_name = filename[:30].strip()
    for ch in " /\\?#&=<>\"'":
        safe_name = safe_name.replace(ch, "-")
    safe_name = safe_name.strip("-") or "image"

    return f"{path_prefix}/{date_str}/images/{safe_name}_{suffix}{ext}"


def _get_cos_client():
    """
    获取 COS 客户端实例和配置。
    Returns:
        (client, cos_cfg) 或 (None, error_dict)
    """
    if not HAS_COS_SDK:
        return None, {
            "status": "error",
            "error_code": "MissingDependency",
            "error_message": "cos-python-sdk-v5 未安装。请执行: pip install cos-python-sdk-v5",
        }

    if not is_cos_available():
        return None, {
            "status": "error",
            "error_code": "NotConfigured",
            "error_message": "COS 凭据未配置，跳过上传。",
        }

    try:
        cos_cfg = get_cos_config()
    except EnvironmentError as e:
        return None, {
            "status": "error",
            "error_code": "ConfigError",
            "error_message": str(e),
        }

    config = CosConfig(
        Region=cos_cfg["region"],
        SecretId=cos_cfg["secret_id"],
        SecretKey=cos_cfg["secret_key"],
        Timeout=120,
    )
    client = CosS3Client(config)
    return client, cos_cfg


def upload_image(image_bytes: bytes, filename: str, content_type: str = "") -> dict:
    """
    将图片二进制数据上传到腾讯云 COS

    Args:
        image_bytes: 图片二进制数据
        filename: 文件名（用于生成 object key 和推断 Content-Type）
        content_type: MIME 类型，为空则自动推断

    Returns:
        成功: {"status": "success", "image_url": "https://...", "object_key": "..."}
        失败: {"status": "error", "error_code": "...", "error_message": "..."}
    """
    client, cos_cfg = _get_cos_client()
    if client is None:
        return cos_cfg  # cos_cfg 此时是 error dict

    # 图片大小限制：10MB
    if len(image_bytes) > 10 * 1024 * 1024:
        return {
            "status": "error",
            "error_code": "FileTooLarge",
            "error_message": f"图片大小 {len(image_bytes) / 1024 / 1024:.1f}MB 超过 10MB 限制",
        }

    # 自动推断 Content-Type
    if not content_type:
        import mimetypes
        guessed = mimetypes.guess_type(filename)[0]
        content_type = guessed or "image/jpeg"

    try:
        object_key = _build_image_object_key(filename, cos_cfg["path_prefix"])
        bucket = cos_cfg["bucket"]

        acl_ok = False
        try:
            client.put_object(
                Bucket=bucket,
                Body=image_bytes,
                Key=object_key,
                ContentType=content_type,
                ACL="public-read",
            )
            acl_ok = True
        except Exception as acl_err:
            log_warn(f"[COS] put_object 带 ACL 失败（{acl_err}），退化为不带 ACL 上传")
            client.put_object(
                Bucket=bucket,
                Body=image_bytes,
                Key=object_key,
                ContentType=content_type,
            )

        if not acl_ok:
            try:
                client.put_object_acl(
                    Bucket=bucket,
                    Key=object_key,
                    ACL="public-read",
                )
            except Exception as acl_err2:
                log_warn(f"[COS] put_object_acl 设置失败: {acl_err2}")

        encoded_key = quote(object_key, safe="/")
        image_url = f"https://{bucket}.cos.{cos_cfg['region']}.myqcloud.com/{encoded_key}"

        return {
            "status": "success",
            "image_url": image_url,
            "object_key": object_key,
        }

    except Exception as e:
        return {
            "status": "error",
            "error_code": "UploadFailed",
            "error_message": f"COS 图片上传失败: {str(e)}",
        }
