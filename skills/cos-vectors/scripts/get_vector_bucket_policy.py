#!/usr/bin/env python3
"""
获取腾讯云 COS 向量桶访问策略

用法:
    python3 get_vector_bucket_policy.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID>
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("获取腾讯云 COS 向量桶访问策略")
    args = parser.parse_args()
    client = create_client(args)

    resp, data = client.get_vector_bucket_policy(Bucket=args.bucket)
    success_output({
        "action": "get_vector_bucket_policy",
        "bucket": args.bucket,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
