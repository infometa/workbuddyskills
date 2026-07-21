from typing_extensions import LiteralString


import os
import requests
import time
import uuid
from typing import Dict, Any

from pydantic import BaseModel

def download_file(url: str) -> str:
    """
    下载链接中的文件并保存为pcap格式

    Args:
        url (str): 文件下载链接

    Returns:
        str: 下载成功的文件路径
    """
    # 创建保存目录
    save_dir = "/tmp/wiremcp"
    os.makedirs(save_dir, exist_ok=True)

    # 生成随机文件名，使用时间戳+随机uuid保证唯一性
    timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
    random_suffix = str(uuid.uuid4())[:8]  # 随机字符串前8位
    filename = f"{timestamp}_{random_suffix}.pcap"

    # 完整文件路径
    file_path = os.path.join(save_dir, filename)

    # 发送HTTP请求下载文件
    response = requests.get(url)
    response.raise_for_status()  # 如果请求失败会抛出异常

    # 保存文件
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path


def get_file_path(file_path: str):
    path = ""
    # 判断是URL还是本地文件路径
    if file_path.startswith(('http://', 'https://')):
        # 如果是URL，使用下载函数
        path = download_file(file_path)
    else:
        # 如果是本地路径，直接使用
        path = file_path

    return path


def format_analysis_report(analysis_result: Dict[str, Any]) -> str:
    """格式化分析报告为可读的字符串（支持普通分析和切片分析）
    
    Args:
        analysis_result: analyze_pcap_file、analyze_packets 或 analyze_pcap_slice 的返回结果
        
    Returns:
        格式化的报告字符串
    """
    if 'error' in analysis_result:
        error_type = "分析失败" 
        return f"{error_type}: {analysis_result['error']}"

    # 根据分析类型设置标题和分隔线
    title = "流量摘要:"
    #separator: LiteralString = "=" * 50
    
    
    # 格式化报告
    report = f"{title}\n"
    #report += separator + "\n\n"
    

    # 包类型时间记录
    time_records = analysis_result.get('packet_time_records', {})
    if time_records:
        report += f"包类型时间记录:\\n"
        
        # 显示主要包类型的时间记录
        main_types = ['ip_packets', 'tcp_packets', 'syn_flood', 'udp_flood', 'icmp_flood', 'http_flood', 'dns_amplification']
        for packet_type in main_types:
            if packet_type in time_records:
                record = time_records[packet_type]
                if record['first_seen']:
                    duration = f" (持续 {record['duration_seconds']:.2f}秒)" if record['duration_seconds'] else ""
                    report += f"- {packet_type}: {record['first_seen']} ~ {record['last_seen']}{duration}\\n"
        
        # 显示UDP协议子类型的时间记录
        udp_protocols = time_records.get('udp_protocols', {})
        if udp_protocols:
            report += f"\\nUDP协议子类型时间记录:\\n"
            for protocol, record in udp_protocols.items():
                if record['first_seen']:
                    duration = f" (持续 {record['duration_seconds']:.2f}秒)" if record['duration_seconds'] else ""
                    report += f"- {protocol}: {record['first_seen']} ~ {record['last_seen']}{duration}\\n"
        
        report += "\\n"
        
    # 摘要信息
    summary = analysis_result['summary']
    report += f"流量摘要:\n"
    report += f"- 总数据包数: {summary['total_packets']}\n"
    report += f"- 持续时间: {summary['duration_seconds']:.2f} 秒\n"
    report += f"- 包速率: {summary['packet_rate']} 包/秒\n"
    report += f"- 唯一源IP: {summary['unique_source_ips']}\n"
    report += f"- 唯一目的IP: {summary['unique_destination_ips']}\n\n"
    
    # 协议统计 (平级结构)
    protocol_stats = analysis_result['protocol_stats']
    report += f"协议统计:\n"
    report += f"- SYN包: {protocol_stats['syn_flood']}\n"
    report += f"- ACK包: {protocol_stats.get('ack_flood', 0)}\n"
    report += f"- UDP包: {protocol_stats['udp_flood']}\n"
    report += f"- ICMP包: {protocol_stats['icmp_flood']}\n"
    report += f"- HTTP请求: {protocol_stats['http_flood']}\n"
    report += f"- DNS响应: {protocol_stats['dns_amplification']}\n"
    report += f"- Memcached攻击: {protocol_stats.get('memcached_reflection', 0)}\n"
    report += f"- DNS攻击: {protocol_stats.get('dns_flood', 0)}\n"
    report += f"- NTP攻击: {protocol_stats.get('ntp_reflection', 0)}\n"
    report += f"- SNMP攻击: {protocol_stats.get('snmp_amplification', 0)}\n"
    report += f"- SSDP攻击: {protocol_stats.get('ssdp_flood', 0)}\n\n"
    
    
    # 检测到的攻击
    attacks = analysis_result['detected_attacks']
    report += f"检测到的攻击 ({len(attacks)} 种):\n"
    
    if not attacks:
        report += "- 未检测到明显的DDOS攻击\n"
    else:
        for attack in attacks:
            report += f"- [{attack['severity'].upper()}] {attack['type']}\n"
            report += f"  速率: {attack['rate']} (阈值: {attack['threshold']})\n"
            report += f"  描述: {attack['description']}\n\n"
    
    # 攻击源国家统计
    attack_sources = analysis_result.get('attack_sources', {})
    if attack_sources:
        report += f"攻击源国家分布:\n"
        
        # 显示所有攻击的总体分布
        if 'all_attacks' in attack_sources:
            all_stats = attack_sources['all_attacks']
            report += f"所有攻击类型总体分布 (前10个国家):\n"
            for country, count in all_stats['top_countries']:
                percentage = (count / all_stats['total_attacks']) * 100
                report += f"  - {country}: {count} 次攻击 ({percentage:.1f}%)\n"
            report += "\n"
        
        # 显示每种攻击类型的分布
        for attack_type, stats in attack_sources.items():
            if attack_type != 'all_attacks' and stats['total_attacks'] > 0:
                report += f"{attack_type} 攻击源分布:\n"
                for country, count in stats['top_countries']:
                    percentage = (count / stats['total_attacks']) * 100
                    report += f"  - {country}: {count} 次攻击 ({percentage:.1f}%)\n"
                report += "\n"
    
    # 风险等级
    risk_level = analysis_result['risk_level']
    risk_emojis = {
        'low': '🟢',
        'medium': '🟡', 
        'high': '🟠',
        'critical': '🔴'
    }
    report += f"总体风险等级: {risk_emojis.get(risk_level, '⚪')} {risk_level.upper()}\n"
    
    # API 补充查询信息
    api_enhancement = analysis_result.get('api_enhancement', {})
    if api_enhancement and api_enhancement.get('queried', 0) > 0:
        report += f"\nAPI 补充查询:\n"
        report += f"- 查询未知IP: {api_enhancement.get('queried', 0)} 个\n"
        report += f"- 成功定位: {api_enhancement.get('succeeded', 0)} 个\n"
        if api_enhancement.get('still_unknown', 0) > 0:
            report += f"- 仍未知: {api_enhancement.get('still_unknown', 0)} 个\n"
        enhanced_countries = api_enhancement.get('enhanced_countries', {})
        if enhanced_countries:
            report += f"- 补充修正国家分布:\n"
            for country, count in sorted(enhanced_countries.items(), key=lambda x: x[1], reverse=True):
                report += f"  - {country}: {count} 包\n"
    
    return report
