"""
攻击检测模块
负责基于统计信息检测各种DDOS攻击
"""

from typing import Dict, List
from .packet_statistics import PacketStatistics


class AttackDetector:
    """攻击检测类 - 负责基于统计信息检测各种DDOS攻击"""
    
    def __init__(self):
        """初始化攻击检测器"""
        # DDOS检测阈值
        self.thresholds = {
            'syn_flood': 1000,      # SYN包/秒
            'ack_flood': 800,     # ACK包/秒
            'udp_flood': 2000,      # UDP包/秒
            'icmp_flood': 500,      # ICMP包/秒
            'http_flood': 100,      # HTTP请求/秒
            'dns_amplification': 50, # DNS响应/秒
            'dns_flood': 30, # DNS攻击包/秒
            'memcached_reflection': 10, # Memcached反射包/秒
            'ntp_reflection': 20,    # NTP反射包/秒
            'snmp_amplification': 15,   # SNMP反射包/秒
            'ssdp_flood': 25, # SSDP反射包/秒
            'packet_rate': 5000,    # 总包率/秒
            'connection_rate': 100, # 新连接/秒
        }
    
    def detect_attacks(self, stats: PacketStatistics) :
        """检测具体的DDOS攻击类型
        
        Args:
            stats: PacketStatistics实例
            
        Returns:
            (attacks, system_anomalies): 攻击列表和系统异常列表的元组
        """
        result= {"attacts": [], "system_anomalies": []}

        attacks = []  # 具体的攻击类型
        system_anomalies = []  # 系统异常检测（高包率、高连接率）
        
        duration = stats.get_duration()
        if duration == 0:
            duration = 1
        
        packet_stats = stats.get_stats()
        
        
        # SYN Flood检测
        syn_rate = packet_stats['syn_flood'] / duration
        if syn_rate > self.thresholds['syn_flood']:
            attacks.append({
                'type': 'SYN_Flood',
                'category': 'SYN洪水攻击',
                'severity': 'high',
                'rate': syn_rate,
                'threshold': self.thresholds['syn_flood'],
                'description': '检测到SYN洪水攻击，大量半开连接'
            })
        
        # UDP Flood检测（主类型）
        udp_rate = packet_stats['udp_flood'] / duration
        if udp_rate > self.thresholds['udp_flood']:
            attacks.append({
                'type': 'UDP_Flood',
                'category': 'UDP洪水攻击',
                'severity': 'high',
                'rate': udp_rate,
                'threshold': self.thresholds['udp_flood'],
                'description': '检测到UDP洪水攻击'
            })
        
        # Memcached反射攻击检测
        memcached_rate = packet_stats['memcached_reflection'] / duration
        if memcached_rate > self.thresholds['memcached_reflection']:
            attacks.append({
                'type': 'memcached_reflection',
                'category': 'Memcached放大反射攻击',
                'severity': 'critical',
                'rate': memcached_rate,
                'threshold': self.thresholds['memcached_reflection'],
                'description': '检测到Memcached反射攻击（源端口11211）'
            })
        
        # NTP反射攻击检测
        ntp_rate = packet_stats['ntp_reflection'] / duration
        if ntp_rate > self.thresholds['ntp_reflection']:
            attacks.append({
                'type': 'ntp_reflection',
                'category': 'NTP反射放大攻击',
                'severity': 'high',
                'rate': ntp_rate,
                'threshold': self.thresholds['ntp_reflection'],
                'description': '检测到NTP反射攻击（源端口123）'
            })
        
        # SNMP反射攻击检测
        snmp_rate = packet_stats['snmp_amplification'] / duration  
        if snmp_rate > self.thresholds['snmp_amplification']:
            attacks.append({
                'type': 'snmp_amplification',
                'category': 'SNMP放大攻击',
                'severity': 'high',
                'rate': snmp_rate,
                'threshold': self.thresholds['snmp_amplification'],
                'description': '检测到SNMP反射攻击（源端口161）'
            })
        
        # ACK Flood检测
        ack_rate = packet_stats['ack_flood'] / duration
        if ack_rate > self.thresholds['ack_flood']:
            attacks.append({
                'type': 'ACK_Flood',
                'category': 'ACK洪水攻击',
                'severity': 'high',
                'rate': ack_rate,
                'threshold': self.thresholds['ack_flood'],
                'description': '检测到ACK洪水攻击'
            })
        
        # DNS反射攻击检测（DNS攻击包）
        dns_flood_rate = packet_stats['dns_flood'] / duration
        if dns_flood_rate > self.thresholds['dns_flood']:
            attacks.append({
                'type': 'dns_flood',
                'category': 'DNS洪水攻击',
                'severity': 'high',
                'rate': dns_flood_rate,
                'threshold': self.thresholds['dns_flood'],
                'description': '检测到DNS反射攻击（源端口53）'
            })
        
        # DNS放大攻击检测
        dns_amplification_rate = packet_stats['dns_amplification'] / duration
        if dns_amplification_rate > self.thresholds['dns_amplification']:
            attacks.append({
                'type': 'DNS_Amplification',
                'category': 'DNS放大攻击',
                'severity': 'critical',
                'rate': dns_amplification_rate,
                'threshold': self.thresholds['dns_amplification'],
                'description': '检测到DNS放大攻击'
            })
        
        # ICMP Flood检测
        icmp_rate = packet_stats['icmp_flood'] / duration
        if icmp_rate > self.thresholds['icmp_flood']:
            attacks.append({
                'type': 'ICMP_Flood',
                'category': 'ICMP洪水攻击',
                'severity': 'medium',
                'rate': icmp_rate,
                'threshold': self.thresholds['icmp_flood'],
                'description': '检测到ICMP洪水攻击（Ping Flood）'
            })
        
        # SSDP反射攻击检测
        ssdp_rate = packet_stats['ssdp_flood'] / duration
        if ssdp_rate > self.thresholds['ssdp_flood']:
            attacks.append({
                'type': 'ssdp_flood',
                'category': 'SSDP洪水攻击',
                'severity': 'high',
                'rate': ssdp_rate,
                'threshold': self.thresholds['ssdp_flood'],
                'description': '检测到SSDP反射攻击（源端口1900）'
            })
        
        # HTTP Flood检测
        http_rate = packet_stats['http_flood'] / duration
        if http_rate > self.thresholds['http_flood']:
            attacks.append({
                'type': 'HTTP_Flood',
                'category': '应用层攻击',
                'severity': 'high',
                'rate': http_rate,
                'threshold': self.thresholds['http_flood'],
                'description': '检测到HTTP洪水攻击'
            })

        
        # 高包率检测（系统异常）

        # 计算速率
        packet_rate = packet_stats['total_packets'] / duration
        if packet_rate > self.thresholds['packet_rate']:
            system_anomalies.append({
                'type': 'High_Packet_Rate',
                'severity': 'medium',
                'rate': packet_rate,
                'threshold': self.thresholds['packet_rate'],
                'description': '检测到异常高的数据包速率'
            })
        
        # 高连接率检测（系统异常）
        connection_rate = stats.get_unique_src_ips_count() / duration
        if connection_rate > self.thresholds['connection_rate']:
            system_anomalies.append({
                'type': 'High_Connection_Rate',
                'severity': 'medium',
                'rate': connection_rate,
                'threshold': self.thresholds['connection_rate'],
                'description': '检测到异常高的新连接速率'
            })
        
        result["attacts"] = attacks
        result["system_anomalies"] = system_anomalies

        return result
    
    def calculate_risk_level(self, attacks: List[Dict]) -> str:
        """计算风险等级"""
        if not attacks:
            return 'low'
        
        severities = [attack['severity'] for attack in attacks]
        
        if 'critical' in severities:
            return 'critical'
        elif 'high' in severities:
            return 'high'
        elif 'medium' in severities:
            return 'medium'
        else:
            return 'low'