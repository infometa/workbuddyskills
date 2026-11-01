#!/usr/bin/env python3
"""Render service receipts for WorkBuddy; no network calls or background scheduling."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

CLOSED = {"CLOSED_FORFEIT_UNLOCK_EXPIRED", "CLOSED_FORFEIT_ZERO_REPLY", "CLOSED_HANDOFF_FULFILLED"}
TASK_TERMINAL = {"completed", "partial_failed", "failed", "canceled", "cancelled"}
TASK_STATUS = {"queued": "排队中", "sending": "进行中", "completed": "已完成",
               "partial_failed": "已结束，部分失败", "failed": "失败",
               "canceled": "已取消", "cancelled": "已取消"}
SCENES = {"hunter_match": "挖掘采购需求", "hunter_invite_v1": "到展邀约"}
STATS = [("targetCount", "目标人数"), ("waitingCount", "待发送数"),
         ("sentCount", "已发送数"), ("deliveredCount", "已送达数"),
         ("readCount", "已读数"), ("failedCount", "发送失败数")]


def text(value):
    return "" if value is None else str(value).strip()


def parse_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(text(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def remaining(record, now=None):
    end = parse_time(record.get("slot_end"))
    clock = parse_time(now) if now else datetime.now(timezone.utc)
    return (end - clock).total_seconds() if end and clock else None


def countdown(seconds):
    if seconds is None:
        return "待确认"
    if seconds <= 0:
        return "已结束"
    mins = int(seconds // 60)
    days, rest = divmod(mins, 1440)
    hours, minutes = divmod(rest, 60)
    return "%d 天 %d 小时 %d 分" % (days, hours, minutes)


def countries(value):
    mapping = {}
    path = Path(__file__).resolve().parent.parent / "references" / "country-iso.md"
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and len(cells[2]) == 2 and cells[2].isupper():
            mapping.setdefault(cells[2], cells[0])
    values = value if isinstance(value, list) else text(value).split(",")
    return "、".join(mapping.get(text(v).upper(), "国家待核实")
                    if len(text(v)) == 2 and text(v).isascii()
                    else text(v) for v in values if text(v))


def task_view(record):
    if not isinstance(record, dict) or not text(record.get("taskId")):
        raise ValueError("taskId is required")
    stats = record.get("stats")
    if not isinstance(stats, dict):
        raise ValueError("stats must be an object")
    fields = [["任务编号", text(record["taskId"])],
              ["触达国家", countries(record.get("countries")) or "待确认"],
              ["消息类型", SCENES.get(record.get("templateFamily"), "待核实")]]
    if text(record.get("keywords")):
        fields.append(["目标产品", text(record["keywords"])])
    if text(record.get("buyerTypeName")):
        fields.append(["买家类型", text(record["buyerTypeName"])])
    if record.get("templateFamily") == "hunter_invite_v1":
        fields.append(["展会名称", text(record.get("exhibitionName")) or "待确认"])
    for key, label in STATS:
        value = stats.get(key)
        fields.append([label, value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else "待确认"])
    fields.append(["任务状态", TASK_STATUS.get(record.get("status"), "待核实")])
    if text(record.get("estimatedSend")):
        fields.append(["预计发送", text(record["estimatedSend"])])
    if record.get("matchStatus") in ("pending", "running", "done"):
        fields.append(["匹配进度", {"pending":"等待匹配","running":"匹配中","done":"匹配完成"}[record["matchStatus"]]])
    return {"title": "AI猎客-WhatsApp触达任务日报", "fields": fields,
            "terminal": record.get("status") in TASK_TERMINAL}


def inquiry_view(record, now=None):
    if not isinstance(record, dict) or not text(record.get("inquiry_id")):
        raise ValueError("inquiry_id is required")
    status = record.get("inquiry_status")
    summary = record.get("inquiry_summary")
    if not isinstance(summary, dict):
        raise ValueError("inquiry_summary must be an object")
    fields = []
    for key, label in [("intent_product","意向产品"),("summary_text","摘要"),
                       ("spec","规格"),("purchase_quantity","采购数量"),
                       ("target_price","目标价"),("lead_time","交期"),("destination","目的地")]:
        if text(summary.get(key)):
            fields.append([label,text(summary[key])])
    seconds = remaining(record, now)
    closed = status in CLOSED or text(status).startswith("CLOSED_")
    status_text = {"UNLOCK_PENDING":"待解锁", "COMMUNICATING":"沟通中",
                   "CLOSED_FORFEIT_UNLOCK_EXPIRED":"已过期（时段结束仍未解锁）",
                   "CLOSED_FORFEIT_ZERO_REPLY":"已关闭（时段内零回复）",
                   "CLOSED_HANDOFF_FULFILLED":"已关闭（履约交接完成）"}.get(status,"已关闭" if closed else "待核实")
    fields.append(["状态", status_text])
    end = parse_time(record.get("slot_end"))
    if end and not closed:
        fields += [["本企业时段截止",end.isoformat(sep=" ")],["剩余时间",countdown(seconds)]]
    if not closed and record.get("queue_index") is not None:
        fields.append(["排队位次",record["queue_index"]])
    active = record.get("slot_state") == "ACTIVE" and seconds is not None and seconds > 0
    start = parse_time(record.get("slot_start"))
    clock = parse_time(now) if now else datetime.now(timezone.utc)
    if start and (clock is None or start > clock):
        active = False
    actions = []
    if status == "UNLOCK_PENDING" and active and seconds >= 3600:
        actions.append("request_unlock")
    elif status == "COMMUNICATING" and active:
        contact = record.get("buyer_contact")
        if isinstance(contact, dict):
            for key,label in [("nickname","联系人"),("wa_number","WhatsApp")]:
                if text(contact.get(key)):
                    fields.append([label,text(contact[key])])
        if record.get("chat_enterable") is True:
            actions.append("request_chat_link")
    return {"title":"WhatsApp 询盘", "fields":fields, "actions":actions, "terminal":closed}


def reminder_plan(payload):
    """Return proposed events; caller saves success_patch only after delivery succeeds."""
    records, snapshot = payload.get("records"), payload.get("snapshot")
    if not isinstance(records, list) or not isinstance(snapshot, dict):
        raise ValueError("records array and snapshot object are required")
    actions, seen = [], set()
    for record in records:
        if not isinstance(record, dict) or not text(record.get("inquiry_id")):
            raise ValueError("each record requires inquiry_id")
        iid = text(record["inquiry_id"])
        if iid in seen:
            raise ValueError("duplicate inquiry_id; reconcile records before planning")
        seen.add(iid)
        status = record.get("inquiry_status")
        previous = snapshot.get(iid) or {}
        if not isinstance(previous, dict):
            raise ValueError("snapshot entry must be an object")
        if text(previous.get("status")).startswith("CLOSED_"):
            continue
        closed = text(status).startswith("CLOSED_")
        if closed or status in ("UNLOCK_PENDING","COMMUNICATING"):
            if status != previous.get("status"):
                actions.append({"inquiry_id":iid, "kind":"update" if previous else "display",
                                "event_key":iid+":status:"+text(status),
                                "success_patch":{"status":status}})
        if closed:
            continue
        if status not in ("UNLOCK_PENDING","COMMUNICATING") or record.get("slot_state") != "ACTIVE":
            continue
        start = parse_time(record.get("slot_start"))
        clock = parse_time(payload.get("now")) if payload.get("now") else datetime.now(timezone.utc)
        if start and (clock is None or start > clock):
            continue
        seconds = remaining(record,payload.get("now"))
        if seconds is None:
            continue
        if seconds <= 0:
            actions.append({"inquiry_id":iid,"kind":"refresh_status"})
            continue
        one = seconds <= 3600
        same_slot = previous.get("slot_end") in (None, record.get("slot_end"))
        if seconds <= 14400 and not (same_slot and previous.get("reminded_1h" if one else "reminded_4h")):
            mark = {"reminded_1h":True,"reminded_4h":True} if one else {"reminded_4h":True}
            mark["slot_end"] = record.get("slot_end")
            if not one and not same_slot:
                mark["reminded_1h"] = False
            kind = "remind_1h" if one else "remind_4h"
            actions.append({"inquiry_id":iid,"kind":kind,
                            "event_key":iid+":"+kind+":"+text(record.get("slot_end")),
                            "success_patch":mark})
    return {"actions":actions,"snapshot_changed":False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["task","inquiry","reminders"])
    parser.add_argument("--now",help="timezone-aware ISO time, useful for deterministic previews")
    args=parser.parse_args()
    import sys
    try:
        payload=json.load(sys.stdin)
        if not isinstance(payload,dict):
            raise ValueError("input must be an object")
        result = task_view(payload) if args.command=="task" else inquiry_view(payload,args.now) if args.command=="inquiry" else reminder_plan(payload)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,TypeError) as exc:
        print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False))
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
