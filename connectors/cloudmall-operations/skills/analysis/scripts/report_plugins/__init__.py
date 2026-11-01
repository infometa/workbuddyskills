"""报告插件注册表。

新增报告类型：
1. 在本目录新建 xxx.py，实现 generate_findings(data) → list[dict]
2. 在下方 REGISTRY 加一行映射
3. 在 workflow_report.md 路由表加一行
4. 新建 schema_examples/cap_{N}.json

完成。
"""

from .trade_weekly import generate_findings as trade_weekly
from .store_benchmark import generate_findings as store_benchmark
from .daily_snapshot import generate_findings as daily_snapshot

REGISTRY = {
    1: trade_weekly,       # 经营周报/月报
    2: store_benchmark,    # 门店对标
    3: daily_snapshot,     # 经营日报
}


def get_findings_generator(capability_id: int):
    """按 capability_id 获取对应的 findings 生成器函数。未注册则降级到周报。"""
    return REGISTRY.get(capability_id, trade_weekly)
