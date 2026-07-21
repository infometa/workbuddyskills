#!/usr/bin/env python3
"""
查询腾讯云 COS 向量桶信息

用法:
    python3 get_vector_bucket.py \
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
    parser = base_parser("查询腾讯云 COS 向量桶信息")
    args = parser.parse_args()
    client = create_client(args)

    resp, data = client.get_vector_bucket(Bucket=args.bucket)
    success_output({
        "action": "get_vector_bucket",
        "bucket": args.bucket,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
