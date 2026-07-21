#!/usr/bin/env python3
"""
列出腾讯云 COS 所有向量桶

用法:
    python3 list_vector_buckets.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        [--max-results 10] \
        [--prefix "my-"]
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("列出腾讯云 COS 所有向量桶")
    parser.add_argument("--max-results", type=int, default=None, help="最大返回数量")
    parser.add_argument("--prefix", default=None, help="桶名前缀过滤")
    args = parser.parse_args()
    client = create_client(args)

    kwargs = {}
    if args.max_results is not None:
        kwargs["MaxResults"] = args.max_results
    if args.prefix is not None:
        kwargs["Prefix"] = args.prefix

    resp, data = client.list_vector_buckets(**kwargs)
    success_output({
        "action": "list_vector_buckets",
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
