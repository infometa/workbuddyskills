#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能日志分析工具 - 日志分析与排查技能配套工具

功能：
1. 智能去重：识别重复模式，只保留代表性样本
2. 日志压缩：提取关键信息，控制 token 消耗
3. 异常聚类：将相似错误自动聚合
4. 时间线分析：按时间展示关键事件
5. 根因定位：通过上下文关联重构问题链路
6. 时间范围验证：确认目标时间是否在日志覆盖范围内
7. 事件链分析：追踪进程状态变化，重构问题链路

适用场景：
- 软件线上故障排查
- 批量异常排查
- 性能瓶颈排查
- 日志量超限处理
- 进程状态排查（如 服务异常退出）

用法:
    python3 smart_log.py overview --file "app.log"
    python3 smart_log.py validate --file "app.log" --time "15:40"
    python3 smart_log.py search --file "app.log" --keyword "error" --dedupe
    python3 smart_log.py errors --file "app.log" --top 10
    python3 smart_log.py timeline --file "app.log" --start "15:40" --end "15:50"
    python3 smart_log.py chain --file "app.log" --events "start,stop,init,exit"
    python3 smart_log.py trace --file "app.log" --trace-id "req-123"
"""

import argparse
import re
import os
import sys
import hashlib
from collections import Counter, defaultdict
from typing import Optional, List, Dict, Tuple, Generator, Any
from dataclasses import dataclass, field
from datetime import datetime


# ==================== 常量定义 ====================

# 常见日志格式的时间戳正则（按优先级排列，先匹配先返回）
TIME_PATTERNS = [
    # glog 格式 (Google logging) - Go 程序常用格式
    # [IWEF]mmdd hh:mm:ss.uuuuuu threadid file:line] msg
    r'^(?P<glevel>[IWEF])(?P<date>\d{4}) (?P<time>\d{2}:\d{2}:\d{2}\.\d+)',
    # [LEVEL][HH:MM:SS.mmm] - Windows 日志格式（level 前可能有空格，如 "[ INFO]"）
    r'\[\s*(?P<level>[A-Z]+)\]\[(?P<time>\d{1,2}:\d{2}:\d{2}\.\d+)\]',
    # [YYYY-MM-DD HH:MM:SS] [LEVEL]
    r'\[(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\]\s*\[(?P<level>[A-Z]+)\]',
    # YYYY-MM-DD HH:MM:SS,mmm LEVEL
    r'(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})[,.]?\d*\s+(?P<level>[A-Z]+)',
    # HH:MM:SS.mmm [LEVEL]
    r'(?P<time>\d{2}:\d{2}:\d{2})[.,]?\d*\s+\[?(?P<level>[A-Z]+)\]?',
    # ISO format
    r'(?P<date>\d{4}-\d{2}-\d{2})T(?P<time>\d{2}:\d{2}:\d{2})',
    # 通用时间格式 HH:MM:SS
    r'(?P<time>\d{2}:\d{2}:\d{2})',
]

COMPILED_PATTERNS = [re.compile(p) for p in TIME_PATTERNS]

# 需要过滤的低价值日志模式
LOW_VALUE_PATTERNS = [
    r'^\s*$',  # 空行
    r'^[-=]{10,}',  # 分隔线
    r'heartbeat|ping|keepalive',  # 心跳日志
    r'DEBUG.*entering|leaving|called',  # 函数进出日志
    r'TRACE',  # 跟踪日志
]

COMPILED_LOW_VALUE = [re.compile(p, re.IGNORECASE) for p in LOW_VALUE_PATTERNS]

# 预设关键词组（用于快速排障）
PRESET_KEYWORDS = {
    'disconnect': r'disconnect|reconnect|close[d]?|reset|broken|drop|timeout|refuse[d]?|dead|lost|abort|shutdown|detach|bye',
    'error': r'error|fail(?:ed|ure)?|panic|fatal|crash|exception',
    'network': r'timeout|refuse|reset|broken|drop|unreachable|dns|proxy|tls|ssl|cert',
    'auth': r'auth|denied|unauthorized|forbidden|token|login|logout|expire',
}

# 错误级别权重（含 glog 单字母级别映射）
LEVEL_WEIGHTS = {
    'FATAL': 100,
    'CRITICAL': 90,
    'ERROR': 80,
    'WARN': 60,
    'WARNING': 60,
    'INFO': 30,
    'DEBUG': 10,
    'TRACE': 5,
}

# glog 单字母级别 → 标准级别名
GLOG_LEVEL_MAP = {
    'I': 'INFO',
    'W': 'WARN',
    'E': 'ERROR',
    'F': 'FATAL',
}


# ==================== 数据类 ====================

@dataclass
class LogLine:
    """日志行"""
    line_num: int
    content: str
    time: Optional[str] = None
    level: Optional[str] = None
    date: Optional[str] = None
    
    @property
    def importance(self) -> int:
        """计算日志重要性"""
        return LEVEL_WEIGHTS.get(self.level or '', 20)


@dataclass
class LogPattern:
    """日志模式（用于去重）"""
    pattern_hash: str
    template: str
    count: int = 1
    first_time: Optional[str] = None
    last_time: Optional[str] = None
    first_line: int = 0
    last_line: int = 0
    samples: List[str] = field(default_factory=list)
    level: Optional[str] = None
    
    def add_occurrence(self, log_line: LogLine):
        """添加一次出现"""
        self.count += 1
        if log_line.time:
            if not self.first_time:
                self.first_time = log_line.time
            self.last_time = log_line.time
        self.last_line = log_line.line_num
        # 保留最多 3 个样本
        if len(self.samples) < 3 and log_line.content not in self.samples:
            self.samples.append(log_line.content)


@dataclass 
class ErrorCluster:
    """错误聚类"""
    error_type: str
    count: int = 0
    first_time: Optional[str] = None
    last_time: Optional[str] = None
    samples: List[str] = field(default_factory=list)
    stack_trace: Optional[str] = None


# ==================== 工具函数 ====================

def detect_log_format(sample_lines: List[str]) -> Optional[re.Pattern]:
    """检测日志格式"""
    for pattern in COMPILED_PATTERNS:
        match_count = sum(1 for line in sample_lines if pattern.search(line))
        if match_count >= len(sample_lines) * 0.2:  # 至少 20% 匹配
            return pattern
    return None


def parse_time(time_str: str) -> Optional[Tuple[int, int, int]]:
    """解析时间字符串，返回 (hour, minute, second)"""
    if not time_str:
        return None
    
    parts = time_str.replace('.', ':').split(':')
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2].split('.')[0]) if len(parts) > 2 else 0
        return (hour, minute, second)
    except (ValueError, IndexError):
        return None


def time_to_seconds(t: Tuple[int, int, int]) -> int:
    """时间转换为秒数"""
    return t[0] * 3600 + t[1] * 60 + t[2]


def time_in_range(time_str: str, start: Optional[Tuple[int, int, int]], 
                  end: Optional[Tuple[int, int, int]]) -> bool:
    """检查时间是否在范围内"""
    t = parse_time(time_str)
    if not t:
        return True  # 无法解析时间则不过滤
    
    t_sec = time_to_seconds(t)
    
    if start and time_to_seconds(start) > t_sec:
        return False
    if end and time_to_seconds(end) < t_sec:
        return False
    return True


def read_file_lines(filepath: str) -> Generator[Tuple[int, str], None, None]:
    """逐行读取文件，支持多种编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding, errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    yield line_num, line.rstrip('\r\n')
            return
        except UnicodeDecodeError:
            continue
    
    # 最后使用 latin-1（不会失败）
    with open(filepath, 'r', encoding='latin-1') as f:
        for line_num, line in enumerate(f, 1):
            yield line_num, line.rstrip('\r\n')


def parse_log_line(line: str, line_num: int, pattern: Optional[re.Pattern]) -> LogLine:
    """解析单行日志"""
    log_line = LogLine(line_num=line_num, content=line)
    
    if pattern:
        match = pattern.search(line)
        if match:
            groups = match.groupdict()
            log_line.time = groups.get('time')
            # glog 格式：单字母级别 (I/W/E/F) 需映射为标准级别名
            glevel = groups.get('glevel')
            if glevel:
                log_line.level = GLOG_LEVEL_MAP.get(glevel, glevel)
            else:
                raw_level = groups.get('level')
                log_line.level = raw_level.upper() if raw_level else None
            log_line.date = groups.get('date')
    
    return log_line


def normalize_log_for_dedup(content: str) -> str:
    """
    标准化日志内容用于去重
    将变化的部分（数字、ID、IP、UUID 等）替换为占位符
    """
    normalized = content

    # 替换 IP 地址（含可选端口）
    normalized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?', '<IP>', normalized)

    # 替换 glog 日期前缀 (I0617/W0617/E0617/F0617)
    normalized = re.sub(r'[IWEF]\d{4}\s', '<GD> ', normalized)

    # 替换完整 UUID (8-4-4-4-12 格式)
    normalized = re.sub(
        r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}',
        '<UUID>', normalized
    )

    # 替换 hex 串 (4+ 字符，UUID 残留或独立 hex)
    # 要求至少包含一个数字，避免误匹配 dead/face/beef 等纯字母英文单词
    # 5-7 字符区间也被覆盖，消除原先 4 字符和 8+ 字符之间的缺口
    normalized = re.sub(r'\b(?=[a-fA-F0-9]{4,}\b)(?=.*\d)[a-fA-F0-9]{4,}\b', '<ID>', normalized)

    # 替换时间戳
    normalized = re.sub(r'\d{2}:\d{2}:\d{2}[.,]?\d*', '<TIME>', normalized)
    normalized = re.sub(r'\d{4}-\d{2}-\d{2}', '<DATE>', normalized)

    # 替换端口
    normalized = re.sub(r':\d{2,5}(?=\s|$|[,\]])', ':<PORT>', normalized)

    # 替换所有剩余数字（包括 1-3 位短数字）
    normalized = re.sub(r'\b\d+\b', '<N>', normalized)

    # 替换文件路径中的变化部分
    normalized = re.sub(r'/tmp/[^\s]+', '/tmp/<PATH>', normalized)
    normalized = re.sub(r'\\temp\\[^\s]+', '\\temp\\<PATH>', normalized)

    # 替换 JSON 字符串值 ("key":"value" → "key":"<S>")
    normalized = re.sub(r'"([^"]+)":"[^"]*"', '"\\1":"<S>"', normalized)

    # 长行截断：超过 200 字符只取前 200 做签名
    if len(normalized) > 200:
        normalized = normalized[:200]

    return normalized


def compute_pattern_hash(normalized: str) -> str:
    """计算模式哈希"""
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def is_low_value_log(content: str) -> bool:
    """判断是否为低价值日志"""
    for pattern in COMPILED_LOW_VALUE:
        if pattern.search(content):
            return True
    return False


def extract_error_type(content: str) -> Optional[str]:
    """从日志内容中提取错误类型"""
    # Java 异常
    match = re.search(r'([A-Za-z]+(?:Exception|Error|Failure))(?:\s|:|$)', content)
    if match:
        return match.group(1)
    
    # Python 异常
    match = re.search(r'(\w+Error|\w+Exception):', content)
    if match:
        return match.group(1)
    
    # 通用错误码
    match = re.search(r'error\s*(?:code|:)\s*([A-Z0-9_]+)', content, re.IGNORECASE)
    if match:
        return f"Error_{match.group(1)}"
    
    # 通用失败
    match = re.search(r'(fail(?:ed|ure)?|timeout|refused|denied)', content, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    
    return None


# ==================== 核心功能 ====================

def get_overview(filepath: str, max_scan_lines: int = 100000) -> Dict:
    """获取日志文件概览"""
    file_size = os.path.getsize(filepath)
    file_size_mb = file_size / (1024 * 1024)
    
    total_lines = 0
    level_counts = Counter()
    error_types = Counter()
    first_time = None
    last_time = None
    sample_lines = []
    high_value_count = 0
    
    pattern = None
    
    for line_num, line in read_file_lines(filepath):
        total_lines += 1
        
        # 收集样本检测格式
        if len(sample_lines) < 100:
            sample_lines.append(line)
        
        if total_lines == 100 and not pattern:
            pattern = detect_log_format(sample_lines)
        
        # 解析日志
        if pattern:
            log_line = parse_log_line(line, line_num, pattern)
            
            if log_line.level:
                level_counts[log_line.level] += 1
                if log_line.level in ('ERROR', 'FATAL', 'CRITICAL', 'WARN', 'WARNING'):
                    high_value_count += 1
                    error_type = extract_error_type(line)
                    if error_type:
                        error_types[error_type] += 1
            
            if log_line.time:
                if not first_time:
                    first_time = log_line.time
                last_time = log_line.time
        
        # 限制扫描
        if total_lines >= max_scan_lines:
            break
    
    # 分析建议
    recommendations = []
    if file_size_mb > 50:
        recommendations.append("⚠️ 文件较大，建议使用 --dedupe 和 --compress 3")
    if high_value_count > 1000:
        recommendations.append("⚠️ 错误日志较多，建议使用 errors 命令聚类分析")
    if not pattern:
        recommendations.append("⚠️ 未识别日志格式，时间过滤可能不准确")
    
    return {
        'file_path': filepath,
        'file_size': f'{file_size_mb:.2f} MB',
        'total_lines': total_lines,
        'scanned_lines': min(total_lines, max_scan_lines),
        'time_range': {
            'start': first_time,
            'end': last_time
        },
        'level_distribution': dict(level_counts.most_common(10)),
        'top_errors': dict(error_types.most_common(10)),
        'high_value_logs': high_value_count,
        'detected_format': TIME_PATTERNS[COMPILED_PATTERNS.index(pattern)] if pattern else 'unknown',
        'recommendations': recommendations
    }


def search_with_dedup(
    filepath: str,
    keyword: Optional[str] = None,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    level_filter: Optional[List[str]] = None,
    context_lines: int = 0,
    limit: int = 50,
    dedupe: bool = True,
    compress_level: int = 2
) -> Dict:
    """智能搜索并去重"""
    
    # 解析参数
    start_time = parse_time(time_start) if time_start else None
    end_time = parse_time(time_end) if time_end else None
    
    keyword_pattern = None
    if keyword:
        try:
            keyword_pattern = re.compile(keyword, re.IGNORECASE)
        except re.error:
            keyword_pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    
    # 检测日志格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 搜索并去重
    patterns_dict: Dict[str, LogPattern] = {}
    raw_matches = []
    scanned_lines = 0
    filtered_count = 0
    
    # 上下文缓冲
    context_buffer = []
    
    for line_num, line in read_file_lines(filepath):
        scanned_lines += 1
        
        # 维护上下文
        if context_lines > 0:
            context_buffer.append((line_num, line))
            if len(context_buffer) > context_lines * 2 + 1:
                context_buffer.pop(0)
        
        # 解析日志行
        log_line = parse_log_line(line, line_num, pattern)
        
        # 时间过滤
        if start_time or end_time:
            if log_line.time and not time_in_range(log_line.time, start_time, end_time):
                continue
        
        # 级别过滤
        if level_filter:
            if not log_line.level or log_line.level not in level_filter:
                continue
        
        # 关键词过滤
        if keyword_pattern:
            if not keyword_pattern.search(line):
                continue
        
        # 低价值过滤
        if compress_level >= 2 and is_low_value_log(line):
            filtered_count += 1
            continue
        
        # 去重处理
        if dedupe:
            normalized = normalize_log_for_dedup(line)
            pattern_hash = compute_pattern_hash(normalized)
            
            if pattern_hash in patterns_dict:
                patterns_dict[pattern_hash].add_occurrence(log_line)
            else:
                patterns_dict[pattern_hash] = LogPattern(
                    pattern_hash=pattern_hash,
                    template=normalized,
                    count=1,
                    first_time=log_line.time,
                    last_time=log_line.time,
                    first_line=line_num,
                    last_line=line_num,
                    samples=[line],
                    level=log_line.level
                )
        else:
            raw_matches.append({
                'line': line_num,
                'time': log_line.time,
                'level': log_line.level,
                'content': line[:200]  # 截断到200字符，避免撑爆 AI 上下文
            })
            if len(raw_matches) >= limit:
                break
    
    # 整理结果
    if dedupe:
        # 按重要性和出现次数排序
        sorted_patterns = sorted(
            patterns_dict.values(),
            key=lambda p: (LEVEL_WEIGHTS.get(p.level or '', 20), p.count),
            reverse=True
        )[:limit]
        
        results = []
        for p in sorted_patterns:
            result = {
                'pattern_id': p.pattern_hash,
                'count': p.count,
                'level': p.level,
                'time_range': f"{p.first_time or '?'} - {p.last_time or '?'}",
                'line_range': f"{p.first_line} - {p.last_line}",
                'sample': p.samples[0][:200] if p.samples else '',  # 截断到200字符
            }
            
            # 压缩级别控制
            if compress_level <= 1 and len(p.samples) > 1:
                result['additional_samples'] = [s[:200] for s in p.samples[1:]]
            
            results.append(result)
        
        return {
            'mode': 'dedupe',
            'query': {
                'keyword': keyword,
                'time_range': f'{time_start or "*"} - {time_end or "*"}',
                'level_filter': level_filter,
                'compress_level': compress_level
            },
            'stats': {
                'scanned_lines': scanned_lines,
                'unique_patterns': len(patterns_dict),
                'returned_patterns': len(results),
                'filtered_low_value': filtered_count,
                'total_matches': sum(p.count for p in patterns_dict.values())
            },
            'results': results
        }
    else:
        return {
            'mode': 'raw',
            'query': {
                'keyword': keyword,
                'time_range': f'{time_start or "*"} - {time_end or "*"}',
                'level_filter': level_filter
            },
            'stats': {
                'scanned_lines': scanned_lines,
                'returned': len(raw_matches)
            },
            'results': raw_matches
        }


def analyze_errors(
    filepath: str,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    top_n: int = 10
) -> Dict:
    """错误聚类分析"""
    
    start_time = parse_time(time_start) if time_start else None
    end_time = parse_time(time_end) if time_end else None
    
    # 检测格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 聚类错误
    error_clusters: Dict[str, ErrorCluster] = {}
    total_errors = 0
    scanned_lines = 0
    
    stack_trace_buffer = []
    current_error_type = None
    
    for line_num, line in read_file_lines(filepath):
        scanned_lines += 1
        log_line = parse_log_line(line, line_num, pattern)
        
        # 时间过滤
        if start_time or end_time:
            if log_line.time and not time_in_range(log_line.time, start_time, end_time):
                continue
        
        # 只分析错误级别
        if log_line.level not in ('ERROR', 'FATAL', 'CRITICAL', 'WARN', 'WARNING'):
            # 检查是否是堆栈跟踪的一部分
            if current_error_type and (line.startswith('\t') or line.startswith('    at ')):
                stack_trace_buffer.append(line)
            continue
        
        total_errors += 1
        
        # 提取错误类型
        error_type = extract_error_type(line) or 'Unknown'
        
        if error_type not in error_clusters:
            error_clusters[error_type] = ErrorCluster(
                error_type=error_type,
                count=1,
                first_time=log_line.time,
                samples=[line[:300]]
            )
        else:
            cluster = error_clusters[error_type]
            cluster.count += 1
            cluster.last_time = log_line.time
            if len(cluster.samples) < 3:
                cluster.samples.append(line[:300])
        
        current_error_type = error_type
        stack_trace_buffer = []
    
    # 排序并返回 top N
    sorted_errors = sorted(
        error_clusters.values(),
        key=lambda c: c.count,
        reverse=True
    )[:top_n]
    
    results = []
    for cluster in sorted_errors:
        results.append({
            'error_type': cluster.error_type,
            'count': cluster.count,
            'percentage': f"{cluster.count * 100 / total_errors:.1f}%" if total_errors > 0 else "0%",
            'first_seen': cluster.first_time,
            'last_seen': cluster.last_time,
            'sample': cluster.samples[0] if cluster.samples else ''
        })
    
    return {
        'stats': {
            'total_errors': total_errors,
            'unique_types': len(error_clusters),
            'scanned_lines': scanned_lines
        },
        'time_range': f'{time_start or "*"} - {time_end or "*"}',
        'top_errors': results
    }


def analyze_timeline(
    filepath: str,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    max_events: int = 20
) -> Dict:
    """时间线分析"""
    
    start_time = parse_time(time_start) if time_start else None
    end_time = parse_time(time_end) if time_end else None
    
    # 检测格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 按分钟统计
    minute_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'total': 0, 'errors': 0, 'warns': 0})
    
    # 关键事件
    key_events = []
    
    # 关键事件模式
    key_event_patterns = [
        r'(start|stop|restart|shutdown|crash|exit|init|begin|end|fail|success)',
        r'(connect|disconnect|timeout|refuse)',
        r'(error|exception|fatal|critical)',
    ]
    key_event_regex = re.compile('|'.join(key_event_patterns), re.IGNORECASE)
    
    scanned_lines = 0
    
    for line_num, line in read_file_lines(filepath):
        scanned_lines += 1
        log_line = parse_log_line(line, line_num, pattern)
        
        # 时间过滤
        if start_time or end_time:
            if log_line.time and not time_in_range(log_line.time, start_time, end_time):
                continue
        
        # 按分钟统计
        if log_line.time:
            minute = log_line.time[:5]  # HH:MM
            minute_stats[minute]['total'] += 1
            if log_line.level == 'ERROR':
                minute_stats[minute]['errors'] += 1
            elif log_line.level in ('WARN', 'WARNING'):
                minute_stats[minute]['warns'] += 1
        
        # 识别关键事件
        if log_line.level in ('ERROR', 'FATAL', 'CRITICAL') or key_event_regex.search(line):
            if len(key_events) < max_events * 3:  # 收集更多，后面筛选
                key_events.append({
                    'line': line_num,
                    'time': log_line.time,
                    'level': log_line.level,
                    'content': line[:200],
                    'importance': log_line.importance
                })
    
    # 选择最重要的事件
    key_events.sort(key=lambda e: e['importance'], reverse=True)
    key_events = key_events[:max_events]
    key_events.sort(key=lambda e: e['line'])  # 按行号排序
    
    # 整理分钟统计
    minute_summary = []
    for minute in sorted(minute_stats.keys()):
        stats = minute_stats[minute]
        if stats['errors'] > 0 or stats['warns'] > 0:
            minute_summary.append({
                'time': minute,
                'total': stats['total'],
                'errors': stats['errors'],
                'warns': stats['warns']
            })
    
    return {
        'time_range': f'{time_start or "*"} - {time_end or "*"}',
        'scanned_lines': scanned_lines,
        'minute_summary': minute_summary[-30:],  # 最多 30 分钟
        'key_events': key_events
    }


def trace_id(
    filepath: str,
    trace_id: str,
    context_lines: int = 2,
    limit: int = 100
) -> Dict:
    """追踪特定 ID"""
    
    # 检测格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 搜索
    results = []
    context_buffer = []
    pending_context = []
    scanned_lines = 0
    
    trace_pattern = re.compile(re.escape(trace_id), re.IGNORECASE)
    
    for line_num, line in read_file_lines(filepath):
        scanned_lines += 1
        
        # 维护上下文
        if context_lines > 0:
            context_buffer.append((line_num, line))
            if len(context_buffer) > context_lines:
                context_buffer.pop(0)
        
        # 处理后置上下文
        new_pending = []
        for result, remaining in pending_context:
            if remaining > 0:
                result['context_after'].append(line[:200])
                new_pending.append((result, remaining - 1))
        pending_context = new_pending
        
        # 匹配
        if trace_pattern.search(line):
            log_line = parse_log_line(line, line_num, pattern)
            
            result = {
                'line': line_num,
                'time': log_line.time,
                'level': log_line.level,
                'content': line[:400],
                'context_before': [],
                'context_after': []
            }
            
            # 添加前置上下文
            if context_lines > 0 and len(context_buffer) > 1:
                for ctx_line, ctx_content in context_buffer[:-1]:
                    result['context_before'].append(ctx_content[:200])
            
            results.append(result)
            
            if context_lines > 0:
                pending_context.append((result, context_lines))
            
            if len(results) >= limit:
                break
    
    return {
        'trace_id': trace_id,
        'stats': {
            'scanned_lines': scanned_lines,
            'matches': len(results)
        },
        'results': results
    }


def validate_time_range(
    filepath: str,
    target_time: str,
    context_minutes: int = 5
) -> Dict:
    """
    验证目标时间是否在日志覆盖范围内
    这是排查的关键第一步，避免在错误的时间段浪费时间
    """
    
    target_parsed = parse_time(target_time)
    if not target_parsed:
        return {
            'valid': False,
            'error': f"无法解析目标时间: {target_time}",
            'suggestion': "请使用 HH:MM 或 HH:MM:SS 格式"
        }
    
    # 检测日志格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 扫描日志时间范围
    first_time = None
    last_time = None
    first_line = None
    last_line = None
    total_lines = 0
    
    # 查找目标时间附近的日志
    target_sec = time_to_seconds(target_parsed)
    nearby_logs = []
    
    for line_num, line in read_file_lines(filepath):
        total_lines += 1
        log_line = parse_log_line(line, line_num, pattern)
        
        if log_line.time:
            if not first_time:
                first_time = log_line.time
                first_line = line_num
            last_time = log_line.time
            last_line = line_num
            
            # 检查是否在目标时间附近（±context_minutes 分钟）
            t = parse_time(log_line.time)
            if t:
                t_sec = time_to_seconds(t)
                if abs(t_sec - target_sec) <= context_minutes * 60:
                    if len(nearby_logs) < 10:  # 最多保留10条
                        nearby_logs.append({
                            'line': line_num,
                            'time': log_line.time,
                            'level': log_line.level,
                            'content': line[:200]
                        })
    
    # 分析结果
    result = {
        'target_time': target_time,
        'log_time_range': {
            'start': first_time,
            'end': last_time,
            'start_line': first_line,
            'end_line': last_line
        },
        'total_lines': total_lines,
        'detected_format': TIME_PATTERNS[COMPILED_PATTERNS.index(pattern)] if pattern else 'unknown'
    }
    
    # 判断目标时间是否在范围内
    if first_time and last_time:
        first_parsed = parse_time(first_time)
        last_parsed = parse_time(last_time)
        
        if first_parsed and last_parsed:
            first_sec = time_to_seconds(first_parsed)
            last_sec = time_to_seconds(last_parsed)
            
            if target_sec < first_sec:
                result['in_range'] = False
                result['position'] = 'before'
                result['message'] = f"⚠️ 目标时间 {target_time} 早于日志开始时间 {first_time}"
                result['suggestion'] = "需要获取更早时间段的日志文件"
            elif target_sec > last_sec:
                result['in_range'] = False
                result['position'] = 'after'
                result['message'] = f"⚠️ 目标时间 {target_time} 晚于日志结束时间 {last_time}"
                result['suggestion'] = "日志在 {last_time} 停止记录，这本身可能是问题线索（如进程被终止）"
                result['important_hint'] = "💡 日志截止时间本身可能就是问题发生的时刻！"
            else:
                result['in_range'] = True
                result['position'] = 'within'
                result['message'] = f"✅ 目标时间 {target_time} 在日志范围内"
                result['nearby_logs'] = nearby_logs
        else:
            result['in_range'] = 'unknown'
            result['message'] = "无法确定时间范围（时间解析失败）"
    else:
        result['in_range'] = 'unknown'
        result['message'] = "无法确定时间范围（未检测到时间戳）"
    
    return result


def analyze_event_chain(
    filepath: str,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None,
    event_keywords: Optional[List[str]] = None,
    limit: int = 50
) -> Dict:
    """
    事件链分析 - 追踪进程状态变化，重构问题发生链路
    
    专门用于分析：
    - 进程启动/停止序列
    - 连接建立/断开过程
    - 初始化/退出流程
    - 状态变化链路
    """
    
    # 默认事件关键词（覆盖常见的状态变化）
    if not event_keywords:
        event_keywords = [
            'start', 'stop', 'init', 'exit', 'quit', 'shutdown', 'terminate',
            'connect', 'disconnect', 'open', 'close', 'begin', 'end',
            'create', 'destroy', 'load', 'unload', 'register', 'unregister',
            'enable', 'disable', 'activate', 'deactivate',
            'success', 'fail', 'error', 'timeout', 'refuse', 'denied'
        ]
    
    # 构建正则
    event_pattern = re.compile(
        r'\b(' + '|'.join(re.escape(k) for k in event_keywords) + r')\b',
        re.IGNORECASE
    )
    
    start_time = parse_time(time_start) if time_start else None
    end_time = parse_time(time_end) if time_end else None
    
    # 检测日志格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 100:
            break
    
    pattern = detect_log_format(sample_lines)
    
    # 收集事件
    events = []
    scanned_lines = 0
    
    for line_num, line in read_file_lines(filepath):
        scanned_lines += 1
        log_line = parse_log_line(line, line_num, pattern)
        
        # 时间过滤
        if start_time or end_time:
            if log_line.time and not time_in_range(log_line.time, start_time, end_time):
                continue
        
        # 事件匹配
        matches = event_pattern.findall(line)
        if matches:
            # 提取匹配的关键词
            matched_keywords = list(set(m.lower() for m in matches))
            
            # 判断事件类型
            event_type = 'unknown'
            if any(k in matched_keywords for k in ['start', 'init', 'begin', 'create', 'load', 'connect', 'open', 'enable', 'activate', 'register']):
                event_type = 'start'
            elif any(k in matched_keywords for k in ['stop', 'exit', 'quit', 'shutdown', 'terminate', 'end', 'destroy', 'unload', 'close', 'disable', 'deactivate', 'unregister']):
                event_type = 'stop'
            elif any(k in matched_keywords for k in ['fail', 'error', 'timeout', 'refuse', 'denied']):
                event_type = 'error'
            elif any(k in matched_keywords for k in ['success']):
                event_type = 'success'
            
            events.append({
                'line': line_num,
                'time': log_line.time,
                'level': log_line.level,
                'event_type': event_type,
                'keywords': matched_keywords,
                'content': line[:300]
            })
            
            if len(events) >= limit:
                break
    
    # 分析事件序列
    event_summary = {
        'total_events': len(events),
        'start_events': sum(1 for e in events if e['event_type'] == 'start'),
        'stop_events': sum(1 for e in events if e['event_type'] == 'stop'),
        'error_events': sum(1 for e in events if e['event_type'] == 'error'),
    }
    
    # 尝试识别关键事件对（如 start -> stop）
    critical_sequences = []
    for i, event in enumerate(events):
        if event['event_type'] == 'stop' and event['level'] in ('INFO', None):
            # 这是一个停止事件，可能是关键线索
            critical_sequences.append({
                'event': event,
                'context': events[max(0, i-3):i]  # 前3个事件作为上下文
            })
    
    return {
        'time_range': f'{time_start or "*"} - {time_end or "*"}',
        'event_keywords': event_keywords[:10],  # 只显示前10个
        'stats': {
            'scanned_lines': scanned_lines,
            **event_summary
        },
        'events': events,
        'critical_sequences': critical_sequences[:5]  # 最多5个关键序列
    }


def tail_log(filepath: str, num_lines: int = 50) -> Dict:
    """
    读取日志末尾N行，带行号+时间戳+级别+截断内容。
    用于快速查看日志最后的记录（如进程退出前的最后日志）。
    """
    # 收集末尾N行（用 deque 高效实现）
    from collections import deque
    tail_lines: deque = deque(maxlen=num_lines)

    # 先检测格式
    sample_lines = []
    for line_num, line in read_file_lines(filepath):
        sample_lines.append(line)
        if len(sample_lines) >= 50:
            break
    pattern = detect_log_format(sample_lines)

    total_lines = 0
    for line_num, line in read_file_lines(filepath):
        total_lines = line_num
        tail_lines.append((line_num, line))

    # 解析每行
    results = []
    for ln, raw_line in tail_lines:
        parsed = parse_log_line(raw_line, ln, pattern)
        results.append({
            'line': parsed.line_num,
            'time': parsed.time or 'N/A',
            'level': parsed.level or 'N/A',
            'content': parsed.content[:200]
        })

    return {
        'file_path': filepath,
        'total_lines': total_lines,
        'showing_lines': len(results),
        'results': results
    }


# ==================== 输出格式化 ====================

def format_output(data: Dict, command: str) -> str:
    """格式化输出"""
    lines = []
    
    if command == 'overview':
        lines.append("=" * 60)
        lines.append("📊 日志文件概览")
        lines.append("=" * 60)
        lines.append(f"📁 文件: {data['file_path']}")
        lines.append(f"📐 大小: {data['file_size']}")
        lines.append(f"📝 总行数: {data['total_lines']} (扫描: {data['scanned_lines']})")
        lines.append(f"⏰ 时间范围: {data['time_range']['start']} - {data['time_range']['end']}")
        lines.append(f"⚠️ 高价值日志: {data['high_value_logs']}")
        lines.append("")
        lines.append("📈 级别分布:")
        for level, count in data['level_distribution'].items():
            lines.append(f"  {level}: {count}")
        if data['top_errors']:
            lines.append("")
            lines.append("🔥 Top 错误类型:")
            for error, count in list(data['top_errors'].items())[:5]:
                lines.append(f"  {error}: {count}")
        if data['recommendations']:
            lines.append("")
            lines.append("💡 建议:")
            for rec in data['recommendations']:
                lines.append(f"  {rec}")
    
    elif command == 'search':
        lines.append("=" * 60)
        lines.append(f"🔍 日志搜索结果 (模式: {data['mode']})")
        lines.append("=" * 60)
        lines.append(f"查询: {data['query']}")
        
        if data['mode'] == 'dedupe':
            lines.append(f"统计: 扫描 {data['stats']['scanned_lines']} 行, "
                        f"匹配 {data['stats']['total_matches']} 条, "
                        f"去重后 {data['stats']['unique_patterns']} 种模式")
            if data['stats'].get('filtered_low_value', 0) > 0:
                lines.append(f"过滤低价值日志: {data['stats']['filtered_low_value']} 条")
        else:
            lines.append(f"统计: 扫描 {data['stats']['scanned_lines']} 行, 返回 {data['stats']['returned']} 条")
        
        lines.append("")
        
        for i, result in enumerate(data['results'], 1):
            lines.append("-" * 50)
            if data['mode'] == 'dedupe':
                lines.append(f"[{i}] {result.get('level', 'N/A')} | 出现 {result['count']} 次 | {result['time_range']}")
                lines.append(f"    行范围: {result['line_range']}")
                lines.append(f"    样本: {result['sample']}")
            else:
                lines.append(f"[{i}] 行 {result['line']} | {result.get('time', 'N/A')} | {result.get('level', 'N/A')}")
                lines.append(f"    {result['content']}")
    
    elif command == 'errors':
        lines.append("=" * 60)
        lines.append("🔥 错误聚类分析")
        lines.append("=" * 60)
        lines.append(f"时间范围: {data['time_range']}")
        lines.append(f"统计: 总错误 {data['stats']['total_errors']} 条, "
                    f"错误类型 {data['stats']['unique_types']} 种")
        lines.append("")
        
        for i, error in enumerate(data['top_errors'], 1):
            lines.append(f"[{i}] {error['error_type']}")
            lines.append(f"    出现次数: {error['count']} ({error['percentage']})")
            lines.append(f"    时间范围: {error['first_seen']} - {error['last_seen']}")
            lines.append(f"    样本: {error['sample']}")
            lines.append("")
    
    elif command == 'timeline':
        lines.append("=" * 60)
        lines.append("📅 时间线分析")
        lines.append("=" * 60)
        lines.append(f"时间范围: {data['time_range']}")
        lines.append(f"扫描行数: {data['scanned_lines']}")
        lines.append("")
        
        if data['minute_summary']:
            lines.append("📊 分钟级统计（有异常的时间段）:")
            for m in data['minute_summary']:
                if m['errors'] > 0 or m['warns'] > 0:
                    lines.append(f"  {m['time']} - 总: {m['total']}, 错误: {m['errors']}, 警告: {m['warns']}")
        
        lines.append("")
        lines.append("🔑 关键事件:")
        for event in data['key_events']:
            lines.append(f"  [{event['time'] or '?'}] [{event['level'] or 'INFO'}] {event['content']}")
    
    elif command == 'trace':
        lines.append("=" * 60)
        lines.append(f"🔍 追踪 ID: {data['trace_id']}")
        lines.append("=" * 60)
        lines.append(f"统计: 扫描 {data['stats']['scanned_lines']} 行, 匹配 {data['stats']['matches']} 条")
        lines.append("")
        
        for i, result in enumerate(data['results'], 1):
            lines.append(f"[{i}] 行 {result['line']} | {result['time'] or 'N/A'} | {result['level'] or 'N/A'}")
            
            if result['context_before']:
                for ctx in result['context_before']:
                    lines.append(f"    (前) {ctx}")
            
            lines.append(f"  → {result['content']}")
            
            if result['context_after']:
                for ctx in result['context_after']:
                    lines.append(f"    (后) {ctx}")
            lines.append("")
    
    elif command == 'validate':
        lines.append("=" * 60)
        lines.append("⏰ 时间范围验证")
        lines.append("=" * 60)
        lines.append(f"目标时间: {data['target_time']}")
        lines.append("")
        
        if 'error' in data:
            lines.append(f"❌ {data['error']}")
            lines.append(f"💡 {data['suggestion']}")
        else:
            lines.append(f"📊 日志时间范围:")
            lines.append(f"  开始: {data['log_time_range']['start']} (行 {data['log_time_range']['start_line']})")
            lines.append(f"  结束: {data['log_time_range']['end']} (行 {data['log_time_range']['end_line']})")
            lines.append(f"  总行数: {data['total_lines']}")
            lines.append("")
            lines.append(f"{data['message']}")
            
            if data.get('suggestion'):
                lines.append(f"💡 {data['suggestion']}")
            
            if data.get('important_hint'):
                lines.append("")
                lines.append(data['important_hint'])
            
            if data.get('nearby_logs'):
                lines.append("")
                lines.append("📋 目标时间附近的日志:")
                for log in data['nearby_logs']:
                    lines.append(f"  [{log['time']}] [{log['level'] or 'N/A'}] {log['content']}")
    
    elif command == 'chain':
        lines.append("=" * 60)
        lines.append("🔗 事件链分析")
        lines.append("=" * 60)
        lines.append(f"时间范围: {data['time_range']}")
        lines.append(f"事件关键词: {', '.join(data['event_keywords'])}")
        lines.append("")
        lines.append(f"📊 统计:")
        lines.append(f"  扫描行数: {data['stats']['scanned_lines']}")
        lines.append(f"  总事件数: {data['stats']['total_events']}")
        lines.append(f"  启动事件: {data['stats']['start_events']}")
        lines.append(f"  停止事件: {data['stats']['stop_events']}")
        lines.append(f"  错误事件: {data['stats']['error_events']}")
        lines.append("")
        
        if data.get('critical_sequences'):
            lines.append("🔴 关键停止事件序列:")
            for seq in data['critical_sequences']:
                lines.append("-" * 50)
                event = seq['event']
                lines.append(f"停止事件: [{event['time']}] {event['content']}")
                if seq['context']:
                    lines.append("  前置事件:")
                    for ctx in seq['context']:
                        lines.append(f"    [{ctx['time']}] [{ctx['event_type']}] {ctx['content'][:100]}")
            lines.append("")
        
        lines.append("📅 事件时间线:")
        # 使用表格式显示事件链
        for event in data['events'][:30]:  # 最多显示30个
            type_icon = {'start': '🟢', 'stop': '🔴', 'error': '⚠️', 'success': '✅'}.get(event['event_type'], '○')
            lines.append(f"  {event['time'] or '?':12} {type_icon} [{event['level'] or 'N/A':5}] {event['content'][:80]}")
    
    elif command == 'tail':
        lines.append("=" * 60)
        lines.append("📄 日志末尾")
        lines.append("=" * 60)
        lines.append(f"📁 文件: {data['file_path']}")
        lines.append(f"📝 总行数: {data['total_lines']}, 显示末尾 {data['showing_lines']} 行")
        lines.append("")
        for i, result in enumerate(data['results'], 1):
            lines.append(f"[{i}] 行 {result['line']} | {result['time']} | {result['level']}")
            lines.append(f"    {result['content']}")
    
    return '\n'.join(lines)


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(
        description='智能日志分析工具 - 支持大文件智能压缩去重',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # overview 命令
    overview_parser = subparsers.add_parser('overview', help='获取日志概览')
    overview_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='智能搜索')
    search_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    search_parser.add_argument('--keyword', '-k', help='关键词（支持正则，| 分隔多个）')
    search_parser.add_argument('--preset', '-p', help='预设关键词组: disconnect|error|network|auth')
    search_parser.add_argument('--start', '-s', help='开始时间 (HH:MM)')
    search_parser.add_argument('--end', '-e', help='结束时间')
    search_parser.add_argument('--level', '-l', help='级别过滤（逗号分隔）')
    search_parser.add_argument('--context', '-c', type=int, default=0, help='上下文行数')
    search_parser.add_argument('--limit', type=int, default=50, help='最大返回条数')
    search_parser.add_argument('--dedupe', '-d', action='store_true', help='启用智能去重')
    search_parser.add_argument('--compress', type=int, default=2, choices=[1, 2, 3], help='压缩级别')
    
    # errors 命令
    errors_parser = subparsers.add_parser('errors', help='错误聚类分析')
    errors_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    errors_parser.add_argument('--start', '-s', help='开始时间')
    errors_parser.add_argument('--end', '-e', help='结束时间')
    errors_parser.add_argument('--top', '-t', type=int, default=10, help='返回 Top N 错误')
    
    # timeline 命令
    timeline_parser = subparsers.add_parser('timeline', help='时间线分析')
    timeline_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    timeline_parser.add_argument('--start', '-s', help='开始时间')
    timeline_parser.add_argument('--end', '-e', help='结束时间')
    timeline_parser.add_argument('--events', type=int, default=20, help='最大事件数')
    
    # trace 命令
    trace_parser = subparsers.add_parser('trace', help='追踪特定 ID')
    trace_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    trace_parser.add_argument('--trace-id', '-t', required=True, help='要追踪的 ID')
    trace_parser.add_argument('--context', '-c', type=int, default=2, help='上下文行数')
    trace_parser.add_argument('--limit', type=int, default=100, help='最大返回条数')
    
    # validate 命令（新增）
    validate_parser = subparsers.add_parser('validate', help='验证目标时间是否在日志范围内')
    validate_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    validate_parser.add_argument('--time', '-t', required=True, help='目标时间 (HH:MM 或 HH:MM:SS)')
    validate_parser.add_argument('--context', '-c', type=int, default=5, help='显示目标时间前后多少分钟的日志')
    
    # chain 命令（新增）
    chain_parser = subparsers.add_parser('chain', help='事件链分析 - 追踪进程状态变化')
    chain_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    chain_parser.add_argument('--start', '-s', help='开始时间')
    chain_parser.add_argument('--end', '-e', help='结束时间')
    chain_parser.add_argument('--events', help='事件关键词（逗号分隔），默认包含 start/stop/init/exit 等')
    chain_parser.add_argument('--limit', type=int, default=50, help='最大返回事件数')
    
    # tail 命令
    tail_parser = subparsers.add_parser('tail', help='查看日志末尾N行')
    tail_parser.add_argument('--file', '-f', required=True, help='日志文件路径')
    tail_parser.add_argument('--lines', '-n', type=int, default=50, help='显示末尾行数（默认50）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 检查文件
    if not os.path.exists(args.file):
        print(f"❌ 错误: 文件不存在 - {args.file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.command == 'overview':
            result = get_overview(args.file)
        
        elif args.command == 'search':
            level_filter = None
            if args.level:
                level_filter = [l.strip().upper() for l in args.level.split(',')]
            
            # 解析预设关键词
            keyword = args.keyword
            if args.preset:
                preset_key = args.preset.strip().lower()
                if preset_key in PRESET_KEYWORDS:
                    keyword = PRESET_KEYWORDS[preset_key]
                else:
                    print(f"❌ 未知预设: {args.preset}，可选: {', '.join(PRESET_KEYWORDS.keys())}", file=sys.stderr)
                    sys.exit(1)
            
            result = search_with_dedup(
                args.file,
                keyword=keyword,
                time_start=args.start,
                time_end=args.end,
                level_filter=level_filter,
                context_lines=args.context,
                limit=args.limit,
                dedupe=args.dedupe,
                compress_level=args.compress
            )
        
        elif args.command == 'errors':
            result = analyze_errors(
                args.file,
                time_start=args.start,
                time_end=args.end,
                top_n=args.top
            )
        
        elif args.command == 'timeline':
            result = analyze_timeline(
                args.file,
                time_start=args.start,
                time_end=args.end,
                max_events=args.events
            )
        
        elif args.command == 'trace':
            result = trace_id(
                args.file,
                trace_id=args.trace_id,
                context_lines=args.context,
                limit=args.limit
            )
        
        elif args.command == 'validate':
            result = validate_time_range(
                args.file,
                target_time=args.time,
                context_minutes=args.context
            )
        
        elif args.command == 'chain':
            event_keywords = None
            if args.events:
                event_keywords = [k.strip() for k in args.events.split(',')]
            
            result = analyze_event_chain(
                args.file,
                time_start=args.start,
                time_end=args.end,
                event_keywords=event_keywords,
                limit=args.limit
            )
        
        elif args.command == 'tail':
            result = tail_log(args.file, num_lines=args.lines)
        
        print(format_output(result, args.command))
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
