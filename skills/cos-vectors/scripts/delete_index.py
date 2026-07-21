#!/usr/bin/env python3
"""
删除腾讯云 COS 向量索引

用法:
    python3 delete_index.py \
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
    parser = base_parser("删除腾讯云 COS 向量索引")
    parser.add_argument("--index", required=True, help="索引名称")
    args = parser.parse_args()
    client = create_client(args)

    resp, data = client.delete_index(Bucket=args.bucket, Index=args.index)
    success_output({
        "action": "delete_index",
        "bucket": args.bucket,
        "index": args.index,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
