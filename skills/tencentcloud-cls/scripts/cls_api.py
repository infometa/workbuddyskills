#!/usr/bin/env python3
"""
腾讯云 CLS API 通用调用脚本
依赖: pip install tencentcloud-sdk-python-cls
认证: 环境变量 TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY
"""

import json
import os
import sys

from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.common_client import CommonClient


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "用法: python3 cls_api.py <Region> <Action> [JSON参数]",
            "example": 'python3 cls_api.py ap-guangzhou SearchLog \'{"TopicId":"xxx","From":1700000000000,"To":1700003600000,"QueryString":"level:ERROR","QuerySyntax":1,"Limit":10}\''
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    region = sys.argv[1]
    action = sys.argv[2]
    params_str = sys.argv[3] if len(sys.argv) > 3 else "{}"

    # 解析 JSON 参数
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"JSON 参数解析失败: {e}"}, ensure_ascii=False))
        sys.exit(1)

    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")

    if not secret_id or not secret_key:
        print(json.dumps({"error": "缺少环境变量 TENCENTCLOUD_SECRET_ID 或 TENCENTCLOUD_SECRET_KEY"}, ensure_ascii=False))
        sys.exit(1)

    try:
        cred = credential.Credential(secret_id, secret_key)

        http_profile = HttpProfile()
        http_profile.endpoint = "cls.tencentcloudapi.com"
        http_profile.reqMethod = "POST"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        # 使用 CommonClient 通用调用，支持任意 Action + dict 参数
        client = CommonClient("cls", "2020-10-16", cred, region, profile=client_profile)
        resp = client.call_json(action, params)

        # resp 是 dict，格式化输出
        if isinstance(resp, str):
            resp = json.loads(resp)
        print(json.dumps(resp, ensure_ascii=False, indent=2))

    except TencentCloudSDKException as e:
        print(json.dumps({
            "error": str(e),
            "code": e.code,
            "requestId": e.requestId
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
