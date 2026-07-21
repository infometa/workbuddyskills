#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地日志占位模块

保留原有日志接口，避免调用方改动；不进行任何网络上报。
"""

from typing import Optional


# AI-Generated Begin
class LoggerReporter:
    """无副作用日志接口。"""

    def log(self, level: str, event: str, **kwargs):
        return None

    def debug(self, event: str, **kwargs):
        self.log("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs):
        self.log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self.log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs):
        self.log("ERROR", event, **kwargs)

    def flush(self, timeout: float = 3.0):
        return None
    # AI-Generated End


# 全局日志实例
_reporter: Optional[LoggerReporter] = None


def get_reporter() -> LoggerReporter:
    """获取全局日志实例"""
    global _reporter
    if _reporter is None:
        _reporter = LoggerReporter()
    return _reporter


# 便捷函数
def debug(event: str, **kwargs):
    """调试级别日志。"""
    get_reporter().debug(event, **kwargs)


def info(event: str, **kwargs):
    """信息级别日志。"""
    get_reporter().info(event, **kwargs)


def warning(event: str, **kwargs):
    """警告级别日志。"""
    get_reporter().warning(event, **kwargs)


def error(event: str, **kwargs):
    """错误级别日志。"""
    get_reporter().error(event, **kwargs)


def flush(timeout: float = 3.0):
    """兼容旧接口，无需等待。"""
    get_reporter().flush(timeout=timeout)


if __name__ == "__main__":
    print("本地日志占位模块，不执行网络上报")
