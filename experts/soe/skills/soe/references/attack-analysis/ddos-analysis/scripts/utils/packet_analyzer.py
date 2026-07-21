"""
数据包分析器模块
专门处理数据包列表的分析和DDOS检测
"""

import time
from typing import Dict, Any
from scapy.all import IP, TCP, UDP, ICMP
from scapy.layers.l2 import GRE
from utils.packet_statistics import PacketStatistics
from utils.attack_detector import AttackDetector


class PacketAnalyzer:
    """数据包分析器 - 专门处理数据包列表的分析"""
    
    def __init__(self, white = ""):
        """初始化数据包分析器"""
        self.packet_stats = PacketStatistics()
        self.attack_detector = AttackDetector()
        
        self.white_list = white.strip().split(",") if isinstance(white, str) else []

    def analyze_packets(self, packets) -> Dict[str, Any]:
        """
        分析数据包列表
        
        Args:
            packets: 数据包列表
            
        Returns:
            DDOS检测结果
        """
        # 重置统计信息
        #self.packet_stats.reset()
        
        # 处理数据包
        for packet in packets:
            self.process_packet(packet)
        
        return self._generate_report()
    
    def process_packet(self, packet):
        """处理单个数据包"""
        if not packet.haslayer(IP):
            return

        # 判断是否为GRE包，如果是则解封
        if packet.haslayer(GRE):
            inner_packet = self._unwrap_gre_packet(packet)
            if inner_packet is not None:
                packet = inner_packet
            else:
                return
        
        if not packet.haslayer(IP):
            return

        # 过滤白名单IP
        if packet[IP].src in self.white_list:
            return
            
        ip_layer = packet[IP]
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        
        # 获取PCAP包的时间戳
        packet_timestamp = float(packet.time) if hasattr(packet, 'time') else None
        
        # 使用PacketStatistics进行统计
        self.packet_stats.increment_total_packets()
        self.packet_stats.add_src_ip(src_ip)
        self.packet_stats.add_dst_ip(dst_ip)
        
        protocal = ""
        # 分析传输层协议
        if packet.haslayer(TCP):
            protocal = self._analyze_tcp(packet, ip_layer)
        elif packet.haslayer(UDP):
            protocal = self._analyze_udp(packet, ip_layer)
        elif packet.haslayer(ICMP):
            protocal = self._analyze_icmp(packet, ip_layer)

        if protocal:
            self.packet_stats.increment_protocol(protocal, ip=src_ip, packet_timestamp=packet_timestamp)

    def _analyze_tcp(self, packet, ip_layer):
        """分析TCP数据包"""
        tcp_layer = packet[TCP]
        src_ip = ip_layer.src
        dst_port = tcp_layer.dport
        src_port = tcp_layer.sport
        
        protocol = ""
        
        # 将 TCP 标志转换为整数以支持 FlagValue 类型
        flags = int(tcp_layer.flags)

        # SYN Flood检测
        if flags & 0x02:  # SYN标志
            protocol = "syn_flood"        
        # ACK Flood检测 (ACK标志，无SYN标志)
        elif (flags & 0x10) and not (flags & 0x02):  # ACK标志且无SYN标志
            protocol = "ack_flood"        
        # HTTP Flood检测
        elif dst_port == 80 or dst_port == 443:
            payload = bytes(tcp_layer.payload)
            if b'GET' in payload or b'POST' in payload or b'HTTP' in payload:
                protocol = "http_flood"
        # DNS over TCP 攻击检测 (端口 53)
        elif src_port == 53 or dst_port == 53:
            try:
                payload = bytes(tcp_layer.payload)
                # TCP DNS 请求/响应通常有特定的格式（DNS header）
                if len(payload) > 12:  # 最小DNS header长度
                    protocol = "dns_flood"
                    # 记录TCP DNS攻击源
            except:
                pass

        return protocol

    def _analyze_udp(self, packet, ip_layer):
        """分析UDP数据包"""
        udp_layer = packet[UDP]
        src_ip = ip_layer.src
        dst_port = udp_layer.dport
        src_port = udp_layer.sport
        
        protocol = "udp_flood"

        # UDP洪水攻击的常见协议分类统计
        # 1. Memcached UDP 反射攻击检测 (源端口 11211)
        if src_port == 11211:
            protocol = "memcached_reflection"
        # 2. DNS 反射攻击检测 (源端口 53)
        elif src_port == 53 or dst_port == 53:
            # DNS放大攻击检测 - 响应包较大
            if len(bytes(udp_layer.payload)) > 100:
                protocol = "dns_amplification"
            else:
                # 记录DNS洪水   
                protocol = "dns_flood"
        # 3. NTP 反射攻击检测 (源端口 123)
        elif src_port == 123:
            protocol = "ntp_reflection"
        # 4. SNMP 反射攻击检测 (源端口 161)
        elif src_port == 161:
            protocol = "snmp_amplification"
        # 5. SSDP 反射攻击检测 (源端口 1900)
        elif src_port == 1900:
            protocol = "ssdp_flood"
        # 6. 否则其他UDP流量
        else:
            protocol = "udp_flood"
        
        return protocol

    def _analyze_icmp(self, packet, ip_layer):
        """分析ICMP数据包"""
        src_ip = ip_layer.src
        protocol = "icmp_flood"
        
        return protocol
    
    def _unwrap_gre_packet(self, packet):
        """
        解封GRE包，获取GRE内层的包
        支持递归处理嵌套的GRE隧道
        
        Args:
            packet: 包含GRE层的数据包
            
        Returns:
            解封后的内层包，如果解封失败则返回None
        """
        try:
            if not packet.haslayer(GRE):
                return None
            
            current_packet = packet
            
            # 递归处理嵌套的GRE隧道
            while current_packet and current_packet.haslayer(GRE):
                gre_layer = current_packet[GRE]
                payload = gre_layer.payload
                
                if payload is None:
                    return None
                
                # 根据GRE协议类型判断内层包的格式
                # GRE协议类型 (proto field in GRE header)
                # 0x0800 = IPv4
                # 0x86DD = IPv6
                # 0x0806 = ARP
                
                current_packet = payload
                
                # 如果不再是IP包，返回当前包
                if not current_packet.haslayer(IP):
                    return current_packet
            
            return current_packet
            
        except Exception:
            # 解封失败时返回None
            return None
    
    def _enhance_unknown_sources_with_api(self, top_n: int = 100) -> dict:
        """
        对嵌入式数据库中未知的攻击源 IP 进行 API 在线补充查询

        在生成报告前调用，将 TOP N 高频未知 IP 的归属国通过在线 API 补充查询，
        并更新 attack_sources 统计（从"未知"转移到正确国家）。

        Args:
            top_n: 只查询 TOP N 个高频未知 IP

        Returns:
            dict: 增强统计信息
        """
        try:
            result = self.packet_stats.enhance_attack_sources_with_api(top_n=top_n)
            if result.get('succeeded', 0) > 0:
                from loguru import logger
                logger.info(
                    f"API 补充查询完成: 查询 {result['queried']} 个未知 IP，"
                    f"成功 {result['succeeded']} 个，"
                    f"修正国家分布: {result['enhanced_countries']}"
                )
            return result
        except Exception as e:
            from loguru import logger
            logger.warning(f"API 补充查询失败（不影响主分析）: {e}")
            return {
                'queried': 0, 'succeeded': 0,
                'enhanced_countries': {}, 'still_unknown': 0,
                'error': str(e)
            }
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成检测报告"""
        duration = self.packet_stats.get_duration()
        if duration == 0:
            duration = 1
        
        # API 补充查询：对嵌入式数据库未知的攻击源 IP 进行在线归属国补充查询
        # 仅查询 TOP N 高频未知 IP，避免逐一查询百万级 IP
        api_enhancement = self._enhance_unknown_sources_with_api()
        
        # 获取统计数据
        stats = self.packet_stats.get_stats()
        attack_sources = self.packet_stats.get_attack_sources()
        
        # 计算速率
        packet_rate = stats['total_packets'] / duration
        syn_rate = stats['syn_flood'] / duration
        udp_rate = stats['udp_flood'] / duration
        icmp_rate = stats['icmp_flood'] / duration
        http_rate = stats['http_flood'] / duration
        dns_amplification = stats['dns_amplification'] / duration
        connection_rate = self.packet_stats.get_unique_src_ips_count() / duration
        
        # 使用AttackDetector检测DDOS类型
        dic_result = self.attack_detector.detect_attacks(self.packet_stats)
        
        detected_attacks =  dic_result.get('attacts', [])
        system_anomalies = dic_result.get('system_anomalies', [])
        # 生成攻击源国家统计
        attack_sources_summary = {}
        for attack_type, country_stats in attack_sources.items():
            if country_stats:  # 只包含有数据的攻击类型
                total_attacks = sum(country_stats.values())
                top_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:100]
                attack_sources_summary[attack_type] = {
                    'total_attacks': total_attacks,
                    'top_countries': top_countries
                }
        
        # 生成攻击类型统计分布（仅针对具体的攻击类型）
        attack_type_distribution = {}
        for attack in detected_attacks:
            attack_type = attack['type']
            if attack_type not in attack_type_distribution:
                attack_type_distribution[attack_type] = 0
            attack_type_distribution[attack_type] += 1
        
        # 按攻击次数排序
        attack_type_distribution = dict(sorted(attack_type_distribution.items(), 
                                             key=lambda x: x[1], reverse=True))
        
        # 生成系统异常统计分布
        system_anomaly_distribution = {}
        for anomaly in system_anomalies:
            anomaly_type = anomaly['type']
            if anomaly_type not in system_anomaly_distribution:
                system_anomaly_distribution[anomaly_type] = 0
            system_anomaly_distribution[anomaly_type] += 1
        
        # 按异常次数排序
        system_anomaly_distribution = dict(sorted(system_anomaly_distribution.items(), 
                                                key=lambda x: x[1], reverse=True))
        
        return {
            'summary': {
                'total_packets': stats['total_packets'],
                'duration_seconds': duration,
                'packet_rate': round(packet_rate, 2),
                'unique_source_ips': self.packet_stats.get_unique_src_ips_count(),
                'unique_destination_ips': self.packet_stats.get_unique_dst_ips_count(),
            },
            'protocol_stats': {
                'syn_flood': stats['syn_flood'],
                'ack_flood': stats['ack_flood'],
                'udp_flood': stats['udp_flood'],
                'icmp_flood': stats['icmp_flood'],
                'http_flood': stats['http_flood'],
                'dns_amplification': stats['dns_amplification'],
                'memcached_reflection': stats['memcached_reflection'],
                'dns_flood': stats['dns_flood'],
                'ntp_reflection': stats['ntp_reflection'],
                'snmp_amplification': stats['snmp_amplification'],
                'ssdp_flood': stats['ssdp_flood'],
            },
            'rates': {
                'syn_rate': round(syn_rate, 2),
                'udp_rate': round(udp_rate, 2),
                'icmp_rate': round(icmp_rate, 2),
                'http_rate': round(http_rate, 2),
                'dns_amplification': round(dns_amplification, 2),
                'connection_rate': round(connection_rate, 2),
            },
            'packet_time_records': self.packet_stats.get_packet_time_records(),
            'detected_attacks': detected_attacks,
            'system_anomalies': system_anomalies,
            'attack_sources': attack_sources_summary,
            'attack_type_distribution': attack_type_distribution,
            'system_anomaly_distribution': system_anomaly_distribution,
            'risk_level': self.attack_detector.calculate_risk_level(detected_attacks + system_anomalies),
            'api_enhancement': api_enhancement,
        }
