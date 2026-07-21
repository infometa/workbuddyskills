#!/usr/bin/env python3
"""
列出腾讯云 COS 向量索引中的向量列表

用法:
    python3 list_vectors.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        --index <IndexName> \
        [--max-results 10] \
        [--return-data] \
        [--return-metadata]
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("列出腾讯云 COS 向量索引中的向量列表")
    parser.add_argument("--index", required=True, help="索引名称")
    parser.add_argument("--max-results", type=int, default=None, help="最大返回数量")
    parser.add_argument("--return-data", action="store_true", default=False, help="是否返回向量数据")
    parser.add_argument("--return-metadata", action="store_true", default=False, help="是否返回元数据")
    parser.add_argument("--segment-count", type=int, default=None, help="分段数")
    parser.add_argument("--segment-index", type=int, default=None, help="分段索引（从0开始）")
    args = parser.parse_args()
    client = create_client(args)

    kwargs = {
        "Bucket": args.bucket,
        "Index": args.index,
    }
    if args.max_results is not None:
        kwargs["MaxResults"] = args.max_results
    if args.return_data:
        kwargs["ReturnData"] = True
    if args.return_metadata:
        kwargs["ReturnMetaData"] = True
    if args.segment_count is not None and args.segment_index is not None:
        kwargs["SegmentCount"] = args.segment_count
        kwargs["SegmentIndex"] = args.segment_index

    resp, data = client.list_vectors(**kwargs)
    success_output({
        "action": "list_vectors",
        "bucket": args.bucket,
        "index": args.index,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
