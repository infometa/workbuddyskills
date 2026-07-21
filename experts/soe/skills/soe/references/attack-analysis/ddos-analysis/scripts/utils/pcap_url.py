# $Id: pcap.py 77 2011-01-06 15:59:38Z dugsong $
# -*- coding: utf-8 -*-
"""Libpcap and Pcapng file format support."""
from __future__ import print_function
from __future__ import absolute_import

from ssl import SSLContext
import sys
import time
from decimal import Decimal
from typing import Any
import urllib.request
import ssl
import io
import struct

import dpkt
from dpkt.compat import intround
from dpkt import pcapng


# big endian magics
TCPDUMP_MAGIC = 0xa1b2c3d4
TCPDUMP_MAGIC_NANO = 0xa1b23c4d
MODPCAP_MAGIC = 0xa1b2cd34

# little endian magics
PMUDPCT_MAGIC = 0xd4c3b2a1
PMUDPCT_MAGIC_NANO = 0x4d3cb2a1
PACPDOM_MAGIC = 0x34cdb2a1

# pcapng magics
PCAPNG_MAGIC = 0x0a0d0d0a  # Section Header Block type (big endian)
PCAPNG_MAGIC_LE = 0x0a0d0d0a  # Same for LE since it's symmetric

PCAP_VERSION_MAJOR = 2
PCAP_VERSION_MINOR = 4

# All valid pcap magics (for detection)
PCAP_MAGICS = {TCPDUMP_MAGIC, TCPDUMP_MAGIC_NANO, MODPCAP_MAGIC, 
               PMUDPCT_MAGIC, PMUDPCT_MAGIC_NANO, PACPDOM_MAGIC}

# see http://www.tcpdump.org/linktypes.html for explanations
DLT_NULL = 0
DLT_EN10MB = 1
DLT_EN3MB = 2
DLT_AX25 = 3
DLT_PRONET = 4
DLT_CHAOS = 5
DLT_IEEE802 = 6
DLT_ARCNET = 7
DLT_SLIP = 8
DLT_PPP = 9
DLT_FDDI = 10
DLT_PFSYNC = 18
DLT_PPP_SERIAL = 50
DLT_PPP_ETHER = 51
DLT_ATM_RFC1483 = 100
DLT_RAW = 101
DLT_C_HDLC = 104
DLT_IEEE802_11 = 105
DLT_FRELAY = 107
DLT_LOOP = 108
DLT_LINUX_SLL = 113
DLT_LTALK = 114
DLT_PFLOG = 117
DLT_PRISM_HEADER = 119
DLT_IP_OVER_FC = 122
DLT_SUNATM = 123
DLT_IEEE802_11_RADIO = 127
DLT_ARCNET_LINUX = 129
DLT_APPLE_IP_OVER_IEEE1394 = 138
DLT_MTP2_WITH_PHDR = 139
DLT_MTP2 = 140
DLT_MTP3 = 141
DLT_SCCP = 142
DLT_DOCSIS = 143
DLT_LINUX_IRDA = 144
DLT_USER0 = 147
DLT_USER1 = 148
DLT_USER2 = 149
DLT_USER3 = 150
DLT_USER4 = 151
DLT_USER5 = 152
DLT_USER6 = 153
DLT_USER7 = 154
DLT_USER8 = 155
DLT_USER9 = 156
DLT_USER10 = 157
DLT_USER11 = 158
DLT_USER12 = 159
DLT_USER13 = 160
DLT_USER14 = 161
DLT_USER15 = 162
DLT_IEEE802_11_RADIO_AVS = 163
DLT_BACNET_MS_TP = 165
DLT_PPP_PPPD = 166
DLT_GPRS_LLC = 169
DLT_GPF_T = 170
DLT_GPF_F = 171
DLT_LINUX_LAPD = 177
DLT_BLUETOOTH_HCI_H4 = 187
DLT_USB_LINUX = 189
DLT_PPI = 192
DLT_IEEE802_15_4 = 195
DLT_SITA = 196
DLT_ERF = 197
DLT_BLUETOOTH_HCI_H4_WITH_PHDR = 201
DLT_AX25_KISS = 202
DLT_LAPD = 203
DLT_PPP_WITH_DIR = 204
DLT_C_HDLC_WITH_DIR = 205
DLT_FRELAY_WITH_DIR = 206
DLT_IPMB_LINUX = 209
DLT_IEEE802_15_4_NONASK_PHY = 215
DLT_USB_LINUX_MMAPPED = 220
DLT_FC_2 = 224
DLT_FC_2_WITH_FRAME_DELIMS = 225
DLT_IPNET = 226
DLT_CAN_SOCKETCAN = 227
DLT_IPV4 = 228
DLT_IPV6 = 229
DLT_IEEE802_15_4_NOFCS = 230
DLT_DBUS = 231
DLT_DVB_CI = 235
DLT_MUX27010 = 236
DLT_STANAG_5066_D_PDU = 237
DLT_NFLOG = 239
DLT_NETANALYZER = 240
DLT_NETANALYZER_TRANSPARENT = 241
DLT_IPOIB = 242
DLT_MPEG_2_TS = 243
DLT_NG40 = 244
DLT_NFC_LLCP = 245
DLT_INFINIBAND = 247
DLT_SCTP = 248
DLT_USBPCAP = 249
DLT_RTAC_SERIAL = 250
DLT_BLUETOOTH_LE_LL = 251
DLT_NETLINK = 253
DLT_BLUETOOTH_LINUX_MONITOR = 253
DLT_BLUETOOTH_BREDR_BB = 255
DLT_BLUETOOTH_LE_LL_WITH_PHDR = 256
DLT_PROFIBUS_DL = 257
DLT_PKTAP = 258
DLT_EPON = 259
DLT_IPMI_HPM_2 = 260
DLT_ZWAVE_R1_R2 = 261
DLT_ZWAVE_R3 = 262
DLT_WATTSTOPPER_DLM = 263
DLT_ISO_14443 = 264
DLT_LINUX_SLL2 = 276

if sys.platform.find('openbsd') != -1:
    DLT_LOOP = 12
    DLT_RAW = 14
else:
    DLT_LOOP = 108
    DLT_RAW = 12

dltoff = {DLT_NULL: 4, DLT_EN10MB: 14, DLT_IEEE802: 22, DLT_ARCNET: 6,
          DLT_SLIP: 16, DLT_PPP: 4, DLT_FDDI: 21, DLT_PFLOG: 48, DLT_PFSYNC: 4,
          DLT_LOOP: 4, DLT_LINUX_SLL: 16, DLT_LINUX_SLL2: 20}


class PktHdr(dpkt.Packet):
    """pcap packet header.

    TODO: Longer class information....

    Attributes:
        __hdr__: Header fields of pcap header.
        TODO.
    """
    __hdr__ = (
        ('tv_sec', 'I', 0),
        ('tv_usec', 'I', 0),
        ('caplen', 'I', 0),
        ('len', 'I', 0),
    )


class PktModHdr(dpkt.Packet):
    """modified pcap packet header.
    https://wiki.wireshark.org/Development/LibpcapFileFormat#modified-pcap

    TODO: Longer class information....

    Attributes:
        __hdr__: Header fields of pcap header.
        TODO.
    """
    __hdr__ = (
        ('tv_sec', 'I', 0),
        ('tv_usec', 'I', 0),
        ('caplen', 'I', 0),
        ('len', 'I', 0),
        ('ifindex', 'I', 0),
        ('protocol', 'H', 0),
        ('pkt_type', 'B', 0),
        ('pad', 'B', 0),
    )


class LEPktHdr(PktHdr):
    __byte_order__ = '<'

class LEPktModHdr(PktModHdr):
    __byte_order__ = '<'


MAGIC_TO_PKT_HDR = {
    TCPDUMP_MAGIC: PktHdr,
    TCPDUMP_MAGIC_NANO: PktHdr,
    MODPCAP_MAGIC: PktModHdr,
    PMUDPCT_MAGIC: LEPktHdr,
    PMUDPCT_MAGIC_NANO: LEPktHdr,
    PACPDOM_MAGIC: LEPktModHdr
}


class FileHdr(dpkt.Packet):
    """pcap file header.

    TODO: Longer class information....

    Attributes:
        __hdr__: Header fields of pcap file header.
        TODO.
    """
    __hdr__ = (
        ('magic', 'I', TCPDUMP_MAGIC),
        ('v_major', 'H', PCAP_VERSION_MAJOR),
        ('v_minor', 'H', PCAP_VERSION_MINOR),
        ('thiszone', 'I', 0),
        ('sigfigs', 'I', 0),
        ('snaplen', 'I', 1500),
        ('linktype', 'I', 1),
    )


class LEFileHdr(FileHdr):
    __byte_order__ = '<'


class Writer(object):
    """Simple pcap dumpfile writer.

    TODO: Longer class information....

    Attributes:
        __hdr__: Header fields of simple pcap dumpfile writer.
        TODO.
    """
    __le = sys.byteorder == 'little'

    def __init__(self, fileobj, snaplen=1500, linktype=DLT_EN10MB, nano=False):
        self.__f = fileobj
        self._precision = 9 if nano else 6
        self._precision_multiplier = 10**self._precision

        magic = TCPDUMP_MAGIC_NANO if nano else TCPDUMP_MAGIC
        if self.__le:
            fh = LEFileHdr(snaplen=snaplen, linktype=linktype, magic=magic)
            self._PktHdr = LEPktHdr()
        else:
            fh = FileHdr(snaplen=snaplen, linktype=linktype, magic=magic)
            self._PktHdr = PktHdr()

        self._pack_hdr = self._PktHdr._pack_hdr
        self.__f.write(bytes(fh))

    def writepkt(self, pkt, ts=None):
        """Write single packet and optional timestamp to file.

        Args:
            pkt: `bytes` will be called on this and written to file.
            ts (float): Timestamp in seconds. Defaults to current time.
        """
        if ts is None:
            ts = time.time()

        self.writepkt_time(bytes(pkt), ts)

    def writepkt_time(self, pkt, ts):
        """Write single packet and its timestamp to file.

        Args:
            pkt (bytes): Some `bytes` to write to the file
            ts (float): Timestamp in seconds
        """
        n = len(pkt)
        sec = int(ts)
        usec = intround(ts % 1 * self._precision_multiplier)
        ph = self._pack_hdr(sec, usec, n, n)
        self.__f.write(ph + pkt)

    def writepkts(self, pkts):
        """Write an iterable of packets to file.

        Timestamps should be in seconds.
        Packets must be of type `bytes` as they will not be cast.

        Args:
            pkts: iterable containing (ts, pkt)
        """
        fd = self.__f
        pack_hdr = self._pack_hdr
        precision_multiplier = self._precision_multiplier

        for ts, pkt in pkts:
            n = len(pkt)
            sec = int(ts)
            usec = intround(ts % 1 * precision_multiplier)
            ph = pack_hdr(sec, usec, n, n)
            fd.write(ph + pkt)

    def close(self):
        self.__f.close()


def open_pcap_source(source, verify_ssl=False):
    """
    打开PCAP文件源（支持本地文件路径或URL）
    
    Args:
        source: 文件路径或URL字符串
        verify_ssl: 是否验证SSL证书（仅URL有效）
        
    Returns:
        文件对象（response对象或真实文件对象）
    """
    if isinstance(source, str):
        # 判断是否为URL
        if source.startswith(('http://', 'https://', 'ftp://')):
            # 从URL读取，返回response对象支持流式读取
            context = None
            if not verify_ssl and source.startswith('https://'):
                context = ssl._create_unverified_context()
            
            try:
                response = urllib.request.urlopen(source, context=context)
                return response
            except Exception as e:
                raise IOError(f"无法从URL读取PCAP文件: {source}\n错误: {str(e)}")
        else:
            # 本地文件
            try:
                return open(source, 'rb')
            except Exception as e:
                raise IOError(f"无法打开本地PCAP文件: {source}\n错误: {str(e)}")
    else:
        # 假设已经是文件对象
        return source


def detect_pcap_format(source, verify_ssl=False):
    """检测 PCAP/PCAPNG 文件格式
    
    Args:
        source: 文件路径、URL 或文件对象
        verify_ssl: 是否验证 SSL 证书
        
    Returns:
        dict: {'format': 'pcap'|'pcapng'|'unknown', 'magic': int, 'details': str}
    """
    try:
        # 读取文件头（至少需要 28 字节来检测两种格式）
        if isinstance(source, str):
            if source.startswith(('http://', 'https://', 'ftp://')):
                # URL
                context = None
                if not verify_ssl and source.startswith('https://'):
                    context = ssl._create_unverified_context()
                req = urllib.request.Request(source)
                req.add_header('User-Agent', 'Mozilla/5.0')
                req.add_header('Range', 'bytes=0-27')
                with urllib.request.urlopen(req, context=context) as response:
                    header_data = response.read()
            else:
                # 本地文件
                with open(source, 'rb') as f:
                    header_data = f.read(28)
        else:
            # 文件对象
            pos = source.tell() if hasattr(source, 'tell') else 0
            header_data = source.read(28)
            if hasattr(source, 'seek'):
                source.seek(pos)
        
        if len(header_data) < 4:
            return {'format': 'unknown', 'magic': 0, 'details': '文件太小，无法检测格式'}
        
        # 读取前4字节
        first_4_bytes_le = struct.unpack('<I', header_data[:4])[0]
        first_4_bytes_be = struct.unpack('>I', header_data[:4])[0]
        
        # 检测 pcapng 格式 (Section Header Block type = 0x0a0d0d0a)
        if first_4_bytes_le == PCAPNG_MAGIC or first_4_bytes_be == PCAPNG_MAGIC:
            return {
                'format': 'pcapng',
                'magic': PCAPNG_MAGIC,
                'details': 'PCAPNG (Next Generation) 格式'
            }
        
        # 检测标准 pcap 格式
        if first_4_bytes_le in PCAP_MAGICS:
            magic_names = {
                TCPDUMP_MAGIC: 'TCPDUMP (big-endian)',
                TCPDUMP_MAGIC_NANO: 'TCPDUMP Nano (big-endian)',
                MODPCAP_MAGIC: 'Modified PCAP (big-endian)',
                PMUDPCT_MAGIC: 'TCPDUMP (little-endian)',
                PMUDPCT_MAGIC_NANO: 'TCPDUMP Nano (little-endian)',
                PACPDOM_MAGIC: 'Modified PCAP (little-endian)'
            }
            return {
                'format': 'pcap',
                'magic': first_4_bytes_le,
                'details': f'PCAP 格式 - {magic_names.get(first_4_bytes_le, "Unknown")}'
            }
        
        if first_4_bytes_be in PCAP_MAGICS:
            return {
                'format': 'pcap',
                'magic': first_4_bytes_be,
                'details': 'PCAP 格式 (big-endian)'
            }
        
        return {
            'format': 'unknown',
            'magic': first_4_bytes_le,
            'details': f'未知格式，magic: {hex(first_4_bytes_le)}'
        }
        
    except Exception as e:
        return {'format': 'error', 'magic': 0, 'details': f'检测失败: {str(e)}'}


class Reader(object):
    """Simple pypcap-compatible pcap file reader.

    TODO: Longer class information....

    Attributes:
        __hdr__: Header fields of simple pypcap-compatible pcap file reader.
        TODO.
    """
    def __init__(self, fileobj, verify_ssl=False):
        # 支持URL和本地文件路径
        if isinstance(fileobj, str):
            fileobj = open_pcap_source(fileobj, verify_ssl=verify_ssl)
        
        self.name = getattr(fileobj, 'name', '<%s>' % fileobj.__class__.__name__)
        self.__f = fileobj
        self.__bytes_read = 0  # 追踪已读取的字节数
        buf = self.__f.read(FileHdr.__hdr_len__)
        self.__bytes_read += len(buf)
        self.__fh = FileHdr(buf)

        # save magic
        self.magic = self.__fh.magic

        if self.magic in (PMUDPCT_MAGIC, PMUDPCT_MAGIC_NANO, PACPDOM_MAGIC):
            self.__fh = LEFileHdr(buf)

        if self.magic not in MAGIC_TO_PKT_HDR:
            raise ValueError('invalid tcpdump header')

        self.__ph = MAGIC_TO_PKT_HDR[self.magic]

        if self.__fh.linktype in dltoff:
            self.dloff = dltoff[self.__fh.linktype]
        else:
            self.dloff = 0
        self._divisor = Decimal('1E9') if self.magic in (TCPDUMP_MAGIC_NANO, PMUDPCT_MAGIC_NANO) else 1E6
        self.snaplen = self.__fh.snaplen
        self.filter = ''
        self.__iter = iter(self)

    @property
    def fd(self):
        return self.__f.fileno()

    def fileno(self):
        return self.fd

    def datalink(self):
        return self.__fh.linktype

    def setfilter(self, value, optimize=1):
        raise NotImplementedError

    def readpkts(self):
        return list(self)

    def getoffset(self):
        """返回当前seek位置"""
        # 尝试使用tell()，如果不支持则返回追踪的字节数
        try:
            return self.__f.tell()
        except (AttributeError, io.UnsupportedOperation):
            return self.__bytes_read

    def getmagic(self):
        return self.magic

    def seek(self, offset, whence=0):
        """设置文件位置指针，为Response对象提供seek支持"""
        try:
            # 尝试直接使用seek()
            return self.__f.seek(offset, whence)
        except (AttributeError, io.UnsupportedOperation):
            # Response不支持seek，仅支持重置到开始位置
            if offset == 0 and whence == 0:
                # 重置字节计数器
                self.__bytes_read = 0
                return 0
            else:
                raise io.UnsupportedOperation("Response对象仅支持seek(0, 0)")

    def __next__(self):
        return next(self.__iter)
    next = __next__  # Python 2 compat

    def dispatch(self, cnt, callback, *args):
        """Collect and process packets with a user callback.

        Return the number of packets processed, or 0 for a savefile.

        Arguments:

        cnt      -- number of packets to process;
                    or 0 to process all packets until EOF
        callback -- function with (timestamp, pkt, *args) prototype
        *args    -- optional arguments passed to callback on execution
        """
        processed = 0
        if cnt > 0:
            for _ in range(cnt):
                try:
                    ts, pkt = next(iter(self))
                except StopIteration:
                    break
                callback(ts, pkt, *args)
                processed += 1
        else:
            for ts, pkt in self:
                callback(ts, pkt, *args)
                processed += 1
        return processed

    def loop(self, callback, *args):
        self.dispatch(0, callback, *args)

    def __iter__(self):
        while 1:
            buf = self.__f.read(self.__ph.__hdr_len__)
            if not buf:
                break
            self.__bytes_read += len(buf)
            hdr = self.__ph(buf)
            buf = self.__f.read(hdr.caplen)
            self.__bytes_read += len(buf)
            yield (hdr.tv_sec + (hdr.tv_usec / self._divisor), buf)


class PcapData:
    """多个连续的PCAP/PCAPNG数据包组成的数据块
    
    用于表示PCAP/PCAPNG文件中的一个数据块，包含多个连续的数据包
    每个数据包由：数据包头部 + 数据组成
    支持类似文件对象的接口（read, seek, tell等）
    支持 pcap 和 pcapng 两种格式
    """
    def __init__(self, packets_data=None, url=None, start=0, size=None, verify_ssl=False):
        """
        初始化PcapData
        
        Args:
            packets_data: 包含多个数据包的二进制数据或数据包列表（可选）
            url: 从URL读取数据（可选），如果指定则从该URL读取
            start: 内容的seek位置，即开始读取的字节偏移（默认为0）
            size: 要读取的字节大小（如果为None则读取从start到文件末尾）
            verify_ssl: 是否验证SSL证书（默认False）
        """
        self.position = 0
        self._is_pcapng = False
        self._file_header_size = FileHdr.__hdr_len__
        
        magic = PMUDPCT_MAGIC
        # 根据参数优先级获取数据
        if url:
            # 从URL读取指定范围的数据
            self.data = self._read_from_url(url, start, size, verify_ssl)

            # 获取文件头来判断格式
            data_header = self._read_from_url(url, 0, max(FileHdr.__hdr_len__, 12), verify_ssl)
            if not data_header:
                raise ValueError("无法获取数据头部，数据可能不是有效的PCAP/PCAPNG文件")
            
            # 检测文件格式
            format_info = self._detect_format(data_header)
            if format_info is None:
                raise ValueError("无法识别文件格式，数据可能不是有效的PCAP/PCAPNG文件")
            
            magic = format_info.get('magic')
            self._is_pcapng = format_info.get('is_pcapng', False)
            self._file_header_size = format_info.get('header_size', FileHdr.__hdr_len__)
            
        elif packets_data is not None:
            # 使用提供的数据
            if isinstance(packets_data, list):
                # 如果是列表，则合并为字节数据
                self.data = b''.join(packets_data)
            else:
                # 如果已是字节数据
                self.data = packets_data
        else:
            raise ValueError("必须提供packets_data或url中的至少一个")
        
        # 根据格式初始化解析器
        if self._is_pcapng:
            self._init_pcapng_parser()
        else:
            self._init_pcap_parser(magic)
    
    def _detect_format(self, data):
        """检测PCAP/PCAPNG文件格式
        
        Args:
            data: 文件头部数据
            
        Returns:
            格式信息字典 {'magic': ..., 'is_pcapng': ..., 'header_size': ...} 或 None
        """
        if len(data) < 4:
            return None
        
        # 读取前4字节
        first_4_bytes = struct.unpack('<I', data[:4])[0]
        first_4_bytes_be = struct.unpack('>I', data[:4])[0]
        
        # 检测 pcapng 格式 (Section Header Block type = 0x0a0d0d0a)
        if first_4_bytes == PCAPNG_MAGIC or first_4_bytes_be == PCAPNG_MAGIC:
            return {
                'magic': PCAPNG_MAGIC,
                'is_pcapng': True,
                'header_size': 0  # pcapng 没有固定的文件头大小
            }
        
        # 检测标准 pcap 格式
        if len(data) >= FileHdr.__hdr_len__:
            # 尝试大端字节序
            try:
                fh = FileHdr(data[:FileHdr.__hdr_len__])
                if fh.magic in MAGIC_TO_PKT_HDR:
                    return {
                        'magic': fh.magic,
                        'is_pcapng': False,
                        'header_size': FileHdr.__hdr_len__
                    }
            except:
                pass
            
            # 尝试小端字节序
            try:
                fh = LEFileHdr(data[:FileHdr.__hdr_len__])
                if fh.magic in MAGIC_TO_PKT_HDR:
                    return {
                        'magic': fh.magic,
                        'is_pcapng': False,
                        'header_size': FileHdr.__hdr_len__
                    }
            except:
                pass
        
        return None
    
    def _init_pcap_parser(self, magic):
        """初始化 pcap 格式解析器"""
        # 参考Reader类的处理方式，根据magic判断字节序并获取对应的数据包头部类
        if magic in (PMUDPCT_MAGIC, PMUDPCT_MAGIC_NANO, PACPDOM_MAGIC):
            # 小端字节序
            self.__ph = MAGIC_TO_PKT_HDR[magic]
        else:
            # 大端字节序
            if magic not in MAGIC_TO_PKT_HDR:
                raise ValueError(f'invalid magic: {hex(magic)}')
            self.__ph = MAGIC_TO_PKT_HDR[magic]
        
        self._divisor = Decimal('1E9') if magic in (TCPDUMP_MAGIC_NANO, PMUDPCT_MAGIC_NANO) else 1E6
    
    def _init_pcapng_parser(self):
        """初始化 pcapng 格式解析器"""
        # pcapng 使用不同的解析方式，通过 dpkt.pcapng 模块处理
        self._pcapng_le = True  # 默认小端，实际在解析时确定
        self._ts_resol = 1e-6   # 默认时间戳分辨率
        self._divisor = Decimal('1E6')
    
    def _read_from_url(self, url, start, size, verify_ssl=False):
        """从URL读取指定范围的数据
        
        Args:
            url: 文件URL
            start: 开始位置（字节偏移）
            size: 要读取的字节大小
            verify_ssl: 是否验证SSL证书（默认False，即跳过验证）
            
        Returns:
            读取的数据字节
        """
        context = None
        if url.startswith('https://'):
            # HTTPS URL，默认跳过SSL证书验证
            context = ssl._create_unverified_context()
        
        try:
            # 构造Range请求头用于范围读取
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            if size is None:
                # 读取从start到文件末尾
                req.add_header('Range', f'bytes={start}-')
            else:
                # 读取指定大小的数据
                end = start + size - 1
                req.add_header('Range', f'bytes={start}-{end}')
            
            with urllib.request.urlopen(req, context=context) as response:
                data = response.read()
            
            return data
        except Exception as e:
            raise IOError(f"无法从URL读取数据: {url}\n错误: {str(e)}")

    
    def read(self, size=-1):
        """读取数据"""
        if size is None or size < 0:
            result = self.data[self.position:]
            self.position = len(self.data)
        else:
            result = self.data[self.position:self.position + size]
            self.position += len(result)
        return result
    
    def seek(self, offset, whence=0):
        """设置读取位置"""
        if whence == 0:  # 相对于文件开始
            self.position = offset
        elif whence == 1:  # 相对于当前位置
            self.position += offset
        elif whence == 2:  # 相对于文件结尾
            self.position = len(self.data) + offset
        return self.position
    
    def tell(self):
        """返回当前位置"""
        return self.position
    
    def __len__(self):
        """返回数据块大小"""
        return len(self.data)

    def __iter__(self):
        """返回迭代器对象（返回self）"""
        self.position = 0
        return self
    
    def __next__(self):
        """获取下一个数据包（实现迭代器协议）
        
        返回: (timestamp, packet_data) 元组
              - timestamp: 数据包时间戳
              - packet_data: 数据包数据
        """
        if self._is_pcapng:
            return self._next_pcapng()
        else:
            return self._next_pcap()
    
    def _next_pcap(self):
        """获取下一个 pcap 格式数据包"""
        hdr_len = self.__ph.__hdr_len__
        
        # 检查是否有足够的字节来读取数据包头部
        if self.position + hdr_len > len(self.data):
            raise StopIteration
        
        # 读取数据包头部
        buf = self.data[self.position:self.position + hdr_len]
        self.position += len(buf)
        
        # 解析数据包头部
        hdr = self.__ph(buf)
        
        # 检查是否有足够的字节来读取数据包数据
        if self.position + hdr.caplen > len(self.data):
            raise StopIteration
        
        # 读取数据包数据
        pkt_data = self.data[self.position:self.position + hdr.caplen]
        self.position += len(pkt_data)
        
        # 计算时间戳并返回
        timestamp = hdr.tv_sec + (hdr.tv_usec / self._divisor)
        return (timestamp, pkt_data)
    
    def _next_pcapng(self):
        """获取下一个 pcapng 格式数据包
        
        pcapng 格式的块结构:
        - Block Type (4 bytes)
        - Block Total Length (4 bytes)
        - Block Body (variable)
        - Block Total Length (4 bytes, repeated)
        """
        while True:
            # 检查是否有足够的字节来读取块头部 (8 bytes minimum)
            if self.position + 8 > len(self.data):
                raise StopIteration
            
            # 读取块类型和块长度
            block_type = struct.unpack('<I', self.data[self.position:self.position + 4])[0]
            block_length = struct.unpack('<I', self.data[self.position + 4:self.position + 8])[0]
            
            # 检查块长度是否合理
            if block_length < 12 or self.position + block_length > len(self.data):
                raise StopIteration
            
            # 读取整个块数据
            block_data = self.data[self.position:self.position + block_length]
            self.position += block_length
            
            # 处理不同类型的块
            # Section Header Block (SHB) = 0x0a0d0d0a
            if block_type == PCAPNG_MAGIC:
                # 检测字节序
                if len(block_data) >= 16:
                    byte_order_magic = struct.unpack('<I', block_data[8:12])[0]
                    self._pcapng_le = (byte_order_magic == pcapng.BYTE_ORDER_MAGIC)
                continue
            
            # Interface Description Block (IDB) = 0x00000001
            elif block_type == pcapng.PCAPNG_BT_IDB:
                # 可以从IDB中获取接口信息，这里简单跳过
                continue
            
            # Enhanced Packet Block (EPB) = 0x00000006
            elif block_type == pcapng.PCAPNG_BT_EPB:
                return self._parse_enhanced_packet_block(block_data)
            
            # Simple Packet Block (SPB) = 0x00000003
            elif block_type == pcapng.PCAPNG_BT_SPB:
                return self._parse_simple_packet_block(block_data)
            
            # Packet Block (obsolete) = 0x00000002
            elif block_type == pcapng.PCAPNG_BT_PB:
                return self._parse_packet_block(block_data)
            
            # 其他块类型，跳过
            else:
                continue
    
    def _parse_enhanced_packet_block(self, block_data):
        """解析 Enhanced Packet Block (EPB)
        
        EPB 结构:
        - Block Type (4 bytes) = 0x00000006
        - Block Total Length (4 bytes)
        - Interface ID (4 bytes)
        - Timestamp (High) (4 bytes)
        - Timestamp (Low) (4 bytes)
        - Captured Packet Length (4 bytes)
        - Original Packet Length (4 bytes)
        - Packet Data (variable, padded to 4 bytes)
        - Options (variable)
        - Block Total Length (4 bytes)
        """
        if len(block_data) < 32:
            raise StopIteration
        
        # 解析字段
        fmt = '<I' if self._pcapng_le else '>I'
        interface_id = struct.unpack(fmt, block_data[8:12])[0]
        ts_high = struct.unpack(fmt, block_data[12:16])[0]
        ts_low = struct.unpack(fmt, block_data[16:20])[0]
        caplen = struct.unpack(fmt, block_data[20:24])[0]
        orig_len = struct.unpack(fmt, block_data[24:28])[0]
        
        # 计算时间戳 (默认单位是微秒)
        timestamp = ((ts_high << 32) | ts_low) * self._ts_resol
        
        # 提取数据包数据
        pkt_data = block_data[28:28 + caplen]
        
        return (timestamp, pkt_data)
    
    def _parse_simple_packet_block(self, block_data):
        """解析 Simple Packet Block (SPB)
        
        SPB 结构:
        - Block Type (4 bytes) = 0x00000003
        - Block Total Length (4 bytes)
        - Original Packet Length (4 bytes)
        - Packet Data (variable, padded to 4 bytes)
        - Block Total Length (4 bytes)
        """
        if len(block_data) < 16:
            raise StopIteration
        
        fmt = '<I' if self._pcapng_le else '>I'
        block_length = struct.unpack(fmt, block_data[4:8])[0]
        orig_len = struct.unpack(fmt, block_data[8:12])[0]
        
        # SPB 没有时间戳，使用 0
        timestamp = 0.0
        
        # 计算数据包长度：block_length - 16 (header + footer) - padding
        caplen = block_length - 16
        pkt_data = block_data[12:12 + caplen]
        
        return (timestamp, pkt_data)
    
    def _parse_packet_block(self, block_data):
        """解析 Packet Block (PB, obsolete)
        
        PB 结构:
        - Block Type (4 bytes) = 0x00000002
        - Block Total Length (4 bytes)
        - Interface ID (2 bytes)
        - Drops Count (2 bytes)
        - Timestamp (High) (4 bytes)
        - Timestamp (Low) (4 bytes)
        - Captured Packet Length (4 bytes)
        - Original Packet Length (4 bytes)
        - Packet Data (variable, padded to 4 bytes)
        - Options (variable)
        - Block Total Length (4 bytes)
        """
        if len(block_data) < 32:
            raise StopIteration
        
        fmt = '<I' if self._pcapng_le else '>I'
        fmt_h = '<H' if self._pcapng_le else '>H'
        
        interface_id = struct.unpack(fmt_h, block_data[8:10])[0]
        drops_count = struct.unpack(fmt_h, block_data[10:12])[0]
        ts_high = struct.unpack(fmt, block_data[12:16])[0]
        ts_low = struct.unpack(fmt, block_data[16:20])[0]
        caplen = struct.unpack(fmt, block_data[20:24])[0]
        orig_len = struct.unpack(fmt, block_data[24:28])[0]
        
        # 计算时间戳
        timestamp = ((ts_high << 32) | ts_low) * self._ts_resol
        
        # 提取数据包数据
        pkt_data = block_data[28:28 + caplen]
        
        return (timestamp, pkt_data)
    
    next = __next__  # Python 2 compat


class PcapngSliceIterator:
    """pcapng 格式的切片迭代器
    
    用于按包索引跳过和读取指定数量的包，而不是按字节偏移。
    适用于 pcapng 格式，因为 pcapng 不支持随机字节访问。
    """
    def __init__(self, reader_iter, skip_count=0, read_count=None):
        """初始化 pcapng 切片迭代器
        
        Args:
            reader_iter: pcapng.Reader 迭代器（已经包含所有数据）
            skip_count: 要跳过的包数量（从0开始）
            read_count: 要读取的包数量（None表示读取到末尾）
        """
        self._reader = reader_iter
        self._skip_count = skip_count
        self._read_count = read_count
        self._skipped = 0
        self._read = 0
        self._exhausted = False
        
        # 跳过指定数量的包
        self._do_skip()
    
    def _do_skip(self):
        """跳过指定数量的包"""
        while self._skipped < self._skip_count:
            try:
                next(self._reader)
                self._skipped += 1
            except StopIteration:
                self._exhausted = True
                break
    
    def __iter__(self):
        return self
    
    def __next__(self):
        """获取下一个数据包"""
        if self._exhausted:
            raise StopIteration
        
        # 检查是否已读取足够的包
        if self._read_count is not None and self._read >= self._read_count:
            raise StopIteration
        
        try:
            packet = next(self._reader)
            self._read += 1
            return packet
        except StopIteration:
            self._exhausted = True
            raise
    
    next = __next__  # Python 2 compat


class UniversalReader(object):
    """
    Universal pcap reader for the libpcap and pcapng file formats
    支持本地文件、网络URL、BytesIO对象
    """
    def __new__(cls, fileobj, verify_ssl=False):
        from io import BytesIO
        
        # 支持URL和本地文件路径
        if isinstance(fileobj, str):
            # 先检测格式
            format_info = detect_pcap_format(fileobj, verify_ssl=verify_ssl)
            
            if format_info['format'] == 'pcapng':
                # pcapng 格式：需要将整个文件读入内存（因为 HTTP response 不支持 seek）
                source = open_pcap_source(fileobj, verify_ssl=verify_ssl)
                try:
                    data = source.read()
                    fileobj = BytesIO(data)
                finally:
                    if hasattr(source, 'close'):
                        try:
                            source.close()
                        except:
                            pass
                
                # 使用 dpkt.pcapng 模块读取
                try:
                    reader = pcapng.Reader(fileobj)
                    return reader
                except ValueError as e:
                    raise ValueError(f'无法解析 pcapng 文件: {e}')
            else:
                # pcap 格式：使用原来的方式
                fileobj = open_pcap_source(fileobj, verify_ssl=verify_ssl)
        
        # 对于非 URL 的情况，尝试先检测格式
        try:
            reader = Reader(fileobj, verify_ssl=verify_ssl)
            return reader
        except ValueError as e1:
            # 尝试 seek 回到开始位置
            try:
                fileobj.seek(0)
            except (AttributeError, io.UnsupportedOperation):
                # 如果不支持 seek，读取所有数据到 BytesIO
                try:
                    data = fileobj.read()
                    fileobj = BytesIO(data)
                except:
                    raise ValueError(f'无法读取文件数据: {e1}')
            
            try:
                # 使用 dpkt.pcapng 模块
                reader = pcapng.Reader(fileobj)
                return reader
            except ValueError as e2:
                raise ValueError('unknown pcap format; libpcap error: %s, pcapng error: %s' % (e1, e2))


def count_pcap_packets(url, chunk_size=2*1024*1024):
    """统计PCAP文件中的数据包数量
    
    使用分块读取和双内存缓冲方式处理大文件，支持处理块边界不完整的数据包。
    
    Args:
        url: PCAP文件URL或本地路径
        chunk_size: 每次读取的块大小（默认2MB）
    
    Returns:
        PCAP文件中的数据包总数
    """
    import threading

    # PCAP文件头大小
    FILE_HDR_SIZE = FileHdr.__hdr_len__
    
    result: dict[str, int | list[Any]] =  {"packet_count": 0, "offsets": [FILE_HDR_SIZE]}
    
    # # 获取文件总大小
    # try:
    #     if url.startswith('http://') or url.startswith('https://'):
    #         content_length = 0
            
    #         # 网络文件：通过Range请求获取大小
    #         import urllib.request
    #         try:
    #             context: SSLContext | None = ssl._create_unverified_context() if url.startswith('https://') else None
    #             req = urllib.request.Request(url)
    #             req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    #             req.add_header('Range', 'bytes=0-0')
    #             with urllib.request.urlopen(req, context=context) as response:
    #                 content_length = response.headers.get('Content-Length') or response.headers.get('Content-Range')
    #                 if content_length:
    #                     # Content-Range 格式: bytes 0-0/filesize
    #                     if '/' in str(content_length):
    #                         content_length = int(str(content_length).split('/')[-1])
    #                     else:
    #                         content_length = int(content_length)
    #         except Exception as e:
    #             print(f"获取文件大小失败: {url}\n错误: {str(e)}")
    #             content_length = 0
                
    #         if content_length:
    #             file_size = int(content_length)
    #         else:
    #             # 读取所有内容以获取大小
    #             file_size = 0
    #     else:
    #         # 本地文件
    #         import os
    #         file_size = os.path.getsize(url)
    # except Exception as e:
    #     raise IOError(f"无法获取文件大小: {url}\n错误: {str(e)}")
    
    file_size = 1000 * 1024 * 1024
    total_packets = 0
    current_offset = FILE_HDR_SIZE  # 从PCAP文件头之后开始
    remainder_data = b''  # 上一个块的剩余数据
    
    # 双内存缓冲
    buffer_a = None
    buffer_b = None
    buffer_lock = threading.Lock()
    buffer_ready = threading.Event()
    
    def read_next_chunk(offset):
        """后台线程：读取下一个块数据"""
        nonlocal buffer_b
        
        if offset >= file_size:
            return
        
        try:
            pcap_data = PcapData(url=url, start=offset, size=chunk_size)
            with buffer_lock:
                buffer_b = pcap_data
            # 设置事件，通知主线程数据已准备好
            buffer_ready.set()
        except Exception as e:
            print(f"读取块数据失败: {e}")
            with buffer_lock:
                buffer_b = None
            buffer_ready.set()
    
    # 读取第一个块
    try:
        pcap_data = PcapData(url=url, start=current_offset, size=chunk_size)
        buffer_a = pcap_data
        current_offset += chunk_size
    except Exception as e:
        raise IOError(f"无法读取PCAP文件: {e}")
    
    # 启动后台读取线程读取第二个块
    read_thread = None
    if current_offset < file_size:
        read_thread = threading.Thread(target=read_next_chunk, args=(current_offset,))
        read_thread.daemon = True
        read_thread.start()
    
    #loop = 0

    # 处理数据块
    while buffer_a is not None or read_thread is not None:
        if buffer_a is None:
            continue
        # 合并上一个块的剩余数据和当前块的数据
        if remainder_data:
            combined_data = remainder_data + buffer_a.data
        else:
            combined_data = buffer_a.data
        
        # 遍历当前块中的数据包
        pcap_data = PcapData(packets_data=combined_data)
        remainder_data = b''
        
        # 逐个处理数据包
        while True:
            try:
                timestamp, packet_data = next(pcap_data)
                total_packets += 1
            except StopIteration:
                # 所有数据包已处理
                break
            except Exception as e:
                # 遇到不完整的数据包，保存剩余数据
                remainder_data = combined_data[pcap_data.position:]
                break
        
        # 如果没有异常且位置小于数据长度，说明有剩余数据
        if not remainder_data and pcap_data.position < len(combined_data):
            remainder_data = combined_data[pcap_data.position:]
        
        buffer_a = None
        result["packet_count"] = total_packets
        result["offsets"].append(current_offset - len(remainder_data))

        # 等待后台线程完成读取下一块数据
        if read_thread is not None and read_thread.is_alive():
            # 等待buffer_ready事件被设置（最多等待30秒）
            ready = buffer_ready.wait(timeout=30)
            
            if ready:
                # 清除事件，准备下一次等待
                buffer_ready.clear()
                
                with buffer_lock:
                    if buffer_b is not None:
                        # 后台线程成功读取了下一块数据
                        buffer_a = buffer_b
                        buffer_b = None
                        
                        # 更新当前偏移到下一块的起点
                        current_offset += chunk_size
                        
                        # 继续启动后台读取线程读取再下一块
                        next_offset = current_offset + chunk_size
                        if next_offset < file_size:
                            read_thread = threading.Thread(target=read_next_chunk, args=(next_offset,))
                            read_thread.daemon = True
                            read_thread.start()
                        else:
                            read_thread = None
                    else:
                        # 后台线程读取失败，停止处理
                        buffer_a = None
                        read_thread = None
            else:
                # 等待超时
                print("警告：等待后台线程超时")
                buffer_a = None
                read_thread = None
        else:
            # 没有后台线程，所有数据已处理完
            buffer_a = None
            read_thread = None
    
    return result


################################################################################
#                                    TESTS                                     #
################################################################################

class TryExceptException:
    def __init__(self, exception_type, msg=''):
        self.exception_type = exception_type
        self.msg = msg

    def __call__(self, f, *args, **kwargs):
        def wrapper(*args, **kwargs):
            try:
                f()
            except self.exception_type as e:
                if self.msg:
                    assert str(e) == self.msg
            else:
                raise Exception("There should have been an Exception raised")
        return wrapper


@TryExceptException(Exception, msg='There should have been an Exception raised')
def test_TryExceptException():
    """Check that we can catch a function which does not throw an exception when it is supposed to"""
    @TryExceptException(NotImplementedError)
    def fun():
        pass

    try:
        fun()
    except Exception as e:
        raise e


def test_pcap_endian():
    be = b'\xa1\xb2\xc3\xd4\x00\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x60\x00\x00\x00\x01'
    le = b'\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x60\x00\x00\x00\x01\x00\x00\x00'
    befh = FileHdr(be)
    lefh = LEFileHdr(le)
    assert (befh.linktype == lefh.linktype)


class TestData():
    pcap = (  # full libpcap file with one packet
        b'\xd4\xc3\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x01\x00\x00\x00'
        b'\xb2\x67\x4a\x42\xae\x91\x07\x00\x46\x00\x00\x00\x46\x00\x00\x00\x00\xc0\x9f\x32\x41\x8c\x00\xe0'
        b'\x18\xb1\x0c\xad\x08\x00\x45\x00\x00\x38\x00\x00\x40\x00\x40\x11\x65\x47\xc0\xa8\xaa\x08\xc0\xa8'
        b'\xaa\x14\x80\x1b\x00\x35\x00\x24\x85\xed'
    )
    modified_pcap = (
        b'\x34\xcd\xb2\xa1\x02\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x01\x00\x00\x00'
        b'\x3c\xfb\x80\x61\x6d\x32\x08\x00\x03\x00\x00\x00\x72\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\xff\xff\xff'

    )


def test_reader():
    import pytest

    data = TestData().pcap

    # --- BytesIO tests ---
    from .compat import BytesIO

    # BytesIO
    fobj = BytesIO(data)
    reader = Reader(fobj)
    assert reader.name == '<BytesIO>'
    _, buf1 = next(iter(reader))
    assert buf1 == data[FileHdr.__hdr_len__ + PktHdr.__hdr_len__:]
    assert reader.datalink() == 1

    with pytest.raises(NotImplementedError):
        reader.setfilter(1, 2)

    # --- dispatch() tests ---

    # test count = 0
    fobj.seek(0)
    reader = Reader(fobj)
    assert reader.dispatch(0, lambda ts, pkt: None) == 1

    # test count > 0
    fobj.seek(0)
    reader = Reader(fobj)
    assert reader.dispatch(4, lambda ts, pkt: None) == 1

    # test iterative dispatch
    fobj.seek(0)
    reader = Reader(fobj)
    assert reader.dispatch(1, lambda ts, pkt: None) == 1
    assert reader.dispatch(1, lambda ts, pkt: None) == 0

    # test loop() over all packets
    fobj.seek(0)
    reader = Reader(fobj)

    class Count:
        counter = 0

        @classmethod
        def inc(cls):
            cls.counter += 1

    reader.loop(lambda ts, pkt: Count.inc())
    assert Count.counter == 1


def test_reader_dloff():
    from binascii import unhexlify
    buf_filehdr = unhexlify(
        'a1b2c3d4'    # TCPDUMP_MAGIC
        '0001'        # v_major
        '0002'        # v_minor
        '00000000'    # thiszone
        '00000000'    # sigfigs
        '00000100'    # snaplen
        '00000023'    # linktype (not known)
    )

    buf_pkthdr = unhexlify(
        '00000003'  # tv_sec
        '00000005'  # tv_usec
        '00000004'  # caplen
        '00000004'  # len
    )

    from .compat import BytesIO
    fobj = BytesIO(buf_filehdr + buf_pkthdr + b'\x11' * 4)
    reader = Reader(fobj)

    # confirm that if the linktype is unknown, it defaults to 0
    assert reader.dloff == 0

    assert next(reader) == (3.000005, b'\x11' * 4)


@TryExceptException(ValueError, msg="invalid tcpdump header")
def test_reader_badheader():
    from .compat import BytesIO
    fobj = BytesIO(b'\x00' * 24)
    _ = Reader(fobj)  # noqa


def test_reader_fd():
    data = TestData().pcap

    import tempfile
    with tempfile.TemporaryFile() as fd:
        fd.write(data)
        fd.seek(0)
        reader = Reader(fd)
        assert reader.fd == fd.fileno()
        assert reader.fileno() == fd.fileno()


def test_reader_modified_pcap_type():
    data = TestData().modified_pcap

    import tempfile
    with tempfile.TemporaryFile() as fd:
        fd.write(data)
        fd.seek(0)
        reader = Reader(fd)
        assert reader.fd == fd.fileno()
        assert reader.fileno() == fd.fileno()

        timestamp, pkts = next(reader)
        assert pkts == 3 * b'\xff'
        assert timestamp == 1635842876.537197000


class WriterTestWrap:
    """
    Decorate a writer test function with an instance of this class.

    The test will be provided with a writer object, which it should write some pkts to.

    After the test has run, the BytesIO object will be passed to a Reader,
    which will compare each pkt to the return value of the test.
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, f, *args, **kwargs):
        def wrapper(*args, **kwargs):
            from .compat import BytesIO
            for little_endian in [True, False]:
                fobj = BytesIO()
                _sysle = Writer._Writer__le
                Writer._Writer__le = little_endian
                f.__globals__['writer'] = Writer(fobj, **self.kwargs.get('writer', {}))
                f.__globals__['fobj'] = fobj
                pkts = f(*args, **kwargs)
                fobj.flush()
                fobj.seek(0)

                assert pkts
                for (ts_out, pkt_out), (ts_in, pkt_in) in zip(pkts, Reader(fobj).readpkts()):
                    assert ts_out == ts_in
                    assert pkt_out == pkt_in

                # 'noqa' for flake8 to ignore these since writer was injected into globals
                writer.close()  # noqa
                Writer._Writer__le = _sysle
        return wrapper


@WriterTestWrap()
def test_writer_precision_normal():
    ts, pkt = 1454725786.526401, b'foo'
    writer.writepkt(pkt, ts=ts)  # noqa
    return [(ts, pkt)]


@WriterTestWrap(writer={'nano': True})
def test_writer_precision_nano():
    ts, pkt = Decimal('1454725786.010203045'), b'foo'
    writer.writepkt(pkt, ts=ts)  # noqa
    return [(ts, pkt)]


@WriterTestWrap(writer={'nano': False})
def test_writer_precision_nano_fail():
    """if writer is not set to nano, supplying this timestamp should be truncated"""
    ts, pkt = (Decimal('1454725786.010203045'), b'foo')
    writer.writepkt(pkt, ts=ts)  # noqa
    return [(1454725786.010203, pkt)]


@WriterTestWrap()
def test_writepkt_no_time():
    ts, pkt = 1454725786.526401, b'foooo'
    _tmp = time.time
    time.time = lambda: ts
    writer.writepkt(pkt)  # noqa
    time.time = _tmp
    return [(ts, pkt)]


@WriterTestWrap(writer={'snaplen': 10})
def test_writepkt_snaplen():
    ts, pkt = 1454725786.526401, b'foooo'
    writer.writepkt(pkt, ts)  # noqa
    return [(ts, pkt)]


@WriterTestWrap()
def test_writepkt_with_time():
    ts, pkt = 1454725786.526401, b'foooo'
    writer.writepkt(pkt, ts)  # noqa
    return [(ts, pkt)]


@WriterTestWrap()
def test_writepkt_time():
    ts, pkt = 1454725786.526401, b'foooo'
    writer.writepkt_time(pkt, ts)  # noqa
    return [(ts, pkt)]


@WriterTestWrap()
def test_writepkts():
    """writing multiple packets from a list"""
    pkts = [
        (1454725786.526401, b"fooo"),
        (1454725787.526401, b"barr"),
        (3243204320.093211, b"grill"),
        (1454725789.526401, b"lol"),
    ]

    writer.writepkts(pkts)  # noqa
    return pkts


def test_universal_reader():
    import pytest
    from .compat import BytesIO

    # libpcap
    data = TestData().pcap
    fobj = BytesIO(data)
    reader = UniversalReader(fobj)
    assert isinstance(reader, Reader)

    # pcapng
    data = pcapng.define_testdata().valid_pcapng
    fobj = BytesIO(data)
    reader = UniversalReader(fobj)
    assert isinstance(reader, pcapng.Reader)

    # unknown
    fobj = BytesIO(b'\x42' * 1000)
    with pytest.raises(ValueError):
        reader = UniversalReader(fobj)
