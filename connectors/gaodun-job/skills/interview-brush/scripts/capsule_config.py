"""胶囊抽题参数装配：capsule_id/手工过滤 → MCP brush_draw 工具入参 payload + sessionInit。

抽题 HTTP 调用已全走 `gaodun-job` MCP 工具 brush_draw（见 SKILL 铁律与 references/api.md），
本模块只做确定性参数装配，不含网络、不含 URL、不含认证。
"""
import json
from pathlib import Path

CAPSULES_PATH = Path(__file__).resolve().parents[1] / "data" / "capsules.json"


def load_capsules(path=CAPSULES_PATH):
    with Path(path).open(encoding="utf-8") as stream:
        document = json.load(stream)
    capsules = {item["id"]: item for item in document["capsules"]}
    if len(capsules) != len(document["capsules"]):
        raise ValueError("duplicate capsule id")
    for capsule in capsules.values():
        filters = capsule["drawFilters"]
        if "questionTag" in filters and "projectId" not in filters:
            raise ValueError("questionTag requires projectId in capsule {}".format(capsule["id"]))
    return capsules


def resolve_start(capsule_id, manual_filters, exclude_question_ids):
    manual_filters = {key: value for key, value in manual_filters.items() if value is not None}
    if capsule_id:
        if manual_filters:
            raise ValueError("--capsule-id cannot be combined with manual draw filters")
        capsules = load_capsules()
        if capsule_id not in capsules:
            raise ValueError("unknown capsule id: {}".format(capsule_id))
        capsule = capsules[capsule_id]
        payload = dict(capsule["drawFilters"])
        session = dict(capsule["sessionInit"])
        session.update({
            "capsuleEntry": True,
            "capsuleId": capsule["id"],
            "capsuleName": capsule["name"],
            "intro": capsule["intro"],
        })
    else:
        payload = manual_filters
        session = None
    if exclude_question_ids:
        payload["excludeQuestionIds"] = exclude_question_ids
    return payload, session
