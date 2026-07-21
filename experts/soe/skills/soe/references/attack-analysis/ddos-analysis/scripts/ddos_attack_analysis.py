#!/usr/bin/env python3
"""
analyze_pcap_slice_tool 使用示例
展示如何调用和处理返回值
"""

import sys
import os
import time
import ast
import json

from dpkt import pcap
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ddos_detector import analyze_pcap_slice_tool, get_pcap_packet_count, merge_slice_analysis_results_tool, format_analysis_report_tool, analyze_ddos_pcap_tool
import re

def extract_dict_from_string(string_repr):
    """从字符串表示中提取字典数据"""
    if isinstance(string_repr, dict):
        return string_repr

    # 尝试 JSON 解析
    try:
        return json.loads(string_repr)
    except (json.JSONDecodeError, TypeError):
        pass

    # 尝试 Python 对象解析（处理单引号等情况）
    try:
        return ast.literal_eval(string_repr)
    except (ValueError, SyntaxError):
        pass

    # 如果都失败，返回原始字符串
    return {"raw": string_repr}


def read_pcap_by_slices(pcap_file, slice_size=20000):
    """使用循环分片读取完整的 PCAP 文件
    
    Args:
        pcap_file: PCAP 文件路径
        slice_size: 每个切片的包数
        
    Yields:
        分析结果字典
    """
    
    # 记录总体开始时间
    total_start_time = time.time()
    
    # 获取文件总包数
    try:
        count_start_time = time.time()
        result = get_pcap_packet_count(pcap_file, slice_size=10000)
        if "error" in result:
            #print(f"❌ 获取包数失败: {result.get('error', '')}")
            return
        total_packets =  result.get("packet_count", 0)
        offsets = result.get("offsets", [])
        count_time = time.time() - count_start_time
        #print(f"📊 文件总包数: {total_packets} (耗时: {count_time:.3f}s)")
    except Exception as e:
        #print(f"❌ 获取包数失败: {e}")
        return
    
    # 计算需要读取的切片数
    slice_count = (total_packets + slice_size - 1) // slice_size
    #print(f"🔄 需要读取 {slice_count} 个切片\n")

    #slice_count = 1
    # 记录切片读取统计
    slice_times = []
    
    nlen = len(offsets)

    # 循环读取每个切片
    #for slice_index in range(slice_count):
    for offset_index in range(nlen):
        offset_info = offsets[offset_index]

        start_offset = offset_info.get("start_offset", 0)
        data_size = offset_info.get("data_size", 0)
        
        end_offset = start_offset + data_size

        slice_start_time = time.time()
        
        #print(f"🔹 切片 {offset_index + 1}/{nlen - 1}: 包起止位置 {start_offset} - {end_offset} ({data_size} 大小)", end="")
        
        try:
            result_str = analyze_pcap_slice_tool(pcap_file, offset_info=offset_info, white= "120.27.173.114")
            result_dict = extract_dict_from_string(result_str)
            
            slice_time = time.time() - slice_start_time
            slice_times.append(slice_time)
            
            packet_count = result_dict.get("slice_info", {}).get("packet_count", 0)
            #print(f" - 实际分析包数：{packet_count} [✓ {slice_time:.3f}s]")
            yield result_dict
        except Exception as e:
            slice_time = time.time() - slice_start_time
            #print(f" [✗ 错误: {e}]")
            continue
    
    # 打印执行时间统计
    total_time = time.time() - total_start_time

def main():
    """主测试函数"""

    # 分析模式选择：
    # mode = "full" - 直接分析整个文件（与 main.py 行为一致）
    # mode = "slice" - 分片分析（内存优化，适合大文件）
    mode = "full"

    pcap_file = sys.argv[1]
    #pcap_file = "https://example.com/sample.cap"  # 示例 URL，不要写入带签名、token 或临时凭据的真实地址
    white = ""  # 白名单IP，逗号分隔

    try:
        if mode == "full":
            # 直接分析整个文件（与 main.py 行为一致）
            result_str = analyze_ddos_pcap_tool(pcap_file, white=white)
            print(result_str)
        else:
            # 分片分析（内存优化，适合大文件）
            lst_result = []

            for result_dict in read_pcap_by_slices(pcap_file, slice_size=20000):

                if result_dict:
                    lst_result.append(result_dict)

            # 合并切片结果
            merged_result = merge_slice_analysis_results_tool(json.dumps(lst_result))
            # 格式化分析报告
            text = format_analysis_report_tool(merged_result)

            print(text)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
