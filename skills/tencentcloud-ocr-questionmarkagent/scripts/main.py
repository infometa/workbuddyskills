#!/usr/bin/env python3
"""
腾讯云试题批改Agent(SubmitQuestionMarkAgentJob/DescribeQuestionMarkAgentJob)调用脚本

面向K12教育场景的试题批改产品，支持整卷/单题端到端处理（试卷切题+题目批改+手写坐标回显）。
异步接口：先调用Submit提交任务获取JobId，再调用Describe轮询查询结果。

需要环境变量: TENCENTCLOUD_SECRET_ID, TENCENTCLOUD_SECRET_KEY

用法:
    python main.py --image-url <url> [options]
    python main.py --image-base64 <base64_or_filepath> [options]
"""

import argparse
import base64
import json
import os
import sys
import time

# SDK 最大图片/PDF限制 (10MB)
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# 默认轮询参数
DEFAULT_POLL_INTERVAL = 2  # 秒
DEFAULT_POLL_TIMEOUT = 300  # 秒

# 任务终态
JOB_TERMINAL_STATES = {"DONE", "FAIL"}

# 任务状态中文映射
JOB_STATUS_MAP = {
    "WAIT": "等待中",
    "RUN": "执行中",
    "FAIL": "任务失败",
    "DONE": "任务成功",
}

# 接口错误码含义映射
ERROR_CODE_MAP = {
    "FailedOperation.DownLoadError": "文件下载失败",
    "FailedOperation.ImageDecodeFailed": "图片解码失败",
    "FailedOperation.ImageSizeTooLarge": "图片尺寸过大，请确保编码后不超过10M",
    "FailedOperation.OcrFailed": "OCR识别失败",
    "FailedOperation.PDFParseFailed": "PDF解析失败",
    "FailedOperation.UnKnowError": "未知错误",
    "FailedOperation.UnKnowFileTypeError": "未知的文件类型",
    "FailedOperation.UnOpenError": "服务未开通，请先在腾讯云控制台开通试题批改Agent服务",
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


def validate_question_config(config_str: str) -> str:
    """校验 QuestionConfigMap JSON 字符串。"""
    valid_keys = {"KnowledgePoints", "TrueAnswer", "ReturnAnswerPosition"}
    try:
        config = json.loads(config_str)
    except json.JSONDecodeError as e:
        print(f"错误: --question-config 不是合法的 JSON 字符串: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(config, dict):
        print("错误: --question-config 必须是 JSON 对象", file=sys.stderr)
        sys.exit(1)

    for key in config:
        if key not in valid_keys:
            print(
                f"警告: --question-config 中的 key '{key}' 不是已知配置项，"
                f"已知配置项: {', '.join(sorted(valid_keys))}",
                file=sys.stderr,
            )

    return config_str


def format_answer_info(answer: dict, index: int) -> dict:
    """格式化单个 AnswerInfo 结构。"""
    result = {"序号": index}

    handwrite_info = answer.get("HandwriteInfo", "")
    if handwrite_info:
        result["手写答案"] = handwrite_info

    is_correct = answer.get("IsCorrect")
    if is_correct is not None:
        result["是否正确"] = is_correct

    answer_analysis = answer.get("AnswerAnalysis", "")
    if answer_analysis:
        result["答案分析"] = answer_analysis

    right_answer = answer.get("RightAnswer", "")
    if right_answer:
        result["正确答案"] = right_answer

    knowledge_points = answer.get("KnowledgePoints")
    if knowledge_points:
        result["知识点"] = knowledge_points

    positions = answer.get("HandwriteInfoPositions")
    if positions:
        result["答案坐标"] = positions

    return result


def format_mark_info(mark_info: dict, prefix: str = "") -> dict:
    """
    递归格式化 MarkInfo 结构。
    prefix 用于生成题号层级，如 "1", "1-1", "1-1-2"。
    """
    result = {}

    if prefix:
        result["题号"] = prefix

    title = mark_info.get("MarkItemTitle", "")
    if title:
        result["题干"] = title

    # 格式化答案列表
    answer_infos = mark_info.get("AnswerInfos") or []
    if answer_infos:
        formatted_answers = []
        for idx, answer in enumerate(answer_infos, 1):
            formatted_answers.append(format_answer_info(answer, idx))
        result["答案列表"] = formatted_answers

    # 递归处理嵌套子题
    sub_mark_infos = mark_info.get("MarkInfos") or []
    if sub_mark_infos:
        formatted_subs = []
        for idx, sub_info in enumerate(sub_mark_infos, 1):
            sub_prefix = f"{prefix}-{idx}" if prefix else str(idx)
            formatted_subs.append(format_mark_info(sub_info, sub_prefix))
        result["子题"] = formatted_subs

    return result


def format_response(submit_resp_json: dict, describe_resp_json: dict) -> dict:
    """格式化完整响应结果（合并Submit和Describe的响应）。"""
    output = {}

    # 任务基本信息
    output["任务ID"] = submit_resp_json.get("JobId", "")
    output["任务状态"] = describe_resp_json.get("JobStatus", "")

    question_count = submit_resp_json.get("QuestionCount", "")
    if question_count:
        output["切题数量"] = question_count

    # 业务错误检查
    error_code = describe_resp_json.get("ErrorCode", "")
    error_message = describe_resp_json.get("ErrorMessage", "")
    if error_code:
        output["业务错误码"] = error_code
        output["业务错误信息"] = error_message

    # 旋转角度
    angle = describe_resp_json.get("Angle")
    if angle is not None:
        output["旋转角度"] = angle

    # 批改结果
    mark_infos = describe_resp_json.get("MarkInfos") or []
    if mark_infos:
        formatted_marks = []
        for idx, mark_info in enumerate(mark_infos, 1):
            formatted_marks.append(format_mark_info(mark_info, str(idx)))
        output["批改结果"] = formatted_marks
    else:
        output["批改结果"] = []

    # RequestId
    output["RequestId"] = describe_resp_json.get("RequestId", "")

    return output


def submit_job(client, models, args) -> dict:
    """提交试题批改任务，返回提交响应的JSON。"""
    req = models.SubmitQuestionMarkAgentJobRequest()

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

    if args.single_question:
        req.BoolSingleQuestion = True

    if args.enable_deep_think:
        req.EnableDeepThink = True

    if args.question_config:
        req.QuestionConfigMap = validate_question_config(args.question_config)

    if args.reference_answer:
        req.ReferenceAnswer = args.reference_answer

    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

    try:
        resp = client.SubmitQuestionMarkAgentJob(req)
    except TencentCloudSDKException as e:
        error_desc = ERROR_CODE_MAP.get(e.code, "")
        error_msg = f"提交任务失败 [{e.code}]: {e.message}"
        if error_desc:
            error_msg += f" ({error_desc})"
        print(error_msg, file=sys.stderr)
        if e.requestId:
            print(f"RequestId: {e.requestId}", file=sys.stderr)
        sys.exit(1)

    return json.loads(resp.to_json_string())


def poll_job_result(client, models, job_id: str, poll_interval: int, poll_timeout: int) -> dict:
    """轮询查询任务结果，返回查询响应的JSON。"""
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

    start_time = time.time()
    poll_count = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > poll_timeout:
            print(
                f"错误: 轮询超时（已等待 {int(elapsed)} 秒，超时限制 {poll_timeout} 秒）",
                file=sys.stderr,
            )
            sys.exit(1)

        poll_count += 1
        req = models.DescribeQuestionMarkAgentJobRequest()
        req.JobId = job_id

        try:
            resp = client.DescribeQuestionMarkAgentJob(req)
        except TencentCloudSDKException as e:
            error_desc = ERROR_CODE_MAP.get(e.code, "")
            error_msg = f"查询任务失败 [{e.code}]: {e.message}"
            if error_desc:
                error_msg += f" ({error_desc})"
            print(error_msg, file=sys.stderr)
            if e.requestId:
                print(f"RequestId: {e.requestId}", file=sys.stderr)
            sys.exit(1)

        resp_json = json.loads(resp.to_json_string())
        job_status = resp_json.get("JobStatus", "")
        status_desc = JOB_STATUS_MAP.get(job_status, job_status)

        if job_status in JOB_TERMINAL_STATES:
            if job_status == "FAIL":
                error_code = resp_json.get("ErrorCode", "")
                error_message = resp_json.get("ErrorMessage", "")
                print(f"任务执行失败 [{error_code}]: {error_message}", file=sys.stderr)
                request_id = resp_json.get("RequestId", "")
                if request_id:
                    print(f"RequestId: {request_id}", file=sys.stderr)
                sys.exit(1)
            return resp_json

        # 非终态，打印进度信息后继续轮询
        print(
            f"[轮询 #{poll_count}] 任务状态: {status_desc} ({job_status})，"
            f"已等待 {int(elapsed)} 秒，{poll_interval} 秒后重试...",
            file=sys.stderr,
        )
        time.sleep(poll_interval)


def run(args: argparse.Namespace) -> None:
    """执行试题批改主流程。"""
    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
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

    # 步骤1: 提交任务
    print("正在提交试题批改任务...", file=sys.stderr)
    submit_resp_json = submit_job(client, models, args)
    job_id = submit_resp_json.get("JobId", "")
    question_count = submit_resp_json.get("QuestionCount", "0")

    if not job_id:
        print("错误: 提交任务成功但未返回 JobId", file=sys.stderr)
        sys.exit(1)

    print(f"任务提交成功，JobId: {job_id}，切题数量: {question_count}", file=sys.stderr)

    # 步骤2: 轮询查询结果
    print("正在轮询查询批改结果...", file=sys.stderr)
    describe_resp_json = poll_job_result(
        client,
        models,
        job_id,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
    )

    print("任务完成，正在输出结果...", file=sys.stderr)

    if args.raw:
        # 原始JSON输出模式（合并submit和describe的结果）
        raw_output = {
            "JobId": job_id,
            "QuestionCount": question_count,
            "QuestionInfo": submit_resp_json.get("QuestionInfo"),
        }
        raw_output.update(describe_resp_json)
        print(json.dumps(raw_output, ensure_ascii=False, indent=2))
    else:
        result = format_response(submit_resp_json, describe_resp_json)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="腾讯云试题批改Agent(SubmitQuestionMarkAgentJob/DescribeQuestionMarkAgentJob)调用工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 通过URL进行整卷批改（输出知识点和正确答案）
  python main.py --image-url "https://example.com/exam_paper.jpg" \\
    --question-config '{"KnowledgePoints":true,"TrueAnswer":true}'

  # 通过URL进行单题批改（带参考答案）
  python main.py --image-url "https://example.com/single_question.jpg" \\
    --single-question --reference-answer "x=2"

  # 开启深度思考模式
  python main.py --image-url "https://example.com/exam.jpg" --enable-deep-think

  # 通过文件路径进行批改（自动Base64编码）
  python main.py --image-base64 ./exam_paper.png

  # 批改PDF试卷（指定页码）
  python main.py --image-base64 ./exam.pdf --pdf-page-number 2

  # 输出原始JSON响应
  python main.py --image-url "https://example.com/exam.jpg" --raw

  # 指定地域和自定义轮询参数
  python main.py --image-url "https://example.com/exam.jpg" \\
    --region ap-beijing --poll-interval 3 --poll-timeout 300
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
        help="PDF页码，仅PDF有效，必须>=1，默认1",
    )
    parser.add_argument(
        "--single-question",
        action="store_true",
        default=False,
        help="是否单题批改（跳过切题），默认false",
    )
    parser.add_argument(
        "--enable-deep-think",
        action="store_true",
        default=False,
        help="是否开启深度思考（更深层推理，速度更慢），默认false",
    )
    parser.add_argument(
        "--question-config",
        type=str,
        default=None,
        help='题目信息输出配置，JSON字符串，例如: \'{"KnowledgePoints":true,"TrueAnswer":true}\'',
    )
    parser.add_argument(
        "--reference-answer",
        type=str,
        default=None,
        help="单题批改时的参考答案（仅单题时有效）",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"轮询间隔时间（秒），默认{DEFAULT_POLL_INTERVAL}",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=DEFAULT_POLL_TIMEOUT,
        help=f"轮询超时时间（秒），默认{DEFAULT_POLL_TIMEOUT}",
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
    run(args)


if __name__ == "__main__":
    main()
