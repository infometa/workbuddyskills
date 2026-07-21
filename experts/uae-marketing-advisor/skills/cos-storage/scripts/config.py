"""
腾讯云 COS 存储桶配置
⚠️ 安全提醒：请勿在此文件中填写真实密钥。
通过环境变量配置：COS_SECRET_ID / COS_SECRET_KEY
如已在环境中设置了上述变量，cos_client.py 将自动读取。
"""
import os

COS_CONFIG = {
    "secret_id": os.environ.get("COS_SECRET_ID", ""),
    "secret_key": os.environ.get("COS_SECRET_KEY", ""),
    "region": os.environ.get("COS_REGION", "ap-shanghai"),
    "bucket": os.environ.get("COS_BUCKET", "uae-marketing-1448789884"),
    "endpoint": os.environ.get("COS_ENDPOINT", "cos.ap-shanghai.myqcloud.com"),
}
