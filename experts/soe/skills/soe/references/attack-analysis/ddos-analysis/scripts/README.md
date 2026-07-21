# PCAP DDoS 检测 MCP 服务器

一个高效的 PCAP 文件分析和 DDoS 攻击检测工具，支持 GeoIP 定位、流量统计和分布式切片分析。

## 功能特性

### 核心功能

1. **IP 地理位置查询**
   - 单个 IP 查询
   - 批量 IP 查询（自动去重）
   - 查询缓存和统计

2. **PCAP 文件分析**
   - 高效的分块读取（每块 2MB）
   - 双内存缓冲异步处理
   - 支持本地文件和网络 URL
   - 自动处理块边界不完整的数据包

3. **DDoS 攻击检测**
   - 多协议攻击识别（UDP、TCP、ICMP）
   - 攻击源国家分布统计
   - 风险等级评估
   - 切片分析和结果合并

4. **高效的流量统计**
   - 流式处理，内存占用低
   - 协议分布统计
   - 时间序列分析
   - 异常流量检测

## 安装

### 依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- `dpkt`: PCAP 文件解析
- `loguru`: 日志管理
- `mcp`: MCP 服务器框架
- GeoIP: 嵌入式二进制数据（scripts/geo/ip_data_embedded.py，自动生成）+ API 补充查询（scripts/geo/api_lookup.py）

### 配置

1. GeoIP 数据（已内置为嵌入式二进制数据，无需外部文件）：
```bash
# IP-国家映射已嵌入 scripts/geo/ip_data_embedded.py（自包含）
# 311,728 条记录，250 个国家/地区，1.66 MB
# 无需从外部下载任何数据库文件
```

2. API 补充查询（可选，自动启用）：
```bash
# 当嵌入式数据库中找不到 IP 归属国时，自动通过在线 API 补充查询
# 采用 TOP N 策略：只查询出现频率最高的 N 个未知 IP（默认 100）
# 多 API 端点容灾（全部 HTTPS）：
#   ip.sb（首选）→ pconline（国内精度高）→ country.is（兜底）
# 无需 API Key，无需额外配置
```

3. 配置环境变量或修改配置文件

## 使用方式

### 1. MCP 服务器模式（推荐）

启动 MCP 服务器：
```bash
python3 main.py
```

然后通过 MCP 客户端调用工具。

### 2. 命令行模式

#### IP 查询
```bash
# 查询单个 IP
python3 main.py ip --query 8.8.8.8

# 查询当前外部 IP
python3 main.py ip --myip

# 批量查询 IP
python3 main.py ip --batch 8.8.8.8 1.1.1.1 114.114.114.114
```

#### PCAP 分析
```bash
# 统计 PCAP 文件中的数据包数量
python3 main.py ddos --count /path/to/file.pcap

# 分析整个 PCAP 文件中的 DDoS 攻击
python3 main.py ddos --analyze /path/to/file.pcap

# 分析指定切片
python3 main.py ddos --slice /path/to/file.pcap --start 1 --packets 2000
```

## API 文档

### IP 查询工具

#### `get_ip_location(ip: str) -> str`
获取 IP 地址的地理位置信息。

**参数：**
- `ip`: IP 地址字符串

**返回：**
- JSON 格式的位置信息

#### `get_my_ip() -> str`
获取当前外部 IP 地址。

**返回：**
- 外部 IP 地址

#### `batch_get_ip_locations(ips: list[str]) -> dict`
批量查询多个 IP 地址的位置（自动去重）。

**参数：**
- `ips`: IP 地址列表

**返回：**
- 包含去重统计和查询结果的字典

### PCAP 分析工具

#### `count_pcap_packets(pcap_file_path: str) -> str`
高效统计 PCAP 文件中的数据包数量。

使用分块读取和双内存缓冲方式处理大文件，内存占用极低。

**参数：**
- `pcap_file_path`: PCAP 文件路径或 URL

**返回：**
```json
{
  "packet_count": 230288,
  "offsets": [24, 1054912, 2107420, ...],
  "magic": 3569595041
}
```

**特点：**
- 第 1 次读取从文件偏移 24 字节开始（跳过 PCAP 文件头）
- 每次预读取 2MB 的数据为一个块
- 后续依次读取 2MB 的数据，直到读取完毕
- 使用双内存切换：处理第 n 块时异步读取第 n+1 块
- 自动处理块边界不完整的数据包，拼接到下一个块

#### `analyze_pcap_slice(pcap_file_path: str, offset_info: dict, max_thread_count: int = 5) -> str`
分析 PCAP 文件的指定切片。

**参数：**
- `pcap_file_path`: PCAP 文件路径
- `offset_info`: 包含起始位置和大小的字典
- `max_thread_count`: 最大线程数

**返回：**
- DDoS 分析结果 JSON

#### `analyze_ddos_pcap(pcap_file_path: str) -> str`
分析整个 PCAP 文件中的 DDoS 攻击。

**参数：**
- `pcap_file_path`: PCAP 文件路径

**返回：**
- 详细的 DDoS 攻击分析报告

#### `merge_slice_analysis_results(slice_results_json: str) -> str`
合并多个 PCAP 切片的分析结果。

**参数：**
- `slice_results_json`: JSON 格式的切片结果字符串

**返回：**
- 合并后的综合分析结果

#### `merge_slice_analysis_results_by_json(slice_results_json: list[str]) -> str`
合并多个 PCAP 切片分析结果（列表格式）。

**参数：**
- `slice_results_json`: JSON 格式的切片结果列表

**返回：**
- 合并后的综合分析结果

#### `format_analysis_report(analysis_result_json: str) -> str`
将分析结果格式化为可读的报告。

**参数：**
- `analysis_result_json`: 分析结果 JSON 字符串

**返回：**
- 格式化的可读性报告

## 核心实现

### 1. `count_pcap_packets` - 分块读取优化

**关键特性：**
- **分块读取**：每次读取 2MB，避免大文件一次性加载
- **双内存缓冲**：主线程处理 buffer_a，后台线程异步读取 buffer_b
- **块边界处理**：自动检测和处理块边界不完整的数据包
- **线程同步**：使用 Event 和 Lock 确保线程安全

**处理流程：**
```
1. 读取第 1 块数据到 buffer_a（24 字节之后）
2. 启动后台线程读取第 2 块到 buffer_b
3. 主线程处理 buffer_a 中的数据包
4. 检测块边界是否有不完整数据包
5. buffer_a 处理完后，切换 buffer_b → buffer_a
6. 启动新线程读取第 3 块到 buffer_b
7. 重复直到所有数据处理完毕
```

### 2. PCAP 数据包处理

**PcapData 类特性：**
- 支持从 URL 或本地数据初始化
- 自动从前 16 字节提取 PCAP 魔数
- 支持大端和小端字节序自动识别
- 实现迭代器协议，支持 `next()` 和 `for` 循环

**数据包迭代：**
```python
pcap_data = PcapData(url='http://example.com/file.pcap')
for timestamp, packet_data in pcap_data:
    # 处理每个数据包
    pass
```

### 3. DDoS 检测算法

**攻击类型识别：**
- **UDP Flood**: 检测单个源向多个目标发送大量 UDP 包
- **TCP Flood**: 检测 TCP SYN/ACK 异常
- **ICMP Flood**: 检测 ICMP Echo Request 异常
- **DNS Amplification**: 检测 DNS 响应异常

**风险评级：**
- **低**：可疑流量
- **中**：明确的攻击信号
- **高**：多个攻击特征叠加

## 性能优化

### 内存优化
- 分块处理，避免加载整个文件
- 双内存缓冲，实现异步 I/O
- 流式数据包处理，即用即释

### 网络优化
- 支持 HTTP Range 请求
- 自动重试失败请求
- SSL/TLS 证书验证禁用（用于自签名证书）

### 并发优化
- 多线程切片分析
- 后台异步读取
- 线程安全的缓冲区管理

## 故障排除

### SSL 证书错误
```
SSL: CERTIFICATE_VERIFY_FAILED
```
**解决方案**：自动使用无验证的 SSL 上下文（已默认启用）

### 403 Forbidden 错误
```
urllib.error.HTTPError: HTTP Error 403: Forbidden
```
**原因**：某些服务器禁止没有 User-Agent 的请求
**解决方案**：已添加标准 User-Agent（已默认启用）

### 数据包不完整警告
```
分块处理中检测到不完整的数据包
```
**原因**：块边界恰好在数据包中间
**解决方案**：自动拼接到下一个块继续处理

## 文件结构

```
pcab_ddos-mcp-server/
├── main.py                 # 主入口和 MCP 服务器
├── ddos_detector.py        # DDoS 检测逻辑
├── utils/
│   ├── pcap_url.py        # PCAP 文件读取和处理
│   ├── traffic_analyzer.py # 流量分析
│   └── geo/              # GeoIP 查询（嵌入式数据 + API 补充）
│       ├── iplib.py     # IP-国家查询（二分查找，嵌入式数据）
│       ├── ip_data_embedded.py # 嵌入式 IP-Country 二进制数据（自包含）
│       └── api_lookup.py # API 补充查询模块（ip.sb/pconline/country.is 多端点容灾 + TOP N 策略）
├── requirements.txt        # 依赖列表
└── README.md              # 本文档
```

## 开发指南

### 添加新的攻击检测

在 `ddos_detector.py` 中添加新的检测函数：

```python
def detect_new_attack(packet_data):
    """检测新类型的攻击"""
    # 实现检测逻辑
    pass
```

### 扩展 GeoIP 功能

修改 `utils/geo/iplib.py` 中的查询逻辑

API 补充查询配置见 `scripts/geo/api_lookup.py`（端点、速率限制、TOP N 阈值）

### 性能调优

- 调整 `count_pcap_packets` 中的 `chunk_size` 参数（默认 2MB）
- 调整线程数 `max_thread_count`（默认 5）

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request

## 支持

如有问题，请联系开发团队或提交 Issue
