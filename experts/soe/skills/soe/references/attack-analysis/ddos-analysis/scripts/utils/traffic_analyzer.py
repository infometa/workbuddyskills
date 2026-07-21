"""
流量分析模块
提供更详细的流量统计功能和PCAP文件处理能力
"""

import os
from collections import defaultdict
from re import S
from typing import Any, Dict, Optional
from threading import Thread, Lock
from queue import Queue
from scapy.all import IP, TCP, rdpcap, Ether
from utils.tools import get_file_path
from utils.packet_analyzer import PacketAnalyzer
from utils import pcap_url

MAX_THREAD_COUNT = 5

class TrafficAnalyzer:
    """流量分析器，提供更详细的流量统计和PCAP文件处理功能"""
    
    def __init__(self, max_thread_count=MAX_THREAD_COUNT):
        """初始化流量分析器"""
        self.max_thread_count = max_thread_count
    
    def _detect_port_scan(self, packets) -> bool:
        """检测端口扫描行为"""
        if len(packets) < 10:  # 数据包太少，不进行检测
            return False
            
        src_ports = defaultdict(set)
        
        for packet in packets:
            if packet.haslayer(IP) and packet.haslayer(TCP):
                ip_layer = packet[IP]
                tcp_layer = packet[TCP]
                
                # 记录每个源IP访问的目的端口
                src_ports[ip_layer.src].add(tcp_layer.dport)
        
        # 如果某个源IP在短时间内访问了大量不同端口，可能是端口扫描
        for src_ip, ports in src_ports.items():
            if len(ports) > 20:  # 访问超过20个不同端口
                return True
                
        return False
    
    def read_pcap_file(self, pcap_file: str):
        """
        读取PCAP文件
        
        Args:
            pcap_file: PCAP文件路径或URL
            
        Returns:
            数据包列表
        """
        try:
            path = get_file_path(pcap_file)
            packets = rdpcap(path)
            return packets
        except Exception as e:
            raise Exception(f'PCAP文件读取失败: {str(e)}')
    
    def count_pcap_packets(self, pcap_file_path: str, slice_size=10000):
        """高效统计PCAP/PCAPNG文件中的报文数量（只返回总数量，内存优化）
        
        Args:
            pcap_file_path: PCAP/PCAPNG文件路径或URL
            
        Returns:
            包含报文总数量的字典，格式: {"data_size": int} 或 {"error": str}
        """
        try:
            packet_count = 0
            npos = 0
            lst_offset = [0]  # pcapng 没有固定的文件头大小，从0开始
            
            # 使用 UniversalReader 支持 pcap 和 pcapng 格式
            pcap_reader = pcap_url.UniversalReader(pcap_file_path)
            
            # 检测文件格式
            is_pcapng = type(pcap_reader).__module__ == 'dpkt.pcapng'
            
            # 获取 magic（仅 pcap 格式支持）
            magic = getattr(pcap_reader, 'magic', 0) if hasattr(pcap_reader, 'getmagic') else 0
            if hasattr(pcap_reader, 'getmagic'):
                magic = pcap_reader.getmagic()

            # 简单计数，不记录任何其他信息
            for _ in pcap_reader:
                packet_count += 1
                npos += 1
                if npos >= slice_size:
                    # pcapng 不支持 getoffset，使用包计数作为偏移
                    if hasattr(pcap_reader, 'getoffset'):
                        lst_offset.append(pcap_reader.getoffset())
                    else:
                        lst_offset.append(packet_count)
                    npos = 0
            
            if npos > 0:
                if hasattr(pcap_reader, 'getoffset'):
                    lst_offset.append(pcap_reader.getoffset())
                else:
                    lst_offset.append(packet_count)

            lst_result = []
            for index in range(len(lst_offset) - 1):
                offset_info = {
                    "start_offset": lst_offset[index], 
                    "data_size": lst_offset[index + 1] - lst_offset[index],
                    "is_pcapng": is_pcapng  # 添加格式标识到每个偏移信息中
                }
                lst_result.append(offset_info)

            return {
                "packet_count": packet_count, 
                "offsets": lst_result, 
                "magic": magic,
                "is_pcapng": is_pcapng
            }
            
        except Exception as e:
            return {"error": f"PCAP/PCAPNG 读取失败: {str(e)}"}

    def analyze_pcap_slice(self, pcap_file_path: str, start_offset: int = 1, data_size: int = 2000, packet_analyzer :PacketAnalyzer = None, is_pcapng: bool = False) -> Dict[str, any]:
        """分析PCAP文件的指定切片（高效按需读取，不全部加载到内存）
        
        优先使用dpkt进行流式读取（内存效率最高），备选scapy
        
        Args:
            pcap_file_path: PCAP文件路径
            start_offset: 起始报文编号（从1开始），对于pcapng是包索引号
            data_size: 要分析的报文数量
            is_pcapng: 是否为pcapng格式（pcapng需要按包索引跳过，而不是字节偏移）
            
        Returns:
            切片分析结果字典
        """
        try:
            # 获取文件大小
            if pcap_file_path.startswith(('http://', 'https://', 'ftp://')):
                # 网络文件：通过HEAD请求获取大小
                import urllib.request
                try:
                    req = urllib.request.Request(pcap_file_path, method='HEAD')
                    with urllib.request.urlopen(req) as response:
                        file_size = int(response.headers.get('Content-Length', 0))
                except:
                    file_size = 0
            else:
                # 本地文件：直接获取文件大小
                file_size = os.path.getsize(pcap_file_path) if os.path.exists(pcap_file_path) else 0
            
            file_size_mb = file_size / (1024 * 1024)
            
            # 分析切片
            result: Any = self._analyze_pcap_slice(pcap_file_path, start_offset, data_size, packet_analyzer=packet_analyzer, is_pcapng=is_pcapng)
            
            result["file_size_mb"] = round(file_size_mb, 2)
            result["file_path"] = pcap_file_path
            
            return {
                "slice_info": result,
                "packets": result.pop("packets", [])
            }
            
        except Exception as e:
            return {"error": f"PCAP切片分析时发生错误: {str(e)}"}

    def _analyze_pcap_slice(self, pcap_file_path: str, start_offset: int, data_size: int, packet_analyzer: Optional[PacketAnalyzer] = None, is_pcapng: bool = False):
        """使用dpkt进行流式读取PCAP/PCAPNG文件切片（内存效率最高）
        
        Args:
            pcap_file_path: PCAP/PCAPNG文件路径或URL
            start_offset: 起始位置（对于pcap是字节偏移，对于pcapng是包索引）
            data_size: 要读取的大小（对于pcap是字节数，对于pcapng是包数量）
            packet_analyzer: 可选的包分析器
            is_pcapng: 是否为pcapng格式
        """
        try:
            # 使用 UniversalReader 支持 pcap 和 pcapng 格式
            pcap_reader = pcap_url.UniversalReader(pcap_file_path)

            # 定义包处理函数：将dpkt原始包转换为Scapy Ether对象，并保留时间戳
            def dpkt_packet_processor(ts_buf):
                ts, buf = ts_buf
                try:
                    ether_packet = Ether(buf)
                    # 将PCAP包的时间戳附加到Scapy包对象
                    ether_packet.time = ts
                    return ether_packet
                except Exception:
                    return (ts, buf)
                
            # 使用通用方法读取切片
            read_result = self._read_pcap_slice(
                pcap_file_path,
                pcap_reader,
                start_offset,
                data_size,
                packet_processor=dpkt_packet_processor,
                packet_analyzer=packet_analyzer,
                is_pcapng=is_pcapng
            )
            
            return {
                "start_offset": start_offset,
                "requested_count": data_size,
                "packet_count": read_result.get("packet_count", 0),
                "end_offset": start_offset + data_size - 1,
                "packets": read_result.get("packets", [])
            }

        except Exception as e:
            return {"error": f"读取文件失败: {str(e)}"}
    
    def _packet_processor_worker(self, task_queue: Queue, result_queue: Queue, packet_processor=None, packet_analyzer :PacketAnalyzer = None):
        """包处理工作线程
        
        从任务队列读取包，进行处理，结果放入结果队列
        """
        while True:
            task = task_queue.get()
            
            # 检查是否为终止信号
            if task is None:
                break
            
            packet_index, raw_packet = task
            
            # 处理包
            if packet_processor:
                processed_packet = packet_processor(raw_packet)
            else:
                processed_packet = raw_packet


            if packet_analyzer:
                packet_analyzer.process_packet(processed_packet)
            else:
                result_queue.put((packet_index, processed_packet))
            task_queue.task_done()
    
    def _read_pcap_slice(self, url, reader_iter, start_offset: int, data_size: int, packet_processor=None, packet_analyzer=None, num_threads: int = None, is_pcapng: bool = False):
        """通用PCAP切片读取方法（支持多线程处理）
        
        Args:
            url: 文件URL或路径
            reader_iter: 包阅读器迭代器
            start_offset: 起始位置（对于pcap是字节偏移，对于pcapng是包索引）
            data_size: 要读取的大小（对于pcap是字节数，对于pcapng是包数量）
            packet_processor: 可选的包处理函数，用于处理每个包
            packet_analyzer: 可选的包分析器
            num_threads: 处理线程数（默认使用实例的max_thread_count）
            is_pcapng: 是否为pcapng格式
            
        Returns:
            处理后的包列表
        """
        result: dict[str, Any | list[Any]] = {"packets": [], "data_size": 0}

        if num_threads is None:
            num_threads = self.max_thread_count
            
        packets = []
        current_packet = 0
        
        # 如果没有包处理器且没有包分析器，使用单线程方式（性能更优）
        if packet_processor is None and packet_analyzer is None:
            for raw_packet in reader_iter:
                current_packet += 1
                
                if current_packet < start_offset:
                    continue
                
            result["packets"].extend(packets)

            return result
        
        # 使用多线程处理
        task_queue = Queue(maxsize=num_threads * 2)
        result_queue = Queue()
        
        # 启动工作线程
        workers = []
        for _ in range(num_threads):
            worker = Thread(
                target=self._packet_processor_worker,
                args=(task_queue, result_queue, packet_processor, packet_analyzer),
                daemon=True
            )
            worker.start()
            workers.append(worker)
        
        # 收集结果的字典（用于排序）
        result_dict = {}

        # 读取并分发包到任务队列
        reading_done = False
        packet_index = 0
        
        # 根据格式选择不同的数据源
        if is_pcapng:
            # pcapng格式：使用 reader_iter 按包索引跳过
            # start_offset 是包索引（从0开始），data_size 是包数量
            pcap_datas = pcap_url.PcapngSliceIterator(reader_iter, skip_count=start_offset, read_count=data_size)
        else:
            # pcap格式：使用字节范围读取
            pcap_datas = pcap_url.PcapData(url=url, start=start_offset, size=data_size)
        
        while True:
            while not reading_done and task_queue.qsize() < num_threads * 2:
                try:
                    raw_packet = next(pcap_datas)
                    
                    # 将包分配给工作线程
                    task_queue.put((packet_index, raw_packet))
                    packet_index += 1
                        
                except StopIteration:
                    reading_done = True
                    break
            
            # 收集处理结果
            while not result_queue.empty():
                idx, processed_packet = result_queue.get()
                result_dict[idx] = processed_packet
            
            # 如果读取完成且队列为空，退出循环
            if reading_done and task_queue.empty():
                break
        
        # 等待所有任务完成
        task_queue.join()
        
        # 收集剩余的结果
        while not result_queue.empty():
            idx, processed_packet = result_queue.get()
            result_dict[idx] = processed_packet
        
        # 停止工作线程
        for _ in range(num_threads):
            task_queue.put(None)
        
        for worker in workers:
            worker.join(timeout=5)
        
        # 按索引顺序返回包
        result["packets"] = [result_dict[i] for i in sorted(result_dict.keys())]
        result["packet_count"] = packet_index
        
        return result
    