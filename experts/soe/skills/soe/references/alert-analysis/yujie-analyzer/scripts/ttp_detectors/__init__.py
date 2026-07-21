"""L1 御界 TTP 检测器"""
from .c2_beacon import detect_c2_beacon
from .tunnel_detection import detect_tunnel
from .lateral_movement import detect_lateral_movement
from .exfiltration import detect_exfiltration

__all__ = [
    "detect_c2_beacon",
    "detect_tunnel",
    "detect_lateral_movement",
    "detect_exfiltration",
]
