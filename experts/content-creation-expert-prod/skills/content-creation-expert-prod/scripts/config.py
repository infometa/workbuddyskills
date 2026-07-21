"""
配置加载器（生产版精简）
========================
只保留 COS 可选配置，去掉 VOD/MCP/TEXT API 配置。
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env():
    """
    加载 .env 文件中的环境变量。
    查找顺序：
    1. scripts/ 同级的 .env
    2. skill 根目录的 .env
    """
    scripts_dir = Path(__file__).resolve().parent
    skill_root = scripts_dir.parent

    # 优先 skill 根目录
    env_file = skill_root / ".env"
    if env_file.exists():
        load_dotenv(str(env_file), override=True)
        return

    # 其次 scripts 同级
    env_file = scripts_dir / ".env"
    if env_file.exists():
        load_dotenv(str(env_file), override=True)


def is_cos_available() -> bool:
    """
    检查 COS 是否可用（凭据 + 桶名 + 地域 全部配置齐全）。
    
    Returns:
        True: COS 配置完整，可以上传
        False: COS 配置不完整，只能本地保存
    """
    secret_id = os.environ.get("COS_SECRET_ID") or os.environ.get("TENCENT_SECRET_ID")
    secret_key = os.environ.get("COS_SECRET_KEY") or os.environ.get("TENCENT_SECRET_KEY")
    bucket = os.environ.get("COS_BUCKET")
    region = os.environ.get("COS_REGION")
    return bool(secret_id and secret_key and bucket and region)


def get_cos_config() -> dict:
    """
    获取 COS 配置。调用前应先用 is_cos_available() 检查。

    Returns:
        dict: {secret_id, secret_key, bucket, region, path_prefix}

    Raises:
        EnvironmentError: COS 配置不完整
    """
    secret_id = os.environ.get("COS_SECRET_ID") or os.environ.get("TENCENT_SECRET_ID")
    secret_key = os.environ.get("COS_SECRET_KEY") or os.environ.get("TENCENT_SECRET_KEY")
    bucket = os.environ.get("COS_BUCKET")
    region = os.environ.get("COS_REGION")

    if not secret_id or not secret_key:
        raise EnvironmentError("COS 凭据未配置（COS_SECRET_ID / COS_SECRET_KEY）")
    if not bucket:
        raise EnvironmentError("COS 桶名未配置（COS_BUCKET）")
    if not region:
        raise EnvironmentError("COS 地域未配置（COS_REGION）")

    path_prefix = os.environ.get("COS_PATH_PREFIX", "")

    return {
        "secret_id": secret_id,
        "secret_key": secret_key,
        "bucket": bucket,
        "region": region,
        "path_prefix": path_prefix.strip("/") if path_prefix else "",
    }
