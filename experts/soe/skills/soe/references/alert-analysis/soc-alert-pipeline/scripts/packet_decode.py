"""网络包解码库 (IPv4 / UDP / TCP / GRE / WireGuard)

复用自 scripts/decode_pkt.py 的逻辑, 拆成纯函数供 parser 调用.

设计原则:
  - 纯函数, 不抛异常到外层 (内部 try/except 兜底)
  - 返回 dict, 解析失败的字段为 None
  - 协议识别表用常量, 便于扩展
"""
from __future__ import annotations
import struct
from typing import Any


# IP 协议号 → 名称
IP_PROTO = {
    1: "icmp",
    6: "tcp",
    17: "udp",
    41: "ipv6",        # IPv6 封装
    47: "gre",
    50: "esp",         # IPsec ESP
    51: "ah",          # IPsec AH
}

# GRE 协议号 → 名称
GRE_PROTO = {
    0x0800: "ipv4",
    0x86DD: "ipv6",
    0x6558: "transparent_ethernet_bridging",
}

# WireGuard message type
WG_MSG_TYPE = {
    1: ("handshake_initiation", 148),
    2: ("handshake_response", 92),
    3: ("cookie_reply", 64),
    4: ("transport_data", -1),  # 变长
}


def _parse_ipv4(data: bytes, offset: int = 0, label: str = "outer") -> dict | None:
    """解析 IPv4 头, 返回字段 dict 或 None (解析失败)"""
    if len(data) < offset + 20:
        return None
    vihl = data[offset]
    version = (vihl >> 4) & 0x0F
    ihl = (vihl & 0x0F) * 4
    if version != 4 or ihl < 20:
        return None
    try:
        total_length = struct.unpack("!H", data[offset + 2:offset + 4])[0]
        proto = data[offset + 9]
        src = ".".join(str(b) for b in data[offset + 12:offset + 16])
        dst = ".".join(str(b) for b in data[offset + 16:offset + 20])
    except (struct.error, IndexError):
        return None
    return {
        "label": label,
        "version": version,
        "ihl": ihl,
        "total_length": total_length,
        "protocol": proto,
        "protocol_name": IP_PROTO.get(proto, f"unknown({proto})"),
        "src_ip": src,
        "dst_ip": dst,
    }


def _parse_udp(data: bytes, offset: int) -> dict | None:
    """解析 UDP 头"""
    if len(data) < offset + 8:
        return None
    try:
        sport, dport, length, cksum = struct.unpack("!HHHH", data[offset:offset + 8])
    except struct.error:
        return None
    return {
        "src_port": sport,
        "dst_port": dport,
        "length": length,
        "checksum": f"0x{cksum:04x}",
    }


def _parse_tcp(data: bytes, offset: int) -> dict | None:
    """解析 TCP 头 (仅基础字段)"""
    if len(data) < offset + 20:
        return None
    try:
        sport, dport, seq, ack, data_off_flags = struct.unpack("!HHIIH", data[offset:offset + 14])
    except struct.error:
        return None
    data_off = (data_off_flags >> 12) & 0xF
    flags = data_off_flags & 0x01FF
    return {
        "src_port": sport,
        "dst_port": dport,
        "seq": seq,
        "ack": ack,
        "data_offset": data_off,
        "flags": f"0x{flags:03x}",
    }


def _parse_gre(data: bytes, offset: int) -> dict | None:
    """解析 GRE 头 (基础 4 字节)"""
    if len(data) < offset + 4:
        return None
    try:
        flags, proto = struct.unpack("!HH", data[offset:offset + 4])
    except struct.error:
        return None
    return {
        "flags": f"0x{flags:04x}",
        "protocol": proto,
        "protocol_name": GRE_PROTO.get(proto, f"unknown(0x{proto:04x})"),
    }


def _parse_wireguard(payload: bytes) -> dict:
    """识别 WireGuard message type (基于首字节)"""
    if len(payload) < 4:
        return {"type_id": None, "type_name": "truncated", "raw_len": len(payload)}
    msg = payload[0]
    name, expected_len = WG_MSG_TYPE.get(msg, (f"unknown({msg})", -1))
    return {
        "type_id": msg,
        "type_name": name,
        "expected_len": expected_len,
        "actual_len": len(payload),
        "first_bytes_hex": payload[:16].hex() if payload else "",
    }


def _hex_to_ascii(h: str, max_len: int = 32) -> str:
    """hex 转可读 ASCII, 不可打印字符用 . 代替"""
    try:
        b = bytes.fromhex(h)
        return ''.join(chr(x) if 32 <= x < 127 else '.' for x in b[:max_len])
    except Exception:
        return ""


def decode_packet_hex(hex_str: str) -> dict[str, Any]:
    """主入口: 解析 SOC 导出 raw_log 里的 packet hex 字符串

    典型链路: [MAC 14B] → [IPv4] → [GRE 4B] → [IPv4] → [UDP/TCP] → [payload]

    Args:
        hex_str: hex 字符串 (无空格/0x 前缀)

    Returns:
        dict:
          - mac: {src, dst, eth_type}
          - outer: IPv4 dict
          - inner: IPv4 dict (如有 GRE/VPN 封装)
          - gre: GRE dict
          - transport: UDP/TCP dict
          - payload_meta: WireGuard / HTTP 识别结果
          - total_len: 字节数
    """
    if not hex_str or not isinstance(hex_str, str):
        return {"error": "empty or non-string input"}

    hex_clean = hex_str.strip().replace(" ", "").replace("0x", "").replace("\n", "")
    try:
        data = bytes.fromhex(hex_clean)
    except ValueError as e:
        return {"error": f"hex 解析失败: {e}"}

    result: dict[str, Any] = {"total_len": len(data)}

    # 1. MAC 头 (14 字节, 可选)
    offset = 0
    if len(data) >= 14:
        try:
            eth_type = struct.unpack("!H", data[12:14])[0]
            result["mac"] = {
                "dst": data[0:6].hex(":"),
                "src": data[6:12].hex(":"),
                "eth_type": f"0x{eth_type:04x}",
            }
            offset = 14
        except struct.error:
            pass

    # 2. 外层 IPv4
    outer = _parse_ipv4(data, offset, "outer")
    if not outer:
        result["error"] = "外层 IPv4 解析失败"
        return result
    result["outer"] = outer
    offset += outer["ihl"]

    # 3. GRE 封装 (protocol=47)
    if outer["protocol"] == 47:
        gre = _parse_gre(data, offset)
        if not gre:
            result["error"] = "GRE 解析失败"
            return result
        result["gre"] = gre
        offset += 4

        # 内层 IPv4 / IPv6
        if gre["protocol"] == 0x0800:
            inner = _parse_ipv4(data, offset, "inner")
            if inner:
                result["inner"] = inner
                offset += inner["ihl"]
            else:
                result["error"] = "内层 IPv4 解析失败"
                return result
        elif gre["protocol"] == 0x86DD:
            result["inner"] = {"label": "inner", "version": 6, "note": "IPv6 不展开解析"}

    # 4. 传输层 (UDP/TCP)
    target_offset = offset
    target_proto = result.get("inner", {}).get("protocol") if "inner" in result else outer["protocol"]

    if target_proto == 17:  # UDP
        udp = _parse_udp(data, target_offset)
        if udp:
            result["transport"] = {"type": "udp", **udp}
            # 5. payload 识别
            payload_off = target_offset + 8
            payload = data[payload_off:payload_off + max(0, udp["length"] - 8)]
            if payload:
                result["payload_meta"] = _identify_payload(udp, payload)
    elif target_proto == 6:  # TCP
        tcp = _parse_tcp(data, target_offset)
        if tcp:
            result["transport"] = {"type": "tcp", **tcp}
            payload_off = target_offset + tcp["data_offset"] * 4
            payload = data[payload_off:]
            if payload:
                result["payload_meta"] = _identify_payload(tcp, payload)
    else:
        result["transport"] = {"type": IP_PROTO.get(target_proto, f"unknown({target_proto})")}

    return result


def _identify_payload(transport: dict, payload: bytes) -> dict:
    """根据端口/首字节识别 payload 协议"""
    sport = transport.get("src_port", 0)
    dport = transport.get("dst_port", 0)
    meta: dict = {
        "len": len(payload),
        "ascii_preview": _hex_to_ascii(payload.hex(), 32) if payload else "",
    }

    # WireGuard 默认端口 51820, 但首字节也带 type
    if dport == 51820 or sport == 51820:
        wg = _parse_wireguard(payload)
        meta["protocol"] = "wireguard"
        meta["wireguard"] = wg
        return meta

    # HTTP 探测
    if payload[:3] in (b"GET", b"PUT", b"POS", b"DEL", b"HEA") or payload[:4] == b"HTTP":
        meta["protocol"] = "http"
        try:
            meta["http_method_or_version"] = payload[:16].decode("ascii", errors="replace")
        except Exception:
            pass
        return meta

    # TLS 探测
    if payload[:1] == b"\x16":
        meta["protocol"] = "tls"
        return meta

    # DNS 探测
    if sport == 53 or dport == 53:
        meta["protocol"] = "dns"
        return meta

    meta["protocol"] = "unknown"
    return meta


def parse_flow_stats(flow: dict) -> dict:
    """从 raw_log.ext.flow 提取标准化流统计

    Args:
        flow: dict, 形如 {"bytes_toserver": ..., "pkts_toserver": ..., ...}

    Returns:
        标准化流统计 dict
    """
    return {
        "bytes_toserver": int(flow.get("bytes_toserver", 0) or 0),
        "bytes_toclient": int(flow.get("bytes_toclient", 0) or 0),
        "pkts_toserver": int(flow.get("pkts_toserver", 0) or 0),
        "pkts_toclient": int(flow.get("pkts_toclient", 0) or 0),
        "start": flow.get("start"),
        "end": flow.get("end"),
        "age": flow.get("age"),  # 流的持续时间 (秒), 可能有
    }


# ==================== 独立测试入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: packet_decode.py <hex_str>")
        print('例:  packet_decode.py "4500003c1c46400040061c0aac100a01..."')
        sys.exit(1)
    import json as _json
    print(_json.dumps(decode_packet_hex(sys.argv[1]), ensure_ascii=False, indent=2))
