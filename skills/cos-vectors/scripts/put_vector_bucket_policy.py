#!/usr/bin/env python3
"""
设置腾讯云 COS 向量桶访问策略

用法:
    python3 put_vector_bucket_policy.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        --policy '{"Statement": [...]}'
"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, fail, run


def main():
    parser = base_parser("设置腾讯云 COS 向量桶访问策略")
    parser.add_argument("--policy", required=True, help="策略 JSON 字符串")
    args = parser.parse_args()
    client = create_client(args)

    try:
        policy = json.loads(args.policy)
    except json.JSONDecodeError as e:
        fail(f"策略 JSON 格式错误: {e}")

    resp, data = client.put_vector_bucket_policy(Bucket=args.bucket, Policy=policy)
    success_output({
        "action": "put_vector_bucket_policy",
        "bucket": args.bucket,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
