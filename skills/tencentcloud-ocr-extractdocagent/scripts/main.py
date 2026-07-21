#!/usr/bin/env python3
"""
腾讯云实时文档抽取Agent(ExtractDocAgent)调用脚本

支持从图片/PDF中按用户自定义的字段名称进行结构化信息抽取。
支持自定义字段名称、字段类型（KV对或表格字段）和字段提示词。
需要环境变量: TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY

用法:
    python main.py --image-url <url> --item-names <json_array> [--pdf-page-number <int>]
    python main.py --image-base64 <base64_or_filepath> --item-names <json_array> [--pdf-page-number <int>]
"""

import argparse
import base64
import json
import os
import sys

# SDK 最大图片/PDF限制 (10MB)
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# KeyType 合法值
VALID_KEY_TYPES = {0, 1}

# KeyType 含义映射
KEY_TYPE_MAP = {
    0: "KV对",
    1: "表格字段",
}

# 接口错误码含义映射
ERROR_CODE_MAP = {
    "FailedOperation.DownLoadError": "文件下载失败",
    "FailedOperation.ImageDecodeFailed": "图片解码失败",
    "FailedOperation.ImageSizeTooLarge": "图片尺寸过大，请确保编码后不超过10M，像素介于20-10000px",
    "FailedOperation.OcrFailed": "OCR识别失败",
    "FailedOperation.PDFParseFailed": "PDF解析失败",
    "FailedOperation.ResponseParseFailed": "结果解析失败",
    "FailedOperation.UnKnowError": "未知错误",
    "FailedOperation.UnKnowFileTypeError": "未知的文件类型",
    "FailedOperation.UnOpenError": "服务未开通，请先在腾讯云控制台开通文档抽取Agent服务",
    "InvalidParameterValue.InvalidParameterValueLimit": "参数值错误",
    "LimitExceeded.TooLargeFileError": "文件内容太大",
    "ResourceUnavailable.InArrears": "账号已欠费",
    "ResourceUnavailable.ResourcePackageRunOut": "账号资源包耗尽",
    "ResourcesSoldOut.ChargeStatusException": "计费状态异常",
}


def validate_env() -> tuple:
    """校验并返回腾讯云API密钥。"""
    secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
    if not secret_id or not secret_key:
        print("错误: 请设置环境变量 TENCENTCLOUD_SECRET_ID 和 TENCENTCLOUD_SECRET_KEY", file=sys.stderr)
        sys.exit(1)
    return secret_id, secret_key


def load_image_base64(value: str) -> str:
    """
    加载 Base64 图片/PDF 内容。
    如果 value 是一个存在的文件路径，则读取文件内容作为 Base64；
    否则直接视为 Base64 字符串。
    """
    if os.path.isfile(value):
        with open(value, "rb") as f:
            raw = f.read()
        # 如果文件内容本身就是Base64文本(如txt文件)，直接使用
        try:
            raw_str = raw.decode("utf-8").strip()
            base64.b64decode(raw_str, validate=True)
            return raw_str
        except (UnicodeDecodeError, ValueError):
            pass
        # 否则将二进制文件编码为Base64
        if len(raw) > MAX_IMAGE_SIZE_BYTES:
            print(f"错误: 文件大小超过 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB 限制", file=sys.stderr)
            sys.exit(1)
        encoded = base64.b64encode(raw).decode("utf-8")
        return encoded
    else:
        # 直接作为 Base64 字符串使用
        try:
            decoded = base64.b64decode(value, validate=True)
            if len(decoded) > MAX_IMAGE_SIZE_BYTES:
                print(f"错误: 图片/PDF大小超过 {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB 限制", file=sys.stderr)
                sys.exit(1)
        except ValueError:
            print("错误: 提供的 ImageBase64 不是合法的 Base64 编码，也不是有效的文件路径", file=sys.stderr)
            sys.exit(1)
        return value


def parse_item_names(item_names_str: str) -> list:
    """
    解析并校验 ItemNames JSON 字符串。
    返回解析后的字典列表。
    """
    try:
        items = json.loads(item_names_str)
    except json.JSONDecodeError as e:
        print(f"错误: --item-names 不是合法的 JSON 字符串: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(items, list):
        print("错误: --item-names 必须是 JSON 数组", file=sys.stderr)
        sys.exit(1)

    if len(items) == 0:
        print("错误: --item-names 至少需要提供一个抽取字段", file=sys.stderr)
        sys.exit(1)

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            print(f"错误: --item-names 第 {i + 1} 个元素必须是 JSON 对象", file=sys.stderr)
            sys.exit(1)

        key_name = item.get("KeyName")
        if not key_name or not isinstance(key_name, str) or not key_name.strip():
            print(f"错误: --item-names 第 {i + 1} 个元素的 KeyName 不能为空", file=sys.stderr)
            sys.exit(1)

        key_type = item.get("KeyType", 0)
        if key_type not in VALID_KEY_TYPES:
            print(
                f"错误: --item-names 第 {i + 1} 个元素的 KeyType 仅支持 0(KV对) 或 1(表格字段)，当前值: {key_type}",
                file=sys.stderr,
            )
            sys.exit(1)

    return items


def format_item_info(item_info: dict) -> dict:
    """格式化单个 ItemInfo 结构。"""
    result = {}
    key = item_info.get("Key")
    if key:
        auto_name = key.get("AutoName", "")
        config_name = key.get("ConfigName", "")
        if auto_name:
            result["字段名(自动识别)"] = auto_name
        if config_name:
            result["字段名(配置)"] = config_name

    value = item_info.get("Value")
    if value:
        auto_content = value.get("AutoContent", "")
        if auto_content:
            result["字段值"] = auto_content
        coord = value.get("Coord")
        if coord:
            result["坐标"] = coord
        page_index = value.get("PageIndex")
        if page_index is not None:
            result["页码"] = page_index

    return result


def format_response(resp_json: dict) -> dict:
    """格式化响应结果。"""
    output = {}

    # 业务错误检查
    error_code = resp_json.get("ErrorCode", "")
    error_message = resp_json.get("ErrorMessage", "")
    if error_code:
        output["业务错误码"] = error_code
        output["业务错误信息"] = error_message

    # 结构化抽取结果
    structural_list = resp_json.get("StructuralList")
    if structural_list:
        formatted_groups = []
        for group_idx, group in enumerate(structural_list):
            groups = group.get("Groups", []) or []
            formatted_lines = []
            for line_info in groups:
                lines = line_info.get("Lines", []) or []
                for item_info in lines:
                    formatted_item = format_item_info(item_info)
                    if formatted_item:
                        formatted_lines.append(formatted_item)
            if formatted_lines:
                formatted_groups.append({
                    "组序号": group_idx + 1,
                    "字段列表": formatted_lines,
                })
        output["抽取结果"] = formatted_groups
    else:
        output["抽取结果"] = []

    # 旋转角度
    angle = resp_json.get("Angle")
    if angle is not None:
        output["旋转角度"] = angle

    # RequestId
    output["RequestId"] = resp_json.get("RequestId", "")

    return output


def call_extract_doc_agent(args: argparse.Namespace) -> None:
    """调用腾讯云 ExtractDocAgent 接口。"""
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.ocr.v20181119 import ocr_client, models
    except ImportError:
        print(
            "错误: 缺少依赖 tencentcloud-sdk-python，请执行: pip install tencentcloud-sdk-python",
            file=sys.stderr,
        )
        sys.exit(1)

    secret_id, secret_key = validate_env()

    # 构建客户端
    cred = credential.Credential(secret_id, secret_key)
    http_profile = HttpProfile()
    http_profile.endpoint = "ocr.tencentcloudapi.com"
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client_profile.request_client = args.user_agent
    region = args.region if args.region else "ap-guangzhou"
    client = ocr_client.OcrClient(cred, region, client_profile)

    # 构建请求
    req = models.ExtractDocAgentRequest()

    if args.image_url:
        req.ImageUrl = args.image_url
    elif args.image_base64:
        req.ImageBase64 = load_image_base64(args.image_base64)
    else:
        print("错误: 必须提供 --image-url 或 --image-base64 之一", file=sys.stderr)
        sys.exit(1)

    # 解析并设置 ItemNames
    item_names_data = parse_item_names(args.item_names)
    item_names_list = []
    for item_data in item_names_data:
        item = models.ItemNames()
        item.KeyName = item_data["KeyName"]
        item.KeyType = item_data.get("KeyType", 0)
        key_prompt = item_data.get("KeyPrompt")
        if key_prompt:
            item.KeyPrompt = key_prompt
        item_names_list.append(item)
    req.ItemNames = item_names_list

    if args.pdf_page_number is not None:
        if args.pdf_page_number < 1:
            print("错误: PdfPageNumber 必须 >= 1", file=sys.stderr)
            sys.exit(1)
        req.PdfPageNumber = args.pdf_page_number

    # 发起请求
    try:
        resp = client.ExtractDocAgent(req)
    except TencentCloudSDKException as e:
        error_desc = ERROR_CODE_MAP.get(e.code, "")
        error_msg = f"API调用失败 [{e.code}]: {e.message}"
        if error_desc:
            error_msg += f" ({error_desc})"
        print(error_msg, file=sys.stderr)
        if e.requestId:
            print(f"RequestId: {e.requestId}", file=sys.stderr)
        sys.exit(1)

    # 解析并格式化输出
    resp_json = json.loads(resp.to_json_string())

    # 检查业务级错误
    error_code = resp_json.get("ErrorCode", "")
    if error_code:
        error_message = resp_json.get("ErrorMessage", "")
        print(f"业务处理失败 [{error_code}]: {error_message}", file=sys.stderr)
        request_id = resp_json.get("RequestId", "")
        if request_id:
            print(f"RequestId: {request_id}", file=sys.stderr)
        sys.exit(1)

    if args.raw:
        # 原始JSON输出模式
        print(json.dumps(resp_json, ensure_ascii=False, indent=2))
    else:
        result = format_response(resp_json)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="腾讯云实时文档抽取Agent(ExtractDocAgent)调用工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 通过URL抽取文档中的KV字段
  python main.py --image-url "https://example.com/contract.jpg" \\
    --item-names '[{"KeyName":"合同编号","KeyType":0,"KeyPrompt":"文档中的合同编号"}]'

  # 同时抽取KV字段和表格字段
  python main.py --image-url "https://example.com/invoice.jpg" \\
    --item-names '[{"KeyName":"发票号码","KeyType":0},{"KeyName":"明细","KeyType":1,"KeyPrompt":"明细条目表格"}]'

  # 通过文件路径(自动Base64编码)抽取
  python main.py --image-base64 ./document.png \\
    --item-names '[{"KeyName":"姓名","KeyType":0},{"KeyName":"金额","KeyType":0}]'

  # 识别PDF中的文档(指定页码)
  python main.py --image-base64 ./document.pdf --pdf-page-number 2 \\
    --item-names '[{"KeyName":"总金额","KeyType":0}]'

  # 输出原始JSON响应
  python main.py --image-url "https://example.com/doc.jpg" \\
    --item-names '[{"KeyName":"标题","KeyType":0}]' --raw
        """,
    )

    # 图片输入（二选一）
    img_group = parser.add_mutually_exclusive_group(required=True)
    img_group.add_argument(
        "--image-url",
        type=str,
        help="图片/PDF的URL地址",
    )
    img_group.add_argument(
        "--image-base64",
        type=str,
        help="图片/PDF的Base64字符串，或文件路径（自动编码）",
    )

    # 必填参数
    parser.add_argument(
        "--item-names",
        type=str,
        required=True,
        help='抽取字段定义，JSON数组字符串，例如: \'[{"KeyName":"合同编号","KeyType":0,"KeyPrompt":"文档中的合同编号"}]\'',
    )

    # 可选参数
    parser.add_argument(
        "--pdf-page-number",
        type=int,
        default=None,
        help="PDF页码，仅PDF有效，必须>=1",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        default=False,
        help="输出原始JSON响应（不做格式化处理）",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="腾讯云地域，默认 ap-guangzhou",
    )
    parser.add_argument(
        "--user-agent",
        type=str,
        default="Skills",
        help="客户端标识，用于统计调用来源，统一固定为 Skills",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    call_extract_doc_agent(args)


if __name__ == "__main__":
    main()
