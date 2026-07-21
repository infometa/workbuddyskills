#!/usr/bin/env python3
"""
列出腾讯云 COS 向量桶中的所有索引

用法:
    python3 list_indexes.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        [--max-results 10] \
        [--prefix "demo-"]
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("列出腾讯云 COS 向量桶中的所有索引")
    parser.add_argument("--max-results", type=int, default=None, help="最大返回数量")
    parser.add_argument("--prefix", default=None, help="索引名前缀过滤")
    args = parser.parse_args()
    client = create_client(args)

    kwargs = {"Bucket": args.bucket}
    if args.max_results is not None:
        kwargs["MaxResults"] = args.max_results
    if args.prefix is not None:
        kwargs["Prefix"] = args.prefix

    resp, data = client.list_indexes(**kwargs)
    success_output({
        "action": "list_indexes",
        "bucket": args.bucket,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
