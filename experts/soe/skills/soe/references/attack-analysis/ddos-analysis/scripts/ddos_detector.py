"""
DDOS检测模块
基于Pcap报文分析，识别各种DDOS攻击类型
"""

from collections import defaultdict
from typing import Dict, List, Any
import ast
import json
import time
from loguru import logger
from geo import locate_ip
from geo.iplib import get_my_external_ip
from utils.traffic_analyzer import TrafficAnalyzer
from utils.packet_analyzer import PacketAnalyzer
from utils.tools import format_analysis_report,get_file_path


# 非 TCP 接口的工具函数
def get_ip_location_tool(ip: str) -> str:
    """获取IP地址的地理位置信息"""
    try:
        result = locate_ip(ip)
        if result is None:
            return f"查询IP地址 {ip} 失败: 无法获取地理位置信息"
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"查询IP地址 {ip} 失败: {str(e)}"


def get_my_ip_tool() -> str:
    """获取当前外部IP地址信息"""
    result = ""
    try:
        ip = get_my_external_ip()
        location = locate_ip(ip)
        ip_result = {
            "ip": ip,
            "location": location
        }
        result = json.dumps(ip_result, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"获取当前IP信息失败: {str(e)}")

    return result

def batch_get_ip_locations_tool(ips: list) -> str:
    """批量获取IP地址地理位置信息（自动去重，串行查询）"""
    start_time = time.time()
    
    # 去重处理，保持原始顺序
    unique_ips = list(dict.fromkeys(ips))
    duplicate_count = len(ips) - len(unique_ips)
    
    # 使用标准的串行查询
    results = {}
    processed_count = 0
    
    for ip in unique_ips:
        try:
            result = locate_ip(ip)
            if result is not None:
                results[ip] = result
                processed_count += 1
            else:
                results[ip] = {"error": f"查询IP {ip} 失败: 无法获取地理位置信息"}
        except Exception as e:
            results[ip] = {"error": f"查询IP {ip} 失败: {str(e)}"}
    
    end_time = time.time()
    
    # 添加统计信息
    summary = {
        "total_requested": len(ips),
        "unique_ips": len(unique_ips),
        "duplicates_removed": duplicate_count,
        "successfully_processed": processed_count,
        "query_time_seconds": round(end_time - start_time, 3),
        "avg_time_per_ip": round((end_time - start_time) / len(unique_ips), 4) if unique_ips else 0,
        "results": results
    }
    
    return json.dumps(summary, indent=2, ensure_ascii=False)


def analyze_ddos_pcap_tool(pcap_file_path: str, white="") -> str:
    """
    分析PCAP文件
    
    Args:
        pcap_file: PCAP文件路径或URL
        
    Returns:
        DDOS检测结果
    """
    result = ""
    try:
        # 使用TrafficAnalyzer读取PCAP文件
        traffic_analyzer = TrafficAnalyzer()
        packets = traffic_analyzer.read_pcap_file(pcap_file_path)
        packet_analyzer = PacketAnalyzer(white=white)
        packet_result =  packet_analyzer.analyze_packets(packets)
        result =  format_analysis_report(analysis_result=packet_result)
    except Exception as e:
        logger.error(f"PCAP文件分析失败: {str(e)}")

    return result

def get_pcap_packet_count(pcap_file_path: str, slice_size=10000) :
    """获取PCAP文件的总包数
    
    Args:
        pcap_file_path: PCAP文件路径
        
    Returns:
        总包数
    """
    traffic_analyzer = TrafficAnalyzer()
    return traffic_analyzer.count_pcap_packets(pcap_file_path, slice_size=slice_size)

def analyze_pcap_slice_tool(pcap_file_path: str, offset_info:dict, max_thread_count = 5, white = ""):
    """分析PCAP文件的指定切片（高效按需读取，不全部加载到内存）
    
    Args:
        pcap_file_path: PCAP文件路径
        offset_info: 偏移信息字典，包含 start_offset, data_size, is_pcapng
        max_thread_count: 最大线程数
        white : 白名单IP
        
    Returns:
        切片分析结果字符串
    """
    result = {}
    packet_analyzer = PacketAnalyzer(white=white)

    if not isinstance(offset_info, dict):
        return result

    start_offset = offset_info.get("start_offset", 0)
    data_size = offset_info.get("data_size", 0)
    is_pcapng = offset_info.get("is_pcapng", False)

    path = pcap_file_path
    try:
        # 使用TrafficAnalyzer获取切片数据
        traffic_analyzer = TrafficAnalyzer(max_thread_count=max_thread_count)
        slice_result = traffic_analyzer.analyze_pcap_slice(path, start_offset=start_offset, data_size=data_size, packet_analyzer=packet_analyzer, is_pcapng=is_pcapng)
        
        if 'error' in slice_result:
            return result
        
        # 如果成功获取切片数据，分析其中的包
        if 'packets' in slice_result:
            packets = slice_result['packets']

            analysis_result = packet_analyzer.analyze_packets(packets)
                
            # 合并切片信息和分析结果
            analysis_result.update(slice_result)
            
            result = analysis_result
        else:
            logger.error("切片结果中未找到数据包")
            
    except Exception as e:
        logger.error(f"PCAP切片分析时发生错误: {str(e)}")

    return result

def merge_slice_analysis_results(slice_results: List[Any]) -> Dict[str, Any]:
    """
    合并多个切片分析结果为一个综合结果
    
    Args:
        slice_results: analyze_pcap_slice_tool 返回结果的列表（可以是字符串或字典）
        
    Returns:
        合并后的分析结果字典，包含：
        - 总体统计信息
        - 合并的时间记录（每种包类型的首次和最后一次出现时间）
        - 合并的攻击检测结果
        - 其他分析信息
    """
    
    if not slice_results:
        logger.warning("切片结果列表为空")
        return {"error": "切片结果列表为空"}
    
    try:
        # 将所有结果转换为字典格式
        parsed_results = []
        for result in slice_results:
            if isinstance(result, str):
                try:
                    # 优先尝试 JSON 解析（与上游 json.dumps 对齐）
                    try:
                        result_dict = json.loads(result)
                    except (json.JSONDecodeError, TypeError):
                        # JSON 解析失败时，使用 ast.literal_eval 安全解析 Python 字面量
                        # （仅支持 dict/list/str/int 等字面量，禁止任何函数调用/属性访问，无 RCE 风险）
                        result_dict = ast.literal_eval(result)
                except (ValueError, SyntaxError):
                    logger.error(f"无法解析字符串结果: {result[:100]}...")
                    continue
            elif isinstance(result, dict):
                result_dict = result
            else:
                logger.warning(f"未知的结果类型: {type(result)}")
                continue
            
            parsed_results.append(result_dict)
        
        if not parsed_results:
            return {"error": "没有有效的结果可以合并"}
        
        # 初始化合并结果
        merged_result = {
            'slice_summaries': [],  # 保存所有切片的摘要
            'summary': {},
            'protocol_stats': {},
            'rates': {},
            'packet_time_records': {},
            'detected_attacks': [],
            'system_anomalies': [],
            'attack_sources': {},
            'attack_type_distribution': defaultdict(int),
            'system_anomaly_distribution': defaultdict(int),
        }
        
        # 1. 合并摘要信息
        total_packets = 0
        total_duration = 0.0
        
        for result in parsed_results:
            slice_summary = result.get('slice_info', {})
            summary = result.get('summary', {})
            
            # 记录切片摘要
            merged_result['slice_summaries'].append({
                'start_offset': slice_summary.get('start_offset'),
                'end_offset': slice_summary.get('end_offset'),
                'packet_count': slice_summary.get('packet_count'),
                'total_packets': summary.get('total_packets', 0),
            })
            
            total_packets += slice_summary.get('packet_count', 0)
            total_duration = max(total_duration, summary.get('duration_seconds', 0))
        
        # 2. 合并协议统计 (平级结构)
        protocol_keys = ['syn_flood', 'ack_flood', 'udp_flood', 'icmp_flood', 'http_flood', 'dns_amplification',
                        'memcached_reflection', 'dns_flood', 'ntp_reflection', 'snmp_amplification', 'ssdp_flood']
        for key in protocol_keys:
            merged_result['protocol_stats'][key] = 0
        
        for result in parsed_results:
            protocol_stats = result.get('protocol_stats', {})
            for key in protocol_keys:
                merged_result['protocol_stats'][key] += protocol_stats.get(key, 0)
        
        # 3. 合并时间记录（平级结构）
        packet_types_with_time = {}
        
        for result in parsed_results:
            time_records = result.get('packet_time_records', {})
            
            for packet_type, record in time_records.items():
                if packet_type not in packet_types_with_time:
                    packet_types_with_time[packet_type] = {
                        'first_seen': None,
                        'last_seen': None,
                        'first_seen_timestamp': None,
                        'last_seen_timestamp': None,
                    }
                
                # 平级处理所有包类型
                first_ts = record.get('first_seen_timestamp')
                last_ts = record.get('last_seen_timestamp')
                
                type_time = packet_types_with_time[packet_type]
                
                if first_ts is not None:
                    if type_time['first_seen_timestamp'] is None:
                        type_time['first_seen_timestamp'] = first_ts
                        type_time['first_seen'] = record.get('first_seen')
                    else:
                        if first_ts < type_time['first_seen_timestamp']:
                            type_time['first_seen_timestamp'] = first_ts
                            type_time['first_seen'] = record.get('first_seen')
                
                if last_ts is not None:
                    if type_time['last_seen_timestamp'] is None:
                        type_time['last_seen_timestamp'] = last_ts
                        type_time['last_seen'] = record.get('last_seen')
                    else:
                        if last_ts > type_time['last_seen_timestamp']:
                            type_time['last_seen_timestamp'] = last_ts
                            type_time['last_seen'] = record.get('last_seen')
                
                if type_time['first_seen_timestamp'] and type_time['last_seen_timestamp']:
                    type_time['duration_seconds'] = type_time['last_seen_timestamp'] - type_time['first_seen_timestamp']
                else:
                    type_time['duration_seconds'] = None
        
        # 将时间记录添加到合并结果中
        for packet_type, time_data in packet_types_with_time.items():
            merged_result['packet_time_records'][packet_type] = time_data
        
        # 4. 合并攻击源统计
        # 首先收集所有国家计数，后面重新计算 top_countries
        attack_sources_country_counts = defaultdict(lambda: defaultdict(int))
        
        for result in parsed_results:
            attack_sources = result.get('attack_sources', {})
            for attack_type, sources_info in attack_sources.items():
                # sources_info 格式: {'total_attacks': N, 'top_countries': [(country, count), ...]}
                if isinstance(sources_info, dict) and 'top_countries' in sources_info:
                    # 从 top_countries 列表中提取国家信息并累加
                    for country, count in sources_info.get('top_countries', []):
                        attack_sources_country_counts[attack_type][country] += count
        
        # 重新计算每个攻击类型的总数和 top_countries
        for attack_type, country_counts in attack_sources_country_counts.items():
            total_attacks = sum(country_counts.values())
            top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            merged_result['attack_sources'][attack_type] = {
                'total_attacks': total_attacks,
                'top_countries': top_countries
            }
        
        # 5. 合并检测到的攻击
        attack_type_count = defaultdict(int)
        for result in parsed_results:
            attacks = result.get('detected_attacks', [])
            for attack in attacks:
                # 避免重复添加相同的攻击
                attack_key = f"{attack['type']}_{attack['severity']}"
                if attack_key not in [f"{a['type']}_{a['severity']}" for a in merged_result['detected_attacks']]:
                    merged_result['detected_attacks'].append(attack)
                attack_type_count[attack['type']] += 1
        
        # 攻击类型分布
        merged_result['attack_type_distribution'] = dict(attack_type_count)
        
        # 6. 合并系统异常
        anomaly_type_count = defaultdict(int)
        for result in parsed_results:
            anomalies = result.get('system_anomalies', [])
            for anomaly in anomalies:
                anomaly_key = f"{anomaly['type']}_{anomaly['severity']}"
                if anomaly_key not in [f"{a['type']}_{a['severity']}" for a in merged_result['system_anomalies']]:
                    merged_result['system_anomalies'].append(anomaly)
                anomaly_type_count[anomaly['type']] += 1
        
        merged_result['system_anomaly_distribution'] = dict(anomaly_type_count)
        
        # 7. 生成最终摘要
        packet_rate = total_packets / total_duration if total_duration > 0 else 0
        
        merged_result['summary'] = {
            'total_packets': total_packets,
            'duration_seconds': total_duration,
            'packet_rate': round(packet_rate, 2),
            'unique_source_ips': 'N/A',  # 无法精确统计（需要原始包数据）
            'unique_destination_ips': 'N/A',
            'slices_count': len(parsed_results),
        }
        
        # 8. 计算速率
        merged_result['rates'] = {
            'syn_rate': round(merged_result['protocol_stats']['syn_flood'] / total_duration, 2) if total_duration > 0 else 0,
            'udp_rate': round(merged_result['protocol_stats']['udp_flood'] / total_duration, 2) if total_duration > 0 else 0,
            'icmp_rate': round(merged_result['protocol_stats']['icmp_flood'] / total_duration, 2) if total_duration > 0 else 0,
            'http_rate': round(merged_result['protocol_stats']['http_flood'] / total_duration, 2) if total_duration > 0 else 0,
            'dns_amplification_rate': round(merged_result['protocol_stats']['dns_amplification'] / total_duration, 2) if total_duration > 0 else 0,
            'dns_flood_rate': round(merged_result['protocol_stats']['dns_flood'] / total_duration, 2) if total_duration > 0 else 0,
        }
        
        # 9. 确定风险等级
        if len(merged_result['detected_attacks']) > 0:
            max_severity = max([a.get('severity', 'medium') for a in merged_result['detected_attacks']], 
                             key=lambda x: {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}.get(x, 1))
            merged_result['risk_level'] = max_severity
        else:
            merged_result['risk_level'] = 'low'
        
        # 10. 合并 API 补充查询结果
        merged_api_enhancement = {
            'queried': 0,
            'succeeded': 0,
            'enhanced_countries': defaultdict(int),
            'still_unknown': 0,
        }
        for result in parsed_results:
            api_enh = result.get('api_enhancement', {})
            merged_api_enhancement['queried'] += api_enh.get('queried', 0)
            merged_api_enhancement['succeeded'] += api_enh.get('succeeded', 0)
            merged_api_enhancement['still_unknown'] += api_enh.get('still_unknown', 0)
            for country, count in api_enh.get('enhanced_countries', {}).items():
                merged_api_enhancement['enhanced_countries'][country] += count
        merged_api_enhancement['enhanced_countries'] = dict(merged_api_enhancement['enhanced_countries'])
        merged_result['api_enhancement'] = merged_api_enhancement
        
        #logger.info(f"成功合并 {len(parsed_results)} 个切片分析结果，总包数: {total_packets}")
        return merged_result
        
    except Exception as e:
        logger.error(f"合并切片分析结果时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"合并失败: {str(e)}"}


def merge_slice_analysis_results_tool(slice_results_json: str) -> str:
    """合并多个PCAP切片分析结果的MCP工具版本
    
    Args:
        slice_results_json: JSON格式的切片分析结果列表字符串
        
    Returns:
        合并后的分析结果JSON字符串
    """
    try:
        # 解析输入的JSON
        slice_results = json.loads(slice_results_json)
        
        if not isinstance(slice_results, list):
            return json.dumps({"error": "输入必须是一个列表"}, ensure_ascii=False)
        
        # 调用合并函数
        merged = merge_slice_analysis_results(slice_results)
        
        # 返回JSON格式的结果
        return json.dumps(merged, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"JSON解析失败: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"合并切片分析结果失败: {str(e)}")
        return json.dumps({"error": f"合并失败: {str(e)}"}, ensure_ascii=False)


def merge_slice_analysis_results_by_json_tool(slice_results_json: list[str]) -> str:
    """合并多个PCAP切片分析结果的MCP工具版本
    
    Args:
        slice_results_json: JSON格式的切片分析结果列表字符串
        
    Returns:
        合并后的分析结果JSON字符串
    """
    try:
        # 解析输入的JSON
        slice_results = slice_results_json
        
        if not isinstance(slice_results, list):
            return json.dumps({"error": "输入必须是一个列表"}, ensure_ascii=False)
        
        # 调用合并函数
        merged = merge_slice_analysis_results(slice_results)
        
        # 返回JSON格式的结果
        return json.dumps(merged, indent=2, ensure_ascii=False)
        
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"JSON解析失败: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"合并切片分析结果失败: {str(e)}")
        return json.dumps({"error": f"合并失败: {str(e)}"}, ensure_ascii=False)


def format_analysis_report_tool(analysis_result_json: str) -> str:
    """格式化分析报告的MCP工具版本
    
    Args:
        analysis_result_json: JSON格式的分析结果字符串
        
    Returns:
        格式化后的可读性报告字符串
    """
    try:
        # 解析输入的JSON
        analysis_result = json.loads(analysis_result_json)
        
        if not isinstance(analysis_result, dict):
            return f"错误: 输入必须是一个字典"
        
        # 调用格式化函数
        report = format_analysis_report(analysis_result)
        
        return report
        
    except json.JSONDecodeError as e:
        return f"JSON解析失败: {str(e)}"
    except Exception as e:
        logger.error(f"格式化分析报告失败: {str(e)}")
        return f"报告格式化失败: {str(e)}"
    
