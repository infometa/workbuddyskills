#!/usr/bin/env python3
"""
创建腾讯云 COS 向量桶

用法:
    python3 create_vector_bucket.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        [--sse-type AES256]
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("创建腾讯云 COS 向量桶")
    parser.add_argument(
        "--sse-type",
        choices=["AES256"],
        default=None,
        help="加密类型，当前仅支持 AES256（可选）",
    )
    args = parser.parse_args()
    client = create_client(args)

    kwargs = {"Bucket": args.bucket}
    if args.sse_type:
        kwargs["SseType"] = args.sse_type

    resp, data = client.create_vector_bucket(**kwargs)
    success_output({
        "action": "create_vector_bucket",
        "bucket": args.bucket,
        "region": args.region,
        "encrypted": args.sse_type is not None,
        "sse_type": args.sse_type,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
