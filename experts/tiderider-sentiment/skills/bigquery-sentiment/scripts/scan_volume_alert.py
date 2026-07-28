#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BigQuery 异常扫描量告警脚本（拖库检测 · D 层审计）
==================================================================

用途：定期扫描 BigQuery 查询作业历史，发现"异常大扫描量"（疑似拖库/全表导出）
并通过企业微信 Webhook 告警。

设计原则（对应"防拖库四层防御"的 D 层：审计与异常检测）：
  正常一次舆情查询扫几百 MB；如果突然有人一次扫了几百 GB / 上 TB，
  或短时间内累计扫描量暴增 —— 这就是拖库信号。

------------------------------------------------------------------
权限前提（重要，二选一）：
  【模式 A · 项目级审计】JOBS_BY_PROJECT —— 看全项目所有人的 job
     · 需要 bigquery.jobs.listAll 权限（通常是 BigQuery Admin / Resource Viewer）
     · 这才是真正的"拖库告警"：能看到别人在拖库
     · ⚠️ 当前 TideRider 的只读凭证【没有】这个权限（这符合最小权限设计）
       —— 需用一个【专门的审计账号】来跑此脚本

  【模式 B · 账号自审】JOBS_BY_USER —— 只看自己账号的 job
     · 无需额外权限，任何只读账号都能跑（已验证可用，region-us）
     · 用途：核对"我自己的账号有没有被冒用去拖库"
     · 局限：只能看到调用者自己，看不到别人

脚本会自动探测：优先尝试模式 A，失败则降级到模式 B。
------------------------------------------------------------------

用法：
  # 用审计账号凭证（模式A）
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/audit-sa.json \
    python3 scan_volume_alert.py --project <PROJECT_ID> --region region-us \
    --lookback-hours 24 --single-job-gb 50 --daily-total-gb 500 \
    --webhook "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=XXX"

  # 干跑（不发告警，只打印）
  python3 scan_volume_alert.py --project <PROJECT_ID> --dry-run
"""

import argparse
import json
import sys
import urllib.request

try:
    from google.cloud import bigquery
except ImportError:
    print("[FATAL] google-cloud-bigquery not installed. Run: pip install google-cloud-bigquery")
    sys.exit(2)


# ============ 阈值默认值（可用命令行覆盖）============
# 这些阈值应基于"正常业务查询规模"来设定。
# TideRider 正常一次舆情查询扫描量：几百 MB ~ 几 GB。
# 因此：
#   - 单次 job 扫描 > 50 GB   => 可疑（远超正常聚合查询）
#   - 单账号 24h 累计 > 500 GB => 高度可疑（疑似批量拖库）
DEFAULT_SINGLE_JOB_GB = 50.0
DEFAULT_DAILY_TOTAL_GB = 500.0
DEFAULT_LOOKBACK_HOURS = 24
DEFAULT_REGION = "region-us"


def gb(bytes_val):
    if not bytes_val:
        return 0.0
    return round(bytes_val / (1024 ** 3), 3)


def build_client(project):
    """项目从凭证自动读取；ADC 场景需显式传 project。"""
    if project:
        return bigquery.Client(project=project)
    return bigquery.Client()


def query_jobs(client, region, lookback_hours, scope):
    """
    scope = 'JOBS_BY_PROJECT'(模式A) 或 'JOBS_BY_USER'(模式B)
    返回 list[dict]，含 user_email / job_id / bytes / statement_type / state
    """
    view = f"`{region}`.INFORMATION_SCHEMA.{scope}"
    sql = f"""
    SELECT
      job_id,
      user_email,
      creation_time,
      total_bytes_processed,
      total_bytes_billed,
      statement_type,
      state,
      query
    FROM {view}
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours HOUR)
      AND job_type = 'QUERY'
      AND state = 'DONE'
    ORDER BY total_bytes_processed DESC
    """
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("hours", "INT64", lookback_hours)]
    )
    rows = []
    for r in client.query(sql, job_config=cfg).result():
        rows.append(dict(r))
    return rows


def detect_anomalies(rows, single_job_gb, daily_total_gb):
    """返回 (single_hits, per_user_totals, offenders)"""
    single_hits = []  # 单次超阈值的 job
    per_user = {}     # user_email -> 累计字节
    for r in rows:
        b = r.get("total_bytes_processed") or 0
        u = r.get("user_email") or "(unknown)"
        per_user[u] = per_user.get(u, 0) + b
        if gb(b) >= single_job_gb:
            single_hits.append(r)

    offenders = []  # 累计超阈值的账号
    for u, b in sorted(per_user.items(), key=lambda x: -x[1]):
        if gb(b) >= daily_total_gb:
            offenders.append((u, gb(b)))
    return single_hits, per_user, offenders


def send_wecom(webhook, markdown_text):
    payload = {"msgtype": "markdown", "markdown": {"content": markdown_text}}
    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def build_alert_markdown(mode, region, hours, single_hits, offenders,
                         single_job_gb, daily_total_gb):
    lines = []
    lines.append("## 🚨 BigQuery 异常扫描量告警")
    lines.append(f"> 模式: **{mode}** · 区域: {region} · 回看: 近 {hours}h")
    lines.append("")
    if offenders:
        lines.append(f"**⚠️ 累计扫描超限账号（阈值 {daily_total_gb} GB / {hours}h）:**")
        for u, total in offenders:
            lines.append(f"- <font color=\"warning\">{u}</font>: 累计 **{total} GB**")
        lines.append("")
    if single_hits:
        lines.append(f"**⚠️ 单次大扫描 job（阈值 {single_job_gb} GB）:**")
        for r in single_hits[:10]:
            lines.append(
                f"- {str(r.get('creation_time'))[:19]} | "
                f"{r.get('user_email')} | "
                f"<font color=\"warning\">{gb(r.get('total_bytes_processed'))} GB</font> | "
                f"{r.get('statement_type')}"
            )
        if len(single_hits) > 10:
            lines.append(f"- …还有 {len(single_hits) - 10} 条")
        lines.append("")
    lines.append("请立即核实：是否为已知业务任务？账号是否被冒用？必要时轮换凭证。")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="BigQuery scan-volume anomaly alert")
    ap.add_argument("--project", default=None, help="GCP project id (ADC 场景必填)")
    ap.add_argument("--region", default=DEFAULT_REGION, help="e.g. region-us / region-asia-east1")
    ap.add_argument("--lookback-hours", type=int, default=DEFAULT_LOOKBACK_HOURS)
    ap.add_argument("--single-job-gb", type=float, default=DEFAULT_SINGLE_JOB_GB)
    ap.add_argument("--daily-total-gb", type=float, default=DEFAULT_DAILY_TOTAL_GB)
    ap.add_argument("--webhook", default=None, help="WeCom webhook url; 省略则只打印不告警")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不发告警")
    args = ap.parse_args()

    client = build_client(args.project)

    # 自动探测权限：优先项目级(模式A)，失败降级账号自审(模式B)
    mode, rows = None, None
    try:
        rows = query_jobs(client, args.region, args.lookback_hours, "JOBS_BY_PROJECT")
        mode = "A·项目级审计(全项目)"
    except Exception as e:
        print(f"[INFO] JOBS_BY_PROJECT 不可用（无 listAll 权限）: {str(e)[:120]}")
        print("[INFO] 降级为 JOBS_BY_USER（只看当前账号）")
        rows = query_jobs(client, args.region, args.lookback_hours, "JOBS_BY_USER")
        mode = "B·账号自审(仅当前账号)"

    single_hits, per_user, offenders = detect_anomalies(
        rows, args.single_job_gb, args.daily_total_gb
    )

    # 控制台摘要
    print(f"\n=== 扫描完成 | 模式 {mode} | {args.region} | 近 {args.lookback_hours}h ===")
    print(f"总 job 数: {len(rows)}")
    print(f"Top 账号扫描量:")
    for u, b in sorted(per_user.items(), key=lambda x: -x[1])[:5]:
        print(f"  {u}: {gb(b)} GB")
    print(f"单次超阈值({args.single_job_gb}GB) job: {len(single_hits)}")
    print(f"累计超阈值({args.daily_total_gb}GB) 账号: {len(offenders)}")

    if not single_hits and not offenders:
        print("\n✅ 无异常，未触发告警。")
        return 0

    md = build_alert_markdown(
        mode, args.region, args.lookback_hours,
        single_hits, offenders, args.single_job_gb, args.daily_total_gb
    )
    print("\n" + "=" * 50)
    print(md)
    print("=" * 50)

    if args.webhook and not args.dry_run:
        try:
            resp = send_wecom(args.webhook, md)
            print(f"\n[OK] 告警已发送: {resp}")
        except Exception as e:
            print(f"\n[ERR] 告警发送失败: {e}")
            return 1
    else:
        print("\n[DRY-RUN] 未发送告警（未提供 --webhook 或指定了 --dry-run）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
