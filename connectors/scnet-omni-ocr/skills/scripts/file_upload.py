"""Upload a local file with presigned fields returned by the MCP server."""

import os
import uuid
from urllib import error, request


def _build_multipart_body(fields: dict, file_name: str, file_content: bytes):
    """Encode regular fields and one file as multipart/form-data."""
    boundary = f"----PythonMultipart{uuid.uuid4().hex}"
    boundary_bytes = boundary.encode("ascii")
    body = bytearray()
    for name, value in fields.items():
        body.extend(b"--" + boundary_bytes + b"\r\n")
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(
                "utf-8"
            )
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    body.extend(b"--" + boundary_bytes + b"\r\n")
    body.extend(
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n".encode("utf-8")
    )
    body.extend(file_content)
    body.extend(b"\r\n--" + boundary_bytes + b"--\r\n")
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def upload_file(presign_data: dict, local_file_path: str):
    """Upload a local file using presigned multipart form fields."""
    fields = {
        "policy": presign_data["policy"],
        "x-amz-algorithm": presign_data["x_amz_algorithm"],
        "x-amz-credential": presign_data["x_amz_credential"],
        "x-amz-date": presign_data["x_amz_date"],
        "x-amz-signature": presign_data["x_amz_signature"],
        "key": presign_data["key"],
    }

    try:
        print(f"开始上传文件：{os.path.basename(local_file_path)}")
        with open(local_file_path, "rb") as file_obj:
            body, content_type = _build_multipart_body(
                fields, os.path.basename(local_file_path), file_obj.read()
            )
        req = request.Request(
            presign_data["upload_url"],
            data=body,
            headers={
                "Content-Type": content_type,
                "Content-Length": str(len(body)),
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                status_code = getattr(response, "status", None)
                if status_code is None:
                    status_code = response.getcode()
                response_text = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            status_code = exc.code
            response_text = exc.read().decode("utf-8", errors="replace")
        if status_code in (200, 204):
            print("文件上传成功")
            return {
                "file_url": presign_data["file_url"],
                "upload_status": "success",
            }
        raise Exception(f"上传失败，状态码：{status_code}，返回：{response_text}")
    except Exception as exc:
        print(f"文件上传异常：{exc}")
        raise


def upload_and_get_web_file_path(
    presign_data: dict, local_file_path: str
) -> str:
    """Upload a local file with MCP-issued presign data and return its URL."""
    if not os.path.isfile(local_file_path):
        raise FileNotFoundError(f"本地文件不存在：{local_file_path}")

    # Allow callers to pass either the complete MCP response or its data field.
    if "data" in presign_data:
        if presign_data.get("code") != 200:
            raise ValueError("获取文件上传凭证失败")
        presign = presign_data.get("data")
    else:
        presign = presign_data
    if not isinstance(presign, dict) or not presign:
        raise ValueError("文件上传凭证为空")

    upload_result = upload_file(presign, local_file_path)
    return upload_result["file_url"]
