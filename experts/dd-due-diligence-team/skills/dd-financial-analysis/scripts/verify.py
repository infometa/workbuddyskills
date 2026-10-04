"""财务数字回填校验脚本（Cloud Agent 沙箱内执行）.

作用：把 LLM 打算写进报告的数字，与 calculate.py 权威重算结果逐项比对。
这是"确定性的归代码"红线的最后一道工程闸口——只要 LLM 篡改/幻觉了任何一个
数字，本脚本就会把它标为 mismatch，报告不得带着未通过的数字定稿。

用法::

    echo '{"inputs": {三表JSON}, "claims": {"current_ratio": 1.66, ...}}' \
        | python3 scripts/verify.py

输入 stdin JSON：
    - inputs：三表 JSON（结构同 calculate.py 的输入）
    - claims：外部报告声称的指标值 {ratio_key: value}，key 必须存在于权威指标中
    - tolerance（可选）：绝对浮点容差，默认 1e-9，最大 1e-6

输出 stdout JSON：
    - verified：是否全部通过
    - mismatches：不一致明细（含权威值 vs 声称值）
    - authoritative：权威重算的完整结果（供报告直接引用）
"""

import json
import math
import os
import sys
from typing import Any, Optional

# 让本脚本无论从哪个 cwd 执行都能 import 同目录的 calculate
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculate import analyze  # noqa: E402

DEFAULT_ABS_TOLERANCE = 1e-9


def _to_float(v: Any) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _match(authoritative: Optional[float], claimed: Optional[float], abs_tol: float) -> bool:
    """容差比对：权威值为 None 时，声称值也必须为 None 才算通过。"""
    if authoritative is None:
        return claimed is None
    if claimed is None:
        return False
    return abs(authoritative - claimed) <= abs_tol


def _parse_claim(value: Any) -> tuple[bool, Optional[float]]:
    if value is None:
        return True, None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False, None
    try:
        claimed = float(value)
    except (OverflowError, ValueError):
        return False, None
    return (True, claimed) if math.isfinite(claimed) else (False, None)


def verify(payload: dict[str, Any]) -> dict[str, Any]:
    inputs = payload.get('inputs')
    if not isinstance(inputs, dict):
        return {'verified': False, 'error': 'missing "inputs" (three-statement JSON)'}

    claims = payload.get('claims') or {}
    if not isinstance(claims, dict):
        return {'verified': False, 'error': '"claims" must be an object of {ratio_key: value}'}
    if not claims:
        return {'verified': False, 'error': '"claims" must contain at least one metric claim'}

    if 'tolerance' in payload:
        abs_tol = _to_float(payload.get('tolerance'))
        if abs_tol is None or not math.isfinite(abs_tol) or not 0 <= abs_tol <= 1e-6:
            return {'verified': False, 'error': 'tolerance must be finite and between 0 and 1e-6'}
    else:
        abs_tol = DEFAULT_ABS_TOLERANCE

    try:
        result = analyze(inputs)
    except (ValueError, TypeError) as exc:
        return {'verified': False, 'error': f'authoritative calculation failed: {exc}'}
    # 兼容旧调用方的 ratio key，同时允许核验金额、天数等新增 metric。
    metrics = result['metrics']

    mismatches: list[dict[str, Any]] = []
    checked = 0
    for key, claimed_raw in claims.items():
        if key not in metrics:
            mismatches.append(
                {'key': key, 'reason': 'unknown ratio key（不在权威指标集合中）'}
            )
            continue
        checked += 1
        authoritative = metrics[key]['value']
        valid_claim, claimed = _parse_claim(claimed_raw)
        if not valid_claim:
            mismatches.append(
                {
                    'key': key,
                    'name_cn': metrics[key]['name_cn'],
                    'authoritative': authoritative,
                    'claimed': repr(claimed_raw),
                    'reason': 'claim 必须是有限数值或显式 null',
                }
            )
            continue
        if not _match(authoritative, claimed, abs_tol):
            mismatches.append(
                {
                    'key': key,
                    'name_cn': metrics[key]['name_cn'],
                    'authoritative': authoritative,
                    'claimed': claimed,
                    'reason': '数字与沙箱权威计算不一致，禁止写入报告',
                }
            )

    return {
        'verified': len(mismatches) == 0,
        'checked_count': checked,
        'mismatch_count': len(mismatches),
        'mismatches': mismatches,
        'tolerance': abs_tol,
        # 权威结果原样带回，报告应直接引用此处数字
        'authoritative': result,
    }


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({'verified': False, 'error': 'empty stdin'}, ensure_ascii=False))
        sys.exit(1)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({'verified': False, 'error': f'invalid JSON: {exc}'}, ensure_ascii=False))
        sys.exit(1)
    if not isinstance(payload, dict):
        print(
            json.dumps(
                {'verified': False, 'error': 'top-level JSON must be an object'},
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    report = verify(payload)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 校验不通过时以非 0 退出，便于 agent 通过退出码判断是否需要重生成
    if not report.get('verified'):
        sys.exit(2)


if __name__ == '__main__':
    main()
