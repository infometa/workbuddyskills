#!/usr/bin/env python3
"""
腾讯云表格识别v3(RecognizeTableAccurateOCR)调用脚本

支持中英文图片/PDF内常规表格、无线表格、多表格的检测和识别，
返回每个单元格的文字内容，支持旋转的表格图片识别，且支持将识别结果保存为Excel格式。
需要环境变量: TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY

用法:
    python main.py --image-url <url> [--pdf-page-number <int>] [--save-excel <path>]
    python main.py --image-base64 <base64_or_filepath> [--pdf-page-number <int>] [--save-excel <path>]
"""

import argparse
import base64
import json
import os
import sys

# SDK 最大图片/PDF限制 (10MB)
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# 表格类型映射
TABLE_TYPE_MAP = {
    0: "非表格文本",
    1: "有线表格",
    2: "无线表格",
}

# 接口错误码含义映射
ERROR_CODE_MAP = {
    "FailedOperation.DownLoadError": "文件下载失败",
    "FailedOperation.EmptyImageError": "图片内容为空",
    "FailedOperation.ImageDecodeFailed": "图片解码失败",
    "FailedOperation.ImageSizeTooLarge": "图片尺寸过大，请确保编码后不超过10M，分辨率建议600*800以上且长宽比小于3",
    "FailedOperation.OcrFailed": "OCR识别失败",
    "FailedOperation.PDFParseFailed": "PDF解析失败",
    "FailedOperation.UnKnowError": "未知错误",
    "FailedOperation.UnKnowFileTypeError": "未知的文件类型",
    "FailedOperation.UnOpenError": "服务未开通，请先在腾讯云控制台开通表格识别服务",
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


def save_excel_data(data_base64: str, output_path: str) -> None:
    """将Base64编码的Excel数据保存为文件。"""
    try:
        excel_bytes = base64.b64decode(data_base64)
        with open(output_path, "wb") as f:
            f.write(excel_bytes)
        print(f"Excel文件已保存至: {output_path}")
    except Exception as e:  # pylint: disable=broad-except
        print(f"警告: 保存Excel文件失败: {e}", file=sys.stderr)


def format_table_detection(table: dict, index: int) -> dict:
    """格式化单个表格检测结果。"""
    table_type = table.get("Type")
    type_desc = TABLE_TYPE_MAP.get(table_type, f"未知类型({table_type})")

    cells = table.get("Cells", []) or []
    formatted_cells = []
    for cell in cells:
        cell_info = {
            "行范围": f"{cell.get('RowTl', '')} - {cell.get('RowBr', '')}",
            "列范围": f"{cell.get('ColTl', '')} - {cell.get('ColBr', '')}",
            "文本": cell.get("Text", ""),
        }
        confidence = cell.get("Confidence")
        if confidence is not None:
            cell_info["置信度"] = confidence
        cell_type = cell.get("Type")
        if cell_type:
            cell_info["单元格类型"] = cell_type
        formatted_cells.append(cell_info)

    result = {
        "表格序号": index + 1,
        "表格类型": type_desc,
        "单元格数量": len(cells),
        "单元格详情": formatted_cells,
    }

    coord_points = table.get("TableCoordPoint")
    if coord_points:
        result["表格坐标"] = [{"X": p.get("X"), "Y": p.get("Y")} for p in coord_points]

    return result


def format_response(resp_json: dict, save_excel_path: str = None) -> dict:
    """格式化响应结果。"""
    output = {}

    # 表格检测结果
    table_detections = resp_json.get("TableDetections")
    if table_detections:
        output["表格数量"] = len(table_detections)
        output["表格详情"] = [
            format_table_detection(table, i)
            for i, table in enumerate(table_detections)
        ]
    else:
        output["表格数量"] = 0
        output["表格详情"] = []

    # Excel数据
    data = resp_json.get("Data")
    if data:
        output["Excel数据"] = "已返回(Base64编码)"
        if save_excel_path:
            save_excel_data(data, save_excel_path)
    else:
        output["Excel数据"] = "无"

    # PDF页数
    pdf_page_size = resp_json.get("PdfPageSize")
    if pdf_page_size is not None and pdf_page_size > 0:
        output["PDF总页数"] = pdf_page_size

    # 旋转角度
    angle = resp_json.get("Angle")
    if angle is not None:
        output["旋转角度"] = angle

    # RequestId
    output["RequestId"] = resp_json.get("RequestId", "")

    return output


def call_recognize_table_accurate_ocr(args: argparse.Namespace) -> None:
    """调用腾讯云 RecognizeTableAccurateOCR 接口。"""
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
    req = models.RecognizeTableAccurateOCRRequest()

    if args.image_url:
        req.ImageUrl = args.image_url
    elif args.image_base64:
        req.ImageBase64 = load_image_base64(args.image_base64)
    else:
        print("错误: 必须提供 --image-url 或 --image-base64 之一", file=sys.stderr)
        sys.exit(1)

    if args.pdf_page_number is not None:
        if args.pdf_page_number < 1:
            print("错误: PdfPageNumber 必须 >= 1", file=sys.stderr)
            sys.exit(1)
        req.PdfPageNumber = args.pdf_page_number

    # 发起请求
    try:
        resp = client.RecognizeTableAccurateOCR(req)
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

    if args.raw:
        # 原始JSON输出模式
        print(json.dumps(resp_json, ensure_ascii=False, indent=2))
    else:
        result = format_response(resp_json, save_excel_path=args.save_excel)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="腾讯云表格识别v3(RecognizeTableAccurateOCR)调用工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 通过URL识别表格
  python main.py --image-url "https://example.com/table.jpg"

  # 通过文件路径(自动Base64编码)识别
  python main.py --image-base64 ./table.png

  # 识别PDF中的表格(指定页码)
  python main.py --image-base64 ./document.pdf --pdf-page-number 2

  # 识别并保存Excel文件
  python main.py --image-url "https://example.com/table.jpg" --save-excel ./result.xlsx

  # 输出原始JSON响应
  python main.py --image-url "https://example.com/table.jpg" --raw
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

    # 可选参数
    parser.add_argument(
        "--pdf-page-number",
        type=int,
        default=None,
        help="PDF页码，仅PDF有效，默认1，必须>=1",
    )
    parser.add_argument(
        "--save-excel",
        type=str,
        default=None,
        help="将识别结果的Excel数据保存到指定路径（如 ./result.xlsx）",
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
    call_recognize_table_accurate_ocr(args)


if __name__ == "__main__":
    main()
