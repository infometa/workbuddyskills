"""
数据包统计模块
负责收集和维护各种协议的统计信息
"""

import time
from collections import defaultdict

class PacketStatistics:
    """数据包统计类 - 负责收集和维护各种协议的统计信息"""
    
    def __init__(self):
        """初始化统计信息"""
        self.reset()
    
    def reset(self):
        """重置所有统计信息"""
        self.stats = {
            'total_packets': 0,
            'syn_flood': 0,
            'ack_flood': 0,
            'udp_flood': 0,
            'icmp_flood': 0,
            'http_flood': 0,
            'dns_amplification': 0,
            'memcached_reflection': 0,
            'dns_flood': 0,
            'ntp_reflection': 0,
            'snmp_amplification': 0,
            'ssdp_flood': 0,
            'unique_src_ips': set(),
            'unique_dst_ips': set(),
            'start_time': time.time(),
        }
        
        # 攻击源IP国家统计
        self.attack_sources = {
            'syn_flood': defaultdict(int),
            'udp_flood': defaultdict(int),
            'icmp_flood': defaultdict(int),
            'http_flood': defaultdict(int),
            'dns_amplification': defaultdict(int),
            'memcached_reflection': defaultdict(int),
            'ntp_reflection': defaultdict(int),
            'snmp_reflection': defaultdict(int),
            'all_attacks': defaultdict(int),

            'ack_flood': defaultdict(int),     # ACK包/秒
            'dns_flood': defaultdict(int), # DNS攻击包/秒
            'ntp_reflection': defaultdict(int),    # NTP反射包/秒
            'snmp_amplification': defaultdict(int),   # SNMP反射包/秒
            'ssdp_flood': defaultdict(int), # SSDP反射包/秒
        }
        
        # 未知 IP 追踪：{ip: {attack_type: count}}，用于 API 补充查询
        # 仅记录嵌入式数据库中找不到归属国的 IP 及其攻击类型分布
        self.unknown_ip_tracker = {}

        # 每种包类型的时间记录
        self.packet_time_records = {
            'syn_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'ack_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'udp_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'icmp_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'http_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'dns_amplification': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'memcached_reflection': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'dns_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'ntp_reflection': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'snmp_amplification': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'ssdp_flood': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'tcp_packets': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
            'ip_packets': {'first_seen': 0.0, 'last_seen': 0.0, 'has_data': False},
        }
    
    def _record_packet_time(self, packet_type: str, packet_timestamp: float = None):
        """记录包类型的第一次和最后一次出现时间
        
        Args:
            packet_type: 包类型
            packet_timestamp: PCAP包的时间戳（秒），如果为None则使用系统时间
        """
        # 使用PCAP包的时间戳，如果没有提供则使用系统时间
        current_time = packet_timestamp if packet_timestamp is not None else time.time()
        
        if packet_type in self.packet_time_records:
            record = self.packet_time_records[packet_type]
            if not record['has_data']:
                record['first_seen'] = current_time
                record['has_data'] = True
            record['last_seen'] = current_time
    
    def increment_total_packets(self):
        """增加总包数"""
        self.stats['total_packets'] += 1
    
    def add_src_ip(self, ip: str):
        """添加源IP"""
        self.stats['unique_src_ips'].add(ip)
    
    def add_dst_ip(self, ip: str):
        """添加目标IP"""
        self.stats['unique_dst_ips'].add(ip)
    
    def increment_protocol(self, protocol: str, ip = "", packet_timestamp: float = None):
        """增加特定UDP协议统计
        
        Args:
            protocol: 协议类型
            ip: 源IP地址
            packet_timestamp: PCAP包的时间戳（秒）
        """
        if protocol in self.stats:
            self.stats[protocol] += 1
        else:
            self.stats[protocol] = 1

        self._record_packet_time(protocol, packet_timestamp)
        if protocol == "syn_flood":
            self._record_packet_time('tcp_packets', packet_timestamp)  # SYN包也是TCP包
        elif protocol == "ack_flood":
            self._record_packet_time('tcp_packets', packet_timestamp)  # ACK包也是TCP包
        elif protocol == "udp_flood":
            self._record_packet_time('ip_packets', packet_timestamp)   # UDP包也是IP包
        elif protocol == "http_flood":
            self._record_packet_time('tcp_packets', packet_timestamp)  # HTTP基于TCP
        elif protocol == "dns_amplification":
            self._record_packet_time('udp_flood', packet_timestamp)  # DNS通常基于UDP
        elif protocol == "memcached_reflection":
            self._record_packet_time('tcp_packets', packet_timestamp)  # Memcached通常基于TCP
        elif protocol == "dns_flood":   
            self._record_packet_time('udp_flood', packet_timestamp)  # DNS通常基于UDP
        
        self._record_packet_time('ip_packets', packet_timestamp)   # DDOS 一般也是IP包  

        if ip:
            self.record_attack_source(protocol, ip)

    def record_attack_source(self, attack_type: str, ip: str):
        """记录攻击源国家统计"""
        from geo import locate_ip
        try:
            result = locate_ip(ip, is_cache=True)
            country = result.get('country_cn', '未知')
        except:
            country = '未知'
        
        # 追踪未知 IP，用于后续 API 补充查询
        if country == '未知':
            if ip not in self.unknown_ip_tracker:
                self.unknown_ip_tracker[ip] = defaultdict(int)
            self.unknown_ip_tracker[ip][attack_type] += 1
        
        self.attack_sources[attack_type][country] += 1
        self.attack_sources['all_attacks'][country] += 1
    
    def enhance_attack_sources_with_api(self, top_n: int = 100) -> dict:
        """
        通过 API 补充查询未知 IP 的归属国，并更新 attack_sources 统计

        策略：取 TOP N 个高频未知 IP，通过在线 API 批量查询归属国，
        然后将这些 IP 的攻击计数从"未知"转移到正确的国家。

        Args:
            top_n: 只查询 TOP N 个高频未知 IP（默认 100）

        Returns:
            dict: 增强统计信息
                - queried: 查询的 IP 数
                - succeeded: 成功查询的 IP 数
                - enhanced_countries: {国家: 修正的包数}
                - still_unknown: 仍然未知的 IP 数
        """
        if not self.unknown_ip_tracker:
            return {
                'queried': 0, 'succeeded': 0,
                'enhanced_countries': {}, 'still_unknown': 0
            }

        from geo import enhance_unknown_ips, enhance_cache_with_api

        # 构建未知 IP 包计数 {ip: total_count}
        ip_counter = {}
        for ip, type_counts in self.unknown_ip_tracker.items():
            ip_counter[ip] = sum(type_counts.values())

        # API 查询 TOP N 未知 IP
        enhanced = enhance_unknown_ips(ip_counter, top_n=top_n)

        # 将成功查询的 IP 写入内存缓存（后续 locate_ip 直接命中）
        enhance_cache_with_api(enhanced)

        # 更新 attack_sources：从"未知"扣除，加到正确国家
        enhanced_countries = {}
        succeeded = 0
        for ip, country_cn in enhanced.items():
            if country_cn == '未知' or ip not in self.unknown_ip_tracker:
                continue

            succeeded += 1
            type_counts = self.unknown_ip_tracker[ip]

            for attack_type, count in type_counts.items():
                # 从"未知"扣除
                if self.attack_sources[attack_type].get('未知', 0) >= count:
                    self.attack_sources[attack_type]['未知'] -= count
                    if self.attack_sources[attack_type]['未知'] <= 0:
                        del self.attack_sources[attack_type]['未知']

                # 加到正确国家
                self.attack_sources[attack_type][country_cn] += count

                # 同步更新 all_attacks
                if self.attack_sources['all_attacks'].get('未知', 0) >= count:
                    self.attack_sources['all_attacks']['未知'] -= count
                    if self.attack_sources['all_attacks']['未知'] <= 0:
                        del self.attack_sources['all_attacks']['未知']
                self.attack_sources['all_attacks'][country_cn] += count

                enhanced_countries[country_cn] = enhanced_countries.get(country_cn, 0) + count

            # 从未知追踪器移除
            del self.unknown_ip_tracker[ip]

        return {
            'queried': min(top_n, len(ip_counter)),
            'succeeded': succeeded,
            'enhanced_countries': enhanced_countries,
            'still_unknown': len(self.unknown_ip_tracker)
        }
    
    def get_duration(self) -> float:
        """获取统计持续时间"""
        return time.time() - self.stats['start_time']
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_attack_sources(self) -> dict:
        """获取攻击源统计"""
        return dict(self.attack_sources)
    
    def get_unique_src_ips_count(self) -> int:
        """获取唯一源IP数量"""
        return len(self.stats['unique_src_ips'])
    
    def get_unique_dst_ips_count(self) -> int:
        """获取唯一目标IP数量"""
        return len(self.stats['unique_dst_ips'])
    
    def get_packet_time_records(self) -> dict:
        """获取包类型时间记录"""
        # 转换时间戳为可读格式
        formatted_records = {}
        
        for packet_type, record in self.packet_time_records.items():
            if record['has_data']:
                formatted_records[packet_type] = {
                    'first_seen': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record['first_seen'])),
                    'last_seen': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record['last_seen'])),
                    'first_seen_timestamp': record['first_seen'],
                    'last_seen_timestamp': record['last_seen'],
                    'duration_seconds': record['last_seen'] - record['first_seen']
                }
            else:
                formatted_records[packet_type] = {
                    'first_seen': None,
                    'last_seen': None,
                    'first_seen_timestamp': None,
                    'last_seen_timestamp': None,
                    'duration_seconds': None
                }
        
        return formatted_records