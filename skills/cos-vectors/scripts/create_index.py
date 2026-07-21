#!/usr/bin/env python3
"""
创建腾讯云 COS 向量索引

用法:
    python3 create_index.py \
        --secret-id <SecretId> \
        --secret-key <SecretKey> \
        --region <Region> \
        --bucket <BucketName-APPID> \
        --index <IndexName> \
        --dimension <Dimension> \
        [--data-type float32] \
        [--distance-metric cosine] \
        [--non-filterable-keys key1,key2]
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import base_parser, create_client, success_output, run


def main():
    parser = base_parser("创建腾讯云 COS 向量索引")
    parser.add_argument("--index", required=True, help="索引名称")
    parser.add_argument("--dimension", required=True, type=int, help="向量维度，范围 1-4096")
    parser.add_argument("--data-type", default="float32", help="向量数据类型，支持 float32（默认）")
    parser.add_argument("--distance-metric", default="cosine", choices=["cosine", "euclidean"], help="距离度量，支持 cosine（默认）、euclidean")
    parser.add_argument("--non-filterable-keys", default=None, help="非过滤元数据键列表，逗号分隔")
    args = parser.parse_args()
    client = create_client(args)

    kwargs = {
        "Bucket": args.bucket,
        "Index": args.index,
        "DataType": args.data_type,
        "Dimension": args.dimension,
        "DistanceMetric": args.distance_metric,
    }
    if args.non_filterable_keys:
        kwargs["NonFilterableMetadataKeys"] = args.non_filterable_keys.split(",")

    resp, data = client.create_index(**kwargs)
    success_output({
        "action": "create_index",
        "bucket": args.bucket,
        "index": args.index,
        "dimension": args.dimension,
        "data_type": args.data_type,
        "distance_metric": args.distance_metric,
        "region": args.region,
        "response_data": data if isinstance(data, dict) else str(data),
    })


if __name__ == "__main__":
    run(main)
