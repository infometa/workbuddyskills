#!/usr/bin/env python3
"""
微云上传参数生成脚本 — 生成 block_sha_list、file_sha、check_sha、check_data 等上传参数。

与微云 FTN 预上传请求中的分块信息一致。

算法说明：
  1. 用一个共享的 SHA1 对象流式（streaming）处理整个文件
  2. 对每个非最后 block，通过 get_state() 获取 SHA1 内部中间状态（h0-h4，小端序输出）
  3. 最后一个 block 的 sha 为标准 SHA1 hexdigest（带 finalization 的完整文件 SHA1，大端序）
  4. check_sha 为最后一块数据去掉 checkBlockSize 之后的 SHA1 内部状态（小端序）
  5. check_data 为文件末尾 checkBlockSize 字节的 Base64 编码

使用方法：
  python3 gen_block_info_list.py <文件路径>

输出内容：
  - file_sha：整个文件的标准 SHA1（40 字符 hex）
  - file_md5：整个文件的 MD5（32 字符 hex）
  - check_sha：SHA1 校验中间状态（40 字符 hex）
  - check_data：文件末尾校验字节的 Base64 编码
  - block_sha_list：可直接用于 McpUploadReq.block_sha_list 的列表
  - 可直接用于 MCP 调用的预上传 JSON 片段

重要说明：
  本脚本包含纯 Python SHA1 实现，支持提取未经 finalization 的内部寄存器状态。
  这是 Python 标准库 hashlib.sha1 无法做到的，也是微云上传协议的核心需求。
"""

import _encoding_fix  # noqa: F401  Windows UTF-8 fix, must be first import

import json
import sys
import os
import base64
import struct


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


# ========== 业务逻辑 ==========

BLOCK_SIZE = 524288  # 512KB，与正确请求体中的 block_size 一致


def gen_upload_params(file_path, block_size):
    """
    生成上传所需的参数：
    block_info_list、file_sha、check_sha、check_data
    """
    file_size = os.path.getsize(file_path)
    # 计算 lastBlockSize 和 checkBlockSize
    last_block_size = file_size % block_size
    if last_block_size == 0:
        last_block_size = block_size
    check_block_size = last_block_size % 128
    if check_block_size == 0:
        check_block_size = 128
    before_block_size = file_size - last_block_size
    block_info_list = []
    sha1 = SHA1()
    with open(file_path, "rb") as f:
        # 处理除最后一块之外的所有 block
        for offset in range(0, before_block_size, block_size):
            data = f.read(block_size)
            sha1.update(data)
            block_info_list.append({
                "sha": sha1.get_state(),
                "offset": offset,
                "size": block_size,
            })
        # 读取最后一块中去掉 checkBlockSize 之后的部分
        between_data = f.read(last_block_size - check_block_size)
        sha1.update(between_data)
        check_sha = sha1.get_state()
        # 读取 checkData 部分
        check_data_bytes = f.read(check_block_size)
        sha1.update(check_data_bytes)
        file_sha = sha1.hexdigest()
        check_data = base64.b64encode(check_data_bytes).decode("utf-8")
        # 最后一个 block 的 sha 为 file_sha
        block_info_list.append({
            "sha": file_sha,
            "offset": before_block_size,
            "size": last_block_size,
        })
    return block_info_list, file_sha, check_sha, check_data


def gen_file_md5(file_path):
    """计算整个文件的 MD5"""
    import hashlib
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    block_info_list, file_sha, check_sha, check_data = gen_upload_params(file_path, BLOCK_SIZE)
    file_md5 = gen_file_md5(file_path)
    print(f"file_path: {file_path}")
    print(f"filename: {filename}")
    print(f"file_size: {file_size}")
    print(f"file_sha:  {file_sha}")
    print(f"file_md5:  {file_md5}")
    print(f"check_sha: {check_sha}")
    print(f"check_data: {check_data}")
    print(f"block_size: {BLOCK_SIZE}")
    print(f"block_count: {len(block_info_list)}")
    print()
    # 输出 block_sha_list（MCP McpUploadReq 需要的格式）
    block_sha_list = [b["sha"] for b in block_info_list]
    print("block_sha_list (for McpUploadReq.block_sha_list):")
    print(json.dumps(block_sha_list, indent=2))
    print()
    print("block_info_list (full detail):")
    print(json.dumps(block_info_list, indent=4))
    # 输出可直接用于 MCP 调用的 JSON 片段
    print()
    print("=== McpUploadReq pre-upload fields ===")
    mcp_req = {
        "filename": filename,
        "file_size": file_size,
        "file_sha": file_sha,
        "file_md5": file_md5,
        "block_sha_list": block_sha_list,
        "check_sha": check_sha,
        "check_data": check_data,
    }
    print(json.dumps(mcp_req, indent=2))


if __name__ == "__main__":
    main()
