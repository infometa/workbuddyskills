#!/usr/bin/env python3
"""
微云通用上传脚本 — 一键上传本地文件到微云网盘。

整合了以下三个步骤：
  1. 计算上传参数（block_sha_list、file_sha、check_sha、check_data、file_md5）
  2. MCP 预上传（检查秒传或获取上传通道）
  3. MCP 分片上传（循环「预上传获取通道 → 上传一片」直到完成）

使用方法：
  python3 upload_to_weiyun.py <文件路径> [--pdir_key <目录key>]

环境变量（可选，也可通过命令行参数传入）：
  WEIYUN_MCP_URL    — MCP 服务地址，默认 https://www.weiyun.com/api/v3/mcpserver
  WEIYUN_MCP_TOKEN  — MCP token，必须提供（命令行 --token 或环境变量）
  WEIYUN_ENV_ID     — 环境标识（如 sit-0cd15bb3），可选

示例：
  # 使用命令行参数
  python3 upload_to_weiyun.py /tmp/Test666.json --token 1fc54abae52bb44d4b8a421cc2734c04

  # 使用环境变量
  export WEIYUN_MCP_TOKEN=1fc54abae52bb44d4b8a421cc2734c04
  python3 upload_to_weiyun.py /tmp/Test666.json

  # 指定上传目录
  python3 upload_to_weiyun.py /tmp/Test666.json --token xxx --pdir_key abc123

依赖：
  pip install requests（如未安装）

重要说明：
  本脚本包含纯 Python SHA1 实现，支持提取未经 finalization 的内部寄存器状态。
  这是 Python 标准库 hashlib.sha1 无法做到的，也是微云上传协议的核心需求。
"""

import _encoding_fix  # noqa: F401  Windows UTF-8 fix, must be first import

import argparse
import base64
import hashlib
import json
import os
import random
import struct
import sys
import time

try:
    import requests
except ImportError:
    print("错误：需要 requests 库，请执行 pip install requests")
    sys.exit(1)


# ========== 纯 Python SHA1 实现（支持获取内部状态）==========

def _left_rotate(n, b):
    """32-bit 左旋转"""
    return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF


class SHA1:
    """纯 Python SHA1 实现，支持获取内部中间状态（不做 finalization）"""

    def __init__(self):
        # SHA1 初始 h0-h4
        self.h0 = 0x67452301
        self.h1 = 0xEFCDAB89
        self.h2 = 0x98BADCFE
        self.h3 = 0x10325476
        self.h4 = 0xC3D2E1F0
        self._message_byte_length = 0
        self._unprocessed = b""

    def update(self, data):
        """往 SHA1 对象中追加数据"""
        self._unprocessed += data
        self._message_byte_length += len(data)
        # 每 64 字节处理一次
        while len(self._unprocessed) >= 64:
            self._process_chunk(self._unprocessed[:64])
            self._unprocessed = self._unprocessed[64:]

    def _process_chunk(self, chunk):
        """处理一个 64 字节的 SHA1 block"""
        assert len(chunk) == 64
        w = [0] * 80
        for i in range(16):
            w[i] = struct.unpack(">I", chunk[i * 4:(i + 1) * 4])[0]
        for i in range(16, 80):
            w[i] = _left_rotate(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1)
        a, b, c, d, e = self.h0, self.h1, self.h2, self.h3, self.h4
        for i in range(80):
            if 0 <= i <= 19:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif 20 <= i <= 39:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif 40 <= i <= 59:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            elif 60 <= i <= 79:
                f = b ^ c ^ d
                k = 0xCA62C1D6
            temp = (_left_rotate(a, 5) + f + e + k + w[i]) & 0xFFFFFFFF
            e = d
            d = c
            c = _left_rotate(b, 30)
            b = a
            a = temp
        self.h0 = (self.h0 + a) & 0xFFFFFFFF
        self.h1 = (self.h1 + b) & 0xFFFFFFFF
        self.h2 = (self.h2 + c) & 0xFFFFFFFF
        self.h3 = (self.h3 + d) & 0xFFFFFFFF
        self.h4 = (self.h4 + e) & 0xFFFFFFFF

    def get_state(self):
        """
        获取 SHA1 内部状态（h0-h4），以小端序输出 20 字节的 hex 字符串。
        注意：不做 padding/finalization，直接读取内部寄存器。
        要求调用时 unprocessed 缓冲区为空（即已处理数据长度是 64 字节的整数倍）。
        """
        assert len(self._unprocessed) == 0, \
            f"get_state 要求 unprocessed 为空，当前有 {len(self._unprocessed)} 字节未处理"
        result = b""
        for h in (self.h0, self.h1, self.h2, self.h3, self.h4):
            result += struct.pack("<I", h)  # 小端序
        return result.hex()

    def hexdigest(self):
        """返回带 finalization 的标准 SHA1 digest（大端序，与 hashlib.sha1 一致）"""
        # 先复制状态，不影响原对象
        message_byte_length = self._message_byte_length
        unprocessed = self._unprocessed
        h0, h1, h2, h3, h4 = self.h0, self.h1, self.h2, self.h3, self.h4
        # padding
        unprocessed += b"\x80"
        unprocessed += b"\x00" * ((56 - len(unprocessed) % 64) % 64)
        unprocessed += struct.pack(">Q", message_byte_length * 8)
        # 临时处理剩余 chunk
        tmp = SHA1.__new__(SHA1)
        tmp.h0, tmp.h1, tmp.h2, tmp.h3, tmp.h4 = h0, h1, h2, h3, h4
        tmp._unprocessed = b""
        tmp._message_byte_length = message_byte_length
        while len(unprocessed) >= 64:
            tmp._process_chunk(unprocessed[:64])
            unprocessed = unprocessed[64:]
        return "{:08x}{:08x}{:08x}{:08x}{:08x}".format(
            tmp.h0, tmp.h1, tmp.h2, tmp.h3, tmp.h4)


# ========== 文件参数计算 ==========

BLOCK_SIZE = 524288  # 512KB


def calc_upload_params(file_path):
    """
    计算微云上传所需的全部参数：
    - block_sha_list：分块 SHA1 列表
    - file_sha：整个文件的标准 SHA1
    - file_md5：整个文件的 MD5
    - check_sha：SHA1 校验中间状态
    - check_data：文件末尾校验字节的 Base64 编码

    返回 dict，可直接用于 MCP 预上传请求。
    """
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    # 计算 lastBlockSize 和 checkBlockSize
    last_block_size = file_size % BLOCK_SIZE
    if last_block_size == 0:
        last_block_size = BLOCK_SIZE
    check_block_size = last_block_size % 128
    if check_block_size == 0:
        check_block_size = 128
    before_block_size = file_size - last_block_size
    block_sha_list = []
    sha1 = SHA1()
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        # 处理除最后一块之外的所有 block
        for offset in range(0, before_block_size, BLOCK_SIZE):
            data = f.read(BLOCK_SIZE)
            sha1.update(data)
            md5.update(data)
            block_sha_list.append(sha1.get_state())
        # 读取最后一块中去掉 checkBlockSize 之后的部分
        between_data = f.read(last_block_size - check_block_size)
        sha1.update(between_data)
        md5.update(between_data)
        check_sha = sha1.get_state()
        # 读取 checkData 部分
        check_data_bytes = f.read(check_block_size)
        sha1.update(check_data_bytes)
        md5.update(check_data_bytes)
        file_sha = sha1.hexdigest()
        check_data = base64.b64encode(check_data_bytes).decode("utf-8")
        # 最后一个 block 的 sha 为 file_sha
        block_sha_list.append(file_sha)
    file_md5 = md5.hexdigest()
    return {
        "filename": filename,
        "file_size": file_size,
        "file_sha": file_sha,
        "file_md5": file_md5,
        "block_sha_list": block_sha_list,
        "check_sha": check_sha,
        "check_data": check_data,
    }


# ========== MCP 调用 ==========

_request_id = 0


def mcp_call(mcp_url, headers, tool_name, arguments, max_retries=3):
    """
    调用微云 MCP Tool，返回解析后的响应 dict。
    遇到 retcode=50000（服务繁忙）时自动重试，最多 max_retries 次，每次间隔 2~5 秒。
    """
    global _request_id
    for attempt in range(1, max_retries + 1):
        _request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": _request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        resp = requests.post(mcp_url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        content = result.get("result", {}).get("content", [])
        parsed = None
        for item in content:
            if item.get("type") == "text":
                parsed = json.loads(item["text"])
                break
        if parsed is None:
            parsed = result
        # 检查是否为服务繁忙错误（retcode=50000），如果是则重试
        retcode = parsed.get("retcode", 0)
        if retcode == 50000 and attempt < max_retries:
            wait = random.uniform(2, 5)
            print(f"  ⚠️ 服务繁忙(50000)，{wait:.1f}s 后重试 ({attempt}/{max_retries})...")
            time.sleep(wait)
            continue
        return parsed
    # 不应到达这里，但以防万一
    return parsed


# ========== 上传核心逻辑 ==========

def upload_file(file_path, mcp_url, headers, pdir_key=None, max_rounds=50):
    """
    上传文件到微云的完整流程：
    1. 计算分块参数
    2. 预上传（检查秒传）
    3. 循环分片上传

    参数：
      file_path   — 本地文件路径
      mcp_url     — MCP 服务地址
      headers     — HTTP 请求头（含 Cookie 和 WyHeader）
      pdir_key    — 上传目标目录 key（可选，不填使用 token 绑定的目录）
      max_rounds  — 最大上传轮数，防止死循环

    返回：
      成功时返回 dict: {"file_id": "...", "filename": "..."}
      失败时抛出异常
    """
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    # 第一步：计算上传参数
    print(f"[1/3] 计算上传参数: {filename} ({file_size} 字节)...")
    params = calc_upload_params(file_path)
    print(f"  block_count={len(params['block_sha_list'])}, "
          f"file_sha={params['file_sha'][:16]}..., "
          f"file_md5={params['file_md5'][:16]}...")
    # 构建预上传请求参数
    pre_upload_args = {
        "filename": params["filename"],
        "file_size": params["file_size"],
        "file_sha": params["file_sha"],
        "file_md5": params["file_md5"],
        "block_sha_list": params["block_sha_list"],
        "check_sha": params["check_sha"],
        "check_data": params["check_data"],
    }
    if pdir_key:
        pre_upload_args["pdir_key"] = pdir_key
    # 读取文件数据到内存（用于分片上传）
    with open(file_path, "rb") as f:
        file_data = f.read()
    # 第二步 & 第三步：循环「预上传 → 上传一片」
    print(f"[2/3] 开始上传...")
    round_num = 0
    while round_num < max_rounds:
        round_num += 1
        # 预上传，获取当前需要上传的通道
        pre_rsp = mcp_call(mcp_url, headers, "weiyun.upload", pre_upload_args)
        # 检查错误
        if pre_rsp.get("error"):
            raise RuntimeError(f"预上传失败: {pre_rsp['error']}")
        # 检查秒传
        if pre_rsp.get("file_exist", False):
            file_id = pre_rsp.get("file_id", "")
            fname = pre_rsp.get("filename", filename)
            print(f"  ✅ 秒传成功！file_id={file_id}")
            return {"file_id": file_id, "filename": fname}
        # 获取通道列表
        ch_list = pre_rsp.get("channel_list", [])
        uk = pre_rsp.get("upload_key", "")
        ex = pre_rsp.get("ex", "")
        # 找第一个 len > 0 的通道
        ch = None
        for c in ch_list:
            if int(c.get("len", 0)) > 0:
                ch = c
                break
        if ch is None:
            state = int(pre_rsp.get("upload_state", 0))
            if state == 2:
                file_id = pre_rsp.get("file_id", "")
                fname = pre_rsp.get("filename", filename)
                print(f"  ✅ 上传完成！file_id={file_id}")
                return {"file_id": file_id, "filename": fname}
            raise RuntimeError(f"无可上传通道，upload_state={state}")
        offset = int(ch["offset"])
        length = int(ch["len"])
        channel_id = int(ch["id"])
        actual_len = min(length, len(file_data) - offset)
        progress_pct = min(100, int(offset / file_size * 100))
        print(f"  [{round_num}] 上传分片: offset={offset}, len={actual_len}, "
              f"ch={channel_id}, progress≈{progress_pct}%")
        # 准备分片数据
        chunk = file_data[offset:offset + actual_len]
        chunk_b64 = base64.b64encode(chunk).decode("utf-8")
        cl = [{"id": int(c["id"]), "offset": int(c["offset"]), "len": int(c["len"])}
              for c in ch_list]
        # 上传分片
        up_rsp = mcp_call(mcp_url, headers, "weiyun.upload", {
            "filename": filename,
            "file_size": file_size,
            "file_sha": params["file_sha"],
            "block_sha_list": [],
            "check_sha": params["check_sha"],
            "upload_key": uk,
            "channel_list": cl,
            "channel_id": channel_id,
            "ex": ex,
            "file_data": chunk_b64,
        })
        # 检查上传结果
        if up_rsp.get("error"):
            raise RuntimeError(f"分片上传失败: {up_rsp['error']}")
        state = int(up_rsp.get("upload_state", 0))
        if state == 2:
            file_id = up_rsp.get("file_id", "")
            fname = up_rsp.get("filename", filename)
            print(f"[3/3] ✅ 上传完成！file_id={file_id}, filename={fname}")
            return {"file_id": file_id, "filename": fname}
    raise RuntimeError(f"超过最大上传轮数 ({max_rounds})，上传未完成")


# ========== 命令行入口 ==========

def main():
    parser = argparse.ArgumentParser(
        description="微云通用上传脚本 — 一键上传本地文件到微云网盘",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s /tmp/Test666.json --token 1fc54abae52bb44d4b8a421cc2734c04
  %(prog)s /tmp/Test666.json --token xxx --pdir_key abc123
  %(prog)s /tmp/Test666.json --token xxx --env_id sit-0cd15bb3

环境变量：
  WEIYUN_MCP_URL    MCP 服务地址（默认 https://www.weiyun.com/api/v3/mcpserver）
  WEIYUN_MCP_TOKEN  MCP token
  WEIYUN_ENV_ID     环境标识
""",
    )
    parser.add_argument("file_path", help="要上传的本地文件路径")
    parser.add_argument("--token", default=None,
                        help="MCP token（也可通过 WEIYUN_MCP_TOKEN 环境变量设置）")
    parser.add_argument("--pdir_key", default=None,
                        help="上传目标目录 key（不填则使用 token 绑定的目录）")
    parser.add_argument("--mcp_url", default=None,
                        help="MCP 服务地址（默认 https://www.weiyun.com/api/v3/mcpserver）")
    parser.add_argument("--env_id", default=None,
                        help="环境标识（如 sit-0cd15bb3，也可通过 WEIYUN_ENV_ID 环境变量设置）")
    parser.add_argument("--max_rounds", type=int, default=50,
                        help="最大上传轮数（默认 50）")
    args = parser.parse_args()
    # 校验文件存在
    if not os.path.isfile(args.file_path):
        print(f"错误：文件不存在: {args.file_path}")
        sys.exit(1)
    # 解析参数（命令行 > 环境变量 > 默认值）
    mcp_url = args.mcp_url or os.environ.get("WEIYUN_MCP_URL", "https://www.weiyun.com/api/v3/mcpserver")
    mcp_token = args.token or os.environ.get("WEIYUN_MCP_TOKEN")
    env_id = args.env_id or os.environ.get("WEIYUN_ENV_ID")
    if not mcp_token:
        print("错误：必须提供 MCP token（--token 参数或 WEIYUN_MCP_TOKEN 环境变量）")
        sys.exit(1)
    # 构建 HTTP 请求头
    headers = {
        "Content-Type": "application/json",
        "WyHeader": f"mcp_token={mcp_token}",
    }
    if env_id:
        headers["Cookie"] = f"env_id={env_id}"
    # 执行上传
    print(f"=" * 60)
    print(f"微云上传: {args.file_path}")
    print(f"MCP URL:  {mcp_url}")
    print(f"Token:    {mcp_token[:8]}...{mcp_token[-4:]}")
    if args.pdir_key:
        print(f"目标目录: {args.pdir_key}")
    if env_id:
        print(f"环境标识: {env_id}")
    print(f"=" * 60)
    start_time = time.time()
    try:
        result = upload_file(
            file_path=args.file_path,
            mcp_url=mcp_url,
            headers=headers,
            pdir_key=args.pdir_key,
            max_rounds=args.max_rounds,
        )
        elapsed = time.time() - start_time
        file_size = os.path.getsize(args.file_path)
        speed = file_size / elapsed / 1024 if elapsed > 0 else 0
        print(f"\n{'=' * 60}")
        print(f"上传成功！")
        print(f"  文件名:  {result['filename']}")
        print(f"  文件ID:  {result['file_id']}")
        print(f"  文件大小: {file_size} 字节")
        print(f"  耗时:    {elapsed:.1f} 秒")
        print(f"  平均速度: {speed:.1f} KB/s")
        print(f"{'=' * 60}")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n上传失败（耗时 {elapsed:.1f} 秒）: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
