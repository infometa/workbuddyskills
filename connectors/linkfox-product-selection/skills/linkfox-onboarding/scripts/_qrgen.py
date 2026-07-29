#!/usr/bin/env python3
"""Pure-Python QR code generator (byte mode, ECC level L).

无外部依赖：仅用 stdlib（zlib、struct、io、os、time）。用于替代 onboarding
里对 qrcode + pillow 的依赖——支付付款场景只需能把 payQrcode / payUrl 打成
可扫描的黑白位图即可，功能上和 qrcode 8.x 的 byte 模式 + level L 一致。

实现遵循 ISO/IEC 18004:2015：
- 编码模式：byte only（UTF-8 十六进制的 0x40 header + length + 数据）
- 纠错等级：L（约 7% 数据损坏可恢复，足够扫码识别）
- 版本：自动选最小能装下的（v1..v40）
- 掩码：0..7 全部尝试，用官方 penalty 打分挑最小的
- 输出：
    matrix(text) -> list[list[int]]  # 0=浅，1=深
    to_ascii(matrix, invert=True) -> str
    to_png(matrix, path, scale=8, border=4) -> None
    render(text, png_path=None, ascii_invert=True) -> {"matrix", "ascii", "png_path"}
"""
from __future__ import annotations

import io
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# 静态表：来自 QR spec Annex E / D.2.1 / Table 7-9
# ---------------------------------------------------------------------------

# Byte-mode data capacity (bytes) for ECC-L, versions 1..40
_BYTE_CAPACITY_L = [
    17, 32, 53, 78, 106, 134, 154, 192, 230, 271,
    321, 367, 425, 458, 520, 586, 644, 718, 792, 858,
    929, 1003, 1091, 1171, 1273, 1367, 1465, 1528, 1628, 1732,
    1840, 1952, 2068, 2188, 2303, 2431, 2563, 2699, 2809, 2953,
]

# EC codewords per block, ECC-L, v1..v40（QR spec Table 9-1）
_EC_L_CODEWORDS = [
    7, 10, 15, 20, 26, 18, 20, 24, 30, 18,
    20, 24, 26, 30, 22, 24, 28, 30, 28, 28,
    28, 28, 30, 30, 26, 28, 30, 30, 30, 30,
    30, 30, 30, 30, 30, 30, 30, 30, 30, 30,
]

# Number of EC blocks, ECC-L, v1..v40
_EC_L_NUM_BLOCKS = [
    1, 1, 1, 1, 1, 2, 2, 2, 2, 4,
    4, 4, 4, 4, 6, 6, 6, 6, 7, 8,
    8, 9, 9, 10, 12, 12, 12, 13, 14, 15,
    16, 17, 18, 19, 19, 20, 21, 22, 24, 25,
]

# Total codewords by version (Annex A Table 1 total data + EC)
_TOTAL_CODEWORDS = [
    26, 44, 70, 100, 134, 172, 196, 242, 292, 346,
    404, 466, 532, 581, 655, 733, 815, 901, 991, 1085,
    1156, 1258, 1364, 1474, 1588, 1706, 1828, 1921, 2051, 2185,
    2323, 2465, 2611, 2761, 2876, 3034, 3196, 3362, 3532, 3706,
]

# Alignment pattern centers by version (v1 has none)
_ALIGN_PATTERN_POS = [
    None,
    [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34],
    [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50], [6, 30, 54], [6, 32, 58], [6, 34, 62],
    [6, 26, 46, 66], [6, 26, 48, 70], [6, 26, 50, 74], [6, 30, 54, 78], [6, 30, 56, 82], [6, 30, 58, 86], [6, 34, 62, 90],
    [6, 28, 50, 72, 94], [6, 26, 50, 74, 98], [6, 30, 54, 78, 102], [6, 28, 54, 80, 106], [6, 32, 58, 84, 110], [6, 30, 58, 86, 114], [6, 34, 62, 90, 118],
    [6, 26, 50, 74, 98, 122], [6, 30, 54, 78, 102, 126], [6, 26, 52, 78, 104, 130], [6, 30, 56, 82, 108, 134], [6, 34, 60, 86, 112, 138], [6, 30, 58, 86, 114, 142], [6, 34, 62, 90, 118, 146],
    [6, 30, 54, 78, 102, 126, 150], [6, 24, 50, 76, 102, 128, 154], [6, 28, 54, 80, 106, 132, 158], [6, 32, 58, 84, 110, 136, 162], [6, 26, 54, 82, 110, 138, 166], [6, 30, 58, 86, 114, 142, 170],
]

# Version info bits (v>=7). Precomputed 18-bit sequences.
_VERSION_INFO_BITS = {
    7: 0x07C94, 8: 0x085BC, 9: 0x09A99, 10: 0x0A4D3, 11: 0x0BBF6, 12: 0x0C762, 13: 0x0D847,
    14: 0x0E60D, 15: 0x0F928, 16: 0x10B78, 17: 0x1145D, 18: 0x12A17, 19: 0x13532, 20: 0x149A6,
    21: 0x15683, 22: 0x168C9, 23: 0x177EC, 24: 0x18EC4, 25: 0x191E1, 26: 0x1AFAB, 27: 0x1B08E,
    28: 0x1CC1A, 29: 0x1D33F, 30: 0x1ED75, 31: 0x1F250, 32: 0x209D5, 33: 0x216F0, 34: 0x228BA,
    35: 0x2379F, 36: 0x24B0B, 37: 0x2542E, 38: 0x26A64, 39: 0x27541, 40: 0x28C69,
}

# Format info bits (ECC L, mask 0..7) — 15 bits including BCH
_FORMAT_INFO_L = [
    0x77C4, 0x72F3, 0x7DAA, 0x789D, 0x662F, 0x6318, 0x6C41, 0x6976,
]


# ---------------------------------------------------------------------------
# Reed-Solomon over GF(256)
# ---------------------------------------------------------------------------
_GF256_EXP = [0] * 512
_GF256_LOG = [0] * 256


def _init_gf():
    x = 1
    for i in range(255):
        _GF256_EXP[i] = x
        _GF256_LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D  # QR primitive polynomial
    for i in range(255, 512):
        _GF256_EXP[i] = _GF256_EXP[i - 255]


_init_gf()


def _gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _GF256_EXP[_GF256_LOG[a] + _GF256_LOG[b]]


def _rs_generator_poly(nsym: int) -> list[int]:
    g = [1]
    for i in range(nsym):
        g = _poly_mul(g, [1, _GF256_EXP[i]])
    return g


def _poly_mul(p: list[int], q: list[int]) -> list[int]:
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a == 0:
            continue
        for j, b in enumerate(q):
            r[i + j] ^= _gf_mul(a, b)
    return r


def _rs_encode(data: list[int], nsym: int) -> list[int]:
    gen = _rs_generator_poly(nsym)
    msg = data + [0] * nsym
    for i in range(len(data)):
        coef = msg[i]
        if coef == 0:
            continue
        for j in range(len(gen)):
            msg[i + j] ^= _gf_mul(gen[j], coef)
    return msg[len(data):]


# ---------------------------------------------------------------------------
# Bit stream + version selection
# ---------------------------------------------------------------------------

class _BitBuf:
    __slots__ = ("bits",)

    def __init__(self):
        self.bits: list[int] = []

    def put(self, val: int, n: int):
        for i in range(n - 1, -1, -1):
            self.bits.append((val >> i) & 1)

    def __len__(self):
        return len(self.bits)

    def to_bytes(self) -> list[int]:
        out = []
        for i in range(0, len(self.bits), 8):
            b = 0
            for j in range(8):
                if i + j < len(self.bits):
                    b = (b << 1) | self.bits[i + j]
                else:
                    b <<= 1
            out.append(b)
        return out


def _choose_version(byte_len: int) -> int:
    for v, cap in enumerate(_BYTE_CAPACITY_L, start=1):
        if byte_len <= cap:
            return v
    raise ValueError(f"数据太长（{byte_len} 字节），超出 QR v40 ECC-L 容量")


def _encode_byte_stream(data: bytes, version: int) -> list[int]:
    # Mode indicator (byte) = 0100
    bb = _BitBuf()
    bb.put(0b0100, 4)
    # Character count indicator: 8 bits (v1-9) / 16 bits (v10-40)
    cc_bits = 8 if version <= 9 else 16
    bb.put(len(data), cc_bits)
    for b in data:
        bb.put(b, 8)
    # Terminator (up to 4 zero bits, but not exceeding capacity)
    total_data_codewords = _data_codewords_count(version)
    total_bits = total_data_codewords * 8
    term = min(4, total_bits - len(bb))
    bb.put(0, term)
    # Pad to byte boundary
    while len(bb) % 8 != 0:
        bb.put(0, 1)
    bytes_out = bb.to_bytes()
    # Fill with pad bytes 0xEC / 0x11 alternating
    pad_bytes = [0xEC, 0x11]
    i = 0
    while len(bytes_out) < total_data_codewords:
        bytes_out.append(pad_bytes[i % 2])
        i += 1
    return bytes_out


def _data_codewords_count(version: int) -> int:
    return _TOTAL_CODEWORDS[version - 1] - _EC_L_NUM_BLOCKS[version - 1] * _EC_L_CODEWORDS[version - 1]


def _build_codewords(data_bytes: list[int], version: int) -> list[int]:
    """把 data codewords 按 QR spec 分组 + 交错，加上 EC codewords，返回最终位流字节数组。"""
    num_blocks = _EC_L_NUM_BLOCKS[version - 1]
    ec_per_block = _EC_L_CODEWORDS[version - 1]
    total_data = len(data_bytes)
    # v40 ECC-L 各 block 数据量相同（无 short/long 分组），简化：均分 + 余数放到尾部块
    short_block_data = total_data // num_blocks
    long_block_count = total_data % num_blocks
    blocks_data: list[list[int]] = []
    blocks_ec: list[list[int]] = []
    idx = 0
    for b in range(num_blocks):
        sz = short_block_data + (1 if b >= num_blocks - long_block_count else 0)
        blk = data_bytes[idx: idx + sz]
        idx += sz
        blocks_data.append(blk)
        blocks_ec.append(_rs_encode(blk, ec_per_block))
    # Interleave data
    max_data = max(len(b) for b in blocks_data)
    result: list[int] = []
    for i in range(max_data):
        for blk in blocks_data:
            if i < len(blk):
                result.append(blk[i])
    # Interleave EC
    for i in range(ec_per_block):
        for blk in blocks_ec:
            result.append(blk[i])
    return result


# ---------------------------------------------------------------------------
# Matrix construction
# ---------------------------------------------------------------------------

def _size_for_version(v: int) -> int:
    return 17 + 4 * v


def _new_matrix(size: int) -> tuple[list[list[int]], list[list[bool]]]:
    matrix = [[0] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]
    return matrix, reserved


def _place_finder(matrix, reserved, r0: int, c0: int):
    size = len(matrix)
    for dr in range(-1, 8):
        for dc in range(-1, 8):
            r, c = r0 + dr, c0 + dc
            if not (0 <= r < size and 0 <= c < size):
                continue
            if dr in (-1, 7) or dc in (-1, 7):
                pass  # separator: leave 0
            elif dr in (0, 6) or dc in (0, 6):
                matrix[r][c] = 1
            elif 2 <= dr <= 4 and 2 <= dc <= 4:
                matrix[r][c] = 1
            reserved[r][c] = True


def _place_alignment(matrix, reserved, version: int):
    positions = _ALIGN_PATTERN_POS[version]
    if not positions:
        return
    n = len(positions)
    for i in range(n):
        for j in range(n):
            r, c = positions[i], positions[j]
            # Skip if overlaps finder
            if reserved[r][c]:
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr, cc = r + dr, c + dc
                    if abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0):
                        matrix[rr][cc] = 1
                    else:
                        matrix[rr][cc] = 0
                    reserved[rr][cc] = True


def _place_timing(matrix, reserved, size: int):
    for i in range(8, size - 8):
        matrix[6][i] = 1 if i % 2 == 0 else 0
        matrix[i][6] = 1 if i % 2 == 0 else 0
        reserved[6][i] = True
        reserved[i][6] = True


def _reserve_format(reserved, size: int):
    # Format info reserved bits: around finder patterns
    for i in range(9):
        if i != 6:
            reserved[i][8] = True
            reserved[8][i] = True
    for i in range(8):
        reserved[size - 1 - i][8] = True
        reserved[8][size - 1 - i] = True
    matrix_dark_module_row = size - 8  # dark module always 1 at (size-8, 8)
    reserved[matrix_dark_module_row][8] = True


def _reserve_version(reserved, size: int, version: int):
    if version < 7:
        return
    for i in range(6):
        for j in range(3):
            reserved[i][size - 11 + j] = True
            reserved[size - 11 + j][i] = True


def _place_version_info(matrix, size: int, version: int):
    if version < 7:
        return
    bits = _VERSION_INFO_BITS[version]
    for i in range(18):
        bit = (bits >> i) & 1
        a = i // 3
        b = i % 3
        matrix[a][size - 11 + b] = bit
        matrix[size - 11 + b][a] = bit


def _place_data(matrix, reserved, bitstream: list[int]):
    size = len(matrix)
    bit_idx = 0
    total = len(bitstream)
    # Column pair from right, skip col 6 (vertical timing)
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
            continue
        for step in range(size):
            row = size - 1 - step if upward else step
            for dc in (0, 1):
                c = col - dc
                if reserved[row][c]:
                    continue
                if bit_idx < total:
                    matrix[row][c] = bitstream[bit_idx]
                    bit_idx += 1
                else:
                    matrix[row][c] = 0
        col -= 2
        upward = not upward


def _bytes_to_bits(data: list[int]) -> list[int]:
    out = []
    for b in data:
        for i in range(7, -1, -1):
            out.append((b >> i) & 1)
    return out


# ---------------------------------------------------------------------------
# Masking
# ---------------------------------------------------------------------------

def _mask_pattern(mask: int, r: int, c: int) -> bool:
    if mask == 0:
        return (r + c) % 2 == 0
    if mask == 1:
        return r % 2 == 0
    if mask == 2:
        return c % 3 == 0
    if mask == 3:
        return (r + c) % 3 == 0
    if mask == 4:
        return ((r // 2) + (c // 3)) % 2 == 0
    if mask == 5:
        return ((r * c) % 2) + ((r * c) % 3) == 0
    if mask == 6:
        return (((r * c) % 2) + ((r * c) % 3)) % 2 == 0
    return (((r + c) % 2) + ((r * c) % 3)) % 2 == 0


def _apply_mask(matrix, reserved, mask: int):
    size = len(matrix)
    for r in range(size):
        for c in range(size):
            if reserved[r][c]:
                continue
            if _mask_pattern(mask, r, c):
                matrix[r][c] ^= 1


def _place_format(matrix, mask: int):
    size = len(matrix)
    bits = _FORMAT_INFO_L[mask]
    # 15 bits placed twice for redundancy
    # First copy: around top-left finder
    for i in range(6):
        matrix[i][8] = (bits >> i) & 1
    matrix[7][8] = (bits >> 6) & 1
    matrix[8][8] = (bits >> 7) & 1
    matrix[8][7] = (bits >> 8) & 1
    for i in range(9, 15):
        matrix[8][14 - i] = (bits >> i) & 1
    # Second copy: split between top-right and bottom-left
    for i in range(8):
        matrix[8][size - 1 - i] = (bits >> i) & 1
    for i in range(7):
        matrix[size - 7 + i][8] = (bits >> (8 + i)) & 1
    # Dark module (always 1)
    matrix[size - 8][8] = 1


def _penalty(matrix) -> int:
    """QR spec 4 项 penalty 打分（越低越好）。"""
    size = len(matrix)
    p = 0
    # Rule 1: 同色连续 5 个及以上
    for r in range(size):
        run = 1
        for c in range(1, size):
            if matrix[r][c] == matrix[r][c - 1]:
                run += 1
                if run == 5:
                    p += 3
                elif run > 5:
                    p += 1
            else:
                run = 1
    for c in range(size):
        run = 1
        for r in range(1, size):
            if matrix[r][c] == matrix[r - 1][c]:
                run += 1
                if run == 5:
                    p += 3
                elif run > 5:
                    p += 1
            else:
                run = 1
    # Rule 2: 2x2 同色块
    for r in range(size - 1):
        for c in range(size - 1):
            v = matrix[r][c]
            if v == matrix[r][c + 1] == matrix[r + 1][c] == matrix[r + 1][c + 1]:
                p += 3
    # Rule 3: 1:1:3:1:1 找型模式（行/列）
    finder_a = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    finder_b = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
    for r in range(size):
        for c in range(size - 10):
            row = [matrix[r][c + k] for k in range(11)]
            if row == finder_a or row == finder_b:
                p += 40
    for c in range(size):
        for r in range(size - 10):
            col = [matrix[r + k][c] for k in range(11)]
            if col == finder_a or col == finder_b:
                p += 40
    # Rule 4: 深浅色比例偏离 50%
    dark = sum(sum(row) for row in matrix)
    ratio = dark * 100 // (size * size)
    p += 10 * (abs(ratio - 50) // 5)
    return p


# ---------------------------------------------------------------------------
# Top-level API
# ---------------------------------------------------------------------------

def make_qr(text: str) -> list[list[int]]:
    """把 text 编码成 QR 矩阵（byte mode, ECC-L, auto version, best mask）。

    Returns:
        list[list[int]]: 0=浅，1=深；边长 = 17 + 4*version（不含 quiet zone）
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    data_bytes = text.encode("utf-8")
    version = _choose_version(len(data_bytes))
    padded = _encode_byte_stream(data_bytes, version)
    codewords = _build_codewords(padded, version)
    remainder_bits = _REMAINDER_BITS[version - 1]
    bitstream = _bytes_to_bits(codewords) + [0] * remainder_bits

    size = _size_for_version(version)
    matrix, reserved = _new_matrix(size)
    _place_finder(matrix, reserved, 0, 0)
    _place_finder(matrix, reserved, 0, size - 7)
    _place_finder(matrix, reserved, size - 7, 0)
    _place_alignment(matrix, reserved, version)
    _place_timing(matrix, reserved, size)
    _reserve_format(reserved, size)
    _reserve_version(reserved, size, version)
    _place_version_info(matrix, size, version)
    _place_data(matrix, reserved, bitstream)

    # 试所有 8 个 mask，取 penalty 最小的
    best_mask = 0
    best_matrix = None
    best_penalty = None
    for mask in range(8):
        # deep copy
        m = [row[:] for row in matrix]
        _apply_mask(m, reserved, mask)
        _place_format(m, mask)
        pen = _penalty(m)
        if best_penalty is None or pen < best_penalty:
            best_penalty = pen
            best_mask = mask
            best_matrix = m
    return best_matrix


# Remainder bits per version (from spec Table 1)
_REMAINDER_BITS = [
    0, 7, 7, 7, 7, 7, 0, 0, 0, 0,
    0, 0, 0, 3, 3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4, 4, 3, 3, 3,
    3, 3, 3, 3, 0, 0, 0, 0, 0, 0,
]


def to_ascii(matrix: list[list[int]], invert: bool = True, border: int = 2) -> str:
    """把矩阵渲染为 ASCII/Unicode 二维码（半高块字符 ▀，一行渲染两行像素）。

    invert=True 时用「白背景 + 深色前景」（terminal light-on-dark 主题下更清晰）；
    invert=False 反过来。border 是 quiet zone 单元数（QR 规范建议至少 4，
    ASCII 展示 2 单元就够扫）。
    """
    size = len(matrix)
    # 加 quiet zone
    padded = [[0] * (size + 2 * border) for _ in range(size + 2 * border)]
    for r in range(size):
        for c in range(size):
            padded[r + border][c + border] = matrix[r][c]
    full = size + 2 * border
    fg, bg = ("██", "  ")
    if invert:
        fg, bg = bg, fg
    out = io.StringIO()
    # 用 ▀ 半高块可以 2 行像素合 1 行终端，但 monospace 字体下 ▀ 宽度不稳；
    # 直接用「██」（两字符宽 = 一像素的等宽近似），可读性最好。
    for r in range(full):
        for c in range(full):
            out.write(fg if padded[r][c] else bg)
        out.write("\n")
    return out.getvalue()


def _png_crc32(chunk_type: bytes, data: bytes) -> int:
    return zlib.crc32(chunk_type + data) & 0xFFFFFFFF


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + chunk_type + data
            + struct.pack(">I", _png_crc32(chunk_type, data)))


def to_png(matrix: list[list[int]], path: str, scale: int = 8, border: int = 4) -> str:
    """把矩阵写成 PNG 文件（1-bit indexed 灰度调色板，stdlib zlib 压缩）。

    scale: 单元像素边长（默认 8 → 二维码模块变成 8x8 像素块，够清晰）
    border: quiet zone 单元数（QR 规范 ≥4）
    Returns:
        path
    """
    size = len(matrix)
    total = size + 2 * border  # 单元数（QR 矩阵 + quiet zone）
    px = total * scale         # 像素数

    # 生成扫描线（1-bit indexed，每行开头 1 字节 filter type=0，之后每 8 像素 = 1 字节）
    # 单元 → 像素展开：先按像素扫描线组装 1 位/像素的字节串
    row_bytes = (px + 7) // 8
    raster = bytearray()
    for py in range(px):
        raster.append(0)  # filter: None
        row_buf = bytearray(row_bytes)
        cy = py // scale
        matrix_row_r = cy - border
        for cx in range(total):
            matrix_col_c = cx - border
            if 0 <= matrix_row_r < size and 0 <= matrix_col_c < size:
                dark = matrix[matrix_row_r][matrix_col_c]
            else:
                dark = 0
            # dark=1 → palette index 1 (黑) ；dark=0 → palette index 0 (白)
            if dark:
                for k in range(scale):
                    x = cx * scale + k
                    if x >= px:
                        break
                    row_buf[x >> 3] |= 0x80 >> (x & 7)
        raster.extend(row_buf)

    ihdr = struct.pack(">IIBBBBB", px, px, 1, 3, 0, 0, 0)  # width,height,bitdepth=1,colortype=3,rest=0
    plte = b"\xff\xff\xff\x00\x00\x00"  # palette: white, black
    trns = b"\xff\xff"  # dummy; skip
    idat = zlib.compress(bytes(raster), 9)

    png = b"\x89PNG\r\n\x1a\n"
    png += _png_chunk(b"IHDR", ihdr)
    png += _png_chunk(b"PLTE", plte)
    png += _png_chunk(b"IDAT", idat)
    png += _png_chunk(b"IEND", b"")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return path


def render(text: str, png_path: str | None = None, ascii_invert: bool = True) -> dict:
    """一步到位：编码 + ASCII + 可选 PNG。

    Returns:
        {"matrix": [[0/1]...], "ascii": "...", "png_path": path or None,
         "version": int, "mask": int}
    """
    matrix = make_qr(text)
    ascii_out = to_ascii(matrix, invert=ascii_invert)
    saved = None
    if png_path:
        saved = to_png(matrix, png_path)
    return {
        "matrix": matrix,
        "ascii": ascii_out,
        "png_path": saved,
        "version": (len(matrix) - 17) // 4,
    }


if __name__ == "__main__":
    import sys
    txt = sys.argv[1] if len(sys.argv) > 1 else "https://os.linkfox.com/"
    r = render(txt, png_path="/tmp/qr_test.png")
    print(r["ascii"])
    print(f"version={r['version']}, png={r['png_path']}")
