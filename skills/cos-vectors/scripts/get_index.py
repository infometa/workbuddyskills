#!/usr/bin/env python3
"""
查询腾讯云 COS 向量索引信息

用法:
    python3 get_index.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        --index <IndexName>
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("查询腾讯云 COS 向量索引信息")
    parser.add_argument("--index", required=True, help="索引名称")
    args = parser.parse_args()
    client = create_client(args)

    resp, data = client.get_index(Bucket=args.bucket, Index=args.index)
    success_output({
        "action": "get_index",
        "bucket": args.bucket,
        "index": args.index,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
